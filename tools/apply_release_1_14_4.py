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
        '<option value="0.25">15 min</option>', '<option value="0.5">30 min</option>',
    ],
    "tools/compact_icon.py": ["def render_compact_icon(", "BRAND_SOURCE", "rounded_rectangle", "ImageDraw"],
    "windows/make_icon.py": ["render_compact_icon", "app_logo.png"],
    "macos/make_icon.py": ["render_compact_icon", "app_logo.png"],
    "linux/build_linux.sh": ["render_compact_icon(256)", "app_logo.png"],
    "pt2vhf_aprs/static/js/v190.js": ["$('[data-v190-alert]',card).forEach"],
    "pt2vhf_aprs/static/css/v141.css": ["@media(max-width:1320px)", "minmax(340px,.85fr)", "overflow-wrap:anywhere"],
    "pt2vhf_aprs/static/js/v112.js": ["ResizeObserver", "invalidateSize({animate:false})"],
    "pt2vhf_aprs/v111_features.py": ["def db_health(*, deep: bool = True)", "db_health(deep=deep)", 'result["integrity"] = "operacional"'],
    "pt2vhf_aprs/v142_features.py": ["hours = float(request.args.get(\"hours\", 24))"],
    "tests/test_v144_release.py": [
        "test_v144_real_aprsis_path_is_igate_and_rf_is_not_internet",
        "test_v144_modal_uses_real_save_restore_and_target_navigation",
    ],
    "tools/capture_manual_screenshots.py": [
        "Beacon 1.14.4 salvo no modal", "unsavedSaveButton",
        "unsavedDiscardButton", "unsavedCancelButton",
        "click(button=\"right\")", "layer?._pt2vhfEdge?.kind === 'igate'",
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
