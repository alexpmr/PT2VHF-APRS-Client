"""Aviso do sistema operacional para mensagem recebida (v2.0.7).

A interface chama /api/notify quando chega mensagem para a estação e a janela não está em foco.
Windows: balão da bandeja (pystray, o ícone que o app já cria). Linux: notify-send (libnotify).
macOS: osascript "display notification". Sem nenhum desses, não faz nada (o aviso na tela continua).
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import threading
import time
from typing import Any, Callable

APP_NAME = "PT2VHF APRS Client"
_tray_notifier: Callable[[str, str], None] | None = None
_last_sent = 0.0
_lock = threading.Lock()
MIN_INTERVAL_SECONDS = 2.0


def register_tray_notifier(func: Callable[[str, str], None] | None) -> None:
    """windows_app registra icon.notify(mensagem, título) do ícone da bandeja."""
    global _tray_notifier
    _tray_notifier = func


def _clean(text: Any, limit: int) -> str:
    return " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split())[:limit]


def _run(cmd: list[str]) -> bool:
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, close_fds=True)
        return True
    except Exception:
        return False


def _applescript_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def method() -> str:
    system = platform.system()
    if system == "Windows":
        return "tray" if _tray_notifier else "none"
    if system == "Darwin":
        return "osascript" if shutil.which("osascript") else "none"
    return "notify-send" if shutil.which("notify-send") else "none"


def notify(title: Any, body: Any) -> dict[str, Any]:
    global _last_sent
    title_text = _clean(title, 80) or APP_NAME
    body_text = _clean(body, 240)
    with _lock:
        now = time.monotonic()
        if now - _last_sent < MIN_INTERVAL_SECONDS:
            return {"ok": False, "reason": "rate_limited"}
        _last_sent = now
    how = method()
    sent = False
    if how == "tray" and _tray_notifier:
        try:
            _tray_notifier(body_text or title_text, title_text)
            sent = True
        except Exception:
            sent = False
    elif how == "osascript":
        script = f"display notification {_applescript_string(body_text)} with title {_applescript_string(title_text)}"
        sent = _run(["osascript", "-e", script])
    elif how == "notify-send":
        sent = _run(["notify-send", "--app-name", APP_NAME, "--icon", "mail-message-new", title_text, body_text])
    return {"ok": sent, "method": how}
