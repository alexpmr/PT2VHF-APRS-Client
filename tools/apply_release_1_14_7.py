from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.7":
    raise SystemExit("VERSION must be 1.14.7")
if '__version__ = "1.14.7"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.7")

database = read("pt2vhf_aprs/database.py")
for marker in (
    "SQLITE_BUSY_TIMEOUT_MS = 5000",
    "SQLITE_CACHE_KIB = 8192",
    "SQLITE_WAL_AUTOCHECKPOINT_PAGES = 1000",
    'conn.execute("PRAGMA temp_store=MEMORY")',
    "idx_packets_time_from_call",
    "idx_packets_medium_time",
    "idx_packets_from_call_norm_time",
    "idx_topology_kind_target_seen",
    "idx_topology_igate_seen",
    "MAP_DATA_CACHE_SECONDS = 30.0",
    "_station_position_issues_conn(conn, station_rows)",
    "Normal RX now keeps the latest snapshot until the short cache TTL",
):
    if marker not in database:
        raise SystemExit(f"v1.14.7 database marker missing: {marker}")

tnc = read("pt2vhf_aprs/tnc_service.py")
for marker in (
    "_schema_lock = threading.Lock()",
    '_schema_ready_db_path = ""',
    "if _schema_ready_db_path == db_key:",
    "_schema_ready_db_path = db_key",
):
    if marker not in tnc:
        raise SystemExit(f"v1.14.7 TNC schema guard missing: {marker}")

tests = read("tests/test_v147_release.py")
for marker in (
    "test_v147_tnc_schema_is_ensured_once_per_database_path",
    "test_v147_continuous_rx_does_not_force_immediate_map_rebuild",
    "test_v147_sqlite_runtime_and_indexes_cover_hot_paths",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.7 regression missing: {marker}")

print("v1.14.7 validation OK")
