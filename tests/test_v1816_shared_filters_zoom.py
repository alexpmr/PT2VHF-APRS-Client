from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1816_version_metadata_is_not_regressed():
    version = read("VERSION").strip()
    parts = tuple(int(item) for item in version.split("."))
    assert parts >= (1, 8, 16)
    assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
    win = read("windows/version_info.txt")
    assert "FileVersion" in win
    assert "ProductVersion" in win


def test_about_uses_pp5au():
    html = read("pt2vhf_aprs/templates/index.html")
    assert "<strong>PP5AU</strong><span>Adriano</span>" in html
    assert "PP5UA" not in html


def test_zoom_is_finer_and_wheel_is_more_gradual():
    js = read("pt2vhf_aprs/static/js/app.js")
    db = read("pt2vhf_aprs/database.py")
    assert "function mapZoomOptions(value)" in js
    assert "zoomSnap: zoomOptions.step" in js
    assert "zoomDelta: zoomOptions.step" in js
    assert "wheelPxPerZoomLevel: zoomOptions.wheelPxPerZoomLevel" in js
    assert "wheelDebounceTime: zoomOptions.wheelDebounceTime" in js
    assert '"map_zoom_step": 0.10' in db


def test_message_content_filters_are_one_pulldown_with_four_categories():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    assert 'id="messageContentFilterButton"' in html
    assert 'id="messageContentFilterMenu"' in html
    assert 'id="messageContentSelectAllButton"' in html
    assert 'id="messageContentClearAllButton"' in html
    for key in ("message", "bulletin", "group", "telemetry"):
        assert f'data-message-content-filter="{key}"' in html
    assert 'id="showNormalMessages"' not in html
    assert 'id="showBulletinMessages"' not in html
    assert 'id="hideTelemetryMessages"' not in html
    assert "function messageContentCategory(message)" in js
    assert "function setAllMessageContentFilters(enabled)" in js
    assert "pt2vhf_message_content_filters_v2" in js
    assert "state.showGroupMessages" in js
    assert "state.showTelemetryMessages" in js


def test_stations_and_messages_share_map_view_filters():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    for ident in (
        "stationViewButton", "stationViewMenu", "stationViewTree",
        "stationViewSelectAllButton", "stationViewClearAllButton",
        "messageViewButton", "messageViewMenu", "messageViewTree",
        "messageViewSelectAllButton", "messageViewClearAllButton",
    ):
        assert f'id="{ident}"' in html
    assert "function sharedStationViewNodes(stations = [])" in js
    assert "function renderAuxViewTrees(" in js
    assert "function bindSharedViewTree(" in js
    assert "function setAllSharedStationView(" in js
    assert "['#mapViewTree', '#stationViewTree', '#messageViewTree']" in js
    assert "stationMatchesViewFilter" in js


def test_messages_use_station_catalog_and_keep_unknowns_visible():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "stationCatalog: []" in js
    assert "function messageRelevantStations(message)" in js
    assert "function messageMatchesStationView(message)" in js
    assert "if (!stations.length) return true;" in js
    assert "state.stationCatalog.length ? state.stationCatalog : state.stations" in js
    assert "messageContentCategoryEnabled(message) && messageMatchesStationView(message)" in js


def test_shared_view_tree_only_active_tree_updates_parent_state():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "function syncSingleViewTreeCheckboxes(tree, updateState = false)" in js
    assert "syncSingleViewTreeCheckboxes(tree, true);" in js
    assert "syncSingleViewTreeCheckboxes($(selector), false);" in js
