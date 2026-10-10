from datetime import datetime
from pathlib import Path

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def event(ts: str, a_pos, b_pos, level: str = "inferred", event_id: int = 1):
    return {
        "id": event_id,
        "timestamp": ts,
        "_epoch": datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp(),
        "a_lat": a_pos[0],
        "a_lon": a_pos[1],
        "b_lat": b_pos[0],
        "b_lon": b_pos[1],
        "evidence_level": level,
    }


def edge(a: str, b: str, events):
    direct = sum(1 for item in events if item["evidence_level"] == "direct")
    inferred = sum(1 for item in events if item["evidence_level"] == "inferred")
    return {
        "a": min(a, b),
        "b": max(a, b),
        "events": list(events),
        "packet_count": len(events),
        "rf_transport_count": direct,
        "rf_path_count": inferred,
        "first_seen": events[0]["timestamp"],
        "last_seen": events[-1]["timestamp"],
        "distance_km": events[-1].get("distance_km", 0.0),
        "classification_source": "RF direto do transporte" if direct else "RF inferido do path",
    }


def connect(graph, a: str, b: str, payload):
    graph.setdefault(a, {})[b] = payload
    graph.setdefault(b, {})[a] = payload


def test_v1419_version_and_overlay_are_active():
    version = tuple(int(part) for part in read("VERSION").strip().split("."))
    assert version >= (1, 14, 19)
    assert "spacetime_topology.install()" in read("pt2vhf_aprs/__init__.py")
    assert db.RF_INFERRED_REFINEMENT_WINDOW_HOURS > 0


def test_v1419_pt2ap_trip_cannot_bridge_itumbiara_and_south():
    graph = {}
    inbound = edge(
        "PP2ITG-15",
        "PT2AP-10",
        [event(
            "2026-10-09T01:25:46+00:00",
            (-18.3675, -49.1973),
            (-18.42, -49.16),
            event_id=1,
        )],
    )
    outbound = edge(
        "PT2AP-10",
        "PY5CTV-13",
        [event(
            "2026-10-09T16:35:40+00:00",
            (-25.30, -49.20),
            (-25.40, -49.10),
            event_id=2,
        )],
    )
    connect(graph, "PP2ITG-15", "PT2AP-10", inbound)
    connect(graph, "PT2AP-10", "PY5CTV-13", outbound)

    positions = {
        "PP2ITG-15": (-18.3675, -49.1973),
        "PT2AP-10": (-25.30, -49.20),
        "PY5CTV-13": (-25.40, -49.10),
    }
    assert db._rf_route_payload(
        ["PP2ITG-15", "PT2AP-10", "PY5CTV-13"],
        graph,
        positions,
        refine_inferred=False,
    ) is None


def test_v1419_mobile_node_must_be_spatially_coherent_even_inside_time_window():
    graph = {}
    connect(
        graph,
        "A",
        "MOBILE-10",
        edge("A", "MOBILE-10", [
            event("2026-10-09T10:00:00+00:00", (-18.0, -49.0), (-18.1, -49.0), event_id=1),
        ]),
    )
    connect(
        graph,
        "MOBILE-10",
        "B",
        edge("MOBILE-10", "B", [
            event("2026-10-09T10:10:00+00:00", (-25.0, -49.0), (-25.1, -49.0), event_id=2),
        ]),
    )
    positions = {"A": (-18.0, -49.0), "MOBILE-10": (-25.0, -49.0), "B": (-25.1, -49.0)}
    assert db._rf_route_payload(["A", "MOBILE-10", "B"], graph, positions, refine_inferred=False) is None


def test_v1419_historical_edge_distance_uses_event_position_not_latest_station_position():
    graph = {}
    historical = event(
        "2026-10-09T01:25:46+00:00",
        (-18.3675, -49.1973),
        (-18.42, -49.16),
        event_id=1,
    )
    connect(graph, "PP2ITG-15", "PT2AP-10", edge("PP2ITG-15", "PT2AP-10", [historical]))

    # Posição mais recente do móvel centenas de quilômetros ao sul.
    positions = {
        "PP2ITG-15": (-18.3675, -49.1973),
        "PT2AP-10": (-25.54117, -49.18350),
    }
    payload = db._rf_route_payload(
        ["PP2ITG-15", "PT2AP-10"],
        graph,
        positions,
        refine_inferred=False,
    )
    assert payload is not None
    assert payload["spatiotemporal_validated"] is True
    assert payload["distance_km"] < 20.0
    assert payload["direct_distance_km"] < 20.0
    assert payload["edges"][0]["target_lat"] == historical["b_lat"]


def test_v1419_contemporary_route_is_accepted_and_reports_window():
    graph = {}
    connect(
        graph,
        "A",
        "D-1",
        edge("A", "D-1", [
            event("2026-10-09T10:00:00+00:00", (-15.0, -47.0), (-15.1, -47.0), "direct", 1),
        ]),
    )
    connect(
        graph,
        "D-1",
        "B",
        edge("D-1", "B", [
            event("2026-10-09T10:08:00+00:00", (-15.1, -47.0), (-15.2, -47.0), "direct", 2),
        ]),
    )
    positions = {"A": (-15.0, -47.0), "D-1": (-15.1, -47.0), "B": (-15.2, -47.0)}
    payload = db._rf_route_payload(["A", "D-1", "B"], graph, positions, refine_inferred=False)
    assert payload is not None
    assert payload["spatiotemporal_validated"] is True
    assert payload["temporal_span_minutes"] == 8.0
    assert payload["route_evidence_start"].startswith("2026-10-09T10:00:00")
    assert payload["route_evidence_end"].startswith("2026-10-09T10:08:00")
