"""Windows updater fallback must preserve TLS trust and verify downloaded binaries."""
from __future__ import annotations

import base64
import hashlib
import ssl
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import pytest

from pt2vhf_aprs import updater


def test_windows_native_download_keeps_certificate_validation(monkeypatch, tmp_path):
    downloaded = tmp_path / "update.exe.download"
    payload = b"mock-installer" * 8
    captured = {}

    def fake_run(args, **kwargs):
        script = base64.b64decode(args[-1]).decode("utf-16-le")
        captured["script"] = script
        captured["args"] = args
        downloaded.write_bytes(payload)
        return SimpleNamespace(returncode=0, stderr=b"", stdout=b"")

    monkeypatch.setattr(updater.sys, "platform", "win32")
    monkeypatch.setattr(updater.subprocess, "run", fake_run)

    updater._windows_native_download(
        "https://www.pt2vhf.com/downloads/aprs-client/test.exe",
        downloaded,
    )
    assert downloaded.read_bytes() == payload
    assert "Invoke-WebRequest" in captured["script"]
    assert "Tls12" in captured["script"]
    assert "ServerCertificateValidationCallback" not in captured["script"]
    assert "SkipCertificateCheck" not in captured["script"]
    assert "-EncodedCommand" in captured["args"]


def test_windows_tls_failure_retries_with_native_trust_and_checks_sha256(monkeypatch, tmp_path):
    payload = b"installer-content"
    name = "PT2VHF_APRS_Client_Setup_x64_v1.14.41.exe"
    url = f"https://www.pt2vhf.com/downloads/aprs-client/{name}"
    called = []

    def failing_urlopen(*_args, **_kwargs):
        raise urllib.error.URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))

    def native(url, destination):
        called.append(url)
        destination.write_bytes(payload)

    monkeypatch.setattr(updater.sys, "platform", "win32")
    monkeypatch.setattr(updater.urllib.request, "build_opener", lambda *_a: SimpleNamespace(open=failing_urlopen))
    monkeypatch.setattr(updater, "_windows_native_download", native)
    monkeypatch.setattr(updater, "current_update_mode", lambda: "windows-installer")
    monkeypatch.setattr(updater, "_current_executable_path", lambda: tmp_path / "installed.exe")
    monkeypatch.setattr(updater, "_current_macos_bundle", lambda: None)
    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
    monkeypatch.setattr(updater, "PENDING_FILE", tmp_path / "pending_update.json")
    monkeypatch.setattr(updater.diag, "log_event", lambda *_args, **_kwargs: None)

    result = updater.download_asset("1.14.41", {
        "name": name,
        "url": url,
        "size": len(payload),
        "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
    })
    assert called == [url]
    assert result["sha256"] == hashlib.sha256(payload).hexdigest()
    assert Path(result["path"]).read_bytes() == payload


def test_native_fallback_hash_mismatch_is_rejected(monkeypatch, tmp_path):
    payload = b"incorrect-download"
    name = "PT2VHF_APRS_Client_Setup_x64_v1.14.41.exe"
    url = f"https://www.pt2vhf.com/downloads/aprs-client/{name}"
    monkeypatch.setattr(updater.sys, "platform", "win32")
    monkeypatch.setattr(
        updater.urllib.request, "build_opener",
        lambda *_args: SimpleNamespace(open=lambda *_a, **_k: (_ for _ in ()).throw(
            urllib.error.URLError(ssl.SSLCertVerificationError("certificate error"))
        )),
    )
    monkeypatch.setattr(updater, "_windows_native_download", lambda _url, path: path.write_bytes(payload))
    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
    monkeypatch.setattr(updater, "PENDING_FILE", tmp_path / "pending_update.json")
    monkeypatch.setattr(updater.diag, "log_event", lambda *_args, **_kwargs: None)

    with pytest.raises(ValueError, match="SHA-256"):
        updater.download_asset("1.14.41", {
            "name": name, "url": url, "size": len(payload),
            "digest": "sha256:" + "0" * 64,
        })
    assert not (tmp_path / name).exists()
    assert not (tmp_path / (name + ".download")).exists()


def test_untrusted_windows_tls_fallback_is_not_bypassed(monkeypatch, tmp_path):
    monkeypatch.setattr(updater.sys, "platform", "win32")
    monkeypatch.setattr(
        updater.subprocess, "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stderr=b"untrusted", stdout=b""),
    )
    monkeypatch.setattr(updater.diag, "log_event", lambda *_args, **_kwargs: None)
    with pytest.raises(RuntimeError, match="certificado HTTPS/TLS"):
        updater._windows_native_download(
            "https://www.pt2vhf.com/downloads/aprs-client/test.exe",
            tmp_path / "test.exe.download",
        )
