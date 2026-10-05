from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.10.1":
    raise SystemExit("VERSION must be 1.10.1")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.10.1"'],
    "pt2vhf_aprs/v190_features.py": ["active_stations", "disappeared", "/api/v190/alerts/settings"],
    "pt2vhf_aprs/static/js/v190.js": [
        "previousActive=null", "seenMessageIds", "databaseProblemLatched",
        "tncWanted=state.tnc?.wanted!==false", "aprsWanted=state.aprs_is?.wanted!==false",
        "window.__pt2vhfV190AlertSettings", "saveAlertSettings",
    ],
    "tests/test_v190_features.py": [
        "test_v190_alert_settings_preserve_false_values",
        "test_v190_alert_state_separates_active_from_disappeared_stations",
        "test_v190_frontend_alerts_are_edge_triggered_and_deduplicated",
    ],
    ".github/workflows/build-production-current.yml": ["apply_release_1_10_1.py"],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.10.1 validation failed: {needle!r} missing from {rel}")
print("v1.10.1 validation OK")
