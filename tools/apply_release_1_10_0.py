from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.10.0":
    raise SystemExit("VERSION must be 1.10.0")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.10.0"'],
    "pt2vhf_aprs/v110_features.py": [
        "QRZ_XML_BASE", "/api/v110/station-profile/", "/api/v110/ais-profile/",
        "/api/v110/rf-metadata", "/api/v110/tm-d700/probe",
        "/api/v110/soak/start", "record_rf_metadata",
    ],
    "pt2vhf_aprs/soak_test.py": ["class SoakTestManager", "memory_leak_suspected", "soak_samples_v110"],
    "pt2vhf_aprs/static/js/v110.js": [
        "QRZ.com", "/api/v110/ais-profile/", "/api/v110/soak/start",
        "/api/v110/tm-d700/probe", "v110-profile-photo",
    ],
    "pt2vhf_aprs/templates/index.html": ["css/v110.css", "js/v110.js"],
    "pt2vhf_aprs/tnc_service.py": [
        "metric_source", "frequency_hz", 'payload["dcd"]', "serial_modem_status",
    ],
    "tools/i18n_audit.py": ["dictionary_coverage_percent", "--strict"],
    "tools/migration_matrix.py": ['"1.6.x"', '"1.9.0"', "PRAGMA integrity_check"],
    "docs/TM_D700_VALIDATION.md": ["Somente considerar o TM-D700", "segunda estação"],
    "tests/test_v110_quality_enrichment.py": ["test_qrz_official_xml_provider_and_cache", "test_soak_report_detects_large_memory_growth"],
    ".github/workflows/build-production-current.yml": ["apply_release_1_10_0.py", "i18n_audit.py --strict", "migration_matrix.py"],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.10.0 validation failed: {needle!r} missing from {rel}")
print("v1.10.0 validation OK")
