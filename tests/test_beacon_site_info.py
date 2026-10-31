"""Mandatory site URL in APRS position information for every beacon transport."""
from __future__ import annotations

import pytest

from pt2vhf_aprs.aprs_service import (
    PT2VHF_BEACON_SITE,
    beacon_comment_with_site,
    build_beacon_packet,
)
from pt2vhf_aprs import database as db


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        ("", "www.PT2VHF.com"),
        ("Teste", "Teste www.PT2VHF.com"),
        ("PT2VHF APRS Client", "PT2VHF APRS Client www.PT2VHF.com"),
        ("PT2VHF APRS www.PT2VHF.com", "PT2VHF APRS www.PT2VHF.com"),
        ("Cliente https://www.pt2vhf.com/aprs", "Cliente www.PT2VHF.com"),
        ("APRS http://pt2vhf.com/aprs-android", "APRS www.PT2VHF.com"),
        ("Texto\\n personalizado  ", "Texto\\n personalizado www.PT2VHF.com"),
    ],
)
def test_site_suffix_and_deduplication(original, expected):
    assert beacon_comment_with_site(original) == expected
    assert beacon_comment_with_site(original).count(PT2VHF_BEACON_SITE) == 1


@pytest.mark.parametrize("text", ["", "TESTE", "X" * 300, "ABC www.pt2vhf.com Y", "Site HTTPS://WWW.PT2VHF.COM/APRS"])
def test_40_char_limit_reserves_room_for_site(text):
    result = beacon_comment_with_site(text)
    assert result.endswith(PT2VHF_BEACON_SITE)
    assert len(result) <= 40
    assert result.lower().count("pt2vhf.com") == 1


def test_position_beacon_contains_site_and_does_not_modify_saved_comment():
    cfg = {
        "callsign": "PT2VHF", "ssid": 3, "latitude": -15.8,
        "longitude": -47.9, "symbol_table": "/", "symbol": ">",
        "altitude": 1100, "comment": "Teste de uma descricao de mensagem bem longa que deveria ser reduzida",
    }
    before = dict(cfg)
    packet = build_beacon_packet(cfg)
    assert packet.startswith("PT2VHF-3>")
    assert ":=1548.00S/04754.00W>" in packet
    assert "www.PT2VHF.com /A=" in packet
    assert packet.count("www.PT2VHF.com") == 1
    assert cfg == before
    information = packet.split(">", 1)[1].split(":", 1)[1].split(" /A=", 1)[0]
    assert information.endswith(PT2VHF_BEACON_SITE)
    assert len(information) <= 40


def test_new_install_default_includes_site_and_old_install_is_transmission_safe():
    assert PT2VHF_BEACON_SITE in db.DEFAULT_CONFIG["comment"]
    for existing in ("PT2VHF APRS Client", "Meu comentario personalizado"):
        cfg = {
            "callsign": "PT2VHF", "ssid": 0, "latitude": -15.8,
            "longitude": -47.9, "comment": existing,
        }
        packet = build_beacon_packet(cfg)
        assert packet.count(PT2VHF_BEACON_SITE) == 1
        assert cfg["comment"] == existing
