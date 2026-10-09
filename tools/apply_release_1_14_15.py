from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.15":
    raise SystemExit("VERSION must be 1.14.15")
if '__version__ = "1.14.15"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.15")

database = read("pt2vhf_aprs/database.py")
for forbidden in (
    "len(found) >= route_limit * 4",
    "RF_CONFIRMED_SHORT_KM",
    "RF_CONFIRMED_MEDIUM_KM",
    "RF_CONFIRMED_LONG_KM",
):
    if forbidden in database:
        raise SystemExit(f"v1.14.15 obsolete RF route logic remains: {forbidden}")

for marker in (
    "def _rf_route_eligible_edges(",
    "def _rf_k_best_routes(",
    "eligible_edges",
    "search_truncated",
    "RF direto observado",
    "RF inferido do path",
):
    if marker not in database:
        raise SystemExit(f"v1.14.15 backend marker missing: {marker}")

js = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "analysis.eligible_edges || []",
    "payload.eligible_nodes || []",
    "fitRfRouteBounds(routes, payload.eligible_edges || [])",
    "&max_routes=12&max_hops=12",
    "enlaces RF elegíveis",
    "routeEvidence?.evidence_level === 'inferred'",
    "inferredRouteEdge ? '5 5'",
):
    if marker not in js:
        raise SystemExit(f"v1.14.15 frontend marker missing: {marker}")

web = read("pt2vhf_aprs/web.py")
if 'request.args.get("max_hops", 12)' not in web:
    raise SystemExit("v1.14.15 web default max_hops must be 12")

tests = read("tests/test_v1415_release.py")
for marker in (
    "test_v1415_eligible_corridor_keeps_all_rf_links_that_can_join_route",
    "test_v1415_route_search_prefers_direct_evidence_without_distance_veto",
    "test_v1415_list_routes_returns_full_eligible_corridor",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.15 regression missing: {marker}")

print("v1.14.15 validation OK")
