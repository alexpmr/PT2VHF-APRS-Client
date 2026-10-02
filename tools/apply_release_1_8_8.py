from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.8":
    raise SystemExit(f"v1.8.8 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.8"'],
    "pt2vhf_aprs/database.py": [
        "def _interaction_calls_conn(",
        "def _build_map_data_uncached(",
        "def map_data(*, force: bool = False)",
        "_map_data_build_lock = threading.Lock()",
        "MAP_DATA_CACHE_SECONDS = 15.0",
        'source="stale-cache"',
        "map_data_singleflight_busy",
        "map_data_build",
        "idx_messages_interaction_in",
        "idx_messages_interaction_out",
        "idx_aprs_queries_interaction",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "data?._meta?.source === 'busy-empty'",
        "}, 15000);",
    ],
    "pt2vhf_aprs/tnc_service.py": [
        "full_scan: bool = True",
        "cached_age < 60.0",
        "if full_scan and sys.platform == \"win32\":",
        'cached["source"] = "cached_metadata"',
    ],
    "pt2vhf_aprs/web.py": [
        'request.args.get("quick")',
        "available_ports(force=force, full_scan=not quick)",
    ],
    "pt2vhf_aprs/static/js/tnc.js": [
        "serialPollTick % 10 === 0",
        "loadPorts({quiet:true, quick:true})",
        "params.set('quick', '1')",
    ],
    "tests/test_v188_performance.py": [
        "test_v188_map_data_singleflight_never_runs_duplicate_heavy_builds",
        "test_v188_concurrent_map_call_uses_stale_snapshot_immediately",
        "test_v188_interaction_query_is_set_based_not_correlated_per_station",
        "test_v188_frontend_reduces_full_map_and_serial_polling",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.8"'],
    "CHANGELOG.md": ["## 1.8.8 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.8", "## Novidades da v1.8.8"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.8 validation failed: {needle!r} missing from {rel}")

database = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")
for func_start, func_end in (
    ("def list_stations(", "def _is_topology_callsign"),
    ("def _build_map_data_uncached(", "def map_data("),
):
    block = database[database.index(func_start):database.index(func_end, database.index(func_start))]
    if "OR EXISTS (" in block:
        raise SystemExit(f"v1.8.8 validation failed: correlated EXISTS remains in {func_start}")

tnc_js = (ROOT / "pt2vhf_aprs/static/js/tnc.js").read_text(encoding="utf-8")
if "serialPollTick % 2 === 0" in tnc_js:
    raise SystemExit("v1.8.8 validation failed: 6-second serial rescan still present")

print("v1.8.8 performance, map single-flight and lightweight serial polling validation OK")
