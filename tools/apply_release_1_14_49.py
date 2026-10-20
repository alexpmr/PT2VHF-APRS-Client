"""Valida invariantes mínimas antes de empacotar a release v1.14.49."""
import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


assert read("VERSION").strip() == "1.14.49"
assert '__version__ = "1.14.49"' in read("pt2vhf_aprs/__init__.py")
assert "filevers=(1, 14, 49, 0)" in read("windows/version_info.txt")
assert "prodvers=(1, 14, 49, 0)" in read("windows/version_info.txt")
assert "## 1.14.49 - 2026-10-20" in read("CHANGELOG.md")
assert '"1.14.49": {' in read("pt2vhf_aprs/version_notes.py")
for workflow in (".github/workflows/build-production-current.yml",
                 ".github/workflows/build-full-current.yml"):
    assert "apply_release_1_14_49.py" in read(workflow)
    assert "apply_release_1_14_48.py" not in read(workflow)

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
print("v1.14.49 release validation OK")
