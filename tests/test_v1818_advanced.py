from __future__ import annotations

import tempfile
from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs.advanced_features import _period_comparison, _quality
from pt2vhf_aprs.agwpe_transport import AGWPEStreamDecoder, enable_raw_command, raw_tx_frame


def test_agwpe_header_roundtrip_raw_frame():
    raw = bytes(range(32))
    decoder = AGWPEStreamDecoder()
    frames = decoder.feed(raw_tx_frame(raw, port=2))
    assert len(frames) == 1
    assert frames[0].kind == "K"
    assert frames[0].port == 2
    assert frames[0].data == raw
    assert len(enable_raw_command()) == 36


def test_advanced_quality_and_comparison_on_empty_db():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "v1818.db"
            db.init_db()
            quality = _quality(24)
            comparison = _period_comparison(24)
            assert quality["packets"] == 0
            assert quality["stations"] == 0
            assert comparison["hours"] == 24
            assert "changes" in comparison
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_v1818_version_and_arm64_updater_metadata(monkeypatch):
    from pt2vhf_aprs import updater
    root = Path(__file__).resolve().parents[1]
    assert (root / "VERSION").read_text(encoding="utf-8").strip() == "1.13.0"
    win = (root / "windows" / "version_info.txt").read_text(encoding="utf-8")
    assert "filevers=(1, 13, 0, 0)" in win
    assert "prodvers=(1, 13, 0, 0)" in win

    monkeypatch.setattr(updater, "_machine", lambda: "arm64")
    monkeypatch.setattr(updater, "current_update_mode", lambda: "linux-tar")
    assert updater.desired_asset_name("1.13.0") == "PT2VHF_APRS_Client_Linux_arm64_v1.13.0.tar.gz"
    monkeypatch.setattr(updater, "current_update_mode", lambda: "linux-deb")
    assert updater.desired_asset_name("1.13.0") == "pt2vhf-aprs-client_1.13.0_arm64.deb"
    monkeypatch.setattr(updater, "current_update_mode", lambda: "linux-appimage")
    assert updater.desired_asset_name("1.13.0") == "PT2VHF_APRS_Client_arm64_v1.13.0.AppImage"


def test_v1818_release_docs_and_routes_are_present():
    root = Path(__file__).resolve().parents[1]
    web = (root / "pt2vhf_aprs" / "advanced_features.py").read_text(encoding="utf-8")
    ui = (root / "pt2vhf_aprs" / "static" / "js" / "v1818.js").read_text(encoding="utf-8")
    for endpoint in (
        "/api/v1818/stations/search",
        "/api/v1818/network-quality",
        "/api/v1818/period-compare",
        "/api/v1818/topology-graph",
        "/api/v1818/export.csv",
        "/api/v1818/export.geojson",
        "/api/v1818/diagnostics.zip",
    ):
        assert endpoint in web
    assert "pt2vhfFocusStation" in ui
    assert "v1818-network-svg" in ui


def test_tnc_transport_visibility_uses_collection_selector():
    source = (Path(__file__).resolve().parents[1] / "pt2vhf_aprs" / "static" / "js" / "tnc.js").read_text(encoding="utf-8")
    assert "$$('.tnc-serial-field').forEach" in source
    assert "$$('.tnc-tcp-field').forEach" in source
    assert "$$('.tnc-agwpe-field').forEach" in source
