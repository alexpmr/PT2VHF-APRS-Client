from pathlib import Path
import sqlite3
import threading
import time

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def reset_map_cache():
    with db._map_data_cache_lock:
        db._map_data_cache_payload = None
        db._map_data_cache_at = 0.0
        db._map_data_cache_build_ms = 0.0
        db._map_data_cache_db_path = str(db.DB_PATH)


def test_v188_interaction_query_is_set_based_not_correlated_per_station():
    source = read("pt2vhf_aprs/database.py")
    start = source.index("def list_stations(")
    end = source.index("def _is_topology_callsign", start)
    stations_block = source[start:end]
    map_start = source.index("def _build_map_data_uncached(")
    map_end = source.index("def map_data(", map_start)
    map_block = source[map_start:map_end]

    assert "OR EXISTS (" not in stations_block
    assert "OR EXISTS (" not in map_block
    assert "_interaction_calls_conn(conn)" in stations_block
    assert "_interaction_calls_conn(conn)" in map_block


def test_v188_interaction_query_returns_expected_calls():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE messages (
            direction TEXT, from_call TEXT, to_call TEXT,
            message_type TEXT, status TEXT
        );
        CREATE TABLE aprs_queries (
            direction TEXT, peer TEXT, status TEXT, response_at TEXT
        );
        """
    )
    conn.executemany(
        "INSERT INTO messages(direction,from_call,to_call,message_type,status) VALUES(?,?,?,?,?)",
        [
            ("in", "PT2AAA", "PT2VHF", "message", ""),
            ("out", "PT2VHF", "PT2BBB", "message", "ACK"),
            ("out", "PT2VHF", "PT2NO", "message", "Pendente"),
        ],
    )
    conn.executemany(
        "INSERT INTO aprs_queries(direction,peer,status,response_at) VALUES(?,?,?,?)",
        [
            ("in", "PT2CCC", "", None),
            ("out", "PT2DDD", "RESPONDIDA", "2026-10-02T00:00:00+00:00"),
            ("out", "PT2NO2", "PENDENTE", None),
        ],
    )
    try:
        calls = db._interaction_calls_conn(conn)
    finally:
        conn.close()
    assert calls == {"PT2AAA", "PT2BBB", "PT2CCC", "PT2DDD"}


def test_v188_map_data_singleflight_never_runs_duplicate_heavy_builds(monkeypatch):
    reset_map_cache()
    build_started = threading.Event()
    release_build = threading.Event()
    calls = {"count": 0}

    def slow_build():
        calls["count"] += 1
        build_started.set()
        release_build.wait(1.0)
        return {"stations": [{"callsign": "NEW"}], "objects": [], "tracks": []}

    monkeypatch.setattr(db, "_build_map_data_uncached", slow_build)
    monkeypatch.setattr(db, "MAP_DATA_INITIAL_WAIT_SECONDS", 0.02)

    owner_result = {}

    def owner():
        owner_result["value"] = db.map_data(force=True)

    thread = threading.Thread(target=owner)
    thread.start()
    assert build_started.wait(0.5)

    results = []
    workers = [threading.Thread(target=lambda: results.append(db.map_data())) for _ in range(7)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(0.5)

    release_build.set()
    thread.join(1.0)

    assert calls["count"] == 1
    assert all(not worker.is_alive() for worker in workers)
    assert all(result["_meta"]["source"] == "busy-empty" for result in results)
    assert owner_result["value"]["stations"][0]["callsign"] == "NEW"
    reset_map_cache()


def test_v188_concurrent_map_call_uses_stale_snapshot_immediately(monkeypatch):
    reset_map_cache()
    with db._map_data_cache_lock:
        db._map_data_cache_payload = {"stations": [{"callsign": "OLD"}], "objects": [], "tracks": []}
        db._map_data_cache_at = time.monotonic() - 120.0
        db._map_data_cache_db_path = str(db.DB_PATH)

    build_started = threading.Event()
    release_build = threading.Event()

    def slow_build():
        build_started.set()
        release_build.wait(1.0)
        return {"stations": [{"callsign": "NEW"}], "objects": [], "tracks": []}

    monkeypatch.setattr(db, "_build_map_data_uncached", slow_build)

    owner = threading.Thread(target=lambda: db.map_data(force=True))
    owner.start()
    assert build_started.wait(0.5)

    started = time.monotonic()
    stale = db.map_data()
    elapsed = time.monotonic() - started

    release_build.set()
    owner.join(1.0)

    assert elapsed < 0.10
    assert stale["stations"][0]["callsign"] == "OLD"
    assert stale["_meta"]["source"] == "stale-cache"
    assert stale["_meta"]["busy"] is True
    reset_map_cache()


def test_v188_sqlite_indexes_cover_interaction_queries():
    source = read("pt2vhf_aprs/database.py")
    assert "idx_messages_to ON messages(to_call)" in source
    assert "idx_messages_interaction_in ON messages(direction,message_type,from_call)" in source
    assert "idx_messages_interaction_out ON messages(direction,status,to_call)" in source
    assert "idx_aprs_queries_interaction ON aprs_queries(direction,status,response_at,peer)" in source


def test_v188_frontend_reduces_full_map_and_serial_polling():
    app = read("pt2vhf_aprs/static/js/app.js")
    tnc = read("pt2vhf_aprs/static/js/tnc.js")
    service = read("pt2vhf_aprs/tnc_service.py")
    web = read("pt2vhf_aprs/web.py")

    assert "}, 15000);" in app
    assert "data?._meta?.source === 'busy-empty'" in app
    assert "serialPollTick % 10 === 0" in tnc
    assert "loadPorts({quiet:true, quick:true})" in tnc
    assert "params.set('quick', '1')" in tnc
    assert "full_scan: bool = True" in service
    assert "if full_scan and sys.platform == \"win32\":" in service
    assert "available_ports(force=force, full_scan=not quick)" in web


def test_v188_version():
    assert read("VERSION").strip() == "1.8.8"
    assert '__version__ = "1.8.8"' in read("pt2vhf_aprs/__init__.py")
