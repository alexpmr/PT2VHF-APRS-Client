from __future__ import annotations

import ctypes
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse

from PIL import Image
import pystray
from pystray import MenuItem as Item

from pt2vhf_aprs import __version__
from pt2vhf_aprs import database as db
from pt2vhf_aprs import diagnostics as diag
from pt2vhf_aprs import updater
from pt2vhf_aprs.aprs_service import service
from pt2vhf_aprs.tnc_service import service as tnc_service
from pt2vhf_aprs.local_server import (
    configured_start_port,
    read_runtime_url,
    runtime_file_for,
    start_local_server,
)
from pt2vhf_aprs.web import create_app

APP_NAME = "PT2VHF APRS Client"
HOST = "127.0.0.1"
PORT = configured_start_port()
URL = f"http://{HOST}:{PORT}"
MUTEX_NAME = "Global\\PT2VHF_APRS_Client_SingleInstance"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 850
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 700

_window = None
_tray_icon: pystray.Icon | None = None
_browser_mode = False
_quitting = False
_server_handle = None


def _already_running() -> bool:
    if os.name != "nt":
        return False
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS


def _focus_existing_window() -> bool:
    if os.name != "nt":
        return False
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, APP_NAME)
        if not hwnd:
            return False
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


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


def _current_url() -> str:
    if _server_handle is not None:
        return _server_handle.url
    discovered = read_runtime_url(db.DB_PATH.parent)
    return discovered or URL


def _open_browser(*_args) -> None:
    webbrowser.open(_current_url(), new=2)


def _open_external_url(url: str) -> bool:
    try:
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme not in {"http", "https", "mailto"}:
            return False
        webbrowser.open(url, new=2)
        return True
    except Exception:
        return False


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
    candidates = [
        _resource_path("windows", "app_icon.ico"),
        _resource_path("pt2vhf_aprs", "static", "img", "app_logo.png"),
    ]
    for logo in candidates:
        try:
            return Image.open(logo).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
        except Exception:
            continue
    return Image.new("RGBA", (64, 64), (15, 23, 30, 255))


def _show_native_window(*_args) -> None:
    global _window
    if _browser_mode or _window is None:
        _open_browser()
        return

    try:
        _window.show()
    except Exception:
        pass

    # O WebView2 pode estar minimizado; força restore/foco pela janela nativa.
    def _focus() -> None:
        time.sleep(0.08)
        _focus_existing_window()

    threading.Thread(target=_focus, name="pt2vhf-focus-window", daemon=True).start()


def _shutdown_components(icon: pystray.Icon | None = None) -> None:
    """Encerra os componentes de fundo antes de finalizar o processo."""
    global _server_handle
    diag.log_event("app_shutdown_requested")
    diag.stop_watchdog()
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
    except Exception:
        pass
    try:
        if _server_handle is not None:
            _server_handle.close()
    except Exception:
        pass
    _server_handle = None

    tray = icon or _tray_icon
    try:
        if tray:
            tray.stop()
    except Exception:
        pass


def _exit_for_update() -> None:
    """Encerra sem confirmação depois que o helper de atualização já foi iniciado."""
    global _quitting
    _quitting = True
    _shutdown_components()
    os._exit(0)


def _exit_app(icon: pystray.Icon | None = None, *_args) -> None:
    global _quitting
    if _quitting:
        return
    _quitting = True
    _shutdown_components(icon)

    if _window is not None:
        try:
            _window.destroy()
            return
        except Exception:
            pass

    # No modo --browser não há janela WebView para encerrar o loop principal.
    os._exit(0)


def _confirm_exit() -> bool:
    if os.name != "nt":
        return True
    try:
        # MB_YESNO | MB_ICONQUESTION | MB_DEFBUTTON2
        flags = 0x00000004 | 0x00000020 | 0x00000100
        result = ctypes.windll.user32.MessageBoxW(
            None,
            "Deseja realmente sair do PT2VHF APRS Client?",
            APP_NAME,
            flags,
        )
        return result == 6  # IDYES
    except Exception:
        return True


def _on_window_closing() -> bool:
    """O X pede confirmação e, se aprovado, encerra toda a aplicação."""
    global _quitting
    if _quitting:
        return True

    if not _confirm_exit():
        return False

    _quitting = True
    _shutdown_components()
    return True


def _create_tray_icon() -> pystray.Icon:
    return pystray.Icon(
        "pt2vhf_aprs_client",
        _make_tray_image(),
        APP_NAME,
        menu=pystray.Menu(
            Item("Abrir PT2VHF APRS Client", _show_native_window, default=True),
            Item("Conectar ao APRS-IS", _connect),
            Item("Desconectar do APRS-IS", _disconnect),
            pystray.Menu.SEPARATOR,
            Item("Abrir pasta de dados", _open_data_folder),
            pystray.Menu.SEPARATOR,
            Item("Sair", _exit_app),
        ),
    )


class NativeApi:
    """Ponte mínima entre a interface WebView e ações nativas seguras."""

    def open_external(self, url: str) -> bool:
        return _open_external_url(url)

    def open_data_folder(self) -> bool:
        try:
            _open_data_folder()
            return True
        except Exception:
            return False

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
            path = Path(str(selected))
            if path.suffix.lower() != ".kml":
                path = path.with_suffix(".kml")
            path.write_text(str(content or ""), encoding="utf-8")
            return {"saved": True, "path": str(path)}
        except Exception as exc:
            return {"saved": False, "error": str(exc)}


def _run_browser_mode(icon: pystray.Icon) -> int:
    _open_browser()
    icon.run()
    return 0


def _run_embedded_window(icon: pystray.Icon) -> int:
    global _window

    try:
        import webview
    except Exception:
        return _run_browser_mode(icon)

    _window = webview.create_window(
        APP_NAME,
        _current_url(),
        js_api=NativeApi(),
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT),
        resizable=True,
        text_select=True,
    )
    _window.events.closing += _on_window_closing

    tray_thread = threading.Thread(
        target=icon.run,
        name="pt2vhf-tray",
        daemon=True,
    )
    tray_thread.start()

    try:
        # EdgeChromium usa o Microsoft Edge WebView2 Runtime do Windows.
        webview.start(gui="edgechromium", debug=False, private_mode=False)
        _shutdown_components()
        return 0
    except Exception as exc:
        # Fallback de diagnóstico: mantém a aplicação utilizável mesmo se o
        # WebView2 Runtime estiver ausente ou danificado.
        try:
            if os.name == "nt":
                ctypes.windll.user32.MessageBoxW(
                    None,
                    "Não foi possível iniciar a janela integrada do PT2VHF APRS Client.\n\n"
                    "A interface será aberta no navegador padrão.\n\n"
                    f"Detalhes: {exc}",
                    APP_NAME,
                    0x30,
                )
        except Exception:
            pass
        _open_browser()
        tray_thread.join()
        return 0


def main() -> int:
    global _browser_mode, _tray_icon, _server_handle, PORT, URL
    _browser_mode = "--browser" in sys.argv[1:]

    if _already_running():
        if _browser_mode:
            _open_browser()
        elif not _focus_existing_window():
            # A instância existente pode estar em modo --browser ou em fallback
            # por indisponibilidade do WebView2.
            _open_browser()
        return 0

    diag.configure(db.DB_PATH.parent)
    diag.log_event("app_start", version=__version__, portable=True)
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
        diag.log_event(
            "local_server_started",
            host=HOST,
            port=PORT,
            url=URL,
            fallback_count=_server_handle.fallback_count,
        )
        print(f"{APP_NAME} — Interface local: {HOST}:{PORT}")
    except Exception as exc:
        diag.log_event("local_server_start_failed", error=str(exc))
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                "Não foi possível reservar uma porta local para o PT2VHF APRS Client.\n\n"
                f"Detalhes: {exc}",
                APP_NAME,
                0x10,
            )
        except Exception:
            pass
        return 2

    if not _wait_for_server():
        diag.dump_threads("local_server_start_timeout")
        return 2

    diag.start_watchdog(URL)

    if not _browser_mode:
        try:
            if bool(db.get_config().get("open_browser_on_start")):
                _open_browser()
        except Exception:
            pass

    _tray_icon = _create_tray_icon()

    if _browser_mode:
        return _run_browser_mode(_tray_icon)

    return _run_embedded_window(_tray_icon)


if __name__ == "__main__":
    raise SystemExit(main())
