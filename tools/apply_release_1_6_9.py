from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = {
    "pt2vhf_aprs/aprs_service.py": ["queue_message_parts", "def shutdown(self)"],
    "pt2vhf_aprs/web.py": ["queue_message_parts"],
    "pt2vhf_aprs/static/js/app.js": ["messageSending", "Mensagem colocada na fila"],
    "pt2vhf_aprs/database.py": ["shutdown_maintenance"],
    "pt2vhf_aprs/templates/index.html": ["img/app_logo.png"],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.9 validation failed: {needle!r} missing from {rel}")
print("v1.6.9 source validation OK")
