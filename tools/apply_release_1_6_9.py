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

tests_path = ROOT / "tests/test_core.py"
tests = tests_path.read_text(encoding="utf-8")

if version_tuple(version) < (1, 6, 23):
    tests = tests.replace(
        '    assert "aprs_logo_official.jpg" in html',
        '    assert "img/app_logo.svg" in html',
    )
else:
    tests = tests.replace(
        '    assert "img/app_logo.svg" in html',
        '    assert "aprs_logo_official.jpg" in html',
    )
tests_path.write_text(tests, encoding="utf-8")

logo_needle = "img/aprs_logo_official.jpg" if version_tuple(version) >= (1, 6, 23) else "img/app_logo.svg"
test_needle = 'assert "aprs_logo_official.jpg" in html' if version_tuple(version) >= (1, 6, 23) else 'assert "img/app_logo.svg" in html'
checks = {
    "pt2vhf_aprs/aprs_service.py": ["queue_message_parts", "def shutdown(self)"],
    "pt2vhf_aprs/web.py": ["queue_message_parts"],
    "pt2vhf_aprs/static/js/app.js": ["messageSending", "Mensagem colocada na fila"],
    "pt2vhf_aprs/database.py": ["shutdown_maintenance"],
    "pt2vhf_aprs/templates/index.html": [logo_needle],
    "tests/test_core.py": [test_needle],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.9 validation failed: {needle!r} missing from {rel}")

print("v1.6.9 source validation OK")
