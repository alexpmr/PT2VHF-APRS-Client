"""v1.14.52: estilo de mapa de calor clássico e popup de nova versão."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_heatmap_uses_density_palette_and_geographic_radius():
    js = read("pt2vhf_aprs/static/js/v142.js")
    css = read("pt2vhf_aprs/static/css/v142.css")
    assert "const HEAT_RADIUS_METERS = 2500;" in js  # v1.14.53: 5 km de diâmetro
    assert "40075016.686 * Math.cos(lat * Math.PI / 180) / Math.pow(2, zoom + 8)" in js
    assert "['#0000ff'" in js.replace("[0, '#0000ff']", "['#0000ff'") and "[1, '#ff0000']" in js
    assert "ctx.getImageData(0, 0, width, height)" in js
    # A mistura "screen" desbotava as cores sobre o mapa.
    assert "mix-blend-mode" not in css
    app = read("pt2vhf_aprs/static/js/app.js")
    assert 'data-legend="rf-coverage"' in app and ".legend-heat" in read("pt2vhf_aprs/static/css/app.css")


def test_new_version_prompt_opens_once_and_snoozes():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "maybePromptUpdate(data);" in js
    assert "showUpdateModal({ prompt: true });" in js
    assert "const UPDATE_PROMPT_SNOOZE_MS = 24 * 60 * 60 * 1000;" in js
    assert "pt2vhf.updatePromptSnooze." in js
    assert "Deseja atualizar agora? " in js
    # Não sobrepõe outro aviso aberto.
    assert "document.querySelector('.message-alert-overlay:not(.hidden)')" in js
