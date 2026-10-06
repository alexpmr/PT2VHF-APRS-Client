from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import jsonify, request

from . import database as db
from .tnc_service import (
    KissStreamDecoder,
    decode_ax25,
    encode_ax25,
    get_tnc_config,
    kiss_encode,
    service as tnc_service,
)
from .tnc_simulator import KISSSimulator, SimulatedPacket


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _ensure_schema() -> None:
    with db.connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notifications_v111(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'info',
                title TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                entity TEXT NOT NULL DEFAULT '',
                read_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_v111_time
              ON notifications_v111(timestamp DESC);

            CREATE TABLE IF NOT EXISTS settings_v111(
                key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tnc_health_events_v111(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                health_state TEXT NOT NULL,
                connected INTEGER NOT NULL DEFAULT 0,
                transport TEXT NOT NULL DEFAULT '',
                endpoint TEXT NOT NULL DEFAULT '',
                frames_rx INTEGER NOT NULL DEFAULT 0,
                frames_tx INTEGER NOT NULL DEFAULT 0,
                bytes_rx INTEGER NOT NULL DEFAULT 0,
                bytes_tx INTEGER NOT NULL DEFAULT 0,
                detail TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_tnc_health_v111_time
              ON tnc_health_events_v111(timestamp DESC);
            """
        )


RETENTION_DEFAULTS = {
    "packets_days": 180,
    "tracks_days": 365,
    "aprs_log_days": 90,
    "topology_events_days": 180,
    "tnc_frames_days": 180,
    "tnc_decisions_days": 180,
    "notifications_days": 90,
    "messages_days": 0,
}


def _setting(key: str, default: dict[str, Any]) -> dict[str, Any]:
    _ensure_schema()
    with db.connection() as conn:
        row = conn.execute("SELECT payload FROM settings_v111 WHERE key=?", (key,)).fetchone()
    if not row:
        return dict(default)
    try:
        value = json.loads(row["payload"])
        return {**default, **value} if isinstance(value, dict) else dict(default)
    except Exception:
        return dict(default)


def _save_setting(key: str, payload: dict[str, Any], default: dict[str, Any]) -> dict[str, Any]:
    _ensure_schema()
    clean = {**default, **dict(payload or {})}
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO settings_v111(key,payload,updated_at) VALUES(?,?,?)
               ON CONFLICT(key) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at""",
            (key, json.dumps(clean, ensure_ascii=False, sort_keys=True), _utc()),
        )
    return clean


def add_notification(
    category: str,
    title: str,
    detail: str = "",
    *,
    severity: str = "info",
    entity: str = "",
) -> dict[str, Any]:
    _ensure_schema()
    category = str(category or "system")[:64]
    severity = str(severity or "info")[:16]
    with db.connection() as conn:
        cur = conn.execute(
            """INSERT INTO notifications_v111(timestamp,category,severity,title,detail,entity)
               VALUES(?,?,?,?,?,?)""",
            (_utc(), category, severity, str(title or "")[:300], str(detail or "")[:3000], str(entity or "")[:120]),
        )
        nid = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM notifications_v111 WHERE id=?", (nid,)).fetchone()
    return dict(row)


def _notifications(limit: int = 100, unread_only: bool = False) -> list[dict[str, Any]]:
    _ensure_schema()
    where = "WHERE read_at IS NULL" if unread_only else ""
    with db.connection() as conn:
        rows = conn.execute(
            f"""SELECT * FROM notifications_v111 {where}
                ORDER BY id DESC LIMIT ?""",
            (max(1, min(int(limit), 500)),),
        ).fetchall()
    return [dict(row) for row in rows]


def _tnc_db_session_counts(connected_since: str) -> dict[str, Any]:
    counts = {"frames_rx": 0, "frames_tx": 0, "last_frame_rx": "", "last_frame_tx": ""}
    if not connected_since:
        return counts
    try:
        with db.connection() as conn:
            if not _table_exists(conn, "tnc_frames"):
                return counts
            for direction, key, last_key in (
                ("RX", "frames_rx", "last_frame_rx"),
                ("TX", "frames_tx", "last_frame_tx"),
            ):
                row = conn.execute(
                    """SELECT COUNT(*) AS c, MAX(timestamp) AS last_at
                       FROM tnc_frames WHERE direction=? AND timestamp>=?""",
                    (direction, connected_since),
                ).fetchone()
                counts[key] = int(row["c"] or 0)
                counts[last_key] = str(row["last_at"] or "")
    except Exception:
        pass
    return counts


def tnc_health_snapshot(*, record_transition: bool = True) -> dict[str, Any]:
    _ensure_schema()
    status = tnc_service.status()
    connected_since = str(status.get("connected_since") or "")
    persisted = _tnc_db_session_counts(connected_since)

    # Reconciliation: runtime counters are fast; persisted frames are authoritative
    # evidence that traffic actually crossed the parser.
    frames_rx = max(int(status.get("frames_rx") or 0), int(persisted["frames_rx"] or 0))
    frames_tx = max(int(status.get("frames_tx") or 0), int(persisted["frames_tx"] or 0))
    bytes_rx = int(status.get("transport_bytes_rx") or 0)
    bytes_tx = int(status.get("transport_bytes_tx") or 0)
    kiss_rx = int(status.get("kiss_frames_rx") or 0)
    invalid = int(status.get("invalid_frames_rx") or 0)
    cfg = get_tnc_config()
    expected_protocol = str(cfg.get("serial_protocol") or ("agwpe" if str(cfg.get("transport") or "") == "agwpe" else "kiss"))
    device_profile = str(cfg.get("device_profile") or "generic_kiss")

    if not status.get("connected"):
        state = "disconnected"
        summary = "Transporte desconectado."
    elif frames_rx > 0 and frames_tx > 0:
        state = "rx_tx_active"
        summary = "RX e TX observados nesta sessão."
    elif frames_rx > 0:
        state = "rx_active"
        summary = "AX.25 RX operacional; nenhum TX confirmado nesta sessão."
    elif kiss_rx > 0 and invalid > 0:
        state = "kiss_invalid_ax25"
        summary = "Frames KISS chegam, mas há AX.25 inválido."
    elif kiss_rx > 0:
        state = "kiss_active"
        summary = "KISS detectado; aguardando AX.25 válido."
    elif bytes_rx > 0 and expected_protocol == "terminal":
        sample = str(status.get("last_transport_sample_ascii") or "")
        prompt_like = any(token in sample.upper() for token in ("CMD:", "COMMAND", "TNC>", "CMD>"))
        state = "terminal_prompt_detected" if prompt_like else "terminal_bytes_active"
        if device_profile in {"kenwood_tm_d700", "kenwood_tm_d710"}:
            summary = "Serial ativa em modo terminal/PKT; bytes recebidos. KISS não é exigido por este perfil."
        else:
            summary = "Bytes recebidos pelo TNC em protocolo terminal; KISS não é o protocolo esperado."
    elif bytes_rx > 0:
        state = "bytes_without_kiss"
        summary = "Bytes recebidos, mas nenhum frame KISS reconhecido."
    else:
        state = "transport_open_waiting"
        summary = "Transporte aberto, aguardando dados."

    snapshot = {
        **status,
        "health_state": state,
        "health_summary": summary,
        "frames_rx": frames_rx,
        "frames_tx": frames_tx,
        "persisted_frames_rx": persisted["frames_rx"],
        "persisted_frames_tx": persisted["frames_tx"],
        "last_frame_rx": persisted["last_frame_rx"] or status.get("last_rx_at") or "",
        "last_frame_tx": persisted["last_frame_tx"] or status.get("last_tx_at") or "",
        "transport_bytes_rx": bytes_rx,
        "transport_bytes_tx": bytes_tx,
        "kiss_frames_rx": kiss_rx,
        "invalid_frames_rx": invalid,
        "expected_protocol": expected_protocol,
        "device_profile": device_profile,
        "serial_baud": cfg.get("serial_baud"),
        "packet_rf_baud": cfg.get("packet_rf_baud"),
        "diagnostic_sample_hex": str(status.get("last_transport_sample_hex") or ""),
        "diagnostic_sample_ascii": str(status.get("last_transport_sample_ascii") or ""),
    }

    if record_transition:
        with db.connection() as conn:
            previous = conn.execute(
                "SELECT * FROM tnc_health_events_v111 ORDER BY id DESC LIMIT 1"
            ).fetchone()
            signature_changed = (
                previous is None
                or str(previous["health_state"]) != state
                or bool(previous["connected"]) != bool(status.get("connected"))
                or str(previous["transport"] or "") != str(status.get("transport") or "")
                or str(previous["endpoint"] or "") != str(status.get("endpoint") or "")
            )
            if signature_changed:
                conn.execute(
                    """INSERT INTO tnc_health_events_v111(
                         timestamp,health_state,connected,transport,endpoint,
                         frames_rx,frames_tx,bytes_rx,bytes_tx,detail
                       ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (
                        _utc(), state, int(bool(status.get("connected"))),
                        str(status.get("transport") or ""), str(status.get("endpoint") or ""),
                        frames_rx, frames_tx, bytes_rx, bytes_tx, summary,
                    ),
                )
    return snapshot


def tnc_health_timeline(limit: int = 100) -> list[dict[str, Any]]:
    _ensure_schema()
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tnc_health_events_v111 ORDER BY id DESC LIMIT ?",
            (max(1, min(int(limit), 500)),),
        ).fetchall()
    return [dict(row) for row in rows]


def run_tnc_self_test() -> dict[str, Any]:
    packets = KISSSimulator.multi_hop_demo()
    simulator = KISSSimulator(fragment_size=7, duplicate_every=2)
    decoder = KissStreamDecoder()
    decoded: list[dict[str, Any]] = []
    chunks = simulator.scenario(packets)
    bytes_rx = 0
    kiss_frames = 0
    invalid = 0
    for chunk in chunks:
        bytes_rx += len(chunk)
        for command, payload in decoder.feed(chunk):
            if (command & 0x0F) != 0 or not payload:
                continue
            kiss_frames += 1
            try:
                decoded.append(decode_ax25(payload))
            except Exception:
                invalid += 1

    tx_frame = encode_ax25("PT2TST", "APZVHF", ":PT2DST  :teste{01", ["WIDE1-1"])
    tx_wire = kiss_encode(tx_frame)
    tx_decoded = []
    tx_decoder = KissStreamDecoder()
    for command, payload in tx_decoder.feed(tx_wire):
        if (command & 0x0F) == 0 and payload:
            tx_decoded.append(decode_ax25(payload))

    checks = {
        "transport_internal": bool(chunks),
        "kiss_rx": kiss_frames >= len(packets),
        "ax25_rx": len(decoded) >= len(packets),
        "parser_aprs_payload": any("teste" in item.get("info_text", "") for item in decoded),
        "rx_counter_model": kiss_frames > 0 and len(decoded) > 0,
        "tx_queue_model": bool(tx_wire),
        "kiss_tx": len(tx_decoded) == 1,
        "ax25_tx": bool(tx_decoded and tx_decoded[0]["source"] == "PT2TST"),
        "ack_frame": any("ack01" in item.get("info_text", "") for item in decoded),
    }
    layers = {
        "transport": bool(checks["transport_internal"]),
        "framing_protocol": bool(checks["kiss_rx"]),
        "ax25": bool(checks["ax25_rx"] and checks["ax25_tx"]),
        "rx": bool(checks["ax25_rx"]),
        "tx_model": bool(checks["kiss_tx"] and checks["ax25_tx"]),
        "physical_rf_tx": False,
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "layers": layers,
        "physical_validation_note": "Autoteste interno não confirma emissão RF física; valide RX/TX no ar com rádio real.",
        "bytes_rx": bytes_rx,
        "kiss_frames_rx": kiss_frames,
        "ax25_valid_rx": len(decoded),
        "ax25_invalid_rx": invalid,
        "simulated_packets": len(packets),
        "tx_wire_bytes": len(tx_wire),
    }


def db_health() -> dict[str, Any]:
    path = Path(db.DB_PATH)
    result: dict[str, Any] = {
        "path": str(path),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "integrity": "unknown",
        "page_count": 0,
        "freelist_count": 0,
        "fragmentation_percent": 0.0,
        "wal_bytes": 0,
        "tables": {},
    }
    wal = Path(str(path) + "-wal")
    if wal.exists():
        result["wal_bytes"] = wal.stat().st_size
    with db.connection() as conn:
        try:
            result["integrity"] = str(conn.execute("PRAGMA quick_check").fetchone()[0])
        except Exception as exc:
            result["integrity"] = f"error: {exc}"
        result["page_count"] = int(conn.execute("PRAGMA page_count").fetchone()[0] or 0)
        result["freelist_count"] = int(conn.execute("PRAGMA freelist_count").fetchone()[0] or 0)
        if result["page_count"]:
            result["fragmentation_percent"] = round(
                result["freelist_count"] * 100.0 / result["page_count"], 2
            )
        for table in (
            "packets", "tracks", "messages", "aprs_log", "topology_events",
            "tnc_frames", "tnc_decisions", "notifications_v111",
        ):
            if _table_exists(conn, table):
                try:
                    result["tables"][table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                except Exception:
                    result["tables"][table] = -1
    return result


def retention_settings() -> dict[str, Any]:
    values = _setting("retention", RETENTION_DEFAULTS)
    for key in RETENTION_DEFAULTS:
        try:
            values[key] = max(0, min(int(values.get(key, RETENTION_DEFAULTS[key])), 3650))
        except Exception:
            values[key] = RETENTION_DEFAULTS[key]
    return values


def apply_retention(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    values = retention_settings() if settings is None else _save_setting("retention", settings, RETENTION_DEFAULTS)
    table_keys = {
        "packets": "packets_days",
        "tracks": "tracks_days",
        "messages": "messages_days",
        "aprs_log": "aprs_log_days",
        "topology_events": "topology_events_days",
        "tnc_frames": "tnc_frames_days",
        "tnc_decisions": "tnc_decisions_days",
        "notifications_v111": "notifications_days",
    }
    deleted: dict[str, int] = {}
    with db.connection() as conn:
        for table, key in table_keys.items():
            days = int(values.get(key) or 0)
            if days <= 0 or not _table_exists(conn, table):
                deleted[table] = 0
                continue
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0).isoformat()
            try:
                cur = conn.execute(f"DELETE FROM {table} WHERE timestamp<?", (cutoff,))
                deleted[table] = max(0, int(cur.rowcount or 0))
            except sqlite3.OperationalError:
                deleted[table] = 0
    db.invalidate_map_data_cache(drop_payload=True)
    return {"settings": values, "deleted": deleted, "health": db_health()}


def optimize_database() -> dict[str, Any]:
    before = db_health()
    with db.connection() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA optimize")
    # VACUUM cannot run inside the managed transaction/context reliably.
    raw = sqlite3.connect(db.DB_PATH, timeout=60)
    try:
        raw.execute("VACUUM")
    finally:
        raw.close()
    after = db_health()
    return {"before": before, "after": after}


def station_operational_profile(callsign: str, hours: int = 24) -> dict[str, Any]:
    call = str(callsign or "").upper().strip()
    if not call:
        raise ValueError("Indicativo inválido.")
    hours = max(1, min(int(hours or 24), 24 * 365))
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).replace(microsecond=0).isoformat()
    result: dict[str, Any] = {
        "callsign": call,
        "period_hours": hours,
        "station": {},
        "summary": {},
        "heard_by": [],
        "paths": [],
        "messages": 0,
    }
    with db.connection() as conn:
        if _table_exists(conn, "stations"):
            row = conn.execute("SELECT * FROM stations WHERE UPPER(callsign)=?", (call,)).fetchone()
            result["station"] = dict(row) if row else {}
        if _table_exists(conn, "packets"):
            row = conn.execute(
                """SELECT COUNT(*) AS packets,
                          MIN(timestamp) AS first_seen,
                          MAX(timestamp) AS last_seen,
                          SUM(CASE WHEN UPPER(COALESCE(medium,''))='RF' THEN 1 ELSE 0 END) AS rf_packets,
                          SUM(CASE WHEN UPPER(COALESCE(medium,''))='APRS-IS' THEN 1 ELSE 0 END) AS aprsis_packets
                   FROM packets WHERE UPPER(from_call)=?""",
                (call,),
            ).fetchone()
            result["summary"].update(dict(row))
        if _table_exists(conn, "tnc_frames"):
            path_rows = conn.execute(
                """SELECT path,'RF' AS medium,COUNT(*) AS packets,MAX(timestamp) AS last_seen
                   FROM tnc_frames
                   WHERE UPPER(source)=? AND timestamp>=? AND COALESCE(path,'') NOT IN ('','[]')
                   GROUP BY path ORDER BY packets DESC,last_seen DESC LIMIT 50""",
                (call, cutoff),
            ).fetchall()
            result["paths"] = [dict(row) for row in path_rows]
        if not result["paths"] and result.get("station", {}).get("path"):
            result["paths"] = [{
                "path": result["station"]["path"],
                "medium": "",
                "packets": 1,
                "last_seen": result["station"].get("last_heard") or "",
            }]
        if _table_exists(conn, "messages"):
            result["messages"] = int(conn.execute(
                """SELECT COUNT(*) FROM messages
                   WHERE UPPER(from_call)=? OR UPPER(to_call)=?""",
                (call, call),
            ).fetchone()[0] or 0)
        if _table_exists(conn, "tnc_heard"):
            row = conn.execute("SELECT * FROM tnc_heard WHERE UPPER(callsign)=?", (call,)).fetchone()
            if row:
                result["tnc_heard"] = dict(row)
        # 'Ouvido por' is grounded in topology observations involving this station.
        if _table_exists(conn, "topology_events"):
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(topology_events)").fetchall()}
            if {"source", "target", "timestamp"} <= cols:
                rows = conn.execute(
                    """SELECT target AS observer,COUNT(*) AS observations,MAX(timestamp) AS last_seen
                       FROM topology_events
                       WHERE UPPER(source)=? AND timestamp>=?
                       GROUP BY target ORDER BY observations DESC,last_seen DESC LIMIT 50""",
                    (call, cutoff),
                ).fetchall()
                result["heard_by"] = [dict(row) for row in rows]
        if not result["heard_by"] and _table_exists(conn, "tnc_edges"):
            rows = conn.execute(
                """SELECT destination AS observer,medium,interactions AS observations,last_seen
                   FROM tnc_edges WHERE UPPER(source)=? AND last_seen>=?
                   ORDER BY interactions DESC,last_seen DESC LIMIT 50""",
                (call, cutoff),
            ).fetchall()
            result["heard_by"] = [dict(row) for row in rows]
    return result


def register_v111_routes(app) -> None:
    _ensure_schema()

    @app.get("/api/v111/tnc/health")
    def api_v111_tnc_health():
        return jsonify(tnc_health_snapshot())

    @app.get("/api/v111/tnc/timeline")
    def api_v111_tnc_timeline():
        return jsonify(tnc_health_timeline(request.args.get("limit", 100)))

    @app.post("/api/v111/tnc/self-test")
    def api_v111_tnc_self_test():
        return jsonify(run_tnc_self_test())

    @app.get("/api/v111/notifications")
    def api_v111_notifications():
        return jsonify(_notifications(request.args.get("limit", 100), request.args.get("unread") in {"1","true"}))

    @app.post("/api/v111/notifications")
    def api_v111_add_notification():
        data = request.get_json(force=True) or {}
        return jsonify({"ok": True, "notification": add_notification(
            data.get("category", "system"), data.get("title", ""), data.get("detail", ""),
            severity=data.get("severity", "info"), entity=data.get("entity", ""),
        )})

    @app.post("/api/v111/notifications/read")
    def api_v111_notifications_read():
        data = request.get_json(silent=True) or {}
        ids = data.get("ids") or []
        with db.connection() as conn:
            if ids:
                clean = [int(x) for x in ids if str(x).isdigit()]
                if clean:
                    placeholders = ",".join("?" for _ in clean)
                    conn.execute(f"UPDATE notifications_v111 SET read_at=? WHERE id IN ({placeholders})", (_utc(), *clean))
            else:
                conn.execute("UPDATE notifications_v111 SET read_at=? WHERE read_at IS NULL", (_utc(),))
        return jsonify({"ok": True})

    @app.get("/api/v111/db/health")
    def api_v111_db_health():
        return jsonify(db_health())

    @app.get("/api/v111/db/retention")
    def api_v111_db_retention():
        return jsonify(retention_settings())

    @app.post("/api/v111/db/retention")
    def api_v111_save_retention():
        data = request.get_json(force=True) or {}
        return jsonify({"ok": True, "settings": _save_setting("retention", data, RETENTION_DEFAULTS)})

    @app.post("/api/v111/db/retention/apply")
    def api_v111_apply_retention():
        return jsonify({"ok": True, **apply_retention()})

    @app.post("/api/v111/db/optimize")
    def api_v111_optimize_db():
        return jsonify({"ok": True, **optimize_database()})

    @app.get("/api/v111/station/<callsign>/profile")
    def api_v111_station_profile(callsign: str):
        return jsonify(station_operational_profile(callsign, request.args.get("hours", 24)))
