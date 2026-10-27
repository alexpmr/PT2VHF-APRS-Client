"""Últimos resultados calculados das Estatísticas (v1.14.61).

Estatísticas do histórico e Recordes RF são caros. O último resultado de cada
combinação de parâmetros fica no SQLite e é reaproveitado ao reabrir a aba;
só é recalculado quando o usuário pede (Recalcular).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from . import database as db
from . import diagnostics as diag


def _ensure(conn) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS saved_results (
        kind TEXT NOT NULL, key TEXT NOT NULL, payload TEXT NOT NULL, saved_at TEXT NOT NULL,
        PRIMARY KEY(kind, key))""")


def save(kind: str, key: Any, payload: Any) -> str:
    saved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with db.connection() as conn:
            _ensure(conn)
            conn.execute(
                "INSERT INTO saved_results(kind,key,payload,saved_at) VALUES(?,?,?,?) "
                "ON CONFLICT(kind,key) DO UPDATE SET payload=excluded.payload,saved_at=excluded.saved_at",
                (kind, json.dumps(key), json.dumps(payload, ensure_ascii=False, default=str), saved_at))
    except Exception as exc:  # guardar é conveniência; nunca derruba o cálculo
        diag.log_event("saved_results_write_failed", kind=kind, error=str(exc))
    return saved_at


def load(kind: str, key: Any) -> tuple[Any, str] | None:
    try:
        with db.connection() as conn:
            _ensure(conn)
            row = conn.execute("SELECT payload,saved_at FROM saved_results WHERE kind=? AND key=?",
                               (kind, json.dumps(key))).fetchone()
        return (json.loads(row["payload"]), str(row["saved_at"])) if row else None
    except Exception as exc:
        diag.log_event("saved_results_read_failed", kind=kind, error=str(exc))
        return None
