"""v1.14.46: UI de automacoes, RX/TX unificado e posicoes APRS invalidas."""
from pathlib import Path
import tempfile
import pytest

from pt2vhf_aprs import database as db, topology_map
from pt2vhf_aprs.aprs_service import APRSService

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_automations_tab_migrates_config_not_duplicate():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/v111.js")
    assert 'data-tab="automations"' in html
    assert 'id="tab-automations"' in html
    assert "const config=$('#automationsGrid')" in js
    assert "const config=$('#tab-config');if(!config||$('#v148AutoReply'))return;" not in js
    for marker in ("v148AutoReplyEnabled", "v148AutoReplyText",
                   "v148AutoReplyCooldown", "auto_reply_enabled", "auto_reply_text"):
        assert marker in js
    assert "Informe o texto da Auto-resposta antes de ativar." in js


def test_tx_rx_indicators_cover_both_transports_independently():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    for marker in ('class="traffic-label">TX', 'class="traffic-label">RX',
                   'class="traffic-led traffic-tx"', 'class="traffic-led traffic-rx"'):
        assert marker in html
    for marker in ("status.tnc || {}", "tnc.transport_bytes_rx",
                   "tnc.transport_bytes_tx", "state.trafficIndicatorTimers[direction]",
                   "trafficIndicatorBaseline"):
        assert marker in js
    assert "trafficIndicatorTimer:" not in js
    assert ".traffic-activity-indicator.tx-active .traffic-tx" in css
    assert ".traffic-activity-indicator.rx-active .traffic-rx" in css


@pytest.mark.parametrize(("raw", "issue"), [
    ("PP5BLU-15>APBK20,WIDE1-1,WIDE2-1,qAR,PP5APR-10:!2677.84S/04900.03W#PHG7190", "invalid_aprs_minutes"),
    ("PP5BLU-15>APRS:!2659.99S/04900.03W#Teste", None),
    ("PP5BLU-15>APRS:!2660.00S/04900.03W#Erro", "invalid_aprs_minutes"),
    ("PP5BLU-15>APRS:!2644.21S/04960.00W#Erro", "invalid_aprs_minutes"),
    ("PP5BLU-15>APRS:!9044.21S/04900.03W#Erro", "invalid_aprs_degrees"),
    ("PP5BLU-15>APRS:!2633.44S/04900.03W#Teste", None),
    ("PP5BLU-15>APRS:/123456z2677.84S/04900.03W#Invalido", "invalid_aprs_minutes"),
    ("PP5BLU-15>APRS:;DIGI     *123456z2677.84S/04900.03W#Invalido", "invalid_aprs_minutes"),
    ("PP5BLU-15>APRS:)DIGI!2677.84S/04900.03W#Invalido", "invalid_aprs_minutes"),
    ("PP5BLU-15>APRS:!/5J test compressed", None),
])
def test_raw_aprs_position_validation(raw, issue):
    assert db.raw_aprs_position_issue(raw) == issue


def test_invalid_position_keeps_packet_but_not_station_coordinates():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "invalid.db"
            db.init_db()
            raw = ("PP5BLU-15>APBK20,WIDE1-1,WIDE2-1,qAR,PP5APR-10:"
                   "!2677.84S/04900.03W#PHG7190Digipeater")
            parsed = {"from": "PP5BLU-15", "format": "uncompressed",
                      "latitude": -27.297333, "longitude": -49.0005,
                      "path": ["WIDE1-1", "WIDE2-1", "qAR", "PP5APR-10"], "raw": raw}
            db.process_received_packet(raw, parsed, "PP5BLU-15", "uncompressed")
            with db.connection() as conn:
                assert conn.execute("SELECT COUNT(*) FROM packets").fetchone()[0] == 1
                assert conn.execute("SELECT COUNT(*) FROM topology_events").fetchone()[0] == 0
                item = conn.execute("SELECT latitude,longitude FROM stations WHERE callsign='PP5BLU-15'").fetchone()
                assert item is not None
                assert item["latitude"] is None and item["longitude"] is None
                assert conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0] == 0
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_historic_malformed_raw_excluded_from_map():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "history.db"
            db.init_db()
            with db.connection() as conn:
                conn.execute(
                    """INSERT INTO topology_events(
                        timestamp,source,target,kind,medium,evidence_level,
                        source_lat,source_lon,target_lat,target_lon,raw)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (db.utc_now_iso(), "PP5BLU-15", "PP5APR-10", "rf",
                     "APRS-IS", "inferred", -27.297333, -49.0005,
                     -26.5, -48.9, "PP5BLU-15>APRS:!2677.84S/04900.03W#"),
                )
            assert topology_map.list_map_edges() == []
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_distinct_private_messages_reply_but_duplicate_suppressed(monkeypatch):
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "autoreply.db"
            db.init_db()
            db.save_config({"callsign": "PT2VHF", "ssid": 0,
                            "latitude": -15.8, "longitude": -47.9,
                            "auto_reply_enabled": True, "auto_reply_text": "Estou ausente",
                            "auto_reply_cooldown_seconds": 300})
            service = APRSService()
            sent = []
            monkeypatch.setattr(service, "queue_message_parts",
                                lambda *args, **kwargs: sent.append((args, kwargs)) or {"row_ids": [1]})
            for message, msg_id in [("Primeira", "ABC"), ("Segunda", "DEF"),
                                    ("Primeira", "ABC"), ("Auto-resposta: teste", "GHI")]:
                text = message + "{" + msg_id
                raw = "PY2ABC-9>APRS::PT2VHF  :" + text
                service._handle_message({"from": "PY2ABC-9", "to": "PT2VHF", "text": text}, raw)
            assert len(sent) == 2
            assert [x[0][1] for x in sent] == ["Estou ausente", "Estou ausente"]
            assert all(x[1]["automated"] is True for x in sent)
    finally:
        db.DB_PATH = original
