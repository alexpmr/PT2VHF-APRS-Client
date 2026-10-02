from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.4":
    raise SystemExit(f"v1.8.4 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.4"'],
    "pt2vhf_aprs/diagnostics.py": ["def evaluate_resource_alerts(", '"app_cpu_percent"', '"system_cpu_percent"', '"system_memory_percent"', '"system_memory_available_mb"'],
    "pt2vhf_aprs/database.py": ['"resource_alert_enabled": 1', '"resource_cpu_critical_percent": 90', '"resource_memory_critical_percent": 90', '"resource_alert_sustain_seconds": 30', '"resource_alert_cooldown_minutes": 10'],
    "pt2vhf_aprs/web.py": ['"resource_critical_alert"', '"critical_alerts"', "diag.evaluate_resource_alerts("],
    "pt2vhf_aprs/templates/index.html": ['id="resourceCriticalAlert"', 'name="resource_alert_enabled"', 'name="resource_cpu_critical_percent"', 'name="resource_memory_critical_percent"', 'name="resource_alert_sustain_seconds"', 'name="resource_alert_cooldown_minutes"'],
    "pt2vhf_aprs/static/js/app.js": ["function showResourceCriticalAlert(", "showResourceCriticalAlert(m)", "system_cpu_percent", "system_memory_percent"],
    "pt2vhf_aprs/static/css/app.css": [".resource-critical-alert", ".map-context-controls", "margin-left: 0;", "margin-right: auto;"],
    "tests/test_v184_resources_mapbar.py": ["test_v184_short_peak_does_not_alert_and_sustained_cpu_does", "test_v184_cooldown_hysteresis_recovery_and_new_alert", "test_v184_map_context_bar_is_left_aligned"],
    "pt2vhf_aprs/version_notes.py": ['"1.8.4"'],
    "CHANGELOG.md": ["## 1.8.4 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.4", "## Novidades da v1.8.4"],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.4 validation failed: {needle!r} missing from {rel}")

from pt2vhf_aprs import diagnostics as diag
state = {}
base = {"app_cpu_percent": 95, "system_cpu_percent": 20, "app_memory_percent": 10, "system_memory_percent": 40}
if diag.evaluate_resource_alerts(base, now=0, tracker_state=state):
    raise SystemExit("v1.8.4 validation failed: short CPU peak alerted immediately")
if diag.evaluate_resource_alerts(base, now=20, tracker_state=state):
    raise SystemExit("v1.8.4 validation failed: short CPU peak alerted before sustain time")
alerts = diag.evaluate_resource_alerts(base, now=31, tracker_state=state)
if len(alerts) != 1 or alerts[0].get("scope") != "app":
    raise SystemExit("v1.8.4 validation failed: sustained app CPU alert missing")

css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
start = css.index(".map-context-controls {")
end = css.index("}", start)
block = css[start:end]
if "margin-left: auto;" in block or "margin-left: 0;" not in block:
    raise SystemExit("v1.8.4 validation failed: Map context bar is not left aligned")

print("v1.8.4 resource health / Map alignment production validation OK")
