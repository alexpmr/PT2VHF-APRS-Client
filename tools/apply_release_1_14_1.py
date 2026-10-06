from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.14.1":
    raise SystemExit("VERSION must be 1.14.1")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.14.1"'],
    "pt2vhf_aprs/templates/index.html": [
        'data-tab="satellites">SAT</button>',
        '<h2>Satélites / ISS</h2>',
        'id="satelliteMap"',
        'class="satellite-card satellite-stations-card"',
        'class="satellite-card satellite-message-card"',
        'id="satelliteResetDefaults"',
        'data-sat-collapsible="beacon"',
        'data-sat-collapsible="agenda"',
        "css/v141.css",
        "js/v141.js",
    ],
    "pt2vhf_aprs/static/js/v112.js": [
        "if(raw===null)return new Set([25544])",
        "showSatelliteImmediately",
        "trackActive<4",
        "removeSatelliteLayers",
        "satelliteResetDefaults",
        "Carregando posição",
        "TLE indisponível",
    ],
    "pt2vhf_aprs/static/js/v113.js": [
        "EM PASSAGEM",
        "LOS em",
        "satName+' / '+callsign",
    ],
    "pt2vhf_aprs/static/js/v141.js": [
        "pt2vhf_v141_sat_panel_",
        "panel.open=saved==='1'",
    ],
    "pt2vhf_aprs/static/css/v141.css": [
        "justify-content:flex-start",
        "grid-template-columns:minmax(0,3fr)",
        ".satellite-secondary-panel>summary",
    ],
    "pt2vhf_aprs/static/js/v111.js": [
        "v111NotifyOpen",
        "Centro de notificações",
    ],
    "pt2vhf_aprs/static/js/v190.js": [
        "__pt2vhfV190AlertSettingsDirty",
        "void saveAlertSettings(false)",
        "if(settings.station_appeared)",
    ],
    "tests/test_v141_release.py": [
        "test_v141_only_iss_is_default_when_selection_key_is_missing",
        "test_v141_selected_satellite_renders_without_waiting_for_status_poll",
        "test_v141_top_notification_bell_removed_but_center_remains_available",
    ],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.14.1 validation failed: {needle!r} missing from {rel}")

v111 = read("pt2vhf_aprs/static/js/v111.js")
for forbidden in ("v111Bell", "🔔"):
    if forbidden in v111:
        raise SystemExit(f"v1.14.1 bell removal failed: {forbidden!r} remains")

v112 = read("pt2vhf_aprs/static/js/v112.js")
if "if(!state.status.length)return" in v112:
    raise SystemExit("v1.14.1 satellite map must not wait for periodic status polling")

win = read("windows/version_info.txt")
for needle in ("filevers=(1, 14, 1, 0)", "prodvers=(1, 14, 1, 0)", "'1.14.1'"):
    if needle not in win:
        raise SystemExit(f"v1.14.1 Windows metadata missing {needle}")

print("v1.14.1 validation OK")
