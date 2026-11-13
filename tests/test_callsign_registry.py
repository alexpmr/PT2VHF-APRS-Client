"""Registro de usuários por indicativo (backlog 13/11/2026), igual ao do PT2VHF Sat Tool v1.8.0.

A consulta de versão envia só o indicativo (update.php?product=aprs&call=PY2XYZ),
ligada por padrão, com opção para desligar; nada é enviado com a estação não
configurada; posição e locator nunca vão na consulta.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs import release_check, web

ROOT = Path(__file__).resolve().parents[1]
STATION = {"callsign": "PY2XYZ", "latitude": -23.5, "longitude": -46.6, "share_callsign_on_update": 1}


def test_callsign_param_and_url():
    assert release_check.callsign_param(" py2xyz ") == "PY2XYZ"
    assert release_check.callsign_param("CT/PY2XYZ/P") == "CT/PY2XYZ/P"
    for bad in ("", None, "PY", "123", "PY2XYZ<script>", "A1" * 9, "PY2 XYZ", "PY2XYZ&x=1", "PY2XYZ-9"):
        assert release_check.callsign_param(bad) == "", bad
    assert release_check.update_url("py2xyz") == release_check.API_URL + "&call=PY2XYZ"
    assert release_check.update_url("CT/PY2XYZ") == release_check.API_URL + "&call=CT%2FPY2XYZ"
    assert release_check.update_url(None) == release_check.API_URL
    assert release_check.API_URL == "https://www.pt2vhf.com/update.php?product=aprs"


def test_station_callsign_rules():
    assert release_check.station_callsign(dict(STATION)) == "PY2XYZ"
    assert release_check.station_callsign(dict(STATION, callsign="py2xyz")) == "PY2XYZ"
    # Opção desligada.
    assert release_check.station_callsign(dict(STATION, share_callsign_on_update=0)) is None
    # Estação não configurada: indicativo vazio, o de exemplo, ou sem latitude/longitude.
    assert release_check.station_callsign(dict(STATION, callsign="")) is None
    assert release_check.station_callsign(dict(STATION, callsign="PT2VHF")) is None
    assert release_check.station_callsign(dict(STATION, latitude=None)) is None
    assert release_check.station_callsign(dict(STATION, longitude="")) is None
    assert release_check.station_callsign(None) is None


def test_python_api_sends_only_the_callsign(monkeypatch):
    seen = {}

    class Response:
        def __init__(self, url):
            self.url = url
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def geturl(self):
            return self.url
        def read(self, _limit):
            raise release_check.ReleaseLookupError("unpublished", "fim do teste")

    class Opener:
        def open(self, req, timeout):
            seen["url"] = req.full_url
            seen["data"] = req.data
            return Response(req.full_url)

    monkeypatch.setattr(release_check.urllib.request, "build_opener", lambda *a: Opener())
    with pytest.raises(release_check.ReleaseLookupError):
        release_check._python_api(callsign="PY2XYZ")
    assert seen["url"] == release_check.API_URL + "&call=PY2XYZ"
    assert seen["data"] is None
    with pytest.raises(release_check.ReleaseLookupError):
        release_check._python_api()
    assert seen["url"] == release_check.API_URL


def test_fetch_passes_callsign_to_windows_fallback(monkeypatch):
    calls = []

    def fail_tls(**kw):
        calls.append(("py", kw))
        raise release_check.ReleaseLookupError("tls", "x")

    def native(**kw):
        calls.append(("win", kw))
        raise release_check.ReleaseLookupError("windows_tls_fallback", "x")

    monkeypatch.setattr(release_check, "_python_api", fail_tls)
    monkeypatch.setattr(release_check, "_windows_native_api", native)
    monkeypatch.setattr(release_check.sys, "platform", "win32")
    monkeypatch.setattr(release_check.time, "sleep", lambda *_: None)
    with pytest.raises(release_check.ReleaseLookupError):
        release_check.fetch_latest_release(callsign="PY2XYZ")
    assert calls and all(kw == {"callsign": "PY2XYZ"} for _, kw in calls)
    assert calls[-1][0] == "win"


@pytest.mark.parametrize("config, expected", [
    (STATION, "PY2XYZ"),
    (dict(STATION, share_callsign_on_update=0), None),
    (dict(STATION, latitude=None, longitude=None), None),
    (dict(STATION, callsign="PT2VHF"), None),
])
def test_update_status_uses_station_callsign(monkeypatch, config, expected):
    seen = {}

    def fake_fetch(callsign=None):
        seen["callsign"] = callsign
        raise release_check.ReleaseLookupError("unpublished", "sem pacote")

    monkeypatch.setattr(web.db, "get_config", lambda: dict(config))
    monkeypatch.setattr(web.release_check, "fetch_latest_release", fake_fetch)
    web.get_update_status(force=True)
    assert seen["callsign"] == expected


def test_config_option_defaults_on_and_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "callsign.db")
    db.init_db()
    assert db.get_config()["share_callsign_on_update"] == 1
    assert db.save_config({"share_callsign_on_update": False})["share_callsign_on_update"] == 0
    assert db.get_config()["share_callsign_on_update"] == 0
    assert db.save_config({"share_callsign_on_update": True})["share_callsign_on_update"] == 1


def test_settings_checkbox_in_updates_section():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    block = html[html.index("<h3>Atualizações</h3>"):]
    block = block[:block.index("</div>\n      </div>")]
    assert 'name="share_callsign_on_update" type="checkbox" checked' in block
    assert "Informar meu indicativo ao consultar versão nova" in block
