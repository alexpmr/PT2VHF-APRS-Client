from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.14.0":
    raise SystemExit("VERSION must be 1.14.0")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.14.0"'],
    "pt2vhf_aprs/v114_satellite_ops.py": [
        "register_v114_routes",
        "next_selected_aprs_pass",
        "satellite_stations",
        "queue_satellite_beacon",
        "satellite_beacon_history_v114",
        "/api/v114/satellites/next-pass",
        "/api/v114/satellites/stations",
        "/api/v114/satellites/<int:norad_id>/beacon/preview",
    ],
    "pt2vhf_aprs/web.py": ["register_v114_routes(app)"],
    "pt2vhf_aprs/tnc_service.py": [
        "def queue_satellite_beacon(",
        "Beacon satélite bloqueado pelas regras de transmissão do TNC.",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="satelliteSelectionPanel"',
        'id="satelliteQuickSearch"',
        'id="satelliteTabCountdown"',
        'id="satelliteStationsList"',
        'id="satelliteMessageTo"',
        'id="satelliteBeaconPath"',
        "css/v114.css",
        "js/v114.js",
    ],
    "pt2vhf_aprs/static/js/v112.js": [
        "visibleCatalogRows",
        "pt2vhf:satellite-selection-changed",
        "satelliteQuickSearch",
    ],
    "pt2vhf_aprs/static/js/v113.js": [
        "/api/v114/satellites/next-pass",
        "pt2vhf_v112_satellite_selected",
        "pt2vhf_v112_satellite_favorites",
    ],
    "pt2vhf_aprs/static/js/v114.js": [
        "/api/messages/send",
        "/api/messages?mine=1",
        "/api/v114/satellites/stations",
        "sendBeacon",
        "previewBeacon",
        "shiftKey",
    ],
    "pt2vhf_aprs/static/js/v111.js": [
        "tab.insertBefore(host",
        "host.parentElement!==tab",
    ],
    "tests/test_v114_release.py": [
        "test_v114_next_pass_honors_eligible_satellites",
        "test_v114_satellite_tab_has_stations_messages_and_shared_message_api",
        "test_v114_tnc_health_component_is_owned_by_tnc_tab_only",
    ],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.14.0 validation failed: {needle!r} missing from {rel}")

nav = read("pt2vhf_aprs/templates/index.html")
nav = nav[nav.index('<nav class="tabs"'):nav.index("</nav>", nav.index('<nav class="tabs"'))]
if 'id="satelliteTabCountdown"' in nav:
    raise SystemExit("v1.14.0 countdown must not remain inside the top tabs")

win = read("windows/version_info.txt")
for needle in ("filevers=(1, 14, 0, 0)", "prodvers=(1, 14, 0, 0)", "'1.14.0'"):
    if needle not in win:
        raise SystemExit(f"v1.14.0 Windows metadata missing {needle}")

print("v1.14.0 validation OK")
