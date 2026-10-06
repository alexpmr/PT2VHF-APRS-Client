from __future__ import annotations

import json
import math
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import jsonify, request

from . import __version__
from . import database as db

try:
    from sgp4.api import Satrec, jday
except Exception:  # pragma: no cover - surfaced by API health
    Satrec = None
    jday = None


CELESTRAK_AMATEUR_TLE = "https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle"
CELESTRAK_STATIONS_TLE = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
SATNOGS_SATELLITES = "https://db.satnogs.org/api/satellites/?format=json"
SATNOGS_TRANSMITTERS = "https://db.satnogs.org/api/transmitters/?format=json"
CACHE_MAX_AGE_SECONDS = 24 * 60 * 60
EARTH_RADIUS_KM = 6378.137
EARTH_FLATTENING = 1.0 / 298.257223563
LIGHT_SPEED_KM_S = 299792.458

_lock = threading.Lock()

# Always-available metadata. Orbital elements are never bundled as if current:
# they are downloaded/cached separately and carry their own epoch/source.
FALLBACK_CATALOG = [
    {
        "norad_id": 25544,
        "name": "ISS (ZARYA)",
        "callsign": "RS0ISS",
        "protocol": "APRS/packet",
        "uplink_hz": 145825000,
        "downlink_hz": 145825000,
        "mode": "FM packet 1200 baud",
        "status": "active",
        "source": "PT2VHF fallback metadata; verify operating schedule",
        "favorite_default": True,
        "notes": "A operação APRS da ISS pode ser suspensa temporariamente; confirme o status antes de operar.",
    }
]


def _cache_path() -> Path:
    return Path(db.DB_PATH).parent / "satellites_v112.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds") if dt else None


def _http_text(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"PT2VHF-APRS-Client/{__version__}",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read(12_000_000)
    return raw.decode("utf-8", errors="replace")


def _http_json(url: str, timeout: int = 12) -> Any:
    return json.loads(_http_text(url, timeout=timeout))


def _load_cache() -> dict[str, Any]:
    path = _cache_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(data: dict[str, Any]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def _parse_tle_groups(text: str) -> dict[int, dict[str, Any]]:
    lines = [line.rstrip() for line in str(text or "").splitlines() if line.strip()]
    out: dict[int, dict[str, Any]] = {}
    i = 0
    while i < len(lines):
        name = ""
        line1 = ""
        line2 = ""
        if lines[i].startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            line1, line2 = lines[i], lines[i + 1]
            i += 2
        elif i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            name, line1, line2 = lines[i].strip(), lines[i + 1], lines[i + 2]
            i += 3
        else:
            i += 1
            continue
        try:
            norad = int(line1[2:7])
        except Exception:
            continue
        out[norad] = {"norad_id": norad, "tle_name": name, "line1": line1, "line2": line2}
    return out


def _frequency_value(value: Any) -> int | None:
    try:
        v = int(float(value))
        return v if v > 0 else None
    except Exception:
        return None


def _discover_satnogs_catalog() -> list[dict[str, Any]]:
    satellites = _http_json(SATNOGS_SATELLITES)
    transmitters = _http_json(SATNOGS_TRANSMITTERS)
    if not isinstance(satellites, list) or not isinstance(transmitters, list):
        raise RuntimeError("Resposta SatNOGS inesperada")

    sat_by_uuid: dict[str, dict[str, Any]] = {}
    sat_by_norad: dict[int, dict[str, Any]] = {}
    for sat in satellites:
        if not isinstance(sat, dict):
            continue
        try:
            norad = int(sat.get("norad_cat_id") or sat.get("norad_catid") or 0)
        except Exception:
            norad = 0
        if norad <= 0:
            continue
        sat_by_norad[norad] = sat
        for key in ("sat_id", "uuid"):
            if sat.get(key):
                sat_by_uuid[str(sat.get(key))] = sat

    grouped: dict[int, dict[str, Any]] = {}
    keywords = ("APRS", "AX.25", "AX25", "PACKET")
    for tx in transmitters:
        if not isinstance(tx, dict):
            continue
        description = " ".join(
            str(tx.get(k) or "") for k in ("description", "mode", "service", "baud")
        ).upper()
        if not any(keyword in description for keyword in keywords):
            continue
        sat = None
        sid = str(tx.get("sat_id") or tx.get("satellite") or "")
        if sid:
            sat = sat_by_uuid.get(sid)
        try:
            norad = int(tx.get("norad_cat_id") or (sat or {}).get("norad_cat_id") or 0)
        except Exception:
            norad = 0
        if norad <= 0:
            continue
        sat = sat or sat_by_norad.get(norad, {})
        status = str(tx.get("status") or sat.get("status") or "").lower()
        if status in {"invalid", "re-entered", "dead", "inactive"}:
            continue

        entry = grouped.setdefault(
            norad,
            {
                "norad_id": norad,
                "name": str(sat.get("name") or sat.get("names") or f"NORAD {norad}"),
                "callsign": "",
                "protocol": "APRS/packet" if "APRS" in description else "packet/AX.25",
                "uplink_hz": None,
                "downlink_hz": None,
                "mode": str(tx.get("mode") or "").strip(),
                "status": status or "unknown",
                "source": "SatNOGS DB",
                "favorite_default": norad == 25544,
                "notes": "",
                "transmitters": [],
            },
        )
        uplink = _frequency_value(tx.get("uplink_low") or tx.get("uplink_high"))
        downlink = _frequency_value(tx.get("downlink_low") or tx.get("downlink_high"))
        entry["uplink_hz"] = entry.get("uplink_hz") or uplink
        entry["downlink_hz"] = entry.get("downlink_hz") or downlink
        call = str(tx.get("callsign") or tx.get("call_sign") or "").strip()
        if call and not entry.get("callsign"):
            entry["callsign"] = call
        entry["transmitters"].append(
            {
                "description": str(tx.get("description") or ""),
                "mode": str(tx.get("mode") or ""),
                "uplink_hz": uplink,
                "downlink_hz": downlink,
                "status": str(tx.get("status") or ""),
            }
        )

    # Ensure ISS remains discoverable even when SatNOGS metadata changes.
    if 25544 not in grouped:
        grouped[25544] = dict(FALLBACK_CATALOG[0])
    return sorted(grouped.values(), key=lambda x: (x.get("norad_id") != 25544, str(x.get("name") or "")))


def _fresh(cache: dict[str, Any]) -> bool:
    try:
        stamp = datetime.fromisoformat(str(cache.get("updated_at") or ""))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return (_utc_now() - stamp).total_seconds() <= CACHE_MAX_AGE_SECONDS
    except Exception:
        return False


def refresh_satellite_data(force: bool = False) -> dict[str, Any]:
    with _lock:
        current = _load_cache()
        if current and _fresh(current) and not force:
            return current

        errors: list[str] = []
        catalog: list[dict[str, Any]]
        try:
            catalog = _discover_satnogs_catalog()
        except Exception as exc:
            errors.append(f"SatNOGS: {exc}")
            catalog = current.get("catalog") if isinstance(current.get("catalog"), list) else list(FALLBACK_CATALOG)

        tle_by_norad: dict[int, dict[str, Any]] = {}
        for url, label in ((CELESTRAK_AMATEUR_TLE, "CelesTrak amateur"), (CELESTRAK_STATIONS_TLE, "CelesTrak stations")):
            try:
                tle_by_norad.update(_parse_tle_groups(_http_text(url)))
            except Exception as exc:
                errors.append(f"{label}: {exc}")

        if not tle_by_norad and isinstance(current.get("tles"), dict):
            for key, value in current["tles"].items():
                try:
                    tle_by_norad[int(key)] = dict(value)
                except Exception:
                    pass

        payload = {
            "updated_at": _iso(_utc_now()),
            "catalog_source": "SatNOGS DB + fallback ISS metadata",
            "tle_source": "CelesTrak amateur/stations GP TLE",
            "catalog": catalog,
            "tles": {str(k): v for k, v in tle_by_norad.items()},
            "errors": errors,
        }
        # Do not overwrite a useful cache with an entirely empty download.
        if not payload["tles"] and current.get("tles"):
            payload["tles"] = current["tles"]
        _save_cache(payload)
        return payload


def get_satellite_data(auto_refresh: bool = True) -> dict[str, Any]:
    cache = _load_cache()
    if auto_refresh and (not cache or not _fresh(cache)):
        try:
            return refresh_satellite_data(force=not bool(cache))
        except Exception:
            pass
    if not cache:
        return {
            "updated_at": None,
            "catalog_source": "fallback",
            "tle_source": "not downloaded",
            "catalog": list(FALLBACK_CATALOG),
            "tles": {},
            "errors": ["Dados orbitais ainda não foram baixados."],
        }
    return cache


def _satrec(tle: dict[str, Any]):
    if Satrec is None:
        raise RuntimeError("Biblioteca SGP4 indisponível.")
    line1 = str(tle.get("line1") or "")
    line2 = str(tle.get("line2") or "")
    if not line1.startswith("1 ") or not line2.startswith("2 "):
        raise ValueError("TLE inválido.")
    return Satrec.twoline2rv(line1, line2)


def _julian(dt: datetime) -> tuple[float, float]:
    if jday is None:
        raise RuntimeError("Biblioteca SGP4 indisponível.")
    dt = dt.astimezone(timezone.utc)
    sec = dt.second + dt.microsecond / 1_000_000
    return jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, sec)


def _gmst_radians(dt: datetime) -> float:
    # IAU-compatible approximation, sufficient for map/pass planning.
    dt = dt.astimezone(timezone.utc)
    unix_days = dt.timestamp() / 86400.0
    jd = 2440587.5 + unix_days
    t = (jd - 2451545.0) / 36525.0
    gmst_deg = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t * t - (t ** 3) / 38710000.0
    return math.radians(gmst_deg % 360.0)


def _eci_to_ecef(r_eci: tuple[float, float, float] | list[float], dt: datetime) -> tuple[float, float, float]:
    theta = _gmst_radians(dt)
    c, s = math.cos(theta), math.sin(theta)
    x, y, z = map(float, r_eci)
    return (c * x + s * y, -s * x + c * y, z)


def _ecef_to_geodetic(x: float, y: float, z: float) -> tuple[float, float, float]:
    a = EARTH_RADIUS_KM
    f = EARTH_FLATTENING
    e2 = f * (2.0 - f)
    lon = math.atan2(y, x)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1.0 - e2))
    alt = 0.0
    for _ in range(8):
        sin_lat = math.sin(lat)
        n = a / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
        alt = p / max(math.cos(lat), 1e-12) - n
        lat = math.atan2(z, p * (1.0 - e2 * n / max(n + alt, 1e-9)))
    return math.degrees(lat), ((math.degrees(lon) + 540.0) % 360.0) - 180.0, alt


def _observer_ecef(lat_deg: float, lon_deg: float, altitude_m: float = 0.0) -> tuple[float, float, float]:
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    a = EARTH_RADIUS_KM
    f = EARTH_FLATTENING
    e2 = f * (2.0 - f)
    n = a / math.sqrt(1.0 - e2 * math.sin(lat) ** 2)
    h = altitude_m / 1000.0
    return (
        (n + h) * math.cos(lat) * math.cos(lon),
        (n + h) * math.cos(lat) * math.sin(lon),
        (n * (1.0 - e2) + h) * math.sin(lat),
    )


def _look_angles(sat_ecef: tuple[float, float, float], lat_deg: float, lon_deg: float, altitude_m: float = 0.0) -> tuple[float, float, float]:
    obs = _observer_ecef(lat_deg, lon_deg, altitude_m)
    dx, dy, dz = (sat_ecef[i] - obs[i] for i in range(3))
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    east = -math.sin(lon) * dx + math.cos(lon) * dy
    north = -math.sin(lat) * math.cos(lon) * dx - math.sin(lat) * math.sin(lon) * dy + math.cos(lat) * dz
    up = math.cos(lat) * math.cos(lon) * dx + math.cos(lat) * math.sin(lon) * dy + math.sin(lat) * dz
    rng = math.sqrt(east * east + north * north + up * up)
    elevation = math.degrees(math.asin(max(-1.0, min(1.0, up / max(rng, 1e-9)))))
    azimuth = (math.degrees(math.atan2(east, north)) + 360.0) % 360.0
    return azimuth, elevation, rng


def _position(tle: dict[str, Any], when: datetime, observer: tuple[float, float, float] | None = None) -> dict[str, Any]:
    sat = _satrec(tle)
    jd, fr = _julian(when)
    error, r, _v = sat.sgp4(jd, fr)
    if error:
        raise RuntimeError(f"SGP4 error {error}")
    ecef = _eci_to_ecef(r, when)
    lat, lon, alt_km = _ecef_to_geodetic(*ecef)
    horizon_angle = math.acos(min(1.0, EARTH_RADIUS_KM / max(EARTH_RADIUS_KM + alt_km, EARTH_RADIUS_KM)))
    footprint_radius_km = EARTH_RADIUS_KM * horizon_angle
    out: dict[str, Any] = {
        "time": _iso(when),
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "altitude_km": round(alt_km, 2),
        "footprint_radius_km": round(footprint_radius_km, 1),
        "speed_km_s": round(math.sqrt(sum(float(v) ** 2 for v in _v)), 4),
    }
    if observer is not None:
        az, el, rng = _look_angles(ecef, observer[0], observer[1], observer[2])
        out.update({"azimuth_deg": round(az, 1), "elevation_deg": round(el, 1), "range_km": round(rng, 1)})
    return out


def _range_km(tle: dict[str, Any], when: datetime, observer: tuple[float, float, float]) -> float:
    sat = _satrec(tle)
    jd, fr = _julian(when)
    error, r, _v = sat.sgp4(jd, fr)
    if error:
        raise RuntimeError(f"SGP4 error {error}")
    return _look_angles(_eci_to_ecef(r, when), observer[0], observer[1], observer[2])[2]


def _doppler_hz(tle: dict[str, Any], when: datetime, observer: tuple[float, float, float], frequency_hz: int | None) -> int | None:
    if not frequency_hz:
        return None
    before = _range_km(tle, when - timedelta(seconds=1), observer)
    after = _range_km(tle, when + timedelta(seconds=1), observer)
    radial_km_s = (after - before) / 2.0
    return int(round(-float(frequency_hz) * radial_km_s / LIGHT_SPEED_KM_S))


def _tle_epoch(tle: dict[str, Any]) -> str | None:
    try:
        sat = _satrec(tle)
        # SGP4 exposes epoch as Julian day split.
        jd = float(sat.jdsatepoch) + float(sat.jdsatepochF)
        unix = (jd - 2440587.5) * 86400.0
        return _iso(datetime.fromtimestamp(unix, tz=timezone.utc))
    except Exception:
        return None


def satellite_catalog() -> list[dict[str, Any]]:
    data = get_satellite_data(auto_refresh=False)
    tles = data.get("tles") if isinstance(data.get("tles"), dict) else {}
    out = []
    for raw in data.get("catalog") or FALLBACK_CATALOG:
        item = dict(raw)
        tle = tles.get(str(item.get("norad_id"))) if isinstance(tles, dict) else None
        item["tle_available"] = bool(tle)
        item["tle_epoch"] = _tle_epoch(tle) if tle else None
        item["tle_source"] = str((tle or {}).get("source") or data.get("tle_source") or "")
        item["tle_source_id"] = str((tle or {}).get("source_id") or "")
        out.append(item)
    return out


def satellite_status(lat: float, lon: float, altitude_m: float = 0.0, when: datetime | None = None) -> list[dict[str, Any]]:
    data = get_satellite_data(auto_refresh=False)
    tles = data.get("tles") if isinstance(data.get("tles"), dict) else {}
    now = when or _utc_now()
    observer = (float(lat), float(lon), float(altitude_m or 0.0))
    result = []
    by_norad = {int(x.get("norad_id")): x for x in data.get("catalog") or FALLBACK_CATALOG if x.get("norad_id")}
    for norad, meta in by_norad.items():
        tle = tles.get(str(norad))
        if not tle:
            continue
        try:
            pos = _position(tle, now, observer)
            pos.update(meta)
            pos["tle_epoch"] = _tle_epoch(tle)
            pos["doppler_uplink_hz"] = _doppler_hz(tle, now, observer, _frequency_value(meta.get("uplink_hz")))
            pos["doppler_downlink_hz"] = _doppler_hz(tle, now, observer, _frequency_value(meta.get("downlink_hz")))
            result.append(pos)
        except Exception as exc:
            item = dict(meta)
            item["error"] = str(exc)
            result.append(item)
    return result


def _refine_crossing(tle: dict[str, Any], observer: tuple[float, float, float], lo: datetime, hi: datetime, rising: bool) -> datetime:
    for _ in range(12):
        mid = lo + (hi - lo) / 2
        el = float(_position(tle, mid, observer).get("elevation_deg") or -90)
        if (el >= 0) == rising:
            hi = mid
        else:
            lo = mid
    return hi if rising else lo


def passes_for_satellite(
    tle: dict[str, Any],
    observer: tuple[float, float, float],
    start: datetime,
    hours: int,
    step_seconds: int = 45,
) -> list[dict[str, Any]]:
    end = start + timedelta(hours=max(1, min(int(hours), 24 * 7)))
    current = start
    previous = _position(tle, current, observer)
    inside = float(previous.get("elevation_deg") or -90) >= 0
    aos = current if inside else None
    samples: list[dict[str, Any]] = [previous] if inside else []
    result: list[dict[str, Any]] = []

    while current < end:
        nxt = min(end, current + timedelta(seconds=step_seconds))
        pos = _position(tle, nxt, observer)
        elev = float(pos.get("elevation_deg") or -90)
        prev_elev = float(previous.get("elevation_deg") or -90)

        if not inside and prev_elev < 0 <= elev:
            aos = _refine_crossing(tle, observer, current, nxt, True)
            inside = True
            samples = [_position(tle, aos, observer), pos]
        elif inside:
            samples.append(pos)

        if inside and prev_elev >= 0 > elev:
            los = _refine_crossing(tle, observer, current, nxt, False)
            samples.append(_position(tle, los, observer))
            top = max(samples, key=lambda x: float(x.get("elevation_deg") or -90))
            result.append(
                {
                    "aos": _iso(aos),
                    "tca": top.get("time"),
                    "los": _iso(los),
                    "max_elevation_deg": round(float(top.get("elevation_deg") or 0), 1),
                    "aos_azimuth_deg": round(float(samples[0].get("azimuth_deg") or 0), 1),
                    "tca_azimuth_deg": round(float(top.get("azimuth_deg") or 0), 1),
                    "los_azimuth_deg": round(float(samples[-1].get("azimuth_deg") or 0), 1),
                    "duration_seconds": int((los - (aos or los)).total_seconds()),
                }
            )
            inside = False
            aos = None
            samples = []
        previous = pos
        current = nxt

    return result


def satellite_passes(lat: float, lon: float, altitude_m: float, hours: int = 24, min_elevation: float = 0.0) -> list[dict[str, Any]]:
    data = get_satellite_data(auto_refresh=False)
    tles = data.get("tles") if isinstance(data.get("tles"), dict) else {}
    observer = (float(lat), float(lon), float(altitude_m or 0.0))
    start = _utc_now()
    result: list[dict[str, Any]] = []
    for meta in data.get("catalog") or FALLBACK_CATALOG:
        norad = int(meta.get("norad_id") or 0)
        tle = tles.get(str(norad))
        if not tle:
            continue
        try:
            for event in passes_for_satellite(tle, observer, start, hours):
                if float(event.get("max_elevation_deg") or 0) < float(min_elevation or 0):
                    continue
                item = dict(event)
                item.update(meta)
                item["tle_epoch"] = _tle_epoch(tle)
                result.append(item)
        except Exception:
            continue
    result.sort(key=lambda x: str(x.get("aos") or ""))
    return result


def satellite_track(norad_id: int, lat: float, lon: float, altitude_m: float, past_minutes: int = 30, future_minutes: int = 90, step_seconds: int = 60) -> dict[str, Any]:
    data = get_satellite_data(auto_refresh=False)
    tles = data.get("tles") if isinstance(data.get("tles"), dict) else {}
    tle = tles.get(str(int(norad_id)))
    if not tle:
        raise KeyError(f"TLE indisponível para NORAD {norad_id}")
    meta = next((dict(x) for x in data.get("catalog") or FALLBACK_CATALOG if int(x.get("norad_id") or 0) == int(norad_id)), {"norad_id": int(norad_id), "name": f"NORAD {norad_id}"})
    observer = (float(lat), float(lon), float(altitude_m or 0.0))
    now = _utc_now()
    past_minutes = max(0, min(int(past_minutes), 180))
    future_minutes = max(1, min(int(future_minutes), 360))
    step_seconds = max(15, min(int(step_seconds), 300))
    start = now - timedelta(minutes=past_minutes)
    end = now + timedelta(minutes=future_minutes)
    points = []
    t = start
    while t <= end:
        points.append(_position(tle, t, observer))
        t += timedelta(seconds=step_seconds)
    current = _position(tle, now, observer)
    current["doppler_uplink_hz"] = _doppler_hz(tle, now, observer, _frequency_value(meta.get("uplink_hz")))
    current["doppler_downlink_hz"] = _doppler_hz(tle, now, observer, _frequency_value(meta.get("downlink_hz")))
    return {"satellite": meta, "current": current, "points": points, "now": _iso(now), "tle_epoch": _tle_epoch(tle)}


def _observer_from_request() -> tuple[float, float, float]:
    cfg = db.get_config()
    lat = request.args.get("lat", cfg.get("latitude"))
    lon = request.args.get("lon", cfg.get("longitude"))
    alt = request.args.get("alt", cfg.get("altitude") or 0)
    if lat in (None, "") or lon in (None, ""):
        raise ValueError("Configure latitude/longitude da estação para calcular passagens.")
    latf, lonf, altf = float(lat), float(lon), float(alt or 0)
    if not (-90 <= latf <= 90 and -180 <= lonf <= 180):
        raise ValueError("Localização da estação inválida.")
    return latf, lonf, altf


def register_v112_satellite_routes(app) -> None:
    @app.get("/api/v112/satellites/catalog")
    def api_v112_satellite_catalog():
        from . import v113_satellites as v113
        data = get_satellite_data(auto_refresh=False)
        scope = str(request.args.get("scope") or v113.get_satellite_settings().get("default_scope") or "aprs")
        return jsonify({
            "catalog": v113.enriched_catalog(scope),
            "scope": scope,
            "updated_at": data.get("updated_at"),
            "catalog_source": data.get("catalog_source"),
            "tle_source": data.get("tle_source"),
            "source_runtime": data.get("source_runtime") or {},
            "errors": data.get("errors") or [],
            "sgp4_available": Satrec is not None,
        })

    @app.post("/api/v112/satellites/update")
    def api_v112_satellite_update():
        try:
            from . import v113_satellites as v113
            data = v113.refresh_multisource(force=True, reason="manual")
            scope = str(request.args.get("scope") or v113.get_satellite_settings().get("default_scope") or "aprs")
            return jsonify({
                "ok": True,
                "updated_at": data.get("updated_at"),
                "catalog": v113.enriched_catalog(scope),
                "errors": data.get("errors") or [],
            })
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 502

    @app.get("/api/v112/satellites/status")
    def api_v112_satellite_status():
        try:
            from . import v113_satellites as v113
            lat, lon, alt = _observer_from_request()
            scope = str(request.args.get("scope") or v113.get_satellite_settings().get("default_scope") or "aprs")
            items = v113.filter_status(satellite_status(lat, lon, alt), scope)
            return jsonify({"items": items, "scope": scope, "observer": {"latitude": lat, "longitude": lon, "altitude_m": alt}})
        except Exception as exc:
            return jsonify({"items": [], "error": str(exc)}), 400

    @app.get("/api/v112/satellites/passes")
    def api_v112_satellite_passes():
        try:
            from . import v113_satellites as v113
            lat, lon, alt = _observer_from_request()
            hours = int(request.args.get("hours", 24))
            min_elevation = float(request.args.get("min_elevation", 0))
            scope = str(request.args.get("scope") or v113.get_satellite_settings().get("default_scope") or "aprs")
            raw = satellite_passes(lat, lon, alt, hours, min_elevation)
            items = v113.filter_passes(raw, scope, operational_only=(scope == "aprs"))
            return jsonify({"items": items, "scope": scope, "observer": {"latitude": lat, "longitude": lon, "altitude_m": alt}})
        except Exception as exc:
            return jsonify({"items": [], "error": str(exc)}), 400

    @app.get("/api/v112/satellites/<int:norad_id>/track")
    def api_v112_satellite_track(norad_id: int):
        try:
            lat, lon, alt = _observer_from_request()
            return jsonify(satellite_track(
                norad_id, lat, lon, alt,
                int(request.args.get("past", 30)),
                int(request.args.get("future", 90)),
                int(request.args.get("step", 60)),
            ))
        except KeyError as exc:
            return jsonify({"error": str(exc)}), 404
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400
