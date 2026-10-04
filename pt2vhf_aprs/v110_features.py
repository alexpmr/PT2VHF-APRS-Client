from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import jsonify, request

from . import __version__
from . import database as db
from . import diagnostics as diag
from .tnc_service import get_tnc_config, probe_transport, service as tnc_service
from .soak_test import soak_manager


QRZ_XML_BASE = "https://xmldata.qrz.com/xml/current/"
QRZ_PUBLIC_PAGE = "https://www.qrz.com/db/{callsign}"
_EXTERNAL_LOCK = threading.Lock()

DEFAULT_EXTERNAL_SETTINGS = {
    "qrz_enabled": False,
    "qrz_username": "",
    "qrz_password": "",
    "qrz_cache_hours": 168,
    "ais_enabled": False,
    "ais_url_template": "",
    "ais_api_key": "",
    "ais_cache_hours": 168,
}


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_schema() -> None:
    with db.connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings_v110(
                key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS external_cache_v110(
                provider TEXT NOT NULL,
                entity_key TEXT NOT NULL,
                payload TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                PRIMARY KEY(provider,entity_key)
            );
            CREATE TABLE IF NOT EXISTS rf_metadata_v110(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                callsign TEXT,
                packet_fingerprint TEXT,
                rssi REAL,
                snr REAL,
                dcd INTEGER,
                frequency_hz REAL,
                channel TEXT,
                provider TEXT NOT NULL DEFAULT '',
                raw_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_rf_metadata_v110_call_time
              ON rf_metadata_v110(callsign,timestamp DESC);
            CREATE TABLE IF NOT EXISTS tm_d700_checks_v110(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                transport TEXT NOT NULL,
                endpoint TEXT,
                serial_baud INTEGER,
                bytes_received INTEGER NOT NULL DEFAULT 0,
                protocol TEXT,
                connected INTEGER NOT NULL DEFAULT 0,
                summary TEXT,
                details_json TEXT NOT NULL DEFAULT '{}'
            );
            """
        )


def _settings() -> dict[str, Any]:
    _ensure_schema()
    with db.connection() as conn:
        row = conn.execute("SELECT payload FROM settings_v110 WHERE key='external'").fetchone()
    data = dict(DEFAULT_EXTERNAL_SETTINGS)
    if row:
        try:
            loaded = json.loads(row["payload"] or "{}")
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception:
            pass
    data["qrz_cache_hours"] = max(1, min(int(data.get("qrz_cache_hours") or 168), 24 * 365))
    data["ais_cache_hours"] = max(1, min(int(data.get("ais_cache_hours") or 168), 24 * 365))
    return data


def _public_settings() -> dict[str, Any]:
    data = _settings()
    data["qrz_password_set"] = bool(data.get("qrz_password"))
    data["ais_api_key_set"] = bool(data.get("ais_api_key"))
    data["qrz_password"] = ""
    data["ais_api_key"] = ""
    return data


def _save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    current = _settings()
    clean = dict(current)
    for key in DEFAULT_EXTERNAL_SETTINGS:
        if key in payload:
            clean[key] = payload[key]
    for secret in ("qrz_password", "ais_api_key"):
        if not str(payload.get(secret) or "").strip():
            clean[secret] = current.get(secret, "")
    clean["qrz_enabled"] = bool(clean.get("qrz_enabled"))
    clean["ais_enabled"] = bool(clean.get("ais_enabled"))
    clean["qrz_username"] = str(clean.get("qrz_username") or "").strip()
    clean["qrz_password"] = str(clean.get("qrz_password") or "")
    clean["ais_url_template"] = str(clean.get("ais_url_template") or "").strip()
    clean["ais_api_key"] = str(clean.get("ais_api_key") or "")
    clean["qrz_cache_hours"] = max(1, min(int(clean.get("qrz_cache_hours") or 168), 8760))
    clean["ais_cache_hours"] = max(1, min(int(clean.get("ais_cache_hours") or 168), 8760))
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO settings_v110(key,payload,updated_at) VALUES('external',?,?)
               ON CONFLICT(key) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at""",
            (json.dumps(clean, ensure_ascii=False, sort_keys=True), _utc()),
        )
    return _public_settings()


def _cache_get(provider: str, key: str, allow_expired: bool = False) -> dict[str, Any] | None:
    _ensure_schema()
    with db.connection() as conn:
        row = conn.execute(
            "SELECT payload,fetched_at,expires_at FROM external_cache_v110 WHERE provider=? AND entity_key=?",
            (provider, key),
        ).fetchone()
    if not row:
        return None
    if not allow_expired and str(row["expires_at"]) < _utc():
        return None
    try:
        data = json.loads(row["payload"])
    except Exception:
        return None
    if isinstance(data, dict):
        data["_cache"] = {"fetched_at": row["fetched_at"], "expires_at": row["expires_at"]}
        return data
    return None


def _cache_put(provider: str, key: str, payload: dict[str, Any], hours: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires = now + timedelta(hours=max(1, int(hours)))
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO external_cache_v110(provider,entity_key,payload,fetched_at,expires_at)
               VALUES(?,?,?,?,?)
               ON CONFLICT(provider,entity_key) DO UPDATE SET
                 payload=excluded.payload,fetched_at=excluded.fetched_at,expires_at=excluded.expires_at""",
            (provider, key, json.dumps(payload, ensure_ascii=False), now.isoformat(), expires.isoformat()),
        )
    out = dict(payload)
    out["_cache"] = {"fetched_at": now.isoformat(), "expires_at": expires.isoformat()}
    return out


def _urlopen(url: str, headers: dict[str, str] | None = None, timeout: float = 8.0) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"PT2VHF-APRS-Client/{__version__}", "Accept": "*/*", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(2_000_000)


def _xml_text_map(element: ET.Element | None) -> dict[str, str]:
    if element is None:
        return {}
    result: dict[str, str] = {}
    for child in list(element):
        name = child.tag.split("}")[-1].strip().lower()
        value = (child.text or "").strip()
        if name and value:
            result[name] = value
    return result


def _qrz_lookup(callsign: str, force: bool = False) -> dict[str, Any]:
    call = re.sub(r"[^A-Z0-9/-]", "", str(callsign or "").upper().strip())
    if not call:
        raise ValueError("Indicativo inválido.")
    cached = None if force else _cache_get("qrz", call)
    if cached:
        return cached
    settings = _settings()
    base_result = {
        "provider": "QRZ.com",
        "callsign": call,
        "profile_url": QRZ_PUBLIC_PAGE.format(callsign=urllib.parse.quote(call)),
        "available": False,
    }
    if not settings.get("qrz_enabled"):
        base_result["status"] = "disabled"
        return base_result
    username = str(settings.get("qrz_username") or "").strip()
    password = str(settings.get("qrz_password") or "")
    if not username or not password:
        base_result["status"] = "credentials_required"
        return base_result

    with _EXTERNAL_LOCK:
        login_url = QRZ_XML_BASE + "?" + urllib.parse.urlencode({
            "username": username,
            "password": password,
            "agent": f"PT2VHF-APRS-Client-{__version__}",
        })
        root = ET.fromstring(_urlopen(login_url))
        session = next((el for el in root.iter() if el.tag.split("}")[-1].lower() == "session"), None)
        session_data = _xml_text_map(session)
        key = session_data.get("key", "")
        if not key:
            raise RuntimeError(session_data.get("error") or "QRZ.com não retornou uma sessão válida.")
        lookup_url = QRZ_XML_BASE + "?" + urllib.parse.urlencode({"s": key, "callsign": call})
        lookup_root = ET.fromstring(_urlopen(lookup_url))
        callsign_el = next((el for el in lookup_root.iter() if el.tag.split("}")[-1].lower() == "callsign"), None)
        data = _xml_text_map(callsign_el)
        if not data:
            err = next((el for el in lookup_root.iter() if el.tag.split("}")[-1].lower() == "error"), None)
            raise LookupError((err.text or "").strip() if err is not None else f"{call} não encontrado no QRZ.com.")

    image = data.get("image") or data.get("imageurl") or ""
    result = {
        **base_result,
        "available": True,
        "status": "ok",
        "name": " ".join(x for x in (data.get("fname"), data.get("name")) if x).strip(),
        "nickname": data.get("nickname", ""),
        "city": data.get("addr2") or data.get("city") or "",
        "state": data.get("state", ""),
        "country": data.get("country", ""),
        "grid": data.get("grid", ""),
        "email": data.get("email", ""),
        "class": data.get("class", ""),
        "image_url": image if image.startswith(("http://", "https://")) else "",
        "source_fields": data,
        "fetched_at": _utc(),
    }
    return _cache_put("qrz", call, result, int(settings["qrz_cache_hours"]))


def _ais_lookup(mmsi: str, imo: str = "", force: bool = False) -> dict[str, Any]:
    key = re.sub(r"\D", "", str(mmsi or ""))
    imo_key = re.sub(r"\D", "", str(imo or ""))
    if not key:
        raise ValueError("MMSI inválido.")
    cache_key = key + (f":{imo_key}" if imo_key else "")
    cached = None if force else _cache_get("ais", cache_key)
    if cached:
        return cached
    settings = _settings()
    result = {"provider": "external", "mmsi": key, "imo": imo_key, "available": False, "image_url": ""}
    if not settings.get("ais_enabled"):
        result["status"] = "disabled"
        return result
    template = str(settings.get("ais_url_template") or "").strip()
    if not template or "{mmsi}" not in template:
        result["status"] = "provider_not_configured"
        return result
    url = template.replace("{mmsi}", urllib.parse.quote(key)).replace("{imo}", urllib.parse.quote(imo_key))
    if not url.startswith(("https://", "http://")):
        raise ValueError("A URL do provedor AIS deve usar HTTP(S).")
    api_key = str(settings.get("ais_api_key") or "")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-Key"] = api_key
    data = json.loads(_urlopen(url, headers=headers).decode("utf-8", errors="replace"))
    if not isinstance(data, dict):
        raise RuntimeError("O provedor AIS não retornou um objeto JSON.")
    image = str(data.get("image_url") or data.get("photo") or data.get("image") or "")
    result.update({
        "available": bool(image),
        "status": "ok",
        "image_url": image if image.startswith(("https://", "http://")) else "",
        "name": data.get("name") or data.get("vessel_name") or "",
        "source_payload": data,
        "fetched_at": _utc(),
    })
    return _cache_put("ais", cache_key, result, int(settings["ais_cache_hours"]))


def record_rf_metadata(
    callsign: str = "",
    *,
    rssi: float | None = None,
    snr: float | None = None,
    dcd: bool | None = None,
    frequency_hz: float | None = None,
    channel: str = "",
    provider: str = "",
    packet_fingerprint: str = "",
    raw: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ensure_schema()
    call = str(callsign or "").upper().strip()
    with db.connection() as conn:
        cur = conn.execute(
            """INSERT INTO rf_metadata_v110(
                 timestamp,callsign,packet_fingerprint,rssi,snr,dcd,frequency_hz,channel,provider,raw_json
               ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                _utc(), call, str(packet_fingerprint or ""), rssi, snr,
                None if dcd is None else int(bool(dcd)), frequency_hz,
                str(channel or ""), str(provider or ""), json.dumps(raw or {}, ensure_ascii=False),
            ),
        )
        rid = int(cur.lastrowid)
    return {
        "id": rid, "callsign": call, "rssi": rssi, "snr": snr, "dcd": dcd,
        "frequency_hz": frequency_hz, "channel": channel, "provider": provider,
    }


def recent_rf_metadata(callsign: str, limit: int = 50) -> list[dict[str, Any]]:
    _ensure_schema()
    with db.connection() as conn:
        rows = conn.execute(
            """SELECT * FROM rf_metadata_v110
               WHERE callsign=? ORDER BY id DESC LIMIT ?""",
            (str(callsign or "").upper().strip(), max(1, min(int(limit), 500))),
        ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["dcd"] = None if item.get("dcd") is None else bool(item["dcd"])
        out.append(item)
    return out


def _tm_d700_probe() -> dict[str, Any]:
    cfg = get_tnc_config()
    probe = probe_transport(cfg)
    status = tnc_service.status()
    result = {
        "timestamp": _utc(),
        "model": "Kenwood TM-D700",
        "mode": "PKT",
        "transport": cfg.get("transport"),
        "endpoint": probe.get("endpoint") or status.get("endpoint") or "",
        "serial_baud": cfg.get("serial_baud"),
        "bytes_received": int(probe.get("bytes_received") or status.get("transport_bytes_rx") or 0),
        "protocol": probe.get("protocol") or "unknown",
        "connected": bool(status.get("connected")),
        "kiss_frames_rx": int(status.get("kiss_frames_rx") or 0),
        "ax25_invalid_rx": int(status.get("ax25_invalid_rx") or 0),
        "tx_transport_frames": int(status.get("transport_frames_tx") or 0),
        "summary": probe.get("summary") or "",
        "physical_validation": False,
        "validation_note": "Compatibilidade física só pode ser confirmada com um TM-D700 real e uma segunda estação/monitor RF.",
    }
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO tm_d700_checks_v110(
                 timestamp,transport,endpoint,serial_baud,bytes_received,protocol,connected,summary,details_json
               ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                result["timestamp"], str(result["transport"] or ""), str(result["endpoint"] or ""),
                int(result["serial_baud"] or 0), result["bytes_received"], str(result["protocol"] or ""),
                int(result["connected"]), str(result["summary"] or ""),
                json.dumps(result, ensure_ascii=False),
            ),
        )
    diag.log_event("tm_d700_probe", **result)
    return result


def register_v110_routes(app) -> None:
    _ensure_schema()

    @app.get("/api/v110/external/settings")
    def api_v110_external_settings():
        return jsonify(_public_settings())

    @app.post("/api/v110/external/settings")
    def api_v110_save_external_settings():
        try:
            return jsonify({"ok": True, "settings": _save_settings(request.get_json(force=True) or {})})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/v110/station-profile/<callsign>")
    def api_v110_station_profile(callsign: str):
        force = request.args.get("refresh") in {"1", "true", "yes"}
        try:
            return jsonify(_qrz_lookup(callsign, force=force))
        except LookupError as exc:
            return jsonify({"provider": "QRZ.com", "callsign": callsign.upper(), "available": False, "status": "not_found", "error": str(exc), "profile_url": QRZ_PUBLIC_PAGE.format(callsign=urllib.parse.quote(callsign.upper()))})
        except Exception as exc:
            cached = _cache_get("qrz", callsign.upper(), allow_expired=True)
            if cached:
                cached["status"] = "stale_cache"
                cached["warning"] = str(exc)
                return jsonify(cached)
            return jsonify({"provider": "QRZ.com", "callsign": callsign.upper(), "available": False, "status": "error", "error": str(exc), "profile_url": QRZ_PUBLIC_PAGE.format(callsign=urllib.parse.quote(callsign.upper()))})

    @app.get("/api/v110/ais-profile/<mmsi>")
    def api_v110_ais_profile(mmsi: str):
        try:
            return jsonify(_ais_lookup(mmsi, request.args.get("imo", ""), request.args.get("refresh") in {"1", "true"}))
        except Exception as exc:
            return jsonify({"provider": "external", "mmsi": mmsi, "available": False, "status": "error", "error": str(exc)})

    @app.post("/api/v110/rf-metadata")
    def api_v110_rf_metadata():
        data = request.get_json(force=True) or {}
        try:
            return jsonify({"ok": True, "metadata": record_rf_metadata(
                data.get("callsign", ""), rssi=data.get("rssi"), snr=data.get("snr"),
                dcd=data.get("dcd"), frequency_hz=data.get("frequency_hz"),
                channel=data.get("channel", ""), provider=data.get("provider", ""),
                packet_fingerprint=data.get("packet_fingerprint", ""), raw=data.get("raw") or {},
            )})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/v110/rf-metadata/<callsign>")
    def api_v110_rf_metadata_call(callsign: str):
        return jsonify(recent_rf_metadata(callsign, request.args.get("limit", 50)))

    @app.post("/api/v110/tm-d700/probe")
    def api_v110_tm_d700_probe():
        try:
            return jsonify({"ok": True, "result": _tm_d700_probe()})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/v110/soak/status")
    def api_v110_soak_status():
        return jsonify(soak_manager.status())

    @app.post("/api/v110/soak/start")
    def api_v110_soak_start():
        data = request.get_json(force=True) or {}
        try:
            return jsonify({"ok": True, "status": soak_manager.start(
                hours=float(data.get("hours") or 24),
                interval_seconds=float(data.get("interval_seconds") or 300),
            )})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/v110/soak/stop")
    def api_v110_soak_stop():
        return jsonify({"ok": True, "status": soak_manager.stop()})

    @app.get("/api/v110/soak/report")
    def api_v110_soak_report():
        return jsonify(soak_manager.report())
