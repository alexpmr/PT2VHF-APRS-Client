"""v1.14.53: mapa de calor com armazenamento e retenção próprios."""
from datetime import datetime, timedelta, timezone

import aprslib

from pt2vhf_aprs import database as db, rf_coverage, retention


def ingest(raw):
    parsed = aprslib.parse(raw)
    db.process_received_packet(raw, parsed, parsed.get("from"), parsed.get("format"), medium="APRS-IS")


PACKETS = [
    "PT2DIG-1>APRS,TCPIP*,qAC,T2BRAZIL:!1545.00S/04752.80W#Digi",
    "PT2CAR-9>APRS,PT2DIG-1*,WIDE2-1,qAR,PT2IGT:!1548.00S/04806.60W>090/025",
]


def test_ingestion_feeds_heatmap_independently_of_other_retention(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "heat.db")
    db.init_db()
    for raw in PACKETS:
        ingest(raw)
    points = rf_coverage.list_points(0)
    by_pos = {(round(p["latitude"], 2), round(p["longitude"], 2)): p for p in points}
    assert by_pos[(-15.8, -48.11)]["tx"] == 1          # posição do tracker ao transmitir
    assert by_pos[(-15.75, -47.88)]["rx"] == 1         # digi que repetiu
    # Apagar eventos, enlaces, tracklogs e estações não afeta o mapa de calor.
    with db.connection() as conn:
        for table in ("topology_events", "topology_edges", "tracks", "stations"):
            conn.execute(f"DELETE FROM {table}")
    assert len(rf_coverage.list_points(0)) == len(points)


def test_own_retention_category_purges_only_heatmap_cells(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "ret.db")
    db.init_db()
    old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(timespec="seconds")
    new = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with db.connection() as conn:
        rf_coverage.record_event_conn(conn, old, "A", "B", (-15.8, -48.1), (-15.7, -47.9), direct=False)
        rf_coverage.record_event_conn(conn, new, "C", "D", (-16.0, -48.0), (-16.1, -48.2), direct=True)
    assert retention.DEFAULT_DAYS["rf_coverage"] == 0          # padrão: permanente
    policy = {key: 0 for key in retention.DEFAULT_DAYS}
    policy["rf_coverage"] = 30
    retention.save_policy(policy, enabled=True)
    retention.apply_retention()
    days = {p["last_seen"][:10] for p in rf_coverage.list_points(0)}
    assert days == {new[:10]}


def test_backfill_copies_existing_rf_history_once(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "bf.db")
    db.init_db()
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with db.connection() as conn:
        conn.execute("DELETE FROM rf_coverage_cells")
        conn.execute("DELETE FROM schema_migrations_v112 WHERE migration_key=?", (rf_coverage.BACKFILL_KEY,))
        conn.execute(
            """INSERT INTO topology_events(timestamp,source,target,kind,medium,evidence_level,
                   source_lat,source_lon,target_lat,target_lon,raw) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (ts, "PT2OLD", "PT2DIG", "rf", "APRS-IS", "inferred", -15.81, -48.12, -15.75, -47.88, ""))
    db.init_db()
    db.init_db()
    points = rf_coverage.list_points(0)
    assert sum(p["count"] for p in points) == 2


def test_period_filter_and_settings_ui():
    from pathlib import Path
    js = (Path(__file__).resolve().parents[1] / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "['rf_coverage', 'Mapa de calor (cobertura RF) — independente das demais'" in js


def test_retention_form_loads_and_saves_every_category():
    # Desde a v1.14.44 o formulário iterava $() (um único elemento): carregar
    # falhava em silêncio (tudo "24 horas") e Salvar lançava erro.
    from pathlib import Path
    js = (Path(__file__).resolve().parents[1] / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "for (const select of $$('#retentionPolicyGrid select[data-retention-category]'))" in js
    assert "for (const el of $$('#retentionPolicyGrid select[data-retention-category]'))" in js
    assert "of $('#retentionPolicyGrid" not in js
