from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.7":
    raise SystemExit(f"v1.7.7 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.7"'],
    "pt2vhf_aprs/templates/index.html": [
        'id="mapContextBar"',
        'id="mapHistoryToggle"',
        'id="clearMessagesButton" type="button" class="btn danger">Limpar</button>',
        'value="#ffff00"',
        'id="topologyWidth" type="range" min="1" max="10" step="1" value="1"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "'Limpar':'Clear'",
        "topology_rf_color: '#ffff00'",
        "topology_igate_color: '#ffff00'",
        "topology_width: 1",
        "30 * 60 * 1000",
    ],
    "pt2vhf_aprs/database.py": [
        '"track_color": "#3ba6ff"',
        '"topology_rf_color": "#ffff00"',
        '"topology_igate_color": "#ffff00"',
        '"topology_width": 1',
        '"sound_on_station_activity": 1',
        '"traffic_animation_enabled": 1',
    ],
    "tools/apply_release_1_6_5.py": [
        "Não recriar o antigo botão",
        "assert 'id=\"toggleReplayBarButton\"' not in html",
    ],
    "tests/test_core.py": [
        "test_v177_message_cleanup_map_defaults_and_update_cadence",
        "test_v177_legacy_build_patch_does_not_restore_global_history_button",
    ],
    "README.md": ["# PT2VHF APRS Client - v1.7.7"],
    "CHANGELOG.md": ["## v1.7.7 - 2026-09-28"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.7"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.7 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
if 'id="toggleReplayBarButton"' in html:
    raise SystemExit("v1.7.7 validation failed: legacy global History button remains")
if html.count('id="mapHistoryToggle"') != 1:
    raise SystemExit("v1.7.7 validation failed: History control is duplicated")

print("v1.7.7 release validation OK")
