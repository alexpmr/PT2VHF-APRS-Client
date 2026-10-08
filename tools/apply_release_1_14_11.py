from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.11":
    raise SystemExit("VERSION must be 1.14.11")
if '__version__ = "1.14.11"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.11")

database = read("pt2vhf_aprs/database.py")
for marker in (
    "def list_rf_route_records(",
    "direct_distance_km",
    "emitted_pairs",
    "source >= nxt",
):
    if marker not in database:
        raise SystemExit(f"v1.14.11 RF ranking marker missing: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
for marker in (
    '>Pesquisar</button>',
    '<span>TNC</span>',
    '<strong id="connectionControlStatus">APRS-IS</strong>',
):
    if marker not in html:
        raise SystemExit(f"v1.14.11 header/map marker missing: {marker}")

js = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "ui('Atualizada', 'Up to date')",
    "statusText.textContent = 'APRS-IS'",
    "status.connected ? 'connected' : 'disconnected'",
    "formatRfDistanceKm(route.direct_distance_km)",
):
    if marker not in js:
        raise SystemExit(f"v1.14.11 app marker missing: {marker}")

tnc_js = read("pt2vhf_aprs/static/js/tnc.js")
for marker in (
    "text.textContent = 'TNC'",
    "connected ? 'connected' : 'disconnected'",
):
    if marker not in tnc_js:
        raise SystemExit(f"v1.14.11 TNC marker missing: {marker}")
if "TNC offline" in tnc_js:
    raise SystemExit("obsolete TNC offline header label remains")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    "v1.14.11 - indicadores compactos do cabeçalho",
    ".connection-control-copy small { display: none; }",
    ".tnc-header-status",
):
    if marker not in css:
        raise SystemExit(f"v1.14.11 CSS marker missing: {marker}")

tests = read("tests/test_v1411_release.py")
for marker in (
    "test_v1411_rf_records_rank_endpoint_distance_not_route_length",
    "test_v1411_rf_records_emit_each_endpoint_pair_once",
    "test_v1411_record_ui_uses_direct_distance_as_primary",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.11 regression missing: {marker}")

print("v1.14.11 validation OK")
