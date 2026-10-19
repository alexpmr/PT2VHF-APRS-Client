"""<div id="map"> vira window.map (elemento DOM) antes de o Leaflet criar o
mapa; os complementos AIS devem esperar um mapa Leaflet real."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ais_enhancements_require_leaflet_map_not_dom_element():
    v110 = (ROOT / "pt2vhf_aprs/static/js/v110.js").read_text(encoding="utf-8")
    v142 = (ROOT / "pt2vhf_aprs/static/js/v142.js").read_text(encoding="utf-8")
    assert "if(typeof window.map?.on!=='function'||window.__v110AisBound)return;" in v110
    assert "if(!window.map||window.__v110AisBound)return;" not in v110
    assert "return typeof map?.on === 'function' ? map : null;" in v142
