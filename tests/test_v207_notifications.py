"""v2.0.7: aviso do sistema para mensagem recebida."""
from pathlib import Path

from pt2vhf_aprs import desktop_notify, database as db

ROOT = Path(__file__).resolve().parent.parent


def test_notify_uses_platform_method(monkeypatch):
    calls = []
    monkeypatch.setattr(desktop_notify, "_last_sent", 0.0)
    monkeypatch.setattr(desktop_notify.platform, "system", lambda: "Linux")
    monkeypatch.setattr(desktop_notify.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(desktop_notify, "_run", lambda cmd: calls.append(cmd) or True)
    out = desktop_notify.notify("Mensagem de PY2ABC", "Olá\nmundo")
    assert out == {"ok": True, "method": "notify-send"}
    assert calls[0][-2:] == ["Mensagem de PY2ABC", "Olá mundo"]
    assert desktop_notify.notify("x", "y")["reason"] == "rate_limited"


def test_windows_uses_tray(monkeypatch):
    got = []
    monkeypatch.setattr(desktop_notify, "_last_sent", 0.0)
    monkeypatch.setattr(desktop_notify.platform, "system", lambda: "Windows")
    desktop_notify.register_tray_notifier(lambda message, title: got.append((message, title)))
    try:
        assert desktop_notify.notify("T", "B")["method"] == "tray"
        assert got == [("B", "T")]
    finally:
        desktop_notify.register_tray_notifier(None)


def test_macos_quotes_text(monkeypatch):
    calls = []
    monkeypatch.setattr(desktop_notify, "_last_sent", 0.0)
    monkeypatch.setattr(desktop_notify.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(desktop_notify.shutil, "which", lambda name: "/usr/bin/osascript")
    monkeypatch.setattr(desktop_notify, "_run", lambda cmd: calls.append(cmd) or True)
    desktop_notify.notify('Diz "oi"', 'a\\b')
    assert calls[0][2] == 'display notification "a\\\\b" with title "Diz \\"oi\\""'


def test_api_local_only_and_respects_setting(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "n.db")
    db.init_db()
    from pt2vhf_aprs.web import create_app
    client = create_app().test_client()
    monkeypatch.setattr(desktop_notify, "notify", lambda title, body: {"ok": True, "method": "test"})
    assert client.post("/api/notify", json={"title": "a"}, environ_base={"REMOTE_ADDR": "10.0.0.5"}).status_code == 403
    assert client.post("/api/notify", json={"title": "a"}).get_json()["ok"]
    db.save_config({"desktop_notifications": False})
    assert client.post("/api/notify", json={"title": "a"}).get_json()["reason"] == "disabled"


def test_ui_hooks():
    app = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    assert "pt2vhf-personal-messages" in app and "pt2vhf-unread-count" in app
    assert 'name="desktop_notifications"' in html and "js/notifications.js" in html
    assert "register_tray_notifier" in (ROOT / "windows_app.py").read_text(encoding="utf-8")
