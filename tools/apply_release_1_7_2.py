from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
try:
    version_tuple = tuple(int(part) for part in version.split("."))
except ValueError as exc:
    raise SystemExit(f"v1.7.2 validation failed: invalid VERSION={version!r}") from exc
if version_tuple < (1, 7, 2):
    raise SystemExit(f"v1.7.2 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['APP_TOCALL = "APZVHF"'],
    "pt2vhf_aprs/database.py": [
        "def client_version_stats",
        '"identifiers": identifiers',
        '"is_own_client": is_own',
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="mapContextBar"',
        'class="map-context-controls"',
        'id="mapHistoryToggle"',
        'id="stationsToggle"',
        'id="tracklogToggle"',
        'id="topologyToggle"',
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".map-context-controls",
        "overflow-x: auto;",
        "grid-template-rows: minmax(260px, 1fr) auto;",
        ".station-last-heard-relative",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function formatRelativeLastHeard(value)",
        "function refreshStationPopupRelativeTimes()",
        'class="station-last-heard-relative"',
        "schedulePolling(refreshStationPopupRelativeTimes, 30000);",
    ],
    "tests/test_core.py": [
        "test_v172_client_versions_consolidate_same_friendly_application",
        "test_v172_map_controls_share_history_context_row",
        "test_v172_station_popup_relative_last_heard_updates_live",
    ],
    "README.md": ["PT2VHF APRS Client"],
    "CHANGELOG.md": ["## v1.7.2 - 2026-09-27"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.2"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.2 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
context_start = html.index('id="mapContextBar"')
main_start = html.index("<main>")
context_html = html[context_start:main_start]
for control in ("mapHistoryToggle", "stationsToggle", "stationsHours", "tracklogToggle", "tracklogHours", "topologyToggle", "topologyHours"):
    if f'id="{control}"' not in context_html:
        raise SystemExit(f"v1.7.2 validation failed: {control} is not in the Map context row")
if 'class="map-top-toolbar"' in html:
    raise SystemExit("v1.7.2 validation failed: legacy map-top-toolbar remains")

print("v1.7.2 release validation OK")
