"""v1.15.5: RF coverage from direct KISS/TNC receptions without a digi."""
from __future__ import annotations

from datetime import datetime, timezone

import aprslib
import pytest

from pt2vhf_aprs import database as db, rf_coverage


def receive(raw: str, medium: str = "RF") -> None:
    parsed = aprslib.parse(raw)
    db.process_received_packet(raw, parsed, parsed.get("from"),
                               parsed.get("format"), medium=medium)


def test_pathless_rf_beacon_produces_coverage_without_topology_edge(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "direct.db")
    db.init_db()
    raw = "PT2CAR-9>APRS:!1548.00S/04806.60W>RF direct"
    receive(raw)
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM topology_events").fetchone()[0] == 0
        assert conn.execute("SELECT medium FROM packets").fetchone()[0] == "RF"
    points = rf_coverage.list_points(24)
    assert len(points) == 1
    assert points[0]["tx"] == 1 and points[0]["rx"] == 0
    assert points[0]["evidence"] == "direct"
    assert "PT2CAR-9" in points[0]["callsigns"]


def test_mobile_rf_positions_fill_observed_cells_without_fabricating_corridor(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "mobile.db")
    db.init_db()
    # Spatial plausibility is covered by its own tests; simulate valid fixes.
    monkeypatch.setattr(db, "_position_is_plausible",
                        lambda *args, **kwargs: (True, {}))
    for minute in ("48", "50", "52", "54", "56"):
        receive(f"PT2CAR-9>APRS:!15{minute}.00S/04806.60W>Mobile")
    points = rf_coverage.list_points(24)
    assert len(points) == 5
    assert sum(p["tx"] for p in points) == 5
    assert all(p["evidence"] == "direct" for p in points)


def test_internet_only_and_invalid_rf_coordinates_do_not_heat_map(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "rejections.db")
    db.init_db()
    receive("PT2NET>APRS:!1548.00S/04806.60W>Internet", "APRS-IS")
    parsed = {"from": "PT2BAD-9", "format": "uncompressed",
              "latitude": -16.2, "longitude": -48.1}
    bad = "PT2BAD-9>APRS:!1568.00S/04806.60W>Invalid minutes"
    db.process_received_packet(bad, parsed, "PT2BAD-9", "uncompressed", medium="RF")
    receive("PT2DMR>APRS,DMR*,qAR,PT2IGT:!1549.00S/04807.00W>Digital", "APRS-IS")
    assert rf_coverage.list_points() == []


def test_digipeated_rf_does_not_count_source_twice(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "digi.db")
    db.init_db()
    receive("PT2CAR-9>APRS,PT2DIG-1*:!1548.00S/04806.60W>RF repeated")
    points = rf_coverage.list_points()
    assert sum(p["tx"] for p in points) == 1


def test_backfill_recovers_only_confirmed_pathless_rf_and_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "backfill.db")
    db.init_db()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw = "PT2OLD-9>APRS:!1548.00S/04806.60W>Historical"
    raw_internet = "PT2NET>APRS:!1547.00S/04806.60W>Internet"
    with db.connection() as conn:
        conn.execute("INSERT INTO packets(timestamp,from_call,raw,medium) VALUES(?,?,?,'RF')",
                     (stamp, "PT2OLD-9", raw))
        conn.execute("INSERT INTO packets(timestamp,from_call,raw,medium) VALUES(?,?,?,'APRS-IS')",
                     (stamp, "PT2NET", raw_internet))
        conn.execute("INSERT INTO tracks(callsign,timestamp,latitude,longitude,raw) VALUES(?,?,?,?,?)",
                     ("PT2OLD-9", stamp, -15.8, -48.11, raw))
        conn.execute("INSERT INTO tracks(callsign,timestamp,latitude,longitude,raw) VALUES(?,?,?,?,?)",
                     ("PT2NET", stamp, -15.78333, -48.11, raw_internet))
        conn.execute("DELETE FROM schema_migrations_v112 WHERE migration_key=?",
                     (rf_coverage.DIRECT_BACKFILL_KEY,))
    db.init_db()
    points = rf_coverage.list_points()
    assert len(points) == 1 and points[0]["count"] == 1
    db.init_db()
    assert sum(p["count"] for p in rf_coverage.list_points()) == 1


def test_position_rejected_by_plausibility_filter_never_creates_rf_sample(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "outlier.db")
    db.init_db()
    receive("PT2CAR-9>APRS:!1548.00S/04806.60W>Initial")
    before = sum(p["count"] for p in rf_coverage.list_points())
    assert before == 1
    monkeypatch.setattr(db, "_position_is_plausible",
                        lambda *args, **kwargs: (False, {"distance_km": 7000, "speed_kmh": 1e6}))
    receive("PT2CAR-9>APRS:!1549.00S/04806.60W>Outlier")
    assert sum(p["count"] for p in rf_coverage.list_points()) == before
