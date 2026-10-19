"""#121: saneamento reversível de posições antigas contaminadas (PP5BLU-15)."""
import json
import tempfile
from pathlib import Path

import pytest

from pt2vhf_aprs import database as db

BAD_RAW = "PP5BLU-15>APBK20,WIDE1-1,WIDE2-1,qAR,PP5APR-10:!2677.84S/04900.03W#PHG7190"
GOOD_RAW = "PP5BLU-15>APBK20,WIDE1-1:!2646.68S/04901.80W#PHG7190"
BAD_LAT, BAD_LON = -27.297333, -49.0005  # 26 + 77.84/60, gravado pelo parser permissivo
GOOD_LAT, GOOD_LON = -26.778, -49.03
MIGRATION_KEY = "v1.14.48-quarantine-malformed-aprs-positions"


@pytest.fixture
def legacy_db():
    original = db.DB_PATH
    with tempfile.TemporaryDirectory() as td:
        db.DB_PATH = Path(td) / "legacy.db"
        try:
            db.init_db()
            with db.connection() as conn:
                # Simula banco anterior à v1.14.46: migração ainda não aplicada.
                conn.execute("DELETE FROM schema_migrations_v112 WHERE migration_key=?", (MIGRATION_KEY,))
                conn.execute(
                    "INSERT INTO packets(timestamp,from_call,raw) VALUES(?,?,?)",
                    ("2026-10-18T10:00:00+00:00", "PP5BLU-15", BAD_RAW),
                )
                conn.execute(
                    "INSERT INTO tracks(callsign,timestamp,latitude,longitude,raw) VALUES(?,?,?,?,?)",
                    ("PP5BLU-15", "2026-10-17T10:00:00+00:00", GOOD_LAT, GOOD_LON, GOOD_RAW),
                )
                conn.execute(
                    "INSERT INTO tracks(callsign,timestamp,latitude,longitude,raw) VALUES(?,?,?,?,?)",
                    ("PP5BLU-15", "2026-10-18T10:00:00+00:00", BAD_LAT, BAD_LON, BAD_RAW),
                )
                # A estação guarda o último raw, que pode nem ser de posição.
                conn.execute(
                    "INSERT INTO stations(callsign,last_heard,latitude,longitude,raw) VALUES(?,?,?,?,?)",
                    ("PP5BLU-15", "2026-10-18T10:05:00+00:00", BAD_LAT, BAD_LON,
                     "PP5BLU-15>APBK20:>status sem posição"),
                )
                conn.execute(
                    "INSERT INTO stations(callsign,last_heard,latitude,longitude,raw) VALUES(?,?,?,?,?)",
                    ("PP5XYZ", "2026-10-18T10:05:00+00:00", -27.5, -48.5, "PP5XYZ>APRS:!2730.00S/04830.00W-ok"),
                )
            yield
        finally:
            db.DB_PATH = original


def _rows(sql, *params):
    with db.connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def test_malformed_owner_and_coords_reproduce_permissive_parser():
    assert db._malformed_position_owner_and_coords(BAD_RAW) == ("PP5BLU-15", BAD_LAT, BAD_LON)
    assert db._malformed_position_owner_and_coords(GOOD_RAW) is None
    obj = "PP5BLU-14>APRS:;PP5BLU-15*181000z2677.84S/04900.03W#obj"
    assert db._malformed_position_owner_and_coords(obj) == ("PP5BLU-15", BAD_LAT, BAD_LON)


def test_quarantine_moves_contaminated_track_and_restores_last_valid_station(legacy_db):
    db.init_db()

    tracks = _rows("SELECT latitude,longitude FROM tracks WHERE callsign='PP5BLU-15'")
    assert tracks == [{"latitude": GOOD_LAT, "longitude": GOOD_LON}]
    station = _rows("SELECT latitude,longitude FROM stations WHERE callsign='PP5BLU-15'")[0]
    assert (station["latitude"], station["longitude"]) == (GOOD_LAT, GOOD_LON)
    # Estação sem relação com o defeito não é tocada; packets fica intacto.
    assert _rows("SELECT latitude FROM stations WHERE callsign='PP5XYZ'")[0]["latitude"] == -27.5
    assert _rows("SELECT raw FROM packets")[0]["raw"] == BAD_RAW

    quarantine = _rows("SELECT source_table,issue,row_json FROM position_quarantine ORDER BY id")
    assert [q["source_table"] for q in quarantine] == ["tracks", "stations"]
    assert quarantine[0]["issue"] == "invalid_aprs_minutes"
    assert json.loads(quarantine[1]["row_json"])["latitude"] == BAD_LAT
    assert _rows("SELECT issue_type FROM station_anomalies WHERE callsign='PP5BLU-15'")[-1]["issue_type"] == \
        "malformed_position_quarantined"


def test_quarantine_runs_once_and_is_reversible(legacy_db):
    db.init_db()
    db.init_db()
    assert len(_rows("SELECT id FROM position_quarantine")) == 2

    assert db.restore_quarantined_positions("PP5BLU-15") == 2
    station = _rows("SELECT latitude,longitude FROM stations WHERE callsign='PP5BLU-15'")[0]
    assert (station["latitude"], station["longitude"]) == (BAD_LAT, BAD_LON)
    assert len(_rows("SELECT id FROM tracks WHERE callsign='PP5BLU-15'")) == 2
    assert db.restore_quarantined_positions() == 0


def test_station_without_valid_history_loses_position_instead_of_guessing(legacy_db):
    with db.connection() as conn:
        conn.execute("DELETE FROM tracks WHERE raw=?", (GOOD_RAW,))
    db.init_db()
    station = _rows("SELECT latitude,longitude FROM stations WHERE callsign='PP5BLU-15'")[0]
    assert station == {"latitude": None, "longitude": None}
