"""v2.0.6: LoRa APRS (pedido do Alex): posição comprimida, overlay numérico e itens."""
import pytest

from pt2vhf_aprs import aprs_parse
from pt2vhf_aprs import database as db
from pt2vhf_aprs.aprs_service import service


def test_lora_igate_compressed_position():
    p = aprs_parse.parse(r"PU2ABC-7>APLRG1,WIDE1-1,qAR,PY2XYZ-10:=LXc#7C\1ha !GLoRa APRS")
    assert p["format"] == "compressed"
    assert p["latitude"] == pytest.approx(-20.2397, abs=1e-3)
    assert p["longitude"] == pytest.approx(-42.9050, abs=1e-3)
    assert (p["symbol_table"], p["symbol"]) == ("L", "a")
    assert p["comment"] == "LoRa APRS" and p["messagecapable"] is True


def test_compressed_course_speed_and_altitude():
    moving = aprs_parse.parse("PU2DEF-9>APLRT1:!/5L!!<*e7>7P[ LoRa")
    assert moving["course"] == 88 and moving["speed"] == pytest.approx(67.1, abs=0.1)
    alt = aprs_parse.parse("PU2GHI-7>APLRT1:!/5L!!<*e7OS]S LoRa")
    assert alt["altitude"] == pytest.approx(3049.4, abs=0.5)


def test_compressed_numeric_overlay_becomes_digit():
    # Na posição comprimida, o overlay 0-9 é transmitido como a-j.
    assert aprs_parse.parse("X>APLRT1:!a5L!!<*e7>7P[ c")["symbol_table"] == "0"
    assert aprs_parse.parse("X>APLRT1:!j5L!!<*e7>7P[ c")["symbol_table"] == "9"
    assert aprs_parse.parse("X>APLRT1:!L5L!!<*e7>7P[ c")["symbol_table"] == "L"


def test_items_plain_and_compressed():
    plain = aprs_parse.parse("X>APLRG1:)LGW!2330.00S/04630.00W& gateway")
    assert plain["format"] == "item" and plain["item_name"] == "LGW" and plain["alive"] is True
    assert plain["latitude"] == pytest.approx(-23.5) and plain["symbol"] == "&"
    killed = aprs_parse.parse("X>APLRG1:)LGW2_/5L!!<*e7&  Gitem")
    assert killed["format"] == "item" and killed["alive"] is False and killed["comment"] == "item"
    with pytest.raises(Exception):
        aprs_parse.parse("X>APLRG1:)?")


def test_lora_packets_reach_map_and_messages(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "lora.db")
    db.init_db()
    service._handle_line(r"PU2ABC-7>APLRG1,WIDE1-1,qAR,PY2XYZ-10:=LXc#7C\1ha !GLoRa APRS")
    service._handle_line("PU2JKL-7>APLRT1,qAR,PY2XYZ-10::PY2ABC   :Teste LoRa{12")
    service._handle_line("PU2MNO-7>APLRG1,qAR,PY2XYZ-10:)LGW!2330.00S/04630.00W& gateway")
    with db.connection() as conn:
        st = conn.execute("SELECT * FROM stations WHERE callsign='PU2ABC-7'").fetchone()
        assert st["latitude"] == pytest.approx(-20.2397, abs=1e-3) and st["packet_format"] == "compressed"
        msg = conn.execute("SELECT * FROM messages WHERE from_call='PU2JKL-7'").fetchone()
        assert msg["message"] == "Teste LoRa" and msg["to_call"] == "PY2ABC"
        obj = conn.execute("SELECT * FROM aprs_objects WHERE name='LGW'").fetchone()
        assert obj["source_callsign"] == "PU2MNO-7" and obj["latitude"] == pytest.approx(-23.5)
