from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.13.0":
    raise SystemExit("VERSION must be 1.13.0")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.13.0"'],
    "pt2vhf_aprs/v113_satellites.py": [
        "AMSAT_NASABARE_TLE",
        "classify_operation",
        "refresh_multisource",
        "next_aprs_pass",
        "start_scheduler",
        "/api/v113/satellites/next-pass",
        "/api/v113/satellites/source-test",
        "/api/v113/satellites/<int:norad_id>/operation",
    ],
    "pt2vhf_aprs/v112_satellites.py": [
        "v113.enriched_catalog(scope)",
        "v113.filter_passes",
        "tle_source_id",
    ],
    "pt2vhf_aprs/web.py": ["register_v113_satellite_routes(app)"],
    "pt2vhf_aprs/templates/index.html": [
        'id="satelliteTabCountdown"',
        'id="satelliteSelectAll"',
        'id="satelliteClearAll"',
        'id="satelliteCatalogScope"',
        'id="satelliteCoverageAlarmEnabled"',
        'id="satelliteSourcesList"',
        'id="tncDeviceProfile"',
        'id="tncSerialProtocol"',
        'id="tncPacketRfBaud"',
        "css/v113.css",
        "js/v113.js",
    ],
    "pt2vhf_aprs/static/js/v113.js": [
        "formatHms",
        "setInterval(renderCountdown,1000)",
        "showAlarm",
        "satellite-source-row",
        "/api/v113/satellites/next-pass",
    ],
    "pt2vhf_aprs/static/js/v112.js": [
        "satellite-operational",
        "data-satellite-service",
        "satelliteSelectAll",
        "satelliteClearAll",
    ],
    "pt2vhf_aprs/tnc_service.py": [
        '"device_profile": "generic_kiss"',
        '"serial_protocol": "kiss"',
        '"packet_rf_baud": 1200',
        "terminal_bytes_active",
        "last_transport_sample_hex",
        "TX automático não é suportado no perfil serial terminal/PKT",
    ],
    "pt2vhf_aprs/v111_features.py": [
        "terminal_prompt_detected",
        '"physical_rf_tx": False',
        "physical_validation_note",
    ],
    "tests/test_v113_release.py": [
        "test_v113_strict_aprs_classification_does_not_promote_generic_ax25",
        "test_v113_terminal_profile_blocks_automatic_tx",
        "test_v113_tnc_health_terminal_bytes_not_reported_as_missing_kiss",
    ],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.13.0 validation failed: {needle!r} missing from {rel}")

win = read("windows/version_info.txt")
for needle in ("filevers=(1, 13, 0, 0)", "prodvers=(1, 13, 0, 0)", "'1.13.0'"):
    if needle not in win:
        raise SystemExit(f"v1.13.0 Windows metadata missing {needle}")

print("v1.13.0 validation OK")
