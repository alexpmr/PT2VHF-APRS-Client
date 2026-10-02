from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.12":
    raise SystemExit(f"v1.8.12 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.12"'],
    "pt2vhf_aprs/database.py": [
        'if "medium" not in packet_columns:',
        "ALTER TABLE packets ADD COLUMN medium TEXT NOT NULL DEFAULT 'APRS-IS'",
        'if "rx_fingerprint" not in packet_columns:',
        "ALTER TABLE packets ADD COLUMN rx_fingerprint TEXT",
        "idx_packets_medium_time",
        "idx_packets_medium_call_time",
        "idx_packets_fingerprint_time",
    ],
    "tests/test_v1812_legacy_packets_migration.py": [
        "test_v1812_init_db_migrates_legacy_packets_before_medium_indexes",
        "test_v1812_medium_indexes_are_created_only_after_packet_column_migration",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.12"'],
    "CHANGELOG.md": ["## 1.8.12 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.12", "## Novidades da v1.8.12"],
    "BACKLOG.md": ["## Concluído na v1.8.12"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.12 validation failed: {needle!r} missing from {rel}")

db_source = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")
schema_end = db_source.index("        # Migração v1.7.7:")
schema_script = db_source[:schema_end]
for index_name in (
    "idx_packets_medium_time",
    "idx_packets_medium_call_time",
    "idx_packets_fingerprint_time",
):
    if index_name in schema_script:
        raise SystemExit(
            f"v1.8.12 validation failed: {index_name} created before legacy packet migration"
        )

from pt2vhf_aprs import database as db

original = db.DB_PATH
try:
    with tempfile.TemporaryDirectory() as td:
        legacy = Path(td) / "legacy_packets.db"
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
                row["name"] for row in migrated.execute("PRAGMA table_info(packets)").fetchall()
            }
            indexes = {
                row["name"] for row in migrated.execute("PRAGMA index_list(packets)").fetchall()
            }
            row = migrated.execute(
                "SELECT medium,raw FROM packets WHERE from_call='PT2OLD'"
            ).fetchone()

        if not {"medium", "rx_fingerprint"} <= columns:
            raise SystemExit("v1.8.12 validation failed: legacy packet columns were not migrated")
        required_indexes = {
            "idx_packets_medium_time",
            "idx_packets_medium_call_time",
            "idx_packets_fingerprint_time",
        }
        if not required_indexes <= indexes:
            raise SystemExit("v1.8.12 validation failed: packet indexes missing after migration")
        if not row or row["medium"] != "APRS-IS":
            raise SystemExit("v1.8.12 validation failed: legacy packet default medium")
        if row["raw"] != "PT2OLD>APRS:>legacy":
            raise SystemExit("v1.8.12 validation failed: legacy packet data was not preserved")
finally:
    db.DB_PATH = original
    db.invalidate_map_data_cache(drop_payload=True)

print("v1.8.12 legacy database migration validation OK")
