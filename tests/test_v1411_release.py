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


def _edge(conn, source: str, target: str, packets: int = 5) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    conn.execute(
        "INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen,igate,rf_transport_count) VALUES(?,?,?,?,?,?,?,?)",
        (source, target, "rf", packets, now, now, None, packets),
    )


def test_v1411_version_and_header_markers():
    root = Path(__file__).resolve().parent.parent
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    assert tuple(int(part) for part in version.split(".")) >= (1, 14, 11)
    assert f'__version__ = "{version}"' in (root / "pt2vhf_aprs" / "__init__.py").read_text(encoding="utf-8")

    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    tnc_js = (root / "pt2vhf_aprs" / "static" / "js" / "tnc.js").read_text(encoding="utf-8")

    assert '>Pesquisar</button>' in html
    assert '<span>TNC</span>' in html
    assert '<strong id="connectionControlStatus">APRS-IS</strong>' in html
    assert "ui('Atualizada', 'Up to date')" in js
    assert "statusText.textContent = 'APRS-IS'" in js
    assert "status.connected ? 'connected' : 'disconnected'" in js
    assert "text.textContent = 'TNC'" in tnc_js
    assert "connected ? 'connected' : 'disconnected'" in tnc_js


def test_v1411_rf_records_rank_endpoint_distance_not_route_length():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                # Curved multi-hop route: long traveled path, but endpoints are close.
                _station(conn, "PT2A", 10.0, 10.0)
                _station(conn, "PT2M1", 10.4, 10.0)
                _station(conn, "PT2M2", 10.4, 10.4)
                _station(conn, "PT2B", 10.0, 10.1)
                _edge(conn, "PT2A", "PT2M1", 10)
                _edge(conn, "PT2M1", "PT2M2", 10)
                _edge(conn, "PT2M2", "PT2B", 10)

                # Separate pair with a larger endpoint distance than any hop above.
                _station(conn, "PT2C", 12.0, 10.0)
                _station(conn, "PT2D", 12.0, 10.8)
                _edge(conn, "PT2C", "PT2D", 5)

            records = db.list_rf_route_records(hours=24, limit=20, max_hops=6)
            assert records
            direct_distances = [float(item["direct_distance_km"]) for item in records]
            assert direct_distances == sorted(direct_distances, reverse=True)
            assert set(records[0]["nodes"]) == {"PT2C", "PT2D"}

            curved = next(
                item for item in records
                if {item["source"], item["target"]} == {"PT2A", "PT2B"}
            )
            assert curved["distance_km"] > curved["direct_distance_km"]
    finally:
        db.DB_PATH = original


def test_v1411_rf_records_emit_each_endpoint_pair_once():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _station(conn, "PT2A", -15.8, -47.9)
                _station(conn, "PT2X", -15.7, -47.8)
                _station(conn, "PT2Y", -15.65, -47.75)
                _station(conn, "PT2B", -15.6, -47.7)
                _edge(conn, "PT2A", "PT2X", 8)
                _edge(conn, "PT2X", "PT2B", 8)
                _edge(conn, "PT2A", "PT2Y", 7)
                _edge(conn, "PT2Y", "PT2B", 7)

            records = db.list_rf_route_records(hours=24, limit=50, max_hops=6)
            pairs = [tuple(sorted((item["source"], item["target"]))) for item in records]
            assert len(pairs) == len(set(pairs))
            assert pairs.count(("PT2A", "PT2B")) == 1
    finally:
        db.DB_PATH = original


def test_v1411_record_ui_uses_direct_distance_as_primary():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "formatRfDistanceKm(route.direct_distance_km)" in js
    assert "ui('rota', 'route') + ': ' + formatRfDistanceKm(route.distance_km)" in js
