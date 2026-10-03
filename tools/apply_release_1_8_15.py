from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


version = read("VERSION").strip()
if version != "1.8.15":
    raise SystemExit(f"v1.8.15 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.15"'],
    "windows/version_info.txt": [
        "filevers=(1, 8, 15, 0)",
        "prodvers=(1, 8, 15, 0)",
        "FileVersion', '1.8.15'",
        "ProductVersion', '1.8.15'",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="showNormalMessages"',
        'id="showBulletinMessages"',
        'id="stationSortMode"',
        'id="stationQuickMessagePanel"',
        'id="stationExcludeNonMessageable"',
        'id="tncTransportDiagnostic"',
        "<strong>PP5UA</strong><span>Adriano</span>",
        "Kenwood TM-D700",
        "<strong>PKT</strong>",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "zoomSnap: 0.25",
        "zoomDelta: 0.25",
        "wheelPxPerZoomLevel: 120",
        "pt2vhf_show_normal_messages",
        "pt2vhf_show_bulletin_messages",
        "stationDisplayOrder",
        "function stationMessagingSafety(station)",
        "function sendStationQuickMessage()",
        "stationMatchesViewFilter",
    ],
    "pt2vhf_aprs/database.py": [
        "zoom REAL NOT NULL DEFAULT 4",
        "def save_map_state(latitude: float, longitude: float, zoom: float)",
        "float(zoom)",
    ],
    "pt2vhf_aprs/tnc_service.py": [
        "transport_bytes_rx: int = 0",
        "transport_bytes_tx: int = 0",
        "kiss_frames_rx: int = 0",
        "invalid_frames_rx: int = 0",
        'payload["rx_state"] = "bytes_without_kiss"',
        'self._increment_status("transport_bytes_rx", len(chunk))',
        'self._increment_status("transport_bytes_tx", len(data))',
    ],
    "pt2vhf_aprs/static/js/tnc.js": [
        "Serial conectada",
        "bytes_without_kiss",
        "emissão RF não confirmada pelo Client",
        "não mude o rádio para TNC interno",
    ],
    "tests/test_v1815_complete_release.py": [
        "test_message_tab_has_independent_persistent_display_filters",
        "test_map_supports_fractional_gradual_zoom_and_persists_it",
        "test_station_list_supports_icon_sorting_stable_order_and_quick_send",
        "test_tnc_diagnostics_distinguish_open_transport_from_valid_frames",
    ],
}

missing = []
for rel, snippets in checks.items():
    text = read(rel)
    for snippet in snippets:
        if snippet not in text:
            missing.append(f"{rel}: {snippet}")

if "PU5AAG" in read("pt2vhf_aprs/templates/index.html"):
    missing.append("pt2vhf_aprs/templates/index.html: obsolete PU5AAG")

if missing:
    raise SystemExit("v1.8.15 validation failed:\n- " + "\n- ".join(missing))

print("v1.8.15 production validation OK")
