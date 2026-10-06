from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from flask import jsonify, request

from . import database as db


def _cutoff(hours: int) -> str | None:
    value = max(0, min(int(hours or 0), 24 * 30))
    if value <= 0:
        return None
    return (datetime.now(timezone.utc) - timedelta(hours=value)).isoformat(timespec="seconds")


def _valid_position(lat: Any, lon: Any) -> bool:
    try:
        latitude = float(lat)
        longitude = float(lon)
    except (TypeError, ValueError):
        return False
    return -90 <= latitude <= 90 and -180 <= longitude <= 180 and not (latitude == 0 and longitude == 0)


def _quality_weight(rssi: Any, snr: Any, receptions: int) -> float:
    parts: list[float] = []
    try:
        rv = float(rssi)
        parts.append(max(0.0, min(1.0, (rv + 130.0) / 90.0)))
    except (TypeError, ValueError):
        pass
    try:
        sv = float(snr)
        parts.append(max(0.0, min(1.0, (sv + 20.0) / 40.0)))
    except (TypeError, ValueError):
        pass
    density = max(0.15, min(1.0, 0.20 + math.log1p(max(1, int(receptions or 1))) / 5.0))
    if not parts:
        return round(density, 4)
    quality = sum(parts) / len(parts)
    return round(max(0.15, min(1.0, quality * 0.72 + density * 0.28)), 4)


def rf_coverage_points(hours: int = 24, limit: int = 3500) -> dict[str, Any]:
    hours = max(0, min(int(hours or 0), 24 * 30))
    limit = max(100, min(int(limit or 3500), 8000))
    cutoff = _cutoff(hours)

    params: list[Any] = []
    where = "UPPER(COALESCE(medium,''))='RF' AND from_call IS NOT NULL AND TRIM(from_call)<>''"
    if cutoff:
        where += " AND timestamp>=?"
        params.append(cutoff)

    with db.connection() as conn:
        rf_rows = conn.execute(
            f"""
            SELECT UPPER(TRIM(from_call)) AS callsign,
                   COUNT(*) AS receptions,
                   MAX(timestamp) AS last_seen
              FROM packets
             WHERE {where}
             GROUP BY UPPER(TRIM(from_call))
             ORDER BY receptions DESC, last_seen DESC
            """,
            params,
        ).fetchall()
        rf_by_call = {
            str(row["callsign"]): {
                "receptions": int(row["receptions"] or 0),
                "last_seen": str(row["last_seen"] or ""),
            }
            for row in rf_rows
            if str(row["callsign"] or "").strip()
        }
        if not rf_by_call:
            return {"hours": hours, "points": [], "rf_stations": 0, "quality_points": 0, "density_points": 0}

        track_params: list[Any] = []
        track_where = "(rssi IS NOT NULL OR snr IS NOT NULL)"
        if cutoff:
            track_where += " AND timestamp>=?"
            track_params.append(cutoff)
        quality_rows = conn.execute(
            f"""
            SELECT callsign,timestamp,latitude,longitude,rssi,snr
              FROM tracks
             WHERE {track_where}
             ORDER BY id DESC
             LIMIT ?
            """,
            [*track_params, max(limit * 3, 3000)],
        ).fetchall()

        points: list[dict[str, Any]] = []
        calls_with_quality: set[str] = set()
        for row in quality_rows:
            call = str(row["callsign"] or "").upper().strip()
            if call not in rf_by_call or not _valid_position(row["latitude"], row["longitude"]):
                continue
            receptions = int(rf_by_call[call]["receptions"])
            points.append({
                "callsign": call,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "rssi": None if row["rssi"] is None else float(row["rssi"]),
                "snr": None if row["snr"] is None else float(row["snr"]),
                "receptions": receptions,
                "timestamp": str(row["timestamp"] or ""),
                "weight": _quality_weight(row["rssi"], row["snr"], receptions),
                "source": "rf_quality",
            })
            calls_with_quality.add(call)
            if len(points) >= limit:
                break

        remaining = [call for call in rf_by_call if call not in calls_with_quality]
        if remaining and len(points) < limit:
            station_rows = conn.execute(
                """SELECT callsign,latitude,longitude,last_heard
                     FROM stations
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL"""
            ).fetchall()
            for row in station_rows:
                call = str(row["callsign"] or "").upper().strip()
                if call not in rf_by_call or call in calls_with_quality:
                    continue
                if not _valid_position(row["latitude"], row["longitude"]):
                    continue
                receptions = int(rf_by_call[call]["receptions"])
                points.append({
                    "callsign": call,
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "rssi": None,
                    "snr": None,
                    "receptions": receptions,
                    "timestamp": str(rf_by_call[call]["last_seen"] or row["last_heard"] or ""),
                    "weight": _quality_weight(None, None, receptions),
                    "source": "rf_density",
                })
                if len(points) >= limit:
                    break

    return {
        "hours": hours,
        "points": points,
        "rf_stations": len(rf_by_call),
        "quality_points": sum(1 for point in points if point["source"] == "rf_quality"),
        "density_points": sum(1 for point in points if point["source"] == "rf_density"),
        "weight_basis": "RSSI/SNR quando disponíveis; densidade de recepções RF como fallback",
    }


def register_v142_routes(app) -> None:
    @app.get("/api/v142/rf-coverage")
    def api_v142_rf_coverage():
        try:
            hours = int(request.args.get("hours", 24))
            limit = int(request.args.get("limit", 3500))
            return jsonify(rf_coverage_points(hours=hours, limit=limit))
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
