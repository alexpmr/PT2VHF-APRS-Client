"""v1.14.54: Verificar banco / Reparar estrutura (sem apagar dados)."""
import sqlite3

import aprslib

from pt2vhf_aprs import database as db, db_check


def ingest(raw):
    parsed = aprslib.parse(raw)
    db.process_received_packet(raw, parsed, parsed.get("from"), parsed.get("format"), medium="APRS-IS")


PACKETS = [
    "PT2DIG-1>APRS,TCPIP*,qAC,T2BRAZIL:!1545.00S/04752.80W#Digi",
    "PT2CAR-9>APRS,PT2DIG-1*,WIDE2-1,qAR,PT2IGT:!1548.00S/04806.60W>090/025",
]


def by_key(report):
    return {c["key"]: c for c in report["checks"]}


def test_healthy_database_reports_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "ok.db")
    db.init_db()
    for raw in PACKETS:
        ingest(raw)
    report = db_check.run_check()
    checks = by_key(report)
    assert checks["integrity"]["status"] == "ok"
    assert checks["schema"]["status"] == "ok"
    assert checks["link_events"]["status"] == "ok"
    assert report["stats"]["link_events_with_position"] >= 1
    assert report["can_repair"] is False


def test_missing_geometry_columns_are_detected_and_repaired(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "old.db")
    db.init_db()
    for raw in PACKETS:
        ingest(raw)
    before = db_check.run_check()["stats"]["packets"]
    conn = sqlite3.connect(db.DB_PATH)
    conn.execute("ALTER TABLE topology_events DROP COLUMN rx_fingerprint")
    conn.commit(); conn.close()
    report = db_check.run_check()
    assert by_key(report)["schema"]["status"] == "error"
    assert "topology_events.rx_fingerprint" in by_key(report)["schema"]["detail"]
    assert report["can_repair"] and report["status"] == "error"
    fixed = db_check.repair()
    assert fixed["repaired"] and by_key(fixed)["schema"]["status"] == "ok"
    assert fixed["stats"]["packets"] == before


def test_events_without_any_position_are_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "nogeo.db")
    db.init_db()
    with db.connection() as conn:
        conn.execute("INSERT INTO topology_events(timestamp,source,target,kind) VALUES('2026-10-01T00:00:00+00:00','A','B','rf')")
    report = db_check.run_check()
    assert by_key(report)["link_events"]["status"] == "error"
    assert report["can_repair"]


def test_api_routes(tmp_path, monkeypatch):
    from pt2vhf_aprs import web
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "api.db")
    monkeypatch.setattr(web.scheduled_message_service, "start", lambda *a, **k: None)
    monkeypatch.setattr(web.retention, "start_worker", lambda *a, **k: None)
    db.init_db()
    client = web.create_app().test_client()
    assert client.get("/api/database/check").get_json()["checks"]
    assert client.post("/api/database/repair", json={}).status_code == 400
    assert client.post("/api/database/repair", json={"confirm": True}).get_json()["repaired"]
    assert client.get("/api/tnc/rx-monitor").get_json()["ok"]
