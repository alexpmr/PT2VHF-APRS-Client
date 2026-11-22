"""v2.0.3 (relato PU2MUS, tela 1366x768): janela, cabeçalho e Auto-resposta."""
from pathlib import Path
from types import SimpleNamespace

from pt2vhf_aprs import window_size

ROOT = Path(__file__).resolve().parents[1]


def test_window_fits_1366x768_and_opens_maximized():
    g = window_size.window_geometry((1366, 768))
    assert g["width"] <= 1366 - 40 and g["height"] <= 768 - 100
    assert g["min_size"][0] <= g["width"] and g["min_size"][1] <= g["height"]
    assert g["maximized"] is True


def test_window_large_screen_keeps_default_size():
    g = window_size.window_geometry((1920, 1080))
    assert (g["width"], g["height"], g["maximized"]) == (1400, 850, False)


def test_window_without_screen_info_uses_default():
    assert window_size.window_geometry(None)["width"] == 1400
    assert window_size.primary_screen_size(SimpleNamespace(screens=[SimpleNamespace(width=1280, height=720)])) == (1280, 720)
    assert window_size.primary_screen_size(object()) is None


def test_desktop_shells_use_window_size():
    for name in ("windows_app.py", "linux_app.py", "macos_app.py"):
        assert "window_size.create_window_kwargs(webview)" in (ROOT / name).read_text(encoding="utf-8")


def test_header_compact_and_auto_reply_badge():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
    js = (ROOT / "pt2vhf_aprs/static/js/header_status.js").read_text(encoding="utf-8")
    assert 'id="autoReplyHeaderStatus"' in html and "Auto-Resposta ligada" in html
    assert "js/header_status.js" in html
    assert ".version-status:not(.update) { display: none; }" in css
    assert "@media (max-width: 1500px) and (min-width: 761px)" in css
    assert "auto_reply_enabled" in js and "pt2vhf:config-saved" in js
