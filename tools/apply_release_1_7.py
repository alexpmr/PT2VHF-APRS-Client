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

if version_tuple(version) < (1, 7):
    raise SystemExit(f"v1.7 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/templates/index.html": [
        'data-language="es"',
        'data-language="fr"',
        '<option value="es">Español</option>',
        '<option value="fr">Français</option>',
        'name="traffic_animation_enabled"',
        'name="statistics_font_size"',
        'js/i18n_extra.js',
        'class="map-top-toolbar"',
    ],
    "pt2vhf_aprs/static/js/i18n_extra.js": [
        "window.PT2VHF_I18N",
        "es:",
        "fr:",
        '"Mensagens": "Mensajes"',
        '"Mensagens": "Messages"',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "normalizeLanguage",
        "state.trafficPlaying = state.trafficAnimationEnabled;",
        "state.selectedConversation = destinationConversation ? composerDestination : '';",
        "Novo destinatário:",
        "statistics_font_size",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        "#groupMessagesButton,",
        "white-space: nowrap;",
        "--statistics-font-size",
        ".map-top-toolbar",
    ],
    "pt2vhf_aprs/database.py": [
        '"traffic_animation_enabled": 1',
        '"statistics_font_size": 13',
        '{"pt-BR", "en", "es", "fr"}',
    ],
    "README.md": [
        "Español",
        "Français",
    ],
    "CHANGELOG.md": [
        "## v1.7 - 2026-09-27",
        "v1.7.1, v1.7.2, v1.7.3",
    ],
    "pt2vhf_aprs/version_notes.py": [
        '"1.7"',
        "Nova linha 1.7",
    ],
    "tests/test_core.py": [
        "test_v17_language_options_and_runtime",
        "test_v17_message_conversation_tracks_recipient",
        "test_v17_traffic_animation_defaults_enabled",
        "test_v17_statistics_friendly_names_and_font_control",
        "test_v17_message_filter_buttons_are_compact",
        "test_map_controls_are_above_map_not_overlaid",
    ],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7 validation failed: {needle!r} missing from {rel}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
if "v1.6.25" in readme or "## v1.6.25" in changelog:
    raise SystemExit("v1.7 validation failed: v1.6.25 must not be published")

print("v1.7 UI/i18n/messaging validation OK")
