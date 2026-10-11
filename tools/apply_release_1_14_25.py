from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.14.25"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != VERSION:
    raise SystemExit(f"VERSION must be {VERSION}")
if f'__version__ = "{VERSION}"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit(f"package version must be {VERSION}")

app = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "function translatedPatternText(",
    "translatedPatternText(pt, state.language)",
    "characterData: true",
    "attributeFilter: ['placeholder', 'title', 'aria-label']",
    "sourceTextFromCurrentLocale(",
):
    if marker not in app:
        raise SystemExit(f"v1.14.25 i18n marker missing: {marker}")

runtime = read("pt2vhf_aprs/static/js/i18n_runtime.js")
for marker in ("PT2VHF_I18N_RUNTIME_BEGIN", "PT2VHF_I18N_RUNTIME_END", "window.PT2VHF_I18N"):
    if marker not in runtime:
        raise SystemExit(f"v1.14.25 runtime catalog marker missing: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
if html.find("js/i18n_runtime.js") < 0 or html.find("js/i18n_runtime.js") > html.find("js/app.js"):
    raise SystemExit("i18n_runtime.js must load before app.js")

subprocess.run(
    [sys.executable, str(ROOT / "tools" / "i18n_audit.py"), "--strict"],
    cwd=ROOT,
    check=True,
)

tests = read("tests/test_v1425_release.py")
for marker in (
    "test_v1425_all_locales_have_complete_catalog_coverage",
    "test_v1425_non_english_locales_never_fall_back_to_english",
    "test_v1425_dynamic_dom_mutations_are_translated",
    "test_v1425_parameterized_messages_are_supported",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.25 regression missing: {marker}")

if "## Implementado na v1.14.25 — Auditoria integral de traduções" not in read("BACKLOG.md"):
    raise SystemExit("implemented backlog marker missing")

print("v1.14.25 validation OK")
