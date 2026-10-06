from __future__ import annotations

import tempfile
from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs.v190_features import ALERT_DEFAULTS, _alert_state, _global_search, _json_setting, _save_group, _save_json_setting, _save_station_meta, _snapshot_bytes


def test_v190_group_meta_search_and_backup():
    old = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "v190.db"
            db.init_db()
            with db.connection() as conn:
                conn.execute(
                    """INSERT INTO stations(callsign,name,last_heard,info,message_capable)
                       VALUES('PT2ABC','Teste','2026-10-04T18:00:00+00:00','estacao de teste',1)"""
                )
            group = _save_group({"name": "Amigos"})
            _save_station_meta("PT2ABC", {"friendly_name": "Base ABC", "group_id": group["id"], "note": "teste"})
            rows = _global_search("base", 10)
            assert rows and rows[0]["callsign"] == "PT2ABC"
            assert rows[0]["group_name"] == "Amigos"
            payload = _snapshot_bytes()
            assert payload.startswith(b"PK")
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)


def test_v190_frontend_contains_detachable_panels():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pt2vhf_aprs/static/js/v190.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs/static/css/v190.css").read_text(encoding="utf-8")
    assert "floatPanel('tab-messages'" in js
    assert "floatPanel('tab-stations'" in js
    assert "resize:both" in css
    assert "v190-presentation" in css


def test_v190_alert_settings_preserve_false_values():
    old = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "alerts.db"
            db.init_db()
            payload = dict(ALERT_DEFAULTS)
            payload.update({
                "station_appeared": False,
                "station_disappeared": False,
                "favorite_appeared": False,
                "new_message": True,
            })
            _save_json_setting("alerts", payload)
            saved = _json_setting("alerts", ALERT_DEFAULTS)
            assert saved["station_appeared"] is False
            assert saved["station_disappeared"] is False
            assert saved["favorite_appeared"] is False
            assert saved["new_message"] is True
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)


def test_v190_alert_state_separates_active_from_disappeared_stations():
    old = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "alert-state.db"
            db.init_db()
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            active = (now - timedelta(minutes=1)).replace(microsecond=0).isoformat()
            stale = (now - timedelta(minutes=120)).replace(microsecond=0).isoformat()
            with db.connection() as conn:
                conn.execute(
                    "INSERT INTO stations(callsign,name,last_heard,message_capable) VALUES(?,?,?,?)",
                    ("PT2NEW", "Ativa", active, 1),
                )
                conn.execute(
                    "INSERT INTO stations(callsign,name,last_heard,message_capable) VALUES(?,?,?,?)",
                    ("PT2OLD", "Sumida", stale, 1),
                )
                conn.execute(
                    "INSERT INTO favorites(callsign,created_at) VALUES(?,?)",
                    ("PT2NEW", active),
                )
            state = _alert_state("", 60)
            active_calls = {row["callsign"] for row in state["active_stations"]}
            disappeared_calls = {row["callsign"] for row in state["disappeared"]}
            assert "PT2NEW" in active_calls
            assert "PT2NEW" not in disappeared_calls
            assert "PT2OLD" not in active_calls
            assert "PT2OLD" in disappeared_calls
            favorite = next(row for row in state["active_stations"] if row["callsign"] == "PT2NEW")
            assert favorite["favorite"] == 1
            assert "stations_since" not in state
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)


def test_v190_frontend_alerts_are_edge_triggered_and_deduplicated():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pt2vhf_aprs/static/js/v190.js").read_text(encoding="utf-8")
    assert "previousActive=null" in js
    assert "if(previousActive!==null)" in js
    assert "seenMessageIds" in js
    assert "databaseProblemLatched" in js
    assert "tncWanted=state.tnc?.wanted!==false" in js
    assert "aprsWanted=state.aprs_is?.wanted!==false" in js
    assert "window.__pt2vhfV190AlertSettings" in js
    assert "window.__pt2vhfV190AlertSettingsDirty=true" in js
    assert "void saveAlertSettings(false)" in js
