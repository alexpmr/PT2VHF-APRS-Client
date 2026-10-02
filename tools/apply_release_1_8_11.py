from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.11":
    raise SystemExit(f"v1.8.11 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.11"'],
    "pt2vhf_aprs/database.py": [
        "medium TEXT NOT NULL DEFAULT 'APRS-IS'",
        "rx_fingerprint TEXT",
        "idx_packets_medium_time",
        "idx_packets_medium_call_time",
        "idx_packets_fingerprint_time",
        "def _packet_reception_fingerprint(",
        'medium: str = "APRS-IS"',
        "AS rf_packets",
        "AS aprsis_packets",
        '"rf_packets": rf_packets',
        '"aprsis_packets": aprsis_packets',
    ],
    "pt2vhf_aprs/aprs_service.py": [
        'medium="APRS-IS"',
        'medium="RF"',
    ],
    "pt2vhf_aprs/tnc_service.py": [
        "def heard_stations(",
        "rf_packet_count",
        "rf_evidence",
        "direct_known",
        "def tnc_reception_stats(",
        "rf_unique_stations",
        "logical_packets_deduplicated",
        '"tnc_rf_station_heard"',
        '"tnc_rf_rx_summary"',
    ],
    "pt2vhf_aprs/web.py": [
        "tnc_reception_stats,",
        'payload["reception_media"] = tnc_reception_stats(hours)',
    ],
    "pt2vhf_aprs/templates/index.html": [
        "<th>Recepções</th>",
        "<th>Pacotes RF</th>",
        "<th>Distância</th>",
        'colspan="8"',
    ],
    "pt2vhf_aprs/static/js/tnc.js": [
        "row.rf_packet_count",
        "row.distance_km",
        "row.direct_known",
        "const hasDistance =",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "Recepção RF × APRS-IS",
        "rf_unique_stations",
        "logical_packets_deduplicated",
        "data.reception_media?.logical_packets_deduplicated",
        "rf_packets",
        "aprsis_packets",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        "#tab-config .config-card > h3",
        "color: #ff8a3d;",
        "font-size: 18px;",
        "color: #c85f00;",
        ".topology-stat-cards",
    ],
    "tests/test_v1811_rf_stats_config.py": [
        "test_v1811_packets_persist_reception_medium_and_fingerprint",
        "test_v1811_rf_heard_falls_back_to_persistent_packet_evidence",
        "test_v1811_reception_stats_preserve_both_media_and_deduplicate_logical_packet",
        "test_v1811_statistics_expose_rf_and_aprsis_columns_and_summary",
        "test_v1811_settings_section_titles_are_larger_and_orange",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.11"'],
    "CHANGELOG.md": ["## 1.8.11 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.11", "## Novidades da v1.8.11"],
    "BACKLOG.md": ["## Concluído na v1.8.11"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.11 validation failed: {needle!r} missing from {rel}")

db_source = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")
if "INSERT INTO packets(timestamp, from_call, packet_format, raw) VALUES" in db_source:
    raise SystemExit("v1.8.11 validation failed: legacy packet insert without medium remains")

tnc_js = (ROOT / "pt2vhf_aprs/static/js/tnc.js").read_text(encoding="utf-8")
if '<tr><td colspan="6">' + "${tr('Nenhuma estação ouvida pelo TNC.')}" in tnc_js:
    raise SystemExit("v1.8.11 validation failed: old RF-heard empty-row colspan remains")

print("v1.8.11 RF reception/statistics and settings hierarchy validation OK")
