from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v141_top_notification_bell_removed_but_center_remains_available():
    js = read("pt2vhf_aprs/static/js/v111.js")
    assert "v111Bell" not in js
    assert "🔔" not in js
    assert "v111NotifyOpen" in js
    assert "Centro de notificações" in js
    assert "/api/v111/notifications" in js


def test_v141_new_station_alert_uses_persisted_setting_as_source_of_truth():
    js = read("pt2vhf_aprs/static/js/v190.js")
    assert "window.__pt2vhfV190AlertSettingsDirty" in js
    assert "const settings=window.__pt2vhfV190AlertSettingsDirty" in js
    assert ": {...serverSettings};" in js
    assert "if(settings.station_appeared)" in js
    assert "void saveAlertSettings(false)" in js
