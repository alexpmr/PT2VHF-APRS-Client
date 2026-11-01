"""Language switch labels/flags must match the visual reference (issue #157)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
APP = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
AUDIT = (ROOT / "tools/i18n_audit.py").read_text(encoding="utf-8")


def test_six_reference_languages_and_exact_flags():
    for lang, name, flag in (
        ("pt-BR", "Português (Brasil)", "flag_br.svg"),
        ("en", "English", "flag_uk.svg"),
        ("es", "Español", "flag_spain.svg"),
        ("fr", "Français", "flag_france.svg"),
        ("de-DE", "Deutsch", "flag_germany.svg"),
        ("it-IT", "Italiano", "flag_italy.svg"),
    ):
        assert f'data-language="{lang}"' in HTML
        assert f'<option value="{lang}">{name}</option>' in HTML
        assert flag in HTML
    assert 'flag_england.svg' not in HTML
    assert "flag_england.svg" not in APP
    assert "'pt-BR': { label: 'Português (Brasil)'" in APP
    assert "en: { label: 'English', flag: '/static/img/flag_uk.svg'" in APP


def test_uk_flag_is_union_jack_not_st_georges_cross():
    flag = (ROOT / "pt2vhf_aprs/static/img/flag_uk.svg").read_text(encoding="utf-8")
    assert 'viewBox="0 0 60 36"' in flag
    assert 'fill="#012169"' in flag
    assert 'M0 0L60 36M60 0L0 36' in flag
    assert 'stroke="#C8102E"' in flag


def test_translation_audit_reports_real_literal_coverage():
    assert "def _main_ui_literal_keys()" in AUDIT
    assert '"base_dictionary_missing_ui_count"' in AUDIT
    assert '"note_on_core_ui_coverage"' in AUDIT


def test_additional_existing_languages_not_removed():
    for language in ("ja-JP", "pl-PL", "nl-NL", "zh-CN"):
        assert f'data-language="{language}"' in HTML
