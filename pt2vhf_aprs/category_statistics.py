"""Quick database category counts for the Statistics tab.

The values describe records retained in SQLite, not lifetime transmissions.
Queries are separate from the potentially slow RF route ranking.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from . import database as db


def category_counts(hours: int = 0) -> dict[str, Any]:
    period = int(hours or 0)
    period = 0 if period <= 0 else max(1, min(period, 720))
    cutoff = (
        (datetime.now(timezone.utc) - timedelta(hours=period)).isoformat(timespec="seconds")
        if period else None
    )

    def count(conn, table: str, column: str, *, condition: str = "",
              args: tuple = ()) -> int:
        where = []
        values = []
        if cutoff:
            where.append(column + " >= ?")
            values.append(cutoff)
        if condition:
            where.append(condition)
            values.extend(args)
        return int(conn.execute(
            "SELECT COUNT(*) FROM " + table +
            (" WHERE " + " AND ".join(where) if where else ""), values
        ).fetchone()[0])

    with db.connection() as conn:
        result = {
            "period_hours": period,
            "scope": "retained_history",
            "stations": count(conn, "stations", "last_heard"),
            "objects": count(conn, "aprs_objects", "last_heard"),
            "trackpoints": count(conn, "tracks", "timestamp"),
            "packets": count(conn, "packets", "timestamp"),
            "messages": count(conn, "messages", "timestamp",
                              condition="LOWER(message_type)='message'"),
            "messages_rx": count(conn, "messages", "timestamp",
                                 condition="LOWER(message_type)='message' AND direction='in'"),
            "messages_tx": count(conn, "messages", "timestamp",
                                 condition="LOWER(message_type)='message' AND direction='out'"),
            "bulletins": count(conn, "messages", "timestamp",
                               condition="LOWER(message_type)='bulletin'"),
            "groups": count(conn, "messages", "timestamp",
                            condition="LOWER(message_type)='group'"),
            "rf_links": count(conn, "topology_edges", "last_seen",
                              condition="kind='rf'"),
            "internet_links": count(conn, "topology_edges", "last_seen",
                                    condition="kind='igate'"),
            "topology_events": count(conn, "topology_events", "timestamp"),
        }
        # Digi/iGate are sets of unique identifiers in observed topology,
        # not packet totals and not necessarily disjoint categories.
        for key, sql in (
            ("digis", "SELECT COUNT(DISTINCT UPPER(TRIM(target))) FROM topology_edges WHERE kind='rf' AND igate IS NULL"),
            ("igates", "SELECT COUNT(DISTINCT UPPER(TRIM(igate))) FROM topology_edges WHERE igate IS NOT NULL"),
        ):
            if cutoff:
                sql += " AND last_seen>=?"
            result[key] = int(conn.execute(sql, (cutoff,) if cutoff else ()).fetchone()[0])
    return result
