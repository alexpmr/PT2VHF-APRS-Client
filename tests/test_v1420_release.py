from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from pt2vhf_aprs import database as db
from pt2vhf_aprs.web import KML_NS, _kml_document, _split_track_rows

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def event(ts: str, a_pos, b_pos, level: str = "direct", event_id: int = 1, raw: str = ""):
    distance = db.haversine_km(a_pos[0], a_pos[1], b_pos[0], b_pos[1])
    return {
        "id": event_id,
        "timestamp": ts,
        "_epoch": datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp(),
        "a_lat": a_pos[0],
        "a_lon": a_pos[1],
        "b_lat": b_pos[0],
        "b_lon": b_pos[1],
        "distance_km": distance,
        "evidence_level": level,
        "raw": raw,
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
        "distance_km": events[-1]["distance_km"],
        "classification_source": "RF direto do transporte" if direct else "RF inferido do path",
    }


def connect(graph, a: str, b: str, payload):
    graph.setdefault(a, {})[b] = payload
    graph.setdefault(b, {})[a] = payload


def test_v1420_version_and_release_markers():
    version_text = read("VERSION").strip()
    version = tuple(int(part) for part in version_text.split("."))
    assert version >= (1, 14, 20)
    assert f'__version__ = "{version_text}"' in read("pt2vhf_aprs/__init__.py")
    overlay = read("pt2vhf_aprs/spacetime_topology.py")
    assert "SHARED_NODE_COMPATIBILITY_KM = 25.0" in overlay
    assert 'payload["route_semantics"] = "historical_reachability"' in overlay
    app = read("pt2vhf_aprs/static/js/app.js")
    assert "TRACKLOG_MAX_GAP_MS = 30 * 60_000" in app
    assert "temporalGap" in app


def test_v1420_historical_links_can_form_reachability_route():
    graph = {}
    connect(
        graph,
        "A",
        "B",
        edge("A", "B", [
            event("2026-10-08T10:00:00+00:00", (-15.0, -47.0), (-15.1, -47.0), event_id=1),
        ]),
    )
    connect(
        graph,
        "B",
        "C",
        edge("B", "C", [
            event("2026-10-10T12:00:00+00:00", (-15.1, -47.0), (-15.2, -47.0), event_id=2),
        ]),
    )
    positions = {"A": (-15.0, -47.0), "B": (-15.1, -47.0), "C": (-15.2, -47.0)}
    payload = db._rf_route_payload(["A", "B", "C"], graph, positions, refine_inferred=False)
    assert payload is not None
    assert payload["nodes"] == ["A", "B", "C"]
    assert payload["reachability_class"] == "historical"
    assert payload["historical_reachability"] is True
    assert payload["hops"] == 2


def test_v1420_mobile_relay_uses_contact_coordinates_and_cannot_bridge_trip():
    graph = {}
    connect(
        graph,
        "A",
        "B",
        edge("A", "B", [
            event("2026-10-08T10:00:00+00:00", (-18.3, -49.2), (-18.4, -49.2), event_id=1),
        ]),
    )
    connect(
        graph,
        "B",
        "C",
        edge("B", "C", [
            event("2026-10-10T12:00:00+00:00", (-25.5, -49.2), (-25.6, -49.2), event_id=2),
        ]),
    )
    positions = {"A": (-18.3, -49.2), "B": (-25.5, -49.2), "C": (-25.6, -49.2)}
    assert db._rf_route_payload(["A", "B", "C"], graph, positions, refine_inferred=False) is None


def test_v1420_historical_edge_distance_ignores_current_mobile_position():
    graph = {}
    old_event = event(
        "2026-10-08T10:00:00+00:00",
        (-18.3675, -49.1973),
        (-18.42, -49.16),
        event_id=1,
    )
    connect(graph, "A", "B", edge("A", "B", [old_event]))
    positions = {"A": (-18.3675, -49.1973), "B": (-25.54117, -49.18350)}
    payload = db._rf_route_payload(["A", "B"], graph, positions, refine_inferred=False)
    assert payload is not None
    assert payload["distance_km"] < 20.0
    assert payload["edges"][0]["target_lat"] == old_event["b_lat"]


def test_v1420_long_inferred_edge_is_not_a_direct_physical_hop():
    graph = {}
    long_event = event(
        "2026-10-08T05:29:48+00:00",
        (-34.60, -58.38),
        (-23.55, -46.63),
        level="inferred",
        event_id=1,
    )
    connect(graph, "LU9DCE", "PU2XTC-4", edge("LU9DCE", "PU2XTC-4", [long_event]))
    positions = {"LU9DCE": (-34.60, -58.38), "PU2XTC-4": (-23.55, -46.63)}
    assert db._rf_route_payload(
        ["LU9DCE", "PU2XTC-4"],
        graph,
        positions,
        refine_inferred=False,
    ) is None


def test_v1420_long_reachability_can_be_composed_from_observed_hops():
    graph = {}
    connect(graph, "A", "B", edge("A", "B", [
        event("2026-10-01T10:00:00+00:00", (-30.0, -52.0), (-28.0, -51.0), event_id=1),
    ]))
    connect(graph, "B", "C", edge("B", "C", [
        event("2026-10-04T10:00:00+00:00", (-28.0, -51.0), (-25.0, -49.0), event_id=2),
    ]))
    connect(graph, "C", "D", edge("C", "D", [
        event("2026-10-09T10:00:00+00:00", (-25.0, -49.0), (-23.5, -46.6), event_id=3),
    ]))
    positions = {
        "A": (-30.0, -52.0),
        "B": (-28.0, -51.0),
        "C": (-25.0, -49.0),
        "D": (-23.5, -46.6),
    }
    payload = db._rf_route_payload(["A", "B", "C", "D"], graph, positions, refine_inferred=False)
    assert payload is not None
    assert payload["reachability_class"] == "historical"
    assert payload["nodes"] == ["A", "B", "C", "D"]
    assert payload["hops"] == 3


def test_v1420_tracklog_gap_splits_even_when_points_are_nearby():
    rows = [
        {"callsign": "T-1", "timestamp": "2026-10-10T10:00:00+00:00", "latitude": -15.80, "longitude": -47.90},
        {"callsign": "T-1", "timestamp": "2026-10-10T10:05:00+00:00", "latitude": -15.81, "longitude": -47.91},
        {"callsign": "T-1", "timestamp": "2026-10-10T12:00:00+00:00", "latitude": -15.82, "longitude": -47.92},
        {"callsign": "T-1", "timestamp": "2026-10-10T12:05:00+00:00", "latitude": -15.83, "longitude": -47.93},
    ]
    segments = _split_track_rows(rows)
    assert len(segments) == 2
    assert [len(segment) for segment in segments] == [2, 2]


def test_v1420_kml_does_not_draw_across_tracker_shutdown_gap():
    rows = [
        {"callsign": "T-1", "timestamp": "2026-10-10T10:00:00+00:00", "latitude": -15.80, "longitude": -47.90},
        {"callsign": "T-1", "timestamp": "2026-10-10T10:05:00+00:00", "latitude": -15.81, "longitude": -47.91},
        {"callsign": "T-1", "timestamp": "2026-10-10T12:00:00+00:00", "latitude": -15.54, "longitude": -47.33},
        {"callsign": "T-1", "timestamp": "2026-10-10T12:05:00+00:00", "latitude": -15.55, "longitude": -47.32},
    ]
    raw = _kml_document(
        {"stations": [], "tracks": rows, "topology": []},
        include_stations=False,
        include_positions=False,
        include_tracklogs=True,
        include_topology=False,
    )
    root = ET.fromstring(raw)
    ns = {"k": KML_NS}
    lines = root.findall(".//k:LineString", ns)
    assert len(lines) == 2
    coordinate_sets = [
        (line.find("k:coordinates", ns).text or "").strip()
        for line in lines
    ]
    assert all(len(coords.split()) == 2 for coords in coordinate_sets)
