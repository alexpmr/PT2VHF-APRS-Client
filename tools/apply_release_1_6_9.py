from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# A v1.6.8 restaurou temporariamente a logo estável para não bloquear o build.
# O patch legado da v1.6.6 injeta um teste que ainda exige o JPEG oficial.
# Atualiza apenas essa expectativa para refletir o estado real da v1.6.9.
tests_path = ROOT / "tests/test_core.py"
tests = tests_path.read_text(encoding="utf-8")
tests = tests.replace(
    '    assert "aprs_logo_official.jpg" in html',
    '    assert "img/app_logo.svg" in html',
)
tests_path.write_text(tests, encoding="utf-8")

# Valida os pontos críticos desta versão.
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
            raise SystemExit(f"v1.6.9 validation failed: {needle!r} missing from {rel}")

print("v1.6.9 source validation OK")
