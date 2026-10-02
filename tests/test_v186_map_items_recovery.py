from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v186_map_ver_controls_and_categories_are_present():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")

    for element_id in (
        "mapItemsButton",
        "mapItemsMenu",
        "mapViewTree",
        "mapViewSelectAllButton",
        "mapViewClearAllButton",
    ):
        assert f'id="{element_id}"' in html

    for label in (
        "root:stations",
        "root:digis",
        "root:igates",
        "root:objects",
        "root:tracklogs",
        "root:rf",
        "root:igate-links",
        "root:packets",
    ):
        assert label in js


def test_v186_map_tree_is_rendered_before_backend_data_arrives():
    js = read("pt2vhf_aprs/static/js/app.js")
    start = js.index("function addMapControls()")
    end = js.index("function syncMapLegendCollapsed()", start)
    block = js[start:end]

    assert "renderMapViewTree([], []);" in block
    assert block.index("renderMapViewTree([], []);") < block.index("const period = $('#mapPeriodHours');")


def test_v186_recovers_only_unintentional_all_disabled_visibility():
    js = read("pt2vhf_aprs/static/js/app.js")

    assert "function repairMapVisibilityStateV186()" in js
    assert "const allDisabled = keys.every(key => state[key] === false);" in js
    assert "pt2vhf_map_view_all_cleared" in js
    assert "allDisabled && !explicitlyCleared" in js
    assert "state.mapViewFilters = {};" in js
    assert "localStorage.setItem('pt2vhf_map_view_all_cleared', value ? '0' : '1');" in js


def test_v186_leaflet_resyncs_after_viewport_changes():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "_pt2vhfMapViewportSyncBound" in js
    assert "state.map.invalidateSize({ animate: false });" in js
    assert "window.addEventListener('resize', syncViewport);" in js
    assert "window.addEventListener('orientationchange', syncViewport);" in js


def test_v186_low_height_rules_do_not_change_global_map_geometry():
    css = read("pt2vhf_aprs/static/css/app.css")
    start = css.index("@media (max-height: 800px) and (min-width: 901px)")
    end = css.index(".required-fields-note", start)
    low_height = css[start:end]

    assert ".message-composer" in low_height
    assert ".station-popup" in low_height
    assert ".app-header {" not in low_height
    assert ".tabs {" not in low_height
    assert "body.map-context-visible main" not in low_height
    assert "main { height:" not in low_height


def test_v186_map_tree_survives_map_data_failure():
    js = read("pt2vhf_aprs/static/js/app.js")
    start = js.index("async function loadMapData()")
    end = js.index("function stationIsVisible", start)
    block = js[start:end]
    assert "if (tree && !tree.querySelector('.map-view-node')) renderMapViewTree([], []);" in block


def test_v186_version():
    assert read("VERSION").strip() == "1.8.6"
    assert '__version__ = "1.8.6"' in read("pt2vhf_aprs/__init__.py")
