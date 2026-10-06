from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.14.3":
    raise SystemExit("VERSION must be 1.14.3")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.14.3"'],
    "windows/version_info.txt": [
        "filevers=(1, 14, 3, 0)",
        "prodvers=(1, 14, 3, 0)",
        "FileVersion', '1.14.3'",
        "ProductVersion', '1.14.3'",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="headerSendBeaconButton"',
        ">Enviar Beacon</button>",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "async function sendManualBeacon()",
        "$('#headerSendBeaconButton')?.addEventListener",
        "buttons.some(button => button.disabled)",
        "infrastructure_evidence",
        "metadataInfrastructure",
        "function stationInteractionProfile(s)",
    ],
    "pt2vhf_aprs/database.py": [
        "def _infrastructure_calls_conn(",
        'item["infrastructure_evidence"]',
        "WHERE kind='rf'",
        "SELECT UPPER(TRIM(igate)) AS callsign",
    ],
    "tests/test_v143_release.py": [
        "test_v143_header_manual_beacon_uses_existing_pipeline",
        "test_v143_wide_path_source_is_not_infrastructure_but_real_hop_is",
        "test_v143_interaction_classifier_does_not_use_raw_path_as_role_evidence",
    ],
    "README.md": ["# PT2VHF APRS Client - v1.14.3", "## Novidades da v1.14.3"],
    "CHANGELOG.md": ["## 1.14.3 - 2026-10-06"],
    "BACKLOG.md": ["## Concluído na v1.14.3"],
    "pt2vhf_aprs/version_notes.py": ['"1.14.3": {'],
    "tools/generate_manual.py": ["O botão Enviar Beacon na barra principal superior"],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.14.3 validation failed: {needle!r} missing from {rel}")

profile = read("pt2vhf_aprs/static/js/app.js")
start = profile.index("function stationInteractionProfile(s)")
end = profile.index("function stationInteractionDisabledAttrs", start)
interaction = profile[start:end]
if "s?.raw" in interaction or "WIDE[1-7]" in interaction:
    raise SystemExit("v1.14.3 validation failed: raw/WIDE path still influences interaction role")

print("v1.14.3 validation OK")
