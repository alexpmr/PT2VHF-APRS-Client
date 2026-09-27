from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.4":
    raise SystemExit(f"v1.7.4 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.4"'],
    "pt2vhf_aprs/templates/index.html": [
        'id="updateDownloadProgress" class="update-download-progress hidden"',
        'role="status" aria-live="assertive"',
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".toast { position: fixed; z-index: 5200;",
        ".message-alert-overlay {",
        "z-index: 4000;",
        ".update-download-progress.error",
        ".update-download-progress.success",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function setUpdateProgress(message = '', type = '')",
        "setUpdateProgress(message, 'error');",
        "Não foi possível concluir a atualização automática.",
        "toast(detail, 'error');",
    ],
    "tests/test_core.py": [
        "test_v174_updater_errors_are_visible_above_modal",
        "test_v174_updater_modal_keeps_actionable_controls_after_failure",
    ],
    "README.md": ["# PT2VHF APRS Client - v1.7.4"],
    "CHANGELOG.md": ["## v1.7.4 - 2026-09-27"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.4"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.4 validation failed: {needle!r} missing from {rel}")

css = (ROOT / "pt2vhf_aprs" / "static" / "css" / "app.css").read_text(encoding="utf-8")
if css.index(".toast { position: fixed; z-index: 5200;") < 0:
    raise SystemExit("v1.7.4 validation failed: toast must stay above modal")

print("v1.7.4 release validation OK")
