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

# Até a v1.6.22, este patch protegia os builds contra um JPEG oficial antigo
# que havia sido considerado inválido. A partir da v1.6.23, a logo oficial
# foi validada e voltou a ser a identidade única do aplicativo; portanto,
# não devemos mais reverter a interface/ícones para app_logo.svg/png.
if version_tuple(version) < (1, 6, 23):
    html_path = ROOT / "pt2vhf_aprs/templates/index.html"
    html = html_path.read_text(encoding="utf-8")
    html = html.replace("img/aprs_logo_official.jpg", "img/app_logo.svg")
    html = html.replace('type="image/jpeg"', 'type="image/svg+xml"')
    html_path.write_text(html, encoding="utf-8")

    icon_path = ROOT / "windows/make_icon.py"
    icon = icon_path.read_text(encoding="utf-8")
    icon = icon.replace("aprs_logo_official.jpg", "app_logo.png")
    icon_path.write_text(icon, encoding="utf-8")

    tests_path = ROOT / "tests/test_core.py"
    tests = tests_path.read_text(encoding="utf-8")
    tests = tests.replace(
        '    assert "aprs_logo_official.jpg" in html',
        '    assert "img/app_logo.svg" in html',
    )
    tests_path.write_text(tests, encoding="utf-8")

checks = {
    "pt2vhf_aprs/aprs_service.py": ["queue_message_parts", "def shutdown(self)"],
    "pt2vhf_aprs/web.py": ["queue_message_parts"],
    "pt2vhf_aprs/static/js/app.js": ["messageSending", "Mensagem colocada na fila"],
    "pt2vhf_aprs/database.py": ["shutdown_maintenance"],
}
if version_tuple(version) < (1, 6, 23):
    checks["pt2vhf_aprs/templates/index.html"] = ["img/app_logo.svg"]

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.10 validation failed: {needle!r} missing from {rel}")

if version_tuple(version) >= (1, 6, 23):
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    if "img/aprs_logo_official.jpg" not in html:
        raise SystemExit("v1.6.10 validation failed: v1.6.23+ must preserve the official logo")

print("v1.6.10 source validation OK")
