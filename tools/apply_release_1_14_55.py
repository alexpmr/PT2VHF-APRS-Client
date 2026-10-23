"""Valida invariantes mínimas antes de empacotar a release v1.14.55."""
import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


assert read("VERSION").strip() == "1.14.55"
assert '__version__ = "1.14.55"' in read("pt2vhf_aprs/__init__.py")
assert "filevers=(1, 14, 55, 0)" in read("windows/version_info.txt")
assert "prodvers=(1, 14, 55, 0)" in read("windows/version_info.txt")
assert "## 1.14.55 - 2026-10-23" in read("CHANGELOG.md")
assert '"1.14.55": {' in read("pt2vhf_aprs/version_notes.py")
for workflow in (".github/workflows/build-production-current.yml",
                 ".github/workflows/build-full-current.yml"):
    assert "apply_release_1_14_55.py" in read(workflow)
    assert "apply_release_1_14_54.py" not in read(workflow)

html = read("pt2vhf_aprs/templates/index.html")
database = read("pt2vhf_aprs/database.py")
tnc = read("pt2vhf_aprs/tnc_service.py")
updater = read("pt2vhf_aprs/updater.py")
js = read("pt2vhf_aprs/static/js/app.js")

# Mapa offline com SRI íntegro (inclusive após checkout no Windows).
assert "unpkg.com" not in html
leaflet = (ROOT / "pt2vhf_aprs/static/vendor/leaflet/leaflet.js").read_bytes()
digest = base64.b64encode(hashlib.sha256(leaflet).digest()).decode()
assert f'integrity="sha256-{digest}"' in html, "leaflet.js alterado (CRLF?)"
assert "pt2vhf_aprs/static/vendor/** -text" in read(".gitattributes")

# Topologia ligada explicitamente; sem monkey-patch.
assert "init_db = _spacetime_topology._init_db" in database
assert "db.init_db = _init_db" not in read("pt2vhf_aprs/spacetime_topology.py")

# #118, #121, #103, #86
assert "def open_serial_port(" in tnc and '"serial_rts": "default"' in tnc
assert 'id="tncSerialRts"' in html and 'id="tncSerialLinesText"' in html
assert "_quarantine_malformed_positions_v11448(conn)" in database
assert "def restore_quarantined_positions(" in database
cmd_helper = updater[updater.index("def _write_windows_cmd_helper("):updater.index("def _write_windows_helper(")]
assert "installer completed" not in cmd_helper
assert 'findstr /C:"version=%target% " "%marker%"' in updater
assert "reportLastUpdateApply(data.last_apply)" in js
assert "data-rf-records-metric" in js

# Mudanças da v1.14.47 continuam presentes.
assert 'id="webAccessLabel"' not in html
assert ".brand h1 .app-version" in read("pt2vhf_aprs/static/css/app.css")
topology = read("pt2vhf_aprs/topology_map.py")
assert "repeater_targets = set(mobile_repeaters)" in topology
assert "mobile_repeater_callsigns" not in topology
assert "count: state.mapLayerCounts.rf" in js
assert "function countTopologyLayers(" in js
assert "/api/diagnostics/client-event" in read("pt2vhf_aprs/web.py")
assert "reportMapRender" in js
assert "MOBILE_SPEED_KMH" in topology
assert "latest_by_pair" in topology
assert "def list_rf_activity_points(" in topology
assert "Cobertura RF (mapa de calor)" in js
assert "HEAT_RADIUS_METERS" in read("pt2vhf_aprs/static/js/v142.js")
assert "maybePromptUpdate(data);" in js
assert '"rf_coverage": 0' in read("pt2vhf_aprs/retention.py")
assert "rf_coverage.list_points(hours)" in read("pt2vhf_aprs/web.py")
assert "of $('#retentionPolicyGrid" not in js
assert "const HEAT_RADIUS_METERS = 2500;" in read("pt2vhf_aprs/static/js/v142.js")
# v1.14.54: teste de recepção do TNC e Verificar banco.
assert "def listen_test(" in read("pt2vhf_aprs/tnc_listen.py")
assert "def rx_monitor(" in tnc and 'self._log_rx("bytes", chunk)' in tnc
assert 'id="tncListenTest"' in html and 'id="tncRxMonitorLive"' in html
assert "bindListenTest();" in read("pt2vhf_aprs/static/js/tnc.js")
assert "def run_check(" in read("pt2vhf_aprs/db_check.py") and "def repair(" in read("pt2vhf_aprs/db_check.py")
assert 'id="checkDatabaseButton"' in html and "/api/database/check" in js
web = read("pt2vhf_aprs/web.py")
assert '"/api/tnc/listen-test"' in web and '"/api/database/repair"' in web
for workflow in (".github/workflows/build-production-current.yml",
                 ".github/workflows/build-full-current.yml"):
    text = read(workflow)
    manual = text[text.index("  manual-pdf:"):]
    assert manual[:400].count("runs-on: ubuntu-24.04") == 1
# v1.14.55: planejamento no mapa (enlace entre 2 pontos e melhor ponto).
planning = read("pt2vhf_aprs/planning.py")
assert "APRS_FREQ_MHZ = 145.570" in planning
assert "def link_analysis(" in planning and "def best_points(" in planning and "class TerrainTiles" in planning
assert "def survey_pdf(" in read("pt2vhf_aprs/planning_pdf.py")
assert "register_planning_routes(app)" in web
assert "js/planning.js" in html and "css/planning.css" in html
assert "reportlab" in read("requirements.txt") and "reportlab" in read("requirements-windows7.txt")
for shell in ("windows_app.py", "linux_app.py", "macos_app.py"):
    assert "def save_binary_file(" in read(shell)
print("v1.14.55 release validation OK")
