from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.5":
    raise SystemExit(f"v1.8.5 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.5"'],
    "pt2vhf_aprs/tnc_service.py": [
        "def normalize_message_rf_path(",
        "def queue_local_message(",
        "TNC/RF desconectado",
    ],
    "pt2vhf_aprs/aprs_service.py": [
        'route: str = "auto"',
        'selected_route = "aprs_is" if aprs_ready else ("rf_direct" if rf_ready else "auto")',
        "queue_local_message",
        '"tx_medium": medium',
        '"tx_path": effective_path',
    ],
    "pt2vhf_aprs/database.py": [
        "tx_medium TEXT",
        "tx_path TEXT",
        "ALTER TABLE messages ADD COLUMN tx_medium TEXT",
        "ALTER TABLE messages ADD COLUMN tx_path TEXT",
    ],
    "pt2vhf_aprs/web.py": [
        'route=data.get("route", "auto")',
        'path=data.get("path", "")',
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="messageRoute"',
        'value="auto"',
        'value="aprs_is"',
        'value="rf_direct"',
        'value="rf_custom"',
        'id="messagePath"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function updateMessageRouteMode()",
        "function messageTransportLabel(",
        "message-transport-badge",
        "body:JSON.stringify({ route, path })",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        "@media (max-height: 800px) and (min-width: 901px)",
        "max-height: min(500px, calc(100dvh - 230px));",
        ".message-transport-badge",
    ],
    "tests/test_v185_message_route_responsive.py": [
        "test_v185_rf_path_validation_accepts_standard_paths",
        "test_v185_auto_route_preserves_aprs_is_priority",
        "test_v185_low_height_layout_targets_1360x768_class_displays",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.5"'],
    "CHANGELOG.md": ["## 1.8.5 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.5", "## Novidades da v1.8.5"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.5 validation failed: {needle!r} missing from {rel}")

from pt2vhf_aprs.tnc_service import normalize_message_rf_path

if normalize_message_rf_path("WIDE1-1,WIDE2-1") != ["WIDE1-1", "WIDE2-1"]:
    raise SystemExit("v1.8.5 validation failed: standard RF path normalization")
try:
    normalize_message_rf_path("WIDE1-1*")
except ValueError:
    pass
else:
    raise SystemExit("v1.8.5 validation failed: repeated marker accepted in TX path")

css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
if "@media (max-height: 800px)" not in css or "100dvh" not in css:
    raise SystemExit("v1.8.5 validation failed: low-height responsive rules missing")

print("v1.8.5 message route/path and low-height production validation OK")
