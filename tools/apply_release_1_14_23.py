from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.14.23"
LOCALES = {
    "de-DE": "i18n_de.js",
    "it-IT": "i18n_it.js",
    "ja-JP": "i18n_ja.js",
    "pl-PL": "i18n_pl.js",
    "nl-NL": "i18n_nl.js",
    "zh-CN": "i18n_zh.js",
}


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != VERSION:
    raise SystemExit(f"VERSION must be {VERSION}")
if f'__version__ = "{VERSION}"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit(f"package version must be {VERSION}")

html = read("pt2vhf_aprs/templates/index.html")
app = read("pt2vhf_aprs/static/js/app.js")
database = read("pt2vhf_aprs/database.py")
css = read("pt2vhf_aprs/static/css/app.css")

for locale, filename in LOCALES.items():
    if f'data-language="{locale}"' not in html:
        raise SystemExit(f"language quick option missing: {locale}")
    if f'<option value="{locale}">' not in html:
        raise SystemExit(f"language config option missing: {locale}")
    if f"js/{filename}" not in html:
        raise SystemExit(f"language script missing from template: {filename}")
    pack_path = ROOT / "pt2vhf_aprs" / "static" / "js" / filename
    if not pack_path.exists():
        raise SystemExit(f"language pack file missing: {filename}")
    pack = pack_path.read_text(encoding="utf-8")
    start = pack.find("const values = [")
    end = pack.find("];", start + 1)
    values = re.findall(r'^"((?:[^"\\]|\\.)*)",?\s*$', pack[start:end], re.M)
    if len(values) != 483:
        raise SystemExit(f"{locale} catalog must contain 483 entries; got {len(values)}")
    if f"window.PT2VHF_I18N['{locale}']" not in pack:
        raise SystemExit(f"locale marker missing from {filename}")

for marker in (
    "SUPPORTED_LANGUAGES",
    "'de-DE', 'it-IT', 'ja-JP', 'pl-PL', 'nl-NL', 'zh-CN'",
    "topologyLoadQueued: false",
    "state.topologyLoadQueued = true",
    "synthetic_route_edge: true",
    "const renderEdges = [...edges];",
):
    if marker not in app:
        raise SystemExit(f"v1.14.23 app marker missing: {marker}")

if '{"pt-BR", "en", "es", "fr", "de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN"}' not in database:
    raise SystemExit("database does not accept all ten languages")

for marker in (
    "body.analysis-page-active",
    "#tab-analysis.active",
    "overflow: visible !important;",
    "overflow-y: visible !important;",
):
    if marker not in css:
        raise SystemExit(f"statistics single-scroll marker missing: {marker}")

audit = read("tools/i18n_audit.py")
for marker in ("EXTENDED_LANGUAGE_PACKS", "extended_language_pack_errors", "catalog_size_mismatch"):
    if marker not in audit:
        raise SystemExit(f"i18n audit marker missing: {marker}")

tests = read("tests/test_v1423_release.py")
for marker in (
    "test_v1423_version_and_language_catalogs",
    "test_v1423_database_accepts_every_supported_language",
    "test_v1423_statistics_use_window_scroll_only",
    "test_v1423_route_edges_are_authoritative_for_map_rendering",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.23 regression missing: {marker}")

version_info_path = ROOT / "windows" / "version_info.txt"
version_info = version_info_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20", "1.14.21", "1.14.22"):
    version_info = version_info.replace(old, VERSION)
for old_tuple in (
    "(1, 14, 18, 0)", "(1, 14, 19, 0)", "(1, 14, 20, 0)",
    "(1, 14, 21, 0)", "(1, 14, 22, 0)",
):
    version_info = version_info.replace(old_tuple, "(1, 14, 23, 0)")
version_info_path.write_text(version_info, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20", "1.14.21", "1.14.22"):
    readme = readme.replace(old, VERSION)
readme_path.write_text(readme, encoding="utf-8")

backlog = read("BACKLOG.md")
for heading in (
    "## Implementado na v1.14.23 — Idiomas:",
    "## Implementado na v1.14.23 — Análise de rota RF:",
    "## Implementado na v1.14.23 — Estatísticas:",
):
    if heading not in backlog:
        raise SystemExit(f"implemented backlog marker missing: {heading}")

print("v1.14.23 validation OK")
