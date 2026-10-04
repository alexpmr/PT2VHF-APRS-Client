from __future__ import annotations

import tempfile
from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs.v190_features import _global_search, _save_group, _save_station_meta, _snapshot_bytes


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
