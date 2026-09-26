from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.6.20":
    raise SystemExit(f"v1.6.20 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": [
        '__version__ = "1.6.20"',
        'APP_TOCALL = "APZVHF"',
    ],
    "pt2vhf_aprs/database.py": [
        "def resolve_aprs_device_id(",
        "APRS_DEVICE_ID_PATH",
        '"top_limit": 20',
        '"own_client": own_client',
        'edges.append((previous, candidate, "rf", candidate))',
        "Migração v1.6.20",
    ],
    "pt2vhf_aprs/aprs_service.py": [
        "APP_TOCALL",
        ">{APP_TOCALL},TCPIP*",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function setLanguageMenuOpen(open)",
        "languageQuickCurrentFlag",
        "language-quick-option",
        "const topLimit = Math.max(1, Number(data.top_limit || 20))",
        "client-version-own-row",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="languageQuickCurrent"',
        'id="languageQuickMenu"',
        "flag_england.svg",
        "Software / dispositivos APRS",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".language-quick-current",
        ".language-quick-menu",
        ".client-version-own-row",
    ],
    "tests/test_core.py": [
        "test_aprs_device_friendly_names_and_own_client_identifier",
        "test_qarray_igate_reception_is_rf_link",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.20 validation failed: {needle!r} missing from {rel}")

data_file = ROOT / "pt2vhf_aprs" / "data" / "aprs_device_ids.json"
if not data_file.exists() or data_file.stat().st_size < 10000:
    raise SystemExit("v1.6.20 validation failed: APRS device ID snapshot missing or too small")

for spec in (
    ROOT / "windows" / "PT2VHF_APRS_Client.spec",
    ROOT / "windows" / "PT2VHF_APRS_Client_Portable.spec",
    ROOT / "linux" / "PT2VHF_APRS_Client_Linux.spec",
    ROOT / "macos" / "PT2VHF_APRS_Client_macOS.spec",
):
    text = spec.read_text(encoding="utf-8")
    if "pt2vhf_aprs' / 'data" not in text:
        raise SystemExit(f"v1.6.20 validation failed: data directory missing from {spec.name}")

print("v1.6.20 friendly clients/topology/language validation OK")
