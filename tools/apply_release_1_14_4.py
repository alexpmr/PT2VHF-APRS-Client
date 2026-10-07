"""Validação estrutural da release v1.14.4. Testes reais: pytest + Playwright."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


if read("VERSION").strip() != "1.14.4":
    raise SystemExit("VERSION must be 1.14.4")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.14.4"'],
    "windows/version_info.txt": [
        "filevers=(1, 14, 4, 0)", "prodvers=(1, 14, 4, 0)",
        "FileVersion', '1.14.4'", "ProductVersion', '1.14.4'",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "async function resolveUnsavedConfig(mode)",
        "state.configTransitionBusy",
        "saved = await saveConfigForm()",
        "if (!await loadConfig())",
        "function pendingConfigFeedback(",
        "addEventListener('contextmenu', event => {",
        "openStationQuickMessage(row.dataset.callsign || '')",
        "if (edge.kind !== 'igate') {",
        "dashArray: edge.kind === 'igate' ? '7 5' : null",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="unsavedConfigActionStatus"', 'id="unsavedSaveButton"',
        'id="unsavedDiscardButton"', 'id="unsavedCancelButton"',
    ],
    "tools/compact_icon.py": ["def render_compact_icon(", "BRAND_SOURCE", "rounded_rectangle", "ImageDraw"],
    "windows/make_icon.py": ["render_compact_icon", "app_logo.png"],
    "macos/make_icon.py": ["render_compact_icon", "app_logo.png"],
    "linux/build_linux.sh": ["render_compact_icon(256)", "app_logo.png"],
    "tests/test_v144_release.py": [
        "test_v144_real_aprsis_path_is_igate_and_rf_is_not_internet",
        "test_v144_modal_uses_real_save_restore_and_target_navigation",
    ],
    "tools/capture_manual_screenshots.py": [
        "Beacon 1.14.4 salvo no modal", "unsavedSaveButton",
        "unsavedDiscardButton", "unsavedCancelButton",
        "click(button=\"right\")", "stroke-dasharray",
    ],
    "README.md": ["# PT2VHF APRS Client - v1.14.4", "## Novidades da v1.14.4"],
    "CHANGELOG.md": ["## 1.14.4 - 2026-10-07"],
    "BACKLOG.md": ["## Concluído na v1.14.4"],
    "pt2vhf_aprs/version_notes.py": ['"1.14.4": {'],
}
for path, needles in checks.items():
    text = read(path)
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.14.4: falta {needle!r} em {path}")

print("v1.14.4: validação de metadados e integração OK")
