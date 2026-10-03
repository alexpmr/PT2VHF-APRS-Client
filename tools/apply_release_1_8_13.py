from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.13":
    raise SystemExit(f"v1.8.13 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.13"'],
    "windows/version_info.txt": [
        "filevers=(1, 8, 13, 0)",
        "prodvers=(1, 8, 13, 0)",
        "FileVersion', '1.8.13'",
        "ProductVersion', '1.8.13'",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="messageRoute"',
        '<option value="auto" selected>Automático</option>',
        '<option value="aprs_is">APRS-IS</option>',
        '<option value="rf_direct">RF direto</option>',
        '<option value="rf_custom">RF personalizado</option>',
        'id="elevationToggle"',
        "Relevo com corte",
        "tiny.cc/aprs",
        'id="aboutPromoteButton"',
        "img/app_logo.png",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function stationInteractionProfile(s)",
        "stationInteractionDisabledAttrs",
        '${interactionDisabled}>Ping/ACK</button>',
        '${interactionDisabled}>Enviar mensagem</button>',
        "elevationThresholdSlider",
        "Math.min(9000, Math.max(100",
        "function aboutCopy()",
        "function renderAbout()",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        "@media (max-height: 800px) and (min-width: 901px)",
        ".station-popup-actions",
        ".message-composer",
        ".elevation-vertical-range",
        "height: 390px;",
        ".elevation-vertical-range { height: 255px; }",
    ],
    "pt2vhf_aprs/database.py": [
        "interaction_evidence",
        "message_capable",
        "elevation_slider_max",
        "elevation_threshold",
        "elevation_opacity",
        'if "medium" not in packet_columns:',
        'if "rx_fingerprint" not in packet_columns:',
    ],
    "tests/test_v1813_consolidated_backlog.py": [
        "test_v1813_message_route_backlog_is_present",
        "test_v1813_low_height_layout_covers_1360x768_and_1280x720",
        "test_v1813_non_bidirectional_targets_disable_interaction_actions",
        "test_v1813_dem_elevation_backlog_is_present_and_persistent",
        "test_v1813_about_backlog_is_present_and_localized",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.13"'],
    "CHANGELOG.md": ["## 1.8.13 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.13", "## Novidades da v1.8.13"],
    "BACKLOG.md": ["## Concluído na v1.8.13", "1360×768 e 1280×720"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.13 validation failed: {needle!r} missing from {rel}")

backlog = (ROOT / "BACKLOG.md").read_text(encoding="utf-8")
if "- **Mapa — camada Elevação mínima com corte por altitude**" in backlog:
    raise SystemExit("v1.8.13 validation failed: stale elevation backlog still open")

db_source = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")
schema_end = db_source.index("        # Migração v1.7.7:")
schema_script = db_source[:schema_end]
for index_name in (
    "idx_packets_medium_time",
    "idx_packets_medium_call_time",
    "idx_packets_fingerprint_time",
):
    if index_name in schema_script:
        raise SystemExit(
            f"v1.8.13 validation failed: {index_name} created before legacy packet migration"
        )

print("v1.8.13 consolidated backlog validation OK")
