from pathlib import Path

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v183_aprs_application_device_classification():
    assert db._aprs_client_category(db.resolve_aprs_device_id("APZVHF")) == "application"
    assert db._aprs_client_category(db.resolve_aprs_device_id("APDW18")) == "application"
    assert db._aprs_client_category(db.resolve_aprs_device_id("APDR16")) == "application"
    assert db._aprs_client_category(db.resolve_aprs_device_id("API510")) == "device"
    assert db._aprs_client_category(db.resolve_aprs_device_id("APK004")) == "device"
    assert db._aprs_client_category(db.resolve_aprs_device_id("APT3A1")) == "device"
    assert db._aprs_client_category(db.resolve_aprs_device_id("ZZZZZZ")) == "unknown"


def test_v183_statistics_filter_controls_and_visible_percent_logic():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    database = read("pt2vhf_aprs/database.py")

    for control in ("clientStatsShowApps", "clientStatsShowDevices", "clientStatsShowUnknown"):
        assert f'id="{control}"' in html

    assert "pt2vhf_stats_show_apps" in js
    assert "pt2vhf_stats_show_devices" in js
    assert "pt2vhf_stats_show_unknown" in js
    assert "clientStatsCategoryVisible" in js
    assert "const visibleTotal = candidates.reduce" in js
    assert "Number(item.stations || 0) / visibleTotal" in js
    assert "showCategoryColumn = enabledCategories.length > 1" in js

    assert "APRS_APPLICATION_CLASSES" in database
    assert "APRS_DEVICE_CLASSES" in database
    assert '"category": category' in database
    assert '"category_counts"' in database


def test_v183_map_view_select_all_and_clear_all():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")

    assert 'id="mapViewSelectAllButton"' in html
    assert 'id="mapViewClearAllButton"' in html
    assert 'id="mapViewAllButton"' not in html
    assert "function setAllMapView(enabled)" in js
    assert "setAllMapView(true)" in js
    assert "setAllMapView(false)" in js
    assert "for (const key of Object.keys(MAP_VIEW_STATE_STORAGE)) setMapViewState(key, value)" in js
    assert "persistMapViewFilters()" in js


def test_v183_translations_cover_new_controls():
    app = read("pt2vhf_aprs/static/js/app.js")
    extra = read("pt2vhf_aprs/static/js/i18n_extra.js")

    for text in (
        "Show APRS applications",
        "Show devices",
        "Show unidentified",
        "Select all",
        "Clear all",
        "APRS application",
        "Device / Hardware",
    ):
        assert text in app

    for text in (
        "Mostrar aplicaciones APRS",
        "Afficher les applications APRS",
        "Seleccionar todo",
        "Tout sélectionner",
    ):
        assert text in extra


def test_v183_version():
    version = read("VERSION").strip()
    assert version in {"1.8.2", "1.8.3"}
