from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.22":
    raise SystemExit(f"v1.7.22 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.22"'],
    "pt2vhf_aprs/static/js/app.js": [
        "RAINVIEWER_MAPS_URL",
        "async function refreshWeatherRadar",
        "async function setWeatherRadarEnabled",
        "pt2vhfWeatherPane",
        "weather_radar_opacity",
        "keepInView: true",
        "autoPanPaddingTopLeft: [24, 76]",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="mapLayersButton"',
        'id="weatherRadarToggle"',
        'name="weather_radar_opacity"',
        "RainViewer",
    ],
    "pt2vhf_aprs/database.py": [
        '"weather_radar_opacity": 55',
        "weather_radar_opacity INTEGER NOT NULL DEFAULT 55",
    ],
    "tests/test_v1722_radar.py": [
        "test_v1722_weather_radar_layer_and_popup_protection",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.7.22"'],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.22 validation failed: {needle!r} missing from {rel}")

print("v1.7.22 Windows x64 portable validation OK")
