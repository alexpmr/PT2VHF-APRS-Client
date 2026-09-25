from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "pt2vhf_aprs/static/js/app.js": [
        "mapLoadBusy: false",
        "if (state.mapLoadBusy) return;",
        "if (!state.markers.has(call) || !stationIsVisible(call)) return;",
        "events.slice(-20)",
        "new Set(events.map(event => normalizedCall(event.source))",
        "async function refreshSystemMetrics()",
        "schedulePolling(refreshSystemMetrics, 2000);",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="systemResourceMeter"',
        'id="headerCpuUsage"',
        'id="headerMemoryUsage"',
    ],
    "pt2vhf_aprs/diagnostics.py": [
        "def system_metrics()",
        "root.children(recursive=True)",
    ],
    "pt2vhf_aprs/web.py": [
        '/api/system-metrics',
    ],
    "requirements-windows.txt": [
        "psutil",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.15 validation failed: {needle!r} missing from {rel}")

app_js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
station_block = app_js.split("function stationActivity", 1)[1].split("function trafficSegmentVisible", 1)[0]
if "loadMapData(" in station_block:
    raise SystemExit("v1.6.15 validation failed: stationActivity still triggers full map refresh")

print("v1.6.15 map fan-out fix and system gauges validation OK")
