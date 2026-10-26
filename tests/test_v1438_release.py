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
    assert "edge.kind === 'igate' ? state.mapConfig.topology_igate_color" in segment
    assert "dashArray: edge.kind === 'igate' ? '7 5' : mobileRf ? '2 5' : null" in segment
    assert "style.dashArray = '5 7'" not in segment
    assert "style.dashArray = '2 5'" not in segment
    assert "inferredRouteEdge && topologyEdgeDistanceKm(geometryEdge) > 250" in segment
    assert "RF inferido (não confirmado diretamente)" in js
    assert "line._pt2vhfEdge" in js


@pytest.mark.parametrize(("exc", "expected"), [
    (ssl.SSLCertVerificationError("untrusted"), "tls"),
    (urllib.error.URLError(socket.gaierror("dns")), "dns"),
    (urllib.error.URLError(socket.timeout("timed out")), "timeout"),
    (urllib.error.HTTPError(release_check.API_URL, 403, "Forbidden", {}, None), "http_403"),
    (urllib.error.HTTPError(release_check.API_URL, 502, "Bad Gateway", {}, None), "http_502"),
])
def test_network_error_codes(exc, expected):
    assert release_check.classify_error(exc).code == expected


def manifest(version="1.14.59", host="www.pt2vhf.com"):
    name = f"PT2VHF_APRS_Client_Setup_x64_v{version}.exe"
    return {
        "schema": 1, "source": "https://www.pt2vhf.com", "product": "aprs",
        "status": "available", "version": version,
        "page": "https://www.pt2vhf.com/aprs",
        "files": [{"name": name, "url": f"https://{host}/downloads/aprs-client/{name}",
                   "size": 100, "sha256": "a" * 64}],
    }


def test_site_normalizes_existing_update_contract():
    release = release_check.validate_release(manifest())
    assert release["tag_name"] == "v1.14.59"
    assert release["assets"][0]["digest"] == "sha256:" + "a" * 64


@pytest.mark.parametrize("host", ["github.com", "gitlab.com", "evil.pt2vhf.com"])
def test_external_downloads_rejected(host):
    with pytest.raises(release_check.ReleaseLookupError, match="URL externa"):
        release_check.validate_release(manifest(host=host))


def test_invalid_hash_and_unpublished_rejected():
    info = manifest()
    info["files"][0]["sha256"] = "no"
    with pytest.raises(release_check.ReleaseLookupError):
        release_check.validate_release(info)
    info = manifest()
    info.update(status="unpublished", version=None, files=[])
    with pytest.raises(release_check.ReleaseLookupError) as err:
        release_check.validate_release(info)
    assert err.value.code == "unpublished"


def test_windows_tls_fallback_keeps_official_site(monkeypatch):
    def fail_tls():
        raise urllib.error.URLError(ssl.SSLCertVerificationError("untrusted"))
    monkeypatch.setattr(release_check, "_python_api", fail_tls)
    monkeypatch.setattr(release_check, "_windows_native_api", lambda: release_check.validate_release(manifest()))
    monkeypatch.setattr(release_check.sys, "platform", "win32")
    monkeypatch.setattr(release_check.time, "sleep", lambda *_: None)
    release, source = release_check.fetch_latest_release()
    assert source == "windows_system_tls"
    assert release["tag_name"] == "v1.14.59"


def test_redirects_blocked():
    with pytest.raises(release_check.ReleaseLookupError):
        release_check.NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://gitlab.com")


def test_unpublished_status_is_not_false_latest(monkeypatch):
    def unpublished():
        raise release_check.ReleaseLookupError("unpublished", "Sem pacote público")
    monkeypatch.setattr(web.release_check, "fetch_latest_release", unpublished)
    result = web.get_update_status(force=True)
    assert result["status"] == "unpublished" and not result["update_available"]


def test_site_release_with_package_enables_update(monkeypatch):
    monkeypatch.setattr(web.release_check, "fetch_latest_release",
                        lambda: (release_check.validate_release(manifest("99.0.0")), "pt2vhf_site"))
    monkeypatch.setattr(web.updater, "current_update_mode", lambda: "windows-installer")
    monkeypatch.setattr(web.updater, "_machine", lambda: "x86_64")
    monkeypatch.setattr(web.updater, "pending_update", lambda: None)
    result = web.get_update_status(force=True)
    assert result["status"] == "update_available" and result["asset_ready"]
    assert result["asset_digest"].startswith("sha256:")


def test_frontend_still_displays_errors_and_unpublished():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "data.status === 'unpublished'" in js
    assert "controller.abort(), 45000" in js
    assert "Falha na verificação:" in js

def test_no_false_upgrade_when_package_for_other_platform(monkeypatch):
    data = manifest("99.0.0")
    data["files"][0]["name"] = "PT2VHF_APRS_Client_Portable_x64_v99.0.0.exe"
    data["files"][0]["url"] = "https://www.pt2vhf.com/downloads/aprs-client/PT2VHF_APRS_Client_Portable_x64_v99.0.0.exe"
    monkeypatch.setattr(web.release_check, "fetch_latest_release",
                        lambda: (release_check.validate_release(data), "pt2vhf_site"))
    monkeypatch.setattr(web.updater, "current_update_mode", lambda: "windows-installer")
    monkeypatch.setattr(web.updater, "_machine", lambda: "x86_64")
    monkeypatch.setattr(web.updater, "pending_update", lambda: None)
    result = web.get_update_status(force=True)
    assert result["status"] == "unavailable_platform"
    assert result["update_available"] is False
    assert result["asset_ready"] is False

