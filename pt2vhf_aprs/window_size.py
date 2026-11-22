"""Tamanho inicial da janela do app (v2.0.3, relato PU2MUS em tela 1366x768).

A janela abria com 1400x850 e mínimo de 1100x700, maior que uma tela 1366x768
(que, tirando a barra de tarefas, tem uns 1366x728 úteis). Agora o tamanho é
limitado à tela principal e, em telas pequenas, a janela já abre maximizada.
"""
from __future__ import annotations

from typing import Any

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 600
# Folga para barra de tarefas/Dock e barra de título.
SCREEN_MARGIN_W = 40
SCREEN_MARGIN_H = 100


def primary_screen_size(webview_module: Any) -> tuple[int, int] | None:
    try:
        screens = list(getattr(webview_module, "screens", None) or [])
        if screens:
            return int(screens[0].width), int(screens[0].height)
    except Exception:
        pass
    return None


def window_geometry(screen: tuple[int, int] | None) -> dict[str, Any]:
    """Argumentos width/height/min_size/maximized para webview.create_window."""
    if not screen or screen[0] <= 0 or screen[1] <= 0:
        return {"width": WINDOW_WIDTH, "height": WINDOW_HEIGHT,
                "min_size": (WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT), "maximized": False}
    sw, sh = screen
    fits = sw >= WINDOW_WIDTH + SCREEN_MARGIN_W and sh >= WINDOW_HEIGHT + SCREEN_MARGIN_H
    width = min(WINDOW_WIDTH, max(640, sw - SCREEN_MARGIN_W))
    height = min(WINDOW_HEIGHT, max(480, sh - SCREEN_MARGIN_H))
    return {
        "width": width,
        "height": height,
        "min_size": (min(WINDOW_MIN_WIDTH, width), min(WINDOW_MIN_HEIGHT, height)),
        "maximized": not fits,
    }


def create_window_kwargs(webview_module: Any) -> dict[str, Any]:
    return window_geometry(primary_screen_size(webview_module))
