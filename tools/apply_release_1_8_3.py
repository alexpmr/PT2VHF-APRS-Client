from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.3":
    raise SystemExit(f"v1.8.3 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.3"'],
    "pt2vhf_aprs/database.py": [
        "APRS_APPLICATION_CLASSES",
        "APRS_DEVICE_CLASSES",
        "def _aprs_client_category(",
        '"category": category',
        '"category_counts"',
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="clientStatsShowApps"',
        'id="clientStatsShowDevices"',
        'id="clientStatsShowUnknown"',
        'id="mapViewSelectAllButton"',
        'id="mapViewClearAllButton"',
        "Mostrar aplicativos APRS",
        "Mostrar dispositivos",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "pt2vhf_stats_show_apps",
        "pt2vhf_stats_show_devices",
        "pt2vhf_stats_show_unknown",
        "function clientStatsCategoryVisible(",
        "const visibleTotal = candidates.reduce",
        "Number(item.stations || 0) / visibleTotal",
        "function setAllMapView(enabled)",
        "setAllMapView(true)",
        "setAllMapView(false)",
    ],
    "pt2vhf_aprs/static/js/i18n_extra.js": [
        "Mostrar aplicaciones APRS",
        "Afficher les applications APRS",
        "Seleccionar todo",
        "Tout sélectionner",
    ],
    "tests/test_v183_stats_mapview.py": [
        "test_v183_aprs_application_device_classification",
        "test_v183_statistics_filter_controls_and_visible_percent_logic",
        "test_v183_map_view_select_all_and_clear_all",
        "test_v183_translations_cover_new_controls",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.3"'],
    "CHANGELOG.md": ["## 1.8.3 - 2026-10-01"],
    "README.md": ["# PT2VHF APRS Client - v1.8.3", "## Novidades da v1.8.3"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.3 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
if 'id="mapViewAllButton"' in html or "$('#mapViewAllButton')" in js:
    raise SystemExit("v1.8.3 validation failed: obsolete Map → Ver Tudo control remains active")

from pt2vhf_aprs import database as db

expected = {
    "APZVHF": "application",
    "APDW18": "application",
    "APDR16": "application",
    "API510": "device",
    "APK004": "device",
    "APT3A1": "device",
}
for tocall, category in expected.items():
    resolved = db.resolve_aprs_device_id(tocall)
    actual = db._aprs_client_category(resolved)
    if actual != category:
        raise SystemExit(
            f"v1.8.3 validation failed: {tocall} expected {category}, got {actual}"
        )

if db._aprs_client_category(db.resolve_aprs_device_id("ZZZZZZ")) != "unknown":
    raise SystemExit("v1.8.3 validation failed: unknown TOCALL must remain undetermined")

print("v1.8.3 APRS statistics / Map View production validation OK")
