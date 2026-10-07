from __future__ import annotations

import hashlib
import json
import queue
import re
import socket
import subprocess
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import APP_TOCALL
from . import database as db
from . import diagnostics as diag
from .agwpe_transport import AGWPEStreamDecoder, AGWPETransport, enable_raw_command, raw_tx_frame

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
    "device_profile": "generic_kiss",
    "serial_protocol": "kiss",
    "packet_rf_baud": 1200,
    "tcp_host": "127.0.0.1",
    "tcp_port": 8001,
    "agwpe_host": "127.0.0.1",
    "agwpe_port": 8000,
    "agwpe_radio_port": 0,
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


def normalize_message_rf_path(value: str) -> list[str]:
    """Valida path manual de mensagem RF sem aceitar marcas de hop já repetido."""
    text = str(value or "").upper().strip().strip(",")
    if not text:
        return []
    parts = [item.strip() for item in text.replace(";", ",").split(",") if item.strip()]
    if len(parts) > 8:
        raise ValueError("Path RF excede o limite de 8 hops/endereço intermediários.")
    normalized: list[str] = []
    for item in parts:
        if "*" in item:
            raise ValueError("Não use * no path de transmissão; o marcador é adicionado pelos digipeaters.")
        call, ssid = split_call(item)
        normalized.append(call + (f"-{ssid}" if ssid else ""))
    return normalized



_SERIAL_CHIPSETS = (
    ("CH9102", re.compile(r"\bCH9102[A-Z0-9-]*\b", re.I)),
    ("CH341", re.compile(r"\bCH341[A-Z0-9-]*\b", re.I)),
    ("CH340", re.compile(r"\bCH340[A-Z0-9-]*\b", re.I)),
    ("CP210x", re.compile(r"\bCP210[0-9A-Z-]*\b", re.I)),
    ("FTDI", re.compile(r"\b(?:FTDI|FT232|FT231|FT2232|FT4232)\b", re.I)),
    ("CDC/ACM", re.compile(r"\b(?:CDC|ACM|USB SERIAL DEVICE)\b", re.I)),
)


def _serial_text(value: Any) -> str:
    return str(value or "").strip()


def _serial_chipset(*values: Any) -> str:
    haystack = " ".join(_serial_text(value) for value in values if value).upper()
    for label, pattern in _SERIAL_CHIPSETS:
        if pattern.search(haystack):
            return label
    return ""


def _parse_vid_pid(*values: Any) -> tuple[str, str]:
    haystack = " ".join(_serial_text(value) for value in values if value).upper()
    # pyserial: "USB VID:PID=1A86:55D4"
    match = re.search(r"VID:PID=([0-9A-F]{4}):([0-9A-F]{4})", haystack)
    if match:
        return match.group(1), match.group(2)
    # Windows PnP: "USB\\VID_1A86&PID_55D4\\..."
    match = re.search(r"VID[_:=]?([0-9A-F]{4}).*?PID[_:=]?([0-9A-F]{4})", haystack)
    if match:
        return match.group(1), match.group(2)
    return "", ""


def _friendly_serial_equipment(record: dict[str, Any]) -> tuple[str, str]:
    combined = " ".join(
        _serial_text(record.get(key))
        for key in ("description", "product", "manufacturer", "name", "hwid", "pnp_device_id")
        if record.get(key)
    )
    upper = combined.upper()
    chipset = _serial_chipset(combined)
    if "RADTEL" in upper and ("950" in upper or "RT-950" in upper or "RT950" in upper):
        return "Radtel RT-950 Pro / TNC UART", chipset
    if "RADTEL" in upper:
        return "Radtel — interface serial", chipset
    description = _serial_text(record.get("description") or record.get("name"))
    generic = {
        "", "N/A", "USB SERIAL PORT", "USB-SERIAL", "USB SERIAL DEVICE",
        "COMMUNICATIONS PORT", "SERIAL PORT",
    }
    if description.upper() not in generic and description:
        return description, chipset
    if chipset:
        return f"USB Serial — {chipset}", chipset
    return "Equipamento serial não identificado", chipset


def _windows_registry_serial_ports() -> list[dict[str, Any]]:
    if sys.platform != "win32":
        return []
    try:
        import winreg  # type: ignore
    except Exception:
        return []
    result: list[dict[str, Any]] = []
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
    except OSError:
        return result
    try:
        index = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, index)
            except OSError:
                break
            index += 1
            device = _serial_text(value)
            if device:
                result.append({
                    "device": device,
                    "description": _serial_text(name),
                    "source": "windows_registry",
                })
    finally:
        try:
            winreg.CloseKey(key)
        except Exception:
            pass
    return result


def _windows_cim_serial_ports() -> list[dict[str, Any]]:
    """Enumera PnP serial via Windows/CIM como fallback ao pyserial."""
    if sys.platform != "win32":
        return []
    script = r"""
$ErrorActionPreference='SilentlyContinue'
$items = @()
Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match '\(COM[0-9]+\)' } | ForEach-Object {
  if ($_.Name -match '\((COM[0-9]+)\)') {
    $items += [PSCustomObject]@{
      device = $Matches[1]
      name = [string]$_.Name
      description = [string]$_.Description
      manufacturer = [string]$_.Manufacturer
      pnp_device_id = [string]$_.PNPDeviceID
      pnp_status = [string]$_.Status
      config_manager_error_code = [int]$_.ConfigManagerErrorCode
      source = 'windows_cim'
    }
  }
}
$items | ConvertTo-Json -Compress
"""
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
        text = (completed.stdout or "").strip()
        if completed.returncode != 0 or not text:
            return []
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            parsed = [parsed]
        return [dict(item) for item in parsed if isinstance(item, dict) and item.get("device")]
    except Exception:
        return []


def _pyserial_ports() -> list[dict[str, Any]]:
    if list_ports is None:
        return []
    result: list[dict[str, Any]] = []
    try:
        ports = list_ports.comports(include_links=True)
    except TypeError:
        ports = list_ports.comports()
    except Exception:
        return result
    try:
        for port in ports:
            vid = getattr(port, "vid", None)
            pid = getattr(port, "pid", None)
            result.append({
                "device": _serial_text(getattr(port, "device", "")),
                "description": _serial_text(getattr(port, "description", "")),
                "name": _serial_text(getattr(port, "name", "")),
                "hwid": _serial_text(getattr(port, "hwid", "")),
                "manufacturer": _serial_text(getattr(port, "manufacturer", "")),
                "product": _serial_text(getattr(port, "product", "")),
                "interface": _serial_text(getattr(port, "interface", "")),
                "serial_number": _serial_text(getattr(port, "serial_number", "")),
                "location": _serial_text(getattr(port, "location", "")),
                "vid": f"{int(vid):04X}" if vid is not None else "",
                "pid": f"{int(pid):04X}" if pid is not None else "",
                "source": "pyserial",
            })
    except Exception:
        return result
    return [item for item in result if item.get("device")]


def _merge_serial_ports(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    source_sets: dict[str, set[str]] = defaultdict(set)
    for raw in records:
        device = _serial_text(raw.get("device")).upper()
        if not device:
            continue
        item = merged.setdefault(device, {
            "device": device,
            "description": "",
            "name": "",
            "manufacturer": "",
            "product": "",
            "interface": "",
            "serial_number": "",
            "location": "",
            "hwid": "",
            "pnp_device_id": "",
            "pnp_status": "",
            "config_manager_error_code": 0,
            "vid": "",
            "pid": "",
        })
        source = _serial_text(raw.get("source"))
        if source:
            source_sets[device].add(source)
        for key in (
            "description", "name", "manufacturer", "product", "interface",
            "serial_number", "location", "hwid", "pnp_device_id", "pnp_status",
        ):
            value = _serial_text(raw.get(key))
            if value and not item.get(key):
                item[key] = value
        try:
            error_code = int(raw.get("config_manager_error_code") or 0)
        except (TypeError, ValueError):
            error_code = 0
        if error_code and not item.get("config_manager_error_code"):
            item["config_manager_error_code"] = error_code
        vid = _serial_text(raw.get("vid")).upper()
        pid = _serial_text(raw.get("pid")).upper()
        parsed_vid, parsed_pid = _parse_vid_pid(
            raw.get("hwid"), raw.get("pnp_device_id"), raw.get("name"), raw.get("description")
        )
        item["vid"] = item.get("vid") or vid or parsed_vid
        item["pid"] = item.get("pid") or pid or parsed_pid

    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        match = re.fullmatch(r"COM(\d+)", str(item.get("device") or ""), re.I)
        return (int(match.group(1)) if match else 99999, str(item.get("device") or ""))

    result: list[dict[str, Any]] = []
    for device, item in merged.items():
        friendly, chipset = _friendly_serial_equipment(item)
        item["equipment"] = friendly
        item["chipset"] = chipset
        item["sources"] = sorted(source_sets.get(device) or [])
        result.append(item)
    return sorted(result, key=sort_key)


def _serial_connection_error(port: str, exc: Exception) -> Exception:
    text = str(exc or "").strip()
    lower = text.lower()
    if any(token in lower for token in ("could not open port", "access is denied", "permissionerror", "permission denied")):
        return PermissionError(
            f"Não foi possível abrir {port}: a porta está ocupada por outro programa ou o Windows negou o acesso."
        )
    if any(token in lower for token in ("file not found", "cannot find", "no such file", "not found")):
        return ConnectionError(f"Porta serial {port} inexistente ou desconectada.")
    return ConnectionError(f"Falha ao abrir a porta serial {port}: {text or exc.__class__.__name__}.")


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
        frame_columns = {row["name"] for row in conn.execute("PRAGMA table_info(tnc_frames)").fetchall()}
        for name, ddl in (
            ("rssi", "REAL"),
            ("snr", "REAL"),
            ("dcd", "INTEGER"),
            ("frequency_hz", "REAL"),
            ("channel", "TEXT"),
            ("metric_source", "TEXT"),
        ):
            if name not in frame_columns:
                conn.execute(f"ALTER TABLE tnc_frames ADD COLUMN {name} {ddl}")

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
    if merged["transport"] not in {"tcp", "serial", "agwpe"}:
        raise ValueError("Transporte TNC deve ser KISS TCP, KISS Serial ou AGWPE.")

    merged["serial_port"] = str(merged.get("serial_port") or "").strip()
    merged["serial_baud"] = int(merged.get("serial_baud") or 9600)
    if merged["serial_baud"] not in {1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400}:
        raise ValueError("Baud rate serial inválido.")

    merged["device_profile"] = str(merged.get("device_profile") or "generic_kiss").lower().strip()
    if merged["device_profile"] not in {"generic_kiss", "kenwood_tm_d700", "kenwood_tm_d710", "kantronics", "agwpe", "generic"}:
        raise ValueError("Perfil de equipamento TNC inválido.")
    merged["serial_protocol"] = str(merged.get("serial_protocol") or "kiss").lower().strip()
    if merged["serial_protocol"] not in {"kiss", "terminal", "agwpe", "auto"}:
        raise ValueError("Protocolo esperado inválido.")
    merged["packet_rf_baud"] = int(merged.get("packet_rf_baud") or 1200)
    if merged["packet_rf_baud"] not in {1200, 9600}:
        raise ValueError("Velocidade packet RF deve ser 1200 ou 9600 baud.")
    if merged["transport"] == "agwpe":
        merged["serial_protocol"] = "agwpe"
    if merged["device_profile"] in {"kenwood_tm_d700", "kenwood_tm_d710", "kantronics"} and merged["serial_protocol"] == "auto":
        merged["serial_protocol"] = "terminal"

    merged["tcp_host"] = str(merged.get("tcp_host") or "127.0.0.1").strip()
    merged["tcp_port"] = int(merged.get("tcp_port") or 8001)
    if not (1 <= merged["tcp_port"] <= 65535):
        raise ValueError("Porta TCP do TNC inválida.")

    merged["agwpe_host"] = str(merged.get("agwpe_host") or "127.0.0.1").strip()
    merged["agwpe_port"] = int(merged.get("agwpe_port") or 8000)
    merged["agwpe_radio_port"] = max(0, min(255, int(merged.get("agwpe_radio_port") or 0)))
    if not (1 <= merged["agwpe_port"] <= 65535):
        raise ValueError("Porta AGWPE inválida.")

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
        if merged["transport"] == "serial" and merged["serial_protocol"] == "terminal":
            raise ValueError("TX automático não é suportado no perfil serial terminal/PKT; use KISS/AGWPE ou mantenha o perfil em monitor.")
        if not merged["tx_confirmed"]:
            raise ValueError("Confirme explicitamente a habilitação de transmissão automática em RF.")
        if not merged["auto_tx_enabled"] and (merged["digi_enabled"] or merged["igate_tx_enabled"]):
            raise ValueError("Digipeater/iGate TX exige a chave Transmissão automática habilitada.")

    if strict and merged["transport"] == "serial" and not merged["serial_port"]:
        raise ValueError("Selecione a porta serial do TNC.")
    if strict and merged["transport"] == "tcp" and not merged["tcp_host"]:
        raise ValueError("Informe o host do KISS TCP.")
    if strict and merged["transport"] == "agwpe" and not merged["agwpe_host"]:
        raise ValueError("Informe o host do AGWPE.")

    return merged



def probe_transport(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Teste não destrutivo do transporte configurado, sem transmitir RF."""
    cfg = normalize_tnc_config(payload or get_tnc_config(), strict=False)
    started = time.monotonic()
    transport = str(cfg.get("transport") or "")
    result: dict[str, Any] = {
        "ok": False,
        "transport": transport,
        "endpoint": "",
        "elapsed_ms": None,
        "bytes_received": 0,
        "protocol": "unknown",
        "expected_protocol": str(cfg.get("serial_protocol") or ("agwpe" if transport == "agwpe" else "kiss")),
        "device_profile": str(cfg.get("device_profile") or "generic_kiss"),
        "serial_baud": int(cfg.get("serial_baud") or 9600),
        "packet_rf_baud": int(cfg.get("packet_rf_baud") or 1200),
        "sample_hex": "",
        "sample_ascii": "",
        "summary": "",
    }
    current_service = globals().get("service")
    if current_service is not None:
        try:
            live = current_service.status()
        except Exception:
            live = {}
        if live.get("connected"):
            result.update({
                "ok": True,
                "endpoint": str(live.get("endpoint") or ""),
                "bytes_received": int(live.get("transport_bytes_rx") or 0),
                "protocol": "agwpe" if transport == "agwpe" else ("kiss" if int(live.get("kiss_frames_rx") or 0) > 0 else ("terminal-bytes" if str(cfg.get("serial_protocol") or "") == "terminal" and int(live.get("transport_bytes_rx") or 0) > 0 else "transport-open")),
                "sample_hex": str(live.get("last_transport_sample_hex") or ""),
                "sample_ascii": str(live.get("last_transport_sample_ascii") or ""),
                "summary": "TNC já está conectado; teste usa o estado da sessão atual para não disputar a porta/transporte.",
                "live_status": live,
                "elapsed_ms": 0.0,
            })
            return result
    handle = None
    try:
        if transport == "serial":
            if serial is None:
                raise RuntimeError("pyserial não está instalado.")
            if not cfg.get("serial_port"):
                raise ValueError("Porta serial não configurada.")
            result["endpoint"] = f"{cfg['serial_port']} @ {cfg['serial_baud']}"
            handle = serial.Serial(
                port=cfg["serial_port"],
                baudrate=int(cfg["serial_baud"]),
                timeout=0.35,
                write_timeout=1.0,
            )
            waiting = int(getattr(handle, "in_waiting", 0) or 0)
            sample = handle.read(min(max(waiting, 1), 4096)) if waiting else b""
            result["bytes_received"] = len(sample)
            if sample:
                safe = bytes(sample[:128])
                result["sample_hex"] = safe.hex(" ")
                result["sample_ascii"] = "".join(chr(b) if 32 <= b <= 126 else "." for b in safe)
                decoder = KissStreamDecoder()
                frames = decoder.feed(sample)
                if frames:
                    result["protocol"] = "kiss"
                elif str(cfg.get("serial_protocol") or "") == "terminal":
                    result["protocol"] = "terminal-bytes"
                else:
                    result["protocol"] = "bytes-unrecognized"
            else:
                result["protocol"] = "serial-open"
            result["ok"] = True
            result["summary"] = (
                f"Serial aberta em {result['endpoint']}; "
                + (f"{len(sample)} byte(s) lido(s), protocolo {result['protocol']}." if sample else "sem bytes disponíveis durante o teste.")
            )
        elif transport == "tcp":
            result["endpoint"] = f"{cfg['tcp_host']}:{cfg['tcp_port']}"
            handle = socket.create_connection((cfg["tcp_host"], int(cfg["tcp_port"])), timeout=3.0)
            handle.settimeout(0.35)
            try:
                sample = handle.recv(4096)
            except socket.timeout:
                sample = b""
            result["bytes_received"] = len(sample)
            if sample:
                decoder = KissStreamDecoder()
                frames = decoder.feed(sample)
                result["protocol"] = "kiss" if frames else "bytes-unrecognized"
            else:
                result["protocol"] = "kiss-tcp-open"
            result["ok"] = True
            result["summary"] = f"KISS TCP acessível em {result['endpoint']}."
        elif transport == "agwpe":
            result["endpoint"] = f"{cfg['agwpe_host']}:{cfg['agwpe_port']}"
            handle = AGWPETransport(cfg["agwpe_host"], int(cfg["agwpe_port"]), timeout=3.0)
            handle.sendall(enable_raw_command())
            result["protocol"] = "agwpe"
            result["ok"] = True
            result["summary"] = f"AGWPE acessível em {result['endpoint']}; raw mode solicitado sem transmitir RF."
        else:
            raise ValueError(f"Transporte não suportado: {transport}")
    except Exception as exc:
        result["summary"] = str(exc)
        result["error"] = str(exc)
    finally:
        try:
            if handle is not None:
                handle.close()
        except Exception:
            pass
        result["elapsed_ms"] = round((time.monotonic() - started) * 1000.0, 1)
    diag.log_event("tnc_transport_probe", **result)
    return result

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
    rssi: float | None = None,
    snr: float | None = None,
    dcd: bool | None = None,
    frequency_hz: float | None = None,
    channel: str = "",
    metric_source: str = "",
) -> None:
    _ensure_schema()
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO tnc_frames(
                 timestamp,direction,medium,source,destination,path,packet_type,raw_tnc2,reason,
                 rssi,snr,dcd,frequency_hz,channel,metric_source
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                utc_now_iso(), direction.upper(), medium.upper(), source.upper(), destination.upper(),
                json.dumps(path or [], ensure_ascii=False), packet_type, raw_tnc2, reason,
                rssi, snr, None if dcd is None else int(bool(dcd)), frequency_hz,
                str(channel or ""), str(metric_source or ""),
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


def update_heard(packet: dict[str, Any], raw_tnc2: str) -> bool:
    source = str(packet.get("source") or "").upper().strip()
    if not source:
        return False
    path = packet.get("path") or []
    direct = 1 if not any(bool(item.get("repeated")) for item in path) else 0
    packet_type = packet_priority_kind(packet.get("info_text") or "")
    now = utc_now_iso()
    with db.connection() as conn:
        existed = conn.execute("SELECT 1 FROM tnc_heard WHERE callsign=?", (source,)).fetchone() is not None
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
    return not existed


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
    """Lista estações com evidência RF persistida no TNC e/ou no pipeline APRS."""
    _ensure_schema()
    limit = max(1, min(int(limit or 250), 2000))
    cfg = db.get_config()
    own_lat, own_lon = cfg.get("latitude"), cfg.get("longitude")
    own_valid = db._valid_geo_position(own_lat, own_lon)

    with db.connection() as conn:
        heard_rows = conn.execute(
            "SELECT * FROM tnc_heard ORDER BY last_heard DESC"
        ).fetchall()
        rf_rows = conn.execute(
            """SELECT UPPER(TRIM(from_call)) AS callsign,
                      MAX(timestamp) AS last_rf_packet,
                      COUNT(*) AS rf_packet_count
                 FROM packets
                WHERE medium='RF'
                  AND from_call IS NOT NULL
                  AND TRIM(from_call) <> ''
                GROUP BY UPPER(TRIM(from_call))"""
        ).fetchall()
        station_rows = conn.execute(
            """SELECT callsign,latitude,longitude,last_heard
                 FROM stations
                WHERE callsign IS NOT NULL"""
        ).fetchall()

    merged: dict[str, dict[str, Any]] = {}
    for row in heard_rows:
        item = dict(row)
        call = str(item.get("callsign") or "").upper().strip()
        if not call:
            continue
        try:
            item["path"] = json.loads(item.get("path") or "[]")
        except Exception:
            item["path"] = []
        item["rf_packet_count"] = 0
        item["rf_evidence"] = "tnc_heard"
        item["direct_known"] = True
        merged[call] = item

    for row in rf_rows:
        call = str(row["callsign"] or "").upper().strip()
        if not call:
            continue
        item = merged.setdefault(call, {
            "callsign": call,
            "last_heard": str(row["last_rf_packet"] or ""),
            "last_direct_heard": None,
            "direct": 0,
            "path": [],
            "heard_count": 0,
            "last_packet_type": "",
            "last_raw": "",
            "rf_evidence": "packets",
            "direct_known": False,
        })
        item["rf_packet_count"] = int(row["rf_packet_count"] or 0)
        if str(row["last_rf_packet"] or "") > str(item.get("last_heard") or ""):
            item["last_heard"] = str(row["last_rf_packet"] or "")
        if item.get("rf_evidence") == "tnc_heard":
            item["rf_evidence"] = "tnc_heard+packets"

    station_by_call = {
        str(row["callsign"] or "").upper().strip(): dict(row)
        for row in station_rows
        if str(row["callsign"] or "").strip()
    }
    for call, item in merged.items():
        station = station_by_call.get(call) or {}
        item["latitude"] = station.get("latitude")
        item["longitude"] = station.get("longitude")
        item["distance_km"] = None
        if own_valid and db._valid_geo_position(item.get("latitude"), item.get("longitude")):
            item["distance_km"] = round(db.haversine_km(
                float(own_lat), float(own_lon),
                float(item["latitude"]), float(item["longitude"]),
            ), 2)

    result = sorted(
        merged.values(),
        key=lambda item: str(item.get("last_heard") or ""),
        reverse=True,
    )[:limit]
    return result


def tnc_reception_stats(hours: int = 24) -> dict[str, Any]:
    """Resumo RF/APRS-IS preservando os dois meios e um total lógico deduplicado."""
    _ensure_schema()
    hours = int(hours or 0)
    cutoff = None
    if hours > 0:
        hours = max(1, min(hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).replace(microsecond=0).isoformat()

    packet_where = "WHERE 1=1"
    packet_params: list[Any] = []
    frame_where = "WHERE direction='RX'"
    frame_params: list[Any] = []
    if cutoff:
        packet_where += " AND timestamp>=?"
        packet_params.append(cutoff)
        frame_where += " AND timestamp>=?"
        frame_params.append(cutoff)

    with db.connection() as conn:
        medium_rows = conn.execute(
            f"""SELECT medium, COUNT(*) AS packets,
                       COUNT(DISTINCT UPPER(TRIM(from_call))) AS stations
                  FROM packets
                  {packet_where}
                 GROUP BY medium""",
            packet_params,
        ).fetchall()
        by_medium = {
            str(row["medium"] or "APRS-IS").upper(): {
                "packets": int(row["packets"] or 0),
                "stations": int(row["stations"] or 0),
            }
            for row in medium_rows
        }
        both_stations = int(conn.execute(
            f"""SELECT COUNT(*) FROM (
                    SELECT UPPER(TRIM(from_call)) AS callsign
                      FROM packets
                      {packet_where}
                     AND from_call IS NOT NULL AND TRIM(from_call)<>''
                     GROUP BY UPPER(TRIM(from_call))
                    HAVING SUM(CASE WHEN medium='RF' THEN 1 ELSE 0 END)>0
                       AND SUM(CASE WHEN medium='APRS-IS' THEN 1 ELSE 0 END)>0
                )""",
            packet_params,
        ).fetchone()[0] or 0)
        logical_packets = int(conn.execute(
            f"""WITH ordered AS (
                    SELECT id,timestamp,
                           COALESCE(NULLIF(rx_fingerprint,''), 'id:' || id) AS fp,
                           LAG(timestamp) OVER (
                               PARTITION BY COALESCE(NULLIF(rx_fingerprint,''), 'id:' || id)
                               ORDER BY timestamp,id
                           ) AS previous_timestamp
                      FROM packets
                      {packet_where}
                )
                SELECT COUNT(*)
                  FROM ordered
                 WHERE previous_timestamp IS NULL
                    OR (strftime('%s', timestamp) - strftime('%s', previous_timestamp)) > 10""",
            packet_params,
        ).fetchone()[0] or 0)
        frame_row = conn.execute(
            f"""SELECT COUNT(*) AS frames,
                       COUNT(DISTINCT UPPER(TRIM(source))) AS stations
                  FROM tnc_frames
                  {frame_where}""",
            frame_params,
        ).fetchone()
        direct_sql = (
            "SELECT COUNT(*) FROM tnc_heard WHERE last_direct_heard>=?"
            if cutoff
            else "SELECT COUNT(*) FROM tnc_heard WHERE last_direct_heard IS NOT NULL"
        )
        direct_stations = int(conn.execute(
            direct_sql,
            ([cutoff] if cutoff else []),
        ).fetchone()[0] or 0)

    rf = by_medium.get("RF", {"packets": 0, "stations": 0})
    aprsis = by_medium.get("APRS-IS", {"packets": 0, "stations": 0})
    return {
        "hours": 0 if cutoff is None else hours,
        "rf_packets": int(rf["packets"]),
        "rf_unique_stations": max(int(rf["stations"]), int(frame_row["stations"] or 0)),
        "rf_frames_received": int(frame_row["frames"] or 0),
        "rf_direct_stations": direct_stations,
        "aprsis_packets": int(aprsis["packets"]),
        "aprsis_unique_stations": int(aprsis["stations"]),
        "both_media_stations": both_stations,
        "logical_packets_deduplicated": logical_packets,
    }


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
    last_transport_rx_at: str = ""
    last_transport_tx_at: str = ""
    frames_rx: int = 0
    frames_tx: int = 0
    transport_bytes_rx: int = 0
    transport_bytes_tx: int = 0
    kiss_frames_rx: int = 0
    invalid_frames_rx: int = 0
    last_transport_sample_hex: str = ""
    last_transport_sample_ascii: str = ""
    last_rx_error: str = ""
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
        self._ports_lock = threading.Lock()
        self._ports_cache: list[dict[str, Any]] = []
        self._ports_cache_at = 0.0
        self._ports_signature = ""

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
        payload["device_profile"] = cfg.get("device_profile", "generic_kiss")
        payload["expected_protocol"] = cfg.get("serial_protocol", "kiss")
        payload["serial_baud"] = cfg.get("serial_baud", 9600)
        payload["packet_rf_baud"] = cfg.get("packet_rf_baud", 1200)
        payload["dcd"] = None
        payload["rf_metric_source"] = ""
        if payload.get("connected") and str(cfg.get("transport") or "") == "serial":
            try:
                with self._transport_lock:
                    transport = self._transport
                    if transport is not None and hasattr(transport, "cd"):
                        payload["dcd"] = bool(transport.cd)
                        payload["rf_metric_source"] = "serial_modem_status"
            except Exception:
                payload["dcd"] = None
        connected_since = str(payload.get("connected_since") or "")
        # Reconcilia os contadores em memória com a evidência persistida da sessão.
        # Isso evita a interface permanecer em zero quando um caminho de ingestão
        # registrou frames corretamente, mas o acumulador transitório se perdeu.
        if connected_since:
            try:
                with db.connection() as conn:
                    if conn.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='tnc_frames'"
                    ).fetchone():
                        row = conn.execute(
                            """SELECT
                                   SUM(CASE WHEN direction='RX' THEN 1 ELSE 0 END) AS rx,
                                   SUM(CASE WHEN direction='TX' THEN 1 ELSE 0 END) AS tx,
                                   MAX(CASE WHEN direction='RX' THEN timestamp END) AS last_rx,
                                   MAX(CASE WHEN direction='TX' THEN timestamp END) AS last_tx
                               FROM tnc_frames WHERE timestamp>=?""",
                            (connected_since,),
                        ).fetchone()
                        persisted_rx = int(row["rx"] or 0)
                        persisted_tx = int(row["tx"] or 0)
                        payload["session_persisted_frames_rx"] = persisted_rx
                        payload["session_persisted_frames_tx"] = persisted_tx
                        payload["frames_rx"] = max(int(payload.get("frames_rx") or 0), persisted_rx)
                        payload["frames_tx"] = max(int(payload.get("frames_tx") or 0), persisted_tx)
                        if row["last_rx"] and not payload.get("last_rx_at"):
                            payload["last_rx_at"] = str(row["last_rx"])
                        if row["last_tx"] and not payload.get("last_tx_at"):
                            payload["last_tx_at"] = str(row["last_tx"])
            except Exception as exc:
                diag.log_event("tnc_status_counter_reconcile_error", error=str(exc))
        last_valid_rx = str(payload.get("last_rx_at") or "")
        last_tx = str(payload.get("last_tx_at") or "")
        valid_rx_this_session = bool(last_valid_rx and (not connected_since or last_valid_rx >= connected_since))
        tx_this_session = bool(last_tx and (not connected_since or last_tx >= connected_since))
        if not payload.get("connected"):
            payload["rx_state"] = "disconnected"
            payload["tx_state"] = "disconnected"
        else:
            if valid_rx_this_session:
                payload["rx_state"] = "active"
            elif int(payload.get("kiss_frames_rx") or 0) > 0 or int(payload.get("invalid_frames_rx") or 0) > 0:
                payload["rx_state"] = "invalid"
            elif int(payload.get("transport_bytes_rx") or 0) > 0:
                if str(cfg.get("serial_protocol") or "") == "terminal":
                    payload["rx_state"] = "terminal_bytes_active"
                else:
                    payload["rx_state"] = "bytes_without_kiss"
            else:
                payload["rx_state"] = "waiting"
            payload["tx_state"] = "delivered" if tx_this_session else "waiting"
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

    def available_ports(self, *, force: bool = False, full_scan: bool = True) -> list[dict[str, Any]]:
        now = time.monotonic()
        with self._ports_lock:
            cached_snapshot = [dict(item) for item in self._ports_cache]
            cached_age = now - self._ports_cache_at if self._ports_cache_at else float("inf")
            if full_scan and not force and cached_snapshot and cached_age < 60.0:
                return cached_snapshot

        # Lightweight sources are safe for periodic polling.
        records: list[dict[str, Any]] = []
        records.extend(_pyserial_ports())
        if sys.platform == "win32":
            records.extend(_windows_registry_serial_ports())

        if full_scan and sys.platform == "win32":
            # CIM/PnP is intentionally reserved for an explicit/deep scan.
            # Spawning PowerShell every few seconds can consume substantial CPU.
            records.extend(_windows_cim_serial_ports())
        elif cached_snapshot:
            # Preserve richer metadata learned by the last deep scan, but only
            # for COM ports that still exist in the lightweight sources.
            present = {
                _serial_text(item.get("device")).upper()
                for item in records
                if _serial_text(item.get("device"))
            }
            for item in cached_snapshot:
                if _serial_text(item.get("device")).upper() in present:
                    cached = dict(item)
                    cached["source"] = "cached_metadata"
                    records.append(cached)

        ports = _merge_serial_ports(records)

        cfg = get_tnc_config()
        status = self.status()
        configured = _serial_text(cfg.get("serial_port")).upper()
        connected_port = ""
        if status.get("connected") and str(status.get("transport") or "") == "serial":
            endpoint = str(status.get("endpoint") or "")
            connected_port = endpoint.split("@", 1)[0].strip().upper()

        for item in ports:
            device = str(item.get("device") or "").upper()
            item["configured"] = bool(configured and device == configured)
            item["connected"] = bool(connected_port and device == connected_port)
            code = int(item.get("config_manager_error_code") or 0)
            if item["connected"]:
                item["status"] = "connected"
                item["status_label"] = "Conectado pelo Client"
            elif code:
                item["status"] = "device_error"
                item["status_label"] = f"Erro do dispositivo (código {code})"
            elif item["configured"]:
                item["status"] = "configured"
                item["status_label"] = "Configurado"
            else:
                item["status"] = "detected"
                item["status_label"] = "Detectado"

        signature = json.dumps(
            [{key: item.get(key) for key in ("device", "description", "manufacturer", "vid", "pid", "serial_number")} for item in ports],
            ensure_ascii=False,
            sort_keys=True,
        )
        with self._ports_lock:
            changed = signature != self._ports_signature
            self._ports_signature = signature
            self._ports_cache = [dict(item) for item in ports]
            self._ports_cache_at = now

        if changed or force:
            diag.log_event(
                "tnc_serial_scan",
                force=force,
                full_scan=full_scan,
                count=len(ports),
                ports=ports,
            )
        return ports

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
        if cfg["transport"] == "agwpe":
            transport = AGWPETransport(cfg["agwpe_host"], int(cfg["agwpe_port"]))
            transport.sendall(enable_raw_command())
            return transport
        if cfg["transport"] == "tcp":
            sock = socket.create_connection((cfg["tcp_host"], int(cfg["tcp_port"])), timeout=8)
            sock.settimeout(1.0)
            return sock
        if serial is None:
            raise RuntimeError("pyserial não está instalado; KISS Serial indisponível.")
        try:
            return serial.Serial(
                port=cfg["serial_port"],
                baudrate=int(cfg["serial_baud"]),
                timeout=1.0,
                write_timeout=2.0,
            )
        except Exception as exc:
            raise _serial_connection_error(str(cfg["serial_port"]), exc) from exc

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

    def _read_transport(self, transport: Any, cfg: dict[str, Any]) -> bytes | None:
        if cfg["transport"] in {"tcp", "agwpe"}:
            try:
                return transport.recv(8192)
            except socket.timeout:
                return None
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
                written = transport.write(data)
                if written is not None and int(written) < len(data):
                    raise IOError(f"Escrita serial parcial: {written}/{len(data)} bytes.")
                if hasattr(transport, "flush"):
                    transport.flush()
            self._set_status(last_transport_tx_at=utc_now_iso())
            self._increment_status("transport_bytes_tx", len(data))

    def _connection_loop(self) -> None:
        decoder = KissStreamDecoder()
        agw_decoder = AGWPEStreamDecoder()
        retry = 2
        while self.status()["wanted"] and not self._stop.is_set():
            cfg = get_tnc_config()
            endpoint = (
                f"{cfg['agwpe_host']}:{cfg['agwpe_port']} / radio {cfg['agwpe_radio_port']}" if cfg["transport"] == "agwpe"
                else f"{cfg['tcp_host']}:{cfg['tcp_port']}" if cfg["transport"] == "tcp"
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
                    last_transport_rx_at="",
                    last_transport_tx_at="",
                    transport_bytes_rx=0,
                    transport_bytes_tx=0,
                    kiss_frames_rx=0,
                    invalid_frames_rx=0,
                    last_transport_sample_hex="",
                    last_transport_sample_ascii="",
                    last_rx_error="",
                )
                retry = 2
                while self.status()["wanted"] and not self._stop.is_set():
                    chunk = self._read_transport(transport, cfg)
                    if chunk is None:
                        continue
                    if cfg["transport"] in {"tcp", "agwpe"} and chunk == b"":
                        raise ConnectionError(("AGWPE" if cfg["transport"] == "agwpe" else "KISS TCP") + " encerrou a conexão.")
                    if not chunk:
                        continue
                    safe_sample = bytes(chunk[:128])
                    self._set_status(
                        last_transport_rx_at=utc_now_iso(),
                        last_transport_sample_hex=safe_sample.hex(" "),
                        last_transport_sample_ascii="".join(chr(b) if 32 <= b <= 126 else "." for b in safe_sample),
                    )
                    self._increment_status("transport_bytes_rx", len(chunk))
                    if cfg["transport"] == "agwpe":
                        for agw_frame in agw_decoder.feed(chunk):
                            if agw_frame.kind != "K" or not agw_frame.data:
                                continue
                            self._increment_status("kiss_frames_rx")
                            self._handle_rf_frame(agw_frame.data)
                    else:
                        for command, payload in decoder.feed(chunk):
                            if (command & 0x0F) != 0 or not payload:
                                continue
                            self._increment_status("kiss_frames_rx")
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
                wire = raw_tx_frame(frame, port=int(cfg.get("agwpe_radio_port") or 0)) if cfg.get("transport") == "agwpe" else kiss_encode(frame)
                self._write_transport(wire)
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

    def queue_local_message(self, destination: str, text: str, msg_id: str, path: str = "") -> dict[str, Any]:
        """Enfileira uma mensagem APRS originada localmente para transmissão RF."""
        status = self.status()
        cfg = get_tnc_config()
        if not status.get("connected"):
            raise ConnectionError("TNC/RF desconectado. Conecte o TNC ou escolha APRS-IS.")
        if self._tx_paused or status.get("tx_paused"):
            raise PermissionError("TX RF está pausado. Libere a transmissão no painel TNC / RF.")
        if not cfg.get("auto_tx_enabled") or not cfg.get("tx_confirmed"):
            raise PermissionError("TX RF não está habilitado e confirmado em TNC / RF.")

        source = self._own_call()
        if not source:
            raise ValueError("Configure o indicativo/SSID local antes de transmitir por RF.")
        split_call(destination)
        destination = normalize_call(destination)
        path_items = normalize_message_rf_path(path)
        clean = " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split())
        if not clean:
            raise ValueError("Mensagem RF vazia.")
        msg_id = str(msg_id or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9]{1,5}", msg_id):
            raise ValueError("ID APRS da mensagem RF inválido.")

        info = f":{destination:<9}:{clean}{{{msg_id}"
        frame = encode_ax25(source, APP_TOCALL, info, path_items)
        header = f"{source}>{APP_TOCALL}" + (("," + ",".join(path_items)) if path_items else "")
        raw_tnc2 = f"{header}:{info}"
        if not self._enqueue(frame, f"Mensagem local RF para {destination}", raw_tnc2=raw_tnc2, priority=1):
            raise PermissionError("A mensagem RF foi bloqueada pelas regras de transmissão do TNC.")
        record_decision(
            "message_rf", "queued",
            f"Mensagem local para {destination}; path {','.join(path_items) if path_items else 'direto'}.",
            source=source, destination=destination, raw_tnc2=raw_tnc2,
        )
        return {
            "queued": True,
            "source": source,
            "destination": destination,
            "path": ",".join(path_items),
            "raw": raw_tnc2,
        }

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
            self._increment_status("invalid_frames_rx")
            self._set_status(last_rx_error=str(exc))
            record_decision("rx", "ignored", f"Frame AX.25 inválido: {exc}")
            diag.log_event("tnc_invalid_ax25_frame", error=str(exc), frame_length=len(frame))
            return

        cfg = get_tnc_config()
        fingerprint = _frame_fingerprint(packet)
        duplicate = self._is_duplicate(fingerprint, cfg)
        source = packet["source"]
        destination = packet["destination"]
        kind = packet_priority_kind(packet["info_text"])
        self._set_status(last_rx_at=utc_now_iso(), last_rx_error="")
        self._increment_status("frames_rx")
        record_frame(
            "RX", packet["tnc2"], source=source, destination=destination,
            path=packet["path_text"], packet_type=kind,
            reason="Duplicado observado" if duplicate else "",
        )
        new_rf_station = update_heard(packet, packet["tnc2"])
        if new_rf_station:
            diag.log_event(
                "tnc_rf_station_heard",
                callsign=source,
                direct=not any(bool(item.get("repeated")) for item in (packet.get("path") or [])),
                path=packet.get("path_text") or [],
            )
        if int(self.status().get("frames_rx") or 0) % 100 == 0:
            try:
                summary = tnc_reception_stats(24)
                diag.log_event("tnc_rf_rx_summary", **summary)
            except Exception as exc:
                diag.log_event("tnc_rf_summary_error", error=str(exc))

        if duplicate:
            self._increment_status("duplicates_suppressed")
            record_decision("digi", "suppressed", "Duplicado dentro da janela de supressão.", source=source, destination=destination, raw_tnc2=packet["tnc2"])
            return

        message = parse_message_tnc2(packet["tnc2"])
        if message:
            record_edge(message["source"], message["destination"], "RF", message["text"])

        try:
            from .aprs_service import service as aprs_service
            aprs_service.ingest_rf_packet(packet["tnc2"])
        except Exception as exc:
            diag.log_event("tnc_rf_ingest_error", error=str(exc))

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
