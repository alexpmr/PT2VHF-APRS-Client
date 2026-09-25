from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "pt2vhf_aprs/diagnostics.py": [
        "def begin_request(",
        "def dump_threads(",
        "def start_watchdog(",
        "watchdog_probe_failed",
    ],
    "pt2vhf_aprs/web.py": [
        "@app.before_request",
        "/api/diagnostics/ping",
        "/api/diagnostics/status",
        "/api/diagnostics/log",
    ],
    "windows_app.py": [
        "diag.start_watchdog(URL)",
        'diag.log_event("app_start"',
    ],
    "pt2vhf_aprs/database.py": [
        "diag.log_sqlite_slow",
        "duration_ms >= 750",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "O backend local não respondeu em 10 segundos (",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.12 validation failed: {needle!r} missing from {rel}")

print("v1.6.12 diagnostic instrumentation validation OK")
