from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

db_path = ROOT / "pt2vhf_aprs" / "database.py"
js_path = ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js"

db = db_path.read_text(encoding="utf-8")
js = js_path.read_text(encoding="utf-8")

db_checks = [
    "_topology_query_lock = threading.Lock()",
    "TOPOLOGY_QUERY_MAX_SECONDS = 2.5",
    "JOIN stations s1 ON s1.callsign = e.source",
    "JOIN stations s2 ON s2.callsign = e.target",
    "conn.set_progress_handler(",
    "topology_query_coalesced",
    "topology_query_timeout",
    "idx_topology_source_target",
]
for needle in db_checks:
    if needle not in db:
        raise SystemExit(f"v1.6.16 validation failed: {needle!r} missing from database.py")

for forbidden in (
    "JOIN stations s1 ON UPPER(s1.callsign)=UPPER(e.source)",
    "JOIN stations s2 ON UPPER(s2.callsign)=UPPER(e.target)",
):
    if forbidden in db:
        raise SystemExit(f"v1.6.16 validation failed: expensive topology JOIN remains: {forbidden}")

for needle in (
    "topologyLoadBusy: false",
    "if (state.topologyLoadBusy) return;",
    "state.topologyLoadBusy = false;",
):
    if needle not in js:
        raise SystemExit(f"v1.6.16 validation failed: {needle!r} missing from app.js")

print("v1.6.16 topology query fix validation OK")
