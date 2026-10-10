from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.14.19"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, content: str) -> None:
    (ROOT / rel).write_text(content, encoding="utf-8")


if read("VERSION").strip() != VERSION:
    raise SystemExit(f"VERSION must be {VERSION}")
if f'__version__ = "{VERSION}"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit(f"package version must be {VERSION}")

overlay = read("pt2vhf_aprs/spacetime_topology.py")
for marker in (
    "ROUTE_TEMPORAL_WINDOW_MINUTES = 30.0",
    "EVENT_POSITION_MAX_AGE_HOURS = 12.0",
    "def _ensure_schema_and_backfill()",
    "def _temporal_events(",
    "def _route_payload(",
    "spatiotemporal_validated",
    "topology_spacetime_backfill",
):
    if marker not in overlay:
        raise SystemExit(f"v1.14.19 topology marker missing: {marker}")

package_init = read("pt2vhf_aprs/__init__.py")
if "_spacetime_topology.install()" not in package_init:
    raise SystemExit("v1.14.19 topology overlay is not installed")

tests = read("tests/test_v1419_release.py")
for marker in (
    "test_v1419_pt2ap_trip_cannot_bridge_itumbiara_and_south",
    "test_v1419_mobile_node_must_be_spatially_coherent_even_inside_time_window",
    "test_v1419_historical_edge_distance_uses_event_position_not_latest_station_position",
    "test_v1419_contemporary_route_is_accepted_and_reports_window",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.19 regression missing: {marker}")

# PyInstaller lê este arquivo durante o build. Mantemos o patch idempotente para
# que o artefato Windows sempre carregue a versão correta mesmo em checkout que
# ainda tenha metadata textual da versão anterior.
version_info_path = ROOT / "windows" / "version_info.txt"
version_info = version_info_path.read_text(encoding="utf-8")
version_info = version_info.replace("(1, 14, 18, 0)", "(1, 14, 19, 0)")
version_info = version_info.replace("'1.14.18'", "'1.14.19'")
version_info_path.write_text(version_info, encoding="utf-8")

print("v1.14.19 validation OK")
