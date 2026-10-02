from pathlib import Path

from pt2vhf_aprs.tnc_service import _friendly_serial_equipment, _merge_serial_ports

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v187_merge_serial_ports_keeps_multiple_windows_devices():
    ports = _merge_serial_ports([
        {
            "device": "COM6",
            "description": "USB-Enhanced-SERIAL CH9102",
            "hwid": "USB VID:PID=1A86:55D4",
            "manufacturer": "wch.cn",
            "source": "pyserial",
        },
        {
            "device": "COM10",
            "description": "USB-SERIAL CH340",
            "pnp_device_id": r"USB\VID_1A86&PID_7523\ABC",
            "manufacturer": "wch.cn",
            "source": "windows_cim",
        },
        {
            "device": "COM6",
            "description": r"\Device\Serial0",
            "source": "windows_registry",
        },
    ])
    assert [item["device"] for item in ports] == ["COM6", "COM10"]
    assert ports[0]["chipset"] == "CH9102"
    assert ports[0]["vid"] == "1A86"
    assert ports[0]["pid"] == "55D4"
    assert set(ports[0]["sources"]) == {"pyserial", "windows_registry"}
    assert ports[1]["chipset"] == "CH340"
    assert ports[1]["vid"] == "1A86"
    assert ports[1]["pid"] == "7523"


def test_v187_radtel_name_only_when_metadata_identifies_it():
    generic, chipset = _friendly_serial_equipment({
        "description": "USB-Enhanced-SERIAL CH9102",
        "manufacturer": "wch.cn",
    })
    assert "Radtel" not in generic
    assert chipset == "CH9102"

    radtel, chipset = _friendly_serial_equipment({
        "description": "Radtel RT-950 Pro TNC UART",
        "manufacturer": "Radtel",
        "hwid": "USB VID:PID=1A86:55D4",
    })
    assert radtel == "Radtel RT-950 Pro / TNC UART"
    assert isinstance(chipset, str)


def test_v187_backend_uses_pyserial_and_native_windows_fallbacks():
    source = read("pt2vhf_aprs/tnc_service.py")
    assert "list_ports.comports(include_links=True)" in source
    assert "Get-CimInstance Win32_PnPEntity" in source
    assert r"HARDWARE\DEVICEMAP\SERIALCOMM" in source
    assert "tnc_serial_scan" in source
    assert "manufacturer" in source
    assert "serial_number" in source
    assert "pnp_device_id" in source


def test_v187_serial_ui_has_manual_com_and_explicit_equipment_table():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/tnc.js")
    css = read("pt2vhf_aprs/static/css/tnc.css")

    assert 'id="tncSerialPort"' in html
    assert 'list="tncSerialPortList"' in html
    assert 'id="tncSerialPortList"' in html
    assert 'id="tncSerialDevicesBody"' in html
    assert "Equipamentos seriais detectados" in html
    assert 'id="tncRescanDevices"' in html
    assert "renderSerialDevices" in js
    assert "data-tnc-use-port" in js
    assert "?refresh=1" in js
    assert ".tnc-serial-devices-card" in css


def test_v187_radtel_uart_hint_is_conditional_and_115200():
    js = read("pt2vhf_aprs/static/js/tnc.js")
    assert "Radtel RT-950 Pro detectado" in js
    assert "Interface CH9102 detectada. Se esta porta pertencer a um Radtel RT-950 Pro" in js
    assert "field('tncSerialBaud').value = '115200'" in js


def test_v187_port_open_errors_are_user_friendly():
    source = read("pt2vhf_aprs/tnc_service.py")
    assert "porta está ocupada por outro programa ou o Windows negou o acesso" in source
    assert "inexistente ou desconectada" in source


def test_v187_version():
    assert read("VERSION").strip() == "1.8.7"
    assert '__version__ = "1.8.7"' in read("pt2vhf_aprs/__init__.py")
