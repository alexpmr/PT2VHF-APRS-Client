from __future__ import annotations

from pathlib import Path
import re
import tempfile

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _pack_value_count(locale_file: str) -> int:
    text = read("pt2vhf_aprs/static/js/" + locale_file)
    start = text.index("const values = [")
    end = text.index("];", start)
    return len(re.findall(r'^"((?:[^"\\]|\\.)*)",?\s*$', text[start:end], flags=re.M))


def test_v1423_version_and_language_catalogs():
    version_text = read("VERSION").strip()
    version = tuple(int(part) for part in version_text.split("."))
    assert version >= (1, 14, 23)
    assert f'__version__ = "{version_text}"' in read("pt2vhf_aprs/__init__.py")

    html = read("pt2vhf_aprs/templates/index.html")
    app = read("pt2vhf_aprs/static/js/app.js")
    database = read("pt2vhf_aprs/database.py")

    expected = {
        "de-DE": "i18n_de.js",
        "it-IT": "i18n_it.js",
        "ja-JP": "i18n_ja.js",
        "pl-PL": "i18n_pl.js",
        "nl-NL": "i18n_nl.js",
        "zh-CN": "i18n_zh.js",
    }
    for locale, filename in expected.items():
        assert f'data-language="{locale}"' in html
        assert f'<option value="{locale}">' in html
        assert f"js/{filename}" in html
        assert locale in app
        assert locale in database
        assert _pack_value_count(filename) == 483

    assert "統計" in read("pt2vhf_aprs/static/js/i18n_ja.js")
    assert "简体中文" in html
    assert "Simplified Chinese language pack size mismatch" in read("pt2vhf_aprs/static/js/i18n_zh.js")


def test_v1423_database_accepts_every_supported_language():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "languages.db"
            db.init_db()
            for locale in ("pt-BR", "en", "es", "fr", *LOCALES):
                saved = db.save_config({"language": locale})
                assert saved["language"] == locale
    finally:
        db.DB_PATH = original


def test_v1423_statistics_use_window_scroll_only():
    app = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "document.body.classList.toggle('analysis-page-active', tab === 'analysis')" in app
    assert "body.analysis-page-active" in css
    assert "#tab-analysis .analysis-content" in css
    tail = css[css.rfind("/* v1.14.23 - Estatísticas usa exclusivamente"):]
    assert "overflow: visible !important;" in tail
    assert "overflow-y: visible !important;" in tail
    assert "height: auto !important;" in tail


def test_v1423_route_edges_are_authoritative_for_map_rendering():
    app = read("pt2vhf_aprs/static/js/app.js")
    assert "topologyLoadQueued: false" in app
    assert "state.topologyLoadQueued = true" in app
    assert "synthetic_route_edge: true" in app
    assert "const renderEdges = [...edges];" in app
    assert "for (const [pair, routeEdge] of routeEvidenceByPair.entries())" in app
    assert "renderEdges.push({" in app
    assert "setTimeout(() => { void loadTopology(); }, 0);" in app


def test_v1423_i18n_audit_covers_extended_catalogs():
    audit = read("tools/i18n_audit.py")
    for locale in LOCALES:
        assert f'"{locale}"' in audit
    assert "extended_language_pack_errors" in audit
    assert "catalog_size_mismatch" in audit
