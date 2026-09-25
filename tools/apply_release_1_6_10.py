from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A release completa usa a identidade visual estável até que a nova logo
# oficial seja reintegrada com um arquivo validado.
html_path = ROOT / "pt2vhf_aprs/templates/index.html"
html = html_path.read_text(encoding="utf-8")
html = html.replace("img/aprs_logo_official.jpg", "img/app_logo.svg")
html = html.replace('type="image/jpeg"', 'type="image/svg+xml"')
html_path.write_text(html, encoding="utf-8")

# Proteção adicional contra o patch legado da v1.6.6 voltar a apontar
# o gerador de ícone Windows para o JPEG inválido.
icon_path = ROOT / "windows/make_icon.py"
icon = icon_path.read_text(encoding="utf-8")
icon = icon.replace("aprs_logo_official.jpg", "app_logo.png")
icon_path.write_text(icon, encoding="utf-8")

# O teste legado de identidade visual deve acompanhar a logo estável usada
# no build desta release.
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
    "pt2vhf_aprs/templates/index.html": ["img/app_logo.svg"],
    "tests/test_core.py": ['assert "img/app_logo.svg" in html'],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.10 validation failed: {needle!r} missing from {rel}")

if "aprs_logo_official.jpg" in icon_path.read_text(encoding="utf-8"):
    raise SystemExit("v1.6.10 validation failed: Windows icon still references invalid JPEG")

print("v1.6.10 source validation OK")
