from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pt2vhf_aprs import database as db

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.19":
    raise SystemExit(f"v1.7.19 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.19"'],
    "pt2vhf_aprs/database.py": [
        "def aprs_object_map_metadata",
        "def list_rf_received_by",
        '"station_rankings": station_rankings',
        "map_role",
        "excluded_set",
    ],
    "pt2vhf_aprs/web.py": [
        '@app.get("/api/stations/<callsign>/rf-heard")',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "renderStationStatsTable(data.station_rankings || [])",
        "data-station-stats-sort",
        "Estações recebidas por RF",
        "loadStationRfHeard(station.callsign)",
        "object:family:",
        "pt2vhf_map_view_filters_v2",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".station-ranking-group",
        ".station-ranking-table-wrap",
        ".station-rf-heard-section",
    ],
    "tests/test_core.py": [
        "test_v1719_objects_use_object_semantics_not_publisher_device",
        "test_v1719_unified_station_stats_exclude_digis_and_igates",
        "test_v1719_rf_heard_list_uses_observed_rf_edges",
    ],
    "CHANGELOG.md": ["## v1.7.19 - 2026-09-29"],
    "README.md": ["# PT2VHF APRS Client - v1.7.19"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.19"'],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.19 validation failed: {needle!r} missing from {rel}")

generic = db.aprs_object_map_metadata(
    "LOCALOBJ", "ponto de interesse", "/", ">", "object"
)
if generic.get("map_family_label") != "Outros objetos":
    raise SystemExit(f"v1.7.19 validation failed: generic object family={generic!r}")
if generic.get("device_tocall"):
    raise SystemExit(f"v1.7.19 validation failed: object inherited publisher TOCALL={generic!r}")

print("v1.7.19 production validation OK")
