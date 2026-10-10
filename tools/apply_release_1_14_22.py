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
    "Ranking de alcançabilidade RF, incluindo rotas multi-hop históricas",
    "legacy_current_fallback",
    'candidate["multi_hop"]',
    "RF histórico legado",
):
    if marker not in overlay:
        raise SystemExit(f"v1.14.22 topology marker missing: {marker}")

web = read("pt2vhf_aprs/web.py")
for marker in (
    "DIAGNOSTIC_EXPORT_MAX_EVENTS = 50000",
    "def _topology_diagnostic_payload(",
    '"schema_version": "pt2vhf-topology-diagnostic-1"',
    '@app.get("/api/export/topology-json")',
    '"config_safe": safe_config',
):
    if marker not in web:
        raise SystemExit(f"v1.14.22 JSON export marker missing: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
for marker in (
    'id="jsonExportButton"',
    'id="jsonExportModal"',
    'id="jsonExportMode"',
    "Exportar JSON",
):
    if marker not in html:
        raise SystemExit(f"v1.14.22 HTML marker missing: {marker}")

app = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "async function exportTopologyJson()",
    "/api/export/topology-json?",
    "Gerando diagnóstico JSON",
    "saveJsonContent",
):
    if marker not in app:
        raise SystemExit(f"v1.14.22 app marker missing: {marker}")

icon_path = ROOT / "pt2vhf_aprs" / "static" / "img" / "aprs_taskbar_icon.png"
if not icon_path.exists() or not icon_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
    raise SystemExit("v1.14.22 APRS taskbar icon asset missing or invalid")

make_icon = read("windows/make_icon.py")
if "aprs_taskbar_icon.png" not in make_icon:
    raise SystemExit("v1.14.22 Windows icon generator is not using APRS artwork")

windows_app = read("windows_app.py")
for marker in (
    'APP_USER_MODEL_ID = "PT2VHF.APRS.Client"',
    "SetCurrentProcessExplicitAppUserModelID",
):
    if marker not in windows_app:
        raise SystemExit(f"v1.14.22 taskbar marker missing: {marker}")

tests = read("tests/test_v1422_release.py")
for marker in (
    "test_v1422_record_ranking_explores_multi_hop_paths",
    "test_v1422_icon_asset_and_windows_taskbar_identity",
    "test_v1422_json_export_does_not_export_secrets_by_design",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.22 regression missing: {marker}")

version_info_path = ROOT / "windows" / "version_info.txt"
version_info = version_info_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20", "1.14.21"):
    version_info = version_info.replace(old, VERSION)
for old_tuple in (
    "(1, 14, 18, 0)", "(1, 14, 19, 0)",
    "(1, 14, 20, 0)", "(1, 14, 21, 0)",
):
    version_info = version_info.replace(old_tuple, "(1, 14, 22, 0)")
version_info_path.write_text(version_info, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20", "1.14.21"):
    readme = readme.replace(old, VERSION)
readme_path.write_text(readme, encoding="utf-8")

print("v1.14.22 validation OK")
