from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.9":
    raise SystemExit("VERSION must be 1.14.9")
if '__version__ = "1.14.9"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.9")

database = read("pt2vhf_aprs/database.py")
for marker in (
    "def _rf_route_graph(",
    "def list_rf_route_candidates(",
    "def list_rf_routes(",
    'str(raw.get("kind") or "").lower() == "igate"',
    '"direct_distance_km"',
    '"route_evidence_at"',
):
    if marker not in database:
        raise SystemExit(f"v1.14.9 RF route backend marker missing: {marker}")

web = read("pt2vhf_aprs/web.py")
for marker in (
    '/api/topology/rf-candidates',
    '/api/topology/rf-routes',
    "db.list_rf_route_candidates",
    "db.list_rf_routes",
):
    if marker not in web:
        raise SystemExit(f"v1.14.9 route API marker missing: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
for marker in (
    'id="rfRouteSource"',
    'id="rfRouteTarget"',
    'id="rfRouteTargetList"',
    'id="rfRoutePanel"',
):
    if marker not in html:
        raise SystemExit(f"v1.14.9 map UI marker missing: {marker}")

js = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "function topologyEdgeDistanceKm(",
    "function refreshRfRouteCandidates(",
    "function applyRfRouteAnalysis(",
    "function focusRfRoute(",
    "routeAllowedPairs",
    "formatRfDistanceKm(topologyEdgeDistanceKm(edge))",
):
    if marker not in js:
        raise SystemExit(f"v1.14.9 map logic marker missing: {marker}")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (".rf-route-search", ".rf-route-panel", ".rf-route-card.selected"):
    if marker not in css:
        raise SystemExit(f"v1.14.9 map CSS marker missing: {marker}")

tests = read("tests/test_v149_release.py")
for marker in (
    "test_v149_candidates_only_include_complete_rf_reachability",
    "test_v149_routes_support_multiple_complete_paths_and_distances",
    "test_v149_internet_cannot_complete_an_rf_route",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.9 regression missing: {marker}")

print("v1.14.9 validation OK")
