from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.17":
    raise SystemExit("VERSION must be 1.14.17")
if '__version__ = "1.14.17"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.17")

database = read("pt2vhf_aprs/database.py")
for marker in (
    "RF_INFERRED_REFINEMENT_MIN_KM = 250.0",
    "def _rf_refine_inferred_edge(",
    "def _rf_refine_route_nodes(",
    '"reconstructed_intermediate_nodes"',
    '"unresolved_inferred_edges"',
    "intermediários não identificados",
):
    if marker not in database:
        raise SystemExit(f"v1.14.17 RF refinement marker missing: {marker}")

app_js = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "function showProcessing(",
    "window.pt2vhfWithProcessing = withProcessing;",
    "Intermediários reconstruídos/prováveis",
    "Intermediários não identificados",
    "const processingToken = showProcessing(",
):
    if marker not in app_js:
        raise SystemExit(f"v1.14.17 UI marker missing: {marker}")

v190 = read("pt2vhf_aprs/static/js/v190.js")
for marker in (
    'id="v190BackupFull"',
    "async function createFullBackup()",
    "save_local_download('/api/v190/backup/full', suggested)",
    "triggerBlobDownload(blob, filename)",
    "withProcessing(",
):
    if marker not in v190:
        raise SystemExit(f"v1.14.17 backup marker missing: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
if 'id="globalProcessingOverlay"' not in html:
    raise SystemExit("v1.14.17 processing overlay markup missing")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    ".global-processing-overlay",
    "@keyframes pt2vhf-processing-clock",
    ".rf-route-refinement.warning",
    "v1.14.17 - Configuração usa somente a rolagem principal da aba",
    "#tab-config #configForm.config-grid",
    "#tab-config #configForm .config-card :is(div, section, article, fieldset, ul, ol)",
    "overflow: visible !important;",
):
    if marker not in css:
        raise SystemExit(f"v1.14.17 CSS marker missing: {marker}")

for launcher in ("windows_app.py", "linux_app.py", "macos_app.py"):
    content = read(launcher)
    for marker in (
        "def save_local_download(",
        'allowed = {"/api/v190/backup/full"}',
        "with urlopen(local_url, timeout=180)",
    ):
        if marker not in content:
            raise SystemExit(f"v1.14.17 native backup marker missing in {launcher}: {marker}")

tests = read("tests/test_v1417_release.py")
for marker in (
    "test_v1417_long_inferred_edge_is_reconstructed_when_supported",
    "test_v1417_long_direct_rf_edge_is_never_broken_only_by_distance",
    "test_v1417_full_backup_button_uses_explicit_download_flow",
    "test_v1417_processing_overlay_is_reusable_and_used_by_long_operations",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.17 regression missing: {marker}")

print("v1.14.17 validation OK")
