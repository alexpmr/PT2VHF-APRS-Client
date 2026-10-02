from pathlib import Path

from pt2vhf_aprs import diagnostics as diag

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def metrics(*, app_cpu=0, system_cpu=0, app_memory=0, system_memory=0):
    return {
        "app_cpu_percent": app_cpu,
        "system_cpu_percent": system_cpu,
        "app_memory_percent": app_memory,
        "system_memory_percent": system_memory,
    }


def test_v184_short_peak_does_not_alert_and_sustained_cpu_does():
    state = {}
    assert diag.evaluate_resource_alerts(metrics(app_cpu=95), now=0, tracker_state=state) == []
    assert diag.evaluate_resource_alerts(metrics(app_cpu=95), now=20, tracker_state=state) == []
    alerts = diag.evaluate_resource_alerts(metrics(app_cpu=95), now=31, tracker_state=state)
    assert len(alerts) == 1
    assert alerts[0]["resource"] == "cpu"
    assert alerts[0]["scope"] == "app"
    assert alerts[0]["threshold"] == 90.0


def test_v184_cooldown_hysteresis_recovery_and_new_alert():
    state = {}
    diag.evaluate_resource_alerts(metrics(system_memory=96), now=0, tracker_state=state)
    first = diag.evaluate_resource_alerts(metrics(system_memory=96), now=31, tracker_state=state)
    assert len(first) == 1 and first[0]["scope"] == "system"
    assert diag.evaluate_resource_alerts(metrics(system_memory=96), now=300, tracker_state=state) == []
    assert len(diag.evaluate_resource_alerts(metrics(system_memory=96), now=632, tracker_state=state)) == 1
    assert diag.evaluate_resource_alerts(metrics(system_memory=86), now=640, tracker_state=state) == []
    assert diag.evaluate_resource_alerts(metrics(system_memory=84), now=650, tracker_state=state) == []
    assert diag.evaluate_resource_alerts(metrics(system_memory=96), now=660, tracker_state=state) == []
    assert len(diag.evaluate_resource_alerts(metrics(system_memory=96), now=691, tracker_state=state)) == 1


def test_v184_resource_monitoring_is_configurable_and_logged():
    database = read("pt2vhf_aprs/database.py")
    web = read("pt2vhf_aprs/web.py")
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    for key in (
        "resource_alert_enabled",
        "resource_cpu_critical_percent",
        "resource_memory_critical_percent",
        "resource_alert_sustain_seconds",
        "resource_alert_cooldown_minutes",
    ):
        assert key in database
        assert f'name="{key}"' in html
    assert '"resource_critical_alert"' in web
    assert '"critical_alerts"' in web
    assert "evaluate_resource_alerts(" in web
    assert "showResourceCriticalAlert(m)" in js
    assert 'id="resourceCriticalAlert"' in html
    assert "/api/diagnostics/log" in html


def test_v184_map_context_bar_is_left_aligned():
    css = read("pt2vhf_aprs/static/css/app.css")
    start = css.index(".map-context-controls {")
    end = css.index("}", start)
    block = css[start:end]
    assert "margin-left: 0;" in block
    assert "margin-right: auto;" in block
    assert "margin-left: auto;" not in block


def test_v184_system_and_app_metrics_are_distinct():
    diagnostics = read("pt2vhf_aprs/diagnostics.py")
    js = read("pt2vhf_aprs/static/js/app.js")
    for key in (
        "app_cpu_percent",
        "app_memory_percent",
        "system_cpu_percent",
        "system_memory_percent",
        "system_memory_available_mb",
    ):
        assert key in diagnostics
        assert key in js


def test_v184_version():
    version = read("VERSION").strip()
    parts = tuple(int(item) for item in version.split("."))
    assert parts >= (1, 8, 4)
    assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
