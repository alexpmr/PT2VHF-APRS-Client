from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs import tnc_service
from pt2vhf_aprs.v111_features import (
    RETENTION_DEFAULTS,
    _notifications,
    add_notification,
    apply_retention,
    db_health,
    run_tnc_self_test,
    station_operational_profile,
    tnc_health_snapshot,
)


def test_v111_tnc_self_test_covers_rx_tx_ack():
    result = run_tnc_self_test()
    assert result["ok"] is True
    assert result["kiss_frames_rx"] >= 3
    assert result["ax25_valid_rx"] >= 3
    assert result["checks"]["ack_frame"] is True
    assert result["checks"]["ax25_tx"] is True


def test_v111_notification_center_persists_items():
    old = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "notify.db"
            db.init_db()
            row = add_notification("tnc", "TNC caiu", "teste", severity="warning", entity="COM10")
            assert row["category"] == "tnc"
            rows = _notifications(10)
            assert len(rows) == 1
            assert rows[0]["title"] == "TNC caiu"
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)


def test_v111_database_health_and_retention():
    old = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "retention.db"
            db.init_db()
            old_time = (datetime.now(timezone.utc) - timedelta(days=400)).replace(microsecond=0).isoformat()
            with db.connection() as conn:
                conn.execute(
                    """INSERT INTO packets(timestamp,raw,from_call,medium)
                       VALUES(?,?,?,?)""",
                    (old_time, "PY2OLD>APRS:>old", "PY2OLD", "APRS-IS"),
                )
            result = apply_retention({**RETENTION_DEFAULTS, "packets_days": 30})
            assert result["deleted"]["packets"] >= 1
            health = db_health()
            assert health["integrity"] == "ok"
            assert "packets" in health["tables"]
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)


def test_v111_station_operational_profile_heard_by_and_paths():
    old = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "profile.db"
            db.init_db()
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            tnc_service._ensure_schema()
            with db.connection() as conn:
                conn.execute(
                    """INSERT INTO stations(callsign,name,last_heard,message_capable)
                       VALUES(?,?,?,?)""",
                    ("PY2ABC", "Teste", now, 1),
                )
                conn.execute(
                    """INSERT INTO packets(timestamp,raw,from_call,medium)
                       VALUES(?,?,?,?)""",
                    (now, "PY2ABC>APRS,WIDE1-1:>test", "PY2ABC", "RF"),
                )
                conn.execute(
                    """INSERT INTO tnc_frames(timestamp,direction,medium,source,destination,path,packet_type,raw_tnc2,reason)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (now, "RX", "RF", "PY2ABC", "APRS", '["WIDE1-1"]', "status", "PY2ABC>APRS,WIDE1-1:>test", ""),
                )
                conn.execute(
                    """INSERT INTO topology_events(timestamp,source,target,kind)
                       VALUES(?,?,?,?)""",
                    (now, "PY2ABC", "PT2IGT", "RF"),
                )
            profile = station_operational_profile("PY2ABC", 24)
            assert profile["summary"]["packets"] == 1
            assert profile["summary"]["rf_packets"] == 1
            assert "WIDE1-1" in profile["paths"][0]["path"]
            assert profile["heard_by"][0]["observer"] == "PT2IGT"
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)


def test_v111_tnc_status_reconciles_persisted_session_frames(monkeypatch):
    old = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "tnc.db"
            db.init_db()
            tnc_service._ensure_schema()
            service = tnc_service.TNCService()
            started = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            service._set_status(connected=True, wanted=True, connected_since=started, frames_rx=0, frames_tx=0)
            with db.connection() as conn:
                conn.execute(
                    """INSERT INTO tnc_frames(timestamp,direction,medium,source,destination,path,packet_type,raw_tnc2,reason)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (started, "RX", "RF", "PY2ABC", "APRS", "[]", "position", "PY2ABC>APRS:>test", ""),
                )
                conn.execute(
                    """INSERT INTO tnc_frames(timestamp,direction,medium,source,destination,path,packet_type,raw_tnc2,reason)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    (started, "TX", "RF", "PT2TST", "APRS", "[]", "message", "PT2TST>APRS:>test", ""),
                )
            status = service.status()
            assert status["frames_rx"] == 1
            assert status["frames_tx"] == 1
            assert status["session_persisted_frames_rx"] == 1
            assert status["session_persisted_frames_tx"] == 1
    finally:
        db.DB_PATH = old
        db.invalidate_map_data_cache(drop_payload=True)


def test_v111_frontend_contains_operational_features():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pt2vhf_aprs" / "static" / "js" / "v111.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "v111.css").read_text(encoding="utf-8")
    for needle in (
        "v111Bell", "v111TncSelfTest", "v111DbHealth",
        "/api/v111/station/", "Ouvido por", "Copiar diagnóstico",
    ):
        assert needle in js
    assert ".v111-notify-panel" in css
    assert ".v111-counter-grid" in css
