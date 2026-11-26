from __future__ import annotations

from pathlib import Path

from pt2vhf_aprs import updater
from i18n_catalogs import LOCALES, all_text as i18n_all_text, catalog as i18n_catalog


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1426_win7_regression_is_not_reintroduced():
    launcher = read("windows_legacy_app.py")
    requirements = read("requirements-windows7.txt")
    spec = read("windows/PT2VHF_APRS_Client_Win7_Legacy.spec")
    windows_app = read("windows_app.py")
    assert 'PT2VHF_WIN7_LEGACY"] = "1"' in launcher
    assert 'sys.argv.append("--browser")' not in launcher
    assert "pywebview" not in requirements.lower()
    assert "pythonnet" not in requirements.lower()
    assert 'excludes=["webview", "clr", "pythonnet"]' in spec
    assert "_run_legacy_app_shell" in windows_app
    assert "--app=" in windows_app


def test_v1426_legacy_updater_assets_and_portable_in_place(monkeypatch):
    monkeypatch.setattr(updater, "_machine", lambda: "x86_64")
    monkeypatch.setattr(updater, "current_update_mode", lambda: "windows-legacy-portable")
    assert updater.desired_asset_name("1.14.26") == "PT2VHF_APRS_Client_Win7_Legacy_Portable_x64_v1.14.26.exe"
    monkeypatch.setattr(updater, "current_update_mode", lambda: "windows-legacy-installer")
    assert updater.desired_asset_name("1.14.26") == "PT2VHF_APRS_Client_Setup_Win7_Legacy_x64_v1.14.26.exe"
    source = read("pt2vhf_aprs/updater.py")
    assert 'mode in {"windows-legacy-portable", "windows-legacy-installer"}' in source
    assert "destination = current" in source


def test_v1426_web_lan_status_remains_available():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    assert 'id="webAccessStatus"' in html
    assert 'id="webAccessUrl"' in html
    assert "function updateWebAccessStatus" in js
    assert "localInfo.share_url" in js


def test_v1426_lan_diagnostics_and_firewall_are_explicit():
    web = read("pt2vhf_aprs/web.py")
    module = read("pt2vhf_aprs/lan_access.py")
    html = read("pt2vhf_aprs/templates/index.html")
    assert '/api/local-interface/firewall/allow' in web
    assert "lan_diagnostics(local_info," in web
    assert 'id="lanFirewallButton"' in html
    assert "profile=any" in module
    assert "remoteip=localsubnet" in module
    assert 'ShellExecuteW(' in module
    assert '"runas"' in module
    assert '_firewall_script' in module
    assert "UPnP" not in module


def test_v1426_lan_ip_detection_rejects_loopback_and_link_local():
    source = read("pt2vhf_aprs/local_server.py")
    assert "addr.is_loopback" in source
    assert "addr.is_unspecified" in source
    assert "addr.is_link_local" in source
    assert "is_private" in source


def test_v1426_i18n_patch_covers_all_extra_locales():
    for locale in ("es", "fr", "de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN"):
        assert "Autorizar no Firewall do Windows" in i18n_catalog(locale)
        assert "Abrir endereço LAN no navegador padrão" in i18n_catalog(locale)


def test_v1426_release_metadata():
    assert tuple(map(int, read("VERSION").strip().split("."))) >= (1, 14, 26)
    assert '"1.14.26": {' in read("pt2vhf_aprs/version_notes.py")
    assert "## 1.14.26 - 2026-10-11" in read("CHANGELOG.md")
    assert '"1.14.26": {' in read("pt2vhf_aprs/version_notes.py")
    assert not any(line.startswith("## Novo —") for line in read("BACKLOG.md").splitlines())
