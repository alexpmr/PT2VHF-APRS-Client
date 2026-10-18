"""Acceptance tests for #94: a mobile digi must not create overview-map links.

Synthetic APRS evidence only. The real Brasília map still requires a DB export
for field acceptance, which these fixtures intentionally do not impersonate.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db, topology_map


NOW = datetime.now(timezone.utc).replace(microsecond=0)
SOUTH = (-25.42, -49.24)
SOUTH_DIGI = (-25.39, -49.23)
BRASILIA = (-15.78, -47.91)
BRASILIA_DIGI = (-15.79, -47.90)
FIXED_A = (-15.72, -47.98)
FIXED_B = (-15.74, -47.92)


def event(source, target, source_pos, target_pos, *, hours=0, kind="rf",
          medium="RF", level="direct"):
    return {
        "timestamp": (NOW - timedelta(hours=hours)).isoformat(),
        "source": source, "target": target, "kind": kind,
        "medium": medium, "evidence_level": level,
        "source_lat": source_pos[0], "source_lon": source_pos[1],
        "target_lat": target_pos[0], "target_lon": target_pos[1],
    }


def insert_event(conn, row):
    conn.execute(
        """INSERT INTO topology_events(
               timestamp,source,target,kind,medium,evidence_level,
               source_lat,source_lon,target_lat,target_lon
           ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (row["timestamp"], row["source"], row["target"], row["kind"],
         row["medium"], row["evidence_level"],
         row["source_lat"], row["source_lon"],
         row["target_lat"], row["target_lon"]),
    )


def moving_target_rows():
    return [
        event("PY5SUL-1", "PT2AP-9", SOUTH, SOUTH_DIGI, hours=9),
        event("PY5SUL-1", "PT2AP-9", SOUTH, SOUTH_DIGI, hours=8),
        event("PT2BSB-1", "PT2AP-9", BRASILIA, BRASILIA_DIGI, hours=3),
        event("PT2BSB-1", "PT2AP-9", BRASILIA, BRASILIA_DIGI, hours=2),
    ]


def moving_source_rows():
    return [
        event("PT2AP-9", "PY5SUL-1", SOUTH_DIGI, SOUTH, hours=9),
        event("PT2AP-9", "PY5SUL-1", SOUTH_DIGI, SOUTH, hours=8),
        event("PT2AP-9", "PT2BSB-1", BRASILIA_DIGI, BRASILIA, hours=3),
        event("PT2AP-9", "PT2BSB-1", BRASILIA_DIGI, BRASILIA, hours=2),
    ]


def test_fixed_only_rf_is_still_visible_even_without_internet():
    rows = [event("PT2FIX-1", "PT2FIX-2", FIXED_A, FIXED_B)]
    edges = topology_map._segments_from_events(rows)
    assert len(edges) == 1
    # One new, directly heard fixed-to-fixed RF contact is temporary for 3h.
    assert edges[0]["kind"] == "rf_temp"
    assert edges[0]["direct_rf_confirmed"] is True
    assert edges[0]["source_lat"] == FIXED_A[0]


def test_moving_target_digi_links_hidden_and_historical_rows_preserved():
    rows = moving_target_rows()
    assert "PT2AP-9" in topology_map.moving_rf_repeaters(rows)
    result = topology_map._segments_from_events(rows)
    assert len(result) == 1 and result[0]['kind'] == 'rf_mobile'
    assert result[0]['source'] == 'PT2BSB-1'
    assert len(rows) == 4


def test_moving_source_digi_must_also_hide_all_lines():
    rows = moving_source_rows()
    assert "PT2AP-9" in topology_map.moving_rf_repeaters(rows)
    result = topology_map._segments_from_events(rows)
    assert len(result) == 1 and result[0]['kind'] == 'rf_mobile'


def test_source_and_target_direction_change_does_not_restore_mobile_line():
    rows = moving_target_rows() + moving_source_rows()
    result = topology_map._segments_from_events(rows)
    assert len(result) == 1 and result[0]['kind'] == 'rf_mobile'


def test_mobile_endpoint_suppresses_internet_line_as_well():
    rows = moving_target_rows() + [
        event("PT2BSB-1", "PT2AP-9", BRASILIA, BRASILIA_DIGI,
              hours=1, kind="igate", medium="APRS-IS", level="internet"),
    ]
    result = topology_map._segments_from_events(rows)
    assert len(result) == 1 and result[0]['kind'] == 'rf_mobile'
    assert result[0]['kind'] != 'igate'


def test_single_invalid_spatial_outlier_does_not_label_fixed_digi_mobile():
    rows = [
        event("PT2FIX-1", "PT2FIX-2", FIXED_A, FIXED_B, hours=4),
        event("PT2FIX-1", "PT2FIX-2", FIXED_A, FIXED_B, hours=3),
        event("PT2FIX-1", "PT2FIX-2", FIXED_A, SOUTH_DIGI, hours=2),
    ]
    assert "PT2FIX-2" not in topology_map.moving_rf_repeaters(rows)


def test_no_historical_coordinates_does_not_create_line_from_latest_gps():
    row = event("PT2FIX-1", "PT2FIX-2", FIXED_A, FIXED_B)
    row["target_lat"] = None
    assert topology_map._segments_from_events([row]) == []


def test_mobile_status_survives_switch_to_one_hour_display():
    # Multiple past RF observations demonstrate movement; only one recent
    # event is visible. Changing time filter cannot resurrect the old link.
    with tempfile.TemporaryDirectory() as td:
        prior = db.DB_PATH
        try:
            db.DB_PATH = Path(td) / "regression.sqlite3"
            db.init_db()
            with db.connection() as conn:
                for row in moving_target_rows():
                    insert_event(conn, row)
                insert_event(conn, event("PT2BSB-1", "PT2AP-9", BRASILIA,
                                         BRASILIA_DIGI, hours=0.1))
            result = topology_map.list_map_edges(1)
            assert len(result) == 1 and result[0]['kind'] == 'rf_mobile'
            with db.connection() as conn:
                assert conn.execute(
                    "SELECT COUNT(*) FROM topology_events"
                ).fetchone()[0] == 5
        finally:
            db.DB_PATH = prior


def test_tracklog_displacement_overrides_single_map_event():
    # APRS tracklogs are an independent source of mobile positions. A digi
    # reported only once in map topology still must be classified as mobile
    # when its retained track history proves displacement.
    with tempfile.TemporaryDirectory() as td:
        prior = db.DB_PATH
        try:
            db.DB_PATH = Path(td) / "trackmobile.sqlite3"
            db.init_db()
            with db.connection() as conn:
                for h, pos in ((9, SOUTH_DIGI), (8, SOUTH_DIGI),
                               (3, BRASILIA_DIGI), (2, BRASILIA_DIGI)):
                    conn.execute(
                        "INSERT INTO tracks(callsign,timestamp,latitude,longitude) "
                        "VALUES(?,?,?,?)",
                        ("PT2AP-9", (NOW - timedelta(hours=h)).isoformat(), *pos),
                    )
                insert_event(conn, event("PT2BSB-1", "PT2AP-9", BRASILIA,
                                         BRASILIA_DIGI))
            result = topology_map.list_map_edges(24)
            assert len(result) == 1 and result[0]['kind'] == 'rf_mobile'
            with db.connection() as conn:
                assert conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0] == 4
        finally:
            db.DB_PATH = prior


def test_mobile_observations_are_available_for_coverage_without_rf_lines():
    with tempfile.TemporaryDirectory() as td:
        prior = db.DB_PATH
        try:
            db.DB_PATH = Path(td) / "coverage.sqlite3"
            db.init_db()
            with db.connection() as conn:
                for row in moving_target_rows():
                    insert_event(conn, row)
            result = topology_map.list_map_edges(24)
            assert len(result) == 1 and result[0]['kind'] == 'rf_mobile'
            coverage = topology_map.list_mobile_rf_coverage(24)
            assert len(coverage) >= 2
            assert {v["callsign"] for v in coverage} == {"PT2AP-9"}
            with db.connection() as conn:
                assert conn.execute("SELECT COUNT(*) FROM topology_events").fetchone()[0] == 4
        finally:
            db.DB_PATH = prior


def test_mobile_source_coverage_must_not_be_discarded():
    with tempfile.TemporaryDirectory() as td:
        prior = db.DB_PATH
        try:
            db.DB_PATH = Path(td) / "reversecoverage.sqlite3"
            db.init_db()
            with db.connection() as conn:
                for row in moving_source_rows():
                    insert_event(conn, row)
            samples = topology_map.list_mobile_rf_coverage(24)
            assert {v["callsign"] for v in samples} == {"PT2AP-9"}
        finally:
            db.DB_PATH = prior
