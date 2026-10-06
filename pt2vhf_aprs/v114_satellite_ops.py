from __future__ import annotations

import json
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import jsonify, request

from . import database as db
from .aprs_service import APP_TOCALL, _lat_aprs, _lon_aprs, full_callsign
from .tnc_service import get_tnc_config, normalize_message_rf_path, service as tnc_service
from . import v112_satellites as orbital
from . import v113_satellites as sat113

_lock = threading.Lock()
_scheduler_started = False
_last_tx_monotonic: dict[int, float] = {}

DEFAULT_BEACON_PROFILE = {
    "enabled": False,
    "tx_consent": False,
    "path": "",
    "comment": "SAT",
    "interval_seconds": 60,
    "coverage_only": True,
    "stop_at_los": True,
    "min_elevation_deg": 5.0,
}


def _data_path(name: str) -> Path:
    return Path(db.DB_PATH).parent / name


def _load_json(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except Exception:
        return default


def _save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _profiles() -> dict[str, dict[str, Any]]:
    raw = _load_json(_data_path("satellite_beacon_profiles_v114.json"), {})
    return raw if isinstance(raw, dict) else {}


def get_beacon_profile(norad_id: int) -> dict[str, Any]:
    raw = _profiles().get(str(int(norad_id)), {})
    result = dict(DEFAULT_BEACON_PROFILE)
    if isinstance(raw, dict):
        result.update(raw)
    result["enabled"] = bool(result.get("enabled"))
    result["tx_consent"] = bool(result.get("tx_consent"))
    result["coverage_only"] = bool(result.get("coverage_only", True))
    result["stop_at_los"] = bool(result.get("stop_at_los", True))
    result["path"] = ",".join(normalize_message_rf_path(str(result.get("path") or "")))
    result["comment"] = " ".join(str(result.get("comment") or "SAT").replace("\r", " ").replace("\n", " ").split())[:20]
    result["interval_seconds"] = max(30, min(600, int(result.get("interval_seconds") or 60)))
    result["min_elevation_deg"] = max(0.0, min(90.0, float(result.get("min_elevation_deg") or 0)))
    return result


def save_beacon_profile(norad_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    all_profiles = _profiles()
    merged = dict(get_beacon_profile(norad_id))
    for key in DEFAULT_BEACON_PROFILE:
        if key in payload:
            merged[key] = payload[key]
    # normalize
    merged["path"] = ",".join(normalize_message_rf_path(str(merged.get("path") or "")))
    merged["comment"] = " ".join(str(merged.get("comment") or "SAT").replace("\r", " ").replace("\n", " ").split())[:20]
    merged["interval_seconds"] = max(30, min(600, int(merged.get("interval_seconds") or 60)))
    merged["min_elevation_deg"] = max(0.0, min(90.0, float(merged.get("min_elevation_deg") or 0)))
    merged["enabled"] = bool(merged.get("enabled"))
    merged["tx_consent"] = bool(merged.get("tx_consent"))
    merged["coverage_only"] = bool(merged.get("coverage_only", True))
    merged["stop_at_los"] = bool(merged.get("stop_at_los", True))
    all_profiles[str(int(norad_id))] = merged
    _save_json(_data_path("satellite_beacon_profiles_v114.json"), all_profiles)
    return merged


def _satellite_meta(norad_id: int) -> dict[str, Any]:
    return next(
        (dict(x) for x in sat113.enriched_catalog("all") if int(x.get("norad_id") or 0) == int(norad_id)),
        {"norad_id": int(norad_id), "name": f"NORAD {int(norad_id)}"},
    )


def _observer() -> tuple[float, float, float]:
    cfg = db.get_config()
    lat, lon = cfg.get("latitude"), cfg.get("longitude")
    if lat in (None, "") or lon in (None, ""):
        raise ValueError("Configure latitude e longitude da estação.")
    return float(lat), float(lon), float(cfg.get("altitude") or 0)


def _beacon_payload(profile: dict[str, Any]) -> tuple[str, str]:
    cfg = db.get_config()
    if cfg.get("latitude") is None or cfg.get("longitude") is None:
        raise ValueError("Configure latitude e longitude antes do beacon satélite.")
    table = str(cfg.get("symbol_table") or "/")[:1]
    symbol = str(cfg.get("symbol") or ">")[:1]
    if table not in {"/", "\\"}:
        table = "/"
    comment = str(profile.get("comment") or "SAT")[:20]
    info = f"={_lat_aprs(float(cfg['latitude']))}{table}{_lon_aprs(float(cfg['longitude']))}{symbol}{comment}"
    source = full_callsign(cfg)
    path = str(profile.get("path") or "")
    header = f"{source}>{APP_TOCALL}" + (f",{path}" if path else "")
    return info, f"{header}:{info}"


def beacon_preview(norad_id: int, override: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = dict(get_beacon_profile(norad_id))
    if override:
        profile.update({k: v for k, v in override.items() if k in DEFAULT_BEACON_PROFILE})
        profile["path"] = ",".join(normalize_message_rf_path(str(profile.get("path") or "")))
        profile["comment"] = " ".join(str(profile.get("comment") or "SAT").split())[:20]
    info, raw = _beacon_payload(profile)
    size = len(raw.encode("ascii", errors="replace"))
    warning = ""
    if size > 90:
        warning = "Frame relativamente longo para operação via satélite; reduza path/comentário."
    return {
        "profile": profile,
        "info": info,
        "raw": raw,
        "frame_size_bytes": size,
        "warning": warning,
        "satellite": _satellite_meta(norad_id),
    }


def _ensure_history_table() -> None:
    with db.connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS satellite_beacon_history_v114 (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   timestamp TEXT NOT NULL,
                   norad_id INTEGER NOT NULL,
                   satellite TEXT NOT NULL,
                   frequency_hz INTEGER,
                   path TEXT NOT NULL DEFAULT '',
                   payload TEXT NOT NULL,
                   frame_size_bytes INTEGER NOT NULL DEFAULT 0,
                   status TEXT NOT NULL,
                   error TEXT NOT NULL DEFAULT ''
               )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sat_beacon_v114_time ON satellite_beacon_history_v114(timestamp DESC)"
        )


def _record_beacon(norad_id: int, preview: dict[str, Any], status: str, error: str = "") -> None:
    _ensure_history_table()
    meta = preview.get("satellite") or {}
    frequency = meta.get("downlink_hz") or meta.get("uplink_hz")
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO satellite_beacon_history_v114(
                   timestamp,norad_id,satellite,frequency_hz,path,payload,frame_size_bytes,status,error
               ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                int(norad_id),
                str(meta.get("name") or f"NORAD {norad_id}"),
                int(frequency) if frequency else None,
                str((preview.get("profile") or {}).get("path") or ""),
                str(preview.get("raw") or ""),
                int(preview.get("frame_size_bytes") or 0),
                str(status),
                str(error or ""),
            ),
        )


def _current_satellite_status(norad_id: int) -> dict[str, Any] | None:
    lat, lon, alt = _observer()
    items = orbital.satellite_status(lat, lon, alt)
    return next((x for x in items if int(x.get("norad_id") or 0) == int(norad_id)), None)


def send_satellite_beacon(norad_id: int, *, manual: bool = False) -> dict[str, Any]:
    profile = get_beacon_profile(norad_id)
    if not manual and (not profile["enabled"] or not profile["tx_consent"]):
        raise PermissionError("Beacon satélite automático exige ativação e consentimento explícitos.")
    if manual and not profile["tx_consent"]:
        raise PermissionError("Confirme explicitamente o TX do perfil satélite antes de transmitir.")

    status = _current_satellite_status(norad_id)
    elevation = float((status or {}).get("elevation_deg") or -90.0)
    threshold = float(profile["min_elevation_deg"]) if profile["coverage_only"] else (0.0 if profile["stop_at_los"] else -90.0)
    if elevation < threshold:
        raise PermissionError(
            f"Satélite fora do critério de transmissão: elevação {elevation:.1f}°, mínimo {threshold:.1f}°."
        )
    preview = beacon_preview(norad_id)
    try:
        info = str(preview["info"])
        result = tnc_service.queue_satellite_beacon(
            info,
            path=str(profile.get("path") or ""),
            satellite=str((preview.get("satellite") or {}).get("name") or norad_id),
        )
        _record_beacon(norad_id, preview, "queued")
        _last_tx_monotonic[int(norad_id)] = time.monotonic()
        return {**result, **preview, "elevation_deg": elevation}
    except Exception as exc:
        _record_beacon(norad_id, preview, "error", str(exc))
        raise


def list_beacon_history(limit: int = 100) -> list[dict[str, Any]]:
    _ensure_history_table()
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM satellite_beacon_history_v114 ORDER BY id DESC LIMIT ?",
            (max(1, min(int(limit), 1000)),),
        ).fetchall()
    return [dict(r) for r in rows]


def _eligible_norads(value: str) -> set[int]:
    out: set[int] = set()
    for token in str(value or "").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            out.add(int(token))
        except Exception:
            continue
    return out


def next_selected_aprs_pass(norads: set[int], min_elevation: float = 0.0) -> dict[str, Any] | None:
    if not norads:
        return None
    lat, lon, alt = _observer()
    raw = orbital.satellite_passes(lat, lon, alt, hours=24 * 7, min_elevation=min_elevation)
    rows = [
        p for p in sat113.filter_passes(raw, "aprs", operational_only=True)
        if int(p.get("norad_id") or 0) in norads
    ]
    now = datetime.now(timezone.utc)
    active: list[tuple[datetime, dict[str, Any]]] = []
    future: list[tuple[datetime, dict[str, Any]]] = []
    for item in rows:
        try:
            aos = datetime.fromisoformat(str(item.get("aos")))
            los = datetime.fromisoformat(str(item.get("los")))
            if aos.tzinfo is None:
                aos = aos.replace(tzinfo=timezone.utc)
            if los.tzinfo is None:
                los = los.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if aos <= now <= los:
            active.append((los, item))
        elif aos > now:
            future.append((aos, item))
    chosen = None
    if active:
        chosen = dict(sorted(active, key=lambda x: x[0])[0][1])
        chosen["phase"] = "active"
    elif future:
        chosen = dict(sorted(future, key=lambda x: x[0])[0][1])
        chosen["phase"] = "upcoming"
    return chosen


def _satellite_tokens(norads: set[int]) -> dict[int, set[str]]:
    result: dict[int, set[str]] = {}
    for meta in sat113.enriched_catalog("all"):
        nid = int(meta.get("norad_id") or 0)
        if norads and nid not in norads:
            continue
        tokens = set()
        for value in (meta.get("callsign"), meta.get("name"), meta.get("tle_name")):
            text = str(value or "").upper().strip()
            if text and len(text) >= 3:
                tokens.add(text)
                tokens.update(re.findall(r"[A-Z0-9]{3,}(?:-[0-9]{1,2})?", text))
        if nid == 25544:
            tokens.update({"ARISS", "RS0ISS", "NA1SS"})
        result[nid] = tokens
    return result


def satellite_stations(
    norads: set[int],
    *,
    hours: int = 6,
    rf_only: bool = False,
    messages_only: bool = False,
    limit: int = 200,
) -> list[dict[str, Any]]:
    hours = max(1, min(int(hours), 24 * 30))
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).replace(microsecond=0).isoformat()
    with db.connection() as conn:
        rows = conn.execute(
            """SELECT id,timestamp,from_call,packet_format,raw,medium
               FROM packets
               WHERE timestamp>=? AND COALESCE(from_call,'')<>''
               ORDER BY id DESC LIMIT 6000""",
            (cutoff,),
        ).fetchall()
        msg_rows = conn.execute(
            """SELECT from_call,to_call,message,status,direction,timestamp,tx_medium,tx_path
               FROM messages WHERE message_type='message' AND timestamp>=?
               ORDER BY id DESC LIMIT 5000""",
            (cutoff,),
        ).fetchall()

    station_map = {str(x.get("callsign") or "").upper(): x for x in db.list_stations()}
    msg_count: dict[str, int] = {}
    last_msg: dict[str, dict[str, Any]] = {}
    own = full_callsign(db.get_config()).upper()
    for row in msg_rows:
        item = dict(row)
        peer = str(item.get("from_call") if item.get("direction") == "in" else item.get("to_call") or "").upper()
        if peer == own:
            peer = str(item.get("to_call") or "").upper()
        if not peer:
            continue
        msg_count[peer] = msg_count.get(peer, 0) + 1
        last_msg.setdefault(peer, item)

    tokens = _satellite_tokens(norads)
    aggregated: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = dict(row)
        call = str(item.get("from_call") or "").upper().strip()
        if not call:
            continue
        raw_upper = str(item.get("raw") or "").upper()
        matched: list[int] = []
        for nid, candidates in tokens.items():
            if any(token and token in raw_upper for token in candidates):
                matched.append(nid)
        entry = aggregated.get(call)
        if entry is None:
            station = dict(station_map.get(call) or {})
            entry = {
                "callsign": call,
                "last_heard": item.get("timestamp"),
                "last_raw": item.get("raw"),
                "last_format": item.get("packet_format"),
                "medium": str(item.get("medium") or "APRS-IS").upper(),
                "packet_count": 0,
                "rf_packet_count": 0,
                "aprsis_packet_count": 0,
                "satellite_norads": [],
                "context_match": False,
                "distance_km": station.get("distance_km"),
                "latitude": station.get("latitude"),
                "longitude": station.get("longitude"),
                "name": station.get("name") or "",
                "path": station.get("path") or "",
            }
            aggregated[call] = entry
        entry["packet_count"] += 1
        if str(item.get("medium") or "").upper() == "RF":
            entry["rf_packet_count"] += 1
        else:
            entry["aprsis_packet_count"] += 1
        if matched:
            entry["context_match"] = True
            entry["satellite_norads"] = sorted(set(entry["satellite_norads"]) | set(matched))

    meta = {int(x.get("norad_id") or 0): x for x in sat113.enriched_catalog("all")}
    result = []
    for call, entry in aggregated.items():
        if rf_only and not entry["rf_packet_count"]:
            continue
        if messages_only and not msg_count.get(call):
            continue
        entry["message_count"] = msg_count.get(call, 0)
        entry["last_message"] = last_msg.get(call)
        entry["satellites"] = [
            {
                "norad_id": nid,
                "name": meta.get(nid, {}).get("name") or f"NORAD {nid}",
                "callsign": meta.get(nid, {}).get("callsign") or "",
            }
            for nid in entry["satellite_norads"]
        ]
        result.append(entry)
    result.sort(key=lambda x: (not bool(x.get("context_match")), str(x.get("last_heard") or "")), reverse=False)
    # newest first within context/non-context
    result = sorted(result, key=lambda x: (bool(x.get("context_match")), str(x.get("last_heard") or "")), reverse=True)
    return result[:max(1, min(int(limit), 500))]


def _scheduler_loop() -> None:
    while True:
        try:
            profiles = _profiles()
            for key in list(profiles):
                try:
                    nid = int(key)
                    profile = get_beacon_profile(nid)
                    if not profile["enabled"] or not profile["tx_consent"]:
                        continue
                    last = _last_tx_monotonic.get(nid, 0.0)
                    if time.monotonic() - last < profile["interval_seconds"]:
                        continue
                    status = _current_satellite_status(nid)
                    elevation = float((status or {}).get("elevation_deg") or -90)
                    threshold = profile["min_elevation_deg"] if profile["coverage_only"] else (0.0 if profile["stop_at_los"] else -90.0)
                    if elevation < threshold:
                        continue
                    send_satellite_beacon(nid, manual=False)
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(2)


def start_scheduler() -> None:
    global _scheduler_started
    with _lock:
        if _scheduler_started:
            return
        _scheduler_started = True
        threading.Thread(target=_scheduler_loop, name="satellite-beacon-v114", daemon=True).start()


def register_v114_routes(app) -> None:
    start_scheduler()

    @app.get("/api/v114/satellites/next-pass")
    def api_v114_next_pass():
        try:
            norads = _eligible_norads(request.args.get("norads", ""))
            min_el = float(request.args.get("min_elevation", 0))
            return jsonify({"pass": next_selected_aprs_pass(norads, min_el), "eligible_norads": sorted(norads)})
        except Exception as exc:
            return jsonify({"pass": None, "error": str(exc)}), 400

    @app.get("/api/v114/satellites/stations")
    def api_v114_satellite_stations():
        try:
            return jsonify({
                "items": satellite_stations(
                    _eligible_norads(request.args.get("norads", "")),
                    hours=int(request.args.get("hours", 6)),
                    rf_only=str(request.args.get("rf_only", "")).lower() in {"1", "true", "yes"},
                    messages_only=str(request.args.get("messages_only", "")).lower() in {"1", "true", "yes"},
                    limit=int(request.args.get("limit", 200)),
                )
            })
        except Exception as exc:
            return jsonify({"items": [], "error": str(exc)}), 400

    @app.get("/api/v114/satellites/<int:norad_id>/beacon")
    def api_v114_get_beacon(norad_id: int):
        return jsonify(beacon_preview(norad_id))

    @app.post("/api/v114/satellites/<int:norad_id>/beacon/preview")
    def api_v114_preview_beacon(norad_id: int):
        try:
            return jsonify(beacon_preview(norad_id, request.get_json(silent=True) or {}))
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

    @app.post("/api/v114/satellites/<int:norad_id>/beacon")
    def api_v114_save_beacon(norad_id: int):
        try:
            payload = request.get_json(force=True) or {}
            saved = save_beacon_profile(norad_id, payload)
            return jsonify({"ok": True, **beacon_preview(norad_id), "profile": saved})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/v114/satellites/<int:norad_id>/beacon/send")
    def api_v114_send_beacon(norad_id: int):
        try:
            return jsonify({"ok": True, **send_satellite_beacon(norad_id, manual=True)})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/v114/satellites/beacon/history")
    def api_v114_beacon_history():
        return jsonify(list_beacon_history(request.args.get("limit", 100)))
