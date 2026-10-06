from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs import tnc_service
from pt2vhf_aprs import v111_features
from pt2vhf_aprs import v113_satellites as sat


def read(rel: str) -> str:
    return (Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")


def test_v113_strict_aprs_classification_does_not_promote_generic_ax25():
    colibri = {
        "norad_id": 61746,
        "name": "Colibri-S",
        "protocol": "packet/AX.25",
        "mode": "GFSK",
        "transmitters": [{"description": "AX.25 telemetry", "mode": "GFSK"}],
    }
    classified = sat.classify_operation(colibri)
    assert classified["aprs_confirmed"] is False
    assert classified["operation_type"] == "Packet/AX.25"

    iss = sat.classify_operation({
        "norad_id": 25544,
        "name": "ISS (ZARYA)",
        "protocol": "APRS/packet",
        "transmitters": [],
    })
    assert iss["aprs_confirmed"] is True
    assert iss["operation_type"] == "APRS"


def test_v113_catalog_scope_defaults_to_confirmed_aprs(monkeypatch):
    monkeypatch.setattr(sat.orbital, "satellite_catalog", lambda: [
        {"norad_id": 25544, "name": "ISS", "protocol": "APRS/packet", "transmitters": []},
        {"norad_id": 61746, "name": "Colibri-S", "protocol": "packet/AX.25", "transmitters": [{"description": "AX.25 telemetry"}]},
    ])
    aprs = sat.enriched_catalog("aprs")
    packet = sat.enriched_catalog("packet")
    assert [x["norad_id"] for x in aprs] == [25544]
    assert {x["norad_id"] for x in packet} == {25544, 61746}


def test_v113_operational_override_persists_separately_from_tle(tmp_path):
    original = db.DB_PATH
    try:
        db.DB_PATH = tmp_path / "client.db"
        saved = sat.save_operational_state(25544, {
            "state": "ignore",
            "note": "SSTV/APRS temporariamente fora do ar",
            "services": {"aprs": False, "sstv": True},
        })
        again = sat.get_operational_state(25544)
        assert saved["state"] == "ignore"
        assert again["state"] == "ignore"
        assert again["services"]["aprs"] is False
        assert again["services"]["sstv"] is True
    finally:
        db.DB_PATH = original


def test_v113_source_fallback_and_dedup_by_norad(monkeypatch, tmp_path):
    original = db.DB_PATH
    try:
        db.DB_PATH = tmp_path / "client.db"
        sat.save_satellite_settings({
            "sources": [
                {"id": "celestrak_amateur", "enabled": True, "priority": 10},
                {"id": "celestrak_stations", "enabled": True, "priority": 20},
                {"id": "amsat_nasabare", "enabled": True, "priority": 30},
            ]
        })
        monkeypatch.setattr(sat.orbital, "refresh_satellite_data", lambda force=True: {
            "catalog": [], "tles": {}, "errors": [], "updated_at": None
        })
        captured = {}
        monkeypatch.setattr(sat.orbital, "_save_cache", lambda value: captured.update(value))

        def fake_download(source):
            sid = source["id"]
            if sid == "celestrak_amateur":
                raise RuntimeError("primary unavailable")
            if sid == "celestrak_stations":
                return ({25544: {"norad_id": 25544, "line1": "1 x", "line2": "2 x", "source": "stations"}}, {"ok": True, "count": 1})
            return ({25544: {"norad_id": 25544, "line1": "1 y", "line2": "2 y", "source": "amsat"}, 99999: {"norad_id": 99999, "line1": "1 z", "line2": "2 z", "source": "amsat"}}, {"ok": True, "count": 2})

        monkeypatch.setattr(sat, "_download_source", fake_download)
        result = sat.refresh_multisource(force=True, reason="test")
        assert result["tles"]["25544"]["source"] == "stations"
        assert "99999" in result["tles"]
        assert len(result["tles"]) == 2
        assert any("primary unavailable" in err for err in result["errors"])
        assert captured["tles"]["25544"]["source"] == "stations"
    finally:
        db.DB_PATH = original


def test_v113_scheduler_due_respects_configured_daily_time():
    settings = {**sat.DEFAULT_SETTINGS, "auto_update_enabled": True, "update_hour": 0, "update_minute": 0, "update_interval_hours": 24}
    now = datetime(2026, 10, 6, 0, 5, tzinfo=timezone.utc)
    assert sat._scheduled_due(settings, {}, now) is True
    runtime = {"_last_update": {"at": "2026-10-06T00:01:00+00:00"}}
    assert sat._scheduled_due(settings, runtime, now) is False


def test_v113_tm_d700_serial_and_rf_bauds_are_independent():
    cfg = tnc_service.normalize_tnc_config({
        "transport": "serial",
        "serial_port": "COM2",
        "serial_baud": 9600,
        "device_profile": "kenwood_tm_d700",
        "serial_protocol": "terminal",
        "packet_rf_baud": 1200,
    }, strict=False)
    assert cfg["serial_baud"] == 9600
    assert cfg["packet_rf_baud"] == 1200
    assert cfg["serial_protocol"] == "terminal"


def test_v113_tnc_health_terminal_bytes_not_reported_as_missing_kiss(monkeypatch, tmp_path):
    original = db.DB_PATH
    try:
        db.DB_PATH = tmp_path / "health.db"
        db.init_db()
        status = {
            "connected": True, "connected_since": "", "transport": "serial", "endpoint": "COM2 @ 9600",
            "frames_rx": 0, "frames_tx": 0, "transport_bytes_rx": 120, "transport_bytes_tx": 0,
            "kiss_frames_rx": 0, "invalid_frames_rx": 0, "last_rx_at": "", "last_tx_at": "",
            "last_transport_sample_ascii": "cmd: ", "last_transport_sample_hex": "63 6d 64 3a 20",
        }
        monkeypatch.setattr(v111_features.tnc_service, "status", lambda: dict(status))
        monkeypatch.setattr(v111_features, "get_tnc_config", lambda: {
            "transport": "serial", "device_profile": "kenwood_tm_d700", "serial_protocol": "terminal",
            "serial_baud": 9600, "packet_rf_baud": 1200,
        })
        snap = v111_features.tnc_health_snapshot(record_transition=False)
        assert snap["health_state"] == "terminal_prompt_detected"
        assert "KISS não é exigido" in snap["health_summary"]

        monkeypatch.setattr(v111_features, "get_tnc_config", lambda: {
            "transport": "serial", "device_profile": "generic_kiss", "serial_protocol": "kiss",
            "serial_baud": 9600, "packet_rf_baud": 1200,
        })
        snap2 = v111_features.tnc_health_snapshot(record_transition=False)
        assert snap2["health_state"] == "bytes_without_kiss"
    finally:
        db.DB_PATH = original


def test_v113_tnc_self_test_reports_validation_layers():
    result = v111_features.run_tnc_self_test()
    assert result["layers"]["transport"] is True
    assert result["layers"]["framing_protocol"] is True
    assert result["layers"]["ax25"] is True
    assert result["layers"]["rx"] is True
    assert result["layers"]["tx_model"] is True
    assert result["layers"]["physical_rf_tx"] is False


def test_v113_ui_has_countdown_alarm_bulk_selection_sources_and_tnc_profiles():
    html = read("pt2vhf_aprs/templates/index.html")
    satjs = read("pt2vhf_aprs/static/js/v113.js")
    v112js = read("pt2vhf_aprs/static/js/v112.js")
    tncjs = read("pt2vhf_aprs/static/js/tnc.js")
    css = read("pt2vhf_aprs/static/css/v113.css")

    for ident in (
        "satelliteTabCountdown", "satelliteSelectAll", "satelliteClearAll",
        "satelliteCatalogScope", "satelliteCoverageAlarmEnabled",
        "satelliteSourcesList", "satelliteAutoUpdateEnabled", "satelliteUpdateTime",
        "tncDeviceProfile", "tncSerialProtocol", "tncPacketRfBaud",
        "tncDiagnosticSample",
    ):
        assert f'id="{ident}"' in html

    assert "formatHms" in satjs
    assert "setInterval(renderCountdown,1000)" in satjs
    assert "showAlarm" in satjs
    assert "satellite-source-row" in satjs
    assert "satellite-operational" in v112js
    assert "data-satellite-service" in v112js
    assert "terminal_bytes_active" in tncjs
    assert "Kenwood TM-D700 em modo terminal/PKT" in tncjs
    assert ".satellite-tab-countdown" in css


def test_v113_satellite_backend_registers_scheduler_and_multisource_routes():
    web = read("pt2vhf_aprs/web.py")
    backend = read("pt2vhf_aprs/v113_satellites.py")
    assert "register_v113_satellite_routes(app)" in web
    assert "AMSAT_NASABARE_TLE" in backend
    assert "/api/v113/satellites/next-pass" in backend
    assert "/api/v113/satellites/source-test" in backend
    assert "start_scheduler()" in backend
