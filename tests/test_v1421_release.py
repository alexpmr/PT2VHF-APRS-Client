from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import time

from pt2vhf_aprs import spacetime_topology as st
from pt2vhf_aprs import web

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1421_version_metadata_and_release_markers():
    version = tuple(int(part) for part in read("VERSION").strip().split("."))
    assert version >= (1, 14, 21)
    assert "spacetime_topology.install()" in read("pt2vhf_aprs/__init__.py")

    overlay = read("pt2vhf_aprs/spacetime_topology.py")
    for marker in (
        "GRAPH_CACHE_SECONDS = 20.0",
        "_graph_builds:",
        "rf_route_graph_singleflight_wait",
        "def _build_route_graph_uncached(",
        "def _route_graph(hours: float = 0):",
    ):
        assert marker in overlay

    backend = read("pt2vhf_aprs/web.py")
    for marker in (
        "TOPOLOGY_STATS_CACHE_SECONDS = 30.0",
        "def _topology_stats_payload(",
        'db.topology_stats(key, include_routes=False)',
        '@app.get("/api/topology/rf-records")',
        "topology_stats_singleflight_wait",
    ):
        assert marker in backend

    app = read("pt2vhf_aprs/static/js/app.js")
    for marker in (
        "PROCESSING_SHOW_DELAY_MS = 320",
        "visible: false",
        "topologyStatsLastGood",
        "refreshRfRouteRecordsDeferred",
        "rfRouteOriginsController",
        "rfRouteOriginCache: new Map()",
        "Calculando estatísticas do histórico",
        "mantendo os últimos valores válidos",
    ):
        assert marker in app

    css = read("pt2vhf_aprs/static/css/app.css")
    assert "v1.14.21 - Estatísticas em fluxo único" in css
    assert ".global-processing-overlay.nonblocking" in css


def test_v1421_rf_graph_singleflight_builds_once(monkeypatch):
    calls = 0
    calls_lock = threading.Lock()

    def fake_build(hours: float):
        nonlocal calls
        with calls_lock:
            calls += 1
        time.sleep(0.12)
        return ({"PT2A": {}}, {"PT2A": (-15.0, -47.0)})

    monkeypatch.setattr(st, "_build_route_graph_uncached", fake_build)
    with st._graph_cache_lock:
        st._graph_cache.clear()
        st._graph_builds.clear()
        st._graph_build_errors.clear()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: st._route_graph(0), range(8)))

    assert calls == 1
    assert all(result[0] == {"PT2A": {}} for result in results)


def test_v1421_topology_stats_cache_reuses_full_history_result(monkeypatch):
    calls = {"core": 0, "comparison": 0, "reception": 0}

    def fake_core(hours: int, *, include_routes: bool = True):
        calls["core"] += 1
        assert include_routes is False
        return {
            "hours": hours,
            "edges": 4,
            "packets": 20,
            "rf_route_records": [],
            "rf_route_records_deferred": True,
        }

    def fake_comparison(hours: int):
        calls["comparison"] += 1
        return {"current_events": 12, "previous_events": 0, "delta": 0}

    def fake_reception(hours: int):
        calls["reception"] += 1
        return {"logical_packets_deduplicated": 20}

    monkeypatch.setattr(web.db, "topology_stats", fake_core)
    monkeypatch.setattr(web.db, "topology_period_comparison", fake_comparison)
    monkeypatch.setattr(web, "tnc_reception_stats", fake_reception)

    with web._topology_stats_cache_lock:
        web._topology_stats_cache.clear()
        web._topology_stats_builds.clear()
        web._topology_stats_errors.clear()

    first = web._topology_stats_payload(0)
    second = web._topology_stats_payload(0)

    assert first["edges"] == 4
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert calls == {"core": 1, "comparison": 1, "reception": 1}


def test_v1421_statistics_keep_single_vertical_scroll():
    css = read("pt2vhf_aprs/static/css/app.css")
    marker = css.index("/* v1.14.21 - Estatísticas em fluxo único")
    section = css[marker:]
    assert "#tab-analysis .analysis-content" in section
    assert "overflow-y: auto;" in section
    assert "overflow-x: hidden;" in section
    assert "#tab-analysis .client-version-stats-content" in section
    assert "overflow: visible !important;" in section
    assert "table-layout: fixed;" in section


def test_v1421_processing_overlay_is_delayed_and_concurrency_safe():
    app = read("pt2vhf_aprs/static/js/app.js")
    assert "const PROCESSING_SHOW_DELAY_MS = 320;" in app
    assert "processingOperations.set(token, entry);" in app
    assert "entry.timer = setTimeout" in app
    assert "if (current?.timer) clearTimeout(current.timer);" in app
    assert "filter(entry => entry.visible)" in app
    assert "entries.some(entry => entry.blocking !== false)" in app


def test_v1421_statistics_load_rf_records_independently():
    app = read("pt2vhf_aprs/static/js/app.js")
    web_source = read("pt2vhf_aprs/web.py")
    db_source = read("pt2vhf_aprs/database.py")

    assert "rf_route_records_deferred" in db_source
    assert "include_routes: bool = True" in db_source
    assert "/api/topology/rf-records?hours=" in app
    assert 'id="rfRouteRecordsHost"' in app
    assert "Recordes RF temporariamente indisponíveis" in app
    assert '@app.get("/api/topology/rf-records")' in web_source


def test_v1421_rf_origin_autocomplete_cancels_stale_requests():
    app = read("pt2vhf_aprs/static/js/app.js")
    assert "state.rfRouteOriginsController.abort()" in app
    assert "state.rfRouteOriginGeneration += 1" in app
    assert "if (generation !== state.rfRouteOriginGeneration) return [];" in app
    assert "serverQuery = normalizedQuery;" in app
    assert "'&q=' + encodeURIComponent(serverQuery)" in app
