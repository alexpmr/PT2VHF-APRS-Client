from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db
from pt2vhf_aprs.aprs_service import build_beacon_packet, build_bulletin_packet, calculate_aprs_passcode, classify_message_type, expand_filter, mask_sensitive_log_line, parse_message_line, split_message_id


def test_beacon_packet():
    cfg = {
        "callsign": "PT2VHF", "ssid": 15, "latitude": -15.8, "longitude": -47.9,
        "altitude": 1000, "symbol_table": "/", "symbol": ">", "comment": "Teste"
    }
    packet = build_beacon_packet(cfg)
    assert packet.startswith("PT2VHF-15>APRS,TCPIP*:=1548.00S/04754.00W>")
    assert "/A=003281" in packet


def test_filter_shortcut():
    cfg = {"latitude": -15.8, "longitude": -47.9}
    assert expand_filter("r/500", cfg) == "r/-15.80000/-47.90000/500"
    assert expand_filter("m/50", cfg) == "m/50"


def test_message_parser_with_id():
    raw = "PY2ABC>APRS,TCPIP*::PT2VHF   :Teste de mensagem{123"
    msg = parse_message_line(raw, {})
    assert msg == {"from": "PY2ABC", "to": "PT2VHF", "text": "Teste de mensagem{123"}
    text, mid = split_message_id(msg["text"])
    assert text == "Teste de mensagem"
    assert mid == "123"


def test_database_config_and_station():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            cfg = db.save_config({"callsign": "PT2VHF", "ssid": 0, "latitude": -15.8, "longitude": -47.9})
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
            assert [row["direction"] for row in rows] == ["RX", "TX"]
            assert rows[0]["raw"].startswith("PY2ABC")
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
    assert packet == "PT2VHF-9>APRS,TCPIP*::BLN1     :Boletim geral de teste"
    assert addressee == "BLN1"
    assert message_type == "bulletin"
    assert "{" not in packet

    group_packet, group_to, group_type, _ = build_bulletin_packet(
        source="PT2VHF-9",
        text="Boletim do grupo DF",
        bulletin_id="2",
        group="DF",
    )
    assert group_packet == "PT2VHF-9>APRS,TCPIP*::BLN2DF   :Boletim do grupo DF"
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
                "map_type": "satellite",
                "track_color": "#ff6600",
                "track_width": 5,
            })
            assert cfg["map_type"] == "satellite"
            assert cfg["track_color"] == "#ff6600"
            assert cfg["track_width"] == 5
    finally:
        db.DB_PATH = original


def test_aprs_passcode():
    assert calculate_aprs_passcode("PT2VHF") == 22950
    assert calculate_aprs_passcode("PT2VHF-9") == 22950
    assert calculate_aprs_passcode("PT2VHF-15") == 22950
