import pytest

from pt2vhf_aprs import tnc_service as tnc


class FakeSerial:
    instances = []

    def __init__(self):
        self.port = None
        self.baudrate = None
        self.timeout = None
        self.write_timeout = None
        self.events = []
        self.cts, self.dsr, self.cd, self.ri = True, False, False, False
        self._dtr = self._rts = True  # padrão do pyserial
        FakeSerial.instances.append(self)

    @property
    def dtr(self):
        return self._dtr

    @dtr.setter
    def dtr(self, value):
        self.events.append(("dtr", value))
        self._dtr = value

    @property
    def rts(self):
        return self._rts

    @rts.setter
    def rts(self, value):
        self.events.append(("rts", value))
        self._rts = value

    def open(self):
        self.events.append(("open",))


@pytest.fixture
def fake_serial(monkeypatch):
    FakeSerial.instances.clear()
    monkeypatch.setattr(tnc.serial, "Serial", FakeSerial)
    return FakeSerial


def test_serial_line_modes_default_and_validation():
    cfg = tnc.normalize_tnc_config({"transport": "serial", "serial_port": "COM10"})
    assert cfg["serial_dtr"] == "default" and cfg["serial_rts"] == "default"
    assert tnc.normalize_tnc_config({"serial_rts": "OFF"})["serial_rts"] == "off"
    with pytest.raises(ValueError):
        tnc.normalize_tnc_config({"serial_dtr": "maybe"})


def test_default_mode_keeps_pyserial_behaviour(fake_serial):
    handle = tnc.open_serial_port({"serial_port": "COM10", "serial_baud": 115200}, timeout=1.0, write_timeout=2.0)
    assert handle.events == [("open",)]
    assert handle.port == "COM10" and handle.baudrate == 115200
    assert tnc.serial_line_summary(handle) == "DTR=1 RTS=1 CTS=1 DSR=0 CD=0 RI=0"


def test_lines_are_set_before_open_to_avoid_ptt_pulse(fake_serial):
    cfg = {"serial_port": "COM10", "serial_baud": 115200, "serial_dtr": "off", "serial_rts": "off"}
    handle = tnc.open_serial_port(cfg, timeout=1.0, write_timeout=2.0)
    assert handle.events == [("dtr", False), ("rts", False), ("open",)]
    assert tnc.serial_line_summary(handle).startswith("DTR=0 RTS=0")
