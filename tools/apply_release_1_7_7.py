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
        'Preserve q-construct case',
        'token in {"qAR", "qAO"}',
        'kind = "rf" if direct_rf_gate else "igate"',
    ],
    "pt2vhf_aprs/updater.py": [
        'arch = "ARM64" if machine == "arm64" else "x64"',
        'machine in {"x86_64", "arm64"}',
    ],
    "windows/PT2VHF_APRS_Client_Portable_ARM64.spec": [
        "PT2VHF_APRS_Client_Portable_ARM64",
    ],
    "windows/installer_arm64.iss": [
        "ArchitecturesAllowed=arm64",
        "ArchitecturesInstallIn64BitMode=arm64",
        "PT2VHF_APRS_Client_Setup_ARM64_v",
    ],
    ".github/workflows/build-windows.yml": [
        "windows-arm64:",
        "runs-on: windows-11-arm",
        "architecture: 'arm64'",
        "PT2VHF_APRS_Client_Setup_ARM64_v",
        "PT2VHF_APRS_Client_Portable_ARM64_v",
    ],
    "tools/apply_release_1_6_5.py": [
        "Não recriar o antigo botão",
        "assert 'id=\"toggleReplayBarButton\"' not in html",
    ],
    "tests/test_core.py": [
        "test_v177_message_cleanup_map_defaults_and_update_cadence",
        "test_v177_legacy_build_patch_does_not_restore_global_history_button",
        "test_v177_windows_arm64_build_and_updater_assets",
        "test_v177_remote_igate_qconstruct_is_not_rf_link",
        "test_v177_rf_igate_parser_preserves_qconstruct_case",
    ],
    "README.md": [
        "# PT2VHF APRS Client - v1.7.7",
        "PT2VHF_APRS_Client_Setup_ARM64_vX.Y.exe",
    ],
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
