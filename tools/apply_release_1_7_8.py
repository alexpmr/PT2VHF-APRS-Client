from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.8":
    raise SystemExit(f"v1.7.8 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.8"'],
    "pt2vhf_aprs/static/js/app.js": [
        "for (const segment of (event.segments || []))",
        "await animateTrafficSegment(segment, event, duration)",
        "stationActivity(segment.target)",
        "dashArray: isInternet ? '8 6' : null",
        "const isInternet = segment.kind === 'igate'",
    ],
    "pt2vhf_aprs/database.py": [
        '"respond_to_queries": 1',
        "respond_to_queries INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE config ADD COLUMN respond_to_queries INTEGER NOT NULL DEFAULT 1",
        'kind = "rf" if direct_rf_gate else "igate"',
        'token in {"qAR", "qAO"}',
    ],
    "README.md": [
        "# PT2VHF APRS Client - v1.7.8",
        "Windows x64 Portable",
    ],
    "CHANGELOG.md": ["## v1.7.8 - 2026-09-28"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.8"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.8 validation failed: {needle!r} missing from {rel}")

js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
if "Promise.all((event.segments || []).map(segment => animateTrafficSegment" in js:
    raise SystemExit("v1.7.8 validation failed: traffic animation is still simultaneous")

print("v1.7.8 portable validation OK")
