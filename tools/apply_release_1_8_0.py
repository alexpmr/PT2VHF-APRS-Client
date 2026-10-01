from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.0":
    raise SystemExit(f"v1.8.0 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.0"'],
    "pt2vhf_aprs/tnc_service.py": [
        "class KissStreamDecoder",
        "def decode_ax25",
        "def encode_ax25",
        "def digipeat_frame",
        "def add_igate_q_construct",
        "def direct_heard_recent",
        "def optimizer_report",
        '"auto_tx_enabled": 0',
        '"igate_tx_enabled": 0',
        '"optimizer_mode": "observe"',
        "last_direct_heard",
    ],
    "pt2vhf_aprs/aprs_service.py": [
        "def ingest_rf_packet",
        "def send_igate_packet",
        "tnc_service.handle_is_packet",
        "via_rf: bool = False",
    ],
    "pt2vhf_aprs/web.py": [
        "/api/tnc/status",
        "/api/tnc/ports",
        "/api/tnc/connect",
        "/api/tnc/config",
        "/api/tnc/frames",
        "/api/tnc/decisions",
        "/api/tnc/heard",
        "/api/tnc/optimizer",
        "/api/tnc/tx/stop",
        "/api/tnc/tx/resume",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'data-tab="tnc"',
        'id="tncTransport"',
        'id="tncDigiEnabled"',
        'id="tncIgateRx"',
        'id="tncIgateTx"',
        'id="tncOptimizerMode"',
        'id="tncEmergencyStop"',
        "Quem fala com quem",
    ],
    "pt2vhf_aprs/static/js/tnc.js": [
        "collectConfig",
        "refreshData",
        "/api/tnc/connect",
        "/api/tnc/optimizer",
        "/api/tnc/tx/stop",
    ],
    "requirements.txt": ["pyserial>=3.5,<4.0"],
    "tests/test_v180_tnc.py": [
        "test_kiss_escape_roundtrip",
        "test_ax25_tnc2_roundtrip_and_path_flags",
        "test_fill_in_digi_consumes_wide1_1",
        "test_wide_digi_decrements_remaining_hops",
        "test_digi_blocks_loop_when_own_call_already_in_path",
        "test_recent_direct_hearing_has_own_timestamp",
        "test_v180_no_rf_auto_tx_defaults",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.0"'],
    "CHANGELOG.md": ["## 1.8.0 - 2026-10-01"],
    "README.md": ["# PT2VHF APRS Client - v1.8.0", "## Novidades da v1.8.0"],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.0 validation failed: {needle!r} missing from {rel}")

# Segurança: o release não pode nascer transmitindo automaticamente.
from pt2vhf_aprs.tnc_service import normalize_tnc_config
cfg = normalize_tnc_config({}, strict=False)
for key in ("auto_tx_enabled", "digi_enabled", "igate_tx_enabled"):
    if cfg.get(key):
        raise SystemExit(f"v1.8.0 safety validation failed: {key} must default off")

print("v1.8.0 TNC/RF production validation OK")
