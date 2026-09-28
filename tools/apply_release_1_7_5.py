from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
try:
    version_tuple = tuple(int(part) for part in version.split("."))
except ValueError as exc:
    raise SystemExit(f"v1.7.5 validation failed: invalid VERSION={version!r}") from exc
if version_tuple < (1, 7, 5):
    raise SystemExit(f"v1.7.5 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['APP_TOCALL = "APZVHF"'],
    "pt2vhf_aprs/database.py": [
        "def _valid_geo_position",
        "POSITION_ZERO_EPSILON",
        "station_anomalies",
        "rf_relay_distance",
        "def station_problem_stats",
        "def network_improvement_suggestions",
        "def geographic_export_data",
    ],
    "pt2vhf_aprs/web.py": [
        'def _kml_document(',
        '@app.get("/api/export/kml")',
        'application/vnd.google-earth.kml+xml',
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="kmlExportButton"',
        'id="kmlStations" type="checkbox" checked',
        'id="kmlPositions" type="checkbox" checked',
        'id="kmlTracklogs" type="checkbox" checked',
        'id="kmlTopology" type="checkbox" checked',
        'id="conversationSortKey"',
        '>Apagar todas</button>',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "conversationSortKey",
        "data-map-callsign",
        "problem_stations",
        "improvement_suggestions",
        "function exportKml()",
        "position_valid === false",
    ],
    "tests/test_core.py": [
        "test_v175_rejects_zero_and_rf_implausible_positions",
        "test_v175_kml_export_contains_selected_layers",
        "test_v175_ui_has_kml_export_message_sorting_and_stats_navigation",
        "test_v175_invalid_geometry_is_excluded_from_export_and_replay",
    ],
    "README.md": ["PT2VHF APRS Client"],
    "CHANGELOG.md": ["## v1.7.5 - 2026-09-28"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.5"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.5 validation failed: {needle!r} missing from {rel}")

print("v1.7.5 release validation OK")
