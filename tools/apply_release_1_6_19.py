from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.6.19":
    raise SystemExit(f"v1.6.19 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/database.py": [
        "def client_version_stats(",
        "client_versions",
        "def _aprs_tocall_from_raw(",
    ],
    "pt2vhf_aprs/aprs_service.py": [
        'f"Posição: {lat:.6f}, {lon:.6f}"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "queryLastByStation: new Map()",
        "function queryResultMarkup(query)",
        "function loadStationQueryHistory(",
        "Ver histórico de queries",
        "function renderClientVersionStats(stats)",
        "function setQuickLanguage(language)",
        "function syncLanguageFlag()",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="languageQuickSwitch"',
        'id="languageFlag"',
        'id="clientVersionStatsContent"',
        "language-flag-england",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".station-query-result",
        ".analysis-client-version-panel",
        ".language-quick-switch",
    ],
}
flag_path = ROOT / "pt2vhf_aprs" / "static" / "img" / "flag_england.svg"
if not flag_path.exists():
    raise SystemExit("v1.6.19 validation failed: England flag asset missing")

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.19 validation failed: {needle!r} missing from {rel}")

print("v1.6.19 analysis/query/language UX validation OK")
