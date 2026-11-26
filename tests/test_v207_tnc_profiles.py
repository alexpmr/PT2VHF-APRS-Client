"""v2.0.7: perfis de vários TNCs (pergunta de usuário em 26/11/2026)."""
import tempfile
from pathlib import Path

import pytest

from pt2vhf_aprs import database as db, tnc_service
from pt2vhf_aprs.web import create_app


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setattr(db, "DB_PATH", Path(td) / "profiles.db")
        monkeypatch.setattr(tnc_service, "_schema_ready_db_path", None)
        db.init_db()
        yield create_app().test_client()


def test_profiles_save_list_load_delete(client):
    assert client.get("/api/tnc/profiles").get_json()["profiles"] == []
    radio = {**tnc_service.TNC_DEFAULTS, "transport": "serial", "serial_port": "COM7", "serial_baud": 9600}
    soft = {**tnc_service.TNC_DEFAULTS, "transport": "tcp", "tcp_host": "127.0.0.1", "tcp_port": 8001}
    r = client.post("/api/tnc/profiles", json={"name": "  TM-D710   casa ", "config": radio}).get_json()
    assert r["ok"] and r["profile"]["name"] == "TM-D710 casa"
    client.post("/api/tnc/profiles", json={"name": "Dire Wolf", "config": soft})
    names = [p["name"] for p in client.get("/api/tnc/profiles").get_json()["profiles"]]
    assert names == ["Dire Wolf", "TM-D710 casa"]
    summary = {p["name"]: p["summary"] for p in client.get("/api/tnc/profiles").get_json()["profiles"]}
    assert summary["TM-D710 casa"] == "KISS serial COM7 @ 9600"

    loaded = client.post("/api/tnc/profiles/load", json={"name": "tm-d710 CASA"}).get_json()
    assert loaded["ok"] and loaded["config"]["serial_port"] == "COM7"
    assert tnc_service.get_tnc_config()["transport"] == "serial"
    client.post("/api/tnc/profiles/load", json={"name": "Dire Wolf"})
    assert tnc_service.get_tnc_config()["tcp_port"] == 8001

    # Mesmo nome substitui, sem duplicar.
    client.post("/api/tnc/profiles", json={"name": "dire wolf", "config": {**soft, "tcp_port": 8002}})
    profiles = client.get("/api/tnc/profiles").get_json()["profiles"]
    assert len(profiles) == 2 and "8002" in profiles[0]["summary"]

    assert client.post("/api/tnc/profiles/delete", json={"name": "Dire Wolf"}).status_code == 200
    assert client.post("/api/tnc/profiles/load", json={"name": "Dire Wolf"}).status_code == 404


def test_profile_without_config_saves_current_and_validates_name(client):
    tnc_service.save_tnc_config({**tnc_service.TNC_DEFAULTS, "transport": "agwpe", "agwpe_port": 8000})
    r = client.post("/api/tnc/profiles", json={"name": "Atual"}).get_json()
    assert r["profile"]["config"]["transport"] == "agwpe"
    assert client.post("/api/tnc/profiles", json={"name": "  "}).status_code == 400
    assert client.post("/api/tnc/profiles", json={"name": "x" * 41}).status_code == 400


def test_profiles_ui_is_translated_and_wired():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    assert 'id="tncProfilesCard"' in html and "js/tnc_profiles.js" in html
    assert "window.PT2VHF_TNC = { collectConfig" in (root / "pt2vhf_aprs/static/js/tnc.js").read_text(encoding="utf-8")
    from i18n_catalogs import LOCALES, catalog
    for locale in LOCALES:
        for key in ("Perfis de TNC", "Salvar como perfil", "Informe um nome para o perfil."):
            assert key in catalog(locale), (locale, key)
