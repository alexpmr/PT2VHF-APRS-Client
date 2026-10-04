from __future__ import annotations

import json
import os
import platform
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Any

from . import database as db
from . import diagnostics as diag


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SoakTestManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._started_at = ""
        self._target_hours = 0.0
        self._interval = 300.0
        self._run_id = ""

    def _ensure_schema(self) -> None:
        with db.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS soak_runs_v110(
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    target_hours REAL NOT NULL,
                    interval_seconds REAL NOT NULL,
                    platform TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS soak_samples_v110(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    process_cpu_percent REAL,
                    process_memory_percent REAL,
                    process_rss_bytes INTEGER,
                    system_cpu_percent REAL,
                    system_memory_percent REAL,
                    thread_count INTEGER,
                    handle_count INTEGER,
                    db_size_bytes INTEGER,
                    active_requests INTEGER,
                    extra_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_soak_samples_run_time
                  ON soak_samples_v110(run_id,timestamp);
                """
            )

    def _sample(self) -> dict[str, Any]:
        metrics = diag.system_metrics()
        db_size = 0
        try:
            db_size = db.DB_PATH.stat().st_size if db.DB_PATH.exists() else 0
        except Exception:
            pass
        handles = None
        try:
            if os.name == "nt":
                import ctypes
                count = ctypes.c_ulong()
                if ctypes.windll.kernel32.GetProcessHandleCount(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(count)):
                    handles = int(count.value)
        except Exception:
            handles = None
        return {
            "timestamp": _utc(),
            "process_cpu_percent": metrics.get("process_cpu_percent"),
            "process_memory_percent": metrics.get("process_memory_percent"),
            "process_rss_bytes": metrics.get("process_rss_bytes"),
            "system_cpu_percent": metrics.get("system_cpu_percent"),
            "system_memory_percent": metrics.get("system_memory_percent"),
            "thread_count": metrics.get("thread_count"),
            "handle_count": handles,
            "db_size_bytes": db_size,
            "active_requests": diag.active_requests(),
        }

    def _run(self) -> None:
        deadline = time.monotonic() + self._target_hours * 3600.0
        try:
            while not self._stop.is_set() and time.monotonic() < deadline:
                sample = self._sample()
                with db.connection() as conn:
                    conn.execute(
                        """INSERT INTO soak_samples_v110(
                             run_id,timestamp,process_cpu_percent,process_memory_percent,process_rss_bytes,
                             system_cpu_percent,system_memory_percent,thread_count,handle_count,db_size_bytes,
                             active_requests,extra_json
                           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            self._run_id, sample["timestamp"], sample["process_cpu_percent"],
                            sample["process_memory_percent"], sample["process_rss_bytes"],
                            sample["system_cpu_percent"], sample["system_memory_percent"],
                            sample["thread_count"], sample["handle_count"], sample["db_size_bytes"],
                            sample["active_requests"], "{}",
                        ),
                    )
                self._stop.wait(self._interval)
        finally:
            with db.connection() as conn:
                conn.execute(
                    "UPDATE soak_runs_v110 SET ended_at=?,status=? WHERE run_id=?",
                    (_utc(), "stopped" if self._stop.is_set() else "completed", self._run_id),
                )

    def start(self, hours: float = 24.0, interval_seconds: float = 300.0) -> dict[str, Any]:
        self._ensure_schema()
        hours = max(0.02, min(float(hours), 24 * 30))
        interval_seconds = max(5.0, min(float(interval_seconds), 3600.0))
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise RuntimeError("Já existe um soak test em execução.")
            self._stop.clear()
            self._started_at = _utc()
            self._target_hours = hours
            self._interval = interval_seconds
            self._run_id = datetime.now(timezone.utc).strftime("soak-%Y%m%dT%H%M%SZ")
            with db.connection() as conn:
                conn.execute(
                    """INSERT INTO soak_runs_v110(run_id,started_at,target_hours,interval_seconds,platform,status)
                       VALUES(?,?,?,?,?,?)""",
                    (self._run_id, self._started_at, hours, interval_seconds, platform.platform(), "running"),
                )
            self._thread = threading.Thread(target=self._run, name="PT2VHF-SoakTest", daemon=True)
            self._thread.start()
        return self.status()

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        return self.status()

    def status(self) -> dict[str, Any]:
        alive = bool(self._thread and self._thread.is_alive())
        return {
            "running": alive,
            "run_id": self._run_id,
            "started_at": self._started_at,
            "target_hours": self._target_hours,
            "interval_seconds": self._interval,
        }

    def report(self) -> dict[str, Any]:
        self._ensure_schema()
        run_id = self._run_id
        with db.connection() as conn:
            if not run_id:
                row = conn.execute("SELECT run_id FROM soak_runs_v110 ORDER BY started_at DESC LIMIT 1").fetchone()
                run_id = row["run_id"] if row else ""
            if not run_id:
                return {"available": False}
            run = conn.execute("SELECT * FROM soak_runs_v110 WHERE run_id=?", (run_id,)).fetchone()
            rows = conn.execute("SELECT * FROM soak_samples_v110 WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        samples = [dict(row) for row in rows]
        rss = [float(x["process_rss_bytes"]) for x in samples if x.get("process_rss_bytes") is not None]
        cpu = [float(x["process_cpu_percent"]) for x in samples if x.get("process_cpu_percent") is not None]
        db_sizes = [float(x["db_size_bytes"]) for x in samples if x.get("db_size_bytes") is not None]
        rss_growth = (rss[-1] - rss[0]) if len(rss) >= 2 else 0.0
        duration_hours = 0.0
        if len(samples) >= 2:
            try:
                a = datetime.fromisoformat(samples[0]["timestamp"])
                b = datetime.fromisoformat(samples[-1]["timestamp"])
                duration_hours = max(0.0, (b - a).total_seconds() / 3600.0)
            except Exception:
                pass
        return {
            "available": True,
            "run": dict(run) if run else {},
            "sample_count": len(samples),
            "duration_hours": round(duration_hours, 3),
            "process_cpu_max": max(cpu) if cpu else None,
            "process_cpu_avg": (sum(cpu) / len(cpu)) if cpu else None,
            "rss_start_bytes": rss[0] if rss else None,
            "rss_end_bytes": rss[-1] if rss else None,
            "rss_growth_bytes": rss_growth,
            "rss_growth_per_hour_bytes": (rss_growth / duration_hours) if duration_hours > 0 else None,
            "db_growth_bytes": (db_sizes[-1] - db_sizes[0]) if len(db_sizes) >= 2 else 0,
            "memory_leak_suspected": bool(duration_hours >= 1 and rss_growth > max(100 * 1024 * 1024, (rss[0] * 0.50 if rss else 0))),
            "latest_sample": samples[-1] if samples else None,
        }


soak_manager = SoakTestManager()
