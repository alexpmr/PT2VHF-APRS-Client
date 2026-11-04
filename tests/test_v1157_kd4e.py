"""v1.15.7: relato KD4E (Raspberry Pi + Digirig), Não lidas e Salvar por sub-aba."""
import socket
import threading
from pathlib import Path

import pytest

from pt2vhf_aprs import database as db, tnc_service
from pt2vhf_aprs.aprs_service import build_beacon_packet

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_config_tab_scrolls_as_a_whole_so_tnc_subtab_is_reachable():
    css = read("pt2vhf_aprs/static/css/app.css")
    block = css[css.index("v1.14.17 - Configuração usa somente a rolagem principal da aba"):]
    host = block[:block.index("#tab-config #configForm.config-grid")]
    assert "overflow-y: auto" in host and "overflow: hidden" not in host
    form = block[block.index("#tab-config #configForm.config-grid"):]
    form = form[:form.index("}")]
    assert "height: auto" in form and "overflow: visible" in form


def test_detect_soft_tnc_finds_listening_kiss_port(monkeypatch):
    server = socket.socket(); server.bind(("127.0.0.1", 0)); server.listen(1)
    port = server.getsockname()[1]
    monkeypatch.setattr(tnc_service, "SOFT_TNC_PORTS", (("tcp", port, "KISS TCP"), ("agwpe", 1, "AGWPE")))
    try:
        found = tnc_service.detect_soft_tnc()
    finally:
        server.close()
    assert found == [{"transport": "tcp", "host": "127.0.0.1", "port": port, "label": "KISS TCP"}]


def test_digirig_is_labelled_as_audio_ptt_and_linux_permission_explains_dialout(monkeypatch):
    label, _ = tnc_service._friendly_serial_equipment({"description": "Digirig Lite CP2102N"})
    assert "Dire Wolf" in label
    monkeypatch.setattr(tnc_service.sys, "platform", "linux")
    err = tnc_service._serial_connection_error("/dev/ttyUSB0", OSError("[Errno 13] Permission denied: '/dev/ttyUSB0'"))
    assert isinstance(err, PermissionError) and "dialout" in str(err)


def test_altitude_is_optional_and_beacon_omits_it(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "alt.db")
    db.init_db()
    cfg = db.save_config({"callsign": "PY2ABC", "latitude": -15.8, "longitude": -47.9, "altitude": ""})
    db.validate_required_station_config(cfg)
    assert "/A=" not in build_beacon_packet(cfg)
    cfg = db.save_config({"altitude": 100})
    assert "/A=000328" in build_beacon_packet(cfg)


def test_units_setting_persists_and_defaults_to_metric(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "units.db")
    db.init_db()
    assert db.get_config()["units"] == "metric"
    assert db.save_config({"units": "imperial"})["units"] == "imperial"
    assert db.save_config({"units": "parsecs"})["units"] == "metric"
    html, js = read("pt2vhf_aprs/templates/index.html"), read("pt2vhf_aprs/static/js/app.js")
    assert 'id="appUnits"' in html and 'id="altitudeFeetInput"' in html
    assert "function fmtSpeedKmh(" in js and "' mph'" in js and "' mi'" in js and "' ft'" in js


def test_quit_endpoint_only_from_local_machine(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "quit.db")
    from pt2vhf_aprs import lan_access, updater, web
    # O acesso simulado pela rede não pode vazar para outros testes de LAN.
    monkeypatch.setattr(lan_access, "_last_remote", {"address": "", "path": "", "at": "", "when": 0.0})
    calls = []
    monkeypatch.setattr(updater, "_request_exit_after", lambda delay=1.25: calls.append(delay))
    # Sem threads de fundo: no Windows elas prendiam bancos temporários de outros testes.
    monkeypatch.setattr(web.scheduled_message_service, "start", lambda *a, **k: None)
    monkeypatch.setattr(web.retention, "start_worker", lambda *a, **k: None)
    monkeypatch.setattr(web.version_announce, "start_worker", lambda *a, **k: None)
    db.init_db()
    app = web.create_app()
    client = app.test_client()
    assert client.post("/api/app/quit", environ_base={"REMOTE_ADDR": "192.168.0.50"}).status_code == 403
    assert client.post("/api/app/quit", environ_base={"REMOTE_ADDR": "127.0.0.1"}).get_json()["ok"] is True
    assert calls == [0.6]


def test_unread_toggle_and_filter_scroll_to_newest():
    js = read("pt2vhf_aprs/static/js/app.js")
    handler = js[js.index("$('#unreadMessagesButton')?.addEventListener('click'"):]
    assert "scrollMessagesToNewest" in handler[:400]
    assert "debounce(() => loadMessages({ scrollToNewest: true }), 250)" in js


def test_new_strings_have_live_translations():
    live = read("pt2vhf_aprs/static/js/i18n_live.js")
    for key in ("Unidades", "Opcional", "Detectar Dire Wolf", "Sair", "Altitude (pés)",
                "Dire Wolf encontrado em", "Clique em Salvar TNC / RF e depois em Conectar TNC."):
        assert f'"{key}": [' in live
