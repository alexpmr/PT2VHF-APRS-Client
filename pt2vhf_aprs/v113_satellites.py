from __future__ import annotations

import json
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import jsonify, request

from . import __version__
from . import database as db
from . import v112_satellites as orbital

AMSAT_NASABARE_TLE = "https://www.amsat.org/amsat/ftp/keps/current/nasabare.txt"

DEFAULT_SETTINGS: dict[str, Any] = {
    "auto_update_enabled": True,
    "update_hour": 0,
    "update_minute": 0,
    "update_interval_hours": 24,
    "default_scope": "aprs",
    "sources": [
        {"id": "celestrak_amateur", "label": "CelesTrak — Amateur", "enabled": True, "priority": 10, "url": orbital.CELESTRAK_AMATEUR_TLE},
        {"id": "celestrak_stations", "label": "CelesTrak — Stations", "enabled": True, "priority": 20, "url": orbital.CELESTRAK_STATIONS_TLE},
        {"id": "amsat_nasabare", "label": "AMSAT — nasabare.txt", "enabled": True, "priority": 30, "url": AMSAT_NASABARE_TLE},
    ],
}

_scheduler_started = False
_scheduler_lock = threading.Lock()
_refresh_lock = threading.Lock()


def _data_path(name: str) -> Path:
    return Path(db.DB_PATH).parent / name


def _json_load(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except Exception:
        return default


def _json_save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def get_satellite_settings() -> dict[str, Any]:
    raw = _json_load(_data_path("satellite_settings_v113.json"), {})
    result = dict(DEFAULT_SETTINGS)
    if isinstance(raw, dict):
        result.update({k: v for k, v in raw.items() if k != "sources"})
        if isinstance(raw.get("sources"), list):
            by_id = {str(item.get("id")): dict(item) for item in DEFAULT_SETTINGS["sources"]}
            for item in raw["sources"]:
                if isinstance(item, dict) and str(item.get("id") or "") in by_id:
                    by_id[str(item["id"])].update(item)
            result["sources"] = list(by_id.values())
    result["update_hour"] = max(0, min(23, int(result.get("update_hour") or 0)))
    result["update_minute"] = max(0, min(59, int(result.get("update_minute") or 0)))
    result["update_interval_hours"] = max(1, min(168, int(result.get("update_interval_hours") or 24)))
    result["default_scope"] = str(result.get("default_scope") or "aprs")
    if result["default_scope"] not in {"aprs", "packet", "all"}:
        result["default_scope"] = "aprs"
    result["auto_update_enabled"] = bool(result.get("auto_update_enabled", True))
    result["sources"] = sorted(result["sources"], key=lambda x: int(x.get("priority") or 999))
    return result


def save_satellite_settings(payload: dict[str, Any]) -> dict[str, Any]:
    current = get_satellite_settings()
    data = dict(payload or {})
    for key in ("auto_update_enabled", "update_hour", "update_minute", "update_interval_hours", "default_scope"):
        if key in data:
            current[key] = data[key]
    if isinstance(data.get("sources"), list):
        current["sources"] = data["sources"]
    # normalize through reader
    _json_save(_data_path("satellite_settings_v113.json"), current)
    normalized = get_satellite_settings()
    _json_save(_data_path("satellite_settings_v113.json"), normalized)
    return normalized


def _operations() -> dict[str, dict[str, Any]]:
    raw = _json_load(_data_path("satellite_operations_v113.json"), {})
    return raw if isinstance(raw, dict) else {}


def get_operational_state(norad_id: int) -> dict[str, Any]:
    raw = _operations().get(str(int(norad_id)), {})
    state = str(raw.get("state") or "monitor")
    if state not in {"monitor", "ignore", "inactive"}:
        state = "monitor"
    services = raw.get("services") if isinstance(raw.get("services"), dict) else {}
    return {
        "state": state,
        "note": str(raw.get("note") or "")[:500],
        "services": {
            "aprs": bool(services.get("aprs", True)),
            "sstv": bool(services.get("sstv", True)),
            "telemetry": bool(services.get("telemetry", True)),
            "voice": bool(services.get("voice", True)),
            "packet": bool(services.get("packet", True)),
        },
        "updated_at": raw.get("updated_at"),
    }


def save_operational_state(norad_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    all_ops = _operations()
    state = str(payload.get("state") or "monitor")
    if state not in {"monitor", "ignore", "inactive"}:
        raise ValueError("Estado operacional inválido.")
    current = get_operational_state(norad_id)
    services = dict(current["services"])
    if isinstance(payload.get("services"), dict):
        for key in services:
            if key in payload["services"]:
                services[key] = bool(payload["services"][key])
    item = {
        "state": state,
        "note": str(payload.get("note") or current.get("note") or "")[:500],
        "services": services,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    all_ops[str(int(norad_id))] = item
    _json_save(_data_path("satellite_operations_v113.json"), all_ops)
    return item


def classify_operation(item: dict[str, Any]) -> dict[str, Any]:
    protocol = str(item.get("protocol") or "").lower()
    txs = item.get("transmitters") if isinstance(item.get("transmitters"), list) else []
    evidence = " ".join(
        " ".join(str(tx.get(k) or "") for k in ("description", "mode", "service"))
        for tx in txs if isinstance(tx, dict)
    ).upper()
    # Strict by design: AX.25/packet/GFSK alone does NOT imply APRS.
    aprs = protocol.startswith("aprs") or "APRS" in evidence or int(item.get("norad_id") or 0) == 25544
    if aprs:
        kind = "APRS"
    elif "SSTV" in evidence:
        kind = "SSTV"
    elif "AX.25" in evidence or "AX25" in evidence or "PACKET" in evidence or "packet" in protocol:
        kind = "Packet/AX.25"
    elif "TELEMET" in evidence:
        kind = "Telemetria"
    else:
        kind = "Outro digital"
    out = dict(item)
    out["aprs_confirmed"] = bool(aprs)
    out["operation_type"] = kind
    op = get_operational_state(int(out.get("norad_id") or 0))
    out["operational_state"] = op["state"]
    out["operational_note"] = op["note"]
    out["service_states"] = op["services"]
    out["operational"] = op["state"] == "monitor"
    return out


def enriched_catalog(scope: str = "aprs") -> list[dict[str, Any]]:
    scope = str(scope or "aprs").lower()
    rows = [classify_operation(item) for item in orbital.satellite_catalog()]
    if scope == "aprs":
        rows = [item for item in rows if item["aprs_confirmed"]]
    elif scope == "packet":
        rows = [item for item in rows if item["aprs_confirmed"] or item["operation_type"] == "Packet/AX.25"]
    return rows


def _allowed_norads(scope: str = "aprs", *, operational_only: bool = False) -> set[int]:
    rows = enriched_catalog(scope)
    allowed = set()
    for item in rows:
        if operational_only and (
            item.get("operational_state") != "monitor"
            or (item.get("aprs_confirmed") and not item.get("service_states", {}).get("aprs", True))
        ):
            continue
        allowed.add(int(item.get("norad_id") or 0))
    return allowed


def filter_status(items: list[dict[str, Any]], scope: str = "aprs") -> list[dict[str, Any]]:
    allowed = _allowed_norads(scope)
    meta = {int(x["norad_id"]): x for x in enriched_catalog(scope)}
    out = []
    for raw in items:
        nid = int(raw.get("norad_id") or 0)
        if nid not in allowed:
            continue
        item = dict(raw)
        item.update(meta.get(nid, {}))
        out.append(item)
    return out


def filter_passes(items: list[dict[str, Any]], scope: str = "aprs", *, operational_only: bool = True) -> list[dict[str, Any]]:
    allowed = _allowed_norads(scope, operational_only=operational_only)
    meta = {int(x["norad_id"]): x for x in enriched_catalog(scope)}
    out = []
    for raw in items:
        nid = int(raw.get("norad_id") or 0)
        if nid not in allowed:
            continue
        item = dict(raw)
        item.update(meta.get(nid, {}))
        out.append(item)
    out.sort(key=lambda x: str(x.get("aos") or ""))
    return out


def _source_runtime_path() -> Path:
    return _data_path("satellite_sources_runtime_v113.json")


def _source_runtime() -> dict[str, Any]:
    raw = _json_load(_source_runtime_path(), {})
    return raw if isinstance(raw, dict) else {}


def _download_source(source: dict[str, Any]) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    started = time.monotonic()
    label = str(source.get("label") or source.get("id") or "source")
    url = str(source.get("url") or "")
    if not url:
        raise ValueError("URL da fonte não configurada.")
    req = urllib.request.Request(url, headers={"User-Agent": f"PT2VHF-APRS-Client/{__version__}", "Accept": "text/plain,*/*"})
    with urllib.request.urlopen(req, timeout=15) as response:
        text = response.read(12_000_000).decode("utf-8", errors="replace")
    rows = orbital._parse_tle_groups(text)
    for tle in rows.values():
        tle["source"] = label
        tle["source_id"] = str(source.get("id") or "")
    return rows, {
        "ok": True,
        "label": label,
        "url": url,
        "count": len(rows),
        "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "error": "",
    }


def refresh_multisource(*, force: bool = True, reason: str = "manual") -> dict[str, Any]:
    with _refresh_lock:
        # Discover the catalog independently from orbital-element sources so
        # disabled TLE sources are never contacted implicitly.
        current = orbital._load_cache()
        try:
            catalog = orbital._discover_satnogs_catalog()
            catalog_error = ""
        except Exception as exc:
            catalog = current.get("catalog") if isinstance(current.get("catalog"), list) else list(orbital.FALLBACK_CATALOG)
            catalog_error = f"SatNOGS: {exc}"
        base = dict(current) if isinstance(current, dict) else {}
        base["catalog"] = catalog
        base["catalog_source"] = "SatNOGS DB + fallback ISS metadata"
        settings = get_satellite_settings()
        runtime = _source_runtime()
        merged: dict[int, dict[str, Any]] = {}
        errors: list[str] = [catalog_error] if catalog_error else []
        for source in settings["sources"]:
            sid = str(source.get("id") or "")
            if not bool(source.get("enabled", True)):
                runtime[sid] = {"ok": False, "disabled": True, "label": source.get("label"), "error": ""}
                continue
            try:
                rows, status = _download_source(source)
                runtime[sid] = status
                # Lowest priority number wins. Later sources are fallback only.
                for norad, tle in rows.items():
                    merged.setdefault(int(norad), tle)
            except Exception as exc:
                runtime[sid] = {
                    "ok": False, "label": source.get("label"), "url": source.get("url"),
                    "count": 0, "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                    "error": str(exc),
                }
                errors.append(f"{source.get('label')}: {exc}")

        if not merged:
            for key, value in (current.get("tles") or {}).items():
                try:
                    merged[int(key)] = dict(value)
                except Exception:
                    pass

        base["tles"] = {str(k): v for k, v in merged.items()}
        base["tle_source"] = "Multifonte: " + ", ".join(
            str(s.get("label")) for s in settings["sources"] if s.get("enabled", True)
        )
        base["source_runtime"] = runtime
        base["update_reason"] = reason
        base["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        base["errors"] = list(dict.fromkeys(list(base.get("errors") or []) + errors))
        orbital._save_cache(base)
        runtime["_last_update"] = {"at": base["updated_at"], "reason": reason}
        _json_save(_source_runtime_path(), runtime)
        return base


def next_aprs_pass(lat: float, lon: float, alt: float, min_elevation: float = 0.0) -> dict[str, Any] | None:
    raw = orbital.satellite_passes(lat, lon, alt, hours=24 * 7, min_elevation=min_elevation)
    rows = filter_passes(raw, "aprs", operational_only=True)
    now = datetime.now(timezone.utc)
    active = []
    future = []
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
    if chosen is None:
        return None

    # Estimate Doppler at AOS when frequency/TLE data are available.
    try:
        cache = orbital.get_satellite_data(auto_refresh=False)
        tle = (cache.get("tles") or {}).get(str(int(chosen.get("norad_id") or 0)))
        aos_dt = datetime.fromisoformat(str(chosen.get("aos")))
        if aos_dt.tzinfo is None:
            aos_dt = aos_dt.replace(tzinfo=timezone.utc)
        observer = (float(lat), float(lon), float(alt or 0))
        if tle:
            chosen["doppler_uplink_hz"] = orbital._doppler_hz(tle, aos_dt, observer, orbital._frequency_value(chosen.get("uplink_hz")))
            chosen["doppler_downlink_hz"] = orbital._doppler_hz(tle, aos_dt, observer, orbital._frequency_value(chosen.get("downlink_hz")))
    except Exception:
        pass
    return chosen


def _scheduled_due(settings: dict[str, Any], runtime: dict[str, Any], now: datetime) -> bool:
    if not settings.get("auto_update_enabled"):
        return False
    last_raw = (runtime.get("_last_update") or {}).get("at")
    last = None
    if last_raw:
        try:
            last = datetime.fromisoformat(str(last_raw))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
        except Exception:
            last = None
    target = now.replace(hour=int(settings["update_hour"]), minute=int(settings["update_minute"]), second=0, microsecond=0)
    if target > now:
        target -= timedelta(days=1)
    interval = timedelta(hours=int(settings["update_interval_hours"]))
    if last is None:
        return now >= target
    return last < target <= now and now - last >= min(interval, timedelta(hours=24))


def _scheduler_loop() -> None:
    while True:
        try:
            settings = get_satellite_settings()
            runtime = _source_runtime()
            now = datetime.now().astimezone()
            if _scheduled_due(settings, runtime, now):
                refresh_multisource(force=True, reason="scheduled")
        except Exception:
            pass
        time.sleep(60)


def start_scheduler() -> None:
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True
        threading.Thread(target=_scheduler_loop, name="satellite-tle-scheduler", daemon=True).start()


def register_v113_satellite_routes(app) -> None:
    start_scheduler()

    @app.get("/api/v113/satellites/catalog")
    def api_v113_catalog():
        scope = request.args.get("scope", get_satellite_settings().get("default_scope", "aprs"))
        return jsonify({"catalog": enriched_catalog(scope), "scope": scope})

    @app.get("/api/v113/satellites/next-pass")
    def api_v113_next_pass():
        try:
            cfg = db.get_config()
            lat = float(request.args.get("lat", cfg.get("latitude")))
            lon = float(request.args.get("lon", cfg.get("longitude")))
            alt = float(request.args.get("alt", cfg.get("altitude") or 0))
            min_el = float(request.args.get("min_elevation", 0))
            return jsonify({"pass": next_aprs_pass(lat, lon, alt, min_el)})
        except Exception as exc:
            return jsonify({"pass": None, "error": str(exc)}), 400

    @app.get("/api/v113/satellites/settings")
    def api_v113_settings():
        return jsonify({"settings": get_satellite_settings(), "runtime": _source_runtime()})

    @app.post("/api/v113/satellites/settings")
    def api_v113_save_settings():
        try:
            return jsonify({"settings": save_satellite_settings(request.get_json(force=True) or {})})
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

    @app.post("/api/v113/satellites/update")
    def api_v113_update():
        try:
            data = refresh_multisource(force=True, reason="manual")
            return jsonify({"ok": True, "updated_at": data.get("updated_at"), "runtime": _source_runtime(), "errors": data.get("errors") or []})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 502

    @app.post("/api/v113/satellites/source-test")
    def api_v113_source_test():
        payload = request.get_json(force=True) or {}
        sid = str(payload.get("id") or "")
        source = next((s for s in get_satellite_settings()["sources"] if str(s.get("id")) == sid), None)
        if not source:
            return jsonify({"ok": False, "error": "Fonte desconhecida."}), 404
        try:
            _rows, status = _download_source(source)
            return jsonify(status)
        except Exception as exc:
            return jsonify({"ok": False, "label": source.get("label"), "error": str(exc)}), 502

    @app.get("/api/v113/satellites/<int:norad_id>/operation")
    def api_v113_operation(norad_id: int):
        return jsonify(get_operational_state(norad_id))

    @app.post("/api/v113/satellites/<int:norad_id>/operation")
    def api_v113_save_operation(norad_id: int):
        try:
            return jsonify(save_operational_state(norad_id, request.get_json(force=True) or {}))
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400
