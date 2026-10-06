from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs import v114_satellite_ops as ops


def read(rel: str) -> str:
    return (Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")


def test_v114_next_pass_honors_eligible_satellites(monkeypatch):
    now = datetime.now(timezone.utc)
    raw = [
        {"norad_id": 1, "name": "IGNORED", "aos": (now + timedelta(minutes=2)).isoformat(), "tca": (now + timedelta(minutes=5)).isoformat(), "los": (now + timedelta(minutes=8)).isoformat(), "max_elevation_deg": 20},
        {"norad_id": 2, "name": "SELECTED", "aos": (now + timedelta(minutes=4)).isoformat(), "tca": (now + timedelta(minutes=7)).isoformat(), "los": (now + timedelta(minutes=10)).isoformat(), "max_elevation_deg": 35},
    ]
    monkeypatch.setattr(ops, "_observer", lambda: (-15.8, -47.9, 1100.0))
    monkeypatch.setattr(ops.orbital, "satellite_passes", lambda *a, **k: raw)
    monkeypatch.setattr(ops.sat113, "filter_passes", lambda rows, *a, **k: rows)
    chosen = ops.next_selected_aprs_pass({2}, 0)
    assert chosen is not None
    assert chosen["norad_id"] == 2
    assert ops.next_selected_aprs_pass(set(), 0) is None


def test_v114_beacon_profile_is_short_independent_and_persistent(tmp_path):
    original = db.DB_PATH
    try:
        db.DB_PATH = tmp_path / "client.db"
        db.init_db()
        db.save_config({
            **db.get_config(),
            "callsign": "PT2VHF",
            "ssid": "15",
            "latitude": -15.8,
            "longitude": -47.9,
            "symbol_table": "/",
            "symbol": ">",
        })
        saved = ops.save_beacon_profile(25544, {
            "path": "ARISS",
            "comment": "ISS",
            "interval_seconds": 60,
            "coverage_only": True,
            "stop_at_los": True,
            "min_elevation_deg": 5,
            "enabled": False,
            "tx_consent": False,
        })
        assert saved["path"] == "ARISS"
        assert saved["comment"] == "ISS"
        preview = ops.beacon_preview(25544)
        assert ",ARISS:" in preview["raw"]
        assert preview["raw"].endswith("ISS")
        assert "/A=" not in preview["raw"]
        assert preview["frame_size_bytes"] < 100
        again = ops.get_beacon_profile(25544)
        assert again["path"] == "ARISS"
    finally:
        db.DB_PATH = original


def test_v114_beacon_requires_explicit_consent(monkeypatch, tmp_path):
    original = db.DB_PATH
    try:
        db.DB_PATH = tmp_path / "client.db"
        db.init_db()
        db.save_config({**db.get_config(), "callsign": "PT2VHF", "latitude": -15.8, "longitude": -47.9})
        ops.save_beacon_profile(25544, {"enabled": True, "tx_consent": False, "path": "ARISS"})
        with pytest.raises(PermissionError, match="consentimento"):
            ops.send_satellite_beacon(25544, manual=False)
    finally:
        db.DB_PATH = original


def test_v114_search_and_compact_selection_ui():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/v112.js")
    css = read("pt2vhf_aprs/static/css/v114.css")
    assert 'id="satelliteSelectionPanel"' in html
    assert 'id="satelliteQuickSearch"' in html
    assert 'id="satelliteQuickSearchClear"' in html
    assert "visibleCatalogRows" in js
    assert "meta.callsign" in js
    assert "meta.norad_id" in js
    assert "visibleCatalogRows())state.selected.add" in js
    assert "visibleCatalogRows())state.selected.delete" in js
    assert ".satellite-selection-panel" in css


def test_v114_countdown_is_below_tab_and_large_selected_favorite_only():
    html = read("pt2vhf_aprs/templates/index.html")
    v113 = read("pt2vhf_aprs/static/js/v113.js")
    css = read("pt2vhf_aprs/static/css/v114.css")
    nav_start = html.index('<nav class="tabs"')
    nav_end = html.index("</nav>", nav_start)
    nav = html[nav_start:nav_end]
    assert 'id="satelliteTabCountdown"' not in nav
    assert 'class="satellite-operation-bar"' in html
    assert 'id="satelliteTabCountdown"' in html
    assert "/api/v114/satellites/next-pass" in v113
    assert "pt2vhf_v112_satellite_selected" in v113
    assert "pt2vhf_v112_satellite_favorites" in v113
    assert "font-size:30px" in css


def test_v114_satellite_tab_has_stations_messages_and_shared_message_api():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/v114.js")
    backend = read("pt2vhf_aprs/v114_satellite_ops.py")
    for ident in (
        "satelliteStationsList", "satelliteStationDetail", "satelliteMessageTo",
        "satelliteMessageText", "satelliteMessageSend", "satelliteConversation",
        "satelliteStationsContext", "satelliteStationsContextOnly",
    ):
        assert f'id="{ident}"' in html
    assert "/api/v114/satellites/stations" in js
    assert "/api/messages/send" in js
    assert "/api/messages?mine=1" in js
    assert "Shift" not in js or "shiftKey" in js
    assert "satellite_stations" in backend


def test_v114_satellite_beacon_ui_and_tnc_pipeline():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/v114.js")
    tnc = read("pt2vhf_aprs/tnc_service.py")
    backend = read("pt2vhf_aprs/v114_satellite_ops.py")
    for ident in (
        "satelliteBeaconSatellite", "satelliteBeaconPath", "satelliteBeaconComment",
        "satelliteBeaconInterval", "satelliteBeaconMinElevation",
        "satelliteBeaconCoverageOnly", "satelliteBeaconStopLos",
        "satelliteBeaconEnabled", "satelliteBeaconConsent",
        "satelliteBeaconPreview", "satelliteBeaconSendNow",
    ):
        assert f'id="{ident}"' in html
    assert "queue_satellite_beacon" in tnc
    assert "tx_consent" in backend
    assert "interval_seconds" in backend
    assert "stop_at_los" in backend
    assert "/beacon/preview" in backend
    assert "satellite_beacon_history_v114" in backend
    assert "previewBeacon" in js


def test_v114_tnc_health_component_is_owned_by_tnc_tab_only():
    js = read("pt2vhf_aprs/static/js/v111.js")
    start = js.index("function installTncOperations")
    end = js.index("function installDatabaseHealth", start)
    block = js[start:end]
    assert "const tab=$('#tab-tnc')" in block
    assert "tab.insertBefore(host" in block
    assert "host.parentElement!==tab" in block
    assert "#tab-config" not in block
    assert "#tab-about" not in block


def test_v114_web_registers_satellite_ops():
    web = read("pt2vhf_aprs/web.py")
    assert "register_v114_routes(app)" in web
