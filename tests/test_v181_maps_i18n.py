from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v181_keyless_map_bases_and_hillshade_removal():
    js = read("pt2vhf_aprs/static/js/app.js")
    html = read("pt2vhf_aprs/templates/index.html")
    css = read("pt2vhf_aprs/static/css/app.css")
    db = read("pt2vhf_aprs/database.py")
    web = read("pt2vhf_aprs/web.py")

    # Relevo sombreado was intentionally removed from the active product.
    for text in (js, html, css):
        assert "pt2vhfHillshadePane" not in text
        assert "World_Hillshade/MapServer/tile" not in text
        assert "hillshadeToggle" not in text
    assert "Relevo sombreado" not in html

    # CARTO endpoints must not be used by Light/Dark anymore.
    assert "basemaps.cartocdn.com" not in js
    assert "cartodb-basemaps" not in js
    assert "API KEY REQUIRED" not in js
    assert "API KEY REQUIRED" not in html

    # Keyless base maps.
    assert "tile.openstreetmap.org/{z}/{x}/{y}.png" in js
    assert "tile.opentopomap.org/{z}/{x}/{y}.png" in js
    assert "tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png" in js
    assert "tile.openstreetmap.fr/hot/{z}/{x}/{y}.png" in js
    assert "tile.openstreetmap.de/{z}/{x}/{y}.png" in js
    assert "tile.memomaps.de/tilegen/{z}/{x}/{y}.png" in js
    assert "World_Imagery/MapServer/tile" in js

    # Light/Dark are local visual styles over the standard OSM tiles.
    assert "grayscale(14%)" in js
    assert "invert(92%)" in js

    # Every new base is exposed in both quick and settings selectors.
    for value in ("cyclosm", "humanitarian", "osmde", "opnv"):
        assert html.count(f'value="{value}"') >= 2

    assert '{"osm", "topo", "light", "dark", "cyclosm", "humanitarian", "osmde", "opnv", "satellite"}' in db

    # Resiliency: repeated tile errors fall back to OSM and are logged.
    assert "layer.on('tileerror'" in js
    assert "state.baseLayerErrorCount < 3" in js
    assert "applyBaseMap('osm'" in js
    assert "/api/diagnostics/map-provider-error" in js
    assert '@app.post("/api/diagnostics/map-provider-error")' in web


def test_v181_tnc_rf_translations_follow_app_language():
    tnc = read("pt2vhf_aprs/static/js/tnc.js")
    app = read("pt2vhf_aprs/static/js/app.js")
    extra = read("pt2vhf_aprs/static/js/i18n_extra.js")

    assert "const TNC_I18N" in tnc
    assert "en:" in tnc
    assert "es:" in tnc
    assert "fr:" in tnc
    assert "pt2vhf-language-changed" in tnc
    assert "pt2vhf-language-changed" in app
    assert "translateTncStatic" in tnc
    assert "localizeBackendMessage" in tnc

    # Representative static/dynamic labels in all three non-PT languages.
    for needle in (
        "Refresh ports", "Actualizar puertos", "Actualiser les ports",
        "Who talks to whom", "Quién habla con quién", "Qui parle à qui",
        "Automatic TX off", "TX automático desactivado", "TX automatique désactivé",
        "TNC / RF settings saved.", "Configuración TNC / RF guardada.", "Configuration TNC / RF enregistrée.",
    ):
        assert needle in tnc

    # New map names/help must also be covered by the regular language dictionaries.
    assert "'Humanitário / HOT':'Humanitarian / HOT'" in app
    assert '"Humanitário / HOT": "Humanitario / HOT"' in extra
    assert '"Humanitário / HOT": "Humanitaire / HOT"' in extra


def test_v181_version():
    version = read("VERSION").strip()
    parts = tuple(int(item) for item in version.split("."))
    assert parts >= (1, 8, 1)
    assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
