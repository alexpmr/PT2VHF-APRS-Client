"""Atualizador PT2VHF: manifesto e downloads exclusivamente de www.pt2vhf.com."""
from __future__ import annotations

import base64
import json
import re
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_URL = "https://www.pt2vhf.com/update.php?product=aprs"
WEB_URL = "https://www.pt2vhf.com/aprs"
ORIGIN = "https://www.pt2vhf.com"
HEADERS = {"Accept": "application/json", "User-Agent": "PT2VHF-APRS-Client-Updater"}
HASH_RE = re.compile(r"[0-9a-f]{64}")


class ReleaseLookupError(RuntimeError):
    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(detail)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ReleaseLookupError("redirect", "Redirecionamento bloqueado na atualização.")


def classify_error(exc: BaseException) -> ReleaseLookupError:
    if isinstance(exc, ReleaseLookupError):
        return exc
    if isinstance(exc, urllib.error.HTTPError):
        return ReleaseLookupError("http_%d" % exc.code, "Site PT2VHF respondeu HTTP %d." % exc.code)
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, (ssl.SSLError, ssl.CertificateError)):
        return ReleaseLookupError("tls", "Falha no certificado HTTPS/TLS: %s" % type(reason).__name__)
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return ReleaseLookupError("timeout", "Tempo esgotado ao consultar o site PT2VHF.")
    if isinstance(reason, socket.gaierror):
        return ReleaseLookupError("dns", "Falha ao resolver www.pt2vhf.com (DNS).")
    if isinstance(reason, (ConnectionError, OSError)):
        return ReleaseLookupError("network", "Falha na rede para PT2VHF: %s" % type(reason).__name__)
    if isinstance(exc, (ValueError, UnicodeError)):
        return ReleaseLookupError("invalid_response", "Resposta inválida do site PT2VHF.")
    return ReleaseLookupError("unknown", "Falha no site PT2VHF: %s" % type(exc).__name__)


def is_official_asset(url: str, name: str) -> bool:
    try:
        info = urllib.parse.urlsplit(url)
        return (
            info.scheme == "https" and info.netloc == "www.pt2vhf.com"
            and info.path.startswith("/downloads/aprs-client/")
            and info.path.rsplit("/", 1)[-1] == name
            and not info.query and not info.fragment and "%" not in info.path
            and bool(re.fullmatch(r"[A-Za-z0-9_.-]+", name))
            and name.endswith((".exe", ".AppImage", ".deb", ".tar.gz", ".dmg", ".zip"))
        )
    except (TypeError, ValueError, AttributeError):
        return False


def validate_release(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ReleaseLookupError("invalid_response", "Manifesto não é JSON válido de esquema 1.")
    if data.get("product") != "aprs" or data.get("source") != ORIGIN:
        raise ReleaseLookupError("invalid_source", "O manifesto não pertence ao APRS Client.")
    if data.get("status") == "unpublished":
        raise ReleaseLookupError("unpublished", "Ainda não há instalador APRS público validado no site.")
    version = data.get("version")
    if data.get("status") != "available" or not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ReleaseLookupError("invalid_version", "Versão publicada inválida.")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise ReleaseLookupError("invalid_assets", "Nenhum arquivo publicado.")
    assets = []
    for entry in files:
        if not isinstance(entry, dict):
            raise ReleaseLookupError("invalid_assets", "Arquivo de manifesto inválido.")
        name, url = entry.get("name"), entry.get("url")
        size, sha = entry.get("size"), entry.get("sha256")
        if not isinstance(name, str) or not isinstance(url, str) or not is_official_asset(url, name):
            raise ReleaseLookupError("invalid_assets", "URL externa ou arquivo inválido.")
        if type(size) is not int or size <= 0 or not isinstance(sha, str) or not HASH_RE.fullmatch(sha):
            raise ReleaseLookupError("invalid_assets", "Tamanho ou SHA-256 inválidos.")
        assets.append({"name": name, "browser_download_url": url, "size": size, "digest": "sha256:" + sha})
    return {"tag_name": "v" + version, "html_url": WEB_URL, "body": str(data.get("notes") or ""), "assets": assets}


def _python_api(timeout: float = 7.0) -> dict[str, Any]:
    req = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=timeout) as res:
        if res.geturl() != API_URL:
            raise ReleaseLookupError("redirect", "Endereço inesperado de atualização.")
        raw = res.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ReleaseLookupError("invalid_response", "Manifesto excede limite de tamanho.")
    return validate_release(json.loads(raw.decode("utf-8")))


def _windows_native_api(timeout: int = 12) -> dict[str, Any]:
    if sys.platform != "win32":
        raise ReleaseLookupError("fallback_unavailable", "Fallback de TLS disponível só no Windows.")
    script = (
        "$ErrorActionPreference='Stop';"
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
        "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;"
        "$r=Invoke-RestMethod -Uri '" + API_URL + "' -Method Get -MaximumRedirection 0 "
        "-TimeoutSec " + str(int(timeout)) + " -Headers @{'User-Agent'='PT2VHF-APRS-Client-Updater'};"
        "$r | ConvertTo-Json -Depth 12 -Compress"
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        response = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True, timeout=int(timeout) + 5, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseLookupError("windows_tls_fallback", "Consulta HTTPS nativa não respondeu.") from exc
    if response.returncode:
        raise ReleaseLookupError("windows_tls_fallback", "Consulta HTTPS nativa falhou.")
    try:
        return validate_release(json.loads(response.stdout.decode("utf-8-sig")))
    except (UnicodeError, ValueError, ReleaseLookupError) as exc:
        raise ReleaseLookupError("windows_tls_fallback", "Resposta HTTPS nativa inválida.") from exc


def fetch_latest_release() -> tuple[dict[str, Any], str]:
    failures: list[ReleaseLookupError] = []
    for attempt in range(2):
        try:
            return _python_api(), "pt2vhf_site"
        except Exception as exc:
            issue = classify_error(exc)
            failures.append(issue)
            if issue.code not in ("timeout", "dns", "network", "tls", "http_500", "http_502", "http_503", "http_504"):
                break
            if attempt == 0:
                time.sleep(0.5)
    if sys.platform == "win32" and failures and failures[0].code == "tls":
        try:
            return _windows_native_api(), "windows_system_tls"
        except Exception as exc:
            failures.append(classify_error(exc))
    raise failures[0] if failures else ReleaseLookupError("unknown", "Falha desconhecida.")
