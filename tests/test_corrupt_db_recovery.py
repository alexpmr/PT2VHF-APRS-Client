"""Banco SQLite corrompido não pode impedir a inicialização."""
import sqlite3

from pt2vhf_aprs import database as db
from pt2vhf_aprs import spacetime_topology


def _make_db_with_config(path, callsign="PT2TST"):
    db.init_db()
    db.save_config({"callsign": callsign})
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.close()


def test_garbage_header_is_quarantined_and_app_starts(tmp_path, monkeypatch):
    path = tmp_path / "pt2vhf_aprs.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "LAST_DB_RECOVERY", None)
    _make_db_with_config(path)
    with open(path, "r+b") as fh:
        fh.write(b"\xde\xad\xbe\xef" * 32)

    db.init_db()  # antes: sqlite3.DatabaseError

    info = db.LAST_DB_RECOVERY
    assert info is not None
    quarantined = tmp_path / "corrupted"
    assert any(quarantined.glob("pt2vhf_aprs_corrupt_*.db"))
    assert str(quarantined) in info["quarantined_path"]
    assert db.get_config()["callsign"] != "PT2TST"  # cabeçalho ilegível: nada a salvar
    assert "recuperado" in db.recovery_notice_text()
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"


def test_readable_data_is_salvaged_after_corruption(tmp_path, monkeypatch):
    path = tmp_path / "pt2vhf_aprs.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "LAST_DB_RECOVERY", None)
    _make_db_with_config(path, "PT2SAV")

    real_init = spacetime_topology._init_db
    calls = {"n": 0}

    def flaky_init():
        calls["n"] += 1
        if calls["n"] == 1:
            raise sqlite3.DatabaseError("database disk image is malformed")
        real_init()

    monkeypatch.setattr(spacetime_topology, "_init_db", flaky_init)
    db.init_db()

    info = db.LAST_DB_RECOVERY
    assert info and info["rows_recovered"] >= 1
    assert db.get_config()["callsign"] == "PT2SAV"


def test_salvage_keeps_intact_tables_when_one_table_is_damaged(tmp_path, monkeypatch):
    path = tmp_path / "pt2vhf_aprs.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    _make_db_with_config(path, "PT2PAR")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE junk (id INTEGER PRIMARY KEY, payload TEXT)")
    conn.executemany("INSERT INTO junk (payload) VALUES (?)", [("x" * 900,) for _ in range(400)])
    conn.commit()
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
    conn.close()
    with open(path, "r+b") as fh:  # estraga páginas finais (dados de junk)
        for page in range(page_count - 40, page_count - 20):
            fh.seek(page * page_size)
            fh.write(b"\xff" * page_size)

    quarantined = db._quarantine_database_files()
    db.init_db()
    result = db._salvage_from_corrupt(quarantined)

    assert db.get_config()["callsign"] == "PT2PAR"
    assert "junk" in result["failed_tables"]
    assert 0 < result["tables"]["junk"] < 400


def test_locked_database_is_not_treated_as_corruption():
    assert not db.is_corruption_error(sqlite3.OperationalError("database is locked"))
    assert db.is_corruption_error(sqlite3.DatabaseError("database disk image is malformed"))
    assert db.is_corruption_error(sqlite3.DatabaseError("file is not a database"))
    assert not db.is_corruption_error(ValueError("malformed"))
