from __future__ import annotations

import csv
import io
import json
import os
import platform
import shutil
import statistics
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import Response, jsonify, request, send_file

from . import __version__
from . import database as db
from . import diagnostics as diag
from .aprs_service import service
from .local_server import runtime_info as local_server_runtime_info
from .tnc_service import service as tnc_service


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def _hours_arg(default: int = 24) -> int:
    try:
        value = int(request.args.get("hours", default))
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, 24 * 365))


def _station_rows(query: str, limit: int = 20) -> list[dict[str, Any]]:
    text = str(query or "").upper().strip()
    if not text:
        return []
    like = f"%{text}%"
    exact = text
    with db.connection() as conn:
        rows = conn.execute(
            """SELECT s.callsign,s.name,s.last_heard,s.latitude,s.longitude,s.speed,s.course,s.altitude,
                      s.info,s.symbol_table,s.symbol,s.message_capable,s.path,
                      CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
               FROM stations s
               LEFT JOIN favorites f ON f.callsign=s.callsign
               WHERE UPPER(s.callsign) LIKE ? OR UPPER(COALESCE(s.name,'')) LIKE ?
               ORDER BY CASE WHEN UPPER(s.callsign)=? THEN 0 ELSE 1 END,
                        favorite DESC,last_heard DESC
               LIMIT ?""",
            (like, like, exact, max(1, min(int(limit), 100))),
        ).fetchall()
    return [dict(row) for row in rows]


def _window_counts(start: datetime, end: datetime) -> dict[str, Any]:
    a, b = _iso(start), _iso(end)
    with db.connection() as conn:
        packet = conn.execute(
            """SELECT COUNT(*) AS packets,
                      COUNT(DISTINCT NULLIF(from_call,'')) AS stations,
                      SUM(CASE WHEN UPPER(COALESCE(medium,''))='RF' THEN 1 ELSE 0 END) AS rf,
                      SUM(CASE WHEN UPPER(COALESCE(medium,''))='APRS-IS' THEN 1 ELSE 0 END) AS aprsis,
                      SUM(CASE WHEN rx_fingerprint IS NOT NULL AND rx_fingerprint<>'' THEN 1 ELSE 0 END) AS fingerprinted,
                      COUNT(DISTINCT CASE WHEN rx_fingerprint IS NOT NULL AND rx_fingerprint<>'' THEN rx_fingerprint END) AS fingerprints
               FROM packets WHERE timestamp>=? AND timestamp<?""",
            (a, b),
        ).fetchone()
        msg = conn.execute(
            """SELECT COUNT(*) AS messages,
                      SUM(CASE WHEN LOWER(COALESCE(status,'')) IN ('ack','acked','delivered','confirmed') THEN 1 ELSE 0 END) AS acked,
                      SUM(CASE WHEN LOWER(COALESCE(status,'')) LIKE 'rej%' OR LOWER(COALESCE(status,'')) LIKE 'fail%' THEN 1 ELSE 0 END) AS rejected
               FROM messages WHERE timestamp>=? AND timestamp<? AND message_type='message'""",
            (a, b),
        ).fetchone()
        rtts = [
            float(row[0]) for row in conn.execute(
                """SELECT rtt_ms FROM aprs_queries
                   WHERE response_at>=? AND response_at<? AND rtt_ms IS NOT NULL AND rtt_ms>=0""",
                (a, b),
            ).fetchall()
        ]
        edges = conn.execute(
            """SELECT COUNT(*) FROM topology_events WHERE timestamp>=? AND timestamp<?""",
            (a, b),
        ).fetchone()[0]
        first_seen = conn.execute(
            """SELECT COUNT(*) FROM stations s
               WHERE s.last_heard>=? AND s.last_heard<?
                 AND NOT EXISTS (
                   SELECT 1 FROM packets p
                   WHERE p.from_call=s.callsign AND p.timestamp<?
                 )""",
            (a, b, a),
        ).fetchone()[0]
    packets = int(packet["packets"] or 0)
    fingerprinted = int(packet["fingerprinted"] or 0)
    fingerprints = int(packet["fingerprints"] or 0)
    duplicates = max(0, fingerprinted - fingerprints) if fingerprinted else 0
    return {
        "packets": packets,
        "stations": int(packet["stations"] or 0),
        "rf_packets": int(packet["rf"] or 0),
        "aprsis_packets": int(packet["aprsis"] or 0),
        "duplicates": duplicates,
        "duplicate_rate": round((duplicates / packets * 100.0), 2) if packets else 0.0,
        "messages": int(msg["messages"] or 0),
        "acked_messages": int(msg["acked"] or 0),
        "rejected_messages": int(msg["rejected"] or 0),
        "ack_rate": round((int(msg["acked"] or 0) / int(msg["messages"] or 1) * 100.0), 2) if int(msg["messages"] or 0) else 0.0,
        "query_rtt_avg_ms": round(statistics.fmean(rtts), 1) if rtts else None,
        "query_rtt_median_ms": round(statistics.median(rtts), 1) if rtts else None,
        "topology_events": int(edges or 0),
        "new_stations": int(first_seen or 0),
        "start": a,
        "end": b,
    }


def _period_comparison(hours: int) -> dict[str, Any]:
    end = _now()
    current_start = end - timedelta(hours=hours)
    previous_start = current_start - timedelta(hours=hours)
    current = _window_counts(current_start, end)
    previous = _window_counts(previous_start, current_start)

    def delta(key: str) -> dict[str, Any]:
        cur = current.get(key)
        prev = previous.get(key)
        if not isinstance(cur, (int, float)) or not isinstance(prev, (int, float)):
            return {"current": cur, "previous": prev, "delta": None, "percent": None}
        d = cur - prev
        pct = None if prev == 0 else round((d / prev) * 100.0, 2)
        return {"current": cur, "previous": prev, "delta": d, "percent": pct, "new": bool(prev == 0 and cur > 0)}

    keys = ["packets", "stations", "rf_packets", "aprsis_packets", "duplicates", "messages", "acked_messages", "topology_events", "new_stations"]
    return {"hours": hours, "current": current, "previous": previous, "changes": {key: delta(key) for key in keys}}


def _quality(hours: int) -> dict[str, Any]:
    end = _now()
    start = end - timedelta(hours=hours)
    base = _window_counts(start, end)
    prior_start = start - timedelta(hours=hours)
    with db.connection() as conn:
        current_calls = {
            row[0] for row in conn.execute(
                "SELECT DISTINCT from_call FROM packets WHERE timestamp>=? AND timestamp<? AND from_call IS NOT NULL AND from_call<>''",
                (_iso(start), _iso(end)),
            ).fetchall()
        }
        previous_calls = {
            row[0] for row in conn.execute(
                "SELECT DISTINCT from_call FROM packets WHERE timestamp>=? AND timestamp<? AND from_call IS NOT NULL AND from_call<>''",
                (_iso(prior_start), _iso(start)),
            ).fetchall()
        }
        types = [
            {"type": row[0] or "unknown", "count": int(row[1] or 0)}
            for row in conn.execute(
                """SELECT COALESCE(NULLIF(packet_format,''),'unknown'),COUNT(*)
                   FROM packets WHERE timestamp>=? AND timestamp<?
                   GROUP BY COALESCE(NULLIF(packet_format,''),'unknown')
                   ORDER BY COUNT(*) DESC LIMIT 20""",
                (_iso(start), _iso(end)),
            ).fetchall()
        ]
    base["new_vs_previous"] = sorted(current_calls - previous_calls)
    base["disappeared_vs_previous"] = sorted(previous_calls - current_calls)
    base["packet_types"] = types
    base["period_hours"] = hours
    return base


def _graph(hours: int) -> dict[str, Any]:
    cutoff = _iso(_now() - timedelta(hours=hours))
    with db.connection() as conn:
        edges = [
            dict(row) for row in conn.execute(
                """SELECT source,target,kind,COUNT(*) AS interactions,
                          MIN(timestamp) AS first_seen,MAX(timestamp) AS last_seen
                   FROM topology_events WHERE timestamp>=?
                   GROUP BY source,target,kind
                   ORDER BY interactions DESC LIMIT 2000""",
                (cutoff,),
            ).fetchall()
        ]
        station_meta = {
            row["callsign"]: dict(row)
            for row in conn.execute(
                """SELECT callsign,name,last_heard,latitude,longitude,symbol_table,symbol
                   FROM stations"""
            ).fetchall()
        }
    node_ids = set()
    for edge in edges:
        node_ids.add(edge["source"])
        node_ids.add(edge["target"])
    nodes = []
    degree: dict[str, int] = {node: 0 for node in node_ids}
    for edge in edges:
        degree[edge["source"]] = degree.get(edge["source"], 0) + int(edge["interactions"] or 0)
        degree[edge["target"]] = degree.get(edge["target"], 0) + int(edge["interactions"] or 0)
    for node in node_ids:
        meta = station_meta.get(node, {})
        nodes.append({"id": node, "degree": degree.get(node, 0), **meta})
    nodes.sort(key=lambda item: int(item.get("degree") or 0), reverse=True)
    return {"hours": hours, "nodes": nodes, "edges": edges}


def _csv_export(hours: int) -> bytes:
    cutoff = _iso(_now() - timedelta(hours=hours))
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["timestamp", "callsign", "packet_format", "medium", "raw"])
    with db.connection() as conn:
        for row in conn.execute(
            """SELECT timestamp,from_call,packet_format,medium,raw
               FROM packets WHERE timestamp>=? ORDER BY timestamp""",
            (cutoff,),
        ):
            writer.writerow([row["timestamp"], row["from_call"], row["packet_format"], row["medium"], row["raw"]])
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def _geojson_export(hours: int) -> dict[str, Any]:
    cutoff = _iso(_now() - timedelta(hours=hours))
    features: list[dict[str, Any]] = []
    with db.connection() as conn:
        rows = conn.execute(
            """SELECT callsign,last_heard,latitude,longitude,speed,course,altitude,info,path
               FROM stations WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND last_heard>=?""",
            (cutoff,),
        ).fetchall()
        for row in rows:
            d = dict(row)
            lon, lat = d.pop("longitude"), d.pop("latitude")
            features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": d})
        for row in conn.execute(
            """SELECT callsign,timestamp,latitude,longitude,speed,course,altitude,path,rssi,snr
               FROM tracks WHERE timestamp>=? ORDER BY callsign,timestamp""",
            (cutoff,),
        ).fetchall():
            d = dict(row)
            lon, lat = d.pop("longitude"), d.pop("latitude")
            features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": {"feature_kind": "trackpoint", **d}})
    return {"type": "FeatureCollection", "features": features}


def _diagnostic_summary() -> dict[str, Any]:
    db_path = Path(db.DB_PATH)
    integrity = "unknown"
    counts: dict[str, int] = {}
    migrations: dict[str, Any] = {}
    with db.connection() as conn:
        try:
            integrity = str(conn.execute("PRAGMA quick_check").fetchone()[0])
        except Exception as exc:
            integrity = f"error: {exc}"
        for table in ("stations", "tracks", "messages", "packets", "topology_events", "aprs_queries"):
            try:
                counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            except Exception:
                counts[table] = -1
        migrations["packets_columns"] = [row["name"] for row in conn.execute("PRAGMA table_info(packets)").fetchall()]
        migrations["config_columns"] = [row["name"] for row in conn.execute("PRAGMA table_info(config)").fetchall()]
    disk = shutil.disk_usage(db_path.parent if db_path.parent.exists() else Path.home())
    return {
        "version": __version__,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "database": {
            "path": str(db_path),
            "exists": db_path.exists(),
            "size_bytes": db_path.stat().st_size if db_path.exists() else 0,
            "quick_check": integrity,
            "counts": counts,
            "schema": migrations,
        },
        "disk": {"free_bytes": disk.free, "total_bytes": disk.total},
        "aprs_is": service.status(),
        "tnc": tnc_service.status(),
        "local_server": local_server_runtime_info(),
    }


def _support_zip() -> tuple[io.BytesIO, str]:
    payload = _diagnostic_summary()
    stamp = _now().strftime("%Y%m%d_%H%M%S")
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("diagnostic_summary.json", json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        log_candidates = [
            Path(db.DB_PATH).parent / "diagnostics.log",
            Path(db.DB_PATH).parent.parent / "diagnostics.log",
        ]
        config = db.get_config()
        sensitive_values = [
            str(config.get("passcode") or ""),
            str(config.get("email") or ""),
        ]
        for path in log_candidates:
            if path.exists() and path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                for value in sensitive_values:
                    if value:
                        text = text.replace(value, "***")
                text = text.replace("passcode", "passcode(masked)")
                archive.writestr("diagnostics.log", text[-2_000_000:])
                break
    memory.seek(0)
    return memory, f"PT2VHF_APRS_Client_Diagnostics_{stamp}.zip"


def register_advanced_routes(app) -> None:
    @app.get("/api/v1818/stations/search")
    def api_v1818_station_search():
        return jsonify(_station_rows(request.args.get("q", ""), request.args.get("limit", 20)))

    @app.get("/api/v1818/network-quality")
    def api_v1818_network_quality():
        return jsonify(_quality(_hours_arg()))

    @app.get("/api/v1818/period-compare")
    def api_v1818_period_compare():
        return jsonify(_period_comparison(_hours_arg()))

    @app.get("/api/v1818/topology-graph")
    def api_v1818_topology_graph():
        return jsonify(_graph(_hours_arg()))

    @app.get("/api/v1818/export.csv")
    def api_v1818_export_csv():
        hours = _hours_arg(168)
        body = _csv_export(hours)
        name = f"PT2VHF_APRS_export_{hours}h.csv"
        return Response(body, mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{name}"'})

    @app.get("/api/v1818/export.geojson")
    def api_v1818_export_geojson():
        hours = _hours_arg(168)
        payload = json.dumps(_geojson_export(hours), ensure_ascii=False).encode("utf-8")
        name = f"PT2VHF_APRS_export_{hours}h.geojson"
        return Response(payload, mimetype="application/geo+json", headers={"Content-Disposition": f'attachment; filename="{name}"'})

    @app.get("/api/v1818/diagnostics")
    def api_v1818_diagnostics():
        return jsonify(_diagnostic_summary())

    @app.get("/api/v1818/diagnostics.zip")
    def api_v1818_diagnostics_zip():
        memory, filename = _support_zip()
        diag.log_event("support_package_generated", filename=filename)
        return send_file(memory, mimetype="application/zip", as_attachment=True, download_name=filename)
