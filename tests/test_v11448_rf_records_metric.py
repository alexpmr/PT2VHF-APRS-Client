"""#86: Recordes RF ordenáveis por distância direta ou percurso total."""
from pathlib import Path

from pt2vhf_aprs import spacetime_topology as st

ROOT = Path(__file__).resolve().parents[1]


def _edge(a, b, a_pos, b_pos):
    event = {"id": 1, "a_lat": a_pos[0], "a_lon": a_pos[1], "b_lat": b_pos[0], "b_lon": b_pos[1],
             "timestamp": "2026-10-18T10:00:00+00:00"}
    return {"a": a, "b": b}, event


def test_chain_distance_sums_each_hop():
    graph = {}
    events = []
    points = [("A", (-15.0, -48.0)), ("B", (-16.0, -48.0)), ("C", (-16.0, -47.0))]
    for (a, pa), (b, pb) in zip(points, points[1:]):
        edge, event = _edge(a, b, pa, pb)
        graph.setdefault(a, {})[b] = edge
        graph.setdefault(b, {})[a] = edge
        events.append(event)
    total = st._record_chain_distance(["A", "B", "C"], events, graph)
    hop1 = st.db.haversine_km(-15.0, -48.0, -16.0, -48.0)
    hop2 = st.db.haversine_km(-16.0, -48.0, -16.0, -47.0)
    assert abs(total - (hop1 + hop2)) < 1e-6
    direct = st.db.haversine_km(-15.0, -48.0, -16.0, -47.0)
    assert total > direct


def test_chain_distance_requires_positions():
    edge, event = _edge("A", "B", (-15.0, -48.0), (None, None))
    graph = {"A": {"B": edge}, "B": {"A": edge}}
    assert st._record_chain_distance(["A", "B"], [event], graph) is None


def test_metric_normalization_and_cache_separation():
    assert st._normalize_record_metric("PATH") == "path"
    assert st._normalize_record_metric("x") == "direct"
    assert st._normalize_record_metric(None) == "direct"


def test_api_and_ui_expose_metric():
    web = (ROOT / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")
    js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert 'metric = str(data.get("metric"' in web
    assert '"metric": str(job.get("metric") or "direct")' in web
    assert "data-rf-records-metric" in js
    assert "metric: state.rfRouteRecordsMetric === 'path' ? 'path' : 'direct'" in js
    assert "Percurso total (soma dos saltos)" in js


def test_records_job_api_accepts_metric(tmp_path, monkeypatch):
    from pt2vhf_aprs import database as db, web
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "metric.db")
    db.init_db()
    seen = {}

    def fake_records(**kwargs):
        seen.update(kwargs)
        return []

    monkeypatch.setattr(db, "list_rf_route_records", fake_records)
    job = web._start_rf_record_job(0, 10, 6, metric="path", force=True)
    assert job["metric"] == "path"
    import time
    for _ in range(50):
        if seen:
            break
        time.sleep(0.02)
    assert seen.get("metric") == "path"


def test_path_metric_ranks_curved_route_first():
    import tempfile
    from pt2vhf_aprs import database as db
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _station(conn, call, lat, lon):
        conn.execute("INSERT INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
                     (call, now, lat, lon))

    def add_edge(conn, source, target, packets):
        conn.execute(
            "INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen,igate,rf_transport_count)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (source, target, "rf", packets, now, now, None, packets),
        )

    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with db.connection() as conn:
                _station(conn, "PT2A", 10.0, 10.0)
                _station(conn, "PT2M1", 10.4, 10.0)
                _station(conn, "PT2M2", 10.4, 10.4)
                _station(conn, "PT2B", 10.0, 10.1)
                add_edge(conn, "PT2A", "PT2M1", 10)
                add_edge(conn, "PT2M1", "PT2M2", 10)
                add_edge(conn, "PT2M2", "PT2B", 10)
                _station(conn, "PT2C", 12.0, 10.0)
                _station(conn, "PT2D", 12.0, 10.8)
                add_edge(conn, "PT2C", "PT2D", 5)

            direct = db.list_rf_route_records(hours=24, limit=20, max_hops=6, metric="direct")
            path = db.list_rf_route_records(hours=24, limit=20, max_hops=6, metric="path")
            assert set(direct[0]["nodes"]) == {"PT2C", "PT2D"}
            assert {path[0]["source"], path[0]["target"]} == {"PT2A", "PT2B"}
            assert all(item["ranking_metric"] == "path" for item in path)
            lengths = [float(item["distance_km"]) for item in path]
            assert lengths == sorted(lengths, reverse=True)
    finally:
        db.DB_PATH = original
