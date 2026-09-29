import pytest
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db
from pt2vhf_aprs import updater
from pt2vhf_aprs.aprs_service import APRSService, build_beacon_packet, build_bulletin_packet, build_query_payload, calculate_aprs_passcode, classify_message_type, expand_filter, mask_sensitive_log_line, parse_message_line, parse_query_text, parse_trace_nodes, split_message_id, split_aprs_message_parts
from pt2vhf_aprs.web import _kml_document, version_tuple


def test_beacon_packet():
    cfg = {
        "callsign": "PT2VHF", "ssid": 15, "latitude": -15.8, "longitude": -47.9,
        "altitude": 1000, "symbol_table": "/", "symbol": ">", "comment": "Teste"
    }
    packet = build_beacon_packet(cfg)
    assert packet.startswith("PT2VHF-15>APZVHF,TCPIP*:=1548.00S/04754.00W>")
    assert "/A=003281" in packet


def test_filter_shortcut():
    cfg = {"latitude": -15.8, "longitude": -47.9}
    assert expand_filter("r/2000", cfg) == "r/-15.80000/-47.90000/2000"
    assert expand_filter("m/50", cfg) == "m/50"


def test_message_parser_with_id():
    raw = "PY2ABC>APRS,TCPIP*::PT2VHF   :Teste de mensagem{123"
    msg = parse_message_line(raw, {})
    assert msg == {"from": "PY2ABC", "to": "PT2VHF", "text": "Teste de mensagem{123"}
    text, mid = split_message_id(msg["text"])
    assert text == "Teste de mensagem"
    assert mid == "123"



def test_aprs_query_helpers():
    assert parse_query_text("?APRSP") == ("APRSP", "")
    assert parse_query_text("?APRSS") == ("APRSS", "")
    assert parse_query_text("?PING?") == ("PING", "")
    assert parse_query_text("?APRSH PY2ABC-9") == ("APRSH", "PY2ABC-9")
    assert build_query_payload("APRST") == "?APRST"
    assert build_query_payload("PING") == "?PING?"
    assert build_query_payload("APRSH", "PY2ABC-9").startswith("?APRSH PY2ABC-9")
    assert parse_trace_nodes("PT2VHF>APRS,PT2DIGI*,WIDE2-1:") == ["PT2VHF", "PT2DIGI", "WIDE2-1"]


def test_aprs_query_database_lifecycle():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF", "ssid": 0,
                "latitude": -15.8, "longitude": -47.9, "altitude": 1000,
                "respond_to_queries": True,
            })
            qid = db.add_aprs_query("out", "PY2ABC-9", "APRST", "?APRST")
            assert db.get_aprs_query(qid)["status"] == "Aguardando resposta"
            resolved = db.resolve_aprs_query_response(
                "PY2ABC-9", ["APRST"],
                "PT2VHF>APRS,PT2DIGI*:",
                "PY2ABC-9>APRS::PT2VHF  :PT2VHF>APRS,PT2DIGI*:",
                trace_path=["PT2VHF", "PT2DIGI"],
            )
            assert resolved and resolved["status"] == "Respondida"
            assert resolved["rtt_ms"] is not None
            detail = db.aprs_query_detail(qid)
            assert detail["trace_path_list"] == ["PT2VHF", "PT2DIGI"]
    finally:
        db.DB_PATH = original


def test_aprs_service_sends_standard_query_without_message_id(monkeypatch):
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF", "ssid": 0,
                "latitude": -15.8, "longitude": -47.9, "altitude": 1000,
            })
            service = APRSService()
            service._set_status(connected=True, verified=True)
            # A primeira query não pode cair no rate-limit mesmo se o uptime
            # monotônico do runner ainda for inferior a 30 segundos.
            monkeypatch.setattr("pt2vhf_aprs.aprs_service.time.monotonic", lambda: 5.0)
            sent = []
            monkeypatch.setattr(service, "_send_raw", sent.append)
            result = service.send_query("PY2ABC-9", "APRSP")
            assert result["query_type"] == "APRSP"
            assert sent == ["PT2VHF>APZVHF,TCPIP*::PY2ABC-9 :?APRSP"]
            assert "{" not in sent[0]
    finally:
        db.DB_PATH = original


def test_aprs_service_auto_responds_to_position_query(monkeypatch):
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF", "ssid": 0,
                "latitude": -15.8, "longitude": -47.9, "altitude": 1000,
                "respond_to_queries": True,
            })
            service = APRSService()
            service._set_status(connected=True, verified=True)
            sent = []
            monkeypatch.setattr(service, "_send_raw", sent.append)
            service._handle_message(
                {"from": "PY2ABC-9", "to": "PT2VHF", "text": "?APRSP"},
                "PY2ABC-9>APRS,TCPIP*::PT2VHF   :?APRSP",
            )
            assert sent and sent[0].startswith("PT2VHF>APZVHF,TCPIP*:=")
            incoming = db.list_aprs_queries("PY2ABC-9", 10)
            assert incoming[0]["direction"] == "in"
            assert incoming[0]["status"] == "Respondida"
    finally:
        db.DB_PATH = original

def test_database_config_and_station():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            cfg = db.save_config({"callsign": "PT2VHF", "ssid": 0, "latitude": -15.8, "longitude": -47.9, "altitude": 1000})
            assert cfg["callsign"] == "PT2VHF"
            db.upsert_station({
                "from": "PY2ABC-9", "format": "uncompressed", "latitude": -15.81, "longitude": -47.91,
                "speed": 42.0, "course": 90, "altitude": 1100, "symbol_table": "/", "symbol": ">",
                "comment": "Movel", "path": ["WIDE1-1"], "raw": "x"
            })
            rows = db.list_stations()
            assert len(rows) == 1
            assert rows[0]["distance_km"] is not None
    finally:
        db.DB_PATH = original


def test_mask_sensitive_log_line():
    line = "user PT2VHF pass 12345 vers PT2VHFAPRSClient 0.2.1 filter r/-15.8/-47.9/500"
    masked = mask_sensitive_log_line(line)
    assert "12345" not in masked
    assert "pass ******" in masked
    assert masked.startswith("user PT2VHF ")


def test_aprs_log_rx_tx():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.add_aprs_log("RX", "PY2ABC>APRS:teste")
            db.add_aprs_log("TX", "PT2VHF>APRS:teste")
            rows = db.list_aprs_log(limit=10)
            assert [row["direction"] for row in rows] == ["TX", "RX"]
            assert rows[0]["raw"].startswith("PT2VHF")
            tx = db.list_aprs_log(direction="TX", limit=10)
            assert len(tx) == 1
            db.clear_aprs_log()
            assert db.list_aprs_log(limit=10) == []
    finally:
        db.DB_PATH = original


def test_bulletin_packets():
    packet, addressee, message_type, text = build_bulletin_packet(
        source="PT2VHF-9",
        text="Boletim geral de teste",
        bulletin_id="1",
    )
    assert packet == "PT2VHF-9>APZVHF,TCPIP*::BLN1     :Boletim geral de teste"
    assert addressee == "BLN1"
    assert message_type == "bulletin"
    assert "{" not in packet

    group_packet, group_to, group_type, _ = build_bulletin_packet(
        source="PT2VHF-9",
        text="Boletim do grupo DF",
        bulletin_id="2",
        group="DF",
    )
    assert group_packet == "PT2VHF-9>APZVHF,TCPIP*::BLN2DF   :Boletim do grupo DF"
    assert group_to == "BLN2DF"
    assert group_type == "group_bulletin"
    assert classify_message_type("BLN2DF") == "group_bulletin"
    assert classify_message_type("BLN1") == "bulletin"
    assert classify_message_type("PY2ABC-9") == "message"


def test_map_preferences_persist():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            cfg = db.save_config({
                "callsign": "PT2VHF",
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": 1000,
                "map_type": "satellite",
                "track_color": "#ff6600",
                "track_width": 5,
                "topology_rf_color": "#11aa22",
                "topology_igate_color": "#8844cc",
                "topology_width": 4,
                "map_brightness": 80,
                "sound_on_personal_message": False,
                "message_popup_seconds": 9,
                "open_browser_on_start": True,
                "app_theme": "light",
                "messages_font_family": "consolas",
                "messages_font_size": 14,
                "messages_font_weight": "bold",
                "messages_line_height": 1.55,
                "stations_font_family": "verdana",
                "stations_font_size": 13,
                "stations_font_weight": "bold",
                "stations_line_height": 1.40,
                "logs_font_family": "tahoma",
                "logs_font_size": 15,
                "logs_font_weight": "bold",
                "logs_line_height": 1.45,
            })
            assert cfg["map_type"] == "satellite"
            assert cfg["track_color"] == "#ff6600"
            assert cfg["track_width"] == 5
            assert cfg["topology_rf_color"] == "#11aa22"
            assert cfg["topology_igate_color"] == "#8844cc"
            assert cfg["topology_width"] == 4
            assert cfg["map_brightness"] == 80
            assert cfg["sound_on_personal_message"] == 0
            assert cfg["message_popup_seconds"] == 9
            assert cfg["open_browser_on_start"] == 1
            assert cfg["app_theme"] == "light"
            assert cfg["messages_font_family"] == "consolas"
            assert cfg["messages_font_size"] == 14
            assert cfg["stations_font_family"] == "verdana"
            assert cfg["stations_font_size"] == 13
            assert cfg["messages_font_weight"] == "bold"
            assert cfg["messages_line_height"] == 1.55
            assert cfg["stations_font_weight"] == "bold"
            assert cfg["stations_line_height"] == 1.40
            assert cfg["logs_font_family"] == "tahoma"
            assert cfg["logs_font_size"] == 15
            assert cfg["logs_font_weight"] == "bold"
            assert cfg["logs_line_height"] == 1.45
    finally:
        db.DB_PATH = original


def test_aprs_passcode():
    assert calculate_aprs_passcode("PT2VHF") == 22950
    assert calculate_aprs_passcode("PT2VHF-9") == 22950
    assert calculate_aprs_passcode("PT2VHF-15") == 22950


def test_version_tuple():
    assert version_tuple("v1.0") == (1, 0)
    assert version_tuple("0.2.10") > version_tuple("0.2.9")
    assert version_tuple("v1.0.0") > version_tuple("0.9.99")


def test_clear_messages_and_stations_are_scoped():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({"callsign": "PT2VHF", "latitude": -15.8, "longitude": -47.9, "altitude": 1000})

            db.add_message("in", "PY2ABC", "PT2VHF", "Teste", msg_id="001", status="Recebida")
            db.upsert_station({
                "from": "PY2ABC-9",
                "format": "uncompressed",
                "latitude": -15.81,
                "longitude": -47.91,
                "speed": 10.0,
                "course": 90,
                "altitude": 1000,
                "symbol_table": "/",
                "symbol": ">",
                "comment": "Movel",
                "path": ["WIDE1-1"],
                "raw": "x",
            })

            assert len(db.list_messages()) == 1
            assert len(db.list_stations()) == 1
            assert len(db.map_data()["tracks"]) >= 1

            deleted_messages = db.clear_messages()
            assert deleted_messages == 1
            assert db.list_messages() == []
            assert len(db.list_stations()) == 1

            db.add_message("in", "PY2ABC", "PT2VHF", "Mantida", msg_id="002", status="Recebida")
            deleted = db.clear_stations()
            assert deleted["stations"] == 1
            assert deleted["tracks"] >= 1
            assert db.list_stations() == []
            assert db.map_data()["tracks"] == []
            assert len(db.list_messages()) == 1
            assert db.get_config()["callsign"] == "PT2VHF"
    finally:
        db.DB_PATH = original


def test_new_install_defaults_and_required_station_fields():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            cfg = db.get_config()
            assert cfg["callsign"] == ""
            assert cfg["latitude"] is None
            assert cfg["longitude"] is None
            assert cfg["altitude"] is None
            assert cfg["altitude_source"] == "manual"
            assert cfg["server"] == "soam.aprs2.net"
            assert cfg["port"] == 14580
            assert cfg["aprs_filter"] == db.BRAZIL_FILTER
            assert cfg["app_theme"] == "dark"
            assert cfg["topology_rf_color"] == "#ffff00"
            assert cfg["topology_igate_color"] == "#ffff00"
            assert cfg["topology_width"] == 1
            assert cfg["message_popup_seconds"] == 5
            assert cfg["sound_on_station_activity"] == 1
            assert cfg["highlight_station_activity"] == 1
            assert cfg["connect_on_start"] == 1
            assert cfg["open_browser_on_start"] == 0
            assert cfg["check_updates_on_start"] == 1
            assert cfg["auto_download_updates"] == 0
            assert cfg["install_updates_on_exit"] == 0
            assert cfg["message_retry_seconds"] == 60
            assert cfg["message_retry_attempts"] == 2
            assert cfg["messages_font_weight"] == "normal"
            assert cfg["stations_font_weight"] == "normal"
            assert cfg["logs_font_family"] == "consolas"
            assert cfg["logs_font_size"] == 12

            # A v1.1 permite salvar preferências e a configuração APRS
            # mesmo enquanto a estação ainda está incompleta. Os campos
            # obrigatórios são validados ao iniciar a conexão APRS-IS.
            partial = db.save_config({
                "callsign": "",
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": 1000,
            })
            with pytest.raises(ValueError, match="Indicativo"):
                db.validate_required_station_config(partial)

            partial = db.save_config({
                "callsign": "PY2ABC",
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": "",
            })
            with pytest.raises(ValueError, match="Altitude"):
                db.validate_required_station_config(partial)

            saved = db.save_config({
                "callsign": "PY2ABC",
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": 0,
                "altitude_source": "fallback_zero",
            })
            db.validate_required_station_config(saved)
            assert saved["callsign"] == "PY2ABC"
            assert saved["altitude"] == 0
            assert saved["altitude_source"] == "fallback_zero"
            assert saved["aprs_filter"] == db.BRAZIL_FILTER

            invalid = db.save_config({
                "callsign": "PY2-ABC",
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": 0,
            })
            with pytest.raises(ValueError, match="Indicativo inválido"):
                db.validate_required_station_config(invalid)
    finally:
        db.DB_PATH = original


def test_invalid_theme_is_rejected():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            with pytest.raises(ValueError, match="Tema da aplicação inválido"):
                db.save_config({
                    "callsign": "PY2ABC",
                    "latitude": -15.8,
                    "longitude": -47.9,
                    "altitude": 1000,
                    "app_theme": "neon",
                })
    finally:
        db.DB_PATH = original


def test_clear_tracklogs_keeps_stations():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF",
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": 1000,
            })
            db.upsert_station({
                "from": "PY2ABC-9",
                "format": "uncompressed",
                "latitude": -15.81,
                "longitude": -47.91,
                "speed": 10.0,
                "course": 90,
                "altitude": 1000,
                "symbol_table": "/",
                "symbol": ">",
                "comment": "Movel",
                "path": ["WIDE1-1"],
                "raw": "x",
            })

            assert len(db.list_stations()) == 1
            assert len(db.map_data()["tracks"]) >= 1

            deleted = db.clear_tracklogs()
            assert deleted >= 1
            assert len(db.list_stations()) == 1
            assert db.map_data()["tracks"] == []
    finally:
        db.DB_PATH = original


def test_long_aprs_message_segmentation():
    short = split_aprs_message_parts("Mensagem curta")
    assert short == ["Mensagem curta"]

    long_text = " ".join(["mensagem"] * 30)
    parts = split_aprs_message_parts(long_text)
    assert len(parts) > 1
    assert all(len(part) <= 63 for part in parts)
    assert all(not part.startswith("[") for part in parts)
    assert " ".join(parts) == long_text
    # Quando uma palavra cabe inteira na próxima parte, ela não deve ser cortada.
    text = ("A " * 30) + "PALAVRAINTEIRA final"
    parts = split_aprs_message_parts(text)
    assert any("PALAVRAINTEIRA" in part for part in parts)
    assert all("PALAVR" not in part or "PALAVRAINTEIRA" in part for part in parts)

    # Uma palavra maior que o limite só é cortada como último recurso.
    giant = "X" * 80
    giant_parts = split_aprs_message_parts(giant)
    assert giant_parts == ["X" * 63, "X" * 17]


def test_observed_topology_from_aprs_path():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF",
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": 1000,
            })
            for call, lat, lon in [
                ("PY2ABC-9", -15.81, -47.91),
                ("PT2DGI", -15.82, -47.92),
                ("PT2IGT", -15.83, -47.93),
            ]:
                db.upsert_station({
                    "from": call,
                    "format": "uncompressed",
                    "latitude": lat,
                    "longitude": lon,
                    "speed": 0,
                    "course": 0,
                    "altitude": 1000,
                    "symbol_table": "/",
                    "symbol": ">",
                    "comment": "Teste",
                    "path": [],
                    "raw": "x",
                })

            db.record_topology_from_raw(
                "PY2ABC-9>APRS,PT2DGI*,WIDE2-1,qAR,PT2IGT:>teste"
            )
            edges = db.list_topology_edges(24)
            keys = {(e["source"], e["target"], e["kind"]) for e in edges}
            assert ("PY2ABC-9", "PT2DGI", "rf") in keys
            assert ("PT2DGI", "PT2IGT", "rf") in keys
            igate_edge = next(
                e for e in edges
                if e["source"] == "PT2DGI" and e["target"] == "PT2IGT"
            )
            assert igate_edge["igate"] == "PT2IGT"
    finally:
        db.DB_PATH = original



def test_v162_replay_update_and_settings_ui():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    assert 'data-tab="analysis"' in html
    assert 'id="tab-analysis"' in html
    assert html.count('id="topologyStatsContent"') == 1
    assert "Página única de configuração" not in html
    assert 'name="auto_download_updates"' not in html
    assert 'name="install_updates_on_exit"' not in html
    assert 'id="unreadMessagesButton"' in html
    assert '<option value="0" selected>Completo</option>' in html
    assert 'id="trafficPlayPauseButton"' in html
    assert 'id="trafficTimeline"' in html
    assert 'id="trafficLiveButton"' in html
    assert 'id="trafficActivityIndicator"' in html
    assert 'id="animateTopologyButton"' not in html
    # O botão Salvar configuração é o único submit legítimo do formulário.
    # O handler de submit evita navegação e centraliza a validação/salvamento.
    assert html.count('type="submit"') == 1
    assert 'id="saveConfigFooterButton" type="submit"' in html
    assert "$('#configForm').addEventListener('submit'" in js
    assert 'id="whatsNewModal"' in html
    assert 'name="sound_on_station_activity" type="checkbox" checked' in html
    assert 'name="highlight_station_activity" type="checkbox" checked' in html
    assert "station-log-button" in js
    assert "Ver logs" in html
    assert "favorite-star" in js
    assert "map-line-legend" in js
    assert "analysisPeriod" in js
    assert "30 * 60 * 1000" in js
    assert "AbortController" in js
    assert "showWhatsNewAfterUpdate" in js
    assert "stationIsVisible" in js
    assert ".map-replay-layout" in css
    assert "@keyframes stationTxRing" in css


def test_frontend_collection_selectors_use_query_selector_all():
    import re
    source = (Path(__file__).resolve().parent.parent / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    bad = re.findall(r"(?<!\$)\$\([^\n;]+?\)\.(?:forEach|map|filter|find|some|every)\(", source)
    assert not bad, f"Use $() (querySelectorAll) before collection methods: {bad}"


def test_reset_config_preserves_operational_data():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({
                "callsign": "PT2VHF", "latitude": -15.8, "longitude": -47.9,
                "altitude": 1000, "app_theme": "light", "aprs_filter": "b/PT2VHF",
            })
            db.add_message("in", "PY2ABC", "PT2VHF", "Teste", msg_id="001", status="Recebida")
            reset = db.reset_config()
            assert reset["callsign"] == ""
            assert reset["app_theme"] == "dark"
            assert reset["aprs_filter"] == db.BRAZIL_FILTER
            assert reset["connect_on_start"] == 1
            assert len(db.list_messages()) == 1
    finally:
        db.DB_PATH = original


def test_message_group_metadata_and_retry_candidates():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            row_id = db.add_message(
                "out", "PT2VHF", "PY2ABC", "[1/2] teste",
                msg_id="123", status="Enviada",
                message_group_id="g1", part_index=1, part_count=2, retry_count=0,
            )
            row = db.get_message(row_id)
            assert row["message_group_id"] == "g1"
            assert row["part_index"] == 1
            assert row["part_count"] == 2
            assert row["retry_count"] == 0
            candidates = db.list_retry_candidates(15, 2, limit=10)
            # Registro acabou de ser criado, portanto ainda não venceu o timeout.
            assert candidates == []
    finally:
        db.DB_PATH = original



def test_client_version_stats_by_latest_station_tocall():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            packets = [
                ("PY2AAA-9", "APDW17"),
                ("PY2BBB-9", "APDW17"),
                ("PY2CCC-9", "APDR16"),
                ("PY2DDD-9", "APRS"),
            ]
            for idx, (call, tocall) in enumerate(packets):
                db.upsert_station({
                    "from": call,
                    "format": "status",
                    "latitude": -15.80 - idx * 0.01,
                    "longitude": -47.90 - idx * 0.01,
                    "speed": 0,
                    "course": 0,
                    "altitude": 1000,
                    "symbol_table": "/",
                    "symbol": ">",
                    "comment": "Teste",
                    "path": [],
                    "raw": f"{call}>{tocall},TCPIP*:>teste",
                })

            stats = db.client_version_stats(0)
            assert stats["total_stations"] == 4
            assert stats["identified_stations"] == 3
            assert stats["unidentified_stations"] == 1
            assert stats["items"][0]["identifier"] == "APDW17"
            assert stats["items"][0]["friendly_name"] == "Dire Wolf"
            assert stats["items"][0]["aliases"] == ["Dire Wolf 1.7"]
            assert stats["items"][0]["rank"] == 1
            assert stats["items"][0]["stations"] == 2
            assert stats["items"][1]["identifier"] == "APDR16"
            assert stats["items"][1]["friendly_name"] == "APRSdroid"
            assert stats["items"][1]["rank"] == 2
            assert stats["items"][1]["stations"] == 1
            assert stats["own_client"]["identifier"] == "APZVHF"
    finally:
        db.DB_PATH = original


def test_aprs_device_friendly_names_and_own_client_identifier():
    direwolf = db.resolve_aprs_device_id("APDW18")
    assert direwolf["friendly_name"] == "Dire Wolf 1.8"
    assert direwolf["model"] == "DireWolf"

    aprsdroid = db.resolve_aprs_device_id("APDR16")
    assert aprsdroid["friendly_name"] == "APRSdroid"

    own = db.resolve_aprs_device_id("APZVHF")
    assert own["friendly_name"] == "PT2VHF APRS Client"
    assert own["local_override"] is True


def test_qarray_direct_igate_reception_is_rf_link():
    source, edges = db._observed_topology_edges("PY2ABC-9>APRS,PT2DGI*,WIDE2-1,qAR,PT2IGT:>teste")
    assert source == "PY2ABC-9"
    assert ("PY2ABC-9", "PT2DGI", "rf", None) in edges
    assert ("PT2DGI", "PT2IGT", "rf", "PT2IGT") in edges
    assert not any(kind == "igate" for _a, _b, kind, _igate in edges)

def test_v177_remote_igate_qconstruct_is_not_rf_link():
    source, edges = db._observed_topology_edges(
        "PY2ABC-9>APRS,PT2DGI*,WIDE2-1,qAr,PT2IGT:>teste"
    )
    assert source == "PY2ABC-9"
    assert ("PY2ABC-9", "PT2DGI", "rf", None) in edges
    assert ("PT2DGI", "PT2IGT", "igate", "PT2IGT") in edges
    assert ("PT2DGI", "PT2IGT", "rf", "PT2IGT") not in edges

    source, edges = db._observed_topology_edges(
        "PY2NET>APRS,TCPIP*,qAC,APRSBR:>internet"
    )
    assert source == "PY2NET"
    assert not any(kind == "rf" for _a, _b, kind, _igate in edges)


def test_v177_rf_igate_parser_preserves_qconstruct_case():
    assert db._rf_igate_from_path(["WIDE1-1*", "qAR", "PT2IGT"]) == "PT2IGT"
    assert db._rf_igate_from_path(["WIDE1-1*", "qAr", "PT2IGT"]) == ""
    assert db._rf_igate_from_path(["TCPIP*", "qAO", "PT2IGT"]) == ""


def test_topology_timeline_and_period_comparison():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            for call, lat, lon in [
                ("PY2ABC-9", -15.81, -47.91),
                ("PT2DGI", -15.82, -47.92),
            ]:
                db.upsert_station({
                    "from": call, "format": "uncompressed", "latitude": lat, "longitude": lon,
                    "speed": 0, "course": 0, "altitude": 1000,
                    "symbol_table": "/", "symbol": ">", "comment": "Teste", "path": [], "raw": "x",
                })
            db.record_topology_from_raw("PY2ABC-9>APRS,PT2DGI*:>teste")
            timeline = db.topology_timeline(24)
            assert timeline
            assert timeline[0]["source"] == "PY2ABC-9"
            comparison = db.topology_period_comparison(24)
            assert comparison["current_events"] >= 1
    finally:
        db.DB_PATH = original


def test_complete_topology_favorites_and_packet_traffic():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            for call, lat, lon in [
                ("PY2ABC-9", -15.81, -47.91),
                ("PT2DGI", -15.82, -47.92),
                ("PT2IGT", -15.83, -47.93),
            ]:
                db.upsert_station({
                    "from": call, "format": "uncompressed", "latitude": lat, "longitude": lon,
                    "speed": 0, "course": 0, "altitude": 1000,
                    "symbol_table": "/", "symbol": ">", "comment": "Teste", "path": [], "raw": "x",
                })

            raw = "PY2ABC-9>APRS,PT2DGI*,WIDE2-1,qAR,PT2IGT:>teste"
            db.record_packet(raw, "PY2ABC-9", "status")
            db.record_topology_from_raw(raw)

            complete = db.list_topology_edges(0)
            assert {("PY2ABC-9", "PT2DGI", "rf"), ("PT2DGI", "PT2IGT", "rf")} <= {
                (e["source"], e["target"], e["kind"]) for e in complete
            }
            igate_edge = next(e for e in complete if e["source"] == "PT2DGI" and e["target"] == "PT2IGT")
            assert igate_edge["igate"] == "PT2IGT"
            stats = db.topology_stats(0)
            assert stats["complete"] is True
            assert stats["edges"] >= 2
            assert db.topology_timeline(0)
            assert db.topology_period_comparison(0)["complete"] is True

            traffic = db.packet_traffic_events(hours=0, limit=20)
            assert traffic["events"]
            event = traffic["events"][-1]
            assert event["source"] == "PY2ABC-9"
            assert len(event["segments"]) >= 2

            overview = db.packet_traffic_overview(hours=0, bins=40)
            assert overview["total"] >= 1
            assert overview["first_timestamp"]
            assert overview["last_timestamp"]
            assert len(overview["bins"]) == 40
            bounded = db.packet_traffic_events(
                start=overview["first_timestamp"],
                end=overview["last_timestamp"],
                limit=20,
            )
            assert bounded["events"]

            assert db.set_favorite("PY2ABC-9", True) is True
            assert "PY2ABC-9" in db.list_favorites()
            station = next(s for s in db.list_stations() if s["callsign"] == "PY2ABC-9")
            assert station["favorite"] == 1
            db.clear_stations()
            assert "PY2ABC-9" in db.list_favorites()
            assert db.set_favorite("PY2ABC-9", False) is False
            assert "PY2ABC-9" not in db.list_favorites()
    finally:
        db.DB_PATH = original


def test_incoming_message_read_state():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            row_id = db.add_message(
                "in", "PY2ABC", "PT2VHF", "Mensagem nova",
                msg_id="321", status="Recebida", message_type="message",
            )
            row = db.get_message(row_id)
            assert row["read_at"] is None
            assert db.mark_message_read(row_id) == 1
            assert db.get_message(row_id)["read_at"]

            second = db.add_message(
                "in", "PY2ABC", "PT2VHF", "Outra",
                msg_id="322", status="Recebida", message_type="message",
            )
            assert db.get_message(second)["read_at"] is None
            assert db.mark_conversation_read("PY2ABC", "PT2VHF") >= 1
            assert db.get_message(second)["read_at"]
    finally:
        db.DB_PATH = original


def test_auto_update_flow_is_enabled_and_platform_launchers_register_exit():
    root = Path(__file__).resolve().parent.parent
    web_source = (root / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")
    js_source = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    windows_source = (root / "windows_app.py").read_text(encoding="utf-8")
    linux_source = (root / "linux_app.py").read_text(encoding="utf-8")
    macos_source = (root / "macos_app.py").read_text(encoding="utf-8")
    updater_source = (root / "pt2vhf_aprs" / "updater.py").read_text(encoding="utf-8")
    assert '@app.post("/api/update/install")' in web_source
    assert "download_and_install" in web_source
    assert "installLatestUpdate" in js_source
    assert "register_exit_handler(_exit_for_update)" in windows_source
    assert "register_exit_handler(_exit_for_update)" in linux_source
    assert "register_exit_handler(_exit_for_update)" in macos_source
    assert "UPDATE_LOCK_FILE" in updater_source
    assert "Stop-Process -Id $pidToWait -Force" in updater_source
    assert "kill -KILL" in updater_source
    assert "GITHUB_LATEST_RELEASE_API" in web_source


def test_update_check_cache_is_five_minutes():
    root = Path(__file__).resolve().parent.parent
    web_source = (root / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")
    js_source = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    # O cache HTTP interno continua curto para verificações manuais/forçadas,
    # enquanto o polling automático da interface ocorre a cada 30 minutos.
    assert "UPDATE_CACHE_SECONDS = 5 * 60" in web_source
    assert "30 * 60 * 1000" in js_source


def test_updater_asset_name_contains_version():
    name = updater.desired_asset_name("1.6")
    assert "1.6" in name
    assert name


def test_updater_select_asset_matches_exact_platform_asset(monkeypatch):
    wanted = "PT2VHF_TEST_v1.6.22.bin"
    monkeypatch.setattr(updater, "desired_asset_name", lambda version: wanted)
    release = {
        "assets": [
            {"name": "other.bin", "browser_download_url": "https://github.com/x/other", "size": 1},
            {
                "name": wanted,
                "browser_download_url": "https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.6.22/test.bin",
                "size": 123,
                "digest": "sha256:abc",
            },
        ]
    }
    asset = updater.select_asset(release, "1.6.22")
    assert asset == {
        "name": wanted,
        "url": "https://github.com/alexpmr/PT2VHF-APRS-Client/releases/download/v1.6.22/test.bin",
        "size": 123,
        "digest": "sha256:abc",
    }

def test_topology_stats_active_stations_excludes_telemetry_igates_and_digipeaters():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()

            for _ in range(3):
                db.record_packet("PY2AAA-9>APRS:>teste", "PY2AAA-9", "status")
            for _ in range(2):
                db.record_packet("PY2BBB-9>APRS:!1234.56S/04712.34W>teste", "PY2BBB-9", "position")
            for _ in range(10):
                db.record_packet("PY2TEL>APRS:T#001,001,002,003,004,005,00000000", "PY2TEL", "telemetry")

            db.record_topology_from_raw("PY2SRC>APRS,PT2DGI*,WIDE2-1,qAR,PT2IGT:>teste")
            for _ in range(8):
                db.record_packet("PT2DGI>APRS:>digi", "PT2DGI", "status")
            for _ in range(7):
                db.record_packet("PT2IGT>APRS:>igate", "PT2IGT", "status")

            stats = db.topology_stats(0)
            active = stats["active_stations"]
            assert [(row["callsign"], row["packets"]) for row in active] == [
                ("PY2AAA-9", 3),
                ("PY2BBB-9", 2),
            ]
            assert active[0]["rank"] == 1
            assert active[0]["percent"] == 60.0
            assert active[1]["percent"] == 40.0
            assert stats["active_station_packets"] == 5
    finally:
        db.DB_PATH = original

def test_v1624_official_logo_is_single_branding_source():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    workflow = (root / ".github" / "workflows" / "build-windows.yml").read_text(encoding="utf-8")
    win_icon = (root / "windows" / "make_icon.py").read_text(encoding="utf-8")
    mac_icon = (root / "macos" / "make_icon.py").read_text(encoding="utf-8")
    linux_build = (root / "linux" / "build_linux.sh").read_text(encoding="utf-8")
    manual = (root / "tools" / "generate_manual.py").read_text(encoding="utf-8")

    assert 'type="image/png"' in html
    assert html.count("img/app_logo.png") >= 2
    assert "app_logo.svg" not in html
    assert "app_logo.png" in win_icon
    assert "app_logo.png" in mac_icon
    assert "ImageDraw" not in mac_icon
    assert "app_logo.png" in linux_build
    assert "app_logo.png" in manual
    assert "cp pt2vhf_aprs/static/img/app_logo.png dist-docs/manual_logo.png" in workflow
    assert "app_logo.svg" not in workflow


def test_v1624_version_notes_include_1623_and_1624():
    root = Path(__file__).resolve().parent.parent
    source = (root / "pt2vhf_aprs" / "version_notes.py").read_text(encoding="utf-8")
    assert '"1.6.24"' in source
    assert '"1.6.23"' in source
    assert source.index('"1.6.24"') < source.index('"1.6.23"')

def test_map_controls_are_above_map_not_overlaid():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    context_pos = html.index('id="mapContextBar"')
    history_pos = html.index('id="mapHistoryToggle"')
    main_pos = html.index("<main>")
    map_pos = html.index('id="map"')
    assert context_pos < history_pos < main_pos < map_pos

    for control in ("mapPeriodHours", "mapItemsButton", "topologySpeed", "mapTypeQuick", "kmlExportButton"):
        assert context_pos < html.index(f'id="{control}"') < main_pos

    for removed in ("stationsHours", "tracklogHours", "topologyHours", "topologyToggle"):
        assert f'id="{removed}"' not in html

    assert ".map-context-controls" in css
    assert ".map-items-menu" in css
    assert "function addMapControls()" in js

def test_v17_language_options_and_runtime():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    i18n = (root / "pt2vhf_aprs" / "static" / "js" / "i18n_extra.js").read_text(encoding="utf-8")
    database = (root / "pt2vhf_aprs" / "database.py").read_text(encoding="utf-8")

    assert 'data-language="es"' in html
    assert 'data-language="fr"' in html
    assert '<option value="es">Español</option>' in html
    assert '<option value="fr">Français</option>' in html
    assert "js/i18n_extra.js" in html
    assert "normalizeLanguage" in js
    assert "es:'es-ES'" in js
    assert "fr:'fr-FR'" in js
    assert "window.PT2VHF_I18N" in i18n
    assert "es:" in i18n and "fr:" in i18n
    assert '{"pt-BR", "en", "es", "fr"}' in database


def test_v17_message_conversation_tracks_recipient():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert "$('#messageTo')?.addEventListener('input'" in js
    assert "state.selectedConversation = destinationConversation ? composerDestination : '';" in js
    assert "Novo destinatário:" in js
    assert "There is no recorded conversation with this callsign yet." in js
    assert "$('#messageTo').value = state.selectedConversation;" in js


def test_v17_traffic_animation_defaults_enabled():
    root = Path(__file__).resolve().parent.parent
    database = (root / "pt2vhf_aprs" / "database.py").read_text(encoding="utf-8")
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert '"traffic_animation_enabled": 1' in database
    assert 'name="traffic_animation_enabled" type="checkbox" checked' in html
    assert "state.trafficPlaying = state.trafficAnimationEnabled;" in js
    assert "traffic_animation_enabled" in js


def test_v17_statistics_friendly_names_and_font_control():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    database = (root / "pt2vhf_aprs" / "database.py").read_text(encoding="utf-8")

    assert 'name="statistics_font_size"' in html
    assert 'id="statisticsFontSizeValue"' in html
    assert "--statistics-font-size" in css
    assert "statistics_font_size" in database
    assert "statistics_font_size" in js
    assert '<span class="client-version-tocall">' not in js


def test_v17_message_filter_buttons_are_compact():
    root = Path(__file__).resolve().parent.parent
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")

    assert "#groupMessagesButton," in css
    assert "#myMessagesButton," in css
    assert "#unreadMessagesButton" in css
    assert "min-height: 32px;" in css
    assert "white-space: nowrap;" in css

def test_v171_aprs_announcement_packet():
    packet, addressee, message_type, text = build_bulletin_packet(
        source="PT2VHF-15",
        text="PT2VHF APRS Client v1.7.1 - Download: tiny.cc/aprs",
        bulletin_id="A",
    )
    assert packet == "PT2VHF-15>APZVHF,TCPIP*::BLNA     :PT2VHF APRS Client v1.7.1 - Download: tiny.cc/aprs"
    assert addressee == "BLNA"
    assert message_type == "announcement"
    assert classify_message_type("BLNA") == "announcement"
    assert len(text) <= 67


def test_v171_rejects_implausible_position_jump_until_relocation_is_confirmed():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            base = {
                "from": "PY2OUT-9", "format": "uncompressed",
                "speed": 0.0, "course": 0, "altitude": 1000,
                "symbol_table": "/", "symbol": ">", "comment": "Teste", "path": [], "raw": "x",
            }
            db.upsert_station({**base, "latitude": -15.80, "longitude": -47.90})
            db.upsert_station({**base, "latitude": 51.5074, "longitude": -0.1278})
            db.upsert_station({**base, "latitude": 51.5075, "longitude": -0.1277})

            station = next(row for row in db.list_stations() if row["callsign"] == "PY2OUT-9")
            assert abs(float(station["latitude"]) - (-15.80)) < 0.001
            assert len([x for x in db.map_data()["tracks"] if x["callsign"] == "PY2OUT-9"]) == 1

            # A terceira posição consecutiva coerente na nova região confirma uma relocação.
            db.upsert_station({**base, "latitude": 51.5076, "longitude": -0.1276})
            station = next(row for row in db.list_stations() if row["callsign"] == "PY2OUT-9")
            assert abs(float(station["latitude"]) - 51.5076) < 0.001
            assert len([x for x in db.map_data()["tracks"] if x["callsign"] == "PY2OUT-9"]) == 2
    finally:
        db.DB_PATH = original


def test_v171_updater_requires_helper_readiness_before_exit():
    root = Path(__file__).resolve().parent.parent
    updater_source = (root / "pt2vhf_aprs" / "updater.py").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert "HELPER_READY_FILE" in updater_source
    assert "def _wait_for_helper_ready" in updater_source
    assert "update_helper_start_failed" in updater_source
    assert "A aplicação permanecerá aberta" in updater_source
    assert updater_source.index("launch_pending_update(force=True)") < updater_source.index("_request_exit_after(delay=2.5)")
    assert "if (state.updateDownloading)" in js
    assert "showUpdateModal();" in js
    assert "updateProgressBar" in js


def test_v171_map_controls_are_independent_and_activity_is_removed():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert 'id="mapStationAgeFilter"' not in html
    assert 'id="mapPeriodHours"' in html
    assert 'id="mapItemsButton"' in html
    assert "pt2vhf_map_period_hours" in js
    assert "pt2vhf_map_item_stations" in js
    assert "pt2vhf_map_item_tracklogs" in js
    assert "splitTrackSegments" in js
    assert "distance >= 250" in js

def test_v171_about_tab_and_manual_aprs_promotion():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    web = (root / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")

    assert 'data-tab="about"' in html
    assert 'id="tab-about"' in html
    assert "tiny.cc/aprs" in html
    assert "+55 61 98402-3634" in html
    assert "alexpmr@gmail.com" in html
    assert "aboutPromoteButton" in html
    assert "type:'announcement'" in js
    assert "window.confirm(copy.confirm)" in js
    assert "promotionPacketPreview" in js
    assert '"announcement"' in web


def test_v171_alerts_and_quick_message_links():
    root = Path(__file__).resolve().parent.parent
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert ".tab.has-unread:not(.active)" in css
    assert "messageTabPulse" in css
    assert "messagesTab?.classList.toggle('has-unread'" in js
    assert ".version-status.update" in css
    assert "updateAvailablePulse" in css
    assert "data-quick-message-callsign" in js
    assert "openMessageComposer(link.dataset.quickMessageCallsign" in js


def test_v171_history_is_contextual_to_map():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert 'id="mapContextBar"' in html
    assert 'id="mapHistoryToggle"' in html
    assert "state.activeTab === 'map'" in js
    assert "pt2vhf_map_history_open" in js


def test_v171_i18n_expands_recent_ui_in_all_languages():
    root = Path(__file__).resolve().parent.parent
    app = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    extra = (root / "pt2vhf_aprs" / "static" / "js" / "i18n_extra.js").read_text(encoding="utf-8")

    for text in ("Sobre", "Anúncio geral", "Período das estações", "Período do tracklog", "Replay da Rede"):
        assert text in app or text in extra
    assert '"Sobre": "Acerca de"' in extra
    assert '"Sobre": "À propos"' in extra
    assert "EN_TEXT.get(trimmed)" in app
    assert "renderAbout();" in app

def test_v172_client_versions_consolidate_same_friendly_application(monkeypatch):
    original_db = db.DB_PATH
    original_resolver = db.resolve_aprs_device_id
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            now = db.utc_now_iso()
            with db.connection() as conn:
                conn.executemany(
                    "INSERT INTO stations(callsign,last_heard,raw) VALUES(?,?,?)",
                    [
                        ("PY1AAA", now, "PY1AAA>APAAA:>test"),
                        ("PY1BBB", now, "PY1BBB>APBBB:>test"),
                        ("PT2ONE", now, "PT2ONE>APZVHF:>test"),
                        ("PT2TWO", now, "PT2TWO>APALT:>test"),
                    ],
                )

            def fake_resolver(tocall):
                if tocall in {"APAAA", "APBBB"}:
                    return {
                        "identifier": tocall,
                        "friendly_name": "ircDDB Gateway",
                        "identified": True,
                        "vendor": "ircDDB",
                        "model": "ircDDB Gateway",
                        "class": "software",
                        "os": "",
                    }
                if tocall in {"APZVHF", "APALT"}:
                    return {
                        "identifier": tocall,
                        "friendly_name": "PT2VHF APRS Client",
                        "identified": True,
                        "vendor": "PT2VHF",
                        "model": "PT2VHF APRS Client",
                        "class": "software",
                        "os": "",
                    }
                return original_resolver(tocall)

            monkeypatch.setattr(db, "resolve_aprs_device_id", fake_resolver)
            stats = db.client_version_stats()

            assert len(stats["items"]) == 2
            ircddb = next(item for item in stats["items"] if item["friendly_name"] == "ircDDB Gateway")
            assert ircddb["stations"] == 2
            assert set(ircddb["identifiers"]) == {"APAAA", "APBBB"}

            own = stats["own_client"]
            assert own["friendly_name"] == "PT2VHF APRS Client"
            assert own["stations"] == 2
            assert own["is_own_client"] is True
            assert set(own["identifiers"]) == {"APALT", "APZVHF"}
            assert own["identifier"] == "APZVHF"
    finally:
        db.DB_PATH = original_db


def test_v172_map_controls_share_history_context_row():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")

    context_start = html.index('id="mapContextBar"')
    main_start = html.index("<main>")
    context_html = html[context_start:main_start]
    assert 'id="mapHistoryToggle"' in context_html
    for control in ("mapPeriodHours", "mapItemsButton", "topologySpeed", "mapTypeQuick"):
        assert f'id="{control}"' in context_html
    assert 'class="map-top-toolbar"' not in html
    assert "height: 41px;" in css[css.index(".map-context-bar"):css.index(".map-context-bar.hidden")]
    assert "overflow-x: auto;" in css

def test_v172_station_popup_relative_last_heard_updates_live():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert "function formatRelativeLastHeard(value)" in js
    assert 'class="station-last-heard-relative"' in js
    assert "function refreshStationPopupRelativeTimes()" in js
    assert "schedulePolling(refreshStationPopupRelativeTimes, 30000);" in js
    assert "há ${hours} h e ${minutes} min" in js
    assert "há ${days} dia${days === 1 ? '' : 's'}" in js

def test_v173_updater_helpers_use_real_newlines(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        updates = root / "updates"
        updates.mkdir()
        monkeypatch.setattr(updater, "UPDATE_DIR", updates)
        monkeypatch.setattr(updater, "PENDING_FILE", updates / "pending_update.json")
        monkeypatch.setattr(updater, "APPLY_LOG", updates / "update_apply.log")
        monkeypatch.setattr(updater, "UPDATE_LOCK_FILE", updates / "update.lock")
        monkeypatch.setattr(updater, "HELPER_READY_FILE", updates / "helper_ready")

        pending_windows = {
            "path": str(updates / "PT2VHF_APRS_Client_Portable_x64_v1.7.3.exe"),
            "current_executable": str(root / "PT2VHF_APRS_Client_Portable_x64_v1.7.2.exe"),
            "mode": "windows-portable",
            "pid": 12345,
            "version": "1.7.3",
        }
        ps1 = updater._write_windows_helper(pending_windows)
        powershell = ps1.read_text(encoding="utf-8")
        assert "$ErrorActionPreference='Stop'\n$pidToWait=12345\n" in powershell
        assert "\\n$pidToWait" not in powershell
        assert "\nLog 'updater helper started'\n" in powershell

        pending_linux = {
            "path": str(updates / "PT2VHF_APRS_Client_x86_64_v1.7.3.AppImage"),
            "current_executable": str(root / "PT2VHF_APRS_Client_x86_64_v1.7.2.AppImage"),
            "mode": "linux-appimage",
            "pid": 12345,
            "version": "1.7.3",
        }
        sh = updater._write_posix_helper(pending_linux)
        shell = sh.read_text(encoding="utf-8")
        assert shell.startswith("#!/usr/bin/env bash\nset -e\n")
        assert "\\nset -e" not in shell
        assert "printf '%s %s\\n'" in shell


def test_v173_client_versions_group_semantic_versions_into_one_family():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            now = db.utc_now_iso()
            with db.connection() as conn:
                conn.executemany(
                    "INSERT INTO stations(callsign,last_heard,raw) VALUES(?,?,?)",
                    [
                        ("PY1DW17", now, "PY1DW17>APDW17:>test"),
                        ("PY1DW18", now, "PY1DW18>APDW18:>test"),
                        ("PY1DW19", now, "PY1DW19>APDW19:>test"),
                    ],
                )

            stats = db.client_version_stats()
            dire_wolf = [item for item in stats["items"] if item["friendly_name"] == "Dire Wolf"]
            assert len(dire_wolf) == 1
            assert dire_wolf[0]["stations"] == 3
            assert set(dire_wolf[0]["identifiers"]) == {"APDW17", "APDW18", "APDW19"}
            assert set(dire_wolf[0]["aliases"]) == {"Dire Wolf 1.7", "Dire Wolf 1.8", "Dire Wolf 1.9"}
    finally:
        db.DB_PATH = original


def test_v173_download_install_button_has_immediate_feedback_and_direct_action():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    web = (root / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")
    updater_source = (root / "pt2vhf_aprs" / "updater.py").read_text(encoding="utf-8")

    assert "Feedback visual antes mesmo da chamada HTTP" in js
    assert "Preparando atualização…" in js
    assert "$('#openLatestReleaseButton')?.addEventListener('click', () => void installLatestUpdate());" in js
    assert "update_install_http_requested" in web
    assert "update_install_requested" in updater_source

def test_v174_updater_errors_are_visible_above_modal():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert 'id="updateDownloadProgress" class="update-download-progress hidden"' in html
    assert 'role="status" aria-live="assertive"' in html
    assert ".message-alert-overlay {" in css
    assert "z-index: 4000;" in css
    assert ".toast { position: fixed; z-index: 5200;" in css
    assert ".update-download-progress.error" in css
    assert "function setUpdateProgress(message = '', type = '')" in js
    assert "setUpdateProgress(message, 'error');" in js
    assert "Não foi possível concluir a atualização automática." in js
    assert "toast(detail, 'error');" in js


def test_v174_updater_modal_keeps_actionable_controls_after_failure():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    catch_start = js.index("PT2VHF updater: falha ao baixar/instalar")
    catch_block = js[catch_start:catch_start + 2600]
    assert "state.updateDownloading = false;" in catch_block
    assert "installButton.disabled = false;" in catch_block
    assert "closeButton.disabled = false;" in catch_block
    assert "releaseButton.disabled = false;" in catch_block
    assert "setUpdateProgress(message, 'error');" in catch_block

def test_v175_rejects_zero_and_rf_implausible_positions():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()

            db.upsert_station({
                "from": "PT2PAG-15",
                "format": "uncompressed",
                "latitude": -15.80,
                "longitude": -47.90,
                "path": ["WIDE1-1"],
                "raw": "PT2PAG-15>APRS:!1548.00S/04754.00W>",
            })
            db.upsert_station({
                "from": "PU2ZERO-9",
                "format": "uncompressed",
                "latitude": 0.0,
                "longitude": 0.0,
                "path": ["qAR", "PT2PAG-15"],
                "raw": "PU2ZERO-9>APRS,qAR,PT2PAG-15:!0000.00N/00000.00E>",
            })
            db.upsert_station({
                "from": "PU2AMA-7",
                "format": "mic-e",
                "latitude": 24.0,
                "longitude": 121.0,
                "path": ["PT2ON-15", "WIDE1*", "WIDE2-2", "qAR", "PT2PAG-15"],
                "raw": "PU2AMA-7>APRS,PT2ON-15,WIDE1*,WIDE2-2,qAR,PT2PAG-15:test",
            })

            mapped = {row["callsign"] for row in db.map_data()["stations"]}
            assert "PT2PAG-15" in mapped
            assert "PU2ZERO-9" not in mapped
            assert "PU2AMA-7" not in mapped

            stations = {row["callsign"]: row for row in db.list_stations()}
            assert stations["PU2ZERO-9"]["position_valid"] is False
            assert stations["PU2AMA-7"]["position_valid"] is False

            problems = db.station_problem_stats()
            problem_types = {(row["callsign"], row["issue_type"]) for row in problems}
            assert ("PU2ZERO-9", "zero_position") in problem_types
            assert ("PU2AMA-7", "rf_relay_distance") in problem_types
    finally:
        db.DB_PATH = original


def test_v175_kml_export_contains_selected_layers():
    payload = {
        "stations": [{
            "callsign": "PT2VHF-15",
            "latitude": -15.8,
            "longitude": -47.9,
            "altitude": 1000,
            "last_heard": "2026-09-28T12:00:00+00:00",
            "info": "test",
            "path": "[]",
        }],
        "tracks": [
            {"callsign": "PT2VHF-15", "timestamp": "2026-09-28T12:00:00+00:00", "latitude": -15.8, "longitude": -47.9, "altitude": 1000},
            {"callsign": "PT2VHF-15", "timestamp": "2026-09-28T12:01:00+00:00", "latitude": -15.81, "longitude": -47.91, "altitude": 1002},
        ],
        "topology": [{
            "source": "PT2VHF-15", "target": "PT2PAG-15", "kind": "rf",
            "packet_count": 2, "last_seen": "2026-09-28T12:01:00+00:00",
            "source_lat": -15.8, "source_lon": -47.9,
            "target_lat": -15.7, "target_lon": -47.8,
        }],
    }
    text = _kml_document(payload).decode("utf-8")
    assert "<name>Stations</name>" in text
    assert "<name>Positions</name>" in text
    assert "<name>Tracklogs</name>" in text
    assert "<name>Topology</name>" in text
    assert "PT2VHF-15" in text
    assert "-47.9000000,-15.8000000,1000.0" in text


def test_v175_ui_has_kml_export_message_sorting_and_stats_navigation():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    web = (root / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")

    assert 'id="kmlExportButton"' in html
    for checkbox in ("kmlStations", "kmlPositions", "kmlTracklogs", "kmlTopology"):
        assert f'id="{checkbox}" type="checkbox" checked' in html
    assert 'id="conversationSortKey"' in html
    assert '<option value="sender">Remetente</option>' in html
    assert '<option value="date">Data</option>' in html
    assert 'id="clearMessagesButton" type="button" class="btn danger"' in html
    assert "conversationSortKey" in js
    assert "data-map-callsign" in js
    assert "problem_stations" in js
    assert "improvement_suggestions" in js
    assert '@app.get("/api/export/kml")' in web


def test_v175_invalid_geometry_is_excluded_from_export_and_replay():
    root = Path(__file__).resolve().parent.parent
    database_source = (root / "pt2vhf_aprs" / "database.py").read_text(encoding="utf-8")

    assert "def _valid_geo_position" in database_source
    assert "POSITION_ZERO_EPSILON" in database_source
    assert "rf_relay_distance" in database_source
    assert "station_anomalies" in database_source
    assert "def geographic_export_data" in database_source

def test_v176_manual_conversation_ranking_excludes_automatic_traffic():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({"callsign": "PT2VHF", "ssid": 15})

            db.add_message("in", "PU2AAA", "PT2VHF-15", "Olá Alex", msg_id="101")
            db.add_message("in", "PU2AAA", "PY2BBB", "Bom dia", msg_id="102")
            db.add_message("out", "PT2VHF-15", "PU2AAA", "Resposta parte 1", msg_id="201",
                           message_group_id="grp-1", part_index=1, part_count=2)
            db.add_message("out", "PT2VHF-15", "PU2AAA", "Resposta parte 2", msg_id="202",
                           message_group_id="grp-1", part_index=2, part_count=2)

            # Tráfego que não pode influenciar o ranking de conversa humana.
            db.add_message("in", "PU2AUTO", "PT2VHF-15", "?PING?", msg_id=None)
            db.add_message("in", "PU2AUTO", "PT2VHF-15", "ack123", msg_id=None)
            db.add_message("in", "PU2AUTO", "BLN1", "Boletim", message_type="bulletin")
            db.add_message("out", "PT2VHF-15", "PU2AAA", "retry", msg_id="203", retry_count=1)

            rows = {row["callsign"]: row for row in db.manual_conversation_stats()}
            assert "PT2VHF-15" not in rows
            assert "PU2AUTO" not in rows
            assert rows["PU2AAA"]["interactions"] == 3
            assert rows["PU2AAA"]["sent"] == 2
            assert rows["PU2AAA"]["received"] == 1
            assert rows["PU2AAA"]["peers"] == 2
            assert rows["PY2BBB"]["interactions"] == 1
    finally:
        db.DB_PATH = original


def test_v176_kml_save_as_and_map_toolbar_controls():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    windows = (root / "windows_app.py").read_text(encoding="utf-8")
    linux = (root / "linux_app.py").read_text(encoding="utf-8")
    macos = (root / "macos_app.py").read_text(encoding="utf-8")

    map_bar_start = html.index('id="mapContextBar"')
    map_bar_end = html.index("<main>", map_bar_start)
    map_bar = html[map_bar_start:map_bar_end]
    header = html[:map_bar_start]

    assert 'id="kmlExportButton"' in map_bar
    assert 'id="kmlExportButton"' not in header
    assert 'id="mapHistoryToggle"' in map_bar
    assert map_bar.index('id="mapHistoryToggle"') < map_bar.index('id="kmlExportButton"')
    assert "async function saveKmlContent" in js
    assert "showSaveFilePicker" in js
    assert "save_text_file" in js
    assert "Exportação cancelada." in js

    for source in (windows, linux, macos):
        assert "def save_text_file" in source
        assert "SAVE_DIALOG" in source
        assert 'file_types=("KML (*.kml)", "Todos os arquivos (*.*)")' in source


def test_v176_windows_updater_uses_native_cmd_helper(monkeypatch, tmp_path):
    original_values = {
        "UPDATE_DIR": updater.UPDATE_DIR,
        "PENDING_FILE": updater.PENDING_FILE,
        "APPLY_LOG": updater.APPLY_LOG,
        "UPDATE_LOCK_FILE": updater.UPDATE_LOCK_FILE,
        "HELPER_READY_FILE": updater.HELPER_READY_FILE,
    }
    try:
        monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
        monkeypatch.setattr(updater, "PENDING_FILE", tmp_path / "pending_update.json")
        monkeypatch.setattr(updater, "APPLY_LOG", tmp_path / "update_apply.log")
        monkeypatch.setattr(updater, "UPDATE_LOCK_FILE", tmp_path / "update.lock")
        monkeypatch.setattr(updater, "HELPER_READY_FILE", tmp_path / "helper_ready")

        downloaded = tmp_path / "PT2VHF_APRS_Client_Portable_x64_v1.7.6.exe"
        downloaded.write_bytes(b"test")
        current = tmp_path / "PT2VHF_APRS_Client_Portable_x64_v1.7.5.exe"
        current.write_bytes(b"old")

        helper = updater._write_windows_cmd_helper({
            "path": str(downloaded),
            "current_executable": str(current),
            "mode": "windows-portable",
            "version": "1.7.6",
            "pid": 1234,
        })
        text_value = helper.read_text(encoding="utf-8")
        assert helper.suffix == ".cmd"
        assert '> "%ready%" echo ready' in text_value
        assert 'portable update installed' in text_value
        assert 'move /Y "%downloaded%" "%destination%"' in text_value
        assert "powershell" not in text_value.lower()

        ps = updater._write_windows_helper({
            "path": str(downloaded),
            "current_executable": str(current),
            "mode": "windows-portable",
            "version": "1.7.6",
            "pid": 1234,
        })
        assert ps.read_bytes().startswith(b"\xef\xbb\xbf")
    finally:
        for name, value in original_values.items():
            setattr(updater, name, value)


def test_v176_windows_updater_launch_prefers_comspec_cmd():
    root = Path(__file__).resolve().parent.parent
    source = (root / "pt2vhf_aprs" / "updater.py").read_text(encoding="utf-8")
    assert "_write_windows_cmd_helper(pending)" in source
    assert 'os.environ.get("COMSPEC", r"C:\\Windows\\System32\\cmd.exe")' in source
    assert "timeout: float = 12.0" in source
    assert "CREATE_NO_WINDOW" in source

def test_v177_message_cleanup_map_defaults_and_update_cadence():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert '<button id="clearMessagesButton" type="button" class="btn danger">Limpar</button>' in html
    assert '>Apagar todas</button>' not in html

    map_start = html.index('id="mapContextBar"')
    map_end = html.index("<main>", map_start)
    map_bar = html[map_start:map_end]
    assert map_bar.count('id="mapHistoryToggle"') == 1
    assert 'id="toggleReplayBarButton"' not in html

    assert db.DEFAULT_CONFIG["track_color"].lower() == "#3ba6ff"
    assert db.DEFAULT_CONFIG["topology_rf_color"].lower() == "#ffff00"
    assert db.DEFAULT_CONFIG["topology_igate_color"].lower() == "#ffff00"
    assert db.DEFAULT_CONFIG["topology_width"] == 1
    assert db.DEFAULT_CONFIG["traffic_animation_enabled"] == 1
    assert db.DEFAULT_CONFIG["sound_on_station_activity"] == 1

    assert 'name="topology_width" id="topologyWidth" type="range" min="1" max="10" step="1" value="1"' in html
    assert html.count('value="#ffff00"') >= 2
    assert "30 * 60 * 1000" in js
    assert "5 * 60 * 1000" not in js


def test_v177_legacy_build_patch_does_not_restore_global_history_button():
    root = Path(__file__).resolve().parent.parent
    patch = (root / "tools" / "apply_release_1_6_5.py").read_text(encoding="utf-8")
    assert "Não recriar o antigo botão" in patch
    assert "assert 'id=\"toggleReplayBarButton\"' not in html" in patch

def test_v177_windows_arm64_build_and_updater_assets(monkeypatch):
    root = Path(__file__).resolve().parent.parent
    workflow = (root / ".github" / "workflows" / "build-windows.yml").read_text(encoding="utf-8")
    installer = (root / "windows" / "installer_arm64.iss").read_text(encoding="utf-8")
    portable_spec = (root / "windows" / "PT2VHF_APRS_Client_Portable_ARM64.spec").read_text(encoding="utf-8")
    updater_source = (root / "pt2vhf_aprs" / "updater.py").read_text(encoding="utf-8")

    assert "windows-arm64:" in workflow
    assert "runs-on: windows-11-arm" in workflow
    assert "architecture: 'arm64'" in workflow
    assert "PT2VHF_APRS_Client_Setup_ARM64_v" in workflow
    assert "PT2VHF_APRS_Client_Portable_ARM64_v" in workflow

    assert "ArchitecturesAllowed=arm64" in installer
    assert "ArchitecturesInstallIn64BitMode=arm64" in installer
    assert "PT2VHF_APRS_Client_Setup_ARM64_v" in installer
    assert "PT2VHF_APRS_Client_Portable_ARM64" in portable_spec
    assert 'machine in {"x86_64", "arm64"}' in updater_source

    monkeypatch.setattr(updater, "_machine", lambda: "arm64")
    monkeypatch.setattr(updater, "current_update_mode", lambda: "windows-portable")
    assert updater.desired_asset_name("1.7.7") == "PT2VHF_APRS_Client_Portable_ARM64_v1.7.7.exe"
    monkeypatch.setattr(updater, "current_update_mode", lambda: "windows-installer")
    assert updater.desired_asset_name("1.7.7") == "PT2VHF_APRS_Client_Setup_ARM64_v1.7.7.exe"



def test_v179_map_speed_control_and_version_label():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    speed_pos = html.index('id="topologySpeed"')
    type_pos = html.index('id="mapTypeQuick"')
    assert speed_pos < type_pos
    speed_block = html[speed_pos:type_pos]
    for value, label in (("0.5", "0,5x"), ("1", "1x"), ("2", "2x"), ("5", "5x")):
        assert f'<option value="{value}"' in speed_block
        assert label in speed_block

    assert "setTrafficSpeed(event.target.value, 'topology')" in js
    assert "setTrafficSpeed(event.target.value, 'replay')" in js
    assert "pt2vhf_traffic_speed" in js
    assert "ui(`Versão ${current}`, `Build ${current}`)" in js


def test_v1710_unified_map_items_objects_and_internet_handoff():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    database = (root / "pt2vhf_aprs" / "database.py").read_text(encoding="utf-8")

    assert 'id="mapPeriodHours"' in html
    assert 'id="mapItemsButton"' in html
    assert 'id="mapViewTree"' in html
    assert 'id="mapViewAllButton"' in html
    assert 'id="mapTypeQuick"' in html
    assert '<option value="osm">OSM</option>' in html
    assert '<option value="topo">Topográfico</option>' in html
    assert '<option value="satellite">Satélite</option>' in html

    for removed in ("stationsHours", "tracklogHours", "topologyHours", "topologyToggle"):
        assert f'id="{removed}"' not in html
    assert 'id="trafficRangeStart"' not in html
    assert 'id="trafficRangeEnd"' not in html

    assert "interactive: false" in js
    assert "segment.internet_handoff" in js
    assert "APRS-IS" in js
    assert "edge.kind === 'igate' && !state.igateLinksEnabled" in js
    assert "edge.kind !== 'igate' && !state.rfLinksEnabled" in js
    assert "objectMarkers: new Map()" in js
    assert "tracklogEnabled:" in js
    assert "rfLinksEnabled:" in js
    assert "igateLinksEnabled:" in js
    assert "packetsEnabled:" in js

    assert "CREATE TABLE IF NOT EXISTS aprs_objects" in database
    assert '"internet_handoff": True' in database
    assert '"target": "APRS-IS"' in database

def test_v1711_map_items_menu_not_clipped_and_opens():
    root = Path(__file__).resolve().parent.parent
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    menu_css = css[css.index(".map-items-menu {"):css.index(".map-items-menu label")]
    assert "position: fixed;" in menu_css
    assert "z-index: 5000;" in menu_css

    assert "const positionMapItemsMenu = () => {" in js
    assert "const closeMapItemsMenu = () => {" in js
    assert "menu.classList.remove('hidden')" in js
    assert "requestAnimationFrame(positionMapItemsMenu)" in js
    assert "window.addEventListener('resize', positionMapItemsMenu)" in js
    assert "window.addEventListener('scroll', positionMapItemsMenu, true)" in js

def test_v1712_clickable_markers_use_dedicated_pane():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")

    assert "createPane('pt2vhfVisualPane')" in js
    assert "createPane('pt2vhfMarkerPane')" in js
    assert "visualPane.style.pointerEvents = 'none'" in js
    assert "markerPane.style.pointerEvents = 'auto'" in js
    assert "pane: 'pt2vhfMarkerPane'" in js
    assert "pane: 'pt2vhfVisualPane'" in js
    assert "zIndexOffset: 1200" in js
    assert "zIndexOffset: 1400" in js

    assert ".leaflet-pane.pt2vhf-visual-pane { pointer-events: none !important; }" in css
    assert ".leaflet-pane.pt2vhf-marker-pane { pointer-events: auto !important; }" in css
    assert ".aprs-marker-wrap { background: transparent; border: 0; pointer-events: auto !important; cursor: pointer; }" in css
    assert ".aprs-object-marker-wrap { background: transparent; border: 0; pointer-events: auto !important; cursor: pointer; }" in css

def test_v1713_object_symbols_activity_and_version_status():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")

    assert "const objectHasSymbol = !!String(object.symbol || '').trim();" in js
    assert "aprsSymbolHtml(object.symbol_table || '/', object.symbol, 24)" in js
    assert "aprs-object-fallback" in js
    assert '<div class="aprs-object-marker">◆</div>' not in js

    assert ".setContent('APRS-IS')" not in js
    assert "L.tooltip({ permanent: false, direction: 'top', opacity: .9 })" not in js
    assert "options.duration || 1000" in js

    assert "Versão atualizada" in js
    assert "Versão ${data.latest_version} disponível" in js
    assert "30 * 60 * 1000" in js

    assert "animation: stationTxPulse 1s ease-out;" in css
    assert "animation: stationTxRing 1s ease-out forwards;" in css
    assert ".aprs-object-marker-wrap.station-transmitting .aprs-object-marker" in css

def test_v1715_infrastructure_interaction_requires_evidence():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
    database = (root / "pt2vhf_aprs" / "database.py").read_text(encoding="utf-8")

    assert "function stationInteractionProfile(s)" in js
    assert "interaction_evidence" in js
    assert "const digiSymbol = String(s?.symbol || '') === '#';" in js
    assert "D-?STAR" in js
    assert "HOTSPOT" in js
    assert "DIGI(?:PEATER)?" in js
    assert "stationInteractionDisabledAttrs" in js
    assert '${interactionDisabled}>Ping/ACK</button>' in js
    assert '${interactionDisabled}>Enviar mensagem</button>' in js
    assert "station-interaction-disabled-note" in js

    assert "m.direction='in'" in database
    assert "UPPER(COALESCE(m.status,'')) IN ('ACK','REJ')" in database
    assert "q.response_at IS NOT NULL" in database
    assert "AS interaction_evidence" in database

    assert ".station-popup .btn:disabled" in css
    assert ".station-interaction-disabled-note" in css


def test_v1716_hierarchical_map_filters_and_device_roles():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css = (root / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")

    assert 'id="mapItemsButton"' in html
    assert '>Ver ▾</button>' in html
    assert 'id="mapViewTree"' in html
    assert 'id="mapViewAllButton"' in html
    assert 'id="mapItemStations"' not in html
    assert 'id="mapItemObjects"' not in html

    assert "digisEnabled:" in js
    assert "igatesEnabled:" in js
    assert "function stationMapFilterKeys(station)" in js
    assert "function stationMatchesViewFilter(station)" in js
    assert "function objectMatchesViewFilter(object)" in js
    assert "function renderMapViewTree(stations = [], objects = [])" in js
    assert "groupedMapNodes(stationRows, 'station')" in js
    assert "groupedMapNodes(digiRows, 'digi')" in js
    assert "groupedMapNodes(igateRows, 'igate')" in js
    assert "objectMapNodes(objects)" in js
    assert "pt2vhf_map_view_filters" in js
    assert "pt2vhf_map_view_expanded" in js
    assert "mapCallVisibleForTraffic" in js

    assert ".map-view-tree-menu" in css
    assert ".map-view-checkbox" in css
    assert ".map-view-children.hidden" in css

    digi = db.aprs_map_device_metadata("PY2AAA>APRFGL,WIDE1-1:>LoRa", "", "#")
    assert digi["map_role"] == "digi"
    assert digi["map_subtype"] in {"lora", "hybrid"}
    assert digi["device_class"] == "digi"

    igate = db.aprs_map_device_metadata("PY2AAA>APRFGI,TCPIP*:>LoRa", "", "&")
    assert igate["map_role"] == "igate"
    assert igate["map_subtype"] in {"lora", "hybrid"}
    assert igate["device_class"] == "igate"

    app = db.aprs_map_device_metadata("PY2AAA>APAND1,TCPIP*:>APRSdroid", "", ">")
    assert app["map_role"] == "station"
    assert app["device_class"] == "app"


def test_v1717_map_ver_groups_by_family_not_callsign():
    root = Path(__file__).resolve().parent.parent
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    database = (root / "pt2vhf_aprs" / "database.py").read_text(encoding="utf-8")

    assert "pt2vhf_map_view_filters_v2" in js
    assert "${role}:family:${family}" in js
    assert "object:family:" in js
    assert "map_family_label" in js
    assert "map_family_key" in js

    grouped_start = js.index("function groupedMapNodes(rows, role)")
    grouped_end = js.index("function objectMapNodes(objects)", grouped_start)
    grouped = js[grouped_start:grouped_end]
    assert "device_vendor" not in grouped
    assert "device_tocall" not in grouped
    assert "source_callsign" not in grouped
    assert "children:" not in grouped

    objects_start = js.index("function objectMapNodes(objects)")
    objects_end = js.index("function renderMapViewTree", objects_start)
    object_nodes = js[objects_start:objects_end]
    assert "source_callsign" not in object_nodes
    assert "object.name" not in object_nodes
    assert "children:" not in object_nodes

    assert "def _aprs_map_family" in database
    assert '"RDZSonDe"' in database
    assert '"Bravo Tracker"' in database
    assert '"D-Star"' in database
    assert '"DMR"' in database
    assert '"HBLink D-APRS Gateway"' in database

    rdz = db.aprs_map_device_metadata("PP2LA-11>APRRDZ,TCPIP*:;X3922153*...", "radiosonde", "/")
    assert rdz["map_family_label"] == "RDZSonDe"

    dmr = db.aprs_map_device_metadata("PY2AAA>APBM01,TCPIP*:>BrandMeister DMR", "DMR", ">")
    assert dmr["map_family_label"] == "DMR"

    hblink = db.aprs_map_device_metadata("KF7EEL>APHBL1,TCPIP*:>HBLink D-APRS Gateway", "D-APRS", "&")
    assert hblink["map_family_label"] == "HBLink D-APRS Gateway"
