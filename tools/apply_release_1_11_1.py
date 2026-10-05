from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.11.1":
    raise SystemExit("VERSION must be 1.11.1")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.11.1"'],
    "pt2vhf_aprs/database.py": [
        "def _consolidate_topology_edges(",
        'base["kind"] = "rf" if rf_rows else "igate"',
        'base["mixed_evidence"] = bool(rf_rows and internet_rows)',
        "result = _consolidate_topology_edges(valid_rows)",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "const mixedEvidence = Boolean(edge.mixed_evidence)",
        "Também observado via APRS-IS",
        "edge.kind === 'igate' ? '7 5' : null",
        "edge.kind === 'igate' ? 'Internet/APRS-IS' : 'Enlace RF observado'",
    ],
    "tests/test_core.py": [
        "test_v1111_topology_rf_precedence_when_same_pair_has_internet_evidence",
        "test_v1111_topology_is_dashed_only_when_100_percent_internet",
        "test_v1111_frontend_uses_continuous_rf_for_mixed_topology",
    ],
    ".github/workflows/build-production-current.yml": ["apply_release_1_11_1.py"],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.11.1 validation failed: {needle!r} missing from {rel}")
print("v1.11.1 validation OK")
