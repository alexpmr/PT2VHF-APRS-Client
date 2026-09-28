from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.10":
    raise SystemExit(f"v1.7.10 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.10"'],
    "pt2vhf_aprs/templates/index.html": [
        'id="mapPeriodHours"',
        'id="mapItemsButton"',
        'id="mapItemStations" type="checkbox" checked',
        'id="mapItemObjects" type="checkbox" checked',
        'id="mapItemTracklogs" type="checkbox" checked',
        'id="mapItemRfLinks" type="checkbox" checked',
        'id="mapItemIgateLinks" type="checkbox" checked',
        'id="mapItemPackets" type="checkbox" checked',
        'id="mapTypeQuick"',
        'id="topologySpeed"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function addMapControls()",
        "pt2vhf_map_period_hours",
        "pt2vhf_map_item_igate",
        "segment.internet_handoff",
        "interactive: false",
        "objectMarkers: new Map()",
        "mapTypeQuick",
    ],
    "pt2vhf_aprs/database.py": [
        "CREATE TABLE IF NOT EXISTS aprs_objects",
        '"target": "APRS-IS"',
        '"internet_handoff": True',
    ],
    "tests/test_core.py": [
        "test_v1710_unified_map_items_objects_and_internet_handoff",
    ],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.10 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
for removed in ("stationsHours", "tracklogHours", "topologyHours", "topologyToggle", "trafficRangeStart", "trafficRangeEnd"):
    if f'id="{removed}"' in html:
        raise SystemExit(f"v1.7.10 validation failed: legacy control {removed} still present")

print("v1.7.10 portable validation OK")
