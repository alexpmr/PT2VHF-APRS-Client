"""Regression checks for v1.14.39 RF processing, map, stats and maintenance."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import time

from pt2vhf_aprs import database as db, category_statistics, category_clear
from pt2vhf_aprs import topology_map, web


def _event(conn, stamp, source, digi, source_pos, digi_pos, medium="RF", level="direct"):
    conn.execute(
        """INSERT INTO topology_events(timestamp,source,target,kind,medium,evidence_level,
                   source_lat,source_lon,target_lat,target_lon)
           VALUES(?,?,?,'rf',?,?,?,?,?,?)""",
        (stamp, source, digi, medium, level, *source_pos, *digi_pos),
    )


def test_moving_digi_not_drawn_as_rf_spider_but_preserved_for_coverage():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "coverage.sqlite3"
            db.init_db()
            now = datetime.now(timezone.utc).replace(microsecond=0)
            with db.connection() as conn:
                for delta in (6, 7):
                    _event(conn, (now - timedelta(hours=delta)).isoformat(),
                           "PY5SUL-9", "PT2AP-9", (-25.42, -49.24), (-25.39, -49.23),
                           medium="APRS-IS", level="inferred")
                for delta in (2, 3):
                    _event(conn, (now - timedelta(hours=delta)).isoformat(),
                           "PY4UBA-9", "PT2AP-9", (-19.73, -47.92), (-19.74, -47.93))
                _event(conn, now.isoformat(), "PU2FIX-1", "PT2FIX-2",
                       (-15.72, -47.93), (-15.70, -47.90))
                # Same historical evidence remains available after display suppression.
                assert conn.execute("SELECT COUNT(*) FROM topology_events").fetchone()[0] == 5
            edges = topology_map.list_map_edges(24)
            assert len(edges) == 2
            assert {edge['kind'] for edge in edges} == {'rf_mobile', 'rf_temp'}
            assert len([edge for edge in edges if edge['target'] == 'PT2AP-9']) == 1
            samples = topology_map.list_mobile_rf_coverage(24)
            assert len(samples) >= 2
            assert {p["callsign"] for p in samples} == {"PT2AP-9"}
            assert {p["evidence"] for p in samples} == {"direct", "inferred"}
            assert all(p["count"] >= 2 for p in samples)
            with db.connection() as conn:
                assert conn.execute("SELECT COUNT(*) FROM topology_events").fetchone()[0] == 5
    finally:
        db.DB_PATH = original


def test_fast_category_statistics_count_retained_data_without_duplicate_stations():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "category.sqlite3"
            db.init_db()
            now = datetime.now(timezone.utc).isoformat()
            with db.connection() as conn:
                conn.execute("INSERT INTO stations(callsign,last_heard) VALUES('PT2VHF',?)", (now,))
                for _ in range(3):
                    conn.execute("INSERT INTO packets(timestamp,from_call,raw) VALUES(?,'PT2VHF','PT2VHF>APRS:test')", (now,))
                conn.execute("INSERT INTO messages(timestamp,direction,from_call,to_call,message,message_type) VALUES(?,'in','PT2A','PT2VHF','A','message')", (now,))
                conn.execute("INSERT INTO messages(timestamp,direction,from_call,to_call,message,message_type) VALUES(?,'out','PT2VHF','PT2A','B','message')", (now,))
                conn.execute("INSERT INTO messages(timestamp,direction,from_call,to_call,message,message_type) VALUES(?,'in','PT2A','CQ','C','bulletin')", (now,))
                conn.execute("INSERT INTO tracks(callsign,timestamp,latitude,longitude) VALUES('PT2VHF',?,-15.8,-47.9)", (now,))
                conn.execute("INSERT INTO aprs_objects(name,last_heard,latitude,longitude) VALUES('OBJECT',?,-15.8,-47.9)", (now,))
            summary = category_statistics.category_counts(0)
            assert summary["stations"] == 1 and summary["packets"] == 3
            assert summary["messages"] == 2 and summary["messages_rx"] == 1 and summary["messages_tx"] == 1
            assert summary["bulletins"] == 1 and summary["objects"] == 1 and summary["trackpoints"] == 1
            # Deleting only packets cannot erase messages, stations or track history.
            before = category_clear.preview("packets")
            assert before["count"] == 3
            job = category_clear.start("packets", "CLEAR:packets")
            for _ in range(150):
                job = category_clear.status(job["job_id"])
                if job["status"] in ("done", "error", "cancelled"):
                    break
                time.sleep(0.02)
            assert job["status"] == "done", job
            after = category_statistics.category_counts(0)
            assert after["packets"] == 0
            assert after["stations"] == 1 and after["messages"] == 2
            assert after["objects"] == 1 and after["trackpoints"] == 1
    finally:
        db.DB_PATH = original


def test_category_clear_requires_explicit_approval_and_protects_pending_tx():
    import pytest
    with pytest.raises(ValueError):
        category_clear.start("packets", "CLEAR:stations")
    with pytest.raises(ValueError):
        category_clear.preview("any_sql_table")


def test_rf_records_background_job_has_no_total_wall_clock_deadline(monkeypatch):
    captured = []
    def pretend_records(**kwargs):
        captured.append(kwargs["deadline_seconds"])
        kwargs["progress_callback"]({"phase": "reachability", "percent": 30,
                                     "completed": 30, "total": 100, "nodes": 100})
        return [{"rank": 1, "nodes": ["A", "B"]}]
    monkeypatch.setattr(web.db, "list_rf_route_records", pretend_records)
    job = web._start_rf_record_job(0, 10, 6, force=True)
    for _ in range(120):
        snapshot = web._rf_record_job_public(web._rf_record_jobs[job["job_id"]])
        if snapshot["status"] in {"done", "error"}:
            break
        time.sleep(0.02)
    assert snapshot["status"] == "done", snapshot
    assert captured == [None]
    assert snapshot["records"][0]["rank"] == 1


def test_frontend_has_cancel_eta_and_category_actions():
    js = (Path(__file__).resolve().parents[1] / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "data-rf-record-cancel" in js
    assert "rfRouteCancelPending" in js
    assert "progress.eta_seconds" in js
    assert "/api/statistics/categories?hours=" in js
    assert "data-retention-clear-category" in js
    assert "/api/topology/rf-coverage?hours=" in js
    assert "rfCoverageEnabled" in js
