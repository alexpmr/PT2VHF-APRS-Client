from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db


def _seed_station(conn, callsign: str, lat: float, lon: float) -> None:
    conn.execute(
        "INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
        (callsign, datetime.now(timezone.utc).replace(microsecond=0).isoformat(), lat, lon),
    )


def _seed_edge(conn, source: str, target: str, kind: str = "rf", packets: int = 5) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    conn.execute(
        "INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen,igate) VALUES(?,?,?,?,?,?,?)",
        (source, target, kind, packets, now, now, None),
    )


def test_v149_version_and_ui_markers():
    root = Path(__file__).resolve().parent.parent
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    assert tuple(int(part) for part in version.split(".")) >= (1, 14, 9)
    assert f'__version__ = "{version}"' in (root / "pt2vhf_aprs" / "__init__.py").read_text(encoding="utf-8")
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert 'id="rfRouteSource"' in html
    assert 'id="rfRouteTarget"' in html
    assert 'id="rfRoutePanel"' in html
    assert "refreshRfRouteCandidates" in js
    assert "applyRfRouteAnalysis" in js
    assert "formatRfDistanceKm(topologyEdgeDistanceKm(edge))" in js


def test_v149_candidates_only_include_complete_rf_reachability():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _seed_station(conn, "PT2AAA", -15.80, -47.90)
                _seed_station(conn, "PT2DIG", -15.70, -47.80)
                _seed_station(conn, "PT2BBB", -15.60, -47.70)
                _seed_station(conn, "PT2NET", -15.50, -47.60)
                _seed_edge(conn, "PT2AAA", "PT2DIG", "rf", 9)
                _seed_edge(conn, "PT2DIG", "PT2BBB", "rf", 7)
                _seed_edge(conn, "PT2BBB", "PT2NET", "igate", 50)

            candidates = db.list_rf_route_candidates("PT2AAA", hours=24)
            calls = {item["callsign"] for item in candidates}
            assert {"PT2DIG", "PT2BBB"} <= calls
            assert "PT2NET" not in calls
    finally:
        db.DB_PATH = original


def test_v149_routes_support_multiple_complete_paths_and_distances():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _seed_station(conn, "PT2AAA", -15.80, -47.90)
                _seed_station(conn, "PT2D1", -15.72, -47.84)
                _seed_station(conn, "PT2D2", -15.68, -47.76)
                _seed_station(conn, "PT2BBB", -15.60, -47.70)
                _seed_edge(conn, "PT2AAA", "PT2D1", "rf", 10)
                _seed_edge(conn, "PT2D1", "PT2BBB", "rf", 8)
                _seed_edge(conn, "PT2AAA", "PT2D2", "rf", 6)
                _seed_edge(conn, "PT2D2", "PT2BBB", "rf", 6)

            result = db.list_rf_routes("PT2AAA", "PT2BBB", hours=24, max_routes=12, max_hops=8)
            assert result["source"] == "PT2AAA"
            assert result["target"] == "PT2BBB"
            assert result["direct_distance_km"] > 0
            assert len(result["routes"]) == 2
            paths = {tuple(route["nodes"]) for route in result["routes"]}
            assert ("PT2AAA", "PT2D1", "PT2BBB") in paths
            assert ("PT2AAA", "PT2D2", "PT2BBB") in paths
            for route in result["routes"]:
                assert route["hops"] == 2
                assert route["distance_km"] > 0
                assert len(route["edges"]) == 2
                assert all(edge["distance_km"] > 0 for edge in route["edges"])
    finally:
        db.DB_PATH = original


def test_v149_internet_cannot_complete_an_rf_route():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _seed_station(conn, "PT2AAA", -15.80, -47.90)
                _seed_station(conn, "PT2MID", -15.70, -47.80)
                _seed_station(conn, "PT2BBB", -15.60, -47.70)
                _seed_edge(conn, "PT2AAA", "PT2MID", "rf", 12)
                _seed_edge(conn, "PT2MID", "PT2BBB", "igate", 12)

            result = db.list_rf_routes("PT2AAA", "PT2BBB", hours=24)
            assert result["routes"] == []
    finally:
        db.DB_PATH = original


def test_v149_route_graph_is_bidirectional_for_observed_rf_links():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _seed_station(conn, "PT2AAA", -15.80, -47.90)
                _seed_station(conn, "PT2BBB", -15.60, -47.70)
                _seed_edge(conn, "PT2AAA", "PT2BBB", "rf", 3)

            forward = db.list_rf_routes("PT2AAA", "PT2BBB", hours=24)
            reverse = db.list_rf_routes("PT2BBB", "PT2AAA", hours=24)
            assert len(forward["routes"]) == 1
            assert len(reverse["routes"]) == 1
            assert reverse["routes"][0]["nodes"] == ["PT2BBB", "PT2AAA"]
    finally:
        db.DB_PATH = original
