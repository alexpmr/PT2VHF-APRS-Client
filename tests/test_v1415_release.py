from pathlib import Path

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def edge(*, direct: int = 0, inferred: int = 0, packets: int = 1, distance: float = 10.0):
    return {
        "packet_count": packets,
        "rf_transport_count": direct,
        "rf_path_count": inferred,
        "distance_km": distance,
        "first_seen": "2026-10-09T10:00:00Z",
        "last_seen": "2026-10-09T11:00:00Z",
        "classification_source": "RF recebido" if direct else "RF inferido do path",
    }


def connect(graph, a: str, b: str, payload):
    graph.setdefault(a, {})[b] = payload
    graph.setdefault(b, {})[a] = payload


def test_v1415_version_metadata():
    assert read("VERSION").strip() == "1.14.15"
    assert '__version__ = "1.14.15"' in read("pt2vhf_aprs/__init__.py")
    assert "(1, 14, 15, 0)" in read("windows/version_info.txt")


def test_v1415_eligible_corridor_keeps_all_rf_links_that_can_join_route():
    graph = {}
    positions = {
        "A": (0.0, 0.0),
        "B": (0.0, 1.0),
        "C": (1.0, 1.0),
        "D": (1.0, 2.0),
    }
    connect(graph, "A", "B", edge(direct=3))
    connect(graph, "B", "D", edge(direct=3))
    connect(graph, "A", "C", edge(direct=2))
    connect(graph, "C", "D", edge(direct=2))
    connect(graph, "B", "C", edge(inferred=4))

    rows = db._rf_route_eligible_edges("A", "D", graph, positions, 3)
    pairs = {tuple(sorted((item["source"], item["target"]))) for item in rows}
    assert pairs == {
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
        ("B", "D"),
        ("C", "D"),
    }


def test_v1415_route_search_prefers_direct_evidence_without_distance_veto():
    graph = {}
    positions = {
        "A": (0.0, 0.0),
        "X": (0.0, 1.0),
        "B": (1.0, 0.0),
        "C": (1.0, 1.0),
        "D": (1.0, 2.0),
    }
    connect(graph, "A", "X", edge(inferred=10, packets=10, distance=600.0))
    connect(graph, "X", "D", edge(inferred=10, packets=10, distance=600.0))
    connect(graph, "A", "B", edge(direct=2, packets=2, distance=450.0))
    connect(graph, "B", "C", edge(direct=2, packets=2, distance=450.0))
    connect(graph, "C", "D", edge(direct=2, packets=2, distance=450.0))

    routes, truncated, expanded = db._rf_k_best_routes("A", "D", graph, positions, 2, 4)
    assert truncated is False
    assert expanded > 0
    assert len(routes) == 2
    assert routes[0]["nodes"] == ["A", "B", "C", "D"]
    assert routes[0]["direct_edges"] == 3
    assert routes[0]["inferred_edges"] == 0
    assert routes[1]["nodes"] == ["A", "X", "D"]
    assert routes[1]["inferred_edges"] == 2


def test_v1415_long_direct_rf_edge_is_not_rejected_by_distance():
    graph = {}
    positions = {"A": (-15.0, -47.0), "D": (-23.0, -46.0)}
    connect(graph, "A", "D", edge(direct=1, packets=1, distance=900.0))
    routes, truncated, _expanded = db._rf_k_best_routes("A", "D", graph, positions, 3, 3)
    assert truncated is False
    assert len(routes) == 1
    assert routes[0]["nodes"] == ["A", "D"]
    assert routes[0]["edges"][0]["distance_km"] == 900.0
    assert routes[0]["edges"][0]["evidence_level"] == "direct"


def test_v1415_list_routes_returns_full_eligible_corridor(monkeypatch):
    graph = {}
    positions = {
        "A": (0.0, 0.0),
        "B": (0.0, 1.0),
        "C": (1.0, 1.0),
        "D": (1.0, 2.0),
    }
    connect(graph, "A", "B", edge(direct=4))
    connect(graph, "B", "D", edge(direct=4))
    connect(graph, "A", "C", edge(direct=3))
    connect(graph, "C", "D", edge(direct=3))
    connect(graph, "B", "C", edge(inferred=2))
    monkeypatch.setattr(db, "_rf_route_graph", lambda hours=0: (graph, positions))

    payload = db.list_rf_routes("A", "D", hours=24, max_routes=3, max_hops=3)
    assert payload["graph_edge_count"] == 5
    assert payload["eligible_edge_count"] == 5
    assert len(payload["eligible_edges"]) == 5
    assert payload["search_truncated"] is False
    assert set(payload["eligible_nodes"]) == {"A", "B", "C", "D"}
    assert payload["routes"]


def test_v1415_frontend_uses_eligible_edges_and_twelve_hop_horizon():
    js = read("pt2vhf_aprs/static/js/app.js")
    web = read("pt2vhf_aprs/web.py")
    assert "analysis.eligible_edges || []" in js
    assert "payload.eligible_nodes || []" in js
    assert "fitRfRouteBounds(routes, payload.eligible_edges || [])" in js
    assert "&max_routes=12&max_hops=12" in js
    assert "routeEvidence?.evidence_level === 'inferred'" in js
    assert "inferredRouteEdge ? '5 5'" in js
    assert 'request.args.get("max_hops", 12)' in web


def test_v1415_old_premature_route_cutoff_is_gone():
    database = read("pt2vhf_aprs/database.py")
    assert "len(found) >= route_limit * 4" not in database
    assert "def _rf_k_best_routes(" in database
    assert "def _rf_route_eligible_edges(" in database
