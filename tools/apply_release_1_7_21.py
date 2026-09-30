from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pt2vhf_aprs import database as db

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.21":
    raise SystemExit(f"v1.7.21 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.21"'],
    "pt2vhf_aprs/static/js/app.js": [
        "RAINVIEWER_WEATHER_MAPS_URL",
        "https://api.rainviewer.com/public/weather-maps.json",
        "function loadWeatherRadar",
        "pt2vhfRadarPane",
        "maxNativeZoom: 7",
        "/256/{z}/{x}/{y}/2/1_0.png",
        "weatherRadarEnabled: localStorage.getItem('pt2vhf_map_item_weather_radar') === '1'",
        "Radar meteorológico",
        "weather_radar_transparency",
        "Weather data ©",
        "RainViewer",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'name="weather_radar_transparency"',
        'id="weatherRadarTransparency"',
        "Transparência do radar meteorológico",
        'id="mapLayersButton"',
        'id="mapLayersMenu"',
        'id="weatherRadarLayerToggle"',
    ],
    "pt2vhf_aprs/database.py": [
        '"weather_radar_transparency": 35',
        "weather_radar_transparency INTEGER NOT NULL DEFAULT 35",
    ],
    "tests/test_core.py": [
        "test_v1721_weather_radar_layer_and_transparency_setting",
        "test_v1721_weather_radar_config_persists_and_validates",
        "test_v1721_weather_radar_is_below_aprs_overlays_and_off_by_default",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.7.21"'],
}
for rel, needles in checks.items():
    content = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in content:
            raise SystemExit(f"v1.7.21 validation failed: {needle!r} missing from {rel}")

if db.DEFAULT_CONFIG["weather_radar_transparency"] != 35:
    raise SystemExit("v1.7.21 validation failed: radar transparency default is not 35")

js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
if js.index("radarPane.style.zIndex = '320'") > js.index("visualPane.style.zIndex = '450'"):
    raise SystemExit("v1.7.21 validation failed: radar pane is not below APRS visual pane")

print("v1.7.21 Windows x64 portable weather radar validation OK")
