from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


version = read("VERSION").strip()
if version != "1.8.17":
    raise SystemExit(f"v1.8.17 validation failed: VERSION={version!r}")

# Fail early on Python syntax errors in the files most affected by this release.
for rel in (
    "pt2vhf_aprs/database.py",
    "pt2vhf_aprs/scheduled_messages.py",
    "pt2vhf_aprs/web.py",
    "tests/test_v1817_scheduler_zoom_tnc.py",
):
    ast.parse(read(rel), filename=rel)

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.17"'],
    "windows/version_info.txt": [
        "filevers=(1, 8, 17, 0)",
        "prodvers=(1, 8, 17, 0)",
        "FileVersion', '1.8.17'",
        "ProductVersion', '1.8.17'",
    ],
    "pt2vhf_aprs/database.py": [
        '"map_zoom_step": 0.10',
        "map_zoom_step REAL NOT NULL DEFAULT 0.10",
        "CREATE TABLE IF NOT EXISTS recipient_groups",
        "CREATE TABLE IF NOT EXISTS scheduled_messages",
        "def save_scheduled_message(",
        "def claim_due_scheduled_message(",
        "Boletim de grupo deve usar linha BLN0 a BLN9",
    ],
    "pt2vhf_aprs/scheduled_messages.py": [
        "class ScheduledMessageService",
        "def prepare_schedule_payload(",
        "def calculate_next_run(",
        "def execute_now(",
        "aprs_service.queue_message_parts",
        "aprs_service.send_bulletin",
        "interval_seconds",
        "retry_policy",
        "continue_on_error",
        "retry_targets",
    ],
    "pt2vhf_aprs/web.py": [
        "scheduled_message_service.start()",
        '@app.get("/api/messages/scheduled")',
        '@app.post("/api/messages/scheduled")',
        '@app.post("/api/messages/scheduled/<int:schedule_id>/run-now")',
        '@app.get("/api/messages/recipient-groups")',
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="scheduledMessagesButton"',
        'id="scheduledMessagesPanel"',
        'id="scheduledMessageForm"',
        'id="scheduledTargetType"',
        'id="scheduledRecipientGroup"',
        'id="scheduledMessagesTable"',
        'name="map_zoom_step" id="mapZoomStep"',
        'id="resetMapZoomButton"',
        "<strong>PP5AU</strong><span>Adriano</span>",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function mapZoomOptions(value)",
        "function applyMapZoomPreferences(value)",
        "zoomSnap: zoomOptions.step",
        "function loadScheduledMessages()",
        "function scheduledFormPayload()",
        "function saveRecipientGroup()",
        "pt2vhf_message_content_filters_v2",
    ],
    "pt2vhf_aprs/static/js/tnc.js": [
        "function statusClass(connected, paused, rxState = 'waiting')",
        "Serial conectada — sem KISS",
        "Serial operacional — RX KISS ativo",
        "TNC · Serial sem KISS",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".status.warning",
        "/* v1.8.17 - scheduled messages */",
        ".scheduled-messages-panel",
    ],
    "tests/test_v1817_scheduler_zoom_tnc.py": [
        "test_zoom_step_validation_uses_safe_values",
        "test_recipient_group_and_schedule_roundtrip_in_sqlite",
        "test_weekly_schedule_calculates_future_occurrence",
        "test_tnc_connected_without_valid_kiss_is_warning_not_success",
        "test_list_retry_contains_only_failed_destinations",
    ],
}

missing = []
for rel, snippets in checks.items():
    text = read(rel)
    for snippet in snippets:
        if snippet not in text:
            missing.append(f"{rel}: {snippet}")

if missing:
    raise SystemExit("v1.8.17 validation failed:\n- " + "\n- ".join(missing))

print("v1.8.17 production validation OK")
