from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.23":
    raise SystemExit(f"v1.7.23 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.23"'],
    "pt2vhf_aprs/static/js/app.js": [
        "RAINVIEWER_MAPS_URL",
        "pt2vhfWeatherPane",
        "pt2vhfHillshadePane",
        "pt2vhfElevationPane",
        "World_Hillshade/MapServer/tile",
        "basemaps.cartocdn.com/light_all",
        "basemaps.cartocdn.com/dark_all",
        "ensureElevationLayerClass",
        "/api/layers/elevation/tile/",
        "function setElevationThreshold",
        "function setElevationSliderMax",
        "elevation_slider_max",
        "elevation_opacity",
        "keepInView: true",
        "autoPanPaddingTopLeft: [24, 76]",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="mapLayersButton"',
        'id="weatherRadarToggle"',
        'id="hillshadeToggle"',
        'id="elevationToggle"',
        'value="light"',
        'value="dark"',
        'name="elevation_threshold"',
        'name="elevation_slider_max"',
        'name="elevation_opacity"',
        "Relevo com corte",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".elevation-threshold-control",
        "height: 390px",
        "height: 255px",
    ],
    "pt2vhf_aprs/database.py": [
        '"elevation_threshold": 1000',
        '"elevation_slider_max": 3000',
        '"elevation_opacity": 55',
        "elevation_threshold INTEGER NOT NULL DEFAULT 1000",
        "elevation_slider_max INTEGER NOT NULL DEFAULT 3000",
        "elevation_opacity INTEGER NOT NULL DEFAULT 55",
    ],
    "pt2vhf_aprs/web.py": [
        "ELEVATION_TILE_BASE_URL",
        "/api/layers/elevation/tile/<int:z>/<int:x>/<int:y>",
        "elevation-tiles-prod/terrarium",
    ],
    "tests/test_v1723_relief.py": [
        "test_v1723_relief_cutoff_and_map_layers",
        "test_v1723_keeps_radar_and_popup_protection",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.7.23"'],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.23 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
if "Raios" in html or "lightningToggle" in html:
    raise SystemExit("v1.7.23 validation failed: lightning layer must not be present")

print("v1.7.23 production validation OK")
