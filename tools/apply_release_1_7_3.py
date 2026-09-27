from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
try:
    version_tuple = tuple(int(part) for part in version.split("."))
except ValueError as exc:
    raise SystemExit(f"v1.7.3 validation failed: invalid VERSION={version!r}") from exc
if version_tuple < (1, 7, 3):
    raise SystemExit(f"v1.7.3 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['APP_TOCALL = "APZVHF"'],
    "pt2vhf_aprs/updater.py": [
        "update_install_requested",
        "update_download_started",
        "update_download_validated",
        'script.write_text("\\n".join(lines) + "\\n", encoding="utf-8")',
    ],
    "pt2vhf_aprs/web.py": [
        "update_install_http_requested",
        "update_install_http_failed",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "Feedback visual antes mesmo da chamada HTTP",
        "Preparando atualização…",
        "$('#openLatestReleaseButton')?.addEventListener('click', () => void installLatestUpdate());",
    ],
    "pt2vhf_aprs/database.py": [
        "APRS_CLIENT_CANONICAL_NAMES",
        "def _canonical_client_family",
        '"aliases": sorted',
    ],
    "tests/test_core.py": [
        "test_v173_updater_helpers_use_real_newlines",
        "test_v173_client_versions_group_semantic_versions_into_one_family",
        "test_v173_download_install_button_has_immediate_feedback_and_direct_action",
    ],
    "README.md": ["PT2VHF APRS Client"],
    "CHANGELOG.md": ["## v1.7.3 - 2026-09-27"],
    "pt2vhf_aprs/version_notes.py": ['"1.7.3"'],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.3 validation failed: {needle!r} missing from {rel}")

updater = (ROOT / "pt2vhf_aprs" / "updater.py").read_text(encoding="utf-8")
windows_block = updater[
    updater.index("def _write_windows_helper"):
    updater.index("\ndef _prepare_linux_tar")
]
rollback_block = updater[updater.index("def restore_windows_portable_backup"):]
if "\\\\n" in windows_block:
    raise SystemExit("v1.7.3 validation failed: Windows helper still emits literal \\n separators")
if "\\\\n" in rollback_block:
    raise SystemExit("v1.7.3 validation failed: rollback helper still emits literal \\n separators")

print("v1.7.3 release validation OK")
