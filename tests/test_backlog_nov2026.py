"""Itens do backlog de novembro/2026 resolvidos na versão nova.

- Tirar acentos das mensagens antes de enviar (padrão: ligado).
- Instalador confere o banco existente e conserta se não estiver íntegro (--check-db).
- Sugestões do PU2PYC: e-mail/site do comentário clicáveis, detalhes extras da estação,
  sinal sonoro no ACK e quando o próprio pacote é ouvido repetido por digipeater.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from pt2vhf_aprs import aprs_service, database as db, db_check, tnc_service

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# --- Acentos --------------------------------------------------------------

def test_strip_message_accents():
    f = aprs_service.strip_message_accents
    assert f("Ação às 9h, São Paulo — coração") == "Acao as 9h, Sao Paulo - coracao"
    assert f("Ñandú, Größe, Øre, “aspas” ‘simples’…") == "Nandu, Grosse, Ore, \"aspas\" 'simples'..."
    assert f("PLAIN ascii 123 {}") == "PLAIN ascii 123 {}"
    assert f("") == ""


def test_strip_accents_option_default_on_and_persisted(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "pt2vhf_aprs.db")
    db.init_db()
    assert db.get_config()["strip_message_accents"] == 1
    db.save_config({"strip_message_accents": 0})
    assert db.get_config()["strip_message_accents"] == 0
    db.save_config({"strip_message_accents": 1})
    assert db.get_config()["strip_message_accents"] == 1


def test_queue_message_parts_strips_accents_before_split():
    src = _read("pt2vhf_aprs/aprs_service.py")
    block = src.split("def queue_message_parts", 1)[1].split("def ", 1)[0]
    assert 'cfg.get("strip_message_accents", 1)' in block
    assert block.index("strip_message_accents(text)") < block.index("split_aprs_message_parts(text)")
    assert 'name="strip_message_accents"' in _read("pt2vhf_aprs/templates/index.html")


# --- Banco no instalador ----------------------------------------------------

def test_installer_check_without_database_creates_nothing(tmp_path, monkeypatch):
    path = tmp_path / "pt2vhf_aprs.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    result = db_check.installer_check()
    assert result["exists"] is False and result["action"] == "none"
    assert not path.exists()


def test_installer_check_healthy_database(tmp_path, monkeypatch):
    path = tmp_path / "pt2vhf_aprs.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "LAST_DB_RECOVERY", None)
    db.init_db()
    db.save_config({"callsign": "PY2OK"})
    result = db_check.installer_check()
    assert result["action"] == "ok"
    assert db.get_config()["callsign"] == "PY2OK"


def test_installer_check_recovers_unreadable_database(tmp_path, monkeypatch):
    path = tmp_path / "pt2vhf_aprs.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "LAST_DB_RECOVERY", None)
    db.init_db()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.close()
    with open(path, "r+b") as fh:
        fh.write(b"\xde\xad\xbe\xef" * 32)
    result = db_check.installer_check()
    assert result["action"] == "recovered"
    with sqlite3.connect(path) as check:
        assert check.execute("PRAGMA quick_check").fetchone()[0] == "ok"


def test_installers_run_database_check():
    for rel in ("windows/installer.iss", "windows/installer_arm64.iss", "windows/installer_win7_legacy.iss"):
        text = _read(rel)
        assert 'Parameters: "--check-db"' in text, rel
        assert "runasoriginaluser" in text, rel
    app = _read("windows_app.py")
    assert '"--check-db" in sys.argv[1:]' in app
    assert "db_check.installer_check()" in app


# --- Sugestões do PU2PYC ----------------------------------------------------

def test_station_popup_links_and_extra_details():
    js = _read("pt2vhf_aprs/static/js/app.js")
    assert "function linkifyStationInfo(" in js
    assert "mailto:${value}" in js
    assert "${linkifyStationInfo(s.info || '')}" in js
    assert "${stationExtraDetailsHtml(s)}" in js
    for field in ("device_vendor", "device_model", "device_tocall", "packet_format", "message_capable", "s.raw"):
        assert field in js.split("function stationExtraDetailsHtml", 1)[1].split("function popupHtml", 1)[0], field


def test_sound_options_default_on(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "pt2vhf_aprs.db")
    db.init_db()
    cfg = db.get_config()
    assert cfg["sound_on_message_ack"] == 1
    assert cfg["sound_on_own_digipeat"] == 1
    html = _read("pt2vhf_aprs/templates/index.html")
    assert 'name="sound_on_message_ack"' in html and 'name="sound_on_own_digipeat"' in html


def test_ack_plays_sound_only_for_my_message(monkeypatch):
    played: list[str] = []
    monkeypatch.setattr(aprs_service, "_play_windows_message_sound", lambda kind="message": played.append(kind))
    monkeypatch.setattr(aprs_service.db, "get_config", lambda: {"sound_on_message_ack": 1, "callsign": "PY2ME"})
    monkeypatch.setattr(aprs_service.db, "resolve_ping_ack", lambda *a, **k: None)
    svc = aprs_service.service
    monkeypatch.setattr(aprs_service.db, "mark_message_status", lambda *a, **k: 1)
    svc._handle_message({"from": "PY2YOU", "to": "PY2ME", "text": "ack001"}, "raw")
    assert played == ["ack"]
    monkeypatch.setattr(aprs_service.db, "mark_message_status", lambda *a, **k: 0)
    svc._handle_message({"from": "PY2YOU", "to": "PY2ME", "text": "ack002"}, "raw")
    assert played == ["ack"]


def test_own_packet_digipeated_plays_sound(monkeypatch):
    played: list[str] = []
    monkeypatch.setattr(aprs_service, "_play_windows_message_sound", lambda kind="message": played.append(kind))
    monkeypatch.setattr(tnc_service.db, "get_config", lambda: {"sound_on_own_digipeat": 1})
    svc = tnc_service.service
    monkeypatch.setattr(svc, "_own_call", lambda: "PY2ME-9")
    svc._last_own_digipeat_sound = 0.0
    # Ouvido direto (sem digi): não toca.
    svc._notify_own_digipeat({"source": "PY2ME-9", "path": [{"call": "WIDE1-1", "repeated": False}]})
    assert played == []
    # Outra estação repetida: não toca.
    svc._notify_own_digipeat({"source": "PY2XX", "path": [{"call": "PY2DIG", "repeated": True}]})
    assert played == []
    svc._notify_own_digipeat({"source": "PY2ME-9", "path": [{"call": "PY2DIG", "repeated": True}]})
    assert played == ["digipeat"]
    # Vários digis repetindo o mesmo pacote em sequência: um único aviso.
    svc._notify_own_digipeat({"source": "PY2ME-9", "path": [{"call": "PY2DI2", "repeated": True}]})
    assert played == ["digipeat"]
