from pathlib import Path
import sqlite3
import tempfile

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1812_init_db_migrates_legacy_packets_before_medium_indexes():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            legacy = Path(td) / "legacy.db"
            conn = sqlite3.connect(legacy)
            try:
                conn.executescript(
                    """
                    CREATE TABLE packets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        from_call TEXT,
                        packet_format TEXT,
                        raw TEXT NOT NULL
                    );
                    CREATE INDEX idx_packets_time ON packets(timestamp DESC);
                    INSERT INTO packets(timestamp,from_call,packet_format,raw)
                    VALUES('2026-10-02T20:00:00+00:00','PT2OLD','status','PT2OLD>APRS:>legacy');
                    """
                )
                conn.commit()
            finally:
                conn.close()

            db.DB_PATH = legacy
            db.init_db()

            with db.connection() as migrated:
                columns = {
                    row["name"]: row
                    for row in migrated.execute("PRAGMA table_info(packets)").fetchall()
                }
                indexes = {
                    row["name"]
                    for row in migrated.execute("PRAGMA index_list(packets)").fetchall()
                }
                row = migrated.execute(
                    "SELECT medium,rx_fingerprint FROM packets WHERE from_call='PT2OLD'"
                ).fetchone()

            assert "medium" in columns
            assert "rx_fingerprint" in columns
            assert "idx_packets_medium_time" in indexes
            assert "idx_packets_medium_call_time" in indexes
            assert "idx_packets_fingerprint_time" in indexes
            assert row["medium"] == "APRS-IS"
            assert row["rx_fingerprint"] is None
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_v1812_medium_indexes_are_created_only_after_packet_column_migration():
    source = read("pt2vhf_aprs/database.py")
    script_end = source.index('        # Migração v1.7.7:')
    schema_script = source[:script_end]
    migration_start = source.index('packet_columns = {row["name"]')
    migration_end = source.index('config_columns = {row["name"]', migration_start)
    migration = source[migration_start:migration_end]

    assert "idx_packets_medium_time" not in schema_script
    assert "idx_packets_medium_call_time" not in schema_script
    assert "idx_packets_fingerprint_time" not in schema_script
    assert 'if "medium" not in packet_columns:' in migration
    assert 'ALTER TABLE packets ADD COLUMN medium' in migration
    assert 'if "rx_fingerprint" not in packet_columns:' in migration
    assert 'ALTER TABLE packets ADD COLUMN rx_fingerprint' in migration
    assert migration.index('ALTER TABLE packets ADD COLUMN medium') < migration.index('idx_packets_medium_time')
    assert migration.index('ALTER TABLE packets ADD COLUMN rx_fingerprint') < migration.index('idx_packets_fingerprint_time')


def test_v1812_migration_remains_covered_in_newer_versions():
    version = tuple(int(part) for part in read("VERSION").strip().split("."))
    assert version >= (1, 8, 12)
    init_source = read("pt2vhf_aprs/__init__.py")
    assert f'__version__ = "{read("VERSION").strip()}"' in init_source
