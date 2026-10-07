from __future__ import annotations

from pathlib import Path

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs import tnc_service
from pt2vhf_aprs import v111_features


def read(rel: str) -> str:
    return (Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")


def test_v113_terminal_profile_blocks_automatic_tx():
    with pytest.raises(ValueError, match="terminal/PKT"):
        tnc_service.normalize_tnc_config({
            "transport": "serial",
            "serial_port": "COM2",
            "serial_baud": 9600,
            "device_profile": "kenwood_tm_d700",
            "serial_protocol": "terminal",
            "packet_rf_baud": 1200,
            "auto_tx_enabled": 1,
            "tx_confirmed": 1,
        }, strict=True)


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


def test_v113_tnc_ui_and_diagnostics_remain_after_sat_removal():
    html = read("pt2vhf_aprs/templates/index.html")
    tncjs = read("pt2vhf_aprs/static/js/tnc.js")
    css = read("pt2vhf_aprs/static/css/v113.css")
    for ident in ("tncDeviceProfile", "tncSerialProtocol", "tncPacketRfBaud", "tncDiagnosticSample"):
        assert f'id="{ident}"' in html
    assert "terminal_bytes_active" in tncjs
    assert "Kenwood TM-D700 em modo terminal/PKT" in tncjs
    assert ".tnc-diagnostic-sample" in css
