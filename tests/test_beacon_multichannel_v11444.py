"""Acceptance coverage for v1.14.44 multichannel beacons and orphan RF geometry."""
from __future__ import annotations

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs.aprs_service import APRSService
from pt2vhf_aprs.topology_map import mark_overview_endpoint_coherence
from pt2vhf_aprs.tnc_service import TNCService, normalize_tnc_config


CONFIG = {
    "callsign": "PT2VHF", "ssid": 15,
    "latitude": -15.8, "longitude": -47.9, "altitude": 1100,
    "symbol_table": "/", "symbol": ">", "comment": "Teste",
}


class FakeTNC:
    def __init__(self, connected=True, should_fail=False):
        self.connected = connected
        self.should_fail = should_fail
        self.calls = []
    def status(self):
        return {"connected": self.connected, "wanted": self.connected, "tx_paused": False}
    def queue_local_beacon(self, info):
        self.calls.append(info)
        if self.should_fail:
            raise OSError("Falha KISS simulada")
        return {"queued": True}


@pytest.mark.parametrize("net,rf,expected", [
    (True, True, ("sent", "queued")),
    (True, False, ("sent", "unavailable")),
    (False, True, ("unavailable", "queued")),
])
def test_beacon_sends_every_available_transport(monkeypatch, net, rf, expected):
    from pt2vhf_aprs import tnc_service
    fake = FakeTNC(rf)
    monkeypatch.setattr(db, "get_config", lambda: dict(CONFIG))
    monkeypatch.setattr(tnc_service, "service", fake)
    monkeypatch.setattr(tnc_service, "get_tnc_config", lambda: {
        "auto_tx_enabled": 1, "tx_confirmed": 1})
    monkeypatch.setattr("pt2vhf_aprs.aprs_service.aprslib", None)
    service = APRSService()
    service._set_status(connected=net, verified=net)
    sent = []
    monkeypatch.setattr(service, "_send_raw", lambda value: sent.append(value))
    for _ in range(2):  # segundo clique não tem cooldown
        result = service.send_beacon()
        assert result["transports"]["aprs_is"]["status"] == expected[0]
        assert result["transports"]["tnc"]["status"] == expected[1]
    assert len(sent) == (2 if net else 0)
    assert len(fake.calls) == (2 if rf else 0)
    assert all(value.startswith("=") for value in fake.calls)


def test_beacon_partial_failure_still_sends_other_transport(monkeypatch):
    from pt2vhf_aprs import tnc_service
    fake = FakeTNC(True, should_fail=True)
    monkeypatch.setattr(db, "get_config", lambda: dict(CONFIG))
    monkeypatch.setattr(tnc_service, "service", fake)
    monkeypatch.setattr(tnc_service, "get_tnc_config", lambda: {
        "auto_tx_enabled": 1, "tx_confirmed": 1})
    monkeypatch.setattr("pt2vhf_aprs.aprs_service.aprslib", None)
    service = APRSService()
    service._set_status(connected=True, verified=True)
    sent = []
    monkeypatch.setattr(service, "_send_raw", lambda raw: sent.append(raw))
    result = service.send_beacon()
    assert len(sent) == 1
    assert result["transports"]["aprs_is"]["status"] == "sent"
    assert result["transports"]["tnc"]["status"] == "error"


def test_beacon_rejects_no_authorized_transport(monkeypatch):
    from pt2vhf_aprs import tnc_service
    monkeypatch.setattr(db, "get_config", lambda: dict(CONFIG))
    monkeypatch.setattr(tnc_service, "service", FakeTNC(False))
    monkeypatch.setattr(tnc_service, "get_tnc_config", lambda: {
        "auto_tx_enabled": 0, "tx_confirmed": 0})
    with pytest.raises(ConnectionError, match="Nenhuma conexão"):
        APRSService().send_beacon()


def test_tnc_beacon_never_transmits_internet_path(monkeypatch):
    from pt2vhf_aprs import tnc_service
    service = TNCService()
    monkeypatch.setattr(service, "status", lambda: {"connected": True, "tx_paused": False})
    monkeypatch.setattr(service, "_own_call", lambda: "PT2VHF-15")
    monkeypatch.setattr(tnc_service, "get_tnc_config", lambda: {
        "auto_tx_enabled": 1, "tx_confirmed": 1, "transport": "serial", "serial_protocol": "kiss"})
    frames = []
    monkeypatch.setattr(service, "_enqueue", lambda frame, reason, **kwargs: frames.append((frame, kwargs)) or True)
    monkeypatch.setattr(tnc_service, "record_decision", lambda *args, **kwargs: None)
    answer = service.queue_local_beacon("=1548.00S/04754.00W>TEST")
    assert answer["queued"]
    assert b"TCPIP" not in frames[0][0]
    assert "TCPIP" not in frames[0][1]["raw_tnc2"]


def test_radtel_profile_accepts_115200_and_preserves_explicit_baud():
    cfg = normalize_tnc_config({"device_profile": "radtel_rt950_pro",
        "transport": "serial", "serial_port": "COM10", "serial_baud": 115200}, strict=False)
    assert cfg["serial_baud"] == 115200
    assert cfg["serial_protocol"] == "kiss"
    cfg2 = normalize_tnc_config({"device_profile": "radtel_rt950_pro",
        "transport": "serial", "serial_port": "COM10", "serial_baud": 9600}, strict=False)
    assert cfg2["serial_baud"] == 9600  # migração não muda configuração sem consentimento


def test_orphan_risk_suppressed_only_for_inferred_overview():
    historical = dict(source="PP5AU-7", target="PP5DGI", kind="rf",
        source_lat=-27.1, source_lon=-48.6, target_lat=-27.2, target_lon=-48.5,
        direct_rf_confirmed=False)
    direct = {**historical, "kind": "rf_temp", "direct_rf_confirmed": True}
    positions = {"PP5AU-7": (-26.7, -48.6), "PP5DGI": (-27.2, -48.5)}
    result = mark_overview_endpoint_coherence([historical, direct], positions)
    assert result[0]["render_on_overview"] is False
    assert "PP5AU-7" in result[0]["endpoint_geometry_warning"]
    assert result[1]["render_on_overview"] is True
    close = {**historical, "source_lat": -26.7}
    assert mark_overview_endpoint_coherence([close], positions)[0]["render_on_overview"] is True
