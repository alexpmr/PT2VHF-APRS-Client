"""v1.14.59: anúncio automático da versão na primeira abertura após atualizar."""
import aprslib

from pt2vhf_aprs import __version__, database as db, version_announce as va


class FakeService:
    def __init__(self, connected=True, verified=True):
        self.state = {"connected": connected, "verified": verified}
        self.sent = []

    def status(self):
        return dict(self.state)

    def send_bulletin(self, text, bulletin_id="0", group=""):
        self.sent.append((bulletin_id, text))


LATER = 10 ** 9  # bem depois do atraso de 2 minutos


def existing_install():
    raw = "PT2ABC>APRS,TCPIP*,qAC,T2BRAZIL:!1545.00S/04752.80W-casa"
    p = aprslib.parse(raw)
    db.process_received_packet(raw, p, p.get("from"), p.get("format"), medium="APRS-IS")


def test_default_text_fits_one_bulletin():
    lines = va.render_lines(va.DEFAULT_TEXT)
    assert lines == [f"PT2VHF APRS Client v{__version__} - download em www.PT2VHF.com"]
    assert len(lines[0]) <= 67


def test_update_announces_once(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "up.db")
    db.init_db()
    existing_install()                     # banco já usado: veio de versão anterior
    svc = FakeService()
    assert va.maybe_announce(svc, now=va._started_at) == "waiting_delay"
    assert va.maybe_announce(svc, now=LATER) == "sent"
    assert svc.sent == [("A", va.render_lines(va.DEFAULT_TEXT)[0])]
    assert va.maybe_announce(svc, now=LATER) == "not_pending"
    assert len(svc.sent) == 1


def test_fresh_install_never_announces(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "fresh.db")
    db.init_db()
    svc = FakeService()
    assert va.maybe_announce(svc, now=LATER) == "not_pending"
    assert svc.sent == []


def test_waits_for_verified_aprs_is_and_respects_skip_and_disable(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "skip.db")
    db.init_db()
    existing_install()
    assert va.maybe_announce(FakeService(verified=False), now=LATER) == "waiting_aprs_is"
    va.save_settings({"enabled": False, "text": va.DEFAULT_TEXT})
    assert va.maybe_announce(FakeService(), now=LATER) == "not_pending"
    va.save_settings({"enabled": True, "text": "Novo {versao} {link}"})
    assert va.settings()["lines"] == [f"Novo {__version__} www.PT2VHF.com"]
    va.skip_current()
    svc = FakeService()
    assert va.maybe_announce(svc, now=LATER) == "not_pending" and svc.sent == []


def test_next_version_after_announcement_is_pending_again(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "next.db")
    db.init_db()
    existing_install()
    va.maybe_announce(FakeService(), now=LATER)
    monkeypatch.setattr(va, "__version__", "9.9.9")
    svc = FakeService()
    assert va.maybe_announce(svc, now=LATER) == "sent"
    assert "v9.9.9" in svc.sent[0][1]


def test_station_list_carries_map_role_for_view_filters(tmp_path, monkeypatch):
    """v1.14.59: o Ver de Mensagens/Estações contava 0 digis e 0 iGates."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "roles.db")
    db.init_db()
    for raw in ["PY2DIG-1>APRS,TCPIP*,qAC,T2BRAZIL:!2332.00S/04632.00W#PHG5360/digi",
                "PY2IG>APRS,TCPIP*,qAC,T2BRAZIL:!2333.00S/04633.00WI igate"]:
        p = aprslib.parse(raw)
        db.process_received_packet(raw, p, p.get("from"), p.get("format"), medium="APRS-IS")
    roles = {s["callsign"]: s["map_role"] for s in db.list_stations("")}
    assert roles == {"PY2DIG-1": "digi", "PY2IG": "igate"}
    first = db.resolve_aprs_device_id("APDW16")
    first["features"].append("x")                   # cache não pode vazar mutação
    assert "x" not in db.resolve_aprs_device_id("APDW16")["features"]
