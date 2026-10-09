from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.13":
    raise SystemExit("VERSION must be 1.14.13")
if '__version__ = "1.14.13"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.13")

database = read("pt2vhf_aprs/database.py")
for forbidden in (
    "RF_CONFIRMED_SHORT_KM",
    "RF_CONFIRMED_MEDIUM_KM",
    "RF_CONFIRMED_LONG_KM",
    'if not bool(edge.get("rf_confirmed"))',
):
    if forbidden in database:
        raise SystemExit(f"v1.14.13 obsolete RF exclusion remains: {forbidden}")

js = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "const exclusiveNodes = new Set();",
    "state.rfRouteExclusiveNodes = exclusiveNodes;",
    "setTransientRouteFocusVisibility(false);",
    "fitRfRouteBounds(routes);",
):
    if marker not in js:
        raise SystemExit(f"v1.14.13 manual route focus marker missing: {marker}")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    "v1.14.13 - Estatísticas em fluxo contínuo",
    "overflow-y: visible !important;",
    "max-height: none !important;",
):
    if marker not in css:
        raise SystemExit(f"v1.14.13 statistics marker missing: {marker}")

tests = read("tests/test_v1413_release.py")
for marker in (
    "test_v1413_long_observed_rf_edge_remains_in_graph",
    "test_v1413_aprsis_edge_does_not_complete_rf_graph",
    "test_v1413_manual_route_search_uses_exclusive_ranking_focus",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.13 regression missing: {marker}")

print("v1.14.13 validation OK")
