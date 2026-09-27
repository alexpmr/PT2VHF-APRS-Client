from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
try:
    version_tuple = tuple(int(part) for part in version.split("."))
except ValueError as exc:
    raise SystemExit(f"v1.7.1 validation failed: invalid VERSION={version!r}") from exc
if version_tuple < (1, 7, 1):
    raise SystemExit(f"v1.7.1 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['APP_TOCALL = "APZVHF"'],
    "pt2vhf_aprs/database.py": [
        "TRACK_OUTLIER_MAX_SPEED_KMH",
        "track_position_outlier_rejected",
        "last_valid_track",
    ],
    "pt2vhf_aprs/updater.py": [
        "HELPER_READY_FILE",
        "def _wait_for_helper_ready",
        "update_helper_start_failed",
        "_request_exit_after(delay=2.5)",
    ],
    "pt2vhf_aprs/aprs_service.py": [
        'return "announcement"',
        'message_type = "announcement"',
        "BLN[A-Z]",
    ],
    "pt2vhf_aprs/web.py": ['"announcement"'],
    "pt2vhf_aprs/templates/index.html": [
        'data-tab="about"',
        'id="tab-about"',
        'id="mapContextBar"',
        'id="mapHistoryToggle"',
        'id="stationsToggle"',
        'id="tracklogToggle"',
        'id="topologyToggle"',
        'id="promotionModal"',
        "tiny.cc/aprs",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".tab.has-unread:not(.active)",
        "updateAvailablePulse",
        ".map-context-bar",
        ".about-panel",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "splitTrackSegments",
        "pt2vhf_stations_enabled",
        "pt2vhf_tracklog_enabled",
        "renderAbout",
        "promotionPacketPreview",
        "data-quick-message-callsign",
        "messagesTab?.classList.toggle('has-unread'",
        "showUpdateModal();",
    ],
    "pt2vhf_aprs/static/js/i18n_extra.js": [
        '"Sobre": "Acerca de"',
        '"Sobre": "À propos"',
        '"Anúncio geral": "Anuncio general"',
        '"Anúncio geral": "Annonce générale"',
    ],
    "README.md": [
        "PT2VHF APRS Client",
        "Announcement APRS BLNA",
    ],
    "CHANGELOG.md": [
        "## v1.7.1 - 2026-09-27",
        "saltos irreais",
    ],
    "pt2vhf_aprs/version_notes.py": [
        '"1.7.1"',
        "Atualizador corrigido",
    ],
    "tests/test_core.py": [
        "test_v171_aprs_announcement_packet",
        "test_v171_rejects_implausible_position_jump_until_relocation_is_confirmed",
        "test_v171_updater_requires_helper_readiness_before_exit",
        "test_v171_map_controls_are_independent_and_activity_is_removed",
        "test_v171_about_tab_and_manual_aprs_promotion",
        "test_v171_alerts_and_quick_message_links",
        "test_v171_history_is_contextual_to_map",
        "test_v171_i18n_expands_recent_ui_in_all_languages",
    ],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.1 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
if 'id="mapStationAgeFilter"' in html or "mapStationAgeFilter" in js:
    raise SystemExit("v1.7.1 validation failed: legacy Activity filter remains")

print("v1.7.1 release validation OK")
