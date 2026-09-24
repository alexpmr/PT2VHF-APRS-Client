from __future__ import annotations

import re
import socket
import threading
import time
from dataclasses import dataclass, asdict
from typing import Any

try:
    import aprslib
except ImportError:  # Permite importar o módulo durante validações sem dependências instaladas.
    aprslib = None

from . import __version__
from . import database as db

VERSION = __version__


def _play_windows_message_sound() -> None:
    """Toca um aviso curto no Windows sem bloquear a thread de recepção APRS."""
    try:
        import winsound
    except ImportError:
        return

    def _sound() -> None:
        try:
            winsound.Beep(880, 120)
            winsound.Beep(1175, 180)
        except Exception:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

    threading.Thread(target=_sound, name="pt2vhf-message-sound", daemon=True).start()


MESSAGE_RE = re.compile(r"^(?P<from>[^>]+)>[^:]+::(?P<to>.{9}):(?P<text>.*)$")


@dataclass
class ConnectionStatus:
    wanted: bool = False
    connected: bool = False
    verified: bool = False
    state: str = "Desconectado"
    server_message: str = ""
    last_error: str = ""
    connected_since: str = ""
    active_filter: str = ""
    packets_received: int = 0
    last_packet_at: str = ""


class APRSService:
    def __init__(self) -> None:
        self._status = ConnectionStatus()
        self._status_lock = threading.Lock()
        self._socket_lock = threading.Lock()
        self._socket: socket.socket | None = None
        self._worker: threading.Thread | None = None
        self._beacon_worker: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._msg_counter = int(time.time()) % 1000
        self._last_beacon = 0.0

    def status(self) -> dict[str, Any]:
        with self._status_lock:
            return asdict(self._status)

    def _set_status(self, **kwargs: Any) -> None:
        with self._status_lock:
            for key, value in kwargs.items():
                setattr(self._status, key, value)

    def start_if_configured(self) -> None:
        cfg = db.get_config()
        if cfg.get("connect_on_start"):
            self.connect()

    def connect(self) -> None:
        if aprslib is None:
            raise RuntimeError("Dependência aprslib não instalada. Execute pip install -r requirements.txt")
        db.validate_required_station_config(db.get_config())
        self._set_status(wanted=True, last_error="")
        self._stop_event.clear()
        if not self._worker or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._connection_loop, name="aprs-connection", daemon=True)
            self._worker.start()
        if not self._beacon_worker or not self._beacon_worker.is_alive():
            self._beacon_worker = threading.Thread(target=self._beacon_loop, name="aprs-beacon", daemon=True)
            self._beacon_worker.start()

    def reconnect(self) -> None:
        """Força uma nova sessão APRS-IS usando a configuração atual."""
        if not self.status()["wanted"]:
            self.connect()
            return
        self._set_status(state="Reconectando com a nova configuração...", connected=False, verified=False)
        self._close_socket()

    def disconnect(self) -> None:
        self._set_status(wanted=False, state="Desconectando...")
        self._stop_event.set()
        self._close_socket()
        self._set_status(connected=False, verified=False, state="Desconectado", connected_since="")

    def _close_socket(self) -> None:
        with self._socket_lock:
            sock, self._socket = self._socket, None
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

    def _connection_loop(self) -> None:
        retry = 3
        while self.status()["wanted"]:
            cfg = db.get_config()
            server = cfg.get("server") or "brazil.aprs2.net"
            port = int(cfg.get("port") or 14580)
            call = full_callsign(cfg)
            try:
                self._set_status(state=f"Conectando a {server}:{port}...", connected=False, verified=False)
                sock = socket.create_connection((server, port), timeout=20)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(90)
                with self._socket_lock:
                    self._socket = sock

                login = f"user {call} pass {cfg.get('passcode') or -1} vers PT2VHFAPRSClient {VERSION}"
                aprs_filter = expand_filter(str(cfg.get("aprs_filter") or "").strip(), cfg)
                if aprs_filter:
                    login += f" filter {aprs_filter}"
                self._set_status(
                    active_filter=aprs_filter,
                    packets_received=0,
                    last_packet_at="",
                )
                self._send_raw(login)
                self._set_status(connected=True, state="Conectado; autenticando...", connected_since=db.utc_now_iso())
                retry = 3
                self._last_beacon = 0

                buffer = b""
                while self.status()["wanted"]:
                    chunk = sock.recv(8192)
                    if not chunk:
                        raise ConnectionError("Servidor encerrou a conexão")
                    buffer += chunk
                    while b"\n" in buffer:
                        raw_line, buffer = buffer.split(b"\n", 1)
                        line = raw_line.rstrip(b"\r").decode("latin-1", errors="replace")
                        self._handle_line(line)
            except Exception as exc:
                self._set_status(connected=False, verified=False, state="Conexão perdida", last_error=str(exc))
                self._close_socket()
                if not self.status()["wanted"]:
                    break
                for _ in range(retry):
                    if not self.status()["wanted"]:
                        break
                    time.sleep(1)
                retry = min(retry * 2, 60)
        self._close_socket()
        self._set_status(connected=False, verified=False, state="Desconectado", connected_since="")

    def _handle_line(self, line: str) -> None:
        if not line:
            return
        db.add_aprs_log("RX", line)
        if line.startswith("#"):
            verified = "verified" in line.lower() and "unverified" not in line.lower()
            if "logresp" in line.lower():
                self._set_status(
                    verified=verified,
                    state="Conectado e verificado" if verified else "Conectado sem verificação",
                    server_message=line,
                )
            else:
                self._set_status(server_message=line)
            return

        with self._status_lock:
            current = int(self._status.packets_received or 0)
            self._status.packets_received = current + 1
            self._status.last_packet_at = db.utc_now_iso()

        parsed: dict[str, Any] = {}
        try:
            parsed = aprslib.parse(line) if aprslib else {}
        except Exception:
            # Pacote desconhecido continua no histórico bruto.
            parsed = {"raw": line}
        fmt = str(parsed.get("format") or "")
        from_call = str(parsed.get("from") or extract_source(line) or "")
        db.record_packet(line, from_call, fmt)

        msg = parse_message_line(line, parsed)
        if msg:
            self._handle_message(msg, line)

        if parsed and parsed.get("from"):
            db.upsert_station(parsed)

    def _handle_message(self, msg: dict[str, str], raw: str) -> None:
        text = msg["text"].strip()
        from_call = msg["from"].upper()
        to_call = msg["to"].upper()
        ack = re.fullmatch(r"ack([A-Za-z0-9]{1,5})", text, re.IGNORECASE)
        rej = re.fullmatch(r"rej([A-Za-z0-9]{1,5})", text, re.IGNORECASE)
        if ack:
            db.mark_message_status(ack.group(1), "ACK", from_call)
            return
        if rej:
            db.mark_message_status(rej.group(1), "REJ", from_call)
            return

        message_text, msg_id = split_message_id(text)
        message_type = classify_message_type(to_call)
        db.add_message(
            "in", from_call, to_call, message_text,
            msg_id=msg_id,
            status="Recebida" if message_type == "message" else "Boletim recebido",
            raw=raw,
            message_type=message_type,
        )

        # Alerta e ACK somente para mensagem individual endereçada exatamente a esta estação.
        cfg = db.get_config()
        is_personal_message = message_type == "message" and to_call == full_callsign(cfg).upper()

        if is_personal_message and bool(cfg.get("sound_on_personal_message", 1)):
            _play_windows_message_sound()

        if is_personal_message and msg_id and self.status()["verified"]:
            try:
                self.send_ack(from_call, msg_id)
            except Exception:
                pass

    def _send_raw(self, line: str) -> None:
        data = (line.rstrip("\r\n") + "\r\n").encode("latin-1", errors="replace")
        if len(data) > 512:
            raise ValueError("Pacote APRS excede 512 bytes.")
        with self._socket_lock:
            if not self._socket:
                raise ConnectionError("Não conectado ao APRS-IS.")
            self._socket.sendall(data)
        db.add_aprs_log("TX", mask_sensitive_log_line(line))

    def send_message(self, destination: str, text: str) -> int:
        status = self.status()
        if not status["connected"]:
            raise ConnectionError("Cliente APRS-IS desconectado.")
        if not status["verified"]:
            raise PermissionError("Conexão APRS-IS não verificada; informe um passcode válido para transmitir.")

        cfg = db.get_config()
        source = full_callsign(cfg)
        destination = destination.upper().strip()
        if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", destination):
            raise ValueError("Indicativo de destino inválido.")
        clean = " ".join(str(text).replace("\r", " ").replace("\n", " ").split())
        if not clean:
            raise ValueError("Mensagem vazia.")
        self._msg_counter = (self._msg_counter + 1) % 1000
        msg_id = f"{self._msg_counter:03d}"
        # APRS clássico trabalha com payload curto; limita para manter compatibilidade ampla.
        clean = clean[:63]
        packet = f"{source}>APRS,TCPIP*::{destination:<9}:{clean}{{{msg_id}"
        self._send_raw(packet)
        return db.add_message("out", source, destination, clean, msg_id=msg_id, status="Enviada", raw=packet)

    def send_bulletin(self, text: str, bulletin_id: str = "0", group: str = "") -> int:
        status = self.status()
        if not status["connected"]:
            raise ConnectionError("Cliente APRS-IS desconectado.")
        if not status["verified"]:
            raise PermissionError("Conexão APRS-IS não verificada; informe um passcode válido para transmitir.")

        cfg = db.get_config()
        source = full_callsign(cfg)
        packet, addressee, message_type, clean = build_bulletin_packet(
            source=source,
            text=text,
            bulletin_id=bulletin_id,
            group=group,
        )
        self._send_raw(packet)
        return db.add_message(
            "out",
            source,
            addressee,
            clean,
            msg_id=None,
            status="Boletim enviado",
            raw=packet,
            message_type=message_type,
        )

    def send_ack(self, destination: str, msg_id: str) -> None:
        cfg = db.get_config()
        source = full_callsign(cfg)
        packet = f"{source}>APRS,TCPIP*::{destination:<9}:ack{msg_id}"
        self._send_raw(packet)

    def send_beacon(self) -> None:
        status = self.status()
        if not status["connected"] or not status["verified"]:
            raise ConnectionError("Beacon exige conexão APRS-IS conectada e verificada.")
        cfg = db.get_config()
        if cfg.get("latitude") is None or cfg.get("longitude") is None:
            raise ValueError("Configure latitude e longitude antes de transmitir beacon.")
        packet = build_beacon_packet(cfg)
        self._send_raw(packet)
        # Processa localmente para a própria estação aparecer no banco/mapa sem aguardar eco.
        if aprslib:
            try:
                parsed = aprslib.parse(packet)
                db.record_packet(packet, full_callsign(cfg), str(parsed.get("format") or ""))
                db.upsert_station(parsed)
            except Exception:
                pass
        self._last_beacon = time.time()

    def _beacon_loop(self) -> None:
        while self.status()["wanted"]:
            status = self.status()
            cfg = db.get_config()
            interval = max(1, int(cfg.get("beacon_minutes") or 10)) * 60
            if status["connected"] and status["verified"] and time.time() - self._last_beacon >= interval:
                try:
                    self.send_beacon()
                except Exception as exc:
                    self._set_status(last_error=f"Beacon: {exc}")
                    self._last_beacon = time.time()
            time.sleep(2)


service = APRSService()


def mask_sensitive_log_line(line: str) -> str:
    """Mascara credenciais antes de persistir/exibir o tráfego TX."""
    if str(line).lower().startswith("user "):
        return re.sub(r"(\spass\s+)\S+", r"\1******", str(line), flags=re.IGNORECASE)
    return str(line)


def classify_message_type(addressee: str) -> str:
    value = str(addressee or "").upper().strip()
    if re.fullmatch(r"BLN[0-9]", value):
        return "bulletin"
    if re.fullmatch(r"BLN[0-9][A-Z0-9]{1,5}", value):
        return "group_bulletin"
    return "message"


def build_bulletin_packet(source: str, text: str, bulletin_id: str = "0", group: str = "") -> tuple[str, str, str, str]:
    source = str(source or "").upper().strip()
    bulletin_id = str(bulletin_id or "").strip()
    group = str(group or "").upper().strip()

    if not re.fullmatch(r"[0-9]", bulletin_id):
        raise ValueError("O identificador do boletim deve ser um dígito de 0 a 9.")
    if group and not re.fullmatch(r"[A-Z0-9]{1,5}", group):
        raise ValueError("O grupo do boletim deve ter de 1 a 5 caracteres alfanuméricos.")

    clean = " ".join(str(text).replace("\r", " ").replace("\n", " ").split())
    if not clean:
        raise ValueError("Boletim vazio.")
    clean = clean[:67]

    message_type = "group_bulletin" if group else "bulletin"
    addressee = f"BLN{bulletin_id}{group:<5}" if group else f"BLN{bulletin_id}{'':<5}"
    packet = f"{source}>APRS,TCPIP*::{addressee}:{clean}"
    return packet, addressee.rstrip(), message_type, clean


def calculate_aprs_passcode(callsign: str) -> int:
    """Calcula o passcode APRS-IS clássico a partir do indicativo-base."""
    base = str(callsign or "").upper().strip().split("-", 1)[0]
    if not re.fullmatch(r"[A-Z0-9]{1,6}", base):
        raise ValueError("Indicativo inválido para cálculo do passcode APRS-IS.")

    value = 0x73E2
    for i in range(0, len(base), 2):
        value ^= ord(base[i]) << 8
        if i + 1 < len(base):
            value ^= ord(base[i + 1])
    return value & 0x7FFF


def full_callsign(cfg: dict[str, Any]) -> str:
    call = str(cfg.get("callsign") or "").upper().strip()
    ssid = int(cfg.get("ssid") or 0)
    return f"{call}-{ssid}" if ssid else call



def expand_filter(value: str, cfg: dict[str, Any]) -> str:
    """Aceita o atalho r/500 e o expande para r/lat/lon/500."""
    value = value.strip()
    m = re.fullmatch(r"r/(\d+(?:\.\d+)?)", value, re.IGNORECASE)
    if m:
        if cfg.get("latitude") is None or cfg.get("longitude") is None:
            raise ValueError("O filtro abreviado r/RAIO exige latitude e longitude configuradas.")
        return f"r/{float(cfg['latitude']):.5f}/{float(cfg['longitude']):.5f}/{m.group(1)}"
    return value

def extract_source(line: str) -> str:
    return line.split(">", 1)[0].strip() if ">" in line else ""


def parse_message_line(line: str, parsed: dict[str, Any] | None = None) -> dict[str, str] | None:
    # O TNC2 bruto é preferido porque preserva o identificador {NNN usado para ACK.
    m = MESSAGE_RE.match(line)
    if m:
        return {"from": m.group("from"), "to": m.group("to").strip(), "text": m.group("text")}
    parsed = parsed or {}
    if parsed.get("format") in {"message", "bulletin"} and parsed.get("addresse"):
        return {
            "from": str(parsed.get("from") or extract_source(line)),
            "to": str(parsed.get("addresse") or "").strip(),
            "text": str(parsed.get("message_text") or ""),
        }
    return None


def split_message_id(text: str) -> tuple[str, str | None]:
    m = re.match(r"^(.*)\{([A-Za-z0-9]{1,5})$", text)
    return (m.group(1), m.group(2)) if m else (text, None)


def _lat_aprs(value: float) -> str:
    hemi = "N" if value >= 0 else "S"
    value = abs(value)
    deg = int(value)
    minutes = (value - deg) * 60
    return f"{deg:02d}{minutes:05.2f}{hemi}"


def _lon_aprs(value: float) -> str:
    hemi = "E" if value >= 0 else "W"
    value = abs(value)
    deg = int(value)
    minutes = (value - deg) * 60
    return f"{deg:03d}{minutes:05.2f}{hemi}"


def build_beacon_packet(cfg: dict[str, Any]) -> str:
    source = full_callsign(cfg)
    table = str(cfg.get("symbol_table") or "/")[:1]
    symbol = str(cfg.get("symbol") or ">")[:1]
    if table not in {"/", "\\"}:
        table = "/"
    comment = " ".join(str(cfg.get("comment") or "").replace("\r", " ").replace("\n", " ").split())[:40]
    altitude = ""
    if cfg.get("altitude") is not None:
        feet = max(0, min(999999, int(round(float(cfg["altitude"]) * 3.28084))))
        altitude = f" /A={feet:06d}"
    payload = f"={_lat_aprs(float(cfg['latitude']))}{table}{_lon_aprs(float(cfg['longitude']))}{symbol}{comment}{altitude}"
    return f"{source}>APRS,TCPIP*:{payload}"
