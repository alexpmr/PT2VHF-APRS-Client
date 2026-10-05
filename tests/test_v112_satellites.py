from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs import v112_satellites as sat


ISS_TLE = """ISS (ZARYA)
1 25544U 98067A   19343.69339541  .00001764  00000-0  38792-4 0  9991
2 25544  51.6439 211.2001 0007417  17.6667  85.6398 15.50103472202482
"""


def read(rel: str) -> str:
    return (Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")


def test_v112_tle_parser_and_sgp4_position():
    parsed = sat._parse_tle_groups(ISS_TLE)
    assert 25544 in parsed
    tle = parsed[25544]
    when = datetime(2019, 12, 10, 0, 0, tzinfo=timezone.utc)
    pos = sat._position(tle, when, (-15.8, -47.9, 1100.0))
    assert -90 <= pos["latitude"] <= 90
    assert -180 <= pos["longitude"] <= 180
    assert 300 <= pos["altitude_km"] <= 500
    assert 6.5 <= pos["speed_km_s"] <= 8.5
    assert pos["footprint_radius_km"] > 1000
    assert -90 <= pos["elevation_deg"] <= 90
    assert 0 <= pos["azimuth_deg"] <= 360


def test_v112_pass_calculation_produces_aos_tca_los():
    tle = sat._parse_tle_groups(ISS_TLE)[25544]
    observer = (-15.8, -47.9, 1100.0)
    start = datetime(2019, 12, 10, 0, 0, tzinfo=timezone.utc)
    passes = sat.passes_for_satellite(tle, observer, start, 36, step_seconds=60)
    assert passes
    first = passes[0]
    assert first["aos"] < first["tca"] < first["los"]
    assert first["duration_seconds"] > 0
    assert first["max_elevation_deg"] >= 0
    assert 0 <= first["aos_azimuth_deg"] <= 360
    assert 0 <= first["los_azimuth_deg"] <= 360


def test_v112_rf_transport_forces_last_hop_to_igate_to_remain_rf():
    source, edges = db._observed_topology_edges(
        "PU2AKM-7>APRS,PT2DGI*,WIDE2-1,qAr,PT2PAG-15:>received by local TNC",
        "RF",
    )
    assert source == "PU2AKM-7"
    assert ("PU2AKM-7", "PT2DGI", "rf", None) in edges
    assert ("PT2DGI", "PT2PAG-15", "rf", "PT2PAG-15") in edges
    assert not any(kind == "igate" for _a, _b, kind, _igate in edges)

    _source, internet_edges = db._observed_topology_edges(
        "PU2AKM-7>APRS,PT2DGI*,WIDE2-1,qAr,PT2PAG-15:>from aprs-is",
        "APRS-IS",
    )
    assert ("PT2DGI", "PT2PAG-15", "igate", "PT2PAG-15") in internet_edges


def test_v112_topology_pipeline_persists_transport_evidence(tmp_path):
    original = db.DB_PATH
    try:
        db.DB_PATH = tmp_path / "v112.db"
        db.init_db()
        parsed = {"from": "PU2AKM-7", "format": "status", "path": ["PT2DGI*", "qAr", "PT2PAG-15"]}
        raw = "PU2AKM-7>APRS,PT2DGI*,qAr,PT2PAG-15:>rf"
        db.process_received_packet(raw, parsed, "PU2AKM-7", "status", medium="RF")

        with db.connection() as conn:
            row = conn.execute(
                """SELECT kind,rf_transport_count,rf_path_count,internet_confirmed_count
                   FROM topology_edges
                   WHERE source='PT2DGI' AND target='PT2PAG-15'"""
            ).fetchone()
        assert row is not None
        assert row["kind"] == "rf"
        assert row["rf_transport_count"] >= 1
        assert row["internet_confirmed_count"] == 0
    finally:
        db.DB_PATH = original


def test_v112_old_destructive_igate_migration_is_gone():
    source = read("pt2vhf_aprs/database.py")
    assert "DELETE FROM topology_edges WHERE kind='rf' AND igate IS NOT NULL" not in source
    assert "_repair_topology_rf_evidence_v112" in source
    assert '_record_topology_from_raw_conn(conn, raw, medium)' in source
    assert '"RF direto do transporte"' in source
    assert '"APRS-IS confirmado"' in source


def test_v112_windows_style_floating_panels_include_logs_and_restore():
    js = read("pt2vhf_aprs/static/js/v190.js")
    css = read("pt2vhf_aprs/static/css/v190.css")
    assert "floatPanel('tab-messages','Mensagens')" in js
    assert "floatPanel('tab-stations','Estações')" in js
    assert "floatPanel('tab-log','Logs')" in js
    assert "v190-window-button v190-minimize" in js
    assert "v190-window-button v190-maximize" in js
    assert "v190-window-button v190-close" in js
    assert "restoreRect" in js
    assert "_pt2vhfResetFloatGeometry" in js
    assert ".v190-floating.v190-minimized" in css
    assert ".v190-floating.v190-maximized" in css
    assert ".v190-window-button.v190-close:hover" in css


def test_v112_top_left_search_field_is_not_installed():
    js = read("pt2vhf_aprs/static/js/v190.js")
    boot = js[js.rfind("async function boot"):]
    assert "installGlobalSearch();" not in boot
    assert "document.querySelector('.v1818-search')?.remove();" in boot


def test_v112_satellite_tab_map_view_and_assets_are_wired():
    html = read("pt2vhf_aprs/templates/index.html")
    app = read("pt2vhf_aprs/static/js/app.js")
    web = read("pt2vhf_aprs/web.py")
    satjs = read("pt2vhf_aprs/static/js/v112.js")
    assert 'data-tab="satellites"' in html
    assert 'id="tab-satellites"' in html
    assert 'id="satelliteMap"' in html
    assert "css/v112.css" in html
    assert "js/v112.js" in html
    assert "satellitesEnabled: localStorage.getItem('pt2vhf_map_item_satellites')" in app
    assert "root:satellites" in app
    assert "pt2vhf:satellite-visibility" in app
    assert "window.pt2vhfMainMap = state.map" in app
    assert "register_v112_satellite_routes" in web
    assert "/api/v112/satellites/passes" in read("pt2vhf_aprs/v112_satellites.py")
    assert "satelliteShowFootprint" in satjs
    assert "satelliteFollowSelected" in satjs
    assert "pt2vhf_v112_pass_notified" in satjs
    assert "/api/v111/notifications" in satjs


def test_v112_requirements_include_sgp4():
    assert "sgp4>=" in read("requirements.txt")
