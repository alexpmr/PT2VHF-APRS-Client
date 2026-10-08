from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.14.8":
    raise SystemExit("VERSION must be 1.14.8")
if '__version__ = "1.14.8"' not in read("pt2vhf_aprs/__init__.py"):
    raise SystemExit("package version must be 1.14.8")

db = read("pt2vhf_aprs/database.py")
for marker in (
    '"auto_reply_enabled": 0',
    '"auto_reply_text": "Mensagem recebida. Retornarei assim que possível."',
    '"auto_reply_cooldown_seconds": 300',
    "auto_reply_enabled INTEGER NOT NULL DEFAULT 0",
    "auto_reply_cooldown_seconds INTEGER NOT NULL DEFAULT 300",
    "automated INTEGER NOT NULL DEFAULT 0",
):
    if marker not in db:
        raise SystemExit(f"v1.14.8 database marker missing: {marker}")

service = read("pt2vhf_aprs/aprs_service.py")
for marker in (
    "def _maybe_auto_reply",
    "self._auto_reply_last",
    'route = "rf_direct" if via_rf else "aprs_is"',
    "automated=True",
):
    if marker not in service:
        raise SystemExit(f"v1.14.8 auto-reply marker missing: {marker}")

features = read("pt2vhf_aprs/v111_features.py")
for marker in (
    "def save_retention_settings",
    'DELETE FROM topology_edges WHERE last_seen<?',
    '"reclaimable_bytes": reclaimable_bytes',
):
    if marker not in features:
        raise SystemExit(f"v1.14.8 retention marker missing: {marker}")

ui = read("pt2vhf_aprs/static/js/v111.js")
for marker in ("Não apagar", "1 semana", "1 mês", "v148AutoReplyEnabled", "v148AutoReplyText"):
    if marker not in ui:
        raise SystemExit(f"v1.14.8 UI marker missing: {marker}")

tests = read("tests/test_v148_release.py")
for marker in (
    "test_v148_auto_reply_only_direct_message_and_has_cooldown",
    "test_v148_retention_presets_are_independent_and_prune_topology_edges",
):
    if marker not in tests:
        raise SystemExit(f"v1.14.8 regression missing: {marker}")

print("v1.14.8 validation OK")
