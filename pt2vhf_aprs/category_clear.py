"""Confirmed, bounded SQLite category clearing with asynchronous jobs.

Each category is independent. Topology links are never cascaded when station
snapshots or packets are deleted. Running message transmissions block removal.
"""
from __future__ import annotations

import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Any

from . import database as db
from . import retention
from . import diagnostics as diag

_lock = threading.RLock()
_jobs: dict[str, dict[str, Any]] = {}
_running: str | None = None
_PENDING = "direction='out' AND LOWER(status) IN ('pending','sent','queued','retrying','waiting')"
_SIMPLE = {
    "rf_links": ("topology_edges", "kind='rf'"),
    "internet_links": ("topology_edges", "kind='igate'"),
    "objects": ("aprs_objects", "1=1"),
    "tracks": ("tracks", "1=1"),
    "packets": ("packets", "1=1"),
    "aprs_log": ("aprs_log", "1=1"),
    "topology_events": ("topology_events", "1=1"),
    "rf_coverage": ("rf_coverage_cells", "1=1"),
    "messages": ("messages", "LOWER(message_type)='message'"),
    "bulletins": ("messages", "LOWER(message_type)='bulletin'"),
    "groups": ("messages", "LOWER(message_type)='group'"),
}


def _station_role(conn, row) -> str:
    call = str(row["callsign"] or "").upper().strip()
    meta = db.aprs_map_device_metadata(
        str(row["raw"] or ""), str(row["info"] or ""), str(row["symbol"] or "")
    )
    role = str(meta.get("map_role") or "").lower()
    if role not in {"digi", "igate"}:
        if conn.execute("SELECT 1 FROM topology_edges WHERE igate=? LIMIT 1", (call,)).fetchone():
            role = "igate"
        elif conn.execute(
            "SELECT 1 FROM topology_edges WHERE kind='rf' AND target=? AND igate IS NULL LIMIT 1", (call,)
        ).fetchone():
            role = "digi"
        else:
            role = "station"
    return {"station": "stations", "digi": "digis", "igate": "igates"}[role]


def preview(category: str) -> dict[str, Any]:
    if category not in retention.CATEGORIES:
        raise ValueError("Categoria de retenção desconhecida.")
    with db.connection() as conn:
        if category in _SIMPLE:
            table, where = _SIMPLE[category]
            total = int(conn.execute("SELECT COUNT(*) FROM " + table + " WHERE " + where).fetchone()[0])
            pending = 0
            if table == "messages":
                pending = int(conn.execute(
                    "SELECT COUNT(*) FROM messages WHERE (" + where + ") AND " + _PENDING
                ).fetchone()[0])
        else:
            total = sum(
                1 for row in conn.execute("SELECT callsign,raw,info,symbol FROM stations")
                if _station_role(conn, row) == category
            )
            pending = 0
    return {"category": category, "count": total, "pending_messages": pending,
            "can_clear": pending == 0}


def _remove_batch(category: str, batch: int) -> int:
    with db.connection() as conn:
        if category in _SIMPLE:
            table, where = _SIMPLE[category]
            return max(0, int(conn.execute(
                "DELETE FROM " + table +
                " WHERE rowid IN (SELECT rowid FROM " + table + " WHERE " + where + " LIMIT ?)",
                (batch,)
            ).rowcount or 0))
        selected = []
        # Scan full table but never delete other station categories.
        for row in conn.execute("SELECT rowid,callsign,raw,info,symbol FROM stations"):
            if _station_role(conn, row) == category:
                selected.append(int(row["rowid"]))
                if len(selected) >= batch:
                    break
        if not selected:
            return 0
        marks = ",".join("?" for _ in selected)
        return max(0, int(conn.execute(
            "DELETE FROM stations WHERE rowid IN (" + marks + ")", selected
        ).rowcount or 0))


def _worker(job_id: str, category: str) -> None:
    global _running
    started = time.monotonic()
    acquired = retention._lock.acquire(timeout=30.0)
    try:
        if not acquired:
            raise RuntimeError("Manutenção do banco está ocupada; tente novamente.")
        while True:
            with _lock:
                job = _jobs[job_id]
                if job["cancel"]:
                    job["status"] = "cancelled"
                    break
                job["status"] = "running"
            deleted = _remove_batch(category, 300)
            with _lock:
                job["deleted"] += deleted
            if not deleted:
                with _lock:
                    job["status"] = "done"
                break
            # Cooperative yield avoids monopolizing the APRS SQLite connection.
            time.sleep(0.01)
        diag.log_event("retention_category_clear", category=category,
                       deleted=_jobs[job_id]["deleted"],
                       status=_jobs[job_id]["status"],
                       elapsed_ms=round((time.monotonic() - started) * 1000))
    except Exception as exc:
        with _lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(exc)
        diag.log_event("retention_category_clear_error", category=category, error=str(exc))
    finally:
        if acquired:
            retention._lock.release()
        with _lock:
            _running = None


def start(category: str, confirmation: str) -> dict[str, Any]:
    global _running
    if category not in retention.CATEGORIES:
        raise ValueError("Categoria de retenção desconhecida.")
    if confirmation != "CLEAR:" + category:
        raise ValueError("Confirmação explícita inválida.")
    info = preview(category)
    if info["pending_messages"]:
        raise ValueError("Há mensagens TX pendentes nesta categoria; conclua-as antes de limpar.")
    with _lock:
        if _running and _jobs.get(_running, {}).get("status") in {"queued", "running"}:
            raise RuntimeError("Outra limpeza do banco já está em andamento.")
        job_id = secrets.token_hex(16)
        _jobs[job_id] = {"job_id": job_id, "category": category, "status": "queued",
                         "total": info["count"], "deleted": 0, "cancel": False, "error": ""}
        _running = job_id
    threading.Thread(target=_worker, args=(job_id, category), daemon=True,
                     name="retention-clear-" + category).start()
    return status(job_id)


def status(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        return {key: value for key, value in job.items() if key != "cancel"}


def cancel(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return False
        job["cancel"] = True
        return True
