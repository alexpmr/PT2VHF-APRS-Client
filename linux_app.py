from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser

from waitress import serve

from pt2vhf_aprs import database as db
from pt2vhf_aprs import updater
from pt2vhf_aprs.aprs_service import service
from pt2vhf_aprs.web import create_app

APP_NAME = "PT2VHF APRS Client"
HOST = "127.0.0.1"
PORT = int(os.getenv("PT2VHF_PORT", "8080"))
URL = f"http://{HOST}:{PORT}"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 700


def _wait_for_server(timeout: float = 12.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def _open_browser() -> None:
    webbrowser.open(URL, new=2)


def _shutdown() -> None:
    try:
        service.disconnect()
    except Exception:
        pass
    try:
        updater.launch_pending_update()
    except Exception:
        pass


def _browser_loop() -> int:
    _open_browser()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()
        return 0


def _run_integrated_window() -> int:
    try:
        import webview
    except Exception:
        return _browser_loop()

    try:
        window = webview.create_window(
            APP_NAME,
            URL,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            min_size=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT),
            resizable=True,
            text_select=True,
        )

        def _on_closing() -> bool:
            _shutdown()
            return True

        window.events.closing += _on_closing
        webview.start(debug=False, private_mode=False)
        _shutdown()
        return 0
    except Exception as exc:
        print(
            "A janela integrada não pôde ser iniciada; usando o navegador local. "
            f"Detalhes: {exc}",
            file=sys.stderr,
        )
        return _browser_loop()


def main() -> int:
    db.init_db()
    app = create_app()
    service.start_if_configured()

    server_thread = threading.Thread(
        target=lambda: serve(app, host=HOST, port=PORT, threads=8, url_scheme="http"),
        name="pt2vhf-http",
        daemon=True,
    )
    server_thread.start()

    if not _wait_for_server():
        print(
            f"O servidor local do {APP_NAME} não iniciou em {HOST}:{PORT}.",
            file=sys.stderr,
        )
        return 2

    if "--browser" in sys.argv[1:]:
        return _browser_loop()

    try:
        if bool(db.get_config().get("open_browser_on_start")):
            _open_browser()
    except Exception:
        pass

    return _run_integrated_window()


if __name__ == "__main__":
    raise SystemExit(main())
