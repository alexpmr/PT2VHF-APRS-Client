from __future__ import annotations

import hashlib
import json
import queue
import re
import socket
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import database as db
from . import diagnostics as diag

try:
    import serial  # type: ignore
    from serial.tools import list_ports  # type: ignore
except Exception:  # pragma: no cover - serial is optional in source-only installs
    serial = None
    list_ports = None

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD

TNC_DEFAULTS: dict[str, Any] = {
    "transport": "tcp",
    "serial_port": "",
    "serial_baud": 9600,
    "tcp_host": "127.0.0.1",
    "tcp_port": 8001,
    "auto_connect": 0,
    "role": "monitor",
    "auto_tx_enabled": 0,
    "tx_confirmed": 0,
    "digi_enabled": 0,
    "digi_profile": "fill",
    "digi_aliases": "",
    "digi_max_hops": 3,
    "duplicate_window_seconds": 30,
    "source_rate_limit_per_minute": 30,
    "igate_rx_enabled": 0,
    "igate_tx_enabled": 0,
    "igate_heard_window_minutes": 30,
    "igate_rf_path": "",
    "optimizer_mode": "observe",
    "retention_days": 14,
}

CALL_RE = re.compile(r"^(?P<call>[A-Z0-9]{1,6})(?:-(?P<ssid>\d{1,2}))?$", re.I)
MESSAGE_RE = re.compile(r"^(?P<source>[^>]+)>(?P<header>[^:]+)::(?P<dest>.{9}):(?P<text>.*)$")
WIDE_RE = re.compile(r"^WIDE(?P<n>[1-7])-(?P<remaining>[1-7])$", re.I)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _bool(value: Any) -> int:
    if isinstance(value, str):
        return 0 if value.strip().lower() in {"", "0", "false", "off", "no", "não", "nao"} else 1
    return 1 if bool(value) else 0


def normalize_call(value: str) -> str:
    value = str(value or "").upper().strip()
    if not CALL_RE.fullmatch(value):
        raise ValueError(f"Indicativo/SSID inválido: {value or '(vazio)'}")
    return value


def split_call(value: str) -> tuple[str, int]:
    match = CALL_RE.fullmatch(str(value or "").upper().strip())
    if not match:
        raise ValueError(f"Indicativo/SSID AX.25 inválido: {value}")
    ssid = int(match.group("ssid") or 0)
    if not (0 <= ssid <= 15):
        raise ValueError("SSID AX.25 deve ficar entre 0 e 15.")
    return match.group("call").upper(), ssid


def _ensure_schema() -> None:
    with db.connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tnc_config(
                id INTEGER PRIMARY KEY CHECK(id=1),
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tnc_frames(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                direction TEXT NOT NULL,
                medium TEXT NOT NULL DEFAULT 'RF',
                source TEXT,
                destination TEXT,
                path TEXT,
                packet_type TEXT,
                raw_tnc2 TEXT,
                reason TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_tnc_frames_time ON tnc_frames(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_tnc_frames_src ON tnc_frames(source, timestamp DESC);

            CREATE TABLE IF NOT EXISTS tnc_heard(
                callsign TEXT PRIMARY KEY,
                last_heard TEXT NOT NULL,
                last_direct_heard TEXT,
                direct INTEGER NOT NULL DEFAULT 0,
                path TEXT,
                heard_count INTEGER NOT NULL DEFAULT 0,
                last_packet_type TEXT,
                last_raw TEXT
            );

            CREATE TABLE IF NOT EXISTS tnc_decisions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                decision TEXT NOT NULL,
                source TEXT,
                destination TEXT,
                reason TEXT,
                raw_tnc2 TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_tnc_decisions_time ON tnc_decisions(timestamp DESC);

            CREATE TABLE IF NOT EXISTS tnc_edges(
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                medium TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                interactions INTEGER NOT NULL DEFAULT 0,
                ack_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(source,destination,medium)
            );
            CREATE INDEX IF NOT EXISTS idx_tnc_edges_activity ON tnc_edges(interactions DESC,last_seen DESC);
            """
        )
        heard_columns = {row["name"] for row in conn.execute("PRAGMA table_info(tnc_heard)").fetchall()}
        if "last_direct_heard" not in heard_columns:
            conn.execute("ALTER TABLE tnc_heard ADD COLUMN last_direct_heard TEXT")


def get_tnc_config() -> dict[str, Any]:
    _ensure_schema()
    payload: dict[str, Any] = {}
    with db.connection() as conn:
        row = conn.execute("SELECT payload FROM tnc_config WHERE id=1").fetchone()
        if row:
            try:
                payload = json.loads(row["payload"] or "{}")
            except Exception:
                payload = {}
    merged = dict(TNC_DEFAULTS)
    merged.update(payload if isinstance(payload, dict) else {})
    return normalize_tnc_config(merged, strict=False)


def normalize_tnc_config(payload: dict[str, Any], *, strict: bool = True) -> dict[str, Any]:
    merged = dict(TNC_DEFAULTS)
    merged.update(dict(payload or {}))

    merged["transport"] = str(merged.get("transport") or "tcp").lower().strip()
    if merged["transport"] not in {"tcp", "serial"}:
        raise ValueError("Transporte TNC deve ser KISS TCP ou KISS Serial.")

    merged["serial_port"] = str(merged.get("serial_port") or "").strip()
    merged["serial_baud"] = int(merged.get("serial_baud") or 9600)
    if merged["serial_baud"] not in {1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400}:
        raise ValueError("Baud rate serial inválido.")

    merged["tcp_host"] = str(merged.get("tcp_host") or "127.0.0.1").strip()
    merged["tcp_port"] = int(merged.get("tcp_port") or 8001)
    if not (1 <= merged["tcp_port"] <= 65535):
        raise ValueError("Porta TCP do TNC inválida.")

    for key in (
        "auto_connect", "auto_tx_enabled", "tx_confirmed", "digi_enabled",
        "igate_rx_enabled", "igate_tx_enabled",
    ):
        merged[key] = _bool(merged.get(key))

    merged["role"] = str(merged.get("role") or "monitor").lower().strip()
    if merged["role"] not in {"monitor", "station", "digi", "igate_rx", "igate_bidir", "digi_igate"}:
        raise ValueError("Papel RF/TNC inválido.")

    merged["digi_profile"] = str(merged.get("digi_profile") or "fill").lower().strip()
    if merged["digi_profile"] not in {"fill", "wide", "custom"}:
        raise ValueError("Perfil de digipeater inválido.")
    aliases = []
    for item in str(merged.get("digi_aliases") or "").replace(";", ",").split(","):
        item = item.upper().strip()
        if item and re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", item):
            aliases.append(item)
    merged["digi_aliases"] = ",".join(dict.fromkeys(aliases))

    merged["digi_max_hops"] = max(1, min(7, int(merged.get("digi_max_hops") or 3)))
    merged["duplicate_window_seconds"] = max(5, min(300, int(merged.get("duplicate_window_seconds") or 30)))
    merged["source_rate_limit_per_minute"] = max(5, min(300, int(merged.get("source_rate_limit_per_minute") or 30)))
    merged["igate_heard_window_minutes"] = max(1, min(180, int(merged.get("igate_heard_window_minutes") or 30)))

    rf_path = str(merged.get("igate_rf_path") or "").upper().strip().strip(",")
    if rf_path:
        for item in rf_path.split(","):
            if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", item.strip()):
                raise ValueError("Path RF do iGate contém elemento inválido.")
    merged["igate_rf_path"] = rf_path

    merged["optimizer_mode"] = str(merged.get("optimizer_mode") or "observe").lower().strip()
    if merged["optimizer_mode"] not in {"off", "observe", "automatic"}:
        raise ValueError("Modo do otimizador deve ser off, observe ou automatic.")
    merged["retention_days"] = max(1, min(90, int(merged.get("retention_days") or 14)))

    if strict and (merged["digi_enabled"] or merged["igate_tx_enabled"] or merged["auto_tx_enabled"]):
        if not merged["tx_confirmed"]:
            raise ValueError("Confirme explicitamente a habilitação de transmissão automática em RF.")
        if not merged["auto_tx_enabled"] and (merged["digi_enabled"] or merged["igate_tx_enabled"]):
            raise ValueError("Digipeater/iGate TX exige a chave Transmissão automática habilitada.")

    if strict and merged["transport"] == "serial" and not merged["serial_port"]:
        raise ValueError("Selecione a porta serial do TNC.")
    if strict and merged["transport"] == "tcp" and not merged["tcp_host"]:
        raise ValueError("Informe o host do KISS TCP.")

    return merged


def save_tnc_config(payload: dict[str, Any]) -> dict[str, Any]:
    cfg = normalize_tnc_config(payload, strict=True)
    _ensure_schema()
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO tnc_config(id,payload,updated_at) VALUES(1,?,?)
               ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at""",
            (json.dumps(cfg, ensure_ascii=False, sort_keys=True), utc_now_iso()),
        )
    return cfg


def _trim_history(cfg: dict[str, Any] | None = None) -> None:
    cfg = cfg or get_tnc_config()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=int(cfg["retention_days"]))).replace(microsecond=0).isoformat()
    with db.connection() as conn:
        conn.execute("DELETE FROM tnc_frames WHERE timestamp < ?", (cutoff,))
        conn.execute("DELETE FROM tnc_decisions WHERE timestamp < ?", (cutoff,))
        conn.execute("DELETE FROM tnc_edges WHERE last_seen < ?", (cutoff,))


def record_frame(
    direction: str,
    raw_tnc2: str,
    *,
    medium: str = "RF",
    source: str = "",
    destination: str = "",
    path: list[str] | None = None,
    packet_type: str = "",
    reason: str = "",
) -> None:
    _ensure_schema()
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO tnc_frames(timestamp,direction,medium,source,destination,path,packet_type,raw_tnc2,reason)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                utc_now_iso(), direction.upper(), medium.upper(), source.upper(), destination.upper(),
                json.dumps(path or [], ensure_ascii=False), packet_type, raw_tnc2, reason,
            ),
        )


def record_decision(
    action: str,
    decision: str,
    reason: str,
    *,
    source: str = "",
    destination: str = "",
    raw_tnc2: str = "",
) -> None:
    _ensure_schema()
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO tnc_decisions(timestamp,action,decision,source,destination,reason,raw_tnc2)
               VALUES(?,?,?,?,?,?,?)""",
            (utc_now_iso(), action, decision, source.upper(), destination.upper(), reason, raw_tnc2),
        )


def update_heard(packet: dict[str, Any], raw_tnc2: str) -> None:
    source = str(packet.get("source") or "").upper().strip()
    if not source:
        return
    path = packet.get("path") or []
    direct = 1 if not any(bool(item.get("repeated")) for item in path) else 0
    packet_type = packet_priority_kind(packet.get("info_text") or "")
    now = utc_now_iso()
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO tnc_heard(callsign,last_heard,last_direct_heard,direct,path,heard_count,last_packet_type,last_raw)
               VALUES(?,?,?,?,?,1,?,?)
               ON CONFLICT(callsign) DO UPDATE SET
                 last_heard=excluded.last_heard,
                 last_direct_heard=CASE WHEN excluded.direct=1 THEN excluded.last_heard ELSE tnc_heard.last_direct_heard END,
                 direct=excluded.direct,
                 path=excluded.path,
                 heard_count=tnc_heard.heard_count+1,
                 last_packet_type=excluded.last_packet_type,
                 last_raw=excluded.last_raw""",
            (source, now, now if direct else None, direct, json.dumps(path, ensure_ascii=False), packet_type, raw_tnc2),
        )


def record_edge(source: str, destination: str, medium: str, text: str = "") -> None:
    source = str(source or "").upper().strip()
    destination = str(destination or "").upper().strip()
    if not source or not destination or source == destination:
        return
    now = utc_now_iso()
    ack = 1 if re.match(r"^(ack|rej)[A-Za-z0-9]{1,5}$", str(text or ""), re.I) else 0
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO tnc_edges(source,destination,medium,first_seen,last_seen,interactions,ack_count)
               VALUES(?,?,?,?,?,1,?)
               ON CONFLICT(source,destination,medium) DO UPDATE SET
                 last_seen=excluded.last_seen,
                 interactions=tnc_edges.interactions+1,
                 ack_count=tnc_edges.ack_count+excluded.ack_count""",
            (source, destination, medium.upper(), now, now, ack),
        )


def list_frames(limit: int = 250) -> list[dict[str, Any]]:
    _ensure_schema()
    limit = max(1, min(int(limit or 250), 2000))
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tnc_frames ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        try:
            item["path"] = json.loads(item.get("path") or "[]")
        except Exception:
            item["path"] = []
        out.append(item)
    return out


def list_decisions(limit: int = 250) -> list[dict[str, Any]]:
    _ensure_schema()
    limit = max(1, min(int(limit or 250), 2000))
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tnc_decisions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def heard_stations(limit: int = 250) -> list[dict[str, Any]]:
    _ensure_schema()
    limit = max(1, min(int(limit or 250), 2000))
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tnc_heard ORDER BY last_heard DESC LIMIT ?", (limit,)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        try:
            item["path"] = json.loads(item.get("path") or "[]")
        except Exception:
            item["path"] = []
        result.append(item)
    return result


def top_edges(hours: int = 24, limit: int = 30) -> list[dict[str, Any]]:
    _ensure_schema()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max(1, min(int(hours or 24), 24 * 30)))).replace(microsecond=0).isoformat()
    with db.connection() as conn:
        rows = conn.execute(
            """SELECT source,destination,medium,first_seen,last_seen,interactions,ack_count
               FROM tnc_edges WHERE last_seen >= ?
               ORDER BY interactions DESC,last_seen DESC LIMIT ?""",
            (cutoff, max(1, min(int(limit or 30), 200))),
        ).fetchall()
    return [dict(row) for row in rows]


def direct_heard_recent(callsign: str, window_minutes: int) -> bool:
    callsign = str(callsign or "").upper().strip()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=max(1, int(window_minutes)))).replace(microsecond=0).isoformat()
    with db.connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM tnc_heard WHERE callsign=? AND last_direct_heard IS NOT NULL AND last_direct_heard>=?",
            (callsign, cutoff),
        ).fetchone()
    return bool(row)


def tnc_statistics() -> dict[str, Any]:
    _ensure_schema()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=24)).replace(microsecond=0).isoformat()
    with db.connection() as conn:
        rx = conn.execute("SELECT COUNT(*) c FROM tnc_frames WHERE timestamp>=? AND direction='RX'", (cutoff,)).fetchone()["c"]
        tx = conn.execute("SELECT COUNT(*) c FROM tnc_frames WHERE timestamp>=? AND direction='TX'", (cutoff,)).fetchone()["c"]
        direct = conn.execute("SELECT COUNT(*) c FROM tnc_heard WHERE direct=1 AND last_heard>=?", (cutoff,)).fetchone()["c"]
        heard = conn.execute("SELECT COUNT(*) c FROM tnc_heard WHERE last_heard>=?", (cutoff,)).fetchone()["c"]
        duplicate = conn.execute(
            "SELECT COUNT(*) c FROM tnc_decisions WHERE timestamp>=? AND decision='suppressed' AND reason LIKE 'Duplicado%'",
            (cutoff,),
        ).fetchone()["c"]
        gated_rf = conn.execute(
            "SELECT COUNT(*) c FROM tnc_decisions WHERE timestamp>=? AND action='igate_rf_is' AND decision='sent'",
            (cutoff,),
        ).fetchone()["c"]
        gated_is = conn.execute(
            "SELECT COUNT(*) c FROM tnc_decisions WHERE timestamp>=? AND action='igate_is_rf' AND decision='queued'",
            (cutoff,),
        ).fetchone()["c"]
    return {
        "period_hours": 24,
        "rx": int(rx),
        "tx": int(tx),
        "heard": int(heard),
        "direct_heard": int(direct),
        "duplicates_suppressed": int(duplicate),
        "gated_rf_to_is": int(gated_rf),
        "gated_is_to_rf": int(gated_is),
        "top_edges": top_edges(24, 20),
    }


def kiss_encode(payload: bytes, command: int = 0) -> bytes:
    raw = bytes([command & 0xFF]) + bytes(payload)
    out = bytearray([FEND])
    for byte in raw:
        if byte == FEND:
            out.extend((FESC, TFEND))
        elif byte == FESC:
            out.extend((FESC, TFESC))
        else:
            out.append(byte)
    out.append(FEND)
    return bytes(out)


class KissStreamDecoder:
    def __init__(self) -> None:
        self._buffer = bytearray()
        self._in_frame = False
        self._escaped = False

    def feed(self, data: bytes) -> list[tuple[int, bytes]]:
        frames: list[tuple[int, bytes]] = []
        for byte in data:
            if byte == FEND:
                if self._in_frame and self._buffer:
                    command = self._buffer[0]
                    frames.append((command, bytes(self._buffer[1:])))
                self._buffer.clear()
                self._in_frame = True
                self._escaped = False
                continue
            if not self._in_frame:
                continue
            if self._escaped:
                if byte == TFEND:
                    self._buffer.append(FEND)
                elif byte == TFESC:
                    self._buffer.append(FESC)
                else:
                    self._buffer.append(byte)
                self._escaped = False
                continue
            if byte == FESC:
                self._escaped = True
            else:
                self._buffer.append(byte)
        return frames


def _decode_address(raw: bytes, *, path: bool = False) -> dict[str, Any]:
    if len(raw) != 7:
        raise ValueError("Endereço AX.25 deve ter 7 bytes.")
    call = "".join(chr((byte >> 1) & 0x7F) for byte in raw[:6]).strip().upper()
    ssid = (raw[6] >> 1) & 0x0F
    value = call + (f"-{ssid}" if ssid else "")
    return {
        "call": call,
        "ssid": ssid,
        "value": value,
        "repeated": bool(raw[6] & 0x80) if path else False,
        "last": bool(raw[6] & 0x01),
    }


def _encode_address(value: str, *, last: bool, repeated: bool = False) -> bytes:
    call, ssid = split_call(value.rstrip("*"))
    call = call.ljust(6)[:6]
    out = bytearray((ord(ch) << 1) & 0xFE for ch in call)
    flag = 0x60 | ((ssid & 0x0F) << 1)
    if repeated or value.endswith("*"):
        flag |= 0x80
    if last:
        flag |= 0x01
    out.append(flag)
    return bytes(out)


def decode_ax25(frame: bytes) -> dict[str, Any]:
    frame = bytes(frame)
    if len(frame) < 16:
        raise ValueError("Frame AX.25 curto demais.")
    addresses = []
    offset = 0
    for index in range(10):
        if offset + 7 > len(frame):
            raise ValueError("Endereçamento AX.25 incompleto.")
        item = _decode_address(frame[offset:offset + 7], path=index >= 2)
        addresses.append(item)
        offset += 7
        if item["last"]:
            break
    else:
        raise ValueError("Frame AX.25 excede o número de endereços suportado.")
    if len(addresses) < 2 or offset >= len(frame):
        raise ValueError("Frame AX.25 sem origem/destino.")

    control = frame[offset]
    offset += 1
    pid = None
    if (control & 0x01) == 0 or control in {0x03, 0x13}:
        if offset >= len(frame):
            raise ValueError("Frame AX.25 sem PID.")
        pid = frame[offset]
        offset += 1
    info = frame[offset:]
    info_text = info.decode("latin-1", errors="replace")
    source = addresses[1]["value"]
    destination = addresses[0]["value"]
    path_items = addresses[2:]
    path_text = [item["value"] + ("*" if item["repeated"] else "") for item in path_items]
    header = f"{source}>{destination}"
    if path_text:
        header += "," + ",".join(path_text)
    return {
        "source": source,
        "destination": destination,
        "path": path_items,
        "path_text": path_text,
        "control": control,
        "pid": pid,
        "info": info,
        "info_text": info_text,
        "tnc2": f"{header}:{info_text}",
        "raw_frame": frame,
    }


def encode_ax25(
    source: str,
    destination: str,
    info: bytes | str,
    path: list[str] | None = None,
    *,
    control: int = 0x03,
    pid: int = 0xF0,
) -> bytes:
    source = normalize_call(source)
    destination = normalize_call(destination)
    path = list(path or [])
    addresses = [destination, source] + path
    encoded = bytearray()
    for index, value in enumerate(addresses):
        encoded.extend(_encode_address(value, last=index == len(addresses) - 1, repeated=value.endswith("*")))
    encoded.append(control & 0xFF)
    encoded.append(pid & 0xFF)
    if isinstance(info, str):
        info = info.encode("latin-1", errors="replace")
    encoded.extend(info)
    return bytes(encoded)


def tnc2_to_ax25(raw: str) -> bytes:
    if ":" not in raw or ">" not in raw.split(":", 1)[0]:
        raise ValueError("Pacote TNC2 inválido.")
    header, info = raw.split(":", 1)
    source, remainder = header.split(">", 1)
    parts = [item.strip() for item in remainder.split(",") if item.strip()]
    if not parts:
        raise ValueError("Destino TNC2 ausente.")
    destination = parts[0]
    path = parts[1:]
    return encode_ax25(source, destination, info, path)


def packet_priority_kind(info_text: str) -> str:
    text = str(info_text or "")
    if text.startswith(":") and len(text) >= 11:
        body = text[10:].strip()
        if re.match(r"^(ack|rej)[A-Za-z0-9]{1,5}", body, re.I):
            return "ack"
        return "message"
    if text.startswith("T#") or text.startswith("|"):
        return "telemetry"
    if text.startswith(">"):
        return "status"
    if text.startswith("!") or text.startswith("=") or text.startswith("/") or text.startswith("@"):
        return "position"
    return "other"


def packet_priority(info_text: str) -> int:
    kind = packet_priority_kind(info_text)
    return {"ack": 0, "message": 1, "position": 4, "status": 5, "other": 6, "telemetry": 8}.get(kind, 6)


def parse_message_tnc2(raw: str) -> dict[str, str] | None:
    match = MESSAGE_RE.match(str(raw or ""))
    if not match:
        return None
    return {
        "source": match.group("source").upper().strip(),
        "destination": match.group("dest").upper().strip(),
        "text": match.group("text"),
    }


def strip_internet_path(raw: str) -> str:
    raw = str(raw or "")
    if ":" not in raw or ">" not in raw.split(":", 1)[0]:
        return raw
    header, info = raw.split(":", 1)
    source, rest = header.split(">", 1)
    parts = [part.strip() for part in rest.split(",") if part.strip()]
    if not parts:
        return raw
    kept = [parts[0]]
    for part in parts[1:]:
        upper = part.upper().rstrip("*")
        if upper.startswith("QA") or upper in {"TCPIP", "TCPXX", "NOGATE", "RFONLY"}:
            break
        kept.append(part)
    return f"{source}>{','.join(kept)}:{info}"


def add_igate_q_construct(raw: str, igate_call: str) -> str:
    raw = str(raw or "")
    if ":" not in raw:
        raise ValueError("Pacote APRS inválido para gating.")
    header, info = raw.split(":", 1)
    if any(token.upper().startswith("QA") for token in header.split(",")):
        return raw
    return f"{header},qAR,{normalize_call(igate_call)}:{info}"


def _frame_fingerprint(packet: dict[str, Any]) -> str:
    basis = (
        str(packet.get("source") or "").upper()
        + ">"
        + str(packet.get("destination") or "").upper()
        + ":"
    ).encode("utf-8") + bytes(packet.get("info") or b"")
    return hashlib.sha256(basis).hexdigest()


def digipeat_frame(frame: bytes, own_call: str, cfg: dict[str, Any]) -> tuple[bytes | None, str]:
    packet = decode_ax25(frame)
    own_call = normalize_call(own_call)
    path = list(packet["path"])
    if not path:
        return None, "Sem path para digipeating."

    if any(item["value"].upper() == own_call for item in path):
        return None, "Loop: indicativo local já aparece no path."

    repeated_count = sum(1 for item in path if item["repeated"])
    if repeated_count >= int(cfg.get("digi_max_hops") or 3):
        return None, "Limite de hops repetidos atingido."

    aliases = {item.strip().upper() for item in str(cfg.get("digi_aliases") or "").split(",") if item.strip()}
    profile = str(cfg.get("digi_profile") or "fill")
    selected = -1
    replacement: list[str] = []

    for index, item in enumerate(path):
        if item["repeated"]:
            continue
        value = item["value"].upper()
        wide = WIDE_RE.fullmatch(value)
        if profile == "fill" and value == "WIDE1-1":
            selected = index
            replacement = [own_call + "*"]
            break
        if profile == "wide" and wide:
            selected = index
            remaining = int(wide.group("remaining"))
            n = int(wide.group("n"))
            replacement = [own_call + "*"]
            if remaining > 1:
                replacement.append(f"WIDE{n}-{remaining - 1}")
            break
        if profile == "custom" and value in aliases:
            selected = index
            replacement = [own_call + "*"]
            break

    if selected < 0:
        return None, "Nenhum alias elegível para este perfil de digi."

    new_path: list[str] = []
    for index, item in enumerate(path):
        if index == selected:
            new_path.extend(replacement)
        else:
            new_path.append(item["value"] + ("*" if item["repeated"] else ""))

    if len(new_path) > 8:
        return None, "Path resultante excederia o limite operacional."

    rebuilt = encode_ax25(
        packet["source"], packet["destination"], packet["info"], new_path,
        control=packet["control"], pid=packet["pid"] if packet["pid"] is not None else 0xF0,
    )
    return rebuilt, f"Alias {path[selected]['value']} repetido como {own_call}."


@dataclass
class TNCStatus:
    wanted: bool = False
    connected: bool = False
    state: str = "Desconectado"
    transport: str = ""
    endpoint: str = ""
    last_error: str = ""
    connected_since: str = ""
    last_rx_at: str = ""
    last_tx_at: str = ""
    frames_rx: int = 0
    frames_tx: int = 0
    duplicates_suppressed: int = 0
    tx_paused: bool = False


class TNCService:
    def __init__(self) -> None:
        self._status = TNCStatus()
        self._status_lock = threading.Lock()
        self._transport_lock = threading.Lock()
        self._transport: Any = None
        self._worker: threading.Thread | None = None
        self._tx_worker: threading.Thread | None = None
        self._stop = threading.Event()
        self._tx_queue: queue.PriorityQueue[tuple[int, int, bytes, str, str]] = queue.PriorityQueue()
        self._tx_seq = 0
        self._tx_paused = False
        self._recent_frames: dict[str, float] = {}
        self._recent_is_to_rf: dict[str, float] = {}
        self._source_activity: dict[str, deque[float]] = defaultdict(deque)
        self._tx_activity: deque[float] = deque()

    def status(self) -> dict[str, Any]:
        with self._status_lock:
            payload = asdict(self._status)
        payload["tx_queue"] = self._tx_queue.qsize()
        cfg = get_tnc_config()
        payload["role"] = cfg["role"]
        payload["digi_enabled"] = bool(cfg["digi_enabled"])
        payload["igate_rx_enabled"] = bool(cfg["igate_rx_enabled"])
        payload["igate_tx_enabled"] = bool(cfg["igate_tx_enabled"])
        payload["optimizer_mode"] = cfg["optimizer_mode"]
        return payload

    def _set_status(self, **kwargs: Any) -> None:
        with self._status_lock:
            for key, value in kwargs.items():
                if hasattr(self._status, key):
                    setattr(self._status, key, value)

    def _increment_status(self, key: str, amount: int = 1) -> None:
        with self._status_lock:
            if hasattr(self._status, key):
                setattr(self._status, key, int(getattr(self._status, key) or 0) + int(amount))

    def available_ports(self) -> list[dict[str, str]]:
        if list_ports is None:
            return []
        result = []
        try:
            for port in list_ports.comports():
                result.append({
                    "device": str(port.device or ""),
                    "description": str(port.description or ""),
                    "hwid": str(port.hwid or ""),
                })
        except Exception:
            return []
        return result

    def start_if_configured(self) -> None:
        cfg = get_tnc_config()
        _trim_history(cfg)
        if cfg.get("auto_connect"):
            try:
                self.connect()
            except Exception as exc:
                self._set_status(state="Falha ao iniciar TNC", last_error=str(exc))

    def connect(self) -> None:
        cfg = get_tnc_config()
        normalize_tnc_config(cfg, strict=False)
        if self.status()["connected"]:
            return
        self._set_status(wanted=True, state="Conectando...", last_error="")
        self._stop.clear()
        if not self._worker or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._connection_loop, name="tnc-rx", daemon=True)
            self._worker.start()
        if not self._tx_worker or not self._tx_worker.is_alive():
            self._tx_worker = threading.Thread(target=self._tx_loop, name="tnc-tx", daemon=True)
            self._tx_worker.start()

    def reconnect(self) -> None:
        self.disconnect()
        self.connect()

    def disconnect(self) -> None:
        self._set_status(wanted=False, state="Desconectando...")
        self._stop.set()
        self._close_transport()
        self._set_status(connected=False, state="Desconectado", connected_since="")

    def shutdown(self) -> None:
        self.disconnect()
        for worker in (self._worker, self._tx_worker):
            if worker and worker.is_alive():
                worker.join(timeout=1.5)

    def emergency_stop_tx(self) -> None:
        self._tx_paused = True
        self._set_status(tx_paused=True)
        record_decision("tx", "paused", "Parada imediata de TX acionada pelo usuário.")

    def resume_tx(self) -> None:
        cfg = get_tnc_config()
        if not cfg.get("auto_tx_enabled") or not cfg.get("tx_confirmed"):
            raise PermissionError("TX automático não está habilitado e confirmado na configuração.")
        self._tx_paused = False
        self._set_status(tx_paused=False)
        record_decision("tx", "resumed", "TX automático liberado explicitamente pelo usuário.")

    def _open_transport(self, cfg: dict[str, Any]) -> Any:
        if cfg["transport"] == "tcp":
            sock = socket.create_connection((cfg["tcp_host"], int(cfg["tcp_port"])), timeout=8)
            sock.settimeout(1.0)
            return sock
        if serial is None:
            raise RuntimeError("pyserial não está instalado; KISS Serial indisponível.")
        return serial.Serial(
            port=cfg["serial_port"],
            baudrate=int(cfg["serial_baud"]),
            timeout=1.0,
            write_timeout=2.0,
        )

    def _close_transport(self) -> None:
        with self._transport_lock:
            transport, self._transport = self._transport, None
        if transport is None:
            return
        try:
            if hasattr(transport, "shutdown"):
                transport.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            transport.close()
        except Exception:
            pass

    def _read_transport(self, transport: Any, cfg: dict[str, Any]) -> bytes:
        if cfg["transport"] == "tcp":
            return transport.recv(8192)
        waiting = int(getattr(transport, "in_waiting", 0) or 0)
        return transport.read(max(1, min(waiting or 1, 8192)))

    def _write_transport(self, data: bytes) -> None:
        with self._transport_lock:
            transport = self._transport
            if transport is None:
                raise ConnectionError("TNC desconectado.")
            if hasattr(transport, "sendall"):
                transport.sendall(data)
            else:
                transport.write(data)
                if hasattr(transport, "flush"):
                    transport.flush()

    def _connection_loop(self) -> None:
        decoder = KissStreamDecoder()
        retry = 2
        while self.status()["wanted"] and not self._stop.is_set():
            cfg = get_tnc_config()
            endpoint = (
                f"{cfg['tcp_host']}:{cfg['tcp_port']}" if cfg["transport"] == "tcp"
                else f"{cfg['serial_port']} @ {cfg['serial_baud']}"
            )
            try:
                transport = self._open_transport(cfg)
                with self._transport_lock:
                    self._transport = transport
                self._set_status(
                    connected=True,
                    state="TNC conectado",
                    transport=cfg["transport"],
                    endpoint=endpoint,
                    connected_since=utc_now_iso(),
                    last_error="",
                )
                retry = 2
                while self.status()["wanted"] and not self._stop.is_set():
                    chunk = self._read_transport(transport, cfg)
                    if cfg["transport"] == "tcp" and chunk == b"":
                        raise ConnectionError("KISS TCP encerrou a conexão.")
                    if not chunk:
                        continue
                    for command, payload in decoder.feed(chunk):
                        if (command & 0x0F) != 0 or not payload:
                            continue
                        self._handle_rf_frame(payload)
            except Exception as exc:
                self._set_status(connected=False, state="TNC desconectado", last_error=str(exc))
                diag.log_event("tnc_connection_error", error=str(exc), endpoint=endpoint)
                self._close_transport()
                if not self.status()["wanted"] or self._stop.is_set():
                    break
                time.sleep(retry)
                retry = min(retry * 2, 30)
        self._close_transport()
        self._set_status(connected=False, state="Desconectado", connected_since="")

    def _tx_loop(self) -> None:
        while not self._stop.is_set():
            try:
                priority, seq, frame, reason, raw_tnc2 = self._tx_queue.get(timeout=0.4)
            except queue.Empty:
                continue
            try:
                cfg = get_tnc_config()
                if self._tx_paused:
                    record_decision("tx", "blocked", "TX pausado.", raw_tnc2=raw_tnc2)
                    continue
                if not cfg.get("auto_tx_enabled") or not cfg.get("tx_confirmed"):
                    record_decision("tx", "blocked", "TX automático não habilitado/confirmado.", raw_tnc2=raw_tnc2)
                    continue
                if not self.status()["connected"]:
                    record_decision("tx", "blocked", "TNC desconectado.", raw_tnc2=raw_tnc2)
                    continue
                now = time.monotonic()
                while self._tx_activity and now - self._tx_activity[0] > 60:
                    self._tx_activity.popleft()
                if len(self._tx_activity) >= 60:
                    record_decision("tx", "suppressed", "Limite local de 60 transmissões/min atingido.", raw_tnc2=raw_tnc2)
                    continue
                self._write_transport(kiss_encode(frame))
                self._tx_activity.append(time.monotonic())
                self._set_status(last_tx_at=utc_now_iso())
                self._increment_status("frames_tx")
                try:
                    packet = decode_ax25(frame)
                    record_frame(
                        "TX", packet["tnc2"], source=packet["source"], destination=packet["destination"],
                        path=packet["path_text"], packet_type=packet_priority_kind(packet["info_text"]), reason=reason,
                    )
                except Exception:
                    record_frame("TX", raw_tnc2, reason=reason)
                record_decision("tx", "sent", reason, raw_tnc2=raw_tnc2)
                time.sleep(0.15)
            except Exception as exc:
                self._set_status(last_error=f"TX TNC: {exc}")
                record_decision("tx", "error", str(exc), raw_tnc2=raw_tnc2)
            finally:
                self._tx_queue.task_done()

    def _enqueue(self, frame: bytes, reason: str, *, raw_tnc2: str = "", priority: int | None = None) -> bool:
        cfg = get_tnc_config()
        if self._tx_paused or not cfg.get("auto_tx_enabled") or not cfg.get("tx_confirmed"):
            record_decision("tx", "blocked", "TX automático desligado ou pausado.", raw_tnc2=raw_tnc2)
            return False
        if priority is None:
            try:
                priority = packet_priority(decode_ax25(frame)["info_text"])
            except Exception:
                priority = 6
        self._tx_seq += 1
        self._tx_queue.put((int(priority), self._tx_seq, bytes(frame), reason, raw_tnc2))
        return True

    def _source_rate_allowed(self, source: str, cfg: dict[str, Any]) -> bool:
        now = time.monotonic()
        bucket = self._source_activity[str(source or "").upper()]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        bucket.append(now)
        return len(bucket) <= int(cfg["source_rate_limit_per_minute"])

    def _is_duplicate(self, fingerprint: str, cfg: dict[str, Any]) -> bool:
        now = time.monotonic()
        window = int(cfg["duplicate_window_seconds"])
        self._recent_frames = {key: ts for key, ts in self._recent_frames.items() if now - ts <= window}
        if fingerprint in self._recent_frames:
            return True
        self._recent_frames[fingerprint] = now
        return False

    def _handle_rf_frame(self, frame: bytes) -> None:
        try:
            packet = decode_ax25(frame)
        except Exception as exc:
            record_decision("rx", "ignored", f"Frame AX.25 inválido: {exc}")
            return

        cfg = get_tnc_config()
        fingerprint = _frame_fingerprint(packet)
        duplicate = self._is_duplicate(fingerprint, cfg)
        source = packet["source"]
        destination = packet["destination"]
        kind = packet_priority_kind(packet["info_text"])
        self._set_status(last_rx_at=utc_now_iso())
        self._increment_status("frames_rx")
        record_frame(
            "RX", packet["tnc2"], source=source, destination=destination,
            path=packet["path_text"], packet_type=kind,
            reason="Duplicado observado" if duplicate else "",
        )
        update_heard(packet, packet["tnc2"])

        message = parse_message_tnc2(packet["tnc2"])
        if message:
            record_edge(message["source"], message["destination"], "RF", message["text"])

        try:
            from .aprs_service import service as aprs_service
            aprs_service.ingest_rf_packet(packet["tnc2"])
        except Exception as exc:
            diag.log_event("tnc_rf_ingest_error", error=str(exc))

        if duplicate:
            self._increment_status("duplicates_suppressed")
            record_decision("digi", "suppressed", "Duplicado dentro da janela de supressão.", source=source, destination=destination, raw_tnc2=packet["tnc2"])
            return

        if not self._source_rate_allowed(source, cfg):
            record_decision("digi", "suppressed", "Rate limit por estação excedido.", source=source, destination=destination, raw_tnc2=packet["tnc2"])
            return

        if cfg.get("digi_enabled"):
            self._handle_digipeat(frame, packet, cfg)

        if cfg.get("igate_rx_enabled"):
            self._handle_rf_to_is(packet, cfg)

    def _handle_digipeat(self, frame: bytes, packet: dict[str, Any], cfg: dict[str, Any]) -> None:
        own = self._own_call()
        if not own:
            record_decision("digi", "blocked", "Indicativo local não configurado.", raw_tnc2=packet["tnc2"])
            return
        repeated, reason = digipeat_frame(frame, own, cfg)
        if repeated is None:
            record_decision("digi", "ignored", reason, source=packet["source"], destination=packet["destination"], raw_tnc2=packet["tnc2"])
            return

        if cfg.get("optimizer_mode") == "automatic":
            kind = packet_priority_kind(packet["info_text"])
            now = time.monotonic()
            while self._tx_activity and now - self._tx_activity[0] > 60:
                self._tx_activity.popleft()
            pressure = len(self._tx_activity)
            if pressure >= 30 and kind in {"telemetry", "status"}:
                record_decision(
                    "digi", "suppressed",
                    f"Otimizador automático: pressão local de TX {pressure}/min; tráfego {kind} adiado/suprimido.",
                    source=packet["source"], destination=packet["destination"], raw_tnc2=packet["tnc2"],
                )
                return

        queued = self._enqueue(repeated, "Digipeater: " + reason, raw_tnc2=packet["tnc2"], priority=packet_priority(packet["info_text"]))
        record_decision(
            "digi", "queued" if queued else "blocked", reason if queued else "TX automático não disponível.",
            source=packet["source"], destination=packet["destination"], raw_tnc2=packet["tnc2"],
        )

    def _handle_rf_to_is(self, packet: dict[str, Any], cfg: dict[str, Any]) -> None:
        path_tokens = {
            str(item or "").upper().rstrip("*")
            for item in (packet.get("path_text") or [])
            if str(item or "").strip()
        }
        blocked_tokens = {"NOGATE", "RFONLY"}
        blocked = sorted(path_tokens & blocked_tokens)
        if blocked:
            record_decision(
                "igate_rf_is", "blocked",
                "Path solicita não fazer gating para Internet: " + ", ".join(blocked),
                source=packet["source"], destination=packet["destination"], raw_tnc2=packet["tnc2"],
            )
            return
        if any(token.startswith("QA") or token in {"TCPIP", "TCPXX"} for token in path_tokens):
            record_decision(
                "igate_rf_is", "blocked",
                "Pacote contém marcador de APRS-IS/Internet no path; possível loop de gating.",
                source=packet["source"], destination=packet["destination"], raw_tnc2=packet["tnc2"],
            )
            return
        try:
            own = self._own_call()
            if not own:
                raise RuntimeError("Indicativo local não configurado.")
            gated = add_igate_q_construct(packet["tnc2"], own)
            if len(gated.encode("latin-1", errors="replace")) > 512:
                raise ValueError("Pacote excede o limite operacional após inclusão do q-construct.")
            from .aprs_service import service as aprs_service
            aprs_service.send_igate_packet(gated)
            record_decision(
                "igate_rf_is", "sent", "Pacote RF encaminhado ao APRS-IS.",
                source=packet["source"], destination=packet["destination"], raw_tnc2=packet["tnc2"],
            )
        except Exception as exc:
            record_decision(
                "igate_rf_is", "blocked", str(exc),
                source=packet["source"], destination=packet["destination"], raw_tnc2=packet["tnc2"],
            )

    def handle_is_packet(self, raw: str, parsed: dict[str, Any] | None = None) -> None:
        cfg = get_tnc_config()
        message = parse_message_tnc2(raw)
        if message:
            record_edge(message["source"], message["destination"], "APRS-IS", message["text"])
        if not cfg.get("igate_tx_enabled") or not cfg.get("auto_tx_enabled") or self._tx_paused:
            return
        if not message:
            return

        destination = message["destination"]
        source = message["source"]
        own = self._own_call()
        if not own or destination == own or source == own:
            return
        if not direct_heard_recent(destination, int(cfg["igate_heard_window_minutes"])):
            record_decision(
                "igate_is_rf", "blocked",
                f"Destino {destination} não foi ouvido diretamente por RF na janela configurada.",
                source=source, destination=destination, raw_tnc2=raw,
            )
            return

        cleaned = strip_internet_path(raw)
        fingerprint = hashlib.sha256(cleaned.encode("latin-1", errors="replace")).hexdigest()
        now = time.monotonic()
        window = int(cfg["duplicate_window_seconds"])
        self._recent_is_to_rf = {key: ts for key, ts in self._recent_is_to_rf.items() if now - ts <= window}
        if fingerprint in self._recent_is_to_rf:
            record_decision("igate_is_rf", "suppressed", "Mensagem Internet→RF duplicada.", source=source, destination=destination, raw_tnc2=raw)
            return
        self._recent_is_to_rf[fingerprint] = now

        path = [item.strip() for item in str(cfg.get("igate_rf_path") or "").split(",") if item.strip()]
        third_party = "}" + cleaned
        if len(third_party.encode("latin-1", errors="replace")) > 255:
            record_decision(
                "igate_is_rf", "blocked",
                "Mensagem encapsulada excede o tamanho seguro para transmissão AX.25.",
                source=source, destination=destination, raw_tnc2=raw,
            )
            return
        frame = encode_ax25(own, "APZVHF", third_party, path)
        queued = self._enqueue(frame, f"iGate IS→RF para {destination} ouvido recentemente", raw_tnc2=cleaned, priority=0)
        record_decision(
            "igate_is_rf", "queued" if queued else "blocked",
            f"Destino {destination} ouvido diretamente; mensagem elegível para RF." if queued else "TX automático não disponível.",
            source=source, destination=destination, raw_tnc2=raw,
        )

    def _own_call(self) -> str:
        cfg = db.get_config()
        base = str(cfg.get("callsign") or "").upper().strip()
        if not base:
            return ""
        try:
            ssid = int(cfg.get("ssid") or 0)
        except Exception:
            ssid = 0
        return base + (f"-{ssid}" if ssid else "")

    def optimizer_report(self) -> dict[str, Any]:
        cfg = get_tnc_config()
        stats = tnc_statistics()
        recommendations: list[dict[str, Any]] = []
        for edge in stats["top_edges"][:10]:
            dest = edge["destination"]
            recent = direct_heard_recent(dest, int(cfg["igate_heard_window_minutes"]))
            if recent and edge["medium"] == "APRS-IS":
                recommendations.append({
                    "type": "igate",
                    "severity": "info",
                    "title": f"{dest} presente no RF local",
                    "detail": f"{edge['source']} → {dest}: {edge['interactions']} interações; destino ouvido diretamente. Mensagens IS→RF podem ser elegíveis.",
                })
        if stats["duplicates_suppressed"]:
            recommendations.append({
                "type": "duplicate",
                "severity": "good",
                "title": "Duplicatas suprimidas",
                "detail": f"{stats['duplicates_suppressed']} duplicatas foram evitadas nas últimas 24 h.",
            })
        if not recommendations:
            recommendations.append({
                "type": "observe",
                "severity": "neutral",
                "title": "Coletando relações",
                "detail": "O analisador está aprendendo quem fala com quem. Nenhum ajuste automático é necessário no momento.",
            })
        return {
            "mode": cfg["optimizer_mode"],
            "statistics": stats,
            "recommendations": recommendations,
            "heard": heard_stations(100),
        }


service = TNCService()
