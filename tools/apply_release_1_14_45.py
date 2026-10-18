"""Valida invariantes mínimas antes de empacotar a release v1.14.45."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


assert read("VERSION").strip() == "1.14.45"
assert '__version__ = "1.14.45"' in read("pt2vhf_aprs/__init__.py")
assert "filevers=(1, 14, 45, 0)" in read("windows/version_info.txt")
assert "prodvers=(1, 14, 45, 0)" in read("windows/version_info.txt")
assert "## 1.14.45 - 2026-10-18" in read("CHANGELOG.md")
assert '"1.14.45": {' in read("pt2vhf_aprs/version_notes.py")
assert "# PT2VHF APRS Client - v1.14.45" in read("README.md")
for workflow in (".github/workflows/build-production-current.yml",
                 ".github/workflows/build-full-current.yml"):
    assert "apply_release_1_14_45.py" in read(workflow)
    assert "apply_release_1_14_44.py" not in read(workflow)
tnc = read("pt2vhf_aprs/tnc_service.py")
aprs = read("pt2vhf_aprs/aprs_service.py")
web = read("pt2vhf_aprs/web.py")
js = read("pt2vhf_aprs/static/js/app.js")
assert "def queue_local_beacon(" in tnc
assert '"radtel_rt950_pro"' in tnc
assert "def ensure_beacon_worker(" in aprs
assert "tnc_service.queue_local_beacon(payload)" in aprs
assert "return jsonify(service.send_beacon())" in web
assert "const result = await api('/api/beacon', { method:'POST' });" in js
assert "edge.render_on_overview === false" in js
assert "mark_overview_endpoint_coherence" in read("pt2vhf_aprs/topology_map.py")
assert "def test_beacon_sends_every_available_transport" in read("tests/test_beacon_multichannel_v11444.py")
assert "test_rf_links_are_solid_while_internet_stays_dashed" in read("tests/test_rf_visual_v11445.py")
assert "inferredRouteEdge ? '5 6'" not in js
assert "inferredRouteEdge ? '#9ca3af'" not in js
assert "dashArray: edge.kind === 'igate' ? '7 5' : mobileRf ? '2 5' : null" in js
print("v1.14.45 release validation OK")
