"""v1.14.61: Estatísticas e Recordes RF reaproveitam o último cálculo guardado."""
import time

from pt2vhf_aprs import database as db, saved_results, web


def _app(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "s.db")
    monkeypatch.setattr(web.scheduled_message_service, "start", lambda *a, **k: None)
    monkeypatch.setattr(web.retention, "start_worker", lambda *a, **k: None)
    monkeypatch.setattr(web.version_announce, "start_worker", lambda *a, **k: None)
    db.init_db()
    web._topology_stats_cache.clear()
    web._rf_record_jobs.clear()
    web._rf_record_job_by_key.clear()
    return web.create_app().test_client()


def test_stats_reused_from_disk_until_recalculate(tmp_path, monkeypatch):
    client = _app(tmp_path, monkeypatch)
    calls = []
    real = db.topology_stats
    monkeypatch.setattr(db, "topology_stats", lambda *a, **k: calls.append(1) or real(*a, **k))
    first = client.get("/api/topology/stats?hours=0").get_json()
    assert first["saved_at"] and len(calls) == 1
    web._topology_stats_cache.clear()           # app reaberto: memória vazia
    again = client.get("/api/topology/stats?hours=0").get_json()
    assert again["from_saved"] and len(calls) == 1
    client.get("/api/topology/stats?hours=0&refresh=1")
    assert len(calls) == 2


def test_rf_records_reused_from_disk_until_force(tmp_path, monkeypatch):
    client = _app(tmp_path, monkeypatch)
    saved_results.save("rf_records", [0, 10, 6, "direct"], [{"source": "A", "target": "B"}])
    calls = []
    monkeypatch.setattr(db, "list_rf_route_records", lambda **k: calls.append(1) or [])
    job = client.post("/api/topology/rf-records/jobs", json={"hours": 0}).get_json()
    assert job["status"] == "done" and job["from_saved"] and job["records"] == [{"source": "A", "target": "B"}]
    assert calls == []
    job = client.post("/api/topology/rf-records/jobs", json={"hours": 0, "force": True}).get_json()
    for _ in range(50):
        if client.get("/api/topology/rf-records/jobs/" + job["job_id"]).get_json()["status"] == "done":
            break
        time.sleep(0.05)
    assert calls == [1]
    assert saved_results.load("rf_records", [0, 10, 6, "direct"])[0] == []
