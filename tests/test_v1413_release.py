from __future__ import annotations

from pathlib import Path

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1413_long_observed_rf_edge_remains_in_graph(monkeypatch):
    rows = [
        {
            "source": "PT2AAA",
            "target": "PY2BBB",
            "kind": "rf",
            "packet_count": 1,
            "rf_transport_count": 1,
            "rf_path_count": 0,
            "internet_confirmed_count": 0,
            "source_lat": -15.0,
            "source_lon": -47.0,
            "target_lat": -23.5,
            "target_lon": -46.6,
            "first_seen": "2026-10-08T10:00:00Z",
            "last_seen": "2026-10-08T10:00:00Z",
            "classification_source": "RF recebido",
        }
    ]
    monkeypatch.setattr(db, "list_topology_edges", lambda hours=0: rows)
    graph, _positions = db._rf_route_graph(0)
    assert "PY2BBB" in graph["PT2AAA"]


def test_v1413_aprsis_edge_does_not_complete_rf_graph(monkeypatch):
    rows = [
        {
            "source": "PT2AAA",
            "target": "PY2BBB",
            "kind": "igate",
            "packet_count": 20,
            "rf_transport_count": 0,
            "rf_path_count": 0,
            "internet_confirmed_count": 20,
            "source_lat": -15.7,
            "source_lon": -47.9,
            "target_lat": -15.8,
            "target_lon": -47.8,
            "first_seen": "2026-10-08T10:00:00Z",
            "last_seen": "2026-10-08T10:05:00Z",
        }
    ]
    monkeypatch.setattr(db, "list_topology_edges", lambda hours=0: rows)
    graph, _positions = db._rf_route_graph(0)
    assert graph == {}


def test_v1413_manual_route_search_uses_exclusive_ranking_focus():
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


def test_v1413_removed_v1412_rf_exclusion_thresholds():
    database = read("pt2vhf_aprs/database.py")
    assert "RF_CONFIRMED_SHORT_KM" not in database
    assert "RF_CONFIRMED_MEDIUM_KM" not in database
    assert "RF_CONFIRMED_LONG_KM" not in database
    assert 'if not bool(edge.get("rf_confirmed"))' not in database


def test_v1413_statistics_has_no_internal_vertical_scroll():
    css = read("pt2vhf_aprs/static/css/app.css")
    marker = "v1.14.13 - Estatísticas em fluxo contínuo"
    assert marker in css
    section = css[css.index(marker):]
    assert "overflow-y: visible !important;" in section
    assert "max-height: none !important;" in section
