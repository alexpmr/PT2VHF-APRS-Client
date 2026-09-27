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

html_path = ROOT / "pt2vhf_aprs/templates/index.html"
html = html_path.read_text(encoding="utf-8")

# O fallback de logo estável valia somente até a v1.6.22. A partir da
# v1.6.23, a logo oficial foi validada e deve permanecer em todos os builds.
if version_tuple(version) < (1, 6, 23):
    html = html.replace("img/aprs_logo_official.jpg", "img/app_logo.svg")
    html = html.replace('type="image/jpeg"', 'type="image/svg+xml"')
    html_path.write_text(html, encoding="utf-8")

checks = {
    "pt2vhf_aprs/aprs_service.py": ["queue_message_parts", "def shutdown(self)"],
    "pt2vhf_aprs/web.py": ["queue_message_parts"],
    "pt2vhf_aprs/static/js/app.js": ["messageSending", "Mensagem colocada na fila"],
    "pt2vhf_aprs/database.py": ["shutdown_maintenance"],
}
checks["pt2vhf_aprs/templates/index.html"] = [
    "img/aprs_logo_official.jpg" if version_tuple(version) >= (1, 6, 23) else "img/app_logo.svg"
]
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.8 validation failed: {needle!r} missing from {rel}")
print("v1.6.8 source validation OK")
