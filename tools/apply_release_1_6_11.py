from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "pt2vhf_aprs/database.py": [
        "def _configure_database_runtime()",
        "PRAGMA busy_timeout=5000",
        "def add_outgoing_message_parts(",
    ],
    "pt2vhf_aprs/aprs_service.py": [
        "db.add_outgoing_message_parts(pending_rows)",
        "queue_message_parts",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "O backend local não respondeu em 10 segundos",
        "schedulePolling",
        "void loadMessages({ scrollToNewest:true });",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.11 validation failed: {needle!r} missing from {rel}")

db_text = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")
connection_block = db_text.split("def connection():", 1)[1].split("def init_db()", 1)[0]
if "PRAGMA journal_mode=WAL" in connection_block:
    raise SystemExit("v1.6.11 validation failed: WAL pragma still runs on every connection")

print("v1.6.11 portable stability validation OK")
