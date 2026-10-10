from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db
from pt2vhf_aprs import spacetime_topology as st
from pt2vhf_aprs import web

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _event(ts: str, a_pos, b_pos, event_id: int):
    return {
        "id": event_id,
        "timestamp": ts,
        "_epoch": datetime.fromisoformat(ts).timestamp(),
        "a_lat": a_pos[0],
        "a_lon": a_pos[1],
        "b_lat": b_pos[0],
        "b_lon": b_pos[1],
        "distance_km": db.haversine_km(*a_pos, *b_pos),
        "evidence_level": "direct",
        "medium": "RF",
        "raw": f"event-{event_id}",
        "rx_fingerprint": "",
    }


def _edge(a: str, b: str, event):
    return {
        "a": min(a, b),
        "b": max(a, b),
        "packet_count": 1,
        "first_seen": event["timestamp"],
        "last_seen": event["timestamp"],
        "distance_km": event["distance_km"],
        "classification_source": "RF direto do transporte",
        "rf_transport_count": 1,
        "rf_path_count": 0,
        "events": [event],
    }


def _connect(graph, a: str, b: str, edge):
    graph.setdefault(a, {})[b] = edge
    graph.setdefault(b, {})[a] = edge


def test_v1422_version_and_markers():
    assert read("VERSION").strip() == "1.14.22"
    assert '__version__ = "1.14.22"' in read("pt2vhf_aprs/__init__.py")
    app = read("pt2vhf_aprs/static/js/app.js")
    html = read("pt2vhf_aprs/templates/index.html")
    web_source = read("pt2vhf_aprs/web.py")
    windows = read("windows_app.py")
    make_icon = read("windows/make_icon.py")

    assert 'id="topologyJsonExportButton"' in html
    assert "exportTopologyJson" in app
    assert "/api/export/topology-json" in app
    assert '@app.get("/api/export/topology-json")' in web_source
    assert "SetCurrentProcessExplicitAppUserModelID" in windows
    assert 'SOURCE = ROOT / "windows" / "aprs_taskbar_icon.png"' in make_icon


def test_v1422_rf_records_keep_multihop_reachability(monkeypatch):
    positions = {
        "A": (-16.0, -49.0),
        "B": (-16.5, -48.7),
        "C": (-17.0, -48.2),
        "D": (-17.5, -47.7),
    }
    graph = {}
    ts = "2026-10-10T12:00:00+00:00"
    direct = _event(ts, positions["A"], positions["D"], 1)
    _connect(graph, "A", "D", _edge("A", "D", direct))

    e2 = _event(ts, positions["A"], positions["B"], 2)
    e3 = _event(ts, positions["B"], positions["C"], 3)
    e4 = _event(ts, positions["C"], positions["D"], 4)
    _connect(graph, "A", "B", _edge("A", "B", e2))
    _connect(graph, "B", "C", _edge("B", "C", e3))
    _connect(graph, "C", "D", _edge("C", "D", e4))

    monkeypatch.setattr(st, "_route_graph", lambda hours=0: (graph, positions))
    records = st._route_records(0, limit=20, max_hops=6, beam_width=500)
    record = next(item for item in records if {item["source"], item["target"]} == {"A", "D"})
    assert record["hops"] == 3
    assert record["multihop"] is True
    assert record["nodes"] in (["A", "B", "C", "D"], ["D", "C", "B", "A"])


def test_v1422_legacy_topology_edge_survives_without_event_rows():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "legacy.db"
            db.init_db()
            ts = "2026-10-01T12:00:00+00:00"
            with db.connection() as conn:
                conn.execute(
                    "INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2A", ts, -16.68, -49.25),
                )
                conn.execute(
                    "INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2B", ts, -17.74, -48.63),
                )
                conn.execute(
                    "INSERT INTO tracks(callsign,timestamp,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2A", ts, -16.68, -49.25),
                )
                conn.execute(
                    "INSERT INTO tracks(callsign,timestamp,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2B", ts, -17.74, -48.63),
                )
                conn.execute(
                    """INSERT INTO topology_edges(
                           source,target,kind,packet_count,first_seen,last_seen,igate,
                           rf_transport_count,rf_path_count,internet_confirmed_count
                       ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    ("PT2A", "PT2B", "rf", 3, ts, ts, None, 3, 0, 0),
                )

            graph, _positions = st._build_route_graph_uncached(0)
            assert "PT2B" in graph.get("PT2A", {})
            assert graph["PT2A"]["PT2B"].get("legacy_fallback") is True
    finally:
        db.DB_PATH = original
        with st._graph_cache_lock:
            st._graph_cache.clear()
            st._graph_builds.clear()
            st._graph_build_errors.clear()


def test_v1422_json_diagnostic_contains_topology_without_secrets():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "diagnostic.db"
            db.init_db()
            ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            with db.connection() as conn:
                conn.execute(
                    "INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2A", ts, -15.8, -47.9),
                )
                conn.execute(
                    "INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2B", ts, -15.9, -47.8),
                )
                conn.execute(
                    "INSERT INTO tracks(callsign,timestamp,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2A", ts, -15.8, -47.9),
                )
                conn.execute(
                    "INSERT INTO tracks(callsign,timestamp,latitude,longitude) VALUES(?,?,?,?)",
                    ("PT2B", ts, -15.9, -47.8),
                )
                conn.execute(
                    """INSERT INTO topology_edges(
                           source,target,kind,packet_count,first_seen,last_seen,igate,
                           rf_transport_count,rf_path_count,internet_confirmed_count
                       ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    ("PT2A", "PT2B", "rf", 2, ts, ts, None, 2, 0, 0),
                )

            payload = web._topology_diagnostic_payload(0, full=True)
            assert payload["schema_version"] == "pt2vhf-topology-diagnostic-1"
            assert payload["mode"] == "full"
            assert payload["stations"]
            assert payload["topology_edges_raw"]
            serialized_keys = " ".join(payload.keys()).lower()
            assert "passcode" not in serialized_keys
            assert "token" not in serialized_keys
            assert "password" not in serialized_keys
    finally:
        db.DB_PATH = original


def test_v1422_marker_filters_do_not_hide_links():
    app = read("pt2vhf_aprs/static/js/app.js")
    load_start = app.index("async function loadTopology()")
    load_end = app.index("function locateBrowser", load_start)
    section = app[load_start:load_end]
    assert "filtros de estações/objetos controlam somente os" in section
    assert "mapVisibleCallsigns.has(sourceCall)" not in section
    assert "mapVisibleCallsigns.has(targetCall)" not in section
