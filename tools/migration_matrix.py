from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from pt2vhf_aprs import database as db

PROFILES = ["1.6.x", "1.7.x", "1.8.0", "1.8.4", "1.8.10", "1.8.18", "1.9.0", "new"]


def _seed_legacy(path: Path, profile: str) -> dict:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE config(
              id INTEGER PRIMARY KEY,
              callsign TEXT NOT NULL DEFAULT '',
              ssid INTEGER NOT NULL DEFAULT 0,
              comment TEXT NOT NULL DEFAULT '',
              latitude REAL, longitude REAL, altitude REAL,
              symbol_table TEXT NOT NULL DEFAULT '/', symbol TEXT NOT NULL DEFAULT '>',
              beacon_minutes INTEGER NOT NULL DEFAULT 10,
              email TEXT NOT NULL DEFAULT '', server TEXT NOT NULL DEFAULT 'soam.aprs2.net',
              port INTEGER NOT NULL DEFAULT 14580, passcode TEXT NOT NULL DEFAULT '',
              aprs_filter TEXT NOT NULL DEFAULT '', connect_on_start INTEGER NOT NULL DEFAULT 1,
              updated_at TEXT
            );
            INSERT INTO config(id,callsign,ssid,comment) VALUES(1,'PT2TEST',15,'migration-test');
            CREATE TABLE stations(
              callsign TEXT PRIMARY KEY,name TEXT,last_heard TEXT,latitude REAL,longitude REAL,
              speed REAL,course REAL,altitude REAL,info TEXT,symbol_table TEXT,symbol TEXT,
              message_capable INTEGER DEFAULT 0,path TEXT,packet_format TEXT,raw TEXT
            );
            INSERT INTO stations(callsign,name,last_heard) VALUES('PY2ABC','Teste','2026-01-01T00:00:00+00:00');
            CREATE TABLE messages(
              id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT,direction TEXT,from_call TEXT,to_call TEXT,
              message TEXT,message_id TEXT,status TEXT,acked_at TEXT
            );
            INSERT INTO messages(timestamp,direction,from_call,to_call,message) VALUES('2026-01-01T00:00:00+00:00','in','PY2ABC','PT2TEST-15','hello');
            CREATE TABLE packets(
              id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT,raw TEXT,from_call TEXT,to_call TEXT,path TEXT,
              packet_format TEXT,latitude REAL,longitude REAL,message_text TEXT
            );
            INSERT INTO packets(timestamp,raw,from_call) VALUES('2026-01-01T00:00:00+00:00','PY2ABC>APRS:>test','PY2ABC');
            CREATE TABLE tracks(
              id INTEGER PRIMARY KEY AUTOINCREMENT,callsign TEXT,timestamp TEXT,latitude REAL,longitude REAL,
              speed REAL,course REAL,altitude REAL
            );
            INSERT INTO tracks(callsign,timestamp,latitude,longitude) VALUES('PY2ABC','2026-01-01T00:00:00+00:00',-15.8,-47.9);
            CREATE TABLE favorites(callsign TEXT PRIMARY KEY,created_at TEXT);
            INSERT INTO favorites(callsign,created_at) VALUES('PY2ABC','2026-01-01T00:00:00+00:00');
            """
        )
        if profile in {"1.8.18", "1.9.0"}:
            conn.execute("ALTER TABLE packets ADD COLUMN medium TEXT NOT NULL DEFAULT 'APRS-IS'")
            conn.execute("ALTER TABLE packets ADD COLUMN rx_fingerprint TEXT")
        conn.commit()
    finally:
        conn.close()
    return {"stations": 1, "messages": 1, "packets": 1, "tracks": 1, "favorites": 1}


def run_matrix() -> list[dict]:
    results = []
    original = db.DB_PATH
    try:
        for profile in PROFILES:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "legacy.db"
                before = _seed_legacy(path, profile)
                db.DB_PATH = path
                db.init_db()
                with db.connection() as conn:
                    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                    after = {
                        table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                        for table in before
                    }
                    packet_cols = {row["name"] for row in conn.execute("PRAGMA table_info(packets)").fetchall()}
                    config_cols = {row["name"] for row in conn.execute("PRAGMA table_info(config)").fetchall()}
                ok = integrity == "ok" and after == before and {"medium", "rx_fingerprint"} <= packet_cols and "language" in config_cols
                results.append({"profile": profile, "ok": ok, "integrity": integrity, "before": before, "after": after})
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)
    return results


if __name__ == "__main__":
    result = run_matrix()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not all(row["ok"] for row in result):
        raise SystemExit(1)
