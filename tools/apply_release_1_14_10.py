from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.10":
    raise SystemExit("VERSION must be 1.14.10")
if '__version__ = "1.14.10"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.10")

db = read("pt2vhf_aprs/database.py")
for marker in (
    "def list_rf_route_origins(",
    "def list_rf_route_records(",
    "def _rf_route_payload(",
    '"rf_route_records": list_rf_route_records',
):
    if marker not in db:
        raise SystemExit(f"v1.14.10 database marker missing: {marker}")

web = read("pt2vhf_aprs/web.py")
for marker in (
    '/api/topology/rf-origins',
    "db.list_rf_route_origins",
):
    if marker not in web:
        raise SystemExit(f"v1.14.10 web marker missing: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
for marker in (
    'id="rfRouteSourceList"',
    'list="rfRouteSourceList"',
    'id="rfRouteTargetList"',
):
    if marker not in html:
        raise SystemExit(f"v1.14.10 HTML marker missing: {marker}")

js = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "function refreshRfRouteOrigins(",
    "function renderRfRouteRecords(",
    "function focusRfRecordRoute(",
    "rfRouteExclusiveNodes",
    "ResizeObserver",
    "setTransientRouteFocusVisibility(false)",
):
    if marker not in js:
        raise SystemExit(f"v1.14.10 JS marker missing: {marker}")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    "--map-context-height",
    ".rf-route-records-group",
    ".rf-route-record",
    "overflow-y: visible;",
    "max-height: none;",
):
    if marker not in css:
        raise SystemExit(f"v1.14.10 CSS marker missing: {marker}")

tests = read("tests/test_v1410_release.py")
for marker in (
    "test_v1410_origin_autocomplete_uses_rf_graph_only",
    "test_v1410_longest_rf_record_prefers_complete_multihop_chain_and_excludes_internet",
    "test_v1410_rf_records_respect_statistics_period",
    "test_v1410_record_focus_is_exclusive_and_statistics_scroll_is_page_level",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.10 regression missing: {marker}")

print("v1.14.10 validation OK")
