from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs import scheduled_messages as scheduler


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1817_version_metadata_history_is_preserved():
    notes = read("pt2vhf_aprs/version_notes.py")
    changelog = read("CHANGELOG.md")
    assert '"1.8.17"' in notes
    assert "## 1.8.17" in changelog


def test_zoom_step_is_persistent_config_and_runtime_adjustable():
    database = read("pt2vhf_aprs/database.py")
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")

    assert '"map_zoom_step": 0.10' in database
    assert "map_zoom_step REAL NOT NULL DEFAULT 0.10" in database
    assert "ALTER TABLE config ADD COLUMN map_zoom_step REAL NOT NULL DEFAULT 0.10" in database
    assert '{0.05, 0.10, 0.25, 0.50, 1.00}' in database

    assert 'name="map_zoom_step" id="mapZoomStep"' in html
    for value in ("0.05", "0.10", "0.25", "0.50", "1.00"):
        assert f'value="{value}"' in html
    assert 'id="resetMapZoomButton"' in html

    assert "function normalizeMapZoomStep(value)" in js
    assert "function mapZoomOptions(value)" in js
    assert "function applyMapZoomPreferences(value)" in js
    assert "zoomSnap: zoomOptions.step" in js
    assert "zoomDelta: zoomOptions.step" in js
    assert "wheelPxPerZoomLevel: zoomOptions.wheelPxPerZoomLevel" in js
    assert "$('#mapZoomStep')?.addEventListener('change'" in js


def test_zoom_step_validation_uses_safe_values():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "zoom.db"
            db.init_db()
            saved = db.save_config({"map_zoom_step": 0.25})
            assert float(saved["map_zoom_step"]) == pytest.approx(0.25)
            with pytest.raises(ValueError):
                db.save_config({"map_zoom_step": 0.33})
    finally:
        db.DB_PATH = original


def test_scheduler_schema_and_api_surface_are_present():
    database = read("pt2vhf_aprs/database.py")
    web = read("pt2vhf_aprs/web.py")
    html = read("pt2vhf_aprs/templates/index.html")

    for snippet in (
        "CREATE TABLE IF NOT EXISTS recipient_groups",
        "CREATE TABLE IF NOT EXISTS scheduled_messages",
        "def list_scheduled_messages()",
        "def save_scheduled_message(",
        "def claim_due_scheduled_message(",
        "def complete_scheduled_message(",
    ):
        assert snippet in database

    for endpoint in (
        '/api/messages/scheduled',
        '/api/messages/scheduled/<int:schedule_id>',
        '/api/messages/scheduled/<int:schedule_id>/toggle',
        '/api/messages/scheduled/<int:schedule_id>/run-now',
        '/api/messages/recipient-groups',
    ):
        assert endpoint in web

    for ident in (
        "scheduledMessagesButton",
        "scheduledMessagesPanel",
        "scheduledMessageForm",
        "scheduledScheduleType",
        "scheduledTargetType",
        "scheduledRecipientGroup",
        "scheduledTargets",
        "scheduledRetryPolicy",
        "scheduledMessagesTable",
        "recipientGroupSelect",
        "recipientGroupCallsigns",
    ):
        assert f'id="{ident}"' in html


def test_recipient_group_and_schedule_roundtrip_in_sqlite():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "scheduler.db"
            db.init_db()

            group = db.save_recipient_group({
                "name": "APRS Thursday",
                "callsigns": ["PY2AAA-9", "PU2BBB-7", "PY2AAA-9"],
            })
            assert group["name"] == "APRS Thursday"
            assert group["callsigns"] == ["PY2AAA-9", "PU2BBB-7"]

            run_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(timespec="seconds")
            payload = scheduler.prepare_schedule_payload({
                "name": "Teste único",
                "enabled": True,
                "schedule_type": "once",
                "run_at_utc": run_at,
                "target_type": "list",
                "targets": ["PT2VHF-1"],
                "recipient_group_id": group["id"],
                "message_type": "message",
                "message": "Teste 73",
                "route": "auto",
                "path": "",
                "interval_seconds": 3,
                "retry_policy": "skip",
                "retry_minutes": 10,
                "continue_on_error": True,
            })
            saved = db.save_scheduled_message(payload)
            assert saved["enabled"] is True
            assert saved["target_type"] == "list"
            assert saved["targets"] == ["PT2VHF-1"]
            assert saved["recipient_group_id"] == group["id"]
            assert saved["next_run_at"]

            rows = db.list_scheduled_messages()
            assert len(rows) == 1
            assert rows[0]["name"] == "Teste único"

            assert db.set_scheduled_enabled(saved["id"], False, None) == 1
            disabled = db.get_scheduled_message(saved["id"])
            assert disabled["enabled"] is False
            assert disabled["next_run_at"] is None

            assert db.delete_scheduled_message(saved["id"]) == 1
            assert db.delete_recipient_group(group["id"]) == 1
    finally:
        db.DB_PATH = original


def test_weekly_schedule_calculates_future_occurrence():
    now = datetime.now(timezone.utc)
    local_now = now.astimezone()
    payload = scheduler.prepare_schedule_payload({
        "enabled": True,
        "schedule_type": "weekly",
        "weekday": local_now.weekday(),
        "time_local": (local_now + timedelta(minutes=2)).strftime("%H:%M"),
        "target_type": "station",
        "target": "PT2VHF",
        "message_type": "message",
        "message": "APRS Thursday",
        "route": "auto",
    })
    next_run = datetime.fromisoformat(payload["next_run_at"])
    assert next_run.tzinfo is not None
    assert next_run > now
    assert next_run <= now + timedelta(days=8)


def test_scheduler_supports_station_list_bulletin_and_group_targets():
    scheduler_py = read("pt2vhf_aprs/scheduled_messages.py")
    html = read("pt2vhf_aprs/templates/index.html")
    for value in ("station", "list", "bulletin", "group"):
        assert f'value="{value}"' in html
    assert 'target_type in {"station", "list"}' in scheduler_py
    assert 'if target_type == "group"' in scheduler_py
    assert "aprs_service.send_bulletin" in scheduler_py
    assert "interval_seconds" in scheduler_py
    assert "continue_on_error" in scheduler_py
    assert '"retry_policy"' in read("pt2vhf_aprs/database.py")


def test_tnc_connected_without_valid_kiss_is_warning_not_success():
    js = read("pt2vhf_aprs/static/js/tnc.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "function statusClass(connected, paused, rxState = 'waiting')" in js
    assert "return rxState === 'active' ? 'status connected' : 'status warning';" in js
    assert "Serial conectada — sem KISS" in js
    assert "Serial conectada — aguardando dados" in js
    assert "Serial operacional — RX KISS ativo" in js
    assert "text.textContent = 'TNC'" in js
    assert "connected ? 'connected' : 'disconnected'" in js
    assert ".status.warning" in css


def test_group_schedule_cannot_use_announcement_letter():
    database = read("pt2vhf_aprs/database.py")
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "target_type == \"group\"" in database or "target_type == 'group'" in database
    assert "Boletim de grupo" in read("pt2vhf_aprs/templates/index.html")
    assert "targetType === 'group'" in js
    assert "$('#scheduledBulletinId').value = '0';" in js


def test_list_retry_contains_only_failed_destinations(monkeypatch):
    service = scheduler.ScheduledMessageService()
    sent = []

    def fake_send(schedule, destination=None):
        sent.append(destination)
        if destination == "PU2FAIL-7":
            raise ConnectionError("rota indisponível")
        return {"queued": True}

    monkeypatch.setattr(service, "_send_one", fake_send)
    monkeypatch.setattr(scheduler.diag, "log_event", lambda *args, **kwargs: None)

    schedule = {
        "id": 99,
        "target_type": "list",
        "targets": ["PY2OK-9", "PU2FAIL-7", "PT2OK-1"],
        "recipient_group_id": None,
        "retry_targets": [],
        "interval_seconds": 1,
        "continue_on_error": True,
    }
    monkeypatch.setattr(service._stop, "wait", lambda _seconds: False)

    ok, summary, error, retry_targets = service._execute(schedule, manual=False)
    assert ok is False
    assert sent == ["PY2OK-9", "PU2FAIL-7", "PT2OK-1"]
    assert retry_targets == ["PU2FAIL-7"]
    assert "PY2OK-9" in summary
    assert "PT2OK-1" in summary
    assert "PU2FAIL-7" in error
