from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.14.22"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != VERSION:
    raise SystemExit(f"VERSION must be {VERSION}")
if f'__version__ = "{VERSION}"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit(f"package version must be {VERSION}")

overlay = read("pt2vhf_aprs/spacetime_topology.py")
for marker in (
    "def _legacy_position_at_event_conn(",
    "legacy_fallback",
    "ranking_scope",
    "multihop",
    'seen_modes: set[tuple[str, str]]',
):
    if marker not in overlay:
        raise SystemExit(f"v1.14.22 topology marker missing: {marker}")

web = read("pt2vhf_aprs/web.py")
for marker in (
    "def _topology_diagnostic_payload(",
    'schema_version": "pt2vhf-topology-diagnostic-1"',
    '@app.get("/api/export/topology-json")',
    "topology_json_export_failed",
):
    if marker not in web:
        raise SystemExit(f"v1.14.22 JSON export marker missing: {marker}")

app = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "async function exportTopologyJson()",
    "/api/export/topology-json",
    "filtros de estações/objetos controlam somente os",
    "saveJsonContent",
):
    if marker not in app:
        raise SystemExit(f"v1.14.22 app marker missing: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
if 'id="topologyJsonExportButton"' not in html:
    raise SystemExit("v1.14.22 Exportar JSON button missing")

windows = read("windows_app.py")
for marker in (
    "SetCurrentProcessExplicitAppUserModelID",
    'suffix == ".json"',
):
    if marker not in windows:
        raise SystemExit(f"v1.14.22 Windows marker missing: {marker}")

if not (ROOT / "windows" / "aprs_taskbar_icon.png").exists():
    raise SystemExit("v1.14.22 APRS taskbar icon source missing")
if 'SOURCE = ROOT / "windows" / "aprs_taskbar_icon.png"' not in read("windows/make_icon.py"):
    raise SystemExit("v1.14.22 icon generator does not use APRS artwork")

tests = read("tests/test_v1422_release.py")
for marker in (
    "test_v1422_rf_records_keep_multihop_reachability",
    "test_v1422_legacy_topology_edge_survives_without_event_rows",
    "test_v1422_json_diagnostic_contains_topology_without_secrets",
    "test_v1422_marker_filters_do_not_hide_links",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.22 regression missing: {marker}")

version_info_path = ROOT / "windows" / "version_info.txt"
version_info = version_info_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20", "1.14.21"):
    version_info = version_info.replace(old, VERSION)
for old_tuple in ("(1, 14, 18, 0)", "(1, 14, 19, 0)", "(1, 14, 20, 0)", "(1, 14, 21, 0)"):
    version_info = version_info.replace(old_tuple, "(1, 14, 22, 0)")
version_info_path.write_text(version_info, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20", "1.14.21"):
    readme = readme.replace(old, VERSION)
readme_path.write_text(readme, encoding="utf-8")

backlog = read("BACKLOG.md")
if "## Novo —" in "\n".join(backlog.splitlines()[:180]):
    raise SystemExit("active v1.14.22 backlog still marked as Novo near top")

print("v1.14.22 validation OK")
