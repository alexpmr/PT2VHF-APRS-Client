from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pt2vhf_aprs import database as db

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.20":
    raise SystemExit(f"v1.7.20 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.20"'],
    "pt2vhf_aprs/static/js/app.js": [
        "function statisticsPeriodValue(value)",
        "state.topologyHours = statisticsPeriodValue(state.topologyHours)",
        "topology/stats?hours=",
        "function stationConfigurationComplete",
        "function focusInitialConfigurationIfNeeded",
        "focusInitialConfigurationIfNeeded();",
    ],
    "pt2vhf_aprs/database.py": [
        'direct_rf_gate = token in {"qAR", "qAO"}',
        "TCPIP/TCPXX elsewhere in the",
    ],
    "README.md": [
        "## Downloads da versão mais recente",
        "releases/latest/download/PT2VHF_APRS_Client_Setup_x64_v1.7.20.exe",
        "releases/latest/download/PT2VHF_APRS_Client_Manual_v1.7.20.pdf",
    ],
    "tests/test_core.py": [
        "test_v1720_statistics_period_is_independent_from_map_period",
        "test_v1720_qar_qao_preserve_rf_even_with_tcpip_marker",
        "test_v1720_first_run_opens_configuration_and_focuses_callsign",
        "test_v1720_readme_has_direct_latest_downloads_and_no_download_counter_table",
    ],
    "CHANGELOG.md": ["## v1.7.20 - 2026-09-30"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.20"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.20 validation failed: {needle!r} missing from {rel}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for forbidden in ("## Downloads por Release", "DOWNLOAD_STATS_START", "DOWNLOAD_STATS_END"):
    if forbidden in readme:
        raise SystemExit(f"v1.7.20 validation failed: old download counter section still contains {forbidden!r}")

js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
refresh_start = js.index("async function refreshTopologyAnalysis()")
refresh_end = js.index("document.addEventListener('click', event => {", refresh_start)
refresh = js[refresh_start:refresh_end]
if "state.mapPeriodHours" in refresh:
    raise SystemExit("v1.7.20 validation failed: Statistics still reads Map period")

source, edges = db._observed_topology_edges("PY2SRC>APRS,TCPIP*,qAR,PY2IGT:>rf")
if ("PY2SRC", "PY2IGT", "rf", "PY2IGT") not in edges:
    raise SystemExit(f"v1.7.20 validation failed: qAR/TCPIP classified incorrectly: {edges!r}")
source, edges = db._observed_topology_edges("PY2SRC>APRS,TCPIP*,qAr,PY2IGT:>internet")
if ("PY2SRC", "PY2IGT", "igate", "PY2IGT") not in edges:
    raise SystemExit(f"v1.7.20 validation failed: qAr classified incorrectly: {edges!r}")

print("v1.7.20 production validation OK")
