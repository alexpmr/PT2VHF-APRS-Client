from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.12.0":
    raise SystemExit("VERSION must be 1.12.0")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.12.0"'],
    "requirements.txt": ["sgp4>="],
    "pt2vhf_aprs/v112_satellites.py": [
        "register_v112_satellite_routes",
        "/api/v112/satellites/passes",
        "CELESTRAK_AMATEUR_TLE",
        "SATNOGS_TRANSMITTERS",
        "passes_for_satellite",
        "_doppler_hz",
    ],
    "pt2vhf_aprs/web.py": ["register_v112_satellite_routes(app)"],
    "pt2vhf_aprs/database.py": [
        "_record_topology_from_raw_conn(conn, raw, medium)",
        "_repair_topology_rf_evidence_v112",
        "rf_transport_count",
        "classification_source",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'data-tab="satellites"',
        'id="satelliteMap"',
        "css/v112.css",
        "js/v112.js",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "satellitesEnabled",
        "root:satellites",
        "window.pt2vhfMainMap = state.map",
    ],
    "pt2vhf_aprs/static/js/v190.js": [
        "floatPanel('tab-log','Logs')",
        "v190-window-button v190-maximize",
        "_pt2vhfResetFloatGeometry",
        "document.querySelector('.v1818-search')?.remove();",
    ],
    "pt2vhf_aprs/static/js/v112.js": [
        "satelliteFollowSelected",
        "pt2vhf_v112_pass_notified",
        "/api/v111/notifications",
        "refreshMainMap",
    ],
    "tests/test_v112_satellites.py": [
        "test_v112_tle_parser_and_sgp4_position",
        "test_v112_rf_transport_forces_last_hop_to_igate_to_remain_rf",
        "test_v112_windows_style_floating_panels_include_logs_and_restore",
    ],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.12.0 validation failed: {needle!r} missing from {rel}")

if "DELETE FROM topology_edges WHERE kind='rf' AND igate IS NOT NULL" in read("pt2vhf_aprs/database.py"):
    raise SystemExit("v1.12.0 validation failed: destructive legacy topology migration still present")

print("v1.12.0 validation OK")
