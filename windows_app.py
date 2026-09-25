from __future__ import annotations

import ctypes
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
import pystray
from pystray import MenuItem as Item
from waitress import serve

from pt2vhf_aprs import __version__
from pt2vhf_aprs import database as db
from pt2vhf_aprs import diagnostics as diag
from pt2vhf_aprs.aprs_service import service
from pt2vhf_aprs.web import create_app

APP_NAME = "PT2VHF APRS Client"
HOST = "127.0.0.1"
PORT = int(os.getenv("PT2VHF_PORT", "8080"))
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
    diag.log_event("app_shutdown_requested")
    diag.stop_watchdog()
    try:
        service.shutdown()
    except Exception:
        pass
    try:
        db.shutdown_maintenance()
    except Exception:
        pass

    tray = icon or _tray_icon
    try:
        if tray:
            tray.stop()
    except Exception:
        pass


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
        URL,
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
    global _browser_mode, _tray_icon
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
        diag.dump_threads("local_server_start_timeout")
        if os.name == "nt":
            try:
                ctypes.windll.user32.MessageBoxW(
                    None,
                    "O servidor local do PT2VHF APRS Client não iniciou na porta configurada.",
                    APP_NAME,
                    0x10,
                )
            except Exception:
                pass
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
