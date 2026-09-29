from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pt2vhf_aprs import database as db

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.17":
    raise SystemExit(f"v1.7.17 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.17"'],
    "pt2vhf_aprs/static/js/app.js": [
        "pt2vhf_map_view_filters_v2",
        "${role}:family:${family}",
        "object:family:",
        "function groupedMapNodes(rows, role)",
        "function objectMapNodes(objects)",
        "map_family_label",
        "map_family_key",
    ],
    "pt2vhf_aprs/database.py": [
        "def _aprs_map_family",
        '"RDZSonDe"',
        '"Bravo Tracker"',
        '"D-Star"',
        '"DMR"',
        '"HBLink D-APRS Gateway"',
        '"map_family_key"',
        '"map_family_label"',
    ],
    "tests/test_core.py": [
        "test_v1717_map_ver_groups_by_family_not_callsign",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.7.17"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.17 validation failed: {needle!r} missing from {rel}")

js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

grouped_start = js.index("function groupedMapNodes(rows, role)")
grouped_end = js.index("function objectMapNodes(objects)", grouped_start)
grouped = js[grouped_start:grouped_end]
for forbidden in ("device_vendor", "device_tocall", "source_callsign", "children:"):
    if forbidden in grouped:
        raise SystemExit(f"v1.7.17 validation failed: groupedMapNodes still uses {forbidden}")

objects_start = js.index("function objectMapNodes(objects)")
objects_end = js.index("function renderMapViewTree", objects_start)
object_nodes = js[objects_start:objects_end]
for forbidden in ("source_callsign", "object.name", "children:"):
    if forbidden in object_nodes:
        raise SystemExit(f"v1.7.17 validation failed: objectMapNodes still uses {forbidden}")

rdz = db.aprs_map_device_metadata("PP2LA-11>APRRDZ,TCPIP*:;X3922153*...", "radiosonde", "/")
if rdz.get("map_family_label") != "RDZSonDe":
    raise SystemExit(f"v1.7.17 validation failed: RDZ family={rdz!r}")

dmr = db.aprs_map_device_metadata("PY2AAA>APBM01,TCPIP*:>BrandMeister DMR", "DMR", ">")
if dmr.get("map_family_label") != "DMR":
    raise SystemExit(f"v1.7.17 validation failed: DMR family={dmr!r}")

hblink = db.aprs_map_device_metadata("KF7EEL>APHBL1,TCPIP*:>HBLink D-APRS Gateway", "D-APRS", "&")
if hblink.get("map_family_label") != "HBLink D-APRS Gateway":
    raise SystemExit(f"v1.7.17 validation failed: HBLink family={hblink!r}")

print("v1.7.17 Windows x64 portable validation OK")
