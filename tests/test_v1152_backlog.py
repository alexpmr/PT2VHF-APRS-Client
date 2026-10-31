"""v1.15.2: anúncio no idioma, enlaces mantidos ao limpar estações, botão Enviar Beacon."""
from pathlib import Path

import aprslib
import pytest

from pt2vhf_aprs import __version__, database as db, topology_map, version_announce as va

ROOT = Path(__file__).resolve().parents[1]
DIGI = "PY2DIG-1>APRS,TCPIP*,qAC,T2BRAZIL:!2332.00S/04632.00W#PHG5360/digi"
HOUSE = "PY2FIX>APRS,TCPIP*,qAC,T2BRAZIL:!2335.00S/04635.00W-casa"
HEARD = "PY2FIX>APRS,PY2DIG-1*,WIDE2-1,qAR,PY2IGT:!2335.00S/04635.00W-casa"


def ingest(raw):
    p = aprslib.parse(raw)
    db.process_received_packet(raw, p, p.get("from"), p.get("format"), medium="APRS-IS")


def visible_rf(edges):
    return sorted((e["source"], e["target"]) for e in edges
                  if e.get("kind") == "rf" and e.get("render_on_overview"))


def test_clearing_stations_keeps_links(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "clear.db")
    db.init_db()
    for raw in (DIGI, HOUSE, HEARD):
        ingest(raw)
    with db.connection() as conn:
        edges_before = conn.execute("SELECT COUNT(*) FROM topology_edges").fetchone()[0]
    before = visible_rf(topology_map.list_map_edges(0))
    assert ("PY2FIX", "PY2DIG-1") in before

    deleted = db.clear_stations()
    assert deleted["stations"] >= 2
    assert db.list_stations() == []
    with db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM topology_edges").fetchone()[0] == edges_before
    assert visible_rf(topology_map.list_map_edges(0)) == before


def test_station_that_moved_far_still_hides_inferred_link():
    edge = {"kind": "rf", "source": "A", "target": "B", "source_lat": -23.0, "source_lon": -46.0,
            "target_lat": -23.1, "target_lon": -46.1}
    topology_map.mark_overview_endpoint_coherence([edge], {"A": (-22.0, -43.0)})
    assert edge["render_on_overview"] is False
    topology_map.mark_overview_endpoint_coherence([edge], {})
    assert edge["render_on_overview"] is True


@pytest.mark.parametrize("language,fragment", [
    ("pt-BR", "download em"), ("en", "download at"), ("es", "descarga en"),
    ("fr", "telechargement:"), ("de-DE", "Download:"), ("it-IT", "download su"),
    ("nl-NL", "download via"), ("pl-PL", "pobierz z"), ("ja-JP", "download at"), ("zh-CN", "download at"),
])
def test_announce_text_per_language(language, fragment):
    text = va.default_text(language)
    line = va.render_lines(text, "1.15.10")
    assert len(line) == 1 and len(line[0]) <= va.LINE_LIMIT
    assert fragment in line[0] and line[0].endswith("www.PT2VHF.com") and line[0].isascii()


def test_legacy_default_follows_language_and_custom_text_wins(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "lang.db")
    db.init_db()
    with db.connection() as conn:
        va._ensure_schema(conn)
        va._put(conn, "text", va.LEGACY_DEFAULT_TEXT)
    monkeypatch.setattr(db, "get_config", lambda: {"language": "en"})
    state = va.settings()
    assert state["lines"] == [f"PT2VHF APRS Client v{__version__} - download at www.PT2VHF.com"]
    assert state["default_text"] == va.LANGUAGE_TEXTS["en"]
    va.save_settings({"enabled": True, "text": "Meu texto {versao} {link}"})
    assert va.settings()["lines"] == [f"Meu texto {__version__} www.PT2VHF.com"]


def test_header_beacon_button_and_no_tiny_cc():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert '>Enviar Beacon</button>' in html and "beacon-icon-button" not in html
    assert "tiny.cc" not in html and "tiny.cc" not in js
    assert js.count(": www.PT2VHF.com`") == 10
