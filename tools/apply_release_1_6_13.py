from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "pt2vhf_aprs/database.py": [
        "def _retention_due(",
        "def _trim_history_table(",
        'if _retention_due("packets")',
        'if _retention_due("aprs_log")',
        'if _retention_due("topology_events", len(edges))',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "if (state.activeTab === 'map') await loadMapData();",
        "if (state.activeTab === 'messages') await loadMessages();",
        "schedulePolling(refreshStatus, 3000);",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.13 validation failed: {needle!r} missing from {rel}")

db = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")
for forbidden in (
    "DELETE FROM packets WHERE id NOT IN",
    "DELETE FROM aprs_log WHERE id NOT IN",
    "DELETE FROM topology_events WHERE id NOT IN",
):
    if forbidden in db:
        raise SystemExit(f"v1.6.13 validation failed: expensive per-packet cleanup remains: {forbidden}")

print("v1.6.13 CPU/SQLite optimization validation OK")
