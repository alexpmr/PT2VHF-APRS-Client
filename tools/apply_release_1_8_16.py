from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


version = read("VERSION").strip()
if version != "1.8.16":
    raise SystemExit(f"v1.8.16 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.16"'],
    "windows/version_info.txt": [
        "filevers=(1, 8, 16, 0)",
        "prodvers=(1, 8, 16, 0)",
        "FileVersion', '1.8.16'",
        "ProductVersion', '1.8.16'",
    ],
    "pt2vhf_aprs/templates/index.html": [
        "<strong>PP5AU</strong><span>Adriano</span>",
        'id="messageContentFilterButton"',
        'id="messageContentFilterMenu"',
        'data-message-content-filter="message"',
        'data-message-content-filter="bulletin"',
        'data-message-content-filter="group"',
        'data-message-content-filter="telemetry"',
        'id="stationViewButton"',
        'id="stationViewTree"',
        'id="messageViewButton"',
        'id="messageViewTree"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "zoomSnap: 0.10",
        "zoomDelta: 0.10",
        "wheelPxPerZoomLevel: 300",
        "wheelDebounceTime: 20",
        "function messageContentCategory(message)",
        "function setAllMessageContentFilters(enabled)",
        "pt2vhf_message_content_filters_v2",
        "function sharedStationViewNodes(stations = [])",
        "function renderAuxViewTrees(",
        "function bindSharedViewTree(",
        "function messageMatchesStationView(message)",
        "stationCatalog: []",
        "function syncSingleViewTreeCheckboxes(tree, updateState = false)",
    ],
    "tests/test_v1816_shared_filters_zoom.py": [
        "test_zoom_is_finer_and_wheel_is_more_gradual",
        "test_message_content_filters_are_one_pulldown_with_four_categories",
        "test_stations_and_messages_share_map_view_filters",
        "test_messages_use_station_catalog_and_keep_unknowns_visible",
    ],
}

missing = []
for rel, snippets in checks.items():
    text = read(rel)
    for snippet in snippets:
        if snippet not in text:
            missing.append(f"{rel}: {snippet}")

html = read("pt2vhf_aprs/templates/index.html")
if "PP5UA" in html:
    missing.append("pt2vhf_aprs/templates/index.html: obsolete PP5UA")
for old_id in ('id="showNormalMessages"', 'id="showBulletinMessages"', 'id="hideTelemetryMessages"'):
    if old_id in html:
        missing.append(f"pt2vhf_aprs/templates/index.html: obsolete {old_id}")

if missing:
    raise SystemExit("v1.8.16 validation failed:\n- " + "\n- ".join(missing))

print("v1.8.16 production validation OK")
