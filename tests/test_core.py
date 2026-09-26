import pytest
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db
from pt2vhf_aprs import updater
from pt2vhf_aprs.aprs_service import APRSService, build_beacon_packet, build_bulletin_packet, build_query_payload, calculate_aprs_passcode, classify_message_type, expand_filter, mask_sensitive_log_line, parse_message_line, parse_query_text, parse_trace_nodes, split_message_id, split_aprs_message_parts
from pt2vhf_aprs.web import version_tuple


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
            assert cfg["topology_rf_color"] == "#35a7ff"
            assert cfg["topology_igate_color"] == "#b06cff"
            assert cfg["topology_width"] == 2
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
            assert ("PT2DGI", "PT2IGT", "igate") in keys
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
    assert html.count('type="submit"') == 0
    assert 'id="saveConfigFooterButton" type="button"' in html
    assert 'id="saveConfigFooterButton"' in html
    assert 'id="whatsNewModal"' in html
    assert 'name="sound_on_station_activity" type="checkbox" checked' in html
    assert 'name="highlight_station_activity" type="checkbox" checked' in html
    assert "station-log-button" in js
    assert "Ver logs" in html
    assert "favorite-star" in js
    assert "map-line-legend" in js
    assert "analysisPeriod" in js
    assert "5 * 60 * 1000" in js
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
            assert stats["items"][0]["friendly_name"] == "Dire Wolf 1.7"
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


def test_qarray_igate_reception_is_rf_link():
    source, edges = db._observed_topology_edges("PY2ABC-9>APRS,PT2DGI*,WIDE2-1,qAR,PT2IGT:>teste")
    assert source == "PY2ABC-9"
    assert ("PY2ABC-9", "PT2DGI", "rf", None) in edges
    assert ("PT2DGI", "PT2IGT", "rf", "PT2IGT") in edges
    assert not any(kind == "igate" for _a, _b, kind, _igate in edges)


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


def test_auto_update_is_disabled_but_version_detection_remains():
    root = Path(__file__).resolve().parent.parent
    web_source = (root / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")
    windows_source = (root / "windows_app.py").read_text(encoding="utf-8")
    assert "Atualização automática desativada" in web_source
    assert "launch_pending_update" not in windows_source
    assert "GITHUB_LATEST_RELEASE_API" in web_source


def test_update_check_cache_is_five_minutes():
    root = Path(__file__).resolve().parent.parent
    web_source = (root / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")
    js_source = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "UPDATE_CACHE_SECONDS = 5 * 60" in web_source
    assert "5 * 60 * 1000" in js_source


def test_updater_asset_name_contains_version():
    name = updater.desired_asset_name("1.6")
    assert "1.6" in name
    assert name
