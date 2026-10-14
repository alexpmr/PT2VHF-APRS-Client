"""Consulta segura e diagnosticável da última Release GitHub.

O HTTPS padrão do Python é preferencial. No Windows há fallback pela pilha
TLS/certificados do próprio sistema (PowerShell/.NET), sem desativar validação.
Como último recurso a página oficial confirma apenas o tag, nunca os assets.
"""
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
import urllib.request
from typing import Any

API_URL = "https://api.github.com/repos/alexpmr/PT2VHF-APRS-Client/releases/latest"
WEB_URL = "https://github.com/alexpmr/PT2VHF-APRS-Client/releases/latest"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "PT2VHF-APRS-Client-Updater",
    "X-GitHub-Api-Version": "2022-11-28",
}


class ReleaseLookupError(RuntimeError):
    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(detail)


def classify_error(exc: BaseException) -> ReleaseLookupError:
    if isinstance(exc, ReleaseLookupError):
        return exc
    if isinstance(exc, urllib.error.HTTPError):
        status = int(exc.code)
        if status in (403, 429):
            return ReleaseLookupError("rate_limit", "GitHub respondeu HTTP %d (limite de acesso ou bloqueio)." % status)
        return ReleaseLookupError("http_%d" % status, "GitHub respondeu HTTP %d." % status)
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, (ssl.SSLError, ssl.CertificateError)):
        return ReleaseLookupError("tls", "Falha de validação do certificado HTTPS/TLS: %s" % type(reason).__name__)
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return ReleaseLookupError("timeout", "Tempo esgotado ao consultar o GitHub.")
    if isinstance(reason, socket.gaierror):
        return ReleaseLookupError("dns", "Não foi possível resolver o endereço do GitHub (DNS).")
    if isinstance(reason, (ConnectionError, OSError)):
        return ReleaseLookupError("network", "Falha de conexão com o GitHub: %s" % type(reason).__name__)
    if isinstance(exc, (ValueError, json.JSONDecodeError)):
        return ReleaseLookupError("invalid_response", "Resposta inválida do serviço de Releases.")
    return ReleaseLookupError("unknown", "Falha ao consultar GitHub: %s" % type(exc).__name__)


def validate_release(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ReleaseLookupError("invalid_response", "Resposta de release não é um objeto JSON.")
    tag = str(data.get("tag_name") or "").strip()
    if not re.fullmatch(r"v?\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.-]+)?", tag):
        raise ReleaseLookupError("invalid_tag", "Release retornou uma tag de versão inválida.")
    assets = data.get("assets", [])
    if not isinstance(assets, list):
        raise ReleaseLookupError("invalid_response", "Lista de pacotes da Release é inválida.")
    return data


def _python_api(timeout: float = 7.0) -> dict[str, Any]:
    request = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content = response.read(2_000_000)
    return validate_release(json.loads(content.decode("utf-8")))


def _windows_native_api(timeout: int = 12) -> dict[str, Any]:
    """Usa o repositório de certificados e proxy do Windows quando o Python falha."""
    if sys.platform != "win32":
        raise ReleaseLookupError("fallback_unavailable", "Fallback TLS nativo disponível apenas no Windows.")
    script = (
        "$ErrorActionPreference='Stop';"
        "[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false);"
        "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;"
        "$r=Invoke-RestMethod -Uri '" + API_URL + "' -Method Get "
        "-TimeoutSec " + str(int(timeout)) + " -Headers @{'User-Agent'='PT2VHF-APRS-Client-Updater'};"
        "$r | ConvertTo-Json -Depth 12 -Compress"
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True, timeout=int(timeout) + 5, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseLookupError("windows_tls_fallback", "Consulta HTTPS nativa do Windows não respondeu (%s)." % type(exc).__name__) from exc
    if result.returncode:
        raise ReleaseLookupError("windows_tls_fallback", "Consulta HTTPS nativa do Windows retornou erro (PowerShell).")
    try:
        return validate_release(json.loads(result.stdout.decode("utf-8-sig")))
    except (UnicodeError, ValueError, ReleaseLookupError) as exc:
        raise ReleaseLookupError("windows_tls_fallback", "Resposta da consulta HTTPS nativa não pôde ser validada.") from exc


def _github_web_tag(timeout: float = 6.0) -> dict[str, Any]:
    """Fallback limitado: o redirect do site oficial comprova a tag, não assets."""
    request = urllib.request.Request(WEB_URL, headers={"User-Agent": HEADERS["User-Agent"]})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        resolved = response.geturl()
    match = re.search(r"/releases/tag/(v?\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.-]+)?)", resolved)
    if not match:
        raise ReleaseLookupError("invalid_tag", "Página oficial não indicou tag de release.")
    tag = match.group(1)
    return validate_release({
        "tag_name": tag, "html_url": resolved, "body": "", "assets": [],
        "limited_metadata": True,
    })


def fetch_latest_release() -> tuple[dict[str, Any], str]:
    failures: list[ReleaseLookupError] = []
    for attempt in range(2):
        try:
            return _python_api(), "github_api"
        except Exception as exc:
            issue = classify_error(exc)
            failures.append(issue)
            if issue.code not in ("timeout", "dns", "network", "tls", "http_500", "http_502", "http_503", "http_504"):
                break
            if attempt == 0:
                time.sleep(0.5)

    if sys.platform == "win32":
        try:
            return _windows_native_api(), "windows_system_tls"
        except Exception as exc:
            failures.append(classify_error(exc))

    try:
        return _github_web_tag(), "github_release_page"
    except Exception as exc:
        failures.append(classify_error(exc))

    original = failures[0] if failures else ReleaseLookupError("unknown", "Falha desconhecida.")
    raise ReleaseLookupError(
        original.code,
        "%s Tentativas alternativas não obtiveram confirmação da versão." % str(original),
    )
