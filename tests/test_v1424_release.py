from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time

from pt2vhf_aprs import database as db
from pt2vhf_aprs import spacetime_topology as st
from pt2vhf_aprs import web

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def event(ts: str, a_pos, b_pos, event_id: int):
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


def edge(a: str, b: str, ev):
    aa, bb = sorted((a, b))
    if a == aa:
        normalized = ev
    else:
        normalized = dict(ev)
        normalized["a_lat"], normalized["b_lat"] = ev["b_lat"], ev["a_lat"]
        normalized["a_lon"], normalized["b_lon"] = ev["b_lon"], ev["a_lon"]
    return {
        "a": aa,
        "b": bb,
        "packet_count": 1,
        "first_seen": ev["timestamp"],
        "last_seen": ev["timestamp"],
        "distance_km": ev["distance_km"],
        "classification_source": "RF direto do transporte",
        "rf_transport_count": 1,
        "rf_path_count": 0,
        "events": [normalized],
    }


def connect(graph, a: str, b: str, ev):
    payload = edge(a, b, ev)
    graph.setdefault(a, {})[b] = payload
    graph.setdefault(b, {})[a] = payload


def clear_record_cache():
    with st._rf_records_cache_lock:
        st._rf_records_cache.clear()
        st._rf_records_builds.clear()
        st._rf_records_errors.clear()


def test_v1424_version_and_feature_markers():
    assert read("VERSION").strip() == "1.14.24"
    assert '__version__ = "1.14.24"' in read("pt2vhf_aprs/__init__.py")

    overlay = read("pt2vhf_aprs/spacetime_topology.py")
    web_source = read("pt2vhf_aprs/web.py")
    app = read("pt2vhf_aprs/static/js/app.js")
    html = read("pt2vhf_aprs/templates/index.html")
    css = read("pt2vhf_aprs/static/css/app.css")

    for marker in (
        "RF_RECORDS_CACHE_SECONDS",
        "def _route_records_uncached(",
        "selected_events_override",
        "RF_RECORD_MAX_EXPANSIONS_PER_SOURCE",
        "rf_route_records_build",
    ):
        assert marker in overlay

    for marker in (
        '@app.post("/api/topology/rf-records/jobs")',
        '@app.get("/api/topology/rf-records/jobs/<job_id>")',
        '@app.delete("/api/topology/rf-records/jobs/<job_id>")',
        "def _run_rf_record_job(",
    ):
        assert marker in web_source

    assert 'id="globalProcessingProgress"' in html
    assert "renderRfRouteRecordsProgress" in app
    assert "rfRouteRecordsLastGood: new Map()" in app
    assert "processing-progress-bar" in css
    assert "rf-record-progress-bar" in css


def test_v1424_incremental_ranking_keeps_multihop_without_rewalking_full_paths(monkeypatch):
    positions = {
        "A": (-16.0, -49.0),
        "B": (-16.4, -48.8),
        "C": (-16.8, -48.4),
        "D": (-17.2, -48.0),
    }
    graph = {}
    ts = "2026-10-11T12:00:00+00:00"
    connect(graph, "A", "B", event(ts, positions["A"], positions["B"], 1))
    connect(graph, "B", "C", event(ts, positions["B"], positions["C"], 2))
    connect(graph, "C", "D", event(ts, positions["C"], positions["D"], 3))

    monkeypatch.setattr(st, "_route_graph", lambda hours=0: (graph, positions))
    monkeypatch.setattr(
        st,
        "_compatible_events",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("full path compatibility should not be recalculated")),
    )
    clear_record_cache()

    progress = []
    records = st._route_records(
        0,
        limit=20,
        max_hops=6,
        beam_width=100,
        progress_callback=lambda item: progress.append(dict(item)),
        deadline_seconds=5,
        force=True,
    )

    route = next(item for item in records if {item["source"], item["target"]} == {"A", "D"})
    assert route["hops"] == 3
    assert route["multihop"] is True
    assert route["nodes"] in (["A", "B", "C", "D"], ["D", "C", "B", "A"])
    percents = [float(item["percent"]) for item in progress]
    assert percents
    assert percents == sorted(percents)
    assert percents[-1] == 100
    assert {item["phase"] for item in progress} >= {"indexing", "reachability", "consolidating", "done"}


def test_v1424_cache_reports_immediate_completion(monkeypatch):
    positions = {"A": (-15.0, -47.0), "B": (-15.1, -47.1)}
    graph = {}
    ts = "2026-10-11T12:00:00+00:00"
    connect(graph, "A", "B", event(ts, positions["A"], positions["B"], 1))
    monkeypatch.setattr(st, "_route_graph", lambda hours=0: (graph, positions))
    clear_record_cache()

    first = st._route_records(24, limit=10, max_hops=3, force=True, deadline_seconds=5)
    progress = []
    second = st._route_records(
        24,
        limit=10,
        max_hops=3,
        progress_callback=lambda item: progress.append(dict(item)),
        deadline_seconds=5,
    )
    assert second == first
    assert progress[-1]["phase"] == "cache"
    assert progress[-1]["percent"] == 100
    assert progress[-1]["cache_hit"] is True


def test_v1424_web_job_progress_is_monotonic_and_finishes(monkeypatch):
    def fake_records(*, hours=0, limit=10, max_hops=6, progress_callback=None, **kwargs):
        for percent in (0, 12, 48, 91, 100):
            if progress_callback:
                progress_callback({
                    "phase": "reachability" if percent < 100 else "done",
                    "percent": percent,
                    "completed": percent,
                    "total": 100,
                    "nodes": 10,
                    "edges": 12,
                    "candidates": 20,
                    "message": f"{percent}%",
                })
        return [{"rank": 1, "source": "A", "target": "B", "nodes": ["A", "B"], "hops": 1}]

    monkeypatch.setattr(db, "list_rf_route_records", fake_records)
    with web._rf_record_jobs_lock:
        web._rf_record_jobs.clear()
        web._rf_record_job_by_key.clear()

    snapshot = web._start_rf_record_job(24, 10, 6, force=True)
    job_id = snapshot["job_id"]
    deadline = time.monotonic() + 2
    last = snapshot
    while time.monotonic() < deadline:
        with web._rf_record_jobs_lock:
            job = web._rf_record_jobs[job_id]
            last = web._rf_record_job_public(job)
        if last["status"] == "done":
            break
        time.sleep(0.01)

    assert last["status"] == "done"
    assert last["percent"] == 100
    assert last["records"][0]["source"] == "A"
    assert last["records"][0]["target"] == "B"


def test_v1424_frontend_preserves_last_valid_records_and_uses_real_progress():
    app = read("pt2vhf_aprs/static/js/app.js")
    assert "rfRouteRecordsLastGood.set(String(normalizedHours), records.slice())" in app
    assert "state.rfRouteRecordsLastGood.get(String(normalizedHours)) || []" in app
    assert "updateProcessing(" in app
    assert "Math.max(lastPercent, Number(job.percent || 0))" in app
    assert "await new Promise(resolve => setTimeout(resolve, 650))" in app
    assert "data-rf-record-retry" in app
    assert "O novo cálculo falhou; mantendo o último ranking válido." in app
