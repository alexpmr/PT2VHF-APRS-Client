from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.15":
    raise SystemExit(f"v1.7.15 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.15"'],
    "pt2vhf_aprs/database.py": [
        "AS interaction_evidence",
        "m.direction='in'",
        "UPPER(COALESCE(m.status,'')) IN ('ACK','REJ')",
        "q.response_at IS NOT NULL",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function stationInteractionProfile(s)",
        "const digiSymbol = String(s?.symbol || '') === '#';",
        "DIGI(?:PEATER)?",
        "D-?STAR",
        "HOTSPOT",
        "stationInteractionDisabledAttrs",
        "station-interaction-disabled-note",
        "Versão atualizada",
        "Versão ${data.latest_version} disponível",
        "30 * 60 * 1000",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".station-popup .btn:disabled",
        ".station-interaction-disabled-note",
    ],
    "tests/test_core.py": ["test_v1715_infrastructure_interaction_requires_evidence"],
    "README.md": ["# PT2VHF APRS Client - v1.7.15"],
    "CHANGELOG.md": ["## v1.7.15 - 2026-09-28"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.15"'],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.15 validation failed: {needle!r} missing from {rel}")

print("v1.7.15 production validation OK")
