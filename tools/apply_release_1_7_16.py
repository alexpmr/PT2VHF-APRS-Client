from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pt2vhf_aprs import database as db

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.16":
    raise SystemExit(f"v1.7.16 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.16"'],
    "pt2vhf_aprs/templates/index.html": [
        'id="mapItemsButton"',
        '>Ver ▾</button>',
        'id="mapViewTree"',
        'id="mapViewAllButton"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function stationMapFilterKeys(station)",
        "function stationMatchesViewFilter(station)",
        "function objectMatchesViewFilter(object)",
        "function renderMapViewTree(stations = [], objects = [])",
        "groupedMapNodes(digiRows, 'digi')",
        "groupedMapNodes(igateRows, 'igate')",
        "pt2vhf_map_view_filters",
        "pt2vhf_map_view_expanded",
        "mapCallVisibleForTraffic",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".map-view-tree-menu",
        ".map-view-checkbox",
        ".map-view-children.hidden",
    ],
    "pt2vhf_aprs/database.py": [
        "def aprs_map_device_metadata",
        '"device_class"',
        '"map_role"',
        '"map_subtype"',
    ],
    "tests/test_core.py": [
        "test_v1716_hierarchical_map_filters_and_device_roles",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.7.16"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.16 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
for legacy in ("mapItemStations", "mapItemObjects", "mapItemTracklogs", "mapItemRfLinks", "mapItemIgateLinks", "mapItemPackets"):
    if f'id="{legacy}"' in html:
        raise SystemExit(f"v1.7.16 validation failed: legacy map checkbox {legacy} still present")

digi = db.aprs_map_device_metadata("PY2AAA>APRFGL,WIDE1-1:>LoRa", "", "#")
if digi.get("map_role") != "digi":
    raise SystemExit(f"v1.7.16 validation failed: APRFGL role={digi!r}")

igate = db.aprs_map_device_metadata("PY2AAA>APRFGI,TCPIP*:>LoRa", "", "&")
if igate.get("map_role") != "igate":
    raise SystemExit(f"v1.7.16 validation failed: APRFGI role={igate!r}")

print("v1.7.16 Windows x64 portable validation OK")
