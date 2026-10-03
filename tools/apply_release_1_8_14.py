from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.14":
    raise SystemExit(f"v1.8.14 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.14"'],
    "windows/version_info.txt": [
        "filevers=(1, 8, 14, 0)",
        "prodvers=(1, 8, 14, 0)",
        "FileVersion', '1.8.14'",
        "ProductVersion', '1.8.14'",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="messageRoute"',
        '<option value="auto" selected>Automático</option>',
        '<option value="aprs_is">APRS-IS</option>',
        '<option value="rf_direct">RF direto</option>',
        '<option value="rf_custom">RF personalizado</option>',
        'id="elevationToggle"',
        'id="aboutAprsTitle"',
        'id="aboutAprsText"',
        "tiny.cc/aprs",
        "img/app_logo.png",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function stationInteractionProfile(s)",
        "stationInteractionDisabledAttrs",
        '${interactionDisabled}>Ping/ACK</button>',
        '${interactionDisabled}>Trace</button>',
        '${interactionDisabled}>Enviar mensagem</button>',
        "function elevationGridFromTerrarium(canvas)",
        "function elevationHillshadeFactor(grid, x, y)",
        "const shade = elevationHillshadeFactor(grid, x, y);",
        "Math.min(9000, Math.max(100",
        "aprsTitle: 'O que é APRS?'",
        "aprsTitle: 'What is APRS?'",
        "aprsTitle: '¿Qué es APRS?'",
        "aprsTitle: 'Qu’est-ce que l’APRS ?'",
        "Automatic Packet Reporting System",
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
    "tests/test_v1814_complete_backlogs.py": [
        "test_v1814_about_explicitly_explains_aprs_in_all_languages",
        "test_v1814_elevation_uses_dem_derived_hillshade",
        "test_v1814_all_requested_backlogs_remain_covered",
        "test_v1814_preserves_legacy_sqlite_migration_guard",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.14"'],
    "CHANGELOG.md": ["## 1.8.14 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.14", "## Novidades da v1.8.14"],
    "BACKLOG.md": ["## Concluído na v1.8.14", "hillshade derivado do próprio DEM", "explicação explícita de APRS"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.14 validation failed: {needle!r} missing from {rel}")

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
            f"v1.8.14 validation failed: {index_name} created before legacy packet migration"
        )

print("v1.8.14 complete backlog validation OK")
