from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.9":
    raise SystemExit(f"v1.7.9 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.9"'],
    "pt2vhf_aprs/templates/index.html": [
        'id="topologySpeed"',
        '<option value="0.5">0,5x</option>',
        '<option value="1" selected>1x</option>',
        '<option value="2">2x</option>',
        '<option value="5">5x</option>',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function setTrafficSpeed(value, source = '')",
        "pt2vhf_traffic_speed",
        "setTrafficSpeed(event.target.value, 'topology')",
        "setTrafficSpeed(event.target.value, 'replay')",
        "ui(\`Versão \${current}\`, \`Build \${current}\`)",
        "for (const segment of (event.segments || []))",
    ],
    "tests/test_core.py": ["test_v179_map_speed_control_and_version_label"],
    "README.md": ["# PT2VHF APRS Client - v1.7.9"],
    "CHANGELOG.md": ["## v1.7.9 - 2026-09-28"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.9"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.9 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
topology = html.index('id="topologyToggle"')
speed = html.index('id="topologySpeed"', topology)
period = html.index('id="topologyHours"', topology)
if not topology < speed < period:
    raise SystemExit("v1.7.9 validation failed: speed selector must be between topology toggle and period")

print("v1.7.9 portable validation OK")
