from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.11.0":
    raise SystemExit("VERSION must be 1.11.0")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.11.0"'],
    "pt2vhf_aprs/v111_features.py": [
        "/api/v111/tnc/health", "/api/v111/tnc/self-test",
        "/api/v111/notifications", "/api/v111/db/health",
        "/api/v111/db/retention", "/api/v111/db/optimize",
        "/api/v111/station/", "station_operational_profile",
    ],
    "pt2vhf_aprs/static/js/v111.js": [
        "v111NotifyOpen", "v111TncSelfTest", "v111DbHealth",
        "Ouvido por", "Copiar diagnóstico", "Executar teste completo",
    ],
    "pt2vhf_aprs/static/css/v111.css": [".v111-notify-panel", ".v111-counter-grid"],
    "pt2vhf_aprs/templates/index.html": ["css/v111.css", "js/v111.js"],
    "pt2vhf_aprs/tnc_service.py": [
        "session_persisted_frames_rx", "session_persisted_frames_tx",
        "tnc_status_counter_reconcile_error",
    ],
    "pt2vhf_aprs/static/js/v190.js": [
        "previousActive=null", "seenMessageIds", "databaseProblemLatched",
        "window.pt2vhfNotificationCenterPush",
    ],
    "tests/test_v111_operational_reliability.py": [
        "test_v111_tnc_self_test_covers_rx_tx_ack",
        "test_v111_tnc_status_reconciles_persisted_session_frames",
        "test_v111_station_operational_profile_heard_by_and_paths",
    ],
    ".github/workflows/build-production-current.yml": ["apply_release_1_11_0.py"],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.11.0 validation failed: {needle!r} missing from {rel}")
print("v1.11.0 validation OK")
