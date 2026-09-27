from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.6.23":
    raise SystemExit(f"v1.6.23 validation failed: VERSION={version!r}")

# Consolida a identidade visual estável depois dos patches legados da série 1.6.x.
html_path = ROOT / "pt2vhf_aprs" / "templates" / "index.html"
html = html_path.read_text(encoding="utf-8")
html = html.replace("img/app_logo.svg", "img/app_logo.svg")
html = html.replace('type="image/jpeg"', 'type="image/svg+xml"')
html_path.write_text(html, encoding="utf-8")

windows_icon = ROOT / "windows" / "make_icon.py"
icon_text = windows_icon.read_text(encoding="utf-8")
icon_text = icon_text.replace("app_logo.png", "app_logo.png")
windows_icon.write_text(icon_text, encoding="utf-8")

windows_launcher = ROOT / "windows_app.py"
launcher_text = windows_launcher.read_text(encoding="utf-8")
launcher_text = launcher_text.replace('"app_logo.png"', '"app_logo.png"')
windows_launcher.write_text(launcher_text, encoding="utf-8")

tests_path = ROOT / "tests" / "test_core.py"
tests = tests_path.read_text(encoding="utf-8")
tests = tests.replace('assert "app_logo.png" in html', 'assert "img/app_logo.svg" in html')
tests_path.write_text(tests, encoding="utf-8")

checks = {
    "pt2vhf_aprs/__init__.py": [
        '__version__ = "1.6.23"',
    ],
    "pt2vhf_aprs/templates/index.html": [
        "img/app_logo.svg",
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
        "mapLegendCollapsed: localStorage.getItem(",
        "function syncMapLegendCollapsed()",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".map-station-age-filter",
        ".map-station-age-count",
        ".map-legend-toggle",
    ],
    "windows/make_icon.py": [
        "app_logo.png",
    ],
    "macos/make_icon.py": [
        "app_logo.png",
    ],
    "linux/build_linux.sh": [
        "app_logo.png",
    ],
    "tools/generate_manual.py": [
        "app_logo.png",
    ],
    "README.md": [
        "# PT2VHF APRS Client - v1.6.23",
        "filtro de atividade",
        "logo vetorial/raster",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.23 validation failed: {needle!r} missing from {rel}")

logo_svg = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.svg"
logo_png = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"
if not logo_svg.exists() or logo_svg.stat().st_size < 1000 or not logo_png.exists() or logo_png.stat().st_size < 1000:
    raise SystemExit("v1.6.23 validation failed: application logo assets missing or invalid")

print("v1.6.23 branding/map activity filter validation OK")
