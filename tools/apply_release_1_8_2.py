from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.2":
    raise SystemExit(f"v1.8.2 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.2"'],
    "pt2vhf_aprs/local_server.py": [
        "DEFAULT_START_PORT = 8080",
        "def allocate_local_server(",
        "def start_local_server(",
        "factory(app, host, port, threads)",
        "read_runtime_url",
        "local_server.json",
    ],
    "windows_app.py": [
        "configured_start_port()",
        "start_local_server(",
        "runtime_file_for(db.DB_PATH.parent)",
        "local_server_started",
        "_current_url()",
    ],
    "linux_app.py": [
        "configured_start_port()",
        "start_local_server(",
        "runtime_file_for(db.DB_PATH.parent)",
    ],
    "macos_app.py": [
        "configured_start_port()",
        "start_local_server(",
        "runtime_file_for(db.DB_PATH.parent)",
    ],
    "app.py": [
        "start_local_server(app, runtime_file=runtime_file_for(db.DB_PATH.parent))",
        "Interface local",
    ],
    "pt2vhf_aprs/database.py": [
        'key, label = "ais", "AIS"',
        "MMSI",
        "AIS2APRS",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="appLanguage"',
        'id="localInterfaceStatus"',
        "Interface local:",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "localInterfaceAnnounced",
        "s.local_interface || {}",
        "pt2vhf_map_item_stations",
        "pt2vhf_map_item_packets",
        "state.mapViewFilters[String(key || '')] !== false",
    ],
    "tools/capture_manual_screenshots.py": [
        "wait_runtime_url",
        "local_server.json",
        "page.goto(local_url",
    ],
    "tests/test_v182_port_ais_view.py": [
        "test_v182_dynamic_port_falls_forward_without_probe_race",
        "test_v182_ais_object_classification_is_conservative",
        "test_v182_map_ver_defaults_all_enabled_and_persist_user_choices",
        "test_v182_settings_large_flag_removed_but_quick_language_flags_remain",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.2"'],
    "CHANGELOG.md": ["## 1.8.2 - 2026-10-01"],
    "README.md": ["# PT2VHF APRS Client - v1.8.2", "## Novidades da v1.8.2"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.2 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
for obsolete in ('id="languageFlag"', "function syncLanguageFlag()"):
    if obsolete in html or obsolete in js:
        raise SystemExit(f"v1.8.2 validation failed: obsolete large settings flag hook remains: {obsolete}")

for rel in ("windows_app.py", "linux_app.py", "macos_app.py"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    if "serve(app, host=HOST, port=PORT" in text:
        raise SystemExit(f"v1.8.2 validation failed: fixed direct waitress serve remains in {rel}")

from pt2vhf_aprs import database as db
from pt2vhf_aprs import local_server

ais = db.aprs_object_map_metadata("AIS-123456789", "MMSI: 123456789", "/", "s", "object")
if ais.get("map_family_key") != "ais":
    raise SystemExit("v1.8.2 validation failed: AIS object classification not active")

calls = []
class FakeServer:
    def run(self):
        return None
    def close(self):
        return None

def fake_factory(app, host, port, threads):
    calls.append(port)
    if port < 8082:
        raise OSError("busy")
    return "fake", FakeServer()

handle = local_server.allocate_local_server(
    object(), host="127.0.0.1", start_port=8080, attempts=4, server_factory=fake_factory
)
if handle.port != 8082 or calls != [8080, 8081, 8082]:
    raise SystemExit("v1.8.2 validation failed: sequential dynamic port fallback is incorrect")

print("v1.8.2 dynamic-port/AIS/UI production validation OK")
