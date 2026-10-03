from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1813_consolidation_remains_covered_in_newer_versions():
    current = read("VERSION").strip()
    version = tuple(int(part) for part in current.split("."))
    assert version >= (1, 8, 13)
    assert f'__version__ = "{current}"' in read("pt2vhf_aprs/__init__.py")


def test_v1813_message_route_backlog_is_present():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    service = read("pt2vhf_aprs/aprs_service.py")

    assert 'id="messageRoute"' in html
    assert '<option value="auto" selected>Automático</option>' in html
    assert '<option value="aprs_is">APRS-IS</option>' in html
    assert '<option value="rf_direct">RF direto</option>' in html
    assert '<option value="rf_custom">RF personalizado</option>' in html
    assert 'id="messagePath"' in html
    assert "$('#messageRoute')?.value || 'auto'" in js
    assert "route === 'rf_custom'" in js
    assert '"rf_custom": "rf_custom"' in service


def test_v1813_low_height_layout_covers_1360x768_and_1280x720():
    css = read("pt2vhf_aprs/static/css/app.css")

    # A regra max-height:800 cobre tanto 768 px quanto 720 px de altura
    # em desktops com largura acima de 900 px.
    assert "@media (max-height: 800px) and (min-width: 901px)" in css
    assert "#tab-messages > .panel-header" in css
    assert ".message-composer" in css
    assert ".messages-table-wrap { min-height: 80px; }" in css
    assert ".station-popup-actions" in css
    assert "position: sticky;" in css
    assert "max-height: min(500px, calc(100dvh - 230px));" in css


def test_v1813_non_bidirectional_targets_disable_interaction_actions():
    js = read("pt2vhf_aprs/static/js/app.js")
    db = read("pt2vhf_aprs/database.py")
    css = read("pt2vhf_aprs/static/css/app.css")

    assert "function stationInteractionProfile(s)" in js
    assert "interaction_evidence" in js
    assert "message_capable" in js
    assert "format === 'object' || format === 'item'" in js
    assert "DIGI(?:PEATER)?" in js
    assert "D-?STAR" in js
    assert "HOTSPOT" in js
    assert "function stationInteractionDisabledAttrs(profile)" in js
    assert 'data-query-type="APRSP"' in js
    assert 'data-query-type="APRSS"' in js
    assert 'data-query-type="APRSD"' in js
    assert 'data-query-type="PINGACK"' in js
    assert 'data-query-type="APRST"' in js
    assert '${interactionDisabled}>Enviar mensagem</button>' in js
    assert "station-interaction-disabled-note" in js
    assert "interaction_evidence" in db
    assert "message_capable" in db
    assert ".station-popup .btn:disabled" in css


def test_v1813_dem_elevation_backlog_is_present_and_persistent():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    db = read("pt2vhf_aprs/database.py")

    assert 'id="elevationToggle"' in html
    assert "Relevo com corte" in html
    assert "elevationThresholdSlider" in js
    assert "elevationThresholdNumber" in js
    assert "Math.min(9000, Math.max(100" in js
    assert "|| 3000" in js
    assert "elevation_opacity" in js
    assert "elevation_slider_max" in db
    assert "elevation_threshold" in db
    assert "elevation_opacity" in db
    assert ".elevation-vertical-range" in css
    assert "height: 390px;" in css
    assert "@media (max-height: 700px)" in css
    assert ".elevation-vertical-range { height: 255px; }" in css


def test_v1813_about_backlog_is_present_and_localized():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")

    assert "static', filename='img/app_logo.png'" in html
    assert "tiny.cc/aprs" in html
    assert "wa.me/5561984023634" in html
    assert "mailto:alexpmr@gmail.com" in html
    assert 'id="aboutPromoteButton"' in html
    assert "function aboutCopy()" in js
    assert "'pt-BR': {" in js
    assert "en: {" in js
    assert "es: {" in js
    assert "fr: {" in js
    assert "function renderAbout()" in js
    assert "Announcement APRS" in js


def test_v1813_backlog_marks_consolidation_and_removes_stale_elevation_item():
    backlog = read("BACKLOG.md")
    assert "## Concluído na v1.8.13" in backlog
    assert "Automático / APRS-IS / RF direto / RF personalizado" in backlog
    assert "1360×768 e 1280×720" in backlog
    assert "sem evidência de comunicação bidirecional" in backlog
    assert "Relevo com corte" in backlog
    assert "tiny.cc/aprs" in backlog
    assert "- **Mapa — camada Elevação mínima com corte por altitude**" not in backlog
