from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


version = read("VERSION").strip()
if version != "1.8.18":
    raise SystemExit(f"v1.8.18 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.18"'],
    "pt2vhf_aprs/agwpe_transport.py": ["AGWPE_HEADER", "enable_raw_command", "raw_tx_frame", "AGWPEStreamDecoder"],
    "pt2vhf_aprs/advanced_features.py": [
        "/api/v1818/stations/search", "/api/v1818/network-quality", "/api/v1818/period-compare",
        "/api/v1818/topology-graph", "/api/v1818/export.csv", "/api/v1818/export.geojson",
        "/api/v1818/diagnostics.zip",
    ],
    "pt2vhf_aprs/static/js/v1818.js": ["v1818QuickSearch", "v1818StationPanel", "v1818AdvancedPanel"],
    "pt2vhf_aprs/static/css/v1818.css": [".v1818-side-panel", ".v1818-metrics"],
    "pt2vhf_aprs/templates/index.html": ["css/v1818.css", "js/v1818.js", 'value="agwpe"'],
    "pt2vhf_aprs/tnc_service.py": ["agwpe_host", "agwpe_port", "agwpe_radio_port", "AGWPEStreamDecoder"],
    ".github/workflows/build-production-current.yml": ["linux-arm64", "v1.8.18"],
    "linux/build_linux.sh": ["PT2VHF_LINUX_ARCH", "arm64"],
}
for rel, needles in checks.items():
    text = read(rel)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.18 validation failed: {needle!r} missing from {rel}")
print("v1.8.18 validation OK")
