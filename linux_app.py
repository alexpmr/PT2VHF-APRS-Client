from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen


from pt2vhf_aprs import database as db
from pt2vhf_aprs import updater
from pt2vhf_aprs.aprs_service import service
from pt2vhf_aprs.tnc_service import service as tnc_service
from pt2vhf_aprs.local_server import configured_start_port, runtime_file_for, start_local_server
from pt2vhf_aprs.web import create_app

APP_NAME = "PT2VHF APRS Client"
HOST = "127.0.0.1"
PORT = configured_start_port()
URL = f"http://{HOST}:{PORT}"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 700

_window = None
_server_handle = None


def _wait_for_server(timeout: float = 12.0) -> bool:
    if _server_handle is not None:
        return bool(_server_handle.wait_ready(timeout))
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
    global _server_handle
    try:
        service.shutdown()
    except Exception:
        pass
    try:
        tnc_service.shutdown()
    except Exception:
        pass
    try:
        db.shutdown_maintenance()
    except Exception as exc:
        print(f"Falha na manutenção de encerramento: {exc}", file=sys.stderr)
    try:
        if _server_handle is not None:
            _server_handle.close()
    except Exception:
        pass
    _server_handle = None


def _exit_for_update() -> None:
    _shutdown()
    os._exit(0)


class NativeApi:
    """Bridge for native desktop file dialogs used by the web UI."""

    def save_local_download(self, relative_url: str, filename: str) -> dict:
        """Salva um download gerado pelo backend local usando diálogo nativo."""
        try:
            import webview
            global _window, URL
            if _window is None:
                return {"saved": False, "error": "Janela integrada indisponível."}
            route = str(relative_url or "").strip()
            allowed = {"/api/v190/backup/full"}
            if route not in allowed:
                return {"saved": False, "error": "Rota de download não autorizada."}

            suggested = Path(str(filename or "PT2VHF_APRS_Client_Backup.zip")).name
            if not suggested.lower().endswith(".zip"):
                suggested += ".zip"
            selected = _window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested,
                file_types=("Arquivo ZIP (*.zip)", "Todos os arquivos (*.*)"),
            )
            if not selected:
                return {"saved": False, "cancelled": True}
            if isinstance(selected, (list, tuple)):
                selected = selected[0] if selected else ""
            target = Path(str(selected))
            if target.suffix.lower() != ".zip":
                target = target.with_suffix(".zip")

            local_url = str(URL).rstrip("/") + route
            with urlopen(local_url, timeout=180) as response, target.open("wb") as output:
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    total += len(chunk)
            if total <= 0:
                try:
                    target.unlink(missing_ok=True)
                except Exception:
                    pass
                return {"saved": False, "error": "O servidor retornou um backup vazio."}
            return {"saved": True, "path": str(target), "bytes": total}
        except Exception as exc:
            return {"saved": False, "error": str(exc)}

    def save_text_file(self, filename: str, content: str) -> dict:
        try:
            import webview
            global _window
            if _window is None:
                return {"saved": False, "error": "Janela integrada indisponível."}
            suggested = Path(str(filename or "PT2VHF_APRS_Client_export.kml")).name
            if not suggested.lower().endswith(".kml"):
                suggested += ".kml"
            selected = _window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested,
                file_types=("KML (*.kml)", "Todos os arquivos (*.*)"),
            )
            if not selected:
                return {"saved": False, "cancelled": True}
            if isinstance(selected, (list, tuple)):
                selected = selected[0] if selected else ""
            target = Path(str(selected))
            if target.suffix.lower() != ".kml":
                target = target.with_suffix(".kml")
            target.write_text(str(content or ""), encoding="utf-8")
            return {"saved": True, "path": str(target)}
        except Exception as exc:
            return {"saved": False, "error": str(exc)}


def _browser_loop() -> int:
    _open_browser()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()
        return 0


def _run_integrated_window() -> int:
    global _window
    try:
        import webview
    except Exception:
        return _browser_loop()

    try:
        _window = webview.create_window(
            APP_NAME,
            URL,
            js_api=NativeApi(),
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            min_size=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT),
            resizable=True,
            text_select=True,
        )

        def _on_closing() -> bool:
            _shutdown()
            return True

        _window.events.closing += _on_closing
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
    global _server_handle, PORT, URL
    updater.register_exit_handler(_exit_for_update)
    db.init_db()
    app = create_app()
    service.start_if_configured()
    tnc_service.start_if_configured()

    try:
        _server_handle = start_local_server(
            app,
            host=HOST,
            start_port=PORT,
            runtime_file=runtime_file_for(db.DB_PATH.parent),
        )
        PORT = int(_server_handle.port)
        URL = _server_handle.url
        print(f"{APP_NAME} — Interface local: {HOST}:{PORT}")
    except Exception as exc:
        print(f"Não foi possível reservar uma porta local para {APP_NAME}: {exc}", file=sys.stderr)
        return 2

    if not _wait_for_server():
        print(f"O servidor local do {APP_NAME} não respondeu em {HOST}:{PORT}.", file=sys.stderr)
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
