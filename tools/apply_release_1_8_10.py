from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.10":
    raise SystemExit(f"v1.8.10 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.10"'],
    "pt2vhf_aprs/templates/index.html": [
        'id="connectButton"',
        'id="connectionControlStatus"',
        'id="connectionControlAction"',
        'class="connection-control disconnected"',
        'id="aboutContributorsTitle"',
        'id="aboutContributorsText"',
        "PU5AAG",
        "PY4EI",
        "PU2MUS",
        "PP5PK",
        "PT2YW",
        "PT2PAG",
        "Daniel Kondlatsch",
        "Paulo Galvão",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function connectionControlView(status = {})",
        "function renderConnectionControl(status = {})",
        "const connected = !!status.connected;",
        "const verified = !!status.verified;",
        "const wanted = !!status.wanted;",
        "state.connectionWanted = !!s.wanted;",
        "button.dataset.action = view.action;",
        "if (state.connectionActionBusy) return;",
        "Conectado e verificado",
        "Conectado sem verificação",
        "Conectando…",
        "Reconectando…",
        "Conexão perdida",
        "contributorsTitle:",
        "contributors:",
        "$('#aboutContributorsTitle').textContent = copy.contributorsTitle",
        "$('#aboutContributorsText').textContent = copy.contributors",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".connection-control.connected",
        ".connection-control.unverified",
        ".connection-control.connecting",
        ".connection-control.lost",
        ".about-contributors-list",
        ".about-contributor",
    ],
    "pt2vhf_aprs/static/js/i18n_extra.js": [
        '"Clique para conectar"',
        '"Clique para desconectar"',
        '"Reconectando automaticamente"',
        '"Aguarde…"',
    ],
    "tests/test_v1810_connection_about.py": [
        "test_v1810_header_has_single_unified_aprs_connection_control",
        "test_v1810_connection_control_uses_real_backend_state_not_button_text",
        "test_v1810_connection_states_and_actions_are_explicit",
        "test_v1810_about_lists_all_contributors",
        "test_v1810_about_acknowledgements_are_localized_in_four_languages",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.10"'],
    "CHANGELOG.md": ["## 1.8.10 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.10", "## Novidades da v1.8.10"],
    "BACKLOG.md": ["## Concluído na v1.8.10"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.10 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
if 'id="connectionStatus"' in html:
    raise SystemExit("v1.8.10 validation failed: legacy separate connectionStatus still present")
if html.count('id="connectButton"') != 1:
    raise SystemExit("v1.8.10 validation failed: expected one unified connectButton")

js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
if "button.textContent === ui('Desconectar'" in js:
    raise SystemExit("v1.8.10 validation failed: connection action still inferred from button text")

print("v1.8.10 unified APRS-IS connection control and contributor acknowledgements validation OK")
