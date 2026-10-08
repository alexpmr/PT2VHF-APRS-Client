from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db


def _station(conn, call: str, lat: float, lon: float) -> None:
    conn.execute(
        "INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
        (call, datetime.now(timezone.utc).replace(microsecond=0).isoformat(), lat, lon),
    )


def _edge(conn, source: str, target: str, kind: str = "rf", packets: int = 5, when: str | None = None) -> None:
    ts = when or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    conn.execute(
        "INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen,igate) VALUES(?,?,?,?,?,?,?)",
        (source, target, kind, packets, ts, ts, None),
    )


def test_v1410_version_ui_and_layout_markers():
    root = Path(__file__).resolve().parent.parent
    assert (root / "VERSION").read_text(encoding="utf-8").strip() == "1.14.10"
    assert '__version__ = "1.14.10"' in (root / "pt2vhf_aprs" / "__init__.py").read_text(encoding="utf-8")

    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert 'id="rfRouteSourceList"' in html
    assert 'list="rfRouteSourceList"' in html
    assert "flex-wrap: wrap;" in css
    assert "--map-context-height" in css
    assert ".station-ranking-table-wrap" in css
    assert "overflow-y: visible;" in css
    assert "max-height: none;" in css
    assert "refreshRfRouteOrigins" in js
    assert "focusRfRecordRoute" in js
    assert "rfRouteExclusiveNodes" in js


def test_v1410_origin_autocomplete_uses_rf_graph_only():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _station(conn, "PT2AAA", -15.8, -47.9)
                _station(conn, "PT2BBB", -15.7, -47.8)
                _station(conn, "PT2CCC", -15.6, -47.7)
                _edge(conn, "PT2AAA", "PT2BBB", "rf", 8)
                _edge(conn, "PT2BBB", "PT2CCC", "igate", 20)

            rows = db.list_rf_route_origins(hours=24, query="PT2", limit=20)
            calls = {row["callsign"] for row in rows}
            assert calls == {"PT2AAA", "PT2BBB"}
            assert "PT2CCC" not in calls
    finally:
        db.DB_PATH = original


def test_v1410_longest_rf_record_prefers_complete_multihop_chain_and_excludes_internet():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _station(conn, "PT2AAA", -15.8, -47.9)
                _station(conn, "PT2BBB", -15.0, -47.2)
                _station(conn, "PT2CCC", -14.2, -46.5)
                _station(conn, "PT2NET", -13.0, -45.0)
                _edge(conn, "PT2AAA", "PT2BBB", "rf", 11)
                _edge(conn, "PT2BBB", "PT2CCC", "rf", 9)
                _edge(conn, "PT2CCC", "PT2NET", "igate", 99)

            records = db.list_rf_route_records(hours=24, limit=10, max_hops=6)
            assert records
            longest = records[0]
            assert set(longest["nodes"]) == {"PT2AAA", "PT2BBB", "PT2CCC"}
            assert longest["hops"] == 2
            assert longest["distance_km"] > max(edge["distance_km"] for edge in longest["edges"])
            assert all(edge["classification_source"] for edge in longest["edges"])
            assert all("PT2NET" not in route["nodes"] for route in records)

            canonical = [min(tuple(route["nodes"]), tuple(reversed(route["nodes"]))) for route in records]
            assert len(canonical) == len(set(canonical))
    finally:
        db.DB_PATH = original


def test_v1410_rf_records_respect_statistics_period():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            old = (datetime.now(timezone.utc) - timedelta(days=3)).replace(microsecond=0).isoformat()
            recent = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0).isoformat()
            with db.connection() as conn:
                _station(conn, "PT2O1", -15.8, -47.9)
                _station(conn, "PT2O2", -14.8, -46.9)
                _station(conn, "PT2N1", -15.7, -47.8)
                _station(conn, "PT2N2", -15.6, -47.7)
                _edge(conn, "PT2O1", "PT2O2", "rf", 50, old)
                _edge(conn, "PT2N1", "PT2N2", "rf", 5, recent)

            records = db.list_rf_route_records(hours=24, limit=10)
            assert records
            assert all("PT2O1" not in route["nodes"] for route in records)
            assert any(set(route["nodes"]) == {"PT2N1", "PT2N2"} for route in records)

            stats = db.topology_stats(24)
            assert "rf_route_records" in stats
            assert all("PT2O1" not in route["nodes"] for route in stats["rf_route_records"])
    finally:
        db.DB_PATH = original


def test_v1410_record_focus_is_exclusive_and_statistics_scroll_is_page_level():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")

    assert "state.rfRouteExclusiveNodes = new Set" in js
    assert "routeFocusNodes ? [] : periodObjects.filter" in js
    assert "state.tracklogEnabled && !routeFocusNodes" in js
    assert "setTransientRouteFocusVisibility(false)" in js
    assert "setTransientRouteFocusVisibility(true)" in js
    assert ".rf-route-records-group" in css
    assert ".rf-route-record" in css
