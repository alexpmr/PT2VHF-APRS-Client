from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.1":
    raise SystemExit(f"v1.8.1 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.1"'],
    "pt2vhf_aprs/static/js/app.js": [
        "tile-cyclosm.openstreetmap.fr/cyclosm",
        "tile.openstreetmap.fr/hot",
        "tile.openstreetmap.de/{z}/{x}/{y}.png",
        "tile.memomaps.de/tilegen",
        "function applyBaseMap",
        "layer.on('tileerror'",
        "/api/diagnostics/map-provider-error",
        "pt2vhf-language-changed",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'value="cyclosm"',
        'value="humanitarian"',
        'value="osmde"',
        'value="opnv"',
        'id="elevationToggle"',
    ],
    "pt2vhf_aprs/static/js/tnc.js": [
        "const TNC_I18N",
        "translateTncStatic",
        "localizeBackendMessage",
        "Refresh ports",
        "Actualizar puertos",
        "Actualiser les ports",
    ],
    "pt2vhf_aprs/web.py": [
        '/api/diagnostics/map-provider-error',
        'map_provider_error',
    ],
    "tests/test_v181_maps_i18n.py": [
        "test_v181_keyless_map_bases_and_hillshade_removal",
        "test_v181_tnc_rf_translations_follow_app_language",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.1"'],
    "CHANGELOG.md": ["## 1.8.1 - 2026-10-01"],
    "README.md": ["# PT2VHF APRS Client - v1.8.1", "## Novidades da v1.8.1"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.1 validation failed: {needle!r} missing from {rel}")

for rel in (
    "pt2vhf_aprs/static/js/app.js",
    "pt2vhf_aprs/templates/index.html",
    "pt2vhf_aprs/static/css/app.css",
):
    text = (ROOT / rel).read_text(encoding="utf-8")
    for obsolete in ("pt2vhfHillshadePane", "World_Hillshade/MapServer/tile", "hillshadeToggle", "basemaps.cartocdn.com"):
        if obsolete in text:
            raise SystemExit(f"v1.8.1 validation failed: obsolete {obsolete!r} remains in {rel}")

print("v1.8.1 maps/i18n production validation OK")
