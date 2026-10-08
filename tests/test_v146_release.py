from __future__ import annotations

from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v146_version_metadata():
    version = text("VERSION").strip()
    major, minor, patch = (int(part) for part in version.split("."))
    assert (major, minor, patch) >= (1, 14, 6)
    assert f'__version__ = "{version}"' in text("pt2vhf_aprs/__init__.py")
    win = text("windows/version_info.txt")
    assert f"filevers=({major}, {minor}, {patch}, 0)" in win
    assert "prodvers=(1, 14, 6, 0)" in win
    assert "FileVersion', '1.14.6'" in win
    assert "ProductVersion', '1.14.6'" in win


def test_v146_satellite_runtime_is_removed():
    for rel in (
        "pt2vhf_aprs/v112_satellites.py",
        "pt2vhf_aprs/v113_satellites.py",
        "pt2vhf_aprs/v114_satellite_ops.py",
        "pt2vhf_aprs/static/js/v112.js",
        "pt2vhf_aprs/static/js/v113.js",
        "pt2vhf_aprs/static/js/v114.js",
        "pt2vhf_aprs/static/js/v141.js",
        "pt2vhf_aprs/static/css/v112.css",
        "pt2vhf_aprs/static/css/v114.css",
        "pt2vhf_aprs/static/css/v141.css",
    ):
        assert not (ROOT / rel).exists(), rel

    assert "sgp4" not in text("requirements.txt").lower()
    web = text("pt2vhf_aprs/web.py")
    assert "register_v112_satellite_routes" not in web
    assert "register_v113_satellite_routes" not in web
    assert "register_v114_routes" not in web
    html = text("pt2vhf_aprs/templates/index.html")
    assert 'data-tab="satellites"' not in html
    assert 'id="tab-satellites"' not in html
    assert "satelliteMap" not in html
    for asset in ("js/v112.js", "js/v113.js", "js/v114.js", "js/v141.js"):
        assert asset not in html
    app = text("pt2vhf_aprs/static/js/app.js")
    assert "satellitesEnabled" not in app
    assert "pt2vhf:satellite-visibility" not in app
    assert "queue_satellite_beacon" not in text("pt2vhf_aprs/tnc_service.py")


def test_v146_mixed_pair_preserves_rf_and_aprsis_edges():
    rows = [
        {
            "source": "PY2MIX-9", "target": "PT2IGT-15", "kind": "rf",
            "packet_count": 4, "first_seen": "2026-10-07T12:00:00+00:00",
            "last_seen": "2026-10-07T12:10:00+00:00",
            "rf_transport_count": 4, "rf_path_count": 0, "internet_confirmed_count": 0,
        },
        {
            "source": "PY2MIX-9", "target": "PT2IGT-15", "kind": "igate",
            "packet_count": 9, "first_seen": "2026-10-07T12:20:00+00:00",
            "last_seen": "2026-10-07T12:30:00+00:00",
            "rf_transport_count": 0, "rf_path_count": 0, "internet_confirmed_count": 9,
        },
    ]
    result = db._consolidate_topology_edges(rows)
    assert {edge["kind"] for edge in result} == {"rf", "igate"}
    by_kind = {edge["kind"]: edge for edge in result}
    assert by_kind["rf"]["packet_count"] == 4
    assert by_kind["igate"]["packet_count"] == 9
    assert by_kind["rf"]["mixed_evidence"] is True
    assert by_kind["igate"]["mixed_evidence"] is True
    assert by_kind["igate"]["classification_source"] == "APRS-IS confirmado"


def test_v146_pure_rf_never_becomes_internet():
    _source, edges = db._observed_topology_edges(
        "PY2RF-9>APRS,PT2DGI*,WIDE2-1,qAr,PT2IGT-15:>local RF",
        medium="RF",
    )
    assert edges
    assert all(kind == "rf" for _src, _dst, kind, _igate in edges)


def test_v146_aprsis_link_survives_database_query_even_with_rf_same_pair():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "v146.db"
            db.init_db()
            for call, lat, lon in (
                ("PY2MIX-9", -15.72, -47.72),
                ("PT2IGT-15", -15.81, -47.91),
            ):
                db.upsert_station({
                    "from": call, "format": "uncompressed",
                    "latitude": lat, "longitude": lon, "symbol_table": "/",
                    "symbol": ">", "altitude": 1000, "comment": "Teste v1.14.6",
                    "path": [], "raw": f"{call}>APRS:>teste",
                })
            db.record_topology_from_raw(
                "PY2MIX-9>APRS,TCPIP*,qAr,PT2IGT-15:>internet",
                medium="APRS-IS",
            )
            db.record_topology_from_raw(
                "PY2MIX-9>APRS,qAR,PT2IGT-15:>rf",
                medium="RF",
            )
            rows = [
                row for row in db.list_topology_edges(hours=24)
                if row["source"] == "PY2MIX-9" and row["target"] == "PT2IGT-15"
            ]
            assert {row["kind"] for row in rows} == {"rf", "igate"}
            assert next(row for row in rows if row["kind"] == "igate")["internet_confirmed_count"] >= 1
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_v146_frontend_keeps_layers_independent_and_internet_visible():
    js = text("pt2vhf_aprs/static/js/app.js")
    assert "const orderedEdges = [...edges].sort" in js
    assert "if (edge.kind === 'igate' && !state.igateLinksEnabled) continue" in js
    assert "if (edge.kind !== 'igate' && !state.rfLinksEnabled) continue" in js
    assert "line.bringToFront()" in js
    assert "edge.kind === 'igate' ? '7 5' : null" in js
