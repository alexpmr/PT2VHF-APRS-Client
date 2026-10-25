"""Anúncio da versão por boletim APRS após atualizar o cliente (v1.14.59).

Na primeira abertura de cada versão nova (nunca numa instalação nova), envia
uma única vez o Announcement BLNA pelo APRS-IS verificado, no mesmo formato da
divulgação manual da aba Sobre, por exemplo
"Estou usando PT2VHF APRS Client v1.14.59 - Download: tiny.cc/aprs".
Espera ANNOUNCE_DELAY_SECONDS após abrir o aplicativo para o operador poder
cancelar no aviso de novidades; desligável em Automações.
"""
from __future__ import annotations

import threading
import time
from typing import Any

from . import __version__
from . import database as db
from . import diagnostics as diag

DOWNLOAD_LINK = "tiny.cc/aprs"  # mesmo link curto da divulgação manual (aba Sobre)
DEFAULT_TEXT = "Estou usando PT2VHF APRS Client v{versao} - Download: {link}"
BULLETIN_IDS = ("A",)              # BLNA, como a divulgação manual; uma linha
LINE_LIMIT = 67                    # texto máximo de um boletim APRS
ANNOUNCE_DELAY_SECONDS = 120
CHECK_SECONDS = 60

_lock = threading.Lock()
_thread: threading.Thread | None = None
_started_at = time.monotonic()


def _ensure_schema(conn) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS version_announce (
        key TEXT PRIMARY KEY, value TEXT NOT NULL)""")


def _get(conn, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM version_announce WHERE key=?", (key,)).fetchone()
    return str(row[0]) if row else default


def _put(conn, key: str, value: Any) -> None:
    conn.execute("INSERT INTO version_announce(key,value) VALUES(?,?) "
                 "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))


def render_lines(template: str, version: str | None = None) -> list[str]:
    """Texto do anúncio em linhas de boletim (quebra entre palavras)."""
    version = version or __version__
    text = " ".join(str(template or DEFAULT_TEXT).replace("{versao}", version)
                    .replace("{version}", version).replace("{link}", DOWNLOAD_LINK).split())
    lines: list[str] = []
    words = text.split(" ")
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= LINE_LIMIT:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word[:LINE_LIMIT]
        if len(lines) == len(BULLETIN_IDS):
            break
    if current and len(lines) < len(BULLETIN_IDS):
        lines.append(current)
    return lines[:len(BULLETIN_IDS)]


def _existing_install(conn) -> bool:
    cfg = db.get_config()
    if str(cfg.get("callsign") or "").strip():
        return True
    return bool(conn.execute("SELECT 1 FROM stations LIMIT 1").fetchone())


def settings() -> dict[str, Any]:
    with db.connection() as conn:
        _ensure_schema(conn)
        if not _get(conn, "seen_version"):
            # Primeira execução com este recurso: banco já usado = atualização.
            _put(conn, "seen_version", "anterior" if _existing_install(conn) else __version__)
        enabled = _get(conn, "enabled", "1") == "1"
        template = _get(conn, "text", DEFAULT_TEXT)
        announced = _get(conn, "announced_version")
        skipped = _get(conn, "skipped_version")
        seen = _get(conn, "seen_version")
    pending = bool(enabled and seen != __version__ and announced != __version__ and skipped != __version__)
    return {
        "enabled": enabled, "text": template, "default_text": DEFAULT_TEXT,
        "lines": render_lines(template), "version": __version__, "link": DOWNLOAD_LINK,
        "announced_version": announced, "skipped_version": skipped,
        "pending": pending, "delay_seconds": ANNOUNCE_DELAY_SECONDS,
    }


def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(str(payload.get("text") or DEFAULT_TEXT).split())
    if not render_lines(text):
        raise ValueError("Texto do anúncio vazio.")
    with db.connection() as conn:
        _ensure_schema(conn)
        _put(conn, "enabled", "1" if payload.get("enabled", True) else "0")
        _put(conn, "text", text)
    return settings()


def skip_current() -> dict[str, Any]:
    """Operador não quer anunciar esta versão."""
    with db.connection() as conn:
        _ensure_schema(conn)
        _put(conn, "skipped_version", __version__)
    diag.log_event("version_announce_skipped", version=__version__)
    return settings()


def maybe_announce(service: Any, *, now: float | None = None) -> str:
    """Envia o anúncio se for a hora. Retorna o motivo/resultado (para testes e log)."""
    with _lock:
        state = settings()
        if not state["pending"]:
            return "not_pending"
        if (now if now is not None else time.monotonic()) - _started_at < ANNOUNCE_DELAY_SECONDS:
            return "waiting_delay"
        status = service.status()
        if not status.get("connected") or not status.get("verified"):
            return "waiting_aprs_is"
        for bulletin_id, line in zip(BULLETIN_IDS, state["lines"]):
            service.send_bulletin(line, bulletin_id=bulletin_id)
        with db.connection() as conn:
            _put(conn, "announced_version", __version__)
            _put(conn, "seen_version", __version__)
        diag.log_event("version_announce_sent", version=__version__, lines=state["lines"])
        return "sent"


def _worker(service: Any) -> None:
    db_path = db.DB_PATH
    while True:
        time.sleep(CHECK_SECONDS)
        if db.DB_PATH != db_path:
            return  # banco trocado (testes/restauração): não tocar no novo arquivo daqui
        try:
            if maybe_announce(service) in {"sent", "not_pending"}:
                return
        except Exception as exc:
            diag.log_event("version_announce_error", error=str(exc))


def start_worker(service: Any) -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    try:
        settings()  # registra a versão vista antes de qualquer envio
    except Exception as exc:
        diag.log_event("version_announce_error", error=str(exc))
    _thread = threading.Thread(target=_worker, args=(service,), daemon=True, name="version-announce")
    _thread.start()
