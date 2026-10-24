"""Políticas seguras de retenção, independentes da visualização do mapa.

A exclusão de estações nunca remove topology_edges: os enlaces preservam
source/target e não usam FK em cascata. Manutenção em lotes pequenos.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from . import database as db
from . import diagnostics as diag

# Dias: 0 = permanente. Sem expiração automática de enlaces RF por padrão.
# v1.14.58: tudo permanente por padrão. Prazos curtos só quando o usuário escolher.
DEFAULT_DAYS = {
    "stations": 0,
    "digis": 0,
    "igates": 0,
    "rf_links": 0,
    "internet_links": 0,
    "objects": 0,
    "tracks": 0,
    "messages": 0,
    "bulletins": 0,
    "groups": 0,
    "packets": 0,
    "aprs_log": 0,
    "topology_events": 0,
    # Mapa de calor da Cobertura RF: retenção própria, independente das demais.
    "rf_coverage": 0,
}
# Padrões até a v1.14.57; categorias ainda com esses valores passam a permanentes.
LEGACY_DEFAULT_DAYS = {
    "stations": 30, "internet_links": 30, "objects": 30, "tracks": 30,
    "messages": 90, "bulletins": 30, "groups": 90, "packets": 30,
    "aprs_log": 30, "topology_events": 30,
}
PERMANENT_DEFAULTS_MIGRATION = "v1.14.58-retention-permanent-defaults"
PERIODS = (0, 1, 7, 30, 90, 180, 365)
CATEGORIES = tuple(DEFAULT_DAYS)
_lock = threading.Lock()
_thread = None


def ensure_schema() -> None:
    with db.connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS retention_policies (
            category TEXT PRIMARY KEY, days INTEGER NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS retention_state (
            id INTEGER PRIMARY KEY CHECK(id=1),
            enabled INTEGER NOT NULL DEFAULT 0,
            last_run TEXT, last_deleted INTEGER NOT NULL DEFAULT 0)""")
        # Instalações antigas exigem consentimento antes da primeira purga.
        if conn.execute("SELECT 1 FROM retention_state WHERE id=1").fetchone() is None:
            existing = any(
                conn.execute("SELECT 1 FROM " + name + " LIMIT 1").fetchone()
                for name in ("stations", "messages", "topology_edges", "packets")
            )
            conn.execute("INSERT INTO retention_state(id,enabled) VALUES(1,?)",
                         (0 if existing else 1,))
        for category, days in DEFAULT_DAYS.items():
            conn.execute(
                "INSERT OR IGNORE INTO retention_policies(category,days) VALUES(?,?)",
                (category, days),
            )
        _migrate_to_permanent_defaults(conn)


def _migrate_to_permanent_defaults(conn) -> None:
    """Uma vez: categorias que mantêm o padrão antigo passam a Permanente.

    Só aumenta a retenção (nunca apaga dados). Prazo diferente do padrão
    antigo foi escolha do usuário e é preservado.
    """
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations_v112 (
        migration_key TEXT PRIMARY KEY, applied_at TEXT NOT NULL)""")
    if conn.execute("SELECT 1 FROM schema_migrations_v112 WHERE migration_key=?",
                    (PERMANENT_DEFAULTS_MIGRATION,)).fetchone():
        return
    changed = []
    for category, days in LEGACY_DEFAULT_DAYS.items():
        if conn.execute("UPDATE retention_policies SET days=0, updated_at=CURRENT_TIMESTAMP "
                        "WHERE category=? AND days=?", (category, days)).rowcount:
            changed.append(category)
    conn.execute("INSERT INTO schema_migrations_v112(migration_key,applied_at) VALUES(?,?)",
                 (PERMANENT_DEFAULTS_MIGRATION, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    if changed:
        diag.log_event("retention_permanent_defaults_migrated", categories=changed)


def get_policy() -> dict[str, Any]:
    ensure_schema()
    with db.connection() as conn:
        days = dict(DEFAULT_DAYS)
        days.update({str(row["category"]): int(row["days"]) for row in
                     conn.execute("SELECT category,days FROM retention_policies")})
        state = conn.execute("SELECT * FROM retention_state WHERE id=1").fetchone()
    size = sum(p.stat().st_size for p in
               (db.DB_PATH, db.DB_PATH.with_name(db.DB_PATH.name + "-wal"),
                db.DB_PATH.with_name(db.DB_PATH.name + "-shm")) if p.exists())
    return {"policies": days, "enabled": bool(state["enabled"]),
            "last_run": state["last_run"], "last_deleted": int(state["last_deleted"]),
            "db_bytes": size, "db_megabytes": round(size / 1048576, 2),
            "warning": "Acesso LAN e períodos de exibição não alteram a retenção física."}


def save_policy(policies: dict[str, Any], enabled: bool) -> dict[str, Any]:
    ensure_schema()
    if not isinstance(policies, dict) or any(k not in DEFAULT_DAYS for k in policies):
        raise ValueError("Categoria de retenção desconhecida.")
    parsed = {}
    for key, value in policies.items():
        try:
            days = int(value)
        except (TypeError, ValueError):
            raise ValueError("Período inválido: " + key)
        if days not in PERIODS:
            raise ValueError("Período de retenção não permitido: " + key)
        parsed[key] = days
    with db.connection() as conn:
        for key, days in parsed.items():
            conn.execute(
                "UPDATE retention_policies SET days=?, updated_at=CURRENT_TIMESTAMP WHERE category=?",
                (days, key))
        conn.execute("UPDATE retention_state SET enabled=? WHERE id=1",
                     (1 if enabled else 0,))
    diag.log_event("retention_policy_changed", policies=parsed, enabled=bool(enabled))
    return get_policy()


def _cutoff(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")


def _delete_batch(conn, category: str, days: int, limit: int) -> int:
    """SQL fixo por categoria; nunca remover endpoints de topology_edges por FK."""
    if days == 0:
        return 0
    cutoff = _cutoff(days)
    if category in ("stations", "digis", "igates"):
        # Classificação coerente com o ranking de infraestrutura: pacote
        # próprio e evidência observada na topologia, não um WIDE genérico.
        candidates = conn.execute(
            """SELECT rowid,callsign,raw,info,symbol FROM stations
               WHERE last_heard < ? ORDER BY last_heard LIMIT ?""",
            (cutoff, min(2000, limit * 10)),
        ).fetchall()
        selected: list[int] = []
        for row in candidates:
            call = str(row["callsign"] or "").upper().strip()
            meta = db.aprs_map_device_metadata(
                str(row["raw"] or ""), str(row["info"] or ""),
                str(row["symbol"] or ""))
            role = str(meta.get("map_role") or "").lower()
            if role not in {"digi", "igate"}:
                is_igate = conn.execute(
                    "SELECT 1 FROM topology_edges WHERE igate=? LIMIT 1",
                    (call,)).fetchone() is not None
                is_digi = conn.execute(
                    """SELECT 1 FROM topology_edges WHERE kind='rf'
                       AND target=? AND igate IS NULL LIMIT 1""",
                    (call,)).fetchone() is not None
                role = "igate" if is_igate else ("digi" if is_digi else "station")
            classified = {"station":"stations", "digi":"digis",
                          "igate":"igates"}[role if role in {"digi", "igate"} else "station"]
            if classified == category:
                selected.append(int(row["rowid"]))
                if len(selected) >= limit:
                    break
        if not selected:
            return 0
        placeholders = ",".join("?" for _ in selected)
        return max(0, int(conn.execute(
            "DELETE FROM stations WHERE rowid IN (" + placeholders + ")", selected
        ).rowcount or 0))
    if category in ("rf_links", "internet_links"):
        kind = "rf" if category == "rf_links" else "igate"
        sql = """DELETE FROM topology_edges WHERE rowid IN
            (SELECT rowid FROM topology_edges WHERE kind=? AND last_seen < ?
             ORDER BY last_seen LIMIT ?)"""
        args = (kind, cutoff, limit)
    elif category in ("messages", "bulletins", "groups"):
        kind = {"messages": "message", "bulletins": "bulletin",
                "groups": "group"}[category]
        # Mensagens TX com confirmação ainda pendente não expiram.
        sql = """DELETE FROM messages WHERE id IN
            (SELECT id FROM messages
             WHERE lower(message_type)=? AND timestamp < ?
             AND NOT (direction='out' AND lower(status) IN
                      ('pending','sent','queued','retrying','waiting'))
             ORDER BY timestamp LIMIT ?)"""
        args = (kind, cutoff, limit)
    else:
        table, col = {
            "objects": ("aprs_objects", "last_heard"),
            "tracks": ("tracks", "timestamp"),
            "packets": ("packets", "timestamp"),
            "aprs_log": ("aprs_log", "timestamp"),
            "topology_events": ("topology_events", "timestamp"),
            "rf_coverage": ("rf_coverage_cells", "last_seen"),
        }[category]
        sql = "DELETE FROM %s WHERE rowid IN (SELECT rowid FROM %s WHERE %s < ? ORDER BY %s LIMIT ?)" % (
            table, table, col, col)
        args = (cutoff, limit)
    return max(0, int(conn.execute(sql, args).rowcount or 0))


def apply_retention(*, batch_size: int = 150, max_batches: int = 16) -> dict[str, Any]:
    """Runs at most 2400 deletes per call. Background cycles repeat as needed."""
    ensure_schema()
    if not _lock.acquire(blocking=False):
        return {"ok": False, "busy": True, "deleted": 0}
    started = time.monotonic()
    try:
        info = get_policy()
        deleted_by_category: dict[str, int] = {}
        remaining = max(1, min(int(max_batches), 32))
        for category, days in info["policies"].items():
            if not days or remaining <= 0:
                continue
            total = 0
            for _ in range(min(2, remaining)):
                with db.connection() as conn:
                    count = _delete_batch(conn, category, int(days),
                                          max(1, min(int(batch_size), 500)))
                remaining -= 1
                total += count
                if not count or remaining <= 0:
                    break
            if total:
                deleted_by_category[category] = total
        deleted = sum(deleted_by_category.values())
        with db.connection() as conn:
            conn.execute(
                "UPDATE retention_state SET last_run=?,last_deleted=? WHERE id=1",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), deleted))
            if deleted:
                conn.execute("PRAGMA optimize")
        diag.log_event("retention_sweep", deleted=deleted, categories=deleted_by_category,
                       elapsed_ms=round((time.monotonic()-started)*1000))
        return {"ok": True, "deleted": deleted, "categories": deleted_by_category,
                "elapsed_ms": round((time.monotonic()-started)*1000)}
    finally:
        _lock.release()


def _worker() -> None:
    # Delay gives the app time to finish initialization.
    time.sleep(45)
    while True:
        try:
            if get_policy()["enabled"]:
                apply_retention()
        except Exception as exc:
            diag.log_event("retention_worker_error", error=str(exc))
        time.sleep(1800)


def start_worker() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _thread = threading.Thread(target=_worker, name="pt2vhf-retention", daemon=True)
    _thread.start()
