from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.6.18":
    raise SystemExit(f"v1.6.18 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/database.py": [
        "CREATE TABLE IF NOT EXISTS aprs_queries",
        '"respond_to_queries": 0',
        "def aprs_query_detail(",
        "def resolve_ping_ack(",
    ],
    "pt2vhf_aprs/aprs_service.py": [
        "def send_query(",
        "def send_ping_ack(",
        "def _handle_directed_query(",
        "def parse_trace_nodes(",
        "def build_query_payload(",
    ],
    "pt2vhf_aprs/web.py": [
        '@app.post("/api/queries/send")',
        '@app.get("/api/queries/<int:query_id>")',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "station-query-button",
        "function drawQueryTrace(",
        "function pollQueryResult(",
        "queryTraceLayers: new Set()",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'name="respond_to_queries"',
        "Queries APRS",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.18 validation failed: {needle!r} missing from {rel}")

print("v1.6.18 APRS query diagnostics validation OK")
