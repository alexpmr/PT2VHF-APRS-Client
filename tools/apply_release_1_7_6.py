from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.6":
    raise SystemExit(f"v1.7.6 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.6"'],
    "pt2vhf_aprs/updater.py": [
        "def _write_windows_cmd_helper",
        "_write_windows_cmd_helper(pending)",
        'os.environ.get("COMSPEC", r"C:\\Windows\\System32\\cmd.exe")',
        "timeout: float = 12.0",
        'encoding="utf-8-sig"',
    ],
    "pt2vhf_aprs/database.py": [
        "def manual_conversation_stats",
        '"manual_conversations": manual_conversation_stats',
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="mapContextBar"',
        'id="mapHistoryToggle"',
        'id="kmlExportButton"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "async function saveKmlContent",
        "showSaveFilePicker",
        "save_text_file",
        "manual_conversations",
        "Estações que mais interagiram",
    ],
    "windows_app.py": [
        "def save_text_file",
        "SAVE_DIALOG",
    ],
    "linux_app.py": [
        "def save_text_file",
        "SAVE_DIALOG",
    ],
    "macos_app.py": [
        "def save_text_file",
        "SAVE_DIALOG",
    ],
    "tests/test_core.py": [
        "test_v176_manual_conversation_ranking_excludes_automatic_traffic",
        "test_v176_kml_save_as_and_map_toolbar_controls",
        "test_v176_windows_updater_uses_native_cmd_helper",
        "test_v176_windows_updater_launch_prefers_comspec_cmd",
    ],
    "README.md": ["# PT2VHF APRS Client - v1.7.6"],
    "CHANGELOG.md": ["## v1.7.6 - 2026-09-28"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.6"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.6 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
map_bar_start = html.index('id="mapContextBar"')
map_bar_end = html.index("<main>", map_bar_start)
map_bar = html[map_bar_start:map_bar_end]
header = html[:map_bar_start]
if 'id="kmlExportButton"' not in map_bar or 'id="kmlExportButton"' in header:
    raise SystemExit("v1.7.6 validation failed: KML button is not confined to the map context bar")
if 'id="mapHistoryToggle"' not in map_bar:
    raise SystemExit("v1.7.6 validation failed: History button is not in the map context bar")

print("v1.7.6 release validation OK")
