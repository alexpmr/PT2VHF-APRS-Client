from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

def version_tuple(value: str) -> tuple[int, ...]:
    parts = []
    for piece in str(value or "").strip().lstrip("vV").split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            break
    return tuple(parts or [0])

if version_tuple(version) < (1, 6, 17):
    raise SystemExit(f"v1.6.17 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/database.py": [
        "def process_received_packet(",
        "_topology_query_lock = threading.Lock()",
        "JOIN stations s1 ON s1.callsign = e.source",
        "JOIN stations s2 ON s2.callsign = e.target",
        "TOPOLOGY_QUERY_MAX_SECONDS = 2.5",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "mapLoadBusy: false",
        "topologyLoadBusy: false",
        "async function refreshSystemMetrics()",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="systemResourceMeter"',
    ],
    "pt2vhf_aprs/diagnostics.py": [
        "def system_metrics()",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.17 validation failed: {needle!r} missing from {rel}")

print("v1.6.17 full release validation OK")
