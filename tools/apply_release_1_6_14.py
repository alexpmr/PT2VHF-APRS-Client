from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "pt2vhf_aprs/database.py": [
        "def process_received_packet(",
        "def _record_packet_conn(",
        "def _record_topology_from_raw_conn(",
        "def _upsert_station_conn(",
        "def _add_aprs_log_conn(",
        "rx_transaction_slow",
    ],
    "pt2vhf_aprs/aprs_service.py": [
        "db.process_received_packet(line, parsed, from_call, fmt)",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.14 validation failed: {needle!r} missing from {rel}")

service = (ROOT / "pt2vhf_aprs/aprs_service.py").read_text(encoding="utf-8")
block = service.split("def _handle_line", 1)[1].split("def _handle_message", 1)[0]
for forbidden in (
    'db.record_packet(line, from_call, fmt)',
    'db.record_topology_from_raw(line)',
    'db.upsert_station(parsed)',
):
    if forbidden in block:
        raise SystemExit(f"v1.6.14 validation failed: legacy RX write remains: {forbidden}")

print("v1.6.14 single-transaction RX validation OK")
