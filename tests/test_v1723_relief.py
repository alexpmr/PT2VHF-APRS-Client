from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v1723_relief_cutoff_and_map_layers():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
    db = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")
    web = (ROOT / "pt2vhf_aprs/web.py").read_text(encoding="utf-8")

    # Map bases and layers.
    assert "basemaps.cartocdn.com/light_all" not in js
    assert "basemaps.cartocdn.com/dark_all" not in js
    assert "World_Hillshade/MapServer/tile" not in js
    assert "pt2vhfHillshadePane" not in js
    assert "tile-cyclosm.openstreetmap.fr/cyclosm" in js
    assert "tile.openstreetmap.fr/hot" in js
    assert "tile.openstreetmap.de" in js
    assert "tile.memomaps.de/tilegen" in js
    assert "pt2vhfElevationPane" in js
    assert "ensureElevationLayerClass" in js
    assert "/api/layers/elevation/tile/" in js

    # Terrarium decoding and live cutoff.
    assert "(raw[i] * 256 + raw[i + 1] + raw[i + 2] / 256) - 32768" in js
    assert "altitude >= threshold" in js
    assert "function setElevationThreshold" in js
    assert "function setElevationSliderMax" in js
    assert "function redrawElevationTiles" in js
    assert "elevation_slider_max" in js
    assert "elevation_opacity" in js

    # UI.
    assert 'id="hillshadeToggle"' not in html
    assert 'id="elevationToggle"' in html
    assert 'value="light"' in html
    assert 'value="dark"' in html
    assert 'name="elevation_threshold"' in html
    assert 'name="elevation_slider_max"' in html
    assert 'name="elevation_opacity"' in html
    assert "Relevo com corte" in html
    assert "Raios" not in html
    assert ".elevation-threshold-control" in css
    assert "height: 390px" in css
    assert "height: 255px" in css

    # Persistence and migration.
    assert '"elevation_threshold": 1000' in db
    assert '"elevation_slider_max": 3000' in db
    assert '"elevation_opacity": 55' in db
    assert "elevation_threshold INTEGER NOT NULL DEFAULT 1000" in db
    assert "elevation_slider_max INTEGER NOT NULL DEFAULT 3000" in db
    assert "elevation_opacity INTEGER NOT NULL DEFAULT 55" in db
    assert '{"osm", "topo", "light", "dark", "cyclosm", "humanitarian", "osmde", "opnv", "satellite"}' in db

    # Same-origin DEM proxy.
    assert 'ELEVATION_TILE_BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium"' in web
    assert '@app.get("/api/layers/elevation/tile/<int:z>/<int:x>/<int:y>")' in web
    assert 'response.headers["Cache-Control"] = "public, max-age=86400"' in web


def test_v1723_keeps_radar_and_popup_protection():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")

    assert "RAINVIEWER_MAPS_URL" in js
    assert "pt2vhfWeatherPane" in js
    assert "weather_radar_opacity" in js
    assert "keepInView: true" in js
    assert "autoPanPaddingTopLeft: [24, 76]" in js
    assert ".station-popup" in css
