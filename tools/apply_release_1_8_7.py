from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.7":
    raise SystemExit(f"v1.8.7 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.7"'],
    "pt2vhf_aprs/tnc_service.py": [
        "def _windows_cim_serial_ports()",
        "Get-CimInstance Win32_PnPEntity",
        r"HARDWARE\DEVICEMAP\SERIALCOMM",
        "list_ports.comports(include_links=True)",
        "def _merge_serial_ports(",
        "CH9102",
        "CH340",
        "CH341",
        "CP210x",
        "FTDI",
        "CDC/ACM",
        "tnc_serial_scan",
        "porta está ocupada por outro programa ou o Windows negou o acesso",
        "inexistente ou desconectada",
    ],
    "pt2vhf_aprs/web.py": [
        'request.args.get("refresh")',
        "available_ports(force=force)",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="tncSerialPort"',
        'list="tncSerialPortList"',
        'id="tncSerialPortList"',
        'id="tncSerialDevicesBody"',
        'id="tncRescanDevices"',
        "Equipamentos seriais detectados",
    ],
    "pt2vhf_aprs/static/js/tnc.js": [
        "function renderSerialDevices(",
        "function updateSerialProfileHint(",
        "data-tnc-use-port",
        "?refresh=1",
        "Radtel RT-950 Pro detectado",
        "Interface CH9102 detectada. Se esta porta pertencer a um Radtel RT-950 Pro",
        "field('tncSerialBaud').value = '115200'",
    ],
    "pt2vhf_aprs/static/css/tnc.css": [
        ".tnc-serial-devices-card",
        ".tnc-serial-devices-table",
    ],
    "tests/test_v187_serial_devices.py": [
        "test_v187_merge_serial_ports_keeps_multiple_windows_devices",
        "test_v187_backend_uses_pyserial_and_native_windows_fallbacks",
        "test_v187_serial_ui_has_manual_com_and_explicit_equipment_table",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.7"'],
    "CHANGELOG.md": ["## 1.8.7 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.7", "## Novidades da v1.8.7"],
    "requirements.txt": ["pyserial>=3.5,<4.0"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.7 validation failed: {needle!r} missing from {rel}")

from pt2vhf_aprs.tnc_service import _merge_serial_ports, _friendly_serial_equipment

ports = _merge_serial_ports([
    {
        "device": "COM6",
        "description": "USB-Enhanced-SERIAL CH9102",
        "hwid": "USB VID:PID=1A86:55D4",
        "source": "pyserial",
    },
    {
        "device": "COM10",
        "description": "USB-SERIAL CH340",
        "pnp_device_id": r"USB\VID_1A86&PID_7523\ABC",
        "source": "windows_cim",
    },
])
if [item["device"] for item in ports] != ["COM6", "COM10"]:
    raise SystemExit("v1.8.7 validation failed: multiple serial COM ports were not preserved")
if ports[0].get("chipset") != "CH9102" or ports[1].get("chipset") != "CH340":
    raise SystemExit("v1.8.7 validation failed: chipset identification")

generic, _ = _friendly_serial_equipment({"description": "USB-Enhanced-SERIAL CH9102"})
if "Radtel" in generic:
    raise SystemExit("v1.8.7 validation failed: generic CH9102 was incorrectly labeled as Radtel")

print("v1.8.7 serial discovery and equipment identification validation OK")
