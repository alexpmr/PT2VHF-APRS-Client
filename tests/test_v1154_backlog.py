"""Regressões v1.15.4: comentário no pacote, busca e boletim multimeio."""
from __future__ import annotations

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs import aprs_service as aprs
from pt2vhf_aprs import tnc_service as tnc
from pt2vhf_aprs import version_announce as announce


@pytest.mark.parametrize("comment", [
    "", "PT2VHF APRS Client", "Teste curto", "Mensagem personalizada com texto longo que ultrapassa bastante o limite",
    "Minha estacao www.pt2vhf.com", "site https://www.pt2vhf.com/aprs e www.PT2VHF.com",
])
def test_site_in_each_transmitted_beacon(comment):
    cfg = {
        "callsign": "PT2ABC", "ssid": 2, "latitude": -15.5, "longitude": -47.9,
        "symbol": ">", "symbol_table": "/", "comment": comment, "altitude": 1100,
    }
    original = dict(cfg)
    packet = aprs.build_beacon_packet(cfg)
    info = packet.split(":", 1)[1]
    text = info.split(" /A=", 1)[0]
    suffix = text[1 + 8 + 1 + 9 + 1:]  # após posição descomprimida e símbolo
    assert suffix.endswith("www.PT2VHF.com")
    assert suffix.count("www.PT2VHF.com") == 1
    assert len(suffix) <= 40
    assert cfg == original
    assert aprs.beacon_comment_with_site(comment) == suffix


def test_search_messages_matches_sender_recipient_and_accent(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "messages.db")
    db.init_db()
    db.add_message("in", "PY2ABC", "PT2XYZ", "Teste de ligação")
    db.add_message("in", "PY2DEF", "PT2XYZ", "Nada especial")
    assert len(db.list_messages("py2abc")) == 1
    assert len(db.list_messages("PT2XYZ")) == 2
    assert len(db.list_messages("LIGACAO")) == 1
    assert len(db.list_messages("ligação", station_filter="PT2XYZ")) == 1
    assert db.list_messages("não existe", station_filter="PT2XYZ") == []


class DummyService:
    def __init__(self, verified: bool):
        self.verified = verified
        self.sent = []

    def status(self):
        return {"connected": self.verified, "verified": self.verified}

    def send_bulletin(self, text, bulletin_id="0", group=""):
        self.sent.append(("APRS-IS", bulletin_id, text))

    def send_bulletin_rf(self, text, bulletin_id="0", group=""):
        self.sent.append(("RF", bulletin_id, text))


@pytest.mark.parametrize("aprs_ready,rf_ready,medium", [
    (True, True, "APRS-IS"), (True, False, "APRS-IS"),
    (False, True, "RF"), (False, False, None),
])
def test_announce_transport_priority(tmp_path, monkeypatch, aprs_ready, rf_ready, medium):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "announce.db")
    db.init_db()
    with db.connection() as conn:
        conn.execute("UPDATE config SET callsign='PT2ABC' WHERE id=1")
    monkeypatch.setattr(tnc.service, "status", lambda: {"connected": rf_ready, "tx_paused": False})
    monkeypatch.setattr(tnc, "get_tnc_config", lambda: {
        "auto_tx_enabled": rf_ready, "tx_confirmed": rf_ready
    })
    service = DummyService(aprs_ready)
    outcome = announce.maybe_announce(service)
    if medium is None:
        assert outcome == "waiting_connection"
        assert not service.sent
    else:
        assert outcome == "sent"
        assert len(service.sent) == 1
        assert service.sent[0][0] == medium
        assert service.sent[0][1] == "A"
        assert "www.PT2VHF.com" in service.sent[0][2]
        assert announce.maybe_announce(service) == "not_pending"


def test_tnc_bulletin_has_no_internet_path_and_queues_only_if_authorized(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "tnc.db")
    db.init_db()
    monkeypatch.setattr(tnc.service, "status", lambda: {"connected": True, "tx_paused": False})
    monkeypatch.setattr(tnc.service, "_own_call", lambda: "PT2ABC")
    monkeypatch.setattr(tnc.service, "_tx_paused", False)
    monkeypatch.setattr(tnc, "get_tnc_config", lambda: {
        "auto_tx_enabled": True, "tx_confirmed": True, "transport": "tcp"
    })
    frames = []
    monkeypatch.setattr(tnc.service, "_enqueue", lambda frame, reason, **kwargs: frames.append(kwargs.get("raw_tnc2")) or True)
    result = tnc.service.queue_local_bulletin("Novo APRS v1.15.4 www.PT2VHF.com", bulletin_id="A")
    assert result["raw"].startswith("PT2ABC>APZVHF::BLNA")
    assert "TCPIP" not in result["raw"]
    assert len(frames) == 1
    assert "www.PT2VHF.com" in frames[0]
