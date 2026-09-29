from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.18":
    raise SystemExit(f"v1.7.18 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.18"'],
    "pt2vhf_aprs/static/js/app.js": [
        "function syncMapViewTreeCheckboxes()",
        "own.checked = some;",
        "own.indeterminate = some && !all;",
        "setMapViewState(own.dataset.mapStateKey, some)",
        "setMapViewFilter(own.dataset.mapFilterKey, some)",
        "function objectMatchesViewFilter(object)",
        "function stationMatchesViewFilter(station)",
    ],
    "tests/test_core.py": [
        "test_v1718_partial_tree_selection_keeps_parent_enabled",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.7.18"'],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.18 validation failed: {needle!r} missing from {rel}")

js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
start = js.index("function syncMapViewTreeCheckboxes()")
end = js.index("async function refreshMapFromViewTree()", start)
block = js[start:end]
required = (
    "const some = children.some(input => input.checked || input.indeterminate);",
    "own.checked = some;",
    "own.indeterminate = some && !all;",
)
for needle in required:
    if needle not in block:
        raise SystemExit(f"v1.7.18 validation failed: partial selection logic missing {needle!r}")

print("v1.7.18 Windows x64 portable validation OK")
