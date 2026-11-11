"""v1.15.9: cancelar reenvio/copiar mensagens (PU2MUS), Kenwood TS-2000 e Ajuda em inglês."""
import re
from pathlib import Path

from pt2vhf_aprs import aprs_service, database as db, tnc_service

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_cancel_stops_retries_for_all_pending_parts(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "msg.db")
    db.init_db()
    ids = [db.add_message("out", "PT2VHF-15", "PY2ABC", f"parte {i}", msg_id=f"1{i}", status="Enviada") for i in range(2)]
    ack = db.add_message("out", "PT2VHF-15", "PY2ABC", "confirmada", msg_id="19", status="ACK")
    with db.connection() as conn:
        conn.execute("UPDATE messages SET message_group_id='G1', timestamp='2000-01-01T00:00:00+00:00' WHERE id IN (?,?,?)", (*ids, ack))
    assert len(db.list_retry_candidates(60, 2)) == 2
    assert db.cancel_message_retries(ids[0]) == 2
    assert db.list_retry_candidates(60, 2) == []
    assert db.get_message(ack)["status"] == "ACK"
    assert db.cancel_message_retries(ids[0]) == 0          # nada mais pendente


def test_automatic_retry_skips_cancelled_but_manual_is_allowed(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "auto.db")
    db.init_db()
    row = db.add_message("out", "PT2VHF-15", "PY2ABC", "texto", msg_id="21", status="Cancelada")
    result = aprs_service.APRSService().retry_message(row, automatic=True)
    assert result["skipped"] and "cancelado" in result["reason"]


def test_message_menu_attempts_and_selection_guard_in_ui():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "messagesTable tbody')?.addEventListener('contextmenu', messageMenuHandler)" in js
    assert "conversationMessages')?.addEventListener('contextmenu', messageMenuHandler)" in js
    for action in ("copy-text", "copy-call", "cancel", "retry"):
        assert f"'{action}'" in js
    assert "if (messageInteractionActive()) { state.messagesRenderPending = true; return; }" in js
    assert "${ui('tentativa', 'attempt')} ${used + 1}/${max + 1}" in js


class FakeSerial:
    def __init__(self):
        self.written = b""
        self.closed = False
    def reset_input_buffer(self): pass
    def write(self, data): self.written += data
    def flush(self): pass
    def read(self, n): return b"cmd:KISS ON\r\n"
    def close(self): self.closed = True


def test_kenwood_kiss_on_and_off(monkeypatch):
    fake = FakeSerial()
    monkeypatch.setattr(tnc_service, "open_serial_port", lambda cfg, **kw: fake)
    monkeypatch.setattr(tnc_service, "record_decision", lambda *a, **k: None)
    cfg = {"serial_port": "COM6", "serial_baud": 9600}
    result = tnc_service.kenwood_tnc_kiss(cfg, True, wait=0.05)
    assert b"KISS ON\rRESTART\r" in fake.written and fake.closed and "KISS ON" in result["reply"]
    fake.written = b""
    tnc_service.kenwood_tnc_kiss(cfg, False, wait=0.05)
    assert fake.written == b"\xc0\xff\xc0"


def test_ts2000_profile_is_accepted():
    cfg = tnc_service.normalize_tnc_config({"transport": "serial", "serial_port": "COM6", "device_profile": "kenwood_ts2000"}, strict=False)
    assert cfg["device_profile"] == "kenwood_ts2000"


def test_help_has_english_for_every_block():
    html = read("pt2vhf_aprs/templates/index.html")
    help_js = read("pt2vhf_aprs/static/js/help_i18n.js")
    keys = set(re.findall(r'data-help-i18n="(h\d+)"', html))
    assert len(keys) >= 60
    for key in keys:
        assert re.search(rf"\n    {key}: '", help_js), key
    assert "continua obrigatória" not in html
