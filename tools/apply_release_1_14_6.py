from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.6":
    raise SystemExit("VERSION must be 1.14.6")
if '__version__ = "1.14.6"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.6")

removed = [
    "pt2vhf_aprs/v112_satellites.py",
    "pt2vhf_aprs/v113_satellites.py",
    "pt2vhf_aprs/v114_satellite_ops.py",
    "pt2vhf_aprs/static/css/v112.css",
    "pt2vhf_aprs/static/css/v114.css",
    "pt2vhf_aprs/static/css/v141.css",
    "pt2vhf_aprs/static/js/v112.js",
    "pt2vhf_aprs/static/js/v113.js",
    "pt2vhf_aprs/static/js/v114.js",
    "pt2vhf_aprs/static/js/v141.js",
]
for rel in removed:
    if (ROOT / rel).exists():
        raise SystemExit(f"retired SAT file still present: {rel}")

requirements = read("requirements.txt").lower()
if "sgp4" in requirements:
    raise SystemExit("sgp4 must not remain in runtime dependencies")

web = read("pt2vhf_aprs/web.py")
for marker in (
    "register_v112_satellite_routes",
    "register_v113_satellite_routes",
    "register_v114_routes",
):
    if marker in web:
        raise SystemExit(f"retired SAT route still registered: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
for marker in (
    'data-tab="satellites"',
    'id="tab-satellites"',
    "satelliteTabCountdown",
    "satelliteMap",
):
    if marker in html:
        raise SystemExit(f"retired SAT UI still present: {marker}")

app = read("pt2vhf_aprs/static/js/app.js")
if "satellitesEnabled" in app or "pt2vhf:satellite-visibility" in app:
    raise SystemExit("retired SAT visibility state still present")
for marker in (
    "orderedEdges",
    "line.bringToFront()",
    "Também observado por RF",
    "Também observado via APRS-IS",
):
    if marker not in app:
        raise SystemExit(f"v1.14.6 topology UI marker missing: {marker}")

database = read("pt2vhf_aprs/database.py")
for marker in (
    "Consolida duplicatas sem apagar evidência APRS-IS confirmada",
    'base["kind"] = kind',
    'base["classification_source"] = "APRS-IS confirmado"',
    "RF e APRS-IS são evidências independentes",
):
    if marker not in database:
        raise SystemExit(f"v1.14.6 topology backend marker missing: {marker}")

tnc = read("pt2vhf_aprs/tnc_service.py")
if "queue_satellite_beacon" in tnc:
    raise SystemExit("satellite beacon pipeline still present")

tests = read("tests/test_v146_release.py")
for marker in (
    "test_v146_satellite_runtime_is_removed",
    "test_v146_mixed_pair_preserves_rf_and_aprsis_edges",
    "test_v146_pure_rf_never_becomes_internet",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.6 regression missing: {marker}")

print("v1.14.6 validation OK")
