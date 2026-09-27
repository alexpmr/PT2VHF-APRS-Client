from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.6.23":
    raise SystemExit(f"v1.6.23 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": [
        '__version__ = "1.6.23"',
    ],
    "pt2vhf_aprs/templates/index.html": [
        "img/aprs_logo_official.jpg",
        'id="mapStationAgeFilter"',
        'value="all" selected',
        'value="lt2"',
        'value="2to24"',
        'value="gt24"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "mapStationAgeFilter: 'all'",
        "function mapStationMatchesAge(station)",
        "function updateMapStationAgeCount(visible, total)",
        "state.mapVisibleCallsigns",
        "state.mapKnownCallsigns",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".map-station-age-filter",
        ".map-station-age-count",
    ],
    "windows/make_icon.py": [
        "aprs_logo_official.jpg",
    ],
    "macos/make_icon.py": [
        "aprs_logo_official.jpg",
    ],
    "linux/build_linux.sh": [
        "aprs_logo_official.jpg",
    ],
    "tools/generate_manual.py": [
        "aprs_logo_official.jpg",
    ],
    "README.md": [
        "# PT2VHF APRS Client - v1.6.23",
        "filtro de atividade",
        "logo oficial",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.23 validation failed: {needle!r} missing from {rel}")

logo = ROOT / "pt2vhf_aprs" / "static" / "img" / "aprs_logo_official.jpg"
if not logo.exists() or logo.stat().st_size < 1000:
    raise SystemExit("v1.6.23 validation failed: official logo missing or invalid")

print("v1.6.23 official branding/map activity filter validation OK")
