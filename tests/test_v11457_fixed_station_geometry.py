"""v1.14.57: enlaces de estações fixas ouvidas há mais de 12 h voltam ao mapa.

O tracklog só ganha ponto novo quando a estação se desloca >= 10 m; a posição
de cada ponta do enlace só aceitava ponto de até 12 h. Estação fixa ouvida há
mais de 12 h ficava sem posição em todo enlace novo e sumia do mapa.
"""
from datetime import datetime, timedelta, timezone

import aprslib

from pt2vhf_aprs import database as db, spacetime_topology, topology_map

DIGI = "PY2DIG-1>APRS,TCPIP*,qAC,T2BRAZIL:!2332.00S/04632.00W#PHG5360/digi"
HOUSE = "PY2FIX>APRS,TCPIP*,qAC,T2BRAZIL:!2335.00S/04635.00W-casa"
HEARD = "PY2FIX>APRS,PY2DIG-1*,WIDE2-1,qAR,PY2IGT:!2335.00S/04635.00W-casa"


def ingest(raw):
    p = aprslib.parse(raw)
    db.process_received_packet(raw, p, p.get("from"), p.get("format"), medium="APRS-IS")


def age_everything(hours):
    old = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    with db.connection() as conn:
        conn.execute("UPDATE tracks SET timestamp=?", (old,))
        conn.execute("DELETE FROM topology_events")


def test_new_link_of_station_first_heard_long_ago_has_geometry(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "fixed.db")
    db.init_db()
    ingest(DIGI)
    ingest(HOUSE)
    age_everything(48)          # primeira escuta há 2 dias; parados desde então
    ingest(DIGI)                # mesmo lugar: nenhum ponto novo no tracklog
    ingest(HEARD)
    edges = {(e["source"], e["target"]): e for e in topology_map.list_map_edges(0)}
    assert ("PY2FIX", "PY2DIG-1") in edges


def test_moved_station_does_not_reuse_old_point(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "moved.db")
    db.init_db()
    ingest(DIGI)
    age_everything(48)
    with db.connection() as conn:   # hoje a estação está em outro lugar
        conn.execute("UPDATE stations SET latitude=-22.9, longitude=-43.2 WHERE callsign='PY2DIG-1'")
        pos = spacetime_topology._position_at_event_conn(conn, "PY2DIG-1", db.utc_now_iso())
    assert pos is None


def test_one_time_backfill_fills_events_saved_without_geometry(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "back.db")
    db.init_db()
    ingest(DIGI)
    ingest(HOUSE)
    now = db.utc_now_iso()
    age_everything(48)
    with db.connection() as conn:
        conn.execute("INSERT INTO topology_events(timestamp,source,target,kind,medium,evidence_level) "
                     "VALUES(?,?,?,?,?,?)", (now, "PY2FIX", "PY2DIG-1", "rf", "APRS-IS", "inferred"))
        conn.execute("DELETE FROM schema_migrations_v1419 WHERE migration_key='v1.14.57-fixed-station-event-geometry'")
        cells_before = conn.execute("SELECT COALESCE(SUM(tx+rx),0) FROM rf_coverage_cells").fetchone()[0]
        assert spacetime_topology._backfill_fixed_station_geometry(conn) == 1
        row = conn.execute("SELECT source_lat,target_lat FROM topology_events").fetchone()
        assert row[0] is not None and row[1] is not None
        assert conn.execute("SELECT COALESCE(SUM(tx+rx),0) FROM rf_coverage_cells").fetchone()[0] == cells_before + 2
        assert spacetime_topology._backfill_fixed_station_geometry(conn) == 0
