from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


version = read("VERSION").strip()
if version != "1.9.0":
    raise SystemExit(f"v1.9.0 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.9.0"'],
    "pt2vhf_aprs/agwpe_transport.py": ["AGWPE_HEADER", "AGWPEStreamDecoder", "raw_tx_frame"],
    "pt2vhf_aprs/tnc_service.py": ["def probe_transport(", "AGWPETransport", "agwpe_radio_port"],
    "pt2vhf_aprs/v190_features.py": [
        "/api/v190/search", "/api/v190/groups", "/api/v190/timeline",
        "/api/v190/backup/full", "/api/v190/backup/restore",
        "/api/v190/alerts/settings", "/api/v190/alerts/state", "/api/v190/tnc/test",
    ],
    "pt2vhf_aprs/static/js/v190.js": [
        "floatPanel('tab-messages'", "floatPanel('tab-stations'", "v190GlobalSearch",
        "v190Presentation", "v190Timeline", "v190Restore", "v190TestTnc",
    ],
    "pt2vhf_aprs/static/css/v190.css": [".v190-floating", "resize:both", ".v190-presentation"],
    "pt2vhf_aprs/templates/index.html": ["css/v190.css", "js/v190.js", 'value="agwpe"'],
    ".github/workflows/build-production-current.yml": ["linux-arm64", "apply_release_1_9_0.py"],
    "linux/build_linux.sh": ["PT2VHF_LINUX_ARCH", "arm64"],
    "tests/test_v190_features.py": ["test_v190_group_meta_search_and_backup", "test_v190_frontend_contains_detachable_panels"],
}
for rel, needles in checks.items():
    text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.9.0 validation failed: {needle!r} missing from {rel}")

print("v1.9.0 validation OK")
