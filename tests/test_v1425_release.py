from __future__ import annotations

from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs import local_server
from pt2vhf_aprs import updater


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1425_header_is_compact_and_theme_lives_in_settings():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    assert 'id="headerSendBeaconButton"' in html
    assert 'class="btn secondary header-beacon-button"' in html  # v1.15.2: botão com texto
    assert '>Enviar Beacon</button>' in html
    assert 'id="themeQuickToggle"' not in html
    assert 'name="app_theme"' in html
    assert "function applyAppearancePreferences" in js
    assert "function previewAppearanceFromForm" in js


def test_v1425_lan_access_is_opt_in_and_runtime_has_safe_urls(monkeypatch):
    assert db.DEFAULT_CONFIG["web_lan_enabled"] == 1
    monkeypatch.setattr(local_server, "detect_lan_ipv4", lambda: "192.168.50.23")
    handle = local_server.LocalServerHandle(
        server=object(),
        server_kind="test",
        host="0.0.0.0",
        port=8087,
        start_port=8080,
    )
    assert handle.local_host == "127.0.0.1"
    assert handle.url == "http://127.0.0.1:8087"
    assert handle.lan_host == "192.168.50.23"
    assert handle.share_url == "http://192.168.50.23:8087"
    assert handle.scope == "lan"


def test_v1425_header_shows_actual_web_address():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    assert 'id="webAccessStatus"' in html
    assert 'id="webAccessUrl"' in html
    assert 'name="web_lan_enabled"' in html
    assert "function updateWebAccessStatus" in js
    assert "localInfo.share_url" in js


def test_v1425_non_english_languages_do_not_silently_fall_back_to_english():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "return EXTRA_I18N[state.language]?.[pt] || pt;" in js
    assert ": EXTRA_I18N[state.language]?.[trimmed];" in js
    assert "domTranslator.translate(root);" in js
    assert "EXTRA_I18N[state.language]?.[pt] || en" not in js
    assert "EXTRA_I18N[state.language]?.[trimmed] || EN_TEXT" not in js
    assert "i18n_v1425.js" in read("pt2vhf_aprs/templates/index.html")


def test_v1425_all_new_lan_strings_have_locale_patch_entries():
    patch = read("pt2vhf_aprs/static/js/i18n_v1425.js")
    for locale in ("es", "fr", "de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN"):
        assert f"'{locale}':" in patch or f"{locale}:" in patch
    for source in (
        "Web local:",
        "Web LAN:",
        "Copiar endereço Web",
        "Permitir acesso Web pela rede local (LAN)",
        "Mensagens agendadas e melhorias de usabilidade",
    ):
        assert source in patch


def test_v1425_py2fdg_is_credited():
    html = read("pt2vhf_aprs/templates/index.html")
    assert "<strong>PY2FDG</strong>" in html
    assert "<span>Fábio</span>" in html
    assert "Mensagens agendadas e melhorias de usabilidade" in html


def test_v1425_win7_legacy_assets_are_isolated(monkeypatch):
    monkeypatch.setattr(updater, "_machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "current_update_mode", lambda: "windows-legacy-portable")
    assert updater.desired_asset_name("1.14.25") == "PT2VHF_APRS_Client_Win7_Legacy_Portable_x64_v1.14.25.exe"
    monkeypatch.setattr(updater, "current_update_mode", lambda: "windows-legacy-installer")
    assert updater.desired_asset_name("1.14.25") == "PT2VHF_APRS_Client_Setup_Win7_Legacy_x64_v1.14.25.exe"


def test_v1425_win7_legacy_build_files_and_pins_are_present():
    requirements = read("requirements-windows7.txt")
    launcher = read("windows_legacy_app.py")
    spec = read("windows/PT2VHF_APRS_Client_Win7_Legacy.spec")
    installer = read("windows/installer_win7_legacy.iss")
    workflow = read(".github/workflows/build-production-current.yml")

    assert "Flask==3.0.3" in requirements
    assert "pyinstaller==5.13.2" in requirements
    assert "Pillow==10.4.0" in requirements
    assert "psutil==6.1.1" in requirements
    assert "pywebview" not in requirements.lower()
    assert "pythonnet" not in requirements.lower()
    assert 'PT2VHF_WIN7_LEGACY"] = "1"' in launcher
    assert 'excludes=["webview", "clr", "pythonnet"]' in spec
    assert "MinVersion=6.1sp1" in installer
    assert "windows-win7-legacy:" in workflow
    assert "python-version: '3.8.10'" in workflow


def test_v1425_release_metadata_is_consistent():
    assert tuple(map(int, read("VERSION").strip().split("."))) >= (1, 14, 25)
    assert "## 1.14.25 - 2026-10-11" in read("CHANGELOG.md")
    assert '"1.14.25": {' in read("pt2vhf_aprs/version_notes.py")
    assert "PT2VHF_APRS_Client_Setup_Win7_Legacy_x64_v{version}.exe" in read("tools/release_notes.py")
    assert "Windows 7 SP1 x64" in read("docs/WINDOWS7.md")
