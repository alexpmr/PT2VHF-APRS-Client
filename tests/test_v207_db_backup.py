"""v2.0.7: cópia automática do banco e restauração na próxima abertura."""
import gzip
import sqlite3
from pathlib import Path

import pytest

from pt2vhf_aprs import database as db, db_backup


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "pt2vhf_aprs.db")
    monkeypatch.setattr(db_backup, "LAST_RESTORE", None)
    db.init_db()
    return tmp_path


def _callsign() -> str:
    return db.get_config()["callsign"]


def test_backup_is_checked_compressed_and_pruned(data_dir):
    names = []
    for index in range(4):
        result = db_backup.make_backup(keep=3)
        assert result["ok"], result
        names.append(result["name"])
        # nomes têm resolução de segundo; força nomes distintos
        (data_dir / "backups" / result["name"]).rename(data_dir / "backups" / f"pt2vhf_aprs_2026010{index + 1}-000000.db.gz")
    db_backup._prune(3)
    listed = db_backup.list_backups()
    assert len(listed) == 3 and listed[0]["name"].startswith("pt2vhf_aprs_20260104")
    raw = gzip.decompress((data_dir / "backups" / listed[0]["name"]).read_bytes())
    assert raw.startswith(b"SQLite format 3")


def test_restore_happens_on_next_start_and_keeps_previous_db(data_dir):
    db.save_config({"callsign": "PY2ABC"})
    backup = db_backup.make_backup(keep=7)
    assert backup["ok"]
    db.save_config({"callsign": "PU2XYZ"})
    assert _callsign() == "PU2XYZ"

    db_backup.schedule_restore(backup["name"])
    assert db_backup.pending_restore()["name"] == backup["name"]
    db.init_db()  # próxima abertura
    assert _callsign() == "PY2ABC"
    assert db_backup.pending_restore() is None
    assert db_backup.LAST_RESTORE["ok"]
    kept = list((data_dir / "before_restore").glob("*/pt2vhf_aprs.db"))
    assert kept and sqlite3.connect(kept[0]).execute("SELECT callsign FROM config").fetchone()[0] == "PU2XYZ"


def test_bad_backup_never_replaces_the_database(data_dir):
    db.save_config({"callsign": "PY2ABC"})
    folder = data_dir / "backups"
    folder.mkdir(exist_ok=True)
    bad = folder / "pt2vhf_aprs_20260101-000000.db.gz"
    bad.write_bytes(gzip.compress(b"isto nao e um banco"))
    db_backup.schedule_restore(bad.name)
    db.init_db()
    assert _callsign() == "PY2ABC"
    assert db_backup.LAST_RESTORE and not db_backup.LAST_RESTORE["ok"]
    assert db_backup.pending_restore() is None
    with pytest.raises(ValueError):
        db_backup.schedule_restore("../../etc/passwd")


def test_backup_due_and_config_defaults(data_dir):
    assert db_backup.backup_due()
    db_backup.make_backup(keep=7)
    assert not db_backup.backup_due()
    cfg = db.get_config()
    assert cfg["db_backup_enabled"] == 1 and cfg["db_backup_keep"] == 7
    assert db.save_config({"db_backup_keep": 99})["db_backup_keep"] == 30


def test_api_and_ui(data_dir):
    from pt2vhf_aprs.web import create_app
    client = create_app().test_client()
    assert client.post("/api/db/backups").get_json()["ok"]
    data = client.get("/api/db/backups").get_json()
    assert len(data["backups"]) == 1 and data["backups"][0]["manual"]
    name = data["backups"][0]["name"]
    assert client.post("/api/db/backups/restore", json={"name": name}, environ_base={"REMOTE_ADDR": "192.168.0.9"}).status_code == 403
    assert client.post("/api/db/backups/restore", json={"name": name}).get_json()["ok"]
    assert client.post("/api/db/backups/cancel-restore").get_json()["ok"]
    html = (Path(__file__).resolve().parent.parent / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    assert 'id="dbBackupCard"' in html and 'name="db_backup_enabled"' in html and "js/db_backup.js" in html
