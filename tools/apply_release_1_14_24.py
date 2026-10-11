from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "1.14.24"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != VERSION:
    raise SystemExit(f"VERSION must be {VERSION}")
if f'__version__ = "{VERSION}"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit(f"package version must be {VERSION}")

overlay = read("pt2vhf_aprs/spacetime_topology.py")
for marker in (
    "RF_RECORDS_CACHE_SECONDS = 90.0",
    "RF_RECORD_EVENT_REPRESENTATIVES = 24",
    "RF_RECORD_MAX_EXPANSIONS_PER_SOURCE = 1400",
    "def _route_records_uncached(",
    "selected_events_override",
    "def _record_event_representatives(",
    "def _record_progress(",
    "_rf_records_cache",
    "_rf_records_builds",
    "rf_route_records_build",
):
    if marker not in overlay:
        raise SystemExit(f"v1.14.24 RF records marker missing: {marker}")

web = read("pt2vhf_aprs/web.py")
for marker in (
    "RF_RECORD_JOB_TTL_SECONDS",
    "def _run_rf_record_job(",
    "def _start_rf_record_job(",
    '@app.post("/api/topology/rf-records/jobs")',
    '@app.get("/api/topology/rf-records/jobs/<job_id>")',
    '@app.delete("/api/topology/rf-records/jobs/<job_id>")',
    "rf_route_records_job_failed",
):
    if marker not in web:
        raise SystemExit(f"v1.14.24 RF job marker missing: {marker}")

app = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "rfRouteRecordsLastGood: new Map()",
    "function renderRfRouteRecordsProgress(",
    "Math.max(lastPercent, Number(job.percent || 0))",
    "/api/topology/rf-records/jobs",
    "data-rf-record-retry",
    "updateProcessing(token, title = '', message = '', progress = undefined)",
):
    if marker not in app:
        raise SystemExit(f"v1.14.24 frontend progress marker missing: {marker}")

html = read("pt2vhf_aprs/templates/index.html")
for marker in (
    'id="globalProcessingProgress"',
    'id="globalProcessingProgressBar"',
    'id="globalProcessingProgressText"',
):
    if marker not in html:
        raise SystemExit(f"v1.14.24 processing overlay marker missing: {marker}")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    ".processing-progress",
    ".rf-record-progress",
    ".rf-record-progress-bar",
    ".rf-route-records-stale-note",
):
    if marker not in css:
        raise SystemExit(f"v1.14.24 progress CSS marker missing: {marker}")

tests = read("tests/test_v1424_release.py")
for marker in (
    "test_v1424_incremental_ranking_keeps_multihop_without_rewalking_full_paths",
    "test_v1424_cache_reports_immediate_completion",
    "test_v1424_web_job_progress_is_monotonic_and_finishes",
    "test_v1424_frontend_preserves_last_valid_records_and_uses_real_progress",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.24 regression missing: {marker}")

backlog = read("BACKLOG.md")
for heading in (
    "## Implementado na v1.14.24 — Estatísticas: indicador de processamento",
    "## Implementado na v1.14.24 — Estatísticas: ranking de Recordes RF",
):
    if heading not in backlog:
        raise SystemExit(f"implemented backlog marker missing: {heading}")

version_info_path = ROOT / "windows" / "version_info.txt"
version_info = version_info_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20", "1.14.21", "1.14.22", "1.14.23"):
    version_info = version_info.replace(old, VERSION)
for old_tuple in (
    "(1, 14, 18, 0)", "(1, 14, 19, 0)", "(1, 14, 20, 0)",
    "(1, 14, 21, 0)", "(1, 14, 22, 0)", "(1, 14, 23, 0)",
):
    version_info = version_info.replace(old_tuple, "(1, 14, 24, 0)")
version_info_path.write_text(version_info, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
for old in ("1.14.18", "1.14.19", "1.14.20", "1.14.21", "1.14.22", "1.14.23"):
    readme = readme.replace(old, VERSION)
readme_path.write_text(readme, encoding="utf-8")

print("v1.14.24 validation OK")
