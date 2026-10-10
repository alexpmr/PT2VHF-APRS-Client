from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.14.21"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != VERSION:
    raise SystemExit(f"VERSION must be {VERSION}")
if f'__version__ = "{VERSION}"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit(f"package version must be {VERSION}")

overlay = read("pt2vhf_aprs/spacetime_topology.py")
for marker in (
    "GRAPH_CACHE_SECONDS = 20.0",
    "_graph_builds:",
    "rf_route_graph_singleflight_wait",
    "def _build_route_graph_uncached(",
    "def _route_graph(hours: float = 0):",
):
    if marker not in overlay:
        raise SystemExit(f"v1.14.21 topology performance marker missing: {marker}")

database = read("pt2vhf_aprs/database.py")
for marker in (
    "def topology_stats(hours: int = 0, *, include_routes: bool = True)",
    "rf_route_records_deferred",
    "topology_stats_component",
    "topology_stats_total",
):
    if marker not in database:
        raise SystemExit(f"v1.14.21 database marker missing: {marker}")

web = read("pt2vhf_aprs/web.py")
for marker in (
    "TOPOLOGY_STATS_CACHE_SECONDS = 30.0",
    "def _topology_stats_payload(",
    'db.topology_stats(key, include_routes=False)',
    '@app.get("/api/topology/rf-records")',
    "topology_stats_singleflight_wait",
):
    if marker not in web:
        raise SystemExit(f"v1.14.21 web marker missing: {marker}")

app = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "PROCESSING_SHOW_DELAY_MS = 320",
    "visible: false",
    "topologyStatsLastGood",
    "refreshRfRouteRecordsDeferred",
    "rfRouteOriginsController",
    "rfRouteOriginCache: new Map()",
    "Calculando estatísticas do histórico",
    "mantendo os últimos valores válidos",
):
    if marker not in app:
        raise SystemExit(f"v1.14.21 app marker missing: {marker}")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    "v1.14.21 - Estatísticas em fluxo único",
    "#tab-analysis .client-version-stats-content",
    "overflow: visible !important;",
    ".global-processing-overlay.nonblocking",
):
    if marker not in css:
        raise SystemExit(f"v1.14.21 CSS marker missing: {marker}")

tests = read("tests/test_v1421_release.py")
for marker in (
    "test_v1421_rf_graph_singleflight_builds_once",
    "test_v1421_topology_stats_cache_reuses_full_history_result",
    "test_v1421_statistics_keep_single_vertical_scroll",
    "test_v1421_processing_overlay_is_delayed_and_concurrency_safe",
    "test_v1421_rf_origin_autocomplete_cancels_stale_requests",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.21 regression missing: {marker}")

version_info_path = ROOT / "windows" / "version_info.txt"
version_info = version_info_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20"):
    version_info = version_info.replace(old, VERSION)
for old_tuple in ("(1, 14, 18, 0)", "(1, 14, 19, 0)", "(1, 14, 20, 0)"):
    version_info = version_info.replace(old_tuple, "(1, 14, 21, 0)")
version_info_path.write_text(version_info, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20"):
    readme = readme.replace(old, VERSION)
readme_path.write_text(readme, encoding="utf-8")

backlog = read("BACKLOG.md")
if "## Novo —" in "\n".join(backlog.splitlines()[:160]):
    raise SystemExit("active v1.14.21 software backlog still marked as Novo near top")

print("v1.14.21 validation OK")
