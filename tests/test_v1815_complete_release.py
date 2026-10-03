from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1815_version_metadata():
    assert read("VERSION").strip() == "1.8.15"
    assert '__version__ = "1.8.15"' in read("pt2vhf_aprs/__init__.py")
    win = read("windows/version_info.txt")
    assert "filevers=(1, 8, 15, 0)" in win
    assert "prodvers=(1, 8, 15, 0)" in win
    assert "FileVersion', '1.8.15'" in win
    assert "ProductVersion', '1.8.15'" in win


def test_about_uses_corrected_pp5ua_callsign():
    html = read("pt2vhf_aprs/templates/index.html")
    test = read("tests/test_v1810_connection_about.py")
    assert "<strong>PP5UA</strong><span>Adriano</span>" in html
    assert '"PP5UA": "Adriano"' in test
    assert "PU5AAG" not in html


def test_message_tab_has_independent_persistent_display_filters():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    assert 'id="showNormalMessages"' in html
    assert 'id="showBulletinMessages"' in html
    assert 'id="hideTelemetryMessages"' in html
    assert "pt2vhf_show_normal_messages" in js
    assert "pt2vhf_show_bulletin_messages" in js
    assert "state.showNormalMessages" in js
    assert "state.showBulletinMessages" in js
    assert "['bulletin', 'group_bulletin', 'announcement']" in js
    assert "renderMessages();" in js


def test_map_supports_fractional_gradual_zoom_and_persists_it():
    js = read("pt2vhf_aprs/static/js/app.js")
    db = read("pt2vhf_aprs/database.py")
    assert "zoomSnap: 0.25" in js
    assert "zoomDelta: 0.25" in js
    assert "wheelPxPerZoomLevel: 120" in js
    assert "wheelDebounceTime: 25" in js
    assert "Number(saved.zoom)" in js
    assert "zoom REAL NOT NULL DEFAULT 4" in db
    assert "zoom: float" in db
    assert "float(zoom)" in db


def test_station_list_supports_icon_sorting_stable_order_and_quick_send():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    assert 'id="stationSortMode"' in html
    assert 'value="symbol_type"' in html
    assert 'data-key="symbol_type"' in html
    assert 'id="stationQuickMessagePanel"' in html
    assert 'id="stationExcludeNonMessageable"' in html
    assert "stationDisplayOrder" in js
    assert "function stationSymbolType(station)" in js
    assert "function stationMessagingSafety(station)" in js
    assert "stationMatchesViewFilter" in js
    assert "[12, 13, 14, 15].includes(ssid)" in js
    assert r"/\bDMR\b|\bD-?STAR\b|\bDSTAR\b/" in js
    assert "function openStationQuickMessage(callsign)" in js
    assert "function sendStationQuickMessage()" in js
    assert "pt2vhf_station_last_quick_message" in js
    assert "pt2vhf_station_exclude_nonmessageable" in js
    assert "Mensagem rápida" in html


def test_tnc_diagnostics_distinguish_open_transport_from_valid_frames():
    html = read("pt2vhf_aprs/templates/index.html")
    service = read("pt2vhf_aprs/tnc_service.py")
    js = read("pt2vhf_aprs/static/js/tnc.js")
    assert 'id="tncTransportDiagnostic"' in html
    assert "Kenwood TM-D700" in html
    assert "<strong>PKT</strong>" in html
    assert "transport_bytes_rx: int = 0" in service
    assert "transport_bytes_tx: int = 0" in service
    assert "kiss_frames_rx: int = 0" in service
    assert "invalid_frames_rx: int = 0" in service
    assert 'payload["rx_state"] = "bytes_without_kiss"' in service
    assert 'payload["tx_state"] = "delivered" if tx_this_session else "waiting"' in service
    assert 'self._increment_status("transport_bytes_rx", len(chunk))' in service
    assert 'self._increment_status("transport_bytes_tx", len(data))' in service
    assert "Serial conectada" in js
    assert "bytes_without_kiss" in js
    assert "emissão RF não confirmada pelo Client" in js
    assert "não mude o rádio para TNC interno" in js
