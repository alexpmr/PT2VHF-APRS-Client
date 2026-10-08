from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import tempfile
import time

from pt2vhf_aprs import database as db
from pt2vhf_aprs import tnc_service as tnc


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v147_version_metadata():
    assert read("VERSION").strip() == "1.14.7"
    assert '__version__ = "1.14.7"' in read("pt2vhf_aprs/__init__.py")
    win = read("windows/version_info.txt")
    assert "filevers=(1, 14, 7, 0)" in win
    assert "prodvers=(1, 14, 7, 0)" in win


def test_v147_tnc_schema_is_ensured_once_per_database_path(monkeypatch):
    original_path = db.DB_PATH
    original_ready = tnc._schema_ready_db_path
    original_connection = db.connection
    calls = {"count": 0}
    with tempfile.TemporaryDirectory() as td:
        db.DB_PATH = Path(td) / "tnc-once.db"
        tnc._schema_ready_db_path = ""

        @contextmanager
        def counted_connection():
            calls["count"] += 1
            with original_connection() as conn:
                yield conn

        monkeypatch.setattr(tnc.db, "connection", counted_connection)
        tnc._ensure_schema()
        assert calls["count"] == 1
        tnc._ensure_schema()
        assert calls["count"] == 1
        assert tnc._schema_ready_db_path == str(db.DB_PATH)

    db.DB_PATH = original_path
    tnc._schema_ready_db_path = original_ready


def test_v147_continuous_rx_does_not_force_immediate_map_rebuild(monkeypatch):
    with db._map_data_cache_lock:
        db._map_data_cache_payload = {
            "stations": [{"callsign": "PT2VHF"}],
            "objects": [],
            "tracks": [],
        }
        db._map_data_cache_at = time.monotonic()
        db._map_data_cache_build_ms = 1.0
        db._map_data_cache_db_path = str(db.DB_PATH)

    calls = {"count": 0}

    def fail_build():
        calls["count"] += 1
        return {"stations": [], "objects": [], "tracks": []}

    monkeypatch.setattr(db, "_build_map_data_uncached", fail_build)
    db.invalidate_map_data_cache(drop_payload=False, coalesce=True)
    result = db.map_data()
    assert result["_meta"]["source"] == "cache"
    assert result["stations"][0]["callsign"] == "PT2VHF"
    assert calls["count"] == 0

    db.invalidate_map_data_cache(drop_payload=True)
    with db._map_data_cache_lock:
        assert db._map_data_cache_payload is None
        assert db._map_data_cache_at == 0.0


def test_v147_sqlite_runtime_and_indexes_cover_hot_paths():
    source = read("pt2vhf_aprs/database.py")
    for marker in (
        "SQLITE_BUSY_TIMEOUT_MS = 5000",
        "SQLITE_CACHE_KIB = 8192",
        "SQLITE_WAL_AUTOCHECKPOINT_PAGES = 1000",
        'conn.execute("PRAGMA temp_store=MEMORY")',
        "idx_packets_time_from_call",
        "idx_packets_medium_time",
        "idx_packets_from_call_norm_time",
        "idx_topology_kind_target_seen",
        "idx_topology_igate_seen",
        "MAP_DATA_CACHE_SECONDS = 30.0",
        "_station_position_issues_conn(conn, station_rows)",
    ):
        assert marker in source


def test_v147_tnc_hot_polling_path_has_schema_guard():
    source = read("pt2vhf_aprs/tnc_service.py")
    assert "_schema_lock = threading.Lock()" in source
    assert '_schema_ready_db_path = ""' in source
    assert "if _schema_ready_db_path == db_key:" in source
    assert "_schema_ready_db_path = db_key" in source
