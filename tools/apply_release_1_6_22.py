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

if version_tuple(version) < (1, 6, 22):
    raise SystemExit(f"v1.6.22 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": [
        '__version__ = "',
    ],
    "pt2vhf_aprs/updater.py": [
        "def download_and_install(",
        "UPDATE_LOCK_FILE",
        "def install_supported(",
        "def _write_windows_helper(",
        "def _write_posix_helper(",
        "Stop-Process -Id $pidToWait -Force",
        "kill -KILL",
        "hdiutil attach",
        "pkexec dpkg -i",
        'archive.extractall(stage, filter="data")',
    ],
    "pt2vhf_aprs/web.py": [
        '@app.post("/api/update/install")',
        "updater.download_and_install(",
        "updater.select_asset(",
        '"asset_ready": False',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "async function installLatestUpdate()",
        "/api/update/install",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="updateInstallNow"',
        "Baixar e instalar nova versão",
    ],
    "windows_app.py": ["updater.register_exit_handler(_exit_for_update)"],
    "linux_app.py": ["updater.register_exit_handler(_exit_for_update)"],
    "macos_app.py": ["updater.register_exit_handler(_exit_for_update)"],
    "tests/test_core.py": [
        "test_auto_update_flow_is_enabled_and_platform_launchers_register_exit",
        "test_updater_select_asset_matches_exact_platform_asset",
    ],
    "README.md": [
        "# PT2VHF APRS Client - v",
        "updater auxiliar",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.22 validation failed: {needle!r} missing from {rel}")

print("v1.6.22 automatic cross-platform updater validation OK")
