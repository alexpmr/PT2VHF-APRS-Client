from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1414_version_metadata():
    version = read("VERSION").strip()
    assert tuple(int(part) for part in version.split(".")) >= (1, 14, 14)
    assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
    win = read("windows/version_info.txt")
    parts = tuple(int(part) for part in version.split("."))
    assert str(parts + (0,)) in win
    assert f"'{version}'" in win


def test_v1414_route_ui_uses_observed_rf_semantics():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "RF confirmado" not in js
    assert "confirmed RF" not in js
    assert "rf_confidence_label" not in js
    assert "rf_confidence_reason" not in js
    assert "RF observado" in js
    assert "Observed RF" in js
    assert "classification_source" in js


def test_v1414_manual_search_keeps_exclusive_focus():
    js = read("pt2vhf_aprs/static/js/app.js")
    start = js.index("async function applyRfRouteAnalysis()")
    end = js.index("function showTopologyHover", start)
    body = js[start:end]
    assert "const exclusiveNodes = new Set();" in body
    assert "state.rfRouteExclusiveNodes = exclusiveNodes;" in body
    assert "setTransientRouteFocusVisibility(false);" in body
    assert "await loadMapData();" in body
    assert "await loadTopology();" in body
    assert "fitRfRouteBounds(routes" in body


def test_v1414_observed_rf_backend_remains_permissive():
    database = read("pt2vhf_aprs/database.py")
    assert "RF_CONFIRMED_SHORT_KM" not in database
    assert "RF_CONFIRMED_MEDIUM_KM" not in database
    assert "RF_CONFIRMED_LONG_KM" not in database
    assert 'if not bool(edge.get("rf_confirmed"))' not in database


def test_v1414_statistics_still_uses_single_vertical_scroll():
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "#tab-analysis .client-version-stats-content" in css
    assert "#tab-analysis .rf-route-record-list" in css
    assert "overflow-y: visible !important;" in css
    assert "max-height: none !important;" in css
