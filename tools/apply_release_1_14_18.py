from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.18":
    raise SystemExit("VERSION must be 1.14.18")
if '__version__ = "1.14.18"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.18")

app = read("pt2vhf_aprs/static/js/app.js")
for marker in (
    "station-follow-button",
    "function followStation(",
    "function ensureTrackFollowPanel(",
    "function updateTrackFollowPanel(",
    "function scheduleTrackFollowPanelRefresh(",
    "state.map?.closePopup?.()",
):
    if marker not in app:
        raise SystemExit(f"v1.14.18 station follow marker missing: {marker}")

css = read("pt2vhf_aprs/static/css/app.css")
for marker in (
    "v1.14.18 - acompanhamento de estação",
    ".station-follow-panel",
    ".station-follow-stop",
):
    if marker not in css:
        raise SystemExit(f"v1.14.18 station follow CSS marker missing: {marker}")

database = read("pt2vhf_aprs/database.py")
for marker in (
    "def mark_message_retry_sent(",
    "def add_incoming_message_once(",
    "ACK/REJ são terminais",
    "NOT IN ('ACK','REJ')",
):
    if marker not in database:
        raise SystemExit(f"v1.14.18 message database marker missing: {marker}")

service = read("pt2vhf_aprs/aprs_service.py")
for marker in (
    "self._retry_lock = threading.RLock()",
    "def send_rf_ack(",
    "def handle_duplicate_rf_message(",
    "msg_id = str(original.get(\"msg_id\") or \"\").strip()",
    "db.mark_message_retry_sent(",
    "db.add_incoming_message_once(",
):
    if marker not in service:
        raise SystemExit(f"v1.14.18 APRS service marker missing: {marker}")

tnc = read("pt2vhf_aprs/tnc_service.py")
for marker in (
    "def queue_local_ack(",
    'info = f":{destination:<9}:ack{clean_id}"',
    "handle_duplicate_rf_message",
):
    if marker not in tnc:
        raise SystemExit(f"v1.14.18 TNC ACK marker missing: {marker}")

tests = read("tests/test_v1418_release.py")
for marker in (
    "test_v1418_station_follow_action_and_live_panel",
    "test_v1418_ack_is_terminal_against_late_tx_state",
    "test_v1418_retry_reuses_same_message_id_and_row",
    "test_v1418_received_message_id_is_deduplicated_but_ack_repeats",
    "test_v1418_tnc_has_pure_rf_ack_and_duplicate_reack",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.18 regression missing: {marker}")

backlog = read("BACKLOG.md")
if "## Novo —" in "\n".join(backlog.splitlines()[:80]):
    raise SystemExit("active software backlog still marked as Novo at the top of BACKLOG.md")

print("v1.14.18 validation OK")
