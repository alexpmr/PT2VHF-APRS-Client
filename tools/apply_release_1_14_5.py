"""Validação estrutural da release v1.14.5."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.5":
    raise SystemExit("VERSION must be 1.14.5")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.14.5"'],
    "windows/version_info.txt": [
        "filevers=(1, 14, 5, 0)", "prodvers=(1, 14, 5, 0)",
        "FileVersion', '1.14.5'", "ProductVersion', '1.14.5'",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "configTouchedFields: new Set()",
        "configEditGeneration: 0",
        "function restoreConfigBaselineLocally()",
        "function configChangedPayload()",
        "const payload = configChangedPayload()",
        "restoreConfigBaselineLocally();",
        "result?.error || ui('Não foi possível salvar.'",
        "applyConfigToForm(cfg, { preserveTouched: !force && editedDuringLoad })",
    ],
    "pt2vhf_aprs/database.py": [
        "provided = set(data) & allowed",
        '"map_zoom_step" in provided',
        'key in provided and not (1.0 <= float(merged[key]) <= 2.0)',
    ],
    "pt2vhf_aprs/static/js/v112.js": [
        "host.querySelectorAll('[data-satellite-service]').forEach",
        "function safeRenderDetail(norad)",
        "Satellite detail rendering error",
    ],
    "tests/test_v145_release.py": [
        "test_v145_partial_config_save_tolerates_legacy_unrelated_value",
        "test_v145_discard_is_local_and_continue_is_network_free",
        "test_v145_satellite_service_controls_use_collection",
    ],
    "tools/capture_manual_screenshots.py": [
        "V145_SLOW_CONFIG_TEST",
        "V145_REAL_ERROR_TEST",
        "V145_DISCARD_OFFLINE_TEST",
    ],
    "README.md": ["# PT2VHF APRS Client - v1.14.5", "## Novidades da v1.14.5"],
    "CHANGELOG.md": ["## 1.14.5 - 2026-10-07"],
    "BACKLOG.md": ["## Concluído na v1.14.5"],
    "pt2vhf_aprs/version_notes.py": ['"1.14.5": {'],
}
for path, needles in checks.items():
    content = read(path)
    for needle in needles:
        if needle not in content:
            raise SystemExit(f"v1.14.5: falta {needle!r} em {path}")

if "$('[data-satellite-service]',host).forEach" in read("pt2vhf_aprs/static/js/v112.js"):
    raise SystemExit("v1.14.5: seletor SAT inseguro ainda presente")

print("v1.14.5: validação de metadados e integração OK")
