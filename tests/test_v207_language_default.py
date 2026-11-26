"""v2.0.7: no exterior o app não pode abrir em português.

Regra (Alex, 26/11/2026): idioma do SO quando o app tem esse idioma; inglês quando não tem.
"""
from pathlib import Path

from pt2vhf_aprs import native_text
from pt2vhf_aprs import os_language as ol

ROOT = Path(__file__).resolve().parents[1]


def _system_language_with(monkeypatch, candidates):
    monkeypatch.setattr(ol, "_candidates", lambda: candidates)
    ol.system_language.cache_clear()
    try:
        return ol.system_language()
    finally:
        ol.system_language.cache_clear()


def test_unsupported_os_language_is_english_even_if_later_candidate_is_portuguese(monkeypatch):
    # Windows em russo com formato regional do Brasil: vale a interface (russo) → inglês.
    assert _system_language_with(monkeypatch, ["ru-RU", "Portuguese_Brazil"]) == "en"
    assert _system_language_with(monkeypatch, ["es-419", "pt_BR"]) == "es"
    assert _system_language_with(monkeypatch, ["C", "C.UTF-8", "de_DE.UTF-8"]) == "de-DE"
    assert _system_language_with(monkeypatch, []) == "en"


def test_windows_bcp47_names_map():
    for tag, expected in {"es-419": "es", "de-CH": "de-DE", "en-IN": "en", "fr-CA": "fr",
                          "zh-Hans-CN": "zh-CN", "pt-PT": "pt-BR", "sv-SE": None}.items():
        assert ol.map_language(tag) == expected, tag


def test_windows_detection_uses_lcid_to_locale_name():
    src = (ROOT / "pt2vhf_aprs/os_language.py").read_text(encoding="utf-8")
    assert "LCIDToLocaleName" in src


def test_save_without_language_does_not_default_to_portuguese(tmp_path, monkeypatch):
    from pt2vhf_aprs import database as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "lang.db")
    monkeypatch.setattr(ol, "system_language", lambda: "pl-PL")
    db.init_db()
    db.save_config({"beacon_minutes": 20})
    cfg = db.get_config()
    assert cfg["language"] == "pl-PL" and int(cfg["language_user_set"]) == 0


def test_index_html_ships_the_app_language(tmp_path, monkeypatch):
    from pt2vhf_aprs import database as db
    from pt2vhf_aprs.web import create_app
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "web.db")
    monkeypatch.setattr(ol, "system_language", lambda: "de-DE")
    db.init_db()
    html = create_app().test_client().get("/").get_data(as_text=True)
    assert '<html lang="de" data-app-language="de-DE">' in html


def test_frontend_fallbacks_are_english():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "SUPPORTED_LANGUAGES.includes(normalized) ? normalized : 'en'" in js
    assert "document.documentElement.dataset.appLanguage" in js
    for name in ("config_tabs.js", "planning.js", "ssid_help.js", "v110.js", "v111.js", "v142.js",
                 "v1818.js", "v190.js", "tnc.js", "help_i18n.js"):
        text = (ROOT / "pt2vhf_aprs/static/js" / name).read_text(encoding="utf-8")
        assert "||'pt-BR')" not in text.replace(" ", ""), name


def test_native_texts_follow_language_with_english_fallback():
    assert native_text.text("tray_exit", "de-DE") == "Beenden"
    assert native_text.text("confirm_exit", "pt-BR").startswith("Deseja")
    assert native_text.text("port_failed", "ja-JP").startswith("Could not")
    assert native_text.text("tray_open", "sv-SE") == "Open PT2VHF APRS Client"
    for entry in native_text.TEXTS.values():
        assert "en" in entry and "pt-BR" in entry
    shell = (ROOT / "windows_app.py").read_text(encoding="utf-8")
    assert "Deseja realmente sair" not in shell and 'Item("Sair"' not in shell


def test_installers_default_to_english():
    for name in ("installer.iss", "installer_arm64.iss", "installer_win7_legacy.iss"):
        text = (ROOT / "windows" / name).read_text(encoding="utf-8-sig")
        langs = text[text.index("[Languages]"):text.index("[CustomMessages]")]
        names = [line.split('"')[1] for line in langs.splitlines() if line.startswith("Name:")]
        assert names[0] == "english", name
        assert "brazilianportuguese" in names and "spanish" in names and "german" in names
        assert "ShowLanguageDialog=auto" in text
        head = text[:text.index("[Code]")]
        assert '"Criar atalho' not in head and '"Executar ' not in head and "{cm:RunApp," in head
