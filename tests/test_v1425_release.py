from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def run_audit() -> dict:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "i18n_audit.py"), "--strict"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_v1425_version_and_release_markers():
    assert read("VERSION").strip() == "1.14.25"
    assert '__version__ = "1.14.25"' in read("pt2vhf_aprs/__init__.py")
    assert '"1.14.25":' in read("pt2vhf_aprs/version_notes.py")
    assert "## 1.14.25 — 2026-10-11" in read("CHANGELOG.md")


def test_v1425_all_locales_have_complete_catalog_coverage():
    audit = run_audit()
    assert audit["runtime_catalog_errors"] == []
    assert audit["extended_language_pack_errors"] == []
    assert audit["missing_es_keys"] == []
    assert audit["missing_fr_keys"] == []
    assert all(value == 100.0 for value in audit["coverage_percent_by_locale"].values())
    assert all(not missing for missing in audit["missing_catalog_keys_by_locale"].values())


def test_v1425_non_english_locales_never_fall_back_to_english():
    app = read("pt2vhf_aprs/static/js/app.js")
    assert "EXTRA_I18N[state.language]?.[pt] || en" not in app
    assert "EXTRA_I18N[state.language]?.[trimmed] || EN_TEXT" not in app
    assert "EXTRA_I18N[state.language]?.[original] || EN_TEXT" not in app
    assert "translatedPatternText(pt, state.language)" in app


def test_v1425_dynamic_dom_mutations_are_translated():
    app = read("pt2vhf_aprs/static/js/app.js")
    assert "characterData: true" in app
    assert "attributes: true" in app
    assert "attributeFilter: ['placeholder', 'title', 'aria-label']" in app
    assert "sourceTextFromCurrentLocale(node.nodeValue)" in app
    assert "languageObserver.disconnect()" in app


def test_v1425_parameterized_messages_are_supported():
    app = read("pt2vhf_aprs/static/js/app.js")
    runtime = read("pt2vhf_aprs/static/js/i18n_runtime.js")
    assert "function translatedPatternText(" in app
    assert "__ARG0__" in app
    assert "__ARG0__" in runtime


def test_v1425_runtime_catalog_loads_before_app():
    html = read("pt2vhf_aprs/templates/index.html")
    assert html.index("js/i18n_runtime.js") < html.index("js/app.js")
