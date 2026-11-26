"""v2.0.7: assistente de primeiro uso."""
import sqlite3
from pathlib import Path

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parent.parent


def test_new_install_shows_wizard_and_skip_is_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "new.db")
    db.init_db()
    cfg = db.get_config()
    assert cfg["onboarding_done"] == 0 and not cfg["callsign"]
    assert db.save_config({"onboarding_done": 1})["onboarding_done"] == 1


def test_upgrade_with_callsign_does_not_show_wizard(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "old.db")
    db.init_db()
    db.save_config({"callsign": "PY2ABC"})
    conn = sqlite3.connect(db.DB_PATH)
    # simula banco da 2.0.6: sem as colunas novas
    cols = [r[1] for r in conn.execute("PRAGMA table_info(config)")]
    keep = [c for c in cols if c not in {name for name, _ in db.V207_CONFIG_COLUMNS}]
    conn.executescript(f"""
        CREATE TABLE config_old AS SELECT {', '.join(keep)} FROM config;
        DROP TABLE config;
        ALTER TABLE config_old RENAME TO config;
    """)
    conn.commit()
    conn.close()
    db.init_db()
    cfg = db.get_config()
    assert cfg["callsign"] == "PY2ABC" and cfg["onboarding_done"] == 1
    assert cfg["db_backup_enabled"] == 1 and cfg["gps_enabled"] == 0


def test_wizard_markup_and_script():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    js = (ROOT / "pt2vhf_aprs/static/js/onboarding.js").read_text(encoding="utf-8")
    assert 'id="onboardingModal"' in html and "js/onboarding.js" in html
    assert "onboarding_done: 1" in js and "serverForPosition" in js
    assert "window.pt2vhfStationHelpers" in (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
