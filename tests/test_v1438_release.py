"""Regressões v1.14.38: RF sólido e consulta de Releases no Windows 10."""
from __future__ import annotations

import json
import socket
import ssl
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import pytest

from pt2vhf_aprs import release_check, web


ROOT = Path(__file__).resolve().parents[1]


def test_rf_style_depends_on_medium_not_evidence_level():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    begin = js.index("const inferredRouteEdge = edge.kind !== 'igate'")
    end = js.index("if (!line) {", begin)
    segment = js[begin:end]
    assert "edge.kind === 'igate' ? state.mapConfig.topology_igate_color : state.mapConfig.topology_rf_color" in segment
    assert "dashArray: edge.kind === 'igate' ? '7 5' : null" in segment
    assert "style.dashArray = '5 7'" not in segment
    assert "style.dashArray = '2 5'" not in segment
    assert "inferredRouteEdge && topologyEdgeDistanceKm(geometryEdge) > 250" in segment
    assert "RF inferido (não confirmado diretamente)" in js
    assert "line._pt2vhfEdge" in js


@pytest.mark.parametrize(("exc", "expected"), [
    (ssl.SSLCertVerificationError("untrusted"), "tls"),
    (urllib.error.URLError(socket.gaierror("dns")), "dns"),
    (urllib.error.URLError(socket.timeout("timed out")), "timeout"),
    (urllib.error.HTTPError(release_check.API_URL, 403, "Forbidden", {}, None), "rate_limit"),
    (urllib.error.HTTPError(release_check.API_URL, 502, "Bad Gateway", {}, None), "http_502"),
])
def test_specific_network_error_codes(exc, expected):
    result = release_check.classify_error(exc)
    assert result.code == expected


def test_validates_release_metadata_strictly():
    assert release_check.validate_release({"tag_name": "v1.14.38", "assets": []})["tag_name"] == "v1.14.38"
    for payload in [None, [], {"tag_name": "not-version", "assets": []}, {"tag_name": "v1.14.38", "assets": {}}]:
        with pytest.raises(release_check.ReleaseLookupError):
            release_check.validate_release(payload)


def test_python_https_success_uses_api(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return json.dumps({"tag_name": "v1.14.38", "assets": []}).encode()

    seen = []
    def urlopen(request, timeout):
        seen.append((request.full_url, timeout))
        return Response()

    monkeypatch.setattr(release_check.urllib.request, "urlopen", urlopen)
    release, source = release_check.fetch_latest_release()
    assert source == "github_api"
    assert release["tag_name"] == "v1.14.38"
    assert seen == [(release_check.API_URL, 7.0)]


def test_windows_native_fallback_after_python_certificate_failure(monkeypatch):
    def bad_python(*_args, **_kwargs):
        raise urllib.error.URLError(ssl.SSLCertVerificationError("untrusted"))

    called = []
    def native():
        called.append(True)
        return {"tag_name": "v1.14.38", "assets": []}

    monkeypatch.setattr(release_check, "_python_api", bad_python)
    monkeypatch.setattr(release_check, "_windows_native_api", native)
    monkeypatch.setattr(release_check, "_github_web_tag", lambda: pytest.fail("web fallback unnecessary"))
    monkeypatch.setattr(release_check.sys, "platform", "win32")
    monkeypatch.setattr(release_check.time, "sleep", lambda _: None)
    release, source = release_check.fetch_latest_release()
    assert source == "windows_system_tls"
    assert called == [True]
    assert release["tag_name"] == "v1.14.38"


def test_powershell_native_fallback_does_not_disable_certificate_verification(monkeypatch):
    monkeypatch.setattr(release_check.sys, "platform", "win32")
    captures = []
    def fake_run(cmd, **kwargs):
        captures.append((cmd, kwargs))
        return SimpleNamespace(returncode=0, stdout=b'{"tag_name":"v1.14.38","assets":[]}')

    monkeypatch.setattr(release_check.subprocess, "run", fake_run)
    assert release_check._windows_native_api()["tag_name"] == "v1.14.38"
    assert captures[0][0][0] == "powershell.exe"
    assert "-EncodedCommand" in captures[0][0]
    assert captures[0][1]["timeout"] >= 12
    import base64
    ps = base64.b64decode(captures[0][0][-1]).decode("utf-16-le")
    assert "[Net.SecurityProtocolType]::Tls12" in ps
    assert "Invoke-RestMethod" in ps
    assert "ServerCertificateValidationCallback" not in ps
    assert "trustAllCerts" not in ps


def test_web_page_fallback_only_confirms_version_not_assets(monkeypatch):
    class Redirect:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return "https://github.com/alexpmr/PT2VHF-APRS-Client/releases/tag/v1.14.38"

    monkeypatch.setattr(release_check.urllib.request, "urlopen", lambda *args, **kwargs: Redirect())
    value = release_check._github_web_tag()
    assert value["tag_name"] == "v1.14.38"
    assert value["assets"] == []
    assert value["limited_metadata"] is True


def test_status_reports_missing_assets_without_false_install_ready(monkeypatch):
    monkeypatch.setattr(web.release_check, "fetch_latest_release", lambda: (
        {"tag_name": "v99.0.0", "html_url": release_check.WEB_URL, "assets": [], "limited_metadata": True},
        "github_release_page",
    ))
    monkeypatch.setattr(web.updater, "pending_update", lambda: None)
    monkeypatch.setattr(web.updater, "select_asset", lambda *_args: None)
    result = web.get_update_status(force=True)
    assert result["status"] == "update_available"
    assert result["latest_version"] == "99.0.0"
    assert result["limited_metadata"] is True
    assert result["asset_ready"] is False
    assert "não puderam ser consultados" in result["error"]


def test_status_error_includes_code_and_never_pretends_latest(monkeypatch):
    def bad_lookup():
        raise release_check.ReleaseLookupError("tls", "Certificado TLS não confiável.")

    monkeypatch.setattr(web.release_check, "fetch_latest_release", bad_lookup)
    result = web.get_update_status(force=True)
    assert result["status"] == "error"
    assert result["error_code"] == "tls"
    assert result["update_available"] is False
    assert "Certificado TLS" in result["error"]


def test_frontend_shows_error_details_and_longer_timeout():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "controller.abort(), 45000" in js
    assert "state.updateInfo?.error_code" in js
    assert "Falha na verificação:" in js
