"""v1.14.35 — historical RF geometry must not follow a mobile digi GPS.

These are real SQLite integration tests with the actual topology endpoint.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db, topology_map, web

ROOT = Path(__file__).resolve().parents[1]


def _event(conn, ts, source, target, kind, source_pos, target_pos, medium="APRS-IS", level="inferred"):
    conn.execute(
        """INSERT INTO topology_events(
               timestamp,source,target,kind,medium,evidence_level,
               source_lat,source_lon,target_lat,target_lon
           ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (ts, source, target, kind, medium, level,
         source_pos[0] if source_pos else None, source_pos[1] if source_pos else None,
         target_pos[0] if target_pos else None, target_pos[1] if target_pos else None),
    )


def test_mobile_pt2ap_historical_rf_edges_cannot_stretch_to_latest_gps(monkeypatch):
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "aprs.db"
            db.init_db()
            now = datetime.now(timezone.utc).replace(microsecond=0)
            south = (now - timedelta(hours=15)).isoformat()
            uberaba = (now - timedelta(hours=4)).isoformat()
            with db.connection() as conn:
                # The digi really repeated local RF packets in the South.
                _event(conn, south, "PY5SUL-9", "PT2AP-10", "rf",
                       (-25.43, -49.27), (-25.39, -49.24),
                       "APRS-IS", "inferred")
                # Hours later, the same moving digi really repeated in Uberaba.
                _event(conn, uberaba, "PY4UBA-9", "PT2AP-10", "rf",
                       (-19.75, -47.93), (-19.73, -47.92),
                       "RF", "direct")
                # The vehicle's current location moved 650+ km near Brasilia.
                conn.execute(
                    """INSERT INTO stations(callsign,last_heard,latitude,longitude)
                       VALUES(?,?,?,?)""",
                    ("PT2AP-10", now.isoformat(), -15.80, -47.88),
                )
                conn.execute(
                    """INSERT INTO stations(callsign,last_heard,latitude,longitude)
                       VALUES(?,?,?,?)""",
                    ("PY5SUL-9", now.isoformat(), -25.43, -49.27),
                )
                conn.execute(
                    """INSERT INTO stations(callsign,last_heard,latitude,longitude)
                       VALUES(?,?,?,?)""",
                    ("PY4UBA-9", now.isoformat(), -19.75, -47.93),
                )
            edges = topology_map.list_map_edges(24)
            assert len(edges) == 2
            by_source = {e["source"]: e for e in edges}
            assert by_source["PY5SUL-9"]["kind"] == "rf"
            assert by_source["PY5SUL-9"]["target_lat"] == -25.39
            assert by_source["PY5SUL-9"]["distance_km"] < 15
            assert by_source["PY4UBA-9"]["target_lat"] == -19.73
            assert by_source["PY4UBA-9"]["distance_km"] < 15
            assert by_source["PY5SUL-9"]["classification_source"].startswith("RF inferido")
            assert by_source["PY5SUL-9"]["rf_inferred"] is True
            assert by_source["PY5SUL-9"]["direct_rf_confirmed"] is False
            assert by_source["PY4UBA-9"]["direct_rf_confirmed"] is True
            assert by_source["PY4UBA-9"]["classification_source"].startswith("RF recebido")
            # Update the moving station yet again: history MUST stay identical.
            with db.connection() as conn:
                conn.execute(
                    "UPDATE stations SET latitude=-15.67,longitude=-47.86 WHERE callsign='PT2AP-10'"
                )
            assert topology_map.list_map_edges(24) == edges
            # Test the real Flask endpoint without launching production
            # scheduler/retention background threads. These global workers
            # otherwise follow db.DB_PATH as subsequent tests switch databases,
            # holding ephemeral SQLite files open on Windows (WinError 32).
            monkeypatch.setattr(web.scheduled_message_service, "start", lambda: None)
            monkeypatch.setattr(web.retention, "start_worker", lambda: None)
            client = web.create_app().test_client()
            response = client.get("/api/topology?hours=24")
            assert response.status_code == 200
            assert {e["source"]: e["target_lat"] for e in response.get_json()} == {
                "PY5SUL-9": -25.39, "PY4UBA-9": -19.73
            }
    finally:
        db.DB_PATH = original


def test_same_pair_multiple_mobile_regions_have_independent_segments():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "aprs.db"
            db.init_db()
            now = datetime.now(timezone.utc).replace(microsecond=0)
            with db.connection() as conn:
                _event(conn, (now - timedelta(hours=4)).isoformat(),
                       "PY2A-9", "PT2AP-10", "rf",
                       (-25.20, -49.2), (-25.19, -49.18))
                _event(conn, (now - timedelta(hours=1)).isoformat(),
                       "PY2A-9", "PT2AP-10", "rf",
                       (-19.80, -47.8), (-19.79, -47.79))
            edges = topology_map.list_map_edges(24)
            assert len(edges) == 2
            assert len({e["segment_id"] for e in edges}) == 2
            assert {e["target_lat"] for e in edges} == {-25.19, -19.79}
    finally:
        db.DB_PATH = original


def test_missing_historical_coordinates_do_not_invent_rf_geometry():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "aprs.db"
            db.init_db()
            now = datetime.now(timezone.utc).isoformat()
            with db.connection() as conn:
                _event(conn, now, "PY5SUL-9", "PT2AP-10", "rf",
                       (-25.4, -49.2), None)
                conn.execute(
                    """INSERT INTO topology_edges(
                           source,target,kind,packet_count,first_seen,last_seen,
                           rf_path_count
                       ) VALUES(?,?,?,?,?,?,?)""",
                    ("PY5SUL-9", "PT2AP-10", "rf", 1, now, now, 1),
                )
                conn.execute(
                    "INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2AP-10", now, -15.7, -47.9),
                )
            assert topology_map.list_map_edges(24) == []
            raw = db.connection()
            with raw as conn:
                assert conn.execute(
                    "SELECT COUNT(*) FROM topology_edges WHERE source='PY5SUL-9'"
                ).fetchone()[0] == 1
    finally:
        db.DB_PATH = original


def test_internet_starlink_and_rf_remain_distinct_and_ssids_not_merged():
    ts = datetime.now(timezone.utc).isoformat()
    rows = [
        dict(timestamp=ts, source="PY5SUL-9", target="PT2AP-10", kind="rf",
             medium="APRS-IS", evidence_level="inferred",
             source_lat=-25.4, source_lon=-49.2, target_lat=-25.39, target_lon=-49.19),
        dict(timestamp=ts, source="PY5SUL-9", target="PT2AP-10", kind="igate",
             medium="APRS-IS", evidence_level="internet",
             source_lat=-25.4, source_lon=-49.2, target_lat=-25.39, target_lon=-49.19),
        dict(timestamp=ts, source="PY5SUL-9", target="PT2AP-15", kind="rf",
             medium="RF", evidence_level="direct",
             source_lat=-25.4, source_lon=-49.2, target_lat=-25.39, target_lon=-49.19),
    ]
    edges = topology_map._segments_from_events(rows)
    assert {(e["kind"], e["target"]) for e in edges} == {
        ("rf", "PT2AP-10"), ("igate", "PT2AP-10"), ("rf", "PT2AP-15")
    }
    both = [e for e in edges if e["target"] == "PT2AP-10"]
    assert all(e["mixed_evidence"] for e in both)
    assert all(e["rf_packet_count"] == 1 and e["internet_packet_count"] == 1 for e in both)
    assert not [e for e in edges if e["source"] == "PT2AP-10" and e["target"] == "PY5SUL-9"]


def test_frontend_and_kml_export_never_use_latest_positions_for_rf_links():
    app = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    server = (ROOT / "pt2vhf_aprs/web.py").read_text(encoding="utf-8")
    map_source = (ROOT / "pt2vhf_aprs/topology_map.py").read_text(encoding="utf-8")
    assert 'topology_map.list_map_edges(hours)' in server
    assert 'payload["topology"] = topology_map.list_map_edges(hours)' in server
    assert "edge.segment_id ||" in app
    assert "historical_geometry" in app
    assert "FROM topology_events" in map_source
    assert "JOIN stations" not in map_source


def test_long_aprs_path_is_never_displayed_as_confirmed_direct_rf():
    now = datetime.now(timezone.utc).isoformat()
    rows = [dict(timestamp=now, source="LU9DCE", target="PU2XTC-4", kind="rf",
                 medium="APRS-IS", evidence_level="inferred",
                 source_lat=-34.6, source_lon=-58.4, target_lat=-22.9, target_lon=-47.1)]
    edge = topology_map._segments_from_events(rows)[0]
    assert edge["distance_km"] > 1000
    assert edge["rf_inferred"] is True
    assert edge["direct_rf_confirmed"] is False
    assert edge["rf_path_count"] == 1
    assert edge["rf_transport_count"] == 0
    app = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "inferredRouteEdge ? '#94a3b8'" in app
    assert "style.dashArray = '5 7'" in app
