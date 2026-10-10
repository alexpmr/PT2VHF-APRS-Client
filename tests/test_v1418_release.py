from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db
from pt2vhf_aprs.aprs_service import APRSService

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1418_version_metadata():
    version = read("VERSION").strip()
    parts = tuple(int(part) for part in version.split("."))
    assert parts >= (1, 14, 18)
    assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
    win = read("windows/version_info.txt")
    assert str(parts + (0,)) in win
    assert f"'{version}'" in win


def test_v1418_station_follow_action_and_live_panel():
    js = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "station-follow-button" in js
    assert "Acompanhar Estação" in js
    assert "function followStation(" in js
    assert "function ensureTrackFollowPanel(" in js
    assert "function updateTrackFollowPanel(" in js
    assert "function scheduleTrackFollowPanelRefresh(" in js
    assert "state.map?.closePopup?.()" in js
    assert "state.map.panTo(point" in js
    assert "state.map.on('dragstart'" in js
    assert ".station-follow-panel" in css
    assert ".station-follow-stop" in css


def test_v1418_ack_is_terminal_against_late_tx_state():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            row_id = db.add_message(
                "out", "PT2VHF", "PP5AU-7", "Teste",
                msg_id="123", status="Enviada",
            )
            assert db.mark_message_status("123", "ACK", "PP5AU-7") == 1
            assert db.mark_message_status("123", "Reenviada", "PP5AU-7") == 0
            assert db.get_message(row_id)["status"] == "ACK"
    finally:
        db.DB_PATH = original


def test_v1418_retry_reuses_same_message_id_and_row(monkeypatch):
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF", "ssid": 0,
                "latitude": -15.8, "longitude": -47.9, "altitude": 1000,
                "message_retry_attempts": 2,
            })
            row_id = db.add_message(
                "out", "PT2VHF", "PP5AU-7", "Teste de retry",
                msg_id="321", status="Enviada",
                retry_count=0, tx_medium="APRS-IS", tx_path="TCPIP*",
            )
            service = APRSService()
            service._set_status(connected=True, verified=True)
            sent = []
            monkeypatch.setattr(service, "_send_raw", sent.append)

            result = service.retry_message(row_id, route="aprs_is")
            row = db.get_message(row_id)
            assert result["id"] == row_id
            assert result["message_id"] == "321"
            assert result["retry_count"] == 1
            assert row["msg_id"] == "321"
            assert row["retry_count"] == 1
            assert row["status"] == "Reenviada"
            assert sent and sent[0].endswith(":Teste de retry{321")
            assert len(db.list_messages(station_filter="PP5AU-7")) == 1
    finally:
        db.DB_PATH = original


def test_v1418_received_message_id_is_deduplicated_but_ack_repeats(monkeypatch):
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF", "ssid": 0,
                "latitude": -15.8, "longitude": -47.9, "altitude": 1000,
            })
            service = APRSService()
            acks = []
            monkeypatch.setattr(service, "send_rf_ack", lambda peer, mid: acks.append((peer, mid)))
            msg = {"from": "PP5AU-7", "to": "PT2VHF", "text": "Duplicada{77"}
            raw = "PP5AU-7>APZVHF::PT2VHF  :Duplicada{77"

            service._handle_message(msg, raw, via_rf=True)
            service._handle_message(msg, raw, via_rf=True)

            rows = db.list_messages(station_filter="PP5AU-7")
            assert len(rows) == 1
            assert rows[0]["msg_id"] == "77"
            assert acks == [("PP5AU-7", "77"), ("PP5AU-7", "77")]
    finally:
        db.DB_PATH = original


def test_v1418_tnc_has_pure_rf_ack_and_duplicate_reack():
    tnc = read("pt2vhf_aprs/tnc_service.py")
    service = read("pt2vhf_aprs/aprs_service.py")
    assert "def queue_local_ack(" in tnc
    assert 'info = f":{destination:<9}:ack{clean_id}"' in tnc
    assert "handle_duplicate_rf_message" in tnc
    assert "def send_rf_ack(" in service
    assert "def handle_duplicate_rf_message(" in service
