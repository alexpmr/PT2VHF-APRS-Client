from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.16":
    raise SystemExit("VERSION must be 1.14.16")
if '__version__ = "1.14.16"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.16")

js = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "trackFollowCallsign",
    "function followTracklog(",
    "function centerFollowedTrack(",
    "state.map.on('dragstart'",
    "state.map.on('zoomend'",
    "function rfRouteNodeCoordinates()",
    "rf-route-node-temp-wrap",
    "function rfRouteFitPadding()",
    "paddingTopLeft",
    "paddingBottomRight",
):
    if marker not in js:
        raise SystemExit(f"v1.14.16 JavaScript marker missing: {marker}")

fit_start = js.index("function fitRfRouteBounds(")
fit_end = js.index("async function focusRfRecordRoute", fit_start)
fit_body = js[fit_start:fit_end]
if "maxZoom: 13" in fit_body:
    raise SystemExit("v1.14.16 must not cap ranking route fit at zoom 13")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    ".rf-route-node-temp",
    ".rf-route-node-temp.has-normal",
    ".rf-route-node-temp.has-normal .rf-route-node-dot",
):
    if marker not in css:
        raise SystemExit(f"v1.14.16 CSS marker missing: {marker}")

tests = read("tests/test_v1416_release.py")
for marker in (
    "test_v1416_tracklog_follow_mode_preserves_zoom",
    "test_v1416_ranking_route_fit_uses_maximum_possible_zoom",
    "test_v1416_all_route_nodes_receive_visible_overlay",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.16 regression missing: {marker}")

print("v1.14.16 validation OK")
