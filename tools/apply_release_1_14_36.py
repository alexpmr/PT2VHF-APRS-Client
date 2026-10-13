"""Valida a consistência da versão completa v1.14.36 antes da compilação."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


assert read("VERSION").strip() == "1.14.36"
assert '__version__ = "1.14.36"' in read("pt2vhf_aprs/__init__.py")
assert "filevers=(1, 14, 36, 0)" in read("windows/version_info.txt")
assert "prodvers=(1, 14, 36, 0)" in read("windows/version_info.txt")
assert "## 1.14.36 - 2026-10-13" in read("CHANGELOG.md")
assert '"1.14.36": {' in read("pt2vhf_aprs/version_notes.py")
assert "# PT2VHF APRS Client - v1.14.36" in read("README.md")
for workflow in (".github/workflows/build-production-current.yml", ".github/workflows/build-full-current.yml"):
    assert "tools/apply_release_1_14_36.py" in read(workflow)
for path, marker in {
    "pt2vhf_aprs/topology_map.py": "rf_direct_count",
    "pt2vhf_aprs/database.py": 'DEFAULT_APRS_FILTER = "r/4000"',
    "pt2vhf_aprs/static/js/app.js": "inferredRouteEdge ? '#94a3b8'",
    "pt2vhf_aprs/templates/index.html": 'value="r/4000"',
    "tests/test_v1436_rf_filter.py": "test_inferred_long_rf_hop_is_not_direct",
}.items():
    assert marker in read(path), f"{path}: missing {marker}"
if any(s.startswith("## Novo —") for s in read("BACKLOG.md").splitlines()):
    raise SystemExit("Untriaged backlog entry")
print("v1.14.36 release validation OK")
