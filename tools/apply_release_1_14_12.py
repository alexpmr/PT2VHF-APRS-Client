from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.12":
    raise SystemExit("VERSION must be 1.14.12")
if '__version__ = "1.14.12"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.12")

database = read("pt2vhf_aprs/database.py")
for marker in (
    "def _rf_edge_confidence(",
    "RF_CONFIRMED_EXCEPTIONAL_OBS",
    '"rf_confidence"',
    '"rf_confirmed"',
    'if not bool(edge.get("rf_confirmed"))',
):
    if marker not in database:
        raise SystemExit(f"v1.14.12 RF confidence marker missing: {marker}")

js = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "function bindRfRoutePanelDrag(",
    "function clampRfRoutePanelPosition(",
    "setPointerCapture",
    "rf_confidence_label",
    "RF confirmado",
):
    if marker not in js:
        raise SystemExit(f"v1.14.12 JS marker missing: {marker}")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    "v1.14.12 - rota RF arrastável",
    ".rf-route-panel.dragging",
    ".client-version-stats-content",
    "overflow-y: visible !important;",
    "max-height: none !important;",
):
    if marker not in css:
        raise SystemExit(f"v1.14.12 CSS marker missing: {marker}")

tests = read("tests/test_v1412_release.py")
for marker in (
    "test_v1412_rf_confidence_rejects_implausible_single_observation_long_hop",
    "test_v1412_exceptional_long_hop_requires_strong_direct_evidence",
    "test_v1412_route_graph_uses_only_confirmed_rf_edges",
    "test_v1412_statistics_cards_do_not_have_vertical_internal_scroll",
    "test_v1412_draggable_route_panel_is_bounded_and_resets_for_new_analysis",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.12 regression missing: {marker}")

print("v1.14.12 validation OK")
