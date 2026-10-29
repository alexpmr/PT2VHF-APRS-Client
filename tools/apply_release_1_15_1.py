"""Valida invariantes mínimas antes de empacotar a release v1.15.1."""
import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


assert read("VERSION").strip() == "1.15.1"
assert '__version__ = "1.15.1"' in read("pt2vhf_aprs/__init__.py")
assert "filevers=(1, 15, 1, 0)" in read("windows/version_info.txt")
assert "prodvers=(1, 15, 1, 0)" in read("windows/version_info.txt")
assert "## 1.15.1 - 2026-10-29" in read("CHANGELOG.md")
assert '"1.15.1": {' in read("pt2vhf_aprs/version_notes.py")
for workflow in (".github/workflows/build-production-current.yml",
                 ".github/workflows/build-full-current.yml"):
    assert "apply_release_1_15_1.py" in read(workflow)
    assert "apply_release_1_15_0.py" not in read(workflow)

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
# v1.14.62: planejamento no mapa (enlace entre 2 pontos e melhor ponto).
planning = read("pt2vhf_aprs/planning.py")
assert "APRS_FREQ_MHZ = 145.570" in planning
assert "def link_analysis(" in planning and "def best_points(" in planning and "class TerrainTiles" in planning
assert "def survey_pdf(" in read("pt2vhf_aprs/planning_pdf.py")
assert "register_planning_routes(app)" in web
assert "js/planning.js" in html and "css/planning.css" in html
assert "reportlab" in read("requirements.txt") and "reportlab" in read("requirements-windows7.txt")
for shell in ("windows_app.py", "linux_app.py", "macos_app.py"):
    assert "def save_binary_file(" in read(shell)
assert "def _map_link_checks(" in read("pt2vhf_aprs/db_check.py")
assert "MOBILE_MIN_TRACK_SPAN_KM" in read("pt2vhf_aprs/topology_map.py")
assert "weather_report" in database
spacetime = read("pt2vhf_aprs/spacetime_topology.py")
assert "def _backfill_fixed_station_geometry(" in spacetime and "_still_at(conn, call, before)" in spacetime
assert "_backfill_fixed_station_geometry(conn)" in spacetime[spacetime.index("def _init_db"):]
assert "PERMANENT_DEFAULTS_MIGRATION" in read("pt2vhf_aprs/retention.py")
assert '"packets_days": 0,' in read("pt2vhf_aprs/v111_features.py")
assert '"retention_days": 0,' in tnc
assert "def maybe_announce(" in read("pt2vhf_aprs/version_announce.py")
assert "version_announce.start_worker(service)" in read("pt2vhf_aprs/web.py")
assert 'id="whatsNewSkipAnnounce"' in html and "installVersionAnnounce();" in read("pt2vhf_aprs/static/js/v111.js")
assert "_compiled_tocall_pattern" in database
assert "saved_results.load(\"topology_stats\"" in read("pt2vhf_aprs/web.py")
assert "refreshTopologyAnalysis({ force: true })" in js
assert "sync_readme_release_downloads.py" not in read(".github/workflows/build-production-current.yml")
assert 'id="officialSiteNotice"' in html and "function showOfficialSiteNotice()" in js
# v1.15.0: menu Ferramentas, análise de cobertura, PDFs com mapa base, TNC / RF em Configuração.
planning_js = read("pt2vhf_aprs/static/js/planning.js")
coverage = read("pt2vhf_aprs/coverage.py")
routes = read("pt2vhf_aprs/planning_routes.py")
assert 'id="toolsMenuButton"' in html and 'id="toolsMenu"' in html
for tool_id in ("toolCoverage", "toolLink", "toolSurvey", "toolPdf", "toolDiagnostics"):
    assert f'id="{tool_id}"' in html
assert html.index('data-tab="automations"') < html.index('id="toolsMenuButton"') < html.index('data-tab="config"')
assert html.index('id="toolsMenu"') < html.index('id="elevationToggle"') < html.index('id="mapContextBar"')
assert "planningSection" not in planning_js and "function openCoverage(" in planning_js
assert "$$('.tab[data-tab]')" in js
assert "DEFAULT_POWER_W = 50.0" in coverage and "DEFAULT_KM = 50.0" in coverage and "MAX_KM = 100.0" in coverage
assert "tx_power_w: 50" in planning_js and "Voltar à cobertura" in planning_js
assert '"sensitivity_uv"' in coverage and '"sensitivity_s"' in coverage
for route in ("/api/planning/coverage", "/api/planning/highest", "/api/planning/best-coverage"):
    assert route in routes
assert "def _observed(" in routes and "_coverage_cache" in routes
assert "def render(" in read("pt2vhf_aprs/pdf_map.py") and "def coverage_pdf(" in read("pt2vhf_aprs/planning_pdf.py")
assert "def despike(" in planning and "despike(flat, width)" in planning
assert '"elevation_color": "#e0ac3e"' in database and 'id="elevationColor"' in html
assert 'data-tab="tnc"' not in html and '<details id="tncConfigBlock"' in html and '<details id="tncMonitorsBlock"' in html
assert html.index('<section id="tab-config"') < html.index('id="tncConfigBlock"') < html.index('<section id="tab-about"')
# v1.15.1: sub-abas da Configuração, voz digital não é RF, cancelar processamento.
assert "js/config_tabs.js" in html and "window.pt2vhfConfigTabs" in read("pt2vhf_aprs/static/js/config_tabs.js")
for key in ("station", "aprsis", "map", "app", "database", "backup"):
    assert f'data-config-tab="{key}"' in html
assert "pt2vhfConfigTabs.show('tnc')" in read("pt2vhf_aprs/static/js/tnc.js")
assert "def digital_voice_origin(" in database and "and not digital" in database
assert "def purge_digital_voice_once(" in read("pt2vhf_aprs/rf_coverage.py")
assert "rf_coverage.purge_digital_voice_once(conn)" in read("pt2vhf_aprs/spacetime_topology.py")
assert "function cancelCurrentProcessing()" in js and 'id="globalProcessingElapsed"' in html
assert "external.addEventListener('abort'" in js
assert 'id="tncSave"' in html and "function tncVisible()" in read("pt2vhf_aprs/static/js/tnc.js")
print("v1.15.1 release validation OK")
