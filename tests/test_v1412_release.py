from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v1412_draggable_route_panel_feature_is_preserved():
    js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (ROOT / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    assert "bindRfRoutePanelDrag" in js
    assert "setPointerCapture" in js
    assert "clampRfRoutePanelPosition" in js
    assert ".rf-route-panel.dragging" in css
    assert "Math.max(0, Math.min(Number(left) || 0, maxLeft))" in js
    assert "Math.max(0, Math.min(Number(top) || 0, maxTop))" in js


def test_v1412_statistics_no_vertical_internal_scroll_is_preserved():
    css = (ROOT / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    required = [
        "#tab-analysis .topology-stats-box",
        "#tab-analysis .topology-stats-content",
        "#tab-analysis .topology-stat-group",
        "#tab-analysis .analysis-client-version-panel",
        "#tab-analysis .client-version-stats-content",
        "#tab-analysis .station-ranking-table-wrap",
        "#tab-analysis .rf-route-record-list",
    ]
    for marker in required:
        assert marker in css
    assert "max-height: none !important;" in css
    assert "overflow-y: visible !important;" in css


def test_v1412_rf_confidence_gate_is_superseded_by_v1413():
    database = (ROOT / "pt2vhf_aprs" / "database.py").read_text(encoding="utf-8")
    assert "RF_CONFIRMED_SHORT_KM" not in database
    assert "RF_CONFIRMED_MEDIUM_KM" not in database
    assert "RF_CONFIRMED_LONG_KM" not in database
    assert 'if not bool(edge.get("rf_confirmed"))' not in database
