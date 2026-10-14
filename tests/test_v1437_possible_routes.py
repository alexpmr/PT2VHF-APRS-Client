"""v1.14.37 — possible paths must never become fabricated RF links."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from pt2vhf_aprs import route_hypotheses as explorer
from pt2vhf_aprs import spacetime_topology as st
from pt2vhf_aprs import web


def _edge(a, b, a_pos, b_pos, when, level="direct"):
    ts = when.isoformat()
    event = {
        "id": 1, "timestamp": ts, "_epoch": when.timestamp(),
        "a_lat": a_pos[0], "a_lon": a_pos[1],
        "b_lat": b_pos[0], "b_lon": b_pos[1],
        "distance_km": 10.0, "evidence_level": level,
        "raw": "", "rx_fingerprint": "",
    }
    return {
        "a": a, "b": b, "events": [event],
        "packet_count": 1, "last_seen": ts, "distance_km": 10.0,
        "rf_transport_count": 1 if level == "direct" else 0,
        "rf_path_count": 1 if level == "inferred" else 0,
    }


def _graph(entries):
    graph = {}
    for a, b, edge in entries:
        graph.setdefault(a, {})[b] = edge
        graph.setdefault(b, {})[a] = edge
    return graph


def test_pt2ap_mobile_south_to_brasilia_not_proven_by_topological_graph(monkeypatch):
    now = datetime.now(timezone.utc)
    # Genuine local RF in two regions; it must NOT imply a continuous path.
    south = _edge("PY5SUL-9", "PT2AP-10", (-25.4, -49.2), (-25.39, -49.19),
                  now - timedelta(days=1))
    df = _edge("PT2AP-10", "PT2VHF", (-15.8, -47.9), (-15.79, -47.89), now)
    graph = _graph([
        ("PY5SUL-9", "PT2AP-10", south),
        ("PT2AP-10", "PT2VHF", df),
    ])
    monkeypatch.setattr(st, "_route_graph", lambda hours=0: (graph, {}))
    result = explorer.explore_possible_routes("PY5SUL-9", "PT2VHF", limit=4)
    assert result["searched_without_ranking_limit"]
    assert result["draw_hypotheses_on_map"] is False
    assert len(result["possible_routes"]) == 1
    candidate = result["possible_routes"][0]
    assert candidate["status"] == "hypothesis_only"
    assert candidate["draw_as_rf"] is False
    assert candidate["direct_rf_confirmed"] is False
    bridge = [b for b in candidate["blockers"] if b["code"] == "mobile_spatial_bridge"]
    assert bridge and bridge[0]["node"] == "PT2AP-10"
    assert bridge[0]["position_gap_km"] > 800
    assert candidate["nodes"] == ["PY5SUL-9", "PT2AP-10", "PT2VHF"]


def test_same_region_separated_in_time_is_only_historical(monkeypatch):
    now = datetime.now(timezone.utc)
    ab = _edge("PT2A", "PT2B", (-15.8, -47.9), (-15.81, -47.91),
               now - timedelta(days=2))
    bc = _edge("PT2B", "PT2C", (-15.81, -47.91), (-15.82, -47.92), now)
    graph = _graph([("PT2A", "PT2B", ab), ("PT2B", "PT2C", bc)])
    monkeypatch.setattr(st, "_route_graph", lambda hours=0: (graph, {}))
    result = explorer.explore_possible_routes("PT2A", "PT2C")
    assert len(result["possible_routes"]) == 1
    candidate = result["possible_routes"][0]
    # If the full evidence-chain validator accepts a spatially compatible
    # historical route, it must retain its *historical* class, not same_packet.
    assert candidate["status"] in {"historical_compatible", "hypothesis_only"}
    assert candidate["status"] != "same_packet"
    assert not candidate["draw_as_rf"]


def test_no_path_does_not_invent_igate_or_merge_ssids(monkeypatch):
    now = datetime.now(timezone.utc)
    edge = _edge("PT2AP-9", "PT2VHF", (-15.8, -47.9), (-15.79, -47.89), now)
    graph = _graph([("PT2AP-9", "PT2VHF", edge)])
    monkeypatch.setattr(st, "_route_graph", lambda hours=0: (graph, {}))
    result = explorer.explore_possible_routes("PT2AP-10", "PT2VHF")
    assert result["possible_routes"] == []


def test_web_endpoint_is_separate_and_rejects_missing_callsigns(monkeypatch):
    monkeypatch.setattr(web.scheduled_message_service, "start", lambda: None)
    monkeypatch.setattr(web.retention, "start_worker", lambda: None)
    client = web.create_app().test_client()
    result = client.get("/api/topology/rf-possible-routes")
    assert result.status_code == 400
    assert "error" in result.get_json()


def test_ui_hypotheses_do_not_create_map_segments():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    html = (root / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    assert 'id="rfPossibleRoutes"' in html
    assert "/api/topology/rf-possible-routes?source=" in js
    assert "Nenhuma hipótese é desenhada ou gravada como enlace" in js
    assert "rfPossibleRoutes: null" in js
    assert "mobile_spatial_bridge" in js
