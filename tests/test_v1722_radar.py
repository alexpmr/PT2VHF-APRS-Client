from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v1722_weather_radar_layer_and_popup_protection():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
    db = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")

    assert "RAINVIEWER_MAPS_URL" in js
    assert "async function refreshWeatherRadar" in js
    assert "setWeatherRadarEnabled" in js
    assert "pt2vhfWeatherPane" in js
    assert "maxNativeZoom: 7" in js
    assert "weather_radar_opacity" in js
    assert "autoPanPaddingTopLeft: [24, 76]" in js
    assert "keepInView: true" in js

    assert 'id="mapLayersButton"' in html
    assert 'id="mapLayersMenu"' in html
    assert 'id="weatherRadarToggle"' in html
    assert 'name="weather_radar_opacity"' in html
    assert "RainViewer" in html

    assert ".map-layers-menu" in css
    assert ".leaflet-pane.pt2vhf-weather-pane" in css
    assert ".station-popup" in css

    assert '"weather_radar_opacity": 55' in db
    assert "weather_radar_opacity INTEGER NOT NULL DEFAULT 55" in db
    assert 'ALTER TABLE config ADD COLUMN weather_radar_opacity INTEGER NOT NULL DEFAULT 55' in db
