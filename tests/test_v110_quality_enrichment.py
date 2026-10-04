from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs import v110_features as v110
from pt2vhf_aprs.soak_test import SoakTestManager


def _temp_db():
    td = tempfile.TemporaryDirectory()
    return td, Path(td.name) / "v110.db"


def test_qrz_official_xml_provider_and_cache(monkeypatch):
    td, path = _temp_db()
    old = db.DB_PATH
    try:
        db.DB_PATH = path
        db.init_db()
        v110._save_settings({
            "qrz_enabled": True,
            "qrz_username": "user",
            "qrz_password": "secret",
            "qrz_cache_hours": 24,
        })
        replies = iter([
            b'<QRZDatabase><Session><Key>ABC123</Key></Session></QRZDatabase>',
            b'<QRZDatabase><Callsign><call>PY2ABC</call><fname>Joao</fname><name>Silva</name><addr2>Sao Paulo</addr2><state>SP</state><country>Brazil</country><grid>GG66</grid><image>https://img.example/PY2ABC.jpg</image></Callsign></QRZDatabase>',
        ])
        monkeypatch.setattr(v110, "_urlopen", lambda *a, **k: next(replies))
        result = v110._qrz_lookup("PY2ABC", force=True)
        assert result["available"] is True
        assert result["city"] == "Sao Paulo"
        assert result["state"] == "SP"
        assert result["grid"] == "GG66"
        assert result["image_url"].startswith("https://")
        cached = v110._qrz_lookup("PY2ABC", force=False)
        assert cached["available"] is True
        assert "_cache" in cached
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)
        td.cleanup()


def test_ais_provider_requires_mmsi_and_uses_configured_json(monkeypatch):
    td, path = _temp_db()
    old = db.DB_PATH
    try:
        db.DB_PATH = path
        db.init_db()
        v110._save_settings({
            "ais_enabled": True,
            "ais_url_template": "https://ais.example/vessel/{mmsi}?imo={imo}",
            "ais_api_key": "key",
            "ais_cache_hours": 12,
        })
        monkeypatch.setattr(v110, "_urlopen", lambda *a, **k: json.dumps({
            "name": "TEST VESSEL",
            "image_url": "https://img.example/vessel.jpg",
        }).encode("utf-8"))
        result = v110._ais_lookup("710123456", "1234567", force=True)
        assert result["available"] is True
        assert result["name"] == "TEST VESSEL"
        assert result["image_url"].startswith("https://")
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)
        td.cleanup()


def test_rf_metadata_preserves_unavailable_values_and_real_values():
    td, path = _temp_db()
    old = db.DB_PATH
    try:
        db.DB_PATH = path
        db.init_db()
        v110.record_rf_metadata("PY2ABC", rssi=-91.5, snr=7.0, dcd=True, frequency_hz=144390000, provider="test-modem")
        rows = v110.recent_rf_metadata("PY2ABC", 5)
        assert rows[0]["rssi"] == -91.5
        assert rows[0]["snr"] == 7.0
        assert rows[0]["dcd"] is True
        v110.record_rf_metadata("PY2DEF", provider="kiss-no-metrics")
        rows2 = v110.recent_rf_metadata("PY2DEF", 1)
        assert rows2[0]["rssi"] is None
        assert rows2[0]["snr"] is None
        assert rows2[0]["dcd"] is None
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)
        td.cleanup()


def test_external_secret_is_preserved_when_blank_update():
    td, path = _temp_db()
    old = db.DB_PATH
    try:
        db.DB_PATH = path
        db.init_db()
        v110._save_settings({"qrz_enabled": True, "qrz_username": "u", "qrz_password": "secret"})
        public = v110._save_settings({"qrz_username": "u2", "qrz_password": ""})
        assert public["qrz_password"] == ""
        assert public["qrz_password_set"] is True
        assert v110._settings()["qrz_password"] == "secret"
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)
        td.cleanup()


def test_soak_report_detects_large_memory_growth():
    td, path = _temp_db()
    old = db.DB_PATH
    try:
        db.DB_PATH = path
        db.init_db()
        manager = SoakTestManager()
        manager._ensure_schema()
        manager._run_id = "test-soak"
        with db.connection() as conn:
            conn.execute(
                "INSERT INTO soak_runs_v110(run_id,started_at,target_hours,interval_seconds,platform,status) VALUES(?,?,?,?,?,?)",
                ("test-soak", "2026-10-01T00:00:00+00:00", 2, 300, "test", "completed"),
            )
            conn.execute(
                "INSERT INTO soak_samples_v110(run_id,timestamp,process_rss_bytes,process_cpu_percent,db_size_bytes) VALUES(?,?,?,?,?)",
                ("test-soak", "2026-10-01T00:00:00+00:00", 100_000_000, 5.0, 1_000_000),
            )
            conn.execute(
                "INSERT INTO soak_samples_v110(run_id,timestamp,process_rss_bytes,process_cpu_percent,db_size_bytes) VALUES(?,?,?,?,?)",
                ("test-soak", "2026-10-01T02:00:00+00:00", 260_000_000, 8.0, 2_000_000),
            )
        report = manager.report()
        assert report["duration_hours"] == 2.0
        assert report["rss_growth_bytes"] == 160_000_000
        assert report["memory_leak_suspected"] is True
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)
        td.cleanup()


def test_v110_frontend_and_docs_present():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pt2vhf_aprs/static/js/v110.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs/static/css/v110.css").read_text(encoding="utf-8")
    docs = (root / "docs/TM_D700_VALIDATION.md").read_text(encoding="utf-8")
    assert "QRZ.com" in js
    assert "/api/v110/ais-profile/" in js
    assert "/api/v110/soak/start" in js
    assert "/api/v110/tm-d700/probe" in js
    assert ".v110-profile-photo" in css
    assert "Somente considerar o TM-D700" in docs
