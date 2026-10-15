"""Valida a integração e os metadados da release v1.14.40."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


version = "1.14.40"
assert read("VERSION").strip() == version
assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
assert "filevers=(1, 14, 40, 0)" in read("windows/version_info.txt")
assert "prodvers=(1, 14, 40, 0)" in read("windows/version_info.txt")
assert "## 1.14.40 - 2026-10-14" in read("CHANGELOG.md")
assert '"1.14.40": {' in read("pt2vhf_aprs/version_notes.py")
assert "# PT2VHF APRS Client - v1.14.40" in read("README.md")
assert "issue #90" in read("BACKLOG.md") or "#90" in read("BACKLOG.md")
assert "#91" in read("BACKLOG.md")
for workflow in (".github/workflows/build-production-current.yml",
                 ".github/workflows/build-full-current.yml"):
    assert "apply_release_1_14_39.py" in read(workflow)
js = read("pt2vhf_aprs/static/js/app.js")
assert "color: edge.kind === 'igate' ? state.mapConfig.topology_igate_color : state.mapConfig.topology_rf_color" in js
assert "dashArray: edge.kind === 'igate' ? '7 5' : null" in js
assert "style.dashArray = '5 7'" not in js
assert "style.dashArray = '2 5'" not in js
assert "controller.abort(), 45000" in js
backend = read("pt2vhf_aprs/web.py")
assert "release_check.fetch_latest_release()" in backend
assert 'payload["error_code"] = issue.code' in backend
assert "diag.log_event(\"update_check_failed\"" in backend
native = read("pt2vhf_aprs/release_check.py")
assert "Invoke-RestMethod" in native
assert "_github_web_tag" in native
assert "ServerCertificateValidationCallback" not in native
assert "test_windows_native_fallback_after_python_certificate_failure" in read("tests/test_v1438_release.py")
if any(line.startswith("## Novo —") for line in read("BACKLOG.md").splitlines()):
    raise SystemExit("Entrada não triada no backlog")
print("v1.14.40 release validation OK")

assert "from . import category_statistics, category_clear" in backend
assert "deadline_seconds=None" in backend
assert "list_mobile_rf_coverage(hours)" in backend
assert "statistics/categories" in backend
assert "retention/clear/<category>" in backend
assert "moving_rf_repeaters" in read("pt2vhf_aprs/topology_map.py")
assert "rfCoverageEnabled" in js
assert "data-rf-record-cancel" in js
assert "progress.eta_seconds" in js
assert "analysisCategoryCounts" in read("pt2vhf_aprs/templates/index.html")
assert "test_moving_digi_not_drawn_as_rf_spider" in read("tests/test_v1439_features.py")
assert 'id="mapTypeQuick"' not in read("pt2vhf_aprs/templates/index.html")
assert 'id="topologySpeed"' in read("pt2vhf_aprs/templates/index.html")
assert "Sair da apresentação" in read("pt2vhf_aprs/static/js/v190.js")
