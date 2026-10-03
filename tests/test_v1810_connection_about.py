from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1810_header_has_single_unified_aprs_connection_control():
    html = read("pt2vhf_aprs/templates/index.html")
    assert 'id="connectButton"' in html
    assert 'id="connectionControlStatus"' in html
    assert 'id="connectionControlAction"' in html
    assert 'class="connection-control disconnected"' in html
    assert 'id="connectionStatus"' not in html
    assert html.count('id="connectButton"') == 1


def test_v1810_connection_control_uses_real_backend_state_not_button_text():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "function connectionControlView(status = {})" in js
    assert "const connected = !!status.connected;" in js
    assert "const verified = !!status.verified;" in js
    assert "const wanted = !!status.wanted;" in js
    assert "state.connectionWanted = !!s.wanted;" in js
    assert "button.dataset.action = view.action;" in js
    assert "button?.dataset.action" in js
    assert "button.textContent === ui('Desconectar'" not in js


def test_v1810_connection_states_and_actions_are_explicit():
    js = read("pt2vhf_aprs/static/js/app.js")
    for label in (
        "Conectado e verificado",
        "Conectado sem verificação",
        "Conectando…",
        "Reconectando…",
        "Conexão perdida",
        "Desconectado",
        "Clique para conectar",
        "Clique para desconectar",
        "Reconectando automaticamente",
    ):
        assert label in js
    assert "state.connectionActionBusy" in js
    assert "if (state.connectionActionBusy) return;" in js


def test_v1810_connection_control_has_visual_state_styles():
    css = read("pt2vhf_aprs/static/css/app.css")
    for selector in (
        ".connection-control.connected",
        ".connection-control.unverified",
        ".connection-control.connecting",
        ".connection-control.lost",
        ".connection-control.disconnected .dot",
        ".connection-control-copy strong",
        ".connection-control-copy small",
    ):
        assert selector in css


def test_v1810_about_lists_all_contributors():
    html = read("pt2vhf_aprs/templates/index.html")
    expected = {
        "PP5UA": "Adriano",
        "PY4EI": "Allan",
        "PU2MUS": "Marco",
        "PP5PK": "Daniel Kondlatsch",
        "PT2YW": "Ywstter",
        "PT2PAG": "Paulo Galvão",
    }
    assert 'id="aboutContributorsTitle"' in html
    assert 'id="aboutContributorsText"' in html
    assert "about-contributors-list" in html
    for callsign, name in expected.items():
        assert callsign in html
        assert name in html


def test_v1810_about_acknowledgements_are_localized_in_four_languages():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert js.count("contributorsTitle:") >= 4
    assert js.count("contributors:") >= 4
    assert "Agradecimentos / Colaboradores" in js
    assert "Acknowledgements / Contributors" in js
    assert "Remerciements / Contributeurs" in js
    assert "radioaficionados" in js
    assert "radioamateurs" in js
    assert "$('#aboutContributorsTitle').textContent = copy.contributorsTitle" in js
    assert "$('#aboutContributorsText').textContent = copy.contributors" in js


def test_v1810_version():
    version = read("VERSION").strip()
    parts = tuple(int(item) for item in version.split("."))
    assert parts >= (1, 8, 10)
    assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
