"""Armazenamento próprio do mapa de calor de Cobertura RF (v1.14.53).

O mapa de calor era calculado a partir de topology_events e perdia dados
quando a retenção de eventos/enlaces os apagava. Aqui cada transmissão (TX,
posição de quem transmitiu o salto) e recepção RF (RX, posição de quem ouviu
ou repetiu) é somada em células de ~1 km por dia UTC, com retenção própria
(categoria "rf_coverage"), independente de tracklogs, estações, digis e
enlaces.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from . import database as db
from . import diagnostics as diag

CELL_DEGREES = 0.01
MAX_CALLSIGNS_PER_CELL = 8
BACKFILL_KEY = "v1.14.53-rf-coverage-cells-backfill"


def ensure_schema(conn) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS rf_coverage_cells (
               day TEXT NOT NULL,
               cell_lat INTEGER NOT NULL,
               cell_lon INTEGER NOT NULL,
               lat_sum REAL NOT NULL DEFAULT 0,
               lon_sum REAL NOT NULL DEFAULT 0,
               tx INTEGER NOT NULL DEFAULT 0,
               rx INTEGER NOT NULL DEFAULT 0,
               direct INTEGER NOT NULL DEFAULT 0,
               callsigns TEXT NOT NULL DEFAULT '[]',
               first_seen TEXT NOT NULL,
               last_seen TEXT NOT NULL,
               PRIMARY KEY (day, cell_lat, cell_lon)
           )"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rf_coverage_cells_day ON rf_coverage_cells(day)")


def _valid(lat: Any, lon: Any) -> tuple[float, float] | None:
    if not db._valid_geo_position(lat, lon):
        return None
    return float(lat), float(lon)


def _add(conn, timestamp: str, callsign: str, pos: tuple[float, float], role: str, direct: bool) -> None:
    day = str(timestamp or "")[:10]
    if len(day) != 10:
        return
    cell = (math.floor(pos[0] / CELL_DEGREES), math.floor(pos[1] / CELL_DEGREES))
    row = conn.execute(
        "SELECT callsigns FROM rf_coverage_cells WHERE day=? AND cell_lat=? AND cell_lon=?",
        (day, *cell),
    ).fetchone()
    calls = json.loads(row["callsigns"]) if row else []
    call = str(callsign or "").strip().upper()
    if call and call not in calls and len(calls) < MAX_CALLSIGNS_PER_CELL:
        calls.append(call)
    conn.execute(
        """INSERT INTO rf_coverage_cells(day,cell_lat,cell_lon,lat_sum,lon_sum,tx,rx,direct,
                                         callsigns,first_seen,last_seen)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(day,cell_lat,cell_lon) DO UPDATE SET
               lat_sum=lat_sum+excluded.lat_sum, lon_sum=lon_sum+excluded.lon_sum,
               tx=tx+excluded.tx, rx=rx+excluded.rx,
               direct=MAX(direct,excluded.direct), callsigns=excluded.callsigns,
               first_seen=MIN(first_seen,excluded.first_seen),
               last_seen=MAX(last_seen,excluded.last_seen)""",
        (day, *cell, pos[0], pos[1], 1 if role == "tx" else 0, 1 if role == "rx" else 0,
         1 if direct else 0, json.dumps(calls), timestamp, timestamp),
    )


def record_event_conn(conn, timestamp: str, source: str, target: str,
                      source_pos: Any, target_pos: Any, *, direct: bool) -> None:
    """Soma um salto RF: TX na posição da origem, RX na posição do destino."""
    for call, pos, role in ((source, source_pos, "tx"), (target, target_pos, "rx")):
        valid = _valid(*pos) if pos else None
        if valid:
            _add(conn, timestamp, call, valid, role, direct)


def backfill_once(conn) -> int:
    """Copia uma vez o histórico RF de topology_events (ignora posição APRS inválida)."""
    if conn.execute("SELECT 1 FROM schema_migrations_v112 WHERE migration_key=?",
                    (BACKFILL_KEY,)).fetchone():
        return 0
    count = 0
    for row in conn.execute(
        """SELECT timestamp,source,target,medium,evidence_level,
                  source_lat,source_lon,target_lat,target_lon,raw
             FROM topology_events WHERE kind='rf' ORDER BY timestamp,id"""
    ).fetchall():
        if row["raw"] and db.raw_aprs_position_issue(str(row["raw"])):
            continue
        direct = str(row["medium"] or "").upper() == "RF" and str(row["evidence_level"] or "").lower() == "direct"
        record_event_conn(conn, str(row["timestamp"] or ""), row["source"], row["target"],
                          (row["source_lat"], row["source_lon"]), (row["target_lat"], row["target_lon"]),
                          direct=direct)
        count += 1
    conn.execute("INSERT INTO schema_migrations_v112(migration_key,applied_at) VALUES(?,?)",
                 (BACKFILL_KEY, db.utc_now_iso()))
    if count:
        diag.log_event("rf_coverage_backfill", events=count)
    return count


def list_points(hours: float = 0, limit: int = 4000) -> list[dict[str, Any]]:
    """Pontos do mapa de calor: células somadas no período (dias UTC)."""
    try:
        period = float(hours or 0)
    except (TypeError, ValueError):
        period = 0.0
    params: list[Any] = []
    where = ""
    if math.isfinite(period) and period > 0:
        start = datetime.now(timezone.utc) - timedelta(hours=min(max(period, 0.25), 24 * 3650))
        where = "WHERE day>=? AND last_seen>=?"
        params += [start.date().isoformat(), start.isoformat(timespec="seconds")]
    with db.connection() as conn:
        rows = conn.execute(
            f"""SELECT cell_lat,cell_lon,SUM(lat_sum) AS lat_sum,SUM(lon_sum) AS lon_sum,
                       SUM(tx) AS tx,SUM(rx) AS rx,MAX(direct) AS direct,
                       GROUP_CONCAT(callsigns,'|') AS calls,
                       MIN(first_seen) AS first_seen,MAX(last_seen) AS last_seen
                  FROM rf_coverage_cells {where}
                 GROUP BY cell_lat,cell_lon""",
            params,
        ).fetchall()
    points = []
    for row in rows:
        count = int(row["tx"] or 0) + int(row["rx"] or 0)
        if count <= 0:
            continue
        calls: list[str] = []
        for chunk in str(row["calls"] or "").split("|"):
            try:
                for call in json.loads(chunk or "[]"):
                    if call not in calls:
                        calls.append(call)
            except ValueError:
                continue
        points.append({
            "latitude": round(float(row["lat_sum"]) / count, 6),
            "longitude": round(float(row["lon_sum"]) / count, 6),
            "tx": int(row["tx"] or 0), "rx": int(row["rx"] or 0), "count": count,
            # 1 observação ~0,37; cresce de forma logarítmica até 1.
            "weight": round(min(1.0, 0.25 + math.log1p(count) / 6.0), 3),
            "evidence": "direct" if row["direct"] else "inferred",
            "callsigns": sorted(calls)[:MAX_CALLSIGNS_PER_CELL],
            "first_seen": row["first_seen"], "last_seen": row["last_seen"],
        })
    points.sort(key=lambda item: (item["count"], item["last_seen"]), reverse=True)
    return points[:max(1, min(int(limit), 8000))]
