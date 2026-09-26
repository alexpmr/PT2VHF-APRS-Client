from __future__ import annotations

import queue
import re
import shutil
import socket
import subprocess
import sys
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


def _connect_ipv4(host: str, port: int, timeout: float = 8.0) -> socket.socket:
    """Conecta explicitamente por IPv4 para evitar esperas longas em redes com IPv6 parcial."""
    last_error: Exception | None = None
    addresses = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    if not addresses:
        raise OSError(f"DNS não retornou endereço IPv4 para {host}")
    for family, socktype, proto, _canonname, sockaddr in addresses:
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(timeout)
        try:
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last_error = exc
            try:
                sock.close()
            except OSError:
                pass
    raise OSError(f"Falha ao conectar em {host}:{port}: {last_error}")


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


def _notify_personal_message(from_call: str, message: str) -> None:
    """Notificação local best-effort, sem interferir na thread APRS."""
    _play_windows_message_sound()

    def _notify() -> None:
        title = f"APRS de {from_call}"
        body = str(message or "")[:180]
        try:
            if sys.platform == "darwin":
                safe_title = title.replace('"', "'")
                safe_body = body.replace('"', "'")
                subprocess.Popen(
                    ["osascript", "-e", f'display notification "{safe_body}" with title "{safe_title}"'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            elif sys.platform.startswith("linux") and shutil.which("notify-send"):
                subprocess.Popen(
                    ["notify-send", title, body],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass

    if sys.platform != "win32":
        threading.Thread(target=_notify, name="pt2vhf-message-notification", daemon=True).start()


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
    packets_sent: int = 0
    last_tx_at: str = ""


class APRSService:
    def __init__(self) -> None:
        self._status = ConnectionStatus()
        self._status_lock = threading.Lock()
        self._socket_lock = threading.Lock()
        self._tx_send_lock = threading.Lock()
        self._socket: socket.socket | None = None
        self._worker: threading.Thread | None = None
        self._beacon_worker: threading.Thread | None = None
        self._tx_worker: threading.Thread | None = None
        self._tx_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._tx_stop_event = threading.Event()
        self._tx_guard = threading.Lock()
        self._recent_tx: dict[str, tuple[float, dict[str, Any]]] = {}
        self._stop_event = threading.Event()
        self._msg_counter = int(time.time()) % 1000
        self._last_beacon = 0.0
        self._query_response_last: dict[tuple[str, str], float] = {}

    def status(self) -> dict[str, Any]:
        with self._status_lock:
            return asdict(self._status)

    def _ensure_tx_worker(self) -> None:
        if self._tx_worker and self._tx_worker.is_alive():
            return
        self._tx_stop_event.clear()
        self._tx_worker = threading.Thread(target=self._tx_loop, name="aprs-tx", daemon=True)
        self._tx_worker.start()

    def _tx_loop(self) -> None:
        while not self._tx_stop_event.is_set():
            try:
                job = self._tx_queue.get(timeout=0.4)
            except queue.Empty:
                continue
            packets = list(job.get("packets") or [])
            try:
                for index, item in enumerate(packets):
                    if self._tx_stop_event.is_set():
                        db.mark_message_status(item["msg_id"], "Cancelada no encerramento")
                        continue
                    try:
                        self._send_raw(item["packet"])
                        db.mark_message_status(item["msg_id"], "Enviada")
                    except Exception as exc:
                        db.mark_message_status(item["msg_id"], "Falhou")
                        for remaining in packets[index + 1:]:
                            db.mark_message_status(remaining["msg_id"], "Falhou")
                        self._set_status(last_error=f"TX de mensagem: {exc}")
                        break
                    if index + 1 < len(packets):
                        time.sleep(0.25)
            finally:
                self._tx_queue.task_done()

    def shutdown(self) -> None:
        self._tx_stop_event.set()
        while True:
            try:
                job = self._tx_queue.get_nowait()
            except queue.Empty:
                break
            try:
                for item in job.get("packets") or []:
                    db.mark_message_status(item["msg_id"], "Cancelada no encerramento")
            finally:
                self._tx_queue.task_done()
        self.disconnect()
        if self._tx_worker and self._tx_worker.is_alive():
            self._tx_worker.join(timeout=1.5)


    def _set_status(self, **kwargs: Any) -> None:
        with self._status_lock:
            for key, value in kwargs.items():
                setattr(self._status, key, value)

    def start_if_configured(self) -> None:
        cfg = db.get_config()
        if cfg.get("connect_on_start"):
            try:
                self.connect()
            except Exception as exc:
                self._set_status(
                    wanted=False,
                    connected=False,
                    verified=False,
                    state="Configuração incompleta",
                    last_error=str(exc),
                )

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
        initial_failures = 0
        had_connected = False
        while self.status()["wanted"]:
            cfg = db.get_config()
            configured_server = str(cfg.get("server") or "soam.aprs2.net").strip()
            port = int(cfg.get("port") or 14580)
            call = full_callsign(cfg)
            try:
                candidates: list[str] = []
                for candidate in (configured_server, "rotate.aprs2.net", "soam.aprs2.net"):
                    if candidate and candidate.lower() not in {item.lower() for item in candidates}:
                        candidates.append(candidate)

                sock = None
                errors: list[str] = []
                server = configured_server
                for index, candidate in enumerate(candidates, start=1):
                    try:
                        server = candidate
                        self._set_status(
                            state=f"Conectando a {candidate}:{port} ({index}/{len(candidates)})...",
                            connected=False,
                            verified=False,
                            last_error="",
                        )
                        sock = _connect_ipv4(candidate, port, timeout=8.0)
                        break
                    except OSError as exc:
                        errors.append(f"{candidate}: {exc}")

                if sock is None:
                    raise ConnectionError(
                        "Não foi possível abrir conexão TCP com o APRS-IS. " + " | ".join(errors)
                    )

                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(90)
                with self._socket_lock:
                    self._socket = sock

                passcode = str(cfg.get("passcode") or "").strip()
                if not passcode:
                    passcode = str(calculate_aprs_passcode(call))
                login = f"user {call} pass {passcode} vers PT2VHFAPRSClient {VERSION}"
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
                initial_failures = 0
                had_connected = True
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
                initial_failures += 1
                state_text = "Conexão perdida" if had_connected else f"Falha ao conectar ({initial_failures}/3)"
                self._set_status(connected=False, verified=False, state=state_text, last_error=str(exc))
                self._close_socket()
                if not self.status()["wanted"]:
                    break

                # Na primeira conexão, não deixa o usuário preso em tentativas infinitas.
                if not had_connected and initial_failures >= 3:
                    self._set_status(
                        wanted=False,
                        connected=False,
                        verified=False,
                        state="Falha ao conectar",
                        last_error=str(exc),
                    )
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

        # Linhas de controle do servidor não passam pelo pipeline de pacote,
        # mas continuam registradas no log APRS.
        if line.startswith("#"):
            db.add_aprs_log("RX", line)
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
            parsed = {"raw": line}

        fmt = str(parsed.get("format") or "")
        from_call = str(parsed.get("from") or extract_source(line) or "")

        # v1.6.14: log, pacote, topologia e estação/track são gravados juntos.
        # Evita 3-4 conexões e commits SQLite independentes para cada RX.
        db.process_received_packet(line, parsed, from_call, fmt)
        self._maybe_resolve_nonmessage_query_response(from_call, parsed, line)

        msg = parse_message_line(line, parsed)
        if msg:
            self._handle_message(msg, line)

    def _maybe_resolve_nonmessage_query_response(self, from_call: str, parsed: dict[str, Any], raw: str) -> None:
        peer = str(from_call or "").upper().strip()
        if not peer:
            return
        fmt = str(parsed.get("format") or "").lower()
        if parsed.get("latitude") is not None and parsed.get("longitude") is not None:
            lat = float(parsed.get("latitude"))
            lon = float(parsed.get("longitude"))
            db.resolve_aprs_query_response(
                peer,
                ["APRSP"],
                f"Posição: {lat:.6f}, {lon:.6f}",
                raw,
            )
            return
        payload = raw.split(":", 1)[1] if ":" in raw else ""
        if fmt == "status" or payload.startswith(">"):
            db.resolve_aprs_query_response(peer, ["APRSS"], payload[:180], raw)
            return
        if fmt in {"object", "item"} or payload.startswith(";"):
            db.resolve_aprs_query_response(peer, ["APRSO"], payload[:180], raw)

    def _handle_directed_query(self, from_call: str, query_text: str, raw: str) -> None:
        query_type, _arg = parse_query_text(query_text)
        qid = db.add_aprs_query(
            "in",
            from_call,
            query_type or "UNKNOWN",
            query_text,
            status="Recebida",
            raw=raw,
        )
        cfg = db.get_config()
        own = full_callsign(cfg).upper()
        if not query_type:
            db.update_aprs_query_result(qid, "Não suportada", response_text="Query desconhecida")
            return
        if not bool(cfg.get("respond_to_queries", 0)):
            db.update_aprs_query_result(qid, "Ignorada", response_text="Respostas automáticas desativadas")
            return
        if not self.status().get("verified"):
            db.update_aprs_query_result(qid, "Ignorada", response_text="APRS-IS não verificado")
            return

        supported = {"APRSP", "APRSS", "APRST", "PING"}
        if query_type not in supported:
            db.update_aprs_query_result(qid, "Não suportada", response_text=f"{query_type} não implementada para resposta automática")
            return

        key = (str(from_call or "").upper().strip(), query_type)
        now = time.monotonic()
        last = float(self._query_response_last.get(key) or 0.0)
        if now - last < 30.0:
            db.update_aprs_query_result(qid, "Rate-limit", response_text="Query repetida em menos de 30 s")
            return
        self._query_response_last[key] = now

        source = own
        if query_type == "APRSP":
            if cfg.get("latitude") is None or cfg.get("longitude") is None:
                db.update_aprs_query_result(qid, "Sem dados", response_text="Posição local não configurada")
                return
            packet = build_beacon_packet(cfg)
        elif query_type == "APRSS":
            status_text = " ".join(str(cfg.get("comment") or "PT2VHF APRS Client").split())[:62]
            packet = f"{source}>APRS,TCPIP*:>{status_text}"
        else:
            received_header = raw.split(":", 1)[0].strip()
            response_text = f"{received_header}:"
            packet = f"{source}>APRS,TCPIP*::{str(from_call).upper():<9}:{response_text}"

        try:
            self._send_raw(packet)
            db.update_aprs_query_result(qid, "Respondida", response_text=packet, response_raw=packet)
        except Exception as exc:
            db.update_aprs_query_result(qid, "Falhou", response_text=str(exc))

    def send_query(self, destination: str, query_type: str, heard_callsign: str = "") -> dict[str, Any]:
        status = self.status()
        if not status["connected"]:
            raise ConnectionError("Cliente APRS-IS desconectado.")
        if not status["verified"]:
            raise PermissionError("Conexão APRS-IS não verificada; não é possível transmitir queries.")

        destination = str(destination or "").upper().strip()
        if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?", destination):
            raise ValueError("Indicativo de destino inválido.")

        query_type = str(query_type or "").upper().strip()
        if query_type == "PINGACK":
            return self.send_ping_ack(destination)

        payload = build_query_payload(query_type, heard_callsign)
        cfg = db.get_config()
        source = full_callsign(cfg)
        packet = f"{source}>APRS,TCPIP*::{destination:<9}:{payload}"
        self._send_raw(packet)
        query_id = db.add_aprs_query(
            "out",
            destination,
            query_type,
            payload,
            status="Aguardando resposta",
            raw=packet,
        )
        return {"id": query_id, "to": destination, "query_type": query_type, "payload": payload, "status": "Aguardando resposta"}

    def send_ping_ack(self, destination: str) -> dict[str, Any]:
        status = self.status()
        if not status["connected"] or not status["verified"]:
            raise ConnectionError("Ping/ACK exige APRS-IS conectado e verificado.")
        destination = str(destination or "").upper().strip()
        if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?", destination):
            raise ValueError("Indicativo de destino inválido.")
        cfg = db.get_config()
        source = full_callsign(cfg)
        self._msg_counter = (self._msg_counter + 1) % 1000
        msg_id = f"{self._msg_counter:03d}"
        packet = f"{source}>APRS,TCPIP*::{destination:<9}:PING{{{msg_id}"
        self._send_raw(packet)
        query_id = db.add_aprs_query(
            "out",
            destination,
            "PINGACK",
            "PING",
            status="Aguardando resposta",
            raw=packet,
            message_id=msg_id,
        )
        return {"id": query_id, "to": destination, "query_type": "PINGACK", "payload": "PING", "message_id": msg_id, "status": "Aguardando resposta"}

    def _handle_message(self, msg: dict[str, str], raw: str) -> None:
        text = msg["text"].strip()
        from_call = msg["from"].upper()
        to_call = msg["to"].upper()
        ack = re.fullmatch(r"ack([A-Za-z0-9]{1,5})", text, re.IGNORECASE)
        rej = re.fullmatch(r"rej([A-Za-z0-9]{1,5})", text, re.IGNORECASE)
        if ack:
            db.mark_message_status(ack.group(1), "ACK", from_call)
            db.resolve_ping_ack(ack.group(1), from_call)
            return
        if rej:
            db.mark_message_status(rej.group(1), "REJ", from_call)
            return

        message_text, msg_id = split_message_id(text)
        cfg = db.get_config()
        own_call = full_callsign(cfg).upper()
        is_personal_message = classify_message_type(to_call) == "message" and to_call == own_call

        if is_personal_message and not msg_id and message_text.strip().startswith("?"):
            self._handle_directed_query(from_call, message_text.strip(), raw)
            return

        upper_text = message_text.strip().upper()
        if to_call == own_call:
            if re.match(r"^[A-Z0-9-]+>[^:]+:$", upper_text):
                trace = parse_trace_nodes(message_text)
                if db.resolve_aprs_query_response(from_call, ["APRST", "PING"], message_text, raw, trace_path=trace):
                    return
            if upper_text.startswith("DIRECTS="):
                if db.resolve_aprs_query_response(from_call, ["APRSD"], message_text, raw):
                    return
            if "_HEARD:" in upper_text or " HEARD:" in upper_text:
                if db.resolve_aprs_query_response(from_call, ["APRSH"], message_text, raw):
                    return

        message_type = classify_message_type(to_call)
        db.add_message(
            "in", from_call, to_call, message_text,
            msg_id=msg_id,
            status="Recebida" if message_type == "message" else "Boletim recebido",
            raw=raw,
            message_type=message_type,
        )

        # Alerta e ACK somente para mensagem individual endereçada exatamente a esta estação.
        is_personal_message = message_type == "message" and to_call == own_call

        if is_personal_message and bool(cfg.get("sound_on_personal_message", 1)):
            _notify_personal_message(from_call, message_text)

        if is_personal_message and msg_id and self.status()["verified"]:
            try:
                self.send_ack(from_call, msg_id)
            except Exception:
                pass

    def _send_raw(self, line: str) -> None:
        data = (line.rstrip("\r\n") + "\r\n").encode("latin-1", errors="replace")
        if len(data) > 512:
            raise ValueError("Pacote APRS excede 512 bytes.")
        with self._tx_send_lock:
            with self._socket_lock:
                sock = self._socket
            if not sock:
                raise ConnectionError("Não conectado ao APRS-IS.")
            try:
                sock.sendall(data)
            except OSError as exc:
                self._set_status(connected=False, verified=False, last_error=f"Falha de transmissão: {exc}")
                self._close_socket()
                raise ConnectionError(f"Falha ao transmitir ao APRS-IS: {exc}") from exc
        if not line.lower().startswith("user "):
            with self._status_lock:
                self._status.packets_sent = int(self._status.packets_sent or 0) + 1
                self._status.last_tx_at = db.utc_now_iso()
        db.add_aprs_log("TX", mask_sensitive_log_line(line))

    def queue_message_parts(self, destination: str, text: str) -> dict[str, Any]:
        status = self.status()
        if not status["connected"]:
            raise ConnectionError("Cliente APRS-IS desconectado.")
        if not status["verified"]:
            raise PermissionError("Conexão APRS-IS não verificada; informe um passcode válido para transmitir.")

        cfg = db.get_config()
        source = full_callsign(cfg)
        destination = str(destination or "").upper().strip()
        if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?", destination):
            raise ValueError("Indicativo de destino inválido.")

        parts = split_aprs_message_parts(text)
        dedupe_key = destination + "\0" + " ".join(parts)
        now = time.monotonic()
        with self._tx_guard:
            self._recent_tx = {k: v for k, v in self._recent_tx.items() if now - v[0] <= 5.0}
            recent = self._recent_tx.get(dedupe_key)
            if recent:
                result = dict(recent[1])
                result["duplicate"] = True
                return result

            message_ids = []
            packets = []
            pending_rows = []
            group_id = f"{int(time.time() * 1000)}-{self._msg_counter:03d}"
            for index, part in enumerate(parts):
                self._msg_counter = (self._msg_counter + 1) % 1000
                msg_id = f"{self._msg_counter:03d}"
                packet = f"{source}>APRS,TCPIP*::{destination:<9}:{part}{{{msg_id}"
                message_ids.append(msg_id)
                packets.append({"packet": packet, "msg_id": msg_id})
                pending_rows.append({
                    "from_call": source,
                    "to_call": destination,
                    "message": part,
                    "msg_id": msg_id,
                    "status": "Na fila",
                    "raw": packet,
                    "message_group_id": group_id,
                    "part_index": index + 1,
                    "part_count": len(parts),
                    "retry_count": 0,
                })

            row_ids = db.add_outgoing_message_parts(pending_rows)
            result = {"row_ids": row_ids, "message_ids": message_ids, "parts": parts, "part_count": len(parts), "group_id": group_id, "queued": True, "duplicate": False}
            self._recent_tx[dedupe_key] = (now, dict(result))

        self._ensure_tx_worker()
        self._tx_queue.put({"packets": packets, "group_id": group_id})
        return result

    def send_message(self, destination: str, text: str) -> int:
        result = self.send_message_parts(destination, text)
        return int(result["row_ids"][0])

    def send_message_parts(self, destination: str, text: str) -> dict[str, Any]:
        status = self.status()
        if not status["connected"]:
            raise ConnectionError("Cliente APRS-IS desconectado.")
        if not status["verified"]:
            raise PermissionError("Conexão APRS-IS não verificada; informe um passcode válido para transmitir.")

        cfg = db.get_config()
        source = full_callsign(cfg)
        destination = destination.upper().strip()
        if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?", destination):
            raise ValueError("Indicativo de destino inválido.")

        parts = split_aprs_message_parts(text)
        row_ids: list[int] = []
        message_ids: list[str] = []
        group_id = f"{int(time.time() * 1000)}-{self._msg_counter:03d}"

        for index, part in enumerate(parts):
            self._msg_counter = (self._msg_counter + 1) % 1000
            msg_id = f"{self._msg_counter:03d}"
            packet = f"{source}>APRS,TCPIP*::{destination:<9}:{part}{{{msg_id}"
            self._send_raw(packet)
            row_ids.append(
                db.add_message(
                    "out", source, destination, part,
                    msg_id=msg_id, status="Enviada", raw=packet,
                    message_group_id=group_id,
                    part_index=index + 1,
                    part_count=len(parts),
                    retry_count=0,
                )
            )
            message_ids.append(msg_id)
            if index + 1 < len(parts):
                time.sleep(0.25)

        return {
            "row_ids": row_ids,
            "message_ids": message_ids,
            "parts": parts,
            "part_count": len(parts),
            "group_id": group_id,
        }

    def retry_message(self, row_id: int) -> dict[str, Any]:
        status = self.status()
        if not status["connected"] or not status["verified"]:
            raise ConnectionError("Retry exige conexão APRS-IS conectada e verificada.")

        original = db.get_message(row_id)
        if not original or original.get("direction") != "out" or original.get("message_type") != "message":
            raise ValueError("Mensagem de saída não encontrada.")

        cfg = db.get_config()
        max_retries = max(0, int(cfg.get("message_retry_attempts") or 0))
        retry_count = int(original.get("retry_count") or 0)
        if retry_count >= max_retries:
            raise ValueError("A mensagem já atingiu o limite configurado de tentativas.")

        source = full_callsign(cfg)
        destination = str(original.get("to_call") or "").upper().strip()
        part = str(original.get("message") or "")
        self._msg_counter = (self._msg_counter + 1) % 1000
        msg_id = f"{self._msg_counter:03d}"
        packet = f"{source}>APRS,TCPIP*::{destination:<9}:{part}{{{msg_id}"
        self._send_raw(packet)
        db.mark_message_retried(int(original["id"]))
        new_row = db.add_message(
            "out", source, destination, part,
            msg_id=msg_id,
            status="Reenviada",
            raw=packet,
            message_group_id=original.get("message_group_id"),
            part_index=original.get("part_index"),
            part_count=original.get("part_count"),
            retry_count=retry_count + 1,
        )
        return {"id": new_row, "message_id": msg_id, "retry_count": retry_count + 1}

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
        last_retry_check = 0.0
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

            if status["connected"] and status["verified"] and time.time() - last_retry_check >= 10:
                last_retry_check = time.time()
                retry_seconds = max(15, int(cfg.get("message_retry_seconds") or 60))
                max_retries = max(0, int(cfg.get("message_retry_attempts") or 0))
                if max_retries:
                    for pending in db.list_retry_candidates(retry_seconds, max_retries, limit=3):
                        try:
                            self.retry_message(int(pending["id"]))
                            time.sleep(0.35)
                        except Exception as exc:
                            self._set_status(last_error=f"Retry de mensagem: {exc}")
                            break
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


def split_aprs_message_parts(text: str, single_limit: int = 63) -> list[str]:
    """Divide mensagens APRS sem rótulos visíveis, preferindo limites entre palavras."""
    clean = " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split())
    if not clean:
        raise ValueError("Mensagem vazia.")
    if len(clean) <= single_limit:
        return [clean]

    chunks: list[str] = []
    remaining = clean
    while remaining:
        if len(remaining) <= single_limit:
            chunks.append(remaining)
            break

        window = remaining[: single_limit + 1]
        cut = max(window.rfind(" ", 0, single_limit + 1), window.rfind("\n", 0, single_limit + 1))
        if cut <= 0:
            # Último recurso: uma palavra individual ultrapassa o limite APRS.
            cut = single_limit

        chunk = remaining[:cut].rstrip()
        if not chunk:
            chunk = remaining[:single_limit]
            cut = single_limit
        chunks.append(chunk)
        remaining = remaining[cut:].lstrip()

    if len(chunks) > 99:
        raise ValueError("Mensagem muito longa; limite de 99 partes APRS.")
    return chunks


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

QUERY_TYPES = {"APRSP", "APRSS", "APRSD", "APRSH", "APRSO", "APRST", "PING", "PINGACK"}


def parse_query_text(text: str) -> tuple[str, str]:
    value = str(text or "").strip()
    upper = value.upper()
    if upper == "?PING?":
        return "PING", ""
    match = re.match(r"^\?(APRSP|APRSS|APRSD|APRSM|APRSO|APRST)(?:\s+.*)?$", upper)
    if match:
        return match.group(1), ""
    match = re.match(r"^\?APRSH(?:\s+)?([A-Z0-9-]{1,9})?", upper)
    if match:
        return "APRSH", str(match.group(1) or "").strip()
    return "", ""


def build_query_payload(query_type: str, heard_callsign: str = "") -> str:
    query_type = str(query_type or "").upper().strip()
    if query_type == "PING":
        return "?PING?"
    if query_type == "APRSH":
        heard = str(heard_callsign or "").upper().strip()
        if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?", heard):
            raise ValueError("Informe um indicativo válido para a query APRSH.")
        return f"?APRSH {heard:<9}"
    if query_type in {"APRSP", "APRSS", "APRSD", "APRSO", "APRST"}:
        return f"?{query_type}"
    raise ValueError("Tipo de query APRS não suportado.")


def parse_trace_nodes(text: str) -> list[str]:
    value = str(text or "").strip()
    if value.endswith(":"):
        value = value[:-1]
    if ">" not in value:
        return []
    source, route = value.split(">", 1)
    nodes = [source.strip().upper().rstrip("*")]
    parts = [part.strip().upper() for part in route.split(",") if part.strip()]
    if parts and parts[0] in {"APRS", "APRS1", "BEACON"}:
        parts = parts[1:]
    for part in parts:
        clean = part.rstrip("*")
        if not clean or clean in {"TCPIP", "TCPXX"} or re.fullmatch(r"QA[A-Z]", clean):
            continue
        nodes.append(clean)
    result: list[str] = []
    for call in nodes:
        if call and (not result or result[-1] != call):
            result.append(call)
    return result



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
