"""Valida metadados e interfaces da release v1.14.37 antes do build."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


version = "1.14.37"
assert read("VERSION").strip() == version
assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
assert "filevers=(1, 14, 37, 0)" in read("windows/version_info.txt")
assert "prodvers=(1, 14, 37, 0)" in read("windows/version_info.txt")
assert "## 1.14.37 - 2026-10-14" in read("CHANGELOG.md")
assert '"1.14.37": {' in read("pt2vhf_aprs/version_notes.py")
assert "# PT2VHF APRS Client - v1.14.37" in read("README.md")
for workflow in (".github/workflows/build-production-current.yml",
                 ".github/workflows/build-full-current.yml"):
    assert "apply_release_1_14_37.py" in read(workflow)
for path, marker in {
    "pt2vhf_aprs/route_hypotheses.py": "explore_possible_routes",
    "pt2vhf_aprs/web.py": '"/api/topology/rf-possible-routes"',
    "pt2vhf_aprs/static/js/app.js": "async function exploreRfPossibleRoutes()",
    "pt2vhf_aprs/templates/index.html": 'id="rfPossibleRoutes"',
    "tests/test_v1437_possible_routes.py": "test_pt2ap_mobile_south_to_brasilia",
    "pt2vhf_aprs/database.py": 'DEFAULT_APRS_FILTER = "r/4000"',
}.items():
    assert marker in read(path), f"{path}: missing {marker}"
if any(s.startswith("## Novo —") for s in read("BACKLOG.md").splitlines()):
    raise SystemExit("Untriaged backlog entry")
print("v1.14.37 release validation OK")
