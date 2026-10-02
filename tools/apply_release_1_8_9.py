from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.9":
    raise SystemExit(f"v1.8.9 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.9"'],
    "pt2vhf_aprs/database.py": [
        '"update_check_minutes": 15',
        "update_check_minutes INTEGER NOT NULL DEFAULT 15",
        'ALTER TABLE config ADD COLUMN update_check_minutes INTEGER NOT NULL DEFAULT 15',
        'merged["update_check_minutes"] = max(5, min(1440',
        "first_heard TEXT",
        "max_altitude REAL",
        "weather_json TEXT",
        "def aprs_object_friendly_details(",
        '"friendly_details"] = aprs_object_friendly_details(item)',
    ],
    "pt2vhf_aprs/templates/index.html": [
        'name="update_check_minutes"',
        'min="5"',
        'max="1440"',
        'value="15"',
        "Intervalo de verificação (minutos)",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function updateCheckMinutes()",
        "function updateCheckIntervalMs()",
        "function rescheduleUpdateChecks()",
        "state.updateSchedulerReady = true",
        "function friendlyObjectPopupHtml(object, objectSymbol)",
        "Estado do voo",
        "Altitude máxima observada",
        "Dados técnicos",
        "Pacote bruto",
        "marker.bindPopup(friendlyObjectPopupHtml(object, objectSymbol)",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".object-friendly-popup",
        ".object-popup-primary-value",
        ".object-popup-technical",
        ".object-popup-raw",
    ],
    "pt2vhf_aprs/static/js/i18n_extra.js": [
        '"Intervalo de verificação (minutos)"',
        '"Balão / Radiossonda"',
        '"Dados técnicos"',
    ],
    "tests/test_v189_updates_objects.py": [
        "test_v189_update_interval_default_and_bounds",
        "test_v189_update_scheduler_is_dynamic_and_no_30_minute_literal",
        "test_v189_object_normalization_balloon_and_ais",
        "test_v189_object_storage_keeps_structured_fields_and_history",
        "test_v189_friendly_popup_replaces_legacy_object_popup",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.9"'],
    "CHANGELOG.md": ["## 1.8.9 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.9", "## Novidades da v1.8.9"],
    "BACKLOG.md": ["## Concluído na v1.8.9"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.9 validation failed: {needle!r} missing from {rel}")

app = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
if "30 * 60 * 1000" in app:
    raise SystemExit("v1.8.9 validation failed: fixed 30-minute update cadence remains")

database = (ROOT / "pt2vhf_aprs/database.py").read_text(encoding="utf-8")
if "json.dumps(weather, ensure_ascii=False, default=str)" not in database:
    raise SystemExit("v1.8.9 validation failed: robust weather persistence missing")

print("v1.8.9 configurable updates and friendly APRS object popups validation OK")
