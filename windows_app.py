from __future__ import annotations

import ctypes
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from PIL import Image
import pystray
from pystray import MenuItem as Item
from waitress import serve

from pt2vhf_aprs import database as db
from pt2vhf_aprs.aprs_service import service
from pt2vhf_aprs.web import create_app

APP_NAME = "PT2VHF APRS Client"
HOST = "127.0.0.1"
PORT = int(os.getenv("PT2VHF_PORT", "8080"))
URL = f"http://{HOST}:{PORT}"
MUTEX_NAME = "Global\\PT2VHF_APRS_Client_SingleInstance"


def _already_running() -> bool:
    if os.name != "nt":
        return False
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS


def _wait_for_server(timeout: float = 12.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def _open_browser(*_args) -> None:
    webbrowser.open(URL, new=2)


def _open_data_folder(*_args) -> None:
    folder = db.DB_PATH.parent
    folder.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(folder)  # type: ignore[attr-defined]


def _connect(*_args) -> None:
    try:
        service.connect()
    except Exception:
        pass


def _disconnect(*_args) -> None:
    try:
        service.disconnect()
    except Exception:
        pass


def _resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def _make_tray_image() -> Image.Image:
    logo = _resource_path("pt2vhf_aprs", "static", "img", "app_logo.png")
    try:
        return Image.open(logo).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
    except Exception:
        return Image.new("RGBA", (64, 64), (15, 23, 30, 255))


def _exit_app(icon: pystray.Icon, *_args) -> None:
    try:
        service.disconnect()
    finally:
        icon.stop()
        os._exit(0)


def main() -> int:
    if _already_running():
        _open_browser()
        return 0

    db.init_db()
    app = create_app()
    service.start_if_configured()

    server_thread = threading.Thread(
        target=lambda: serve(app, host=HOST, port=PORT, threads=8, url_scheme="http"),
        name="pt2vhf-http",
        daemon=True,
    )
    server_thread.start()

    if _wait_for_server():
        _open_browser()

    icon = pystray.Icon(
        "pt2vhf_aprs_client",
        _make_tray_image(),
        APP_NAME,
        menu=pystray.Menu(
            Item("Abrir PT2VHF APRS Client", _open_browser, default=True),
            Item("Conectar ao APRS-IS", _connect),
            Item("Desconectar do APRS-IS", _disconnect),
            pystray.Menu.SEPARATOR,
            Item("Abrir pasta de dados", _open_data_folder),
            pystray.Menu.SEPARATOR,
            Item("Sair", _exit_app),
        ),
    )
    icon.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
