"""v1.15.3: aviso "Aplicativo atualizado" só com Fechar; o anúncio segue programado."""
from pathlib import Path

from pt2vhf_aprs import database as db, version_announce as va

ROOT = Path(__file__).resolve().parents[1]


def test_whats_new_has_only_close_button():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    modal = html[html.index('id="whatsNewModal"'):]
    modal = modal[:modal.index("</div>\n</div>")]
    assert modal.count("<button") == 1
    assert '<button id="whatsNewClose" type="button" class="btn primary">Fechar</button>' in modal
    assert "whatsNewSkipAnnounce" not in html and "whatsNewSkipAnnounce" not in js
    assert "es:'Cerrar'" in js and "de:'Schließen'" in js


def test_closing_does_not_cancel_scheduled_announcement(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "close.db")
    db.init_db()
    import aprslib
    raw = "PT2ABC>APRS,TCPIP*,qAC,T2BRAZIL:!1545.00S/04752.80W-casa"
    p = aprslib.parse(raw)
    db.process_received_packet(raw, p, p.get("from"), p.get("format"), medium="APRS-IS")
    assert va.settings()["pending"] is True   # fechar o aviso não chama /skip
