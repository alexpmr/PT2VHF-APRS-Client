"""Base aprs-deviceid (https://github.com/aprsorg/aprs-deviceid): equipamento/software das estações.

O app traz uma cópia embutida em ``data/aprs_device_ids.json`` e, como os mantenedores recomendam,
busca a versão nova uma vez por semana (em horário sorteado) e guarda na pasta de dados do usuário.
Além do TOCALL (destino), reconhece rádios Mic-E (Yaesu, Kenwood e outros) pelo sufixo do comentário.

Licença da base: CC BY-SA 2.0 (créditos no Sobre / THIRD_PARTY_NOTICES).
"""
from __future__ import annotations

import json
import random
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import __version__

SOURCE_URLS = (
    "https://aprs-deviceid.aprsfoundation.org/tocalls.yaml",
    "https://raw.githubusercontent.com/aprsorg/aprs-deviceid/main/tocalls.yaml",
)
REFRESH_SECONDS = 7 * 24 * 3600
USER_FILE_NAME = "aprs_device_ids.json"
MIN_TOCALLS = 300  # uma base menor que isso veio truncada ou errada

# Identificador experimental usado até o registro oficial (faixa APZ).
LOCAL_OVERRIDES = [
    {
        "tocall": "APZVHF",
        "vendor": "PT2VHF",
        "model": "PT2VHF APRS Client",
        "class": "software",
        "os": "Cross-platform",
        "features": ["messaging"],
        "local_override": True,
    },
]

_SECTIONS = ("classes", "mice", "micelegacy", "tocalls")


def _scalar(text: str) -> str:
    text = text.strip()
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        return json.loads(text)
    if text.startswith("'") and text.endswith("'") and len(text) >= 2:
        return text[1:-1].replace("''", "'")
    return text


def parse_tocalls_yaml(text: str) -> dict[str, list[dict[str, Any]]]:
    """Lê o tocalls.yaml sem depender do PyYAML.

    O arquivo tem formato fixo: quatro seções, cada uma lista de mapas com valores simples e,
    no campo ``features``, uma sublista. Linhas de comentário começam com ``#``.
    """
    out: dict[str, list[dict[str, Any]]] = {name: [] for name in _SECTIONS}
    section: str | None = None
    item: dict[str, Any] | None = None
    list_key: str | None = None
    for raw_line in str(text or "").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "---":
            continue
        if not line.startswith(" ") and stripped.endswith(":"):
            name = stripped[:-1]
            section = name if name in out else None
            item = None
            list_key = None
            continue
        if section is None:
            continue
        indent = len(line) - len(line.lstrip(" "))
        if stripped.startswith("- ") and list_key and item is not None and indent > 2:
            item.setdefault(list_key, []).append(_scalar(stripped[2:]))
            continue
        if stripped.startswith("- "):
            item = {}
            out[section].append(item)
            list_key = None
            stripped = stripped[2:].strip()
        if item is None or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        if value.strip():
            item[key] = _scalar(value)
            list_key = None
        else:
            item[key] = []
            list_key = key
    return out


def build_snapshot(parsed: dict[str, list[dict[str, Any]]], source: str) -> dict[str, Any]:
    tocalls = [dict(entry) for entry in parsed.get("tocalls", []) if entry.get("tocall")]
    known = {str(entry["tocall"]).upper() for entry in tocalls}
    entries = [dict(item) for item in LOCAL_OVERRIDES if item["tocall"] not in known] + tocalls
    return {
        "source": "https://github.com/aprsorg/aprs-deviceid",
        "source_file": "tocalls.yaml",
        "source_url": source,
        "license": "CC BY-SA 2.0",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Snapshot for offline friendly-name resolution. APZVHF is a local experimental identifier "
                "for PT2VHF APRS Client.",
        "entries": entries,
        "mice": [dict(entry) for entry in parsed.get("mice", []) if entry.get("suffix")],
        "micelegacy": [dict(entry) for entry in parsed.get("micelegacy", []) if entry.get("prefix")],
        "classes": [dict(entry) for entry in parsed.get("classes", []) if entry.get("class")],
    }


def snapshot_is_valid(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("entries"), list)
        and len(payload["entries"]) >= MIN_TOCALLS
        and all(isinstance(item, dict) and item.get("tocall") for item in payload["entries"])
    )


# --------------------------------------------------------------------------- Mic-E

MICE_DATA_TYPES = ("`", "'", "\x1c", "\x1d")


def mice_info_field(raw: str) -> str:
    """Campo de informação de um pacote Mic-E (ou "" se não for Mic-E)."""
    line = str(raw or "").rstrip("\r\n")
    if ">" not in line or ":" not in line:
        return ""
    info = line.split(":", 1)[1]
    return info if info[:1] in MICE_DATA_TYPES else ""


def resolve_mice(raw: str, mice: list[dict[str, Any]], legacy: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Identifica o rádio Mic-E pelo comentário (regras do README do aprs-deviceid).

    Depois do tipo de dado vêm 8 bytes (longitude, velocidade/rumo, símbolo). O comentário começa
    com o prefixo de tipo (`` ` ``/``'`` no novo formato, ``>``/``]`` nos Kenwood antigos) e o
    novo formato termina com o sufixo de 2 caracteres do fabricante.
    """
    info = mice_info_field(raw)
    if len(info) < 9:
        return None
    comment = info[9:].rstrip("\r\n")
    if not comment:
        return None
    prefix = comment[0]
    if prefix in ("`", "'") and len(comment) >= 3:
        suffix = comment[-2:]
        for entry in mice:
            if entry.get("suffix") == suffix:
                found = dict(entry)
                if prefix == "`":
                    found["features"] = sorted(set(found.get("features") or []) | {"messaging"})
                return found
        return None
    if prefix in (">", "]"):
        last = comment[-1] if len(comment) > 1 else ""
        best = None
        for entry in legacy:
            if entry.get("prefix") != prefix:
                continue
            suffix = entry.get("suffix")
            if suffix and suffix == last:
                return dict(entry)
            if not suffix and best is None:
                best = dict(entry)
        return best
    return None


# --------------------------------------------------------------------------- atualização semanal

def user_snapshot_path(data_dir: Path) -> Path:
    return Path(data_dir) / USER_FILE_NAME


def _download(url: str, timeout: float = 20.0) -> str:
    try:
        from .release_check import https_handler
        opener = urllib.request.build_opener(https_handler())
    except Exception:
        opener = urllib.request.build_opener()
    request = urllib.request.Request(url, headers={"User-Agent": f"PT2VHF-APRS-Client/{__version__}"})
    with opener.open(request, timeout=timeout) as response:
        data = response.read(2_000_000)
    return data.decode("utf-8")


def refresh_now(data_dir: Path, downloader: Callable[[str], str] = _download) -> dict[str, Any]:
    """Baixa a base nova e grava na pasta de dados. Devolve um resumo (ok, entries, error)."""
    errors = []
    for url in SOURCE_URLS:
        try:
            snapshot = build_snapshot(parse_tocalls_yaml(downloader(url)), url)
        except Exception as exc:  # rede, proxy, TLS ou arquivo inválido: tenta a próxima fonte
            errors.append(f"{url}: {exc}")
            continue
        if not snapshot_is_valid(snapshot):
            errors.append(f"{url}: base incompleta ({len(snapshot.get('entries') or [])} itens)")
            continue
        target = user_snapshot_path(data_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(target)
        return {"ok": True, "entries": len(snapshot["entries"]), "mice": len(snapshot["mice"]), "source": url}
    return {"ok": False, "error": "; ".join(errors)}


def refresh_due(data_dir: Path, now: float | None = None) -> bool:
    target = user_snapshot_path(data_dir)
    try:
        age = (now if now is not None else time.time()) - target.stat().st_mtime
    except OSError:
        return True
    return age >= REFRESH_SECONDS


def start_weekly_refresh(
    data_dir: Path,
    enabled: Callable[[], bool],
    on_updated: Callable[[], None],
    log: Callable[..., None] | None = None,
) -> threading.Thread:
    """Thread de fundo: confere a cada 6 h se a cópia tem mais de 7 dias; a primeira conferência
    sai num horário sorteado (5 a 60 min após abrir) para não sincronizar todos os clientes."""

    def loop() -> None:
        time.sleep(random.uniform(300, 3600))
        while True:
            try:
                if enabled() and refresh_due(data_dir):
                    result = refresh_now(data_dir)
                    if log:
                        log("aprs_device_ids_refresh", **result)
                    if result.get("ok"):
                        on_updated()
            except Exception as exc:  # nunca derrubar o app por causa disso
                if log:
                    log("aprs_device_ids_refresh_failed", error=str(exc))
            time.sleep(6 * 3600 + random.uniform(0, 1800))

    thread = threading.Thread(target=loop, name="aprs-deviceid-refresh", daemon=True)
    thread.start()
    return thread
