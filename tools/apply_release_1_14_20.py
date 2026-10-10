from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.14.20"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != VERSION:
    raise SystemExit(f"VERSION must be {VERSION}")
if f'__version__ = "{VERSION}"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit(f"package version must be {VERSION}")

overlay = read("pt2vhf_aprs/spacetime_topology.py")
for marker in (
    "SHARED_NODE_COMPATIBILITY_KM = 25.0",
    "INFERRED_LONG_HOP_KM = 250.0",
    "def _compatible_events(",
    "def _reachability_class(",
    "historical_reachability",
    'payload["route_semantics"] = "historical_reachability"',
    "def _list_rf_route_candidates(",
):
    if marker not in overlay:
        raise SystemExit(f"v1.14.20 topology marker missing: {marker}")

app = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "TRACKLOG_MAX_GAP_MS = 30 * 60_000",
    "const temporalGap = elapsedMs > TRACKLOG_MAX_GAP_MS",
    "Alcançabilidade histórica",
    "geometryEdge = routeEvidence || edge",
):
    if marker not in app:
        raise SystemExit(f"v1.14.20 app marker missing: {marker}")

web = read("pt2vhf_aprs/web.py")
for marker in (
    "TRACKLOG_MAX_GAP_SECONDS = 30 * 60",
    "def _split_track_rows(",
    "segments = _split_track_rows(rows)",
):
    if marker not in web:
        raise SystemExit(f"v1.14.20 KML marker missing: {marker}")

tests = read("tests/test_v1420_release.py")
for marker in (
    "test_v1420_historical_links_can_form_reachability_route",
    "test_v1420_mobile_relay_uses_contact_coordinates_and_cannot_bridge_trip",
    "test_v1420_long_inferred_edge_is_not_a_direct_physical_hop",
    "test_v1420_kml_does_not_draw_across_tracker_shutdown_gap",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.20 regression missing: {marker}")

version_info_path = ROOT / "windows" / "version_info.txt"
version_info = version_info_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19"):
    version_info = version_info.replace(old, VERSION)
version_info = version_info.replace("(1, 14, 18, 0)", "(1, 14, 20, 0)")
version_info = version_info.replace("(1, 14, 19, 0)", "(1, 14, 20, 0)")
version_info_path.write_text(version_info, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19"):
    readme = readme.replace(old, VERSION)
readme_path.write_text(readme, encoding="utf-8")

print("v1.14.20 validation OK")
