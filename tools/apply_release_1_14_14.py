from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.14":
    raise SystemExit("VERSION must be 1.14.14")
if '__version__ = "1.14.14"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.14")

js = read("pt2vhf_aprs/static/js/app.js")
for forbidden in (
    "RF confirmado",
    "confirmed RF",
    "rf_confidence_label",
    "rf_confidence_reason",
):
    if forbidden in js:
        raise SystemExit(f"v1.14.14 obsolete RF UI marker remains: {forbidden}")

for marker in (
    "RF observado",
    "Observed RF",
    "classification_source",
    "state.rfRouteExclusiveNodes = exclusiveNodes;",
    "setTransientRouteFocusVisibility(false);",
    "fitRfRouteBounds(routes);",
):
    if marker not in js:
        raise SystemExit(f"v1.14.14 required marker missing: {marker}")

database = read("pt2vhf_aprs/database.py")
for forbidden in (
    "RF_CONFIRMED_SHORT_KM",
    "RF_CONFIRMED_MEDIUM_KM",
    "RF_CONFIRMED_LONG_KM",
    'if not bool(edge.get("rf_confirmed"))',
):
    if forbidden in database:
        raise SystemExit(f"v1.14.14 obsolete RF exclusion remains: {forbidden}")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    "#tab-analysis .client-version-stats-content",
    "#tab-analysis .rf-route-record-list",
    "overflow-y: visible !important;",
    "max-height: none !important;",
):
    if marker not in css:
        raise SystemExit(f"v1.14.14 statistics marker missing: {marker}")

tests = read("tests/test_v1414_release.py")
for marker in (
    "test_v1414_route_ui_uses_observed_rf_semantics",
    "test_v1414_manual_search_keeps_exclusive_focus",
    "test_v1414_observed_rf_backend_remains_permissive",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.14 regression missing: {marker}")

print("v1.14.14 validation OK")
