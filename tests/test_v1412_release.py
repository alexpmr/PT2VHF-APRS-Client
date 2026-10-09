from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db


def _station(conn, call: str, lat: float, lon: float) -> None:
    conn.execute(
        "INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
        (call, datetime.now(timezone.utc).replace(microsecond=0).isoformat(), lat, lon),
    )


def _edge(
    conn,
    source: str,
    target: str,
    *,
    rf_transport: int = 0,
    rf_path: int = 0,
    internet: int = 0,
    packets: int | None = None,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    count = int(packets if packets is not None else max(rf_transport, rf_path, internet, 1))
    kind = "igate" if internet and not (rf_transport or rf_path) else "rf"
    conn.execute(
        """INSERT INTO topology_edges(
               source,target,kind,packet_count,first_seen,last_seen,igate,
               rf_transport_count,rf_path_count,internet_confirmed_count
           ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (source, target, kind, count, now, now, None, rf_transport, rf_path, internet),
    )


def test_v1412_version_and_ui_markers():
    root = Path(__file__).resolve().parent.parent
    assert (root / "VERSION").read_text(encoding="utf-8").strip() == "1.14.12"
    assert '__version__ = "1.14.12"' in (root / "pt2vhf_aprs" / "__init__.py").read_text(encoding="utf-8")

    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    assert "bindRfRoutePanelDrag" in js
    assert "setPointerCapture" in js
    assert "clampRfRoutePanelPosition" in js
    assert "rf_confidence_label" in js
    assert ".rf-route-panel.dragging" in css
    assert ".client-version-stats-content" in css
    assert "overflow-y: visible !important;" in css


def test_v1412_rf_confidence_rejects_implausible_single_observation_long_hop():
    short = db._rf_edge_confidence(
        {"rf_transport_count": 1, "rf_path_count": 0, "internet_confirmed_count": 0, "packet_count": 1},
        35.0,
    )
    assert short["confirmed"] is True
    assert short["level"] == "confirmed"

    implausible = db._rf_edge_confidence(
        {"rf_transport_count": 1, "rf_path_count": 0, "internet_confirmed_count": 0, "packet_count": 1},
        1649.0,
    )
    assert implausible["confirmed"] is False
    assert implausible["level"] == "inconsistent"
    assert "1649.0 km" in implausible["reason"]


def test_v1412_exceptional_long_hop_requires_strong_direct_evidence():
    exceptional = db._rf_edge_confidence(
        {
            "rf_transport_count": db.RF_CONFIRMED_EXCEPTIONAL_OBS,
            "rf_path_count": 0,
            "internet_confirmed_count": 0,
            "packet_count": db.RF_CONFIRMED_EXCEPTIONAL_OBS,
        },
        1649.0,
    )
    assert exceptional["confirmed"] is True
    assert exceptional["level"] == "confirmed"
    assert "propagação excepcional" in exceptional["reason"]


def test_v1412_route_graph_uses_only_confirmed_rf_edges():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _station(conn, "PT2AAA", -15.8, -47.9)
                _station(conn, "PT2MID", -15.7, -47.8)
                _station(conn, "PT2BBB", -15.6, -47.7)
                _station(conn, "PU2FAR", -15.8, -32.5)

                _edge(conn, "PT2AAA", "PT2MID", rf_transport=2)
                _edge(conn, "PT2MID", "PT2BBB", rf_transport=2)
                _edge(conn, "PT2AAA", "PU2FAR", rf_transport=1)

            normal = db.list_rf_routes("PT2AAA", "PT2BBB", hours=24)
            assert len(normal["routes"]) == 1
            assert normal["routes"][0]["rf_confidence"] == "confirmed"
            assert all(edge["rf_confidence"] == "confirmed" for edge in normal["routes"][0]["edges"])

            far = db.list_rf_routes("PT2AAA", "PU2FAR", hours=24)
            assert far["routes"] == []

            records = db.list_rf_route_records(hours=24, limit=20)
            assert all("PU2FAR" not in route["nodes"] for route in records)
    finally:
        db.DB_PATH = original


def test_v1412_path_only_long_edge_is_not_100_percent_rf():
    probable = db._rf_edge_confidence(
        {"rf_transport_count": 0, "rf_path_count": 2, "internet_confirmed_count": 0, "packet_count": 2},
        120.0,
    )
    assert probable["confirmed"] is False
    assert probable["level"] == "probable"

    inconsistent = db._rf_edge_confidence(
        {"rf_transport_count": 0, "rf_path_count": 10, "internet_confirmed_count": 0, "packet_count": 10},
        900.0,
    )
    assert inconsistent["confirmed"] is False
    assert inconsistent["level"] == "inconsistent"


def test_v1412_statistics_cards_do_not_have_vertical_internal_scroll():
    root = Path(__file__).resolve().parent.parent
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    required = [
        "#tab-analysis .topology-stats-box",
        "#tab-analysis .topology-stats-content",
        "#tab-analysis .topology-stat-group",
        "#tab-analysis .analysis-client-version-panel",
        "#tab-analysis .client-version-stats-content",
        "#tab-analysis .station-ranking-table-wrap",
        "#tab-analysis .rf-route-record-list",
    ]
    for marker in required:
        assert marker in css
    assert "max-height: none !important;" in css
    assert "overflow-y: visible !important;" in css


def test_v1412_draggable_route_panel_is_bounded_and_resets_for_new_analysis():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "Math.max(0, Math.min(Number(left) || 0, maxLeft))" in js
    assert "Math.max(0, Math.min(Number(top) || 0, maxTop))" in js
    assert "resetRfRoutePanelPosition();" in js
    assert "header.addEventListener('pointerdown'" in js
