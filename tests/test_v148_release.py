from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db
from pt2vhf_aprs.aprs_service import APRSService
from pt2vhf_aprs.v111_features import apply_retention, retention_settings, save_retention_settings


def test_v148_version_metadata_and_ui_markers():
    root = Path(__file__).resolve().parent.parent
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    assert tuple(int(part) for part in version.split(".")) >= (1, 14, 8)
    assert f'__version__ = "{version}"' in (root / "pt2vhf_aprs" / "__init__.py").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "v111.js").read_text(encoding="utf-8")
    assert "Não apagar" in js
    assert "1 semana" in js
    assert "1 mês" in js
    assert "v148AutoReplyEnabled" in js
    assert "v148AutoReplyText" in js


def test_v148_auto_reply_defaults_persist_and_are_disabled_by_default():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            cfg = db.get_config()
            assert cfg["auto_reply_enabled"] == 0
            assert cfg["auto_reply_cooldown_seconds"] == 300
            assert cfg["auto_reply_text"]

            saved = db.save_config({
                "auto_reply_enabled": True,
                "auto_reply_text": "  Estou ausente.\nRetorno em breve.  ",
                "auto_reply_cooldown_seconds": 60,
            })
            assert saved["auto_reply_enabled"] == 1
            assert saved["auto_reply_text"] == "Estou ausente. Retorno em breve."
            assert saved["auto_reply_cooldown_seconds"] == 60
    finally:
        db.DB_PATH = original


def test_v148_auto_reply_only_direct_message_and_has_cooldown(monkeypatch):
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF",
                "ssid": 0,
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": 1000,
                "sound_on_personal_message": False,
                "auto_reply_enabled": True,
                "auto_reply_text": "Recebido automaticamente.",
                "auto_reply_cooldown_seconds": 300,
            })
            service = APRSService()
            sent = []
            monkeypatch.setattr(
                service,
                "queue_message_parts",
                lambda destination, text, route="auto", path="", automated=False: sent.append(
                    (destination, text, route, automated)
                ) or {"row_ids": [1]},
            )

            service._handle_message(
                {"from": "PY2ABC-9", "to": "PT2VHF", "text": "Olá"},
                "PY2ABC-9>APRS::PT2VHF  :Olá",
            )
            service._handle_message(
                {"from": "PY2ABC-9", "to": "PT2VHF", "text": "Outra mensagem"},
                "PY2ABC-9>APRS::PT2VHF  :Outra mensagem",
            )
            service._handle_message(
                {"from": "PY2ABC-9", "to": "BLN0", "text": "Boletim"},
                "PY2ABC-9>APRS::BLN0     :Boletim",
            )

            assert sent == [("PY2ABC-9", "Recebido automaticamente.", "aprs_is", True)]
    finally:
        db.DB_PATH = original


def test_v148_outgoing_auto_reply_is_marked_in_history():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            ids = db.add_outgoing_message_parts([{
                "from_call": "PT2VHF",
                "to_call": "PY2ABC-9",
                "message": "Auto",
                "msg_id": "001",
                "status": "Na fila",
                "automated": True,
                "tx_medium": "APRS-IS",
                "tx_path": "TCPIP*",
            }])
            row = db.get_message(ids[0])
            assert row["automated"] == 1
    finally:
        db.DB_PATH = original


def test_v148_retention_presets_are_independent_and_prune_topology_edges():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            settings = save_retention_settings({
                "messages_days": 7,
                "tracks_days": 30,
                "topology_events_days": 1,
            })
            assert settings["messages_days"] == 7
            assert settings["tracks_days"] == 30
            assert settings["topology_events_days"] == 1
            # Existing categories not supplied keep their previous/default values.
            assert retention_settings()["packets_days"] == 180

            old = (datetime.now(timezone.utc) - timedelta(days=2)).replace(microsecond=0).isoformat()
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            with db.connection() as conn:
                conn.execute(
                    "INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen,igate) VALUES(?,?,?,?,?,?,?)",
                    ("PY2OLD", "PT2OLD", "rf", 1, old, old, None),
                )
                conn.execute(
                    "INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen,igate) VALUES(?,?,?,?,?,?,?)",
                    ("PY2NEW", "PT2NEW", "rf", 1, now, now, None),
                )
                conn.execute(
                    "INSERT INTO topology_events(timestamp,source,target,kind) VALUES(?,?,?,?)",
                    (old, "PY2OLD", "PT2OLD", "rf"),
                )

            result = apply_retention()
            assert result["deleted"]["topology_edges"] == 1
            assert result["deleted"]["topology_events"] == 1
            assert "reclaimable_bytes" in result
            with db.connection() as conn:
                rows = conn.execute("SELECT source FROM topology_edges ORDER BY source").fetchall()
            assert [row["source"] for row in rows] == ["PY2NEW"]
    finally:
        db.DB_PATH = original
