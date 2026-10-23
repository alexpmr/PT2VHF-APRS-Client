from __future__ import annotations

import ctypes
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
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
    read_runtime_browser_url,
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
_legacy_shell_process = None


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
    """Show the LAN IPv4 when reachable; keep localhost for internal checks."""
    if _server_handle is not None:
        if _server_handle.scope == "lan" and _server_handle.lan_host:
            try:
                with socket.create_connection(
                    (_server_handle.lan_host, _server_handle.port), timeout=0.35
                ):
                    return _server_handle.share_url
            except OSError:
                pass
        return _server_handle.url
    discovered = read_runtime_browser_url(db.DB_PATH.parent)
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
    """Opaque, high-contrast APRS badge for the Windows notification area.

    ICO frames used for executable shortcuts are often rescaled by pystray.
    Draw a dedicated notification image so transparent padding or a missing
    resource cannot turn the running application's indicator invisible.
    """
    side = 64
    try:
        img = Image.new("RGBA", (side, side), (12, 35, 53, 255))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((1, 1, 62, 62), radius=12,
                            fill=(11, 35, 53, 255),
                            outline=(117, 227, 255, 255), width=5)
        d.rectangle((9, 7, 54, 14), fill=(255, 196, 53, 255))
        chosen = None
        for font_size in range(29, 13, -1):
            for path in ("arialbd.ttf", "segoeuib.ttf",
                         "DejaVuSans-Bold.ttf"):
                try:
                    font = ImageFont.truetype(path, font_size)
                    left, top, right, bottom = d.textbbox(
                        (0, 0), "APRS", font=font
                    )
                    if right - left <= 55 and bottom - top <= 34:
                        chosen = (font, left, top, right, bottom)
                        break
                except OSError:
                    pass
            if chosen:
                break
        if chosen:
            font, left, top, right, bottom = chosen
            x = (side - (right - left)) // 2 - left
            y = 21 + (32 - (bottom - top)) // 2 - top
            d.text((x, y), "APRS", font=font, fill=(255, 255, 255, 255))
        else:
            # Deliberately visible fallback, even without system fonts.
            font = ImageFont.load_default()
            d.text((11, 28), "APRS", font=font, fill=(255, 255, 255, 255))
        diag.log_event("tray_icon_loaded", source="drawn_aprs_badge",
                       size="64x64", alpha="opaque")
        return img
    except Exception as exc:
        diag.log_event("tray_icon_generation_failed", error=str(exc))

    for logo in (
        _resource_path("windows", "app_icon.ico"),
        _resource_path("pt2vhf_aprs", "static", "img", "app_logo.png"),
    ):
        try:
            with Image.open(logo) as src:
                out = src.convert("RGBA").resize(
                    (64, 64), Image.Resampling.LANCZOS
                )
                diag.log_event("tray_icon_loaded", source=str(logo),
                               size=str(src.size), alpha=str(out.getextrema()[3]))
                return out
        except Exception as exc:
            diag.log_event("tray_icon_resource_failed", source=str(logo),
                           error=str(exc))
    diag.log_event("tray_icon_fallback", reason="all sources unavailable")
    return Image.new("RGBA", (64, 64), (16, 71, 93, 255))


def _mark_updated_instance_ready() -> None:
    """Tell an update helper that the replacement actually booted its HTTP API."""
    marker = str(os.environ.pop("PT2VHF_UPDATE_READY_MARKER", "") or "").strip()
    if not marker:
        return
    try:
        path = Path(marker).resolve()
        expected_dir = (db.DB_PATH.parent / "updates").resolve()
        if path.parent != expected_dir or path.name != "update_ready.flag":
            raise ValueError("unsafe ready marker path")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ready version={} pid={}\\n".format(__version__, os.getpid()),
                        encoding="ascii")
        diag.log_event("update_relaunch_confirmed", version=__version__,
                       pid=os.getpid())
    except Exception as exc:
        diag.log_event("update_relaunch_marker_failed", error=str(exc))


def _show_native_window(*_args) -> None:
    global _window
    if os.getenv("PT2VHF_WIN7_LEGACY") == "1" and not _browser_mode:
        _launch_legacy_app_window()
        return
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

    def save_binary_file(self, filename: str, data_base64: str) -> dict:
        """Salva um PDF gerado pela interface (planejamento) com diálogo nativo."""
        try:
            import base64
            import webview
            global _window
            if _window is None:
                return {"saved": False, "error": "Janela integrada indisponível."}
            if not isinstance(data_base64, str) or len(data_base64) > 30_000_000:
                return {"saved": False, "error": "Arquivo grande demais."}
            data = base64.b64decode(data_base64, validate=True)
            if not data.startswith(b"%PDF-"):
                return {"saved": False, "error": "Somente PDF é aceito."}
            suggested = Path(str(filename or "PT2VHF_APRS_Client.pdf")).name
            if not suggested.lower().endswith(".pdf"):
                suggested += ".pdf"
            selected = _window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested,
                file_types=("PDF (*.pdf)", "Todos os arquivos (*.*)"),
            )
            if not selected:
                return {"saved": False, "cancelled": True}
            if isinstance(selected, (list, tuple)):
                selected = selected[0] if selected else ""
            target = Path(str(selected))
            if target.suffix.lower() != ".pdf":
                target = target.with_suffix(".pdf")
            target.write_bytes(data)
            return {"saved": True, "path": str(target)}
        except Exception as exc:
            return {"saved": False, "error": str(exc)}

    def save_text_file(self, filename: str, content: str) -> dict:
        try:
            import webview
            global _window
            if _window is None:
                return {"saved": False, "error": "Janela integrada indisponível."}

            suggested = Path(str(filename or "PT2VHF_APRS_Client_export.txt")).name
            suffix = Path(suggested).suffix.lower() or ".txt"
            if suffix == ".kml":
                file_types = ("KML (*.kml)", "Todos os arquivos (*.*)")
            elif suffix == ".json":
                file_types = ("JSON (*.json)", "Todos os arquivos (*.*)")
            else:
                file_types = ("Arquivo de texto (*.txt)", "Todos os arquivos (*.*)")

            selected = _window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested,
                file_types=file_types,
            )
            if not selected:
                return {"saved": False, "cancelled": True}
            if isinstance(selected, (list, tuple)):
                selected = selected[0] if selected else ""
            target = Path(str(selected))
            if target.suffix.lower() != suffix:
                target = target.with_suffix(suffix)
            target.write_text(str(content or ""), encoding="utf-8")
            return {"saved": True, "path": str(target)}
        except Exception as exc:
            return {"saved": False, "error": str(exc)}



def _legacy_browser_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_paths = [
        os.getenv("PROGRAMFILES"),
        os.getenv("PROGRAMFILES(X86)"),
        os.getenv("LOCALAPPDATA"),
    ]
    relative = [
        Path("Google/Chrome/Application/chrome.exe"),
        Path("Chromium/Application/chrome.exe"),
        Path("BraveSoftware/Brave-Browser/Application/brave.exe"),
    ]
    for base in env_paths:
        if not base:
            continue
        for rel in relative:
            path = Path(base) / rel
            if path not in candidates:
                candidates.append(path)
    return candidates


def _find_legacy_app_browser() -> Path | None:
    for path in _legacy_browser_candidates():
        try:
            if path.is_file():
                return path
        except Exception:
            continue
    return None


def _launch_legacy_app_window() -> bool:
    global _legacy_shell_process
    url = _current_url()
    browser = _find_legacy_app_browser()
    diag.log_event(
        "win7_legacy_shell_probe",
        version=__version__,
        executable=str(sys.executable),
        browser=str(browser or ""),
        url=url,
        argv=list(sys.argv),
        windows=platform.platform(),
        machine=platform.machine(),
        python=sys.version,
    )
    if browser is None:
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                "O Windows 7 Legacy não encontrou Google Chrome/Chromium/Brave compatível para a janela dedicada.\n\n"
                "A interface será aberta no navegador padrão, mantendo o PT2VHF APRS Client ativo na bandeja.",
                APP_NAME,
                0x30,
            )
        except Exception:
            pass
        diag.log_event("win7_legacy_shell_fallback_browser", reason="compatible_app_browser_not_found")
        return bool(webbrowser.open(url, new=2))

    profile_dir = db.DB_PATH.parent / "win7-shell-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    args = [
        str(browser),
        f"--app={url}",
        "--new-window",
        "--disable-background-mode",
        "--no-first-run",
        "--disable-default-apps",
        f"--user-data-dir={profile_dir}",
    ]
    try:
        _legacy_shell_process = subprocess.Popen(
            args,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        diag.log_event(
            "win7_legacy_shell_started",
            browser=str(browser),
            pid=_legacy_shell_process.pid,
            url=url,
        )
        time.sleep(0.8)
        exit_code = _legacy_shell_process.poll()
        if exit_code == 0:
            # Chromium may forward --app to an existing browser process and exit
            # the short-lived launcher successfully. This is not an update error.
            diag.log_event("win7_legacy_shell_handoff", exit_code=0, browser=str(browser),
                           profile_dir=str(profile_dir), url=url, pid=_legacy_shell_process.pid)
            return True
        if exit_code is not None:
            raise RuntimeError(f"Shell encerrou imediatamente (exit={exit_code}).")
        return True
    except Exception as exc:
        diag.log_event("win7_legacy_shell_failed", browser=str(browser), error=str(exc), url=url)
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                "Não foi possível iniciar a janela dedicada do Windows 7 Legacy.\n\n"
                "A interface será aberta no navegador padrão e o backend continuará ativo.\n\n"
                f"Detalhes: {exc}",
                APP_NAME,
                0x30,
            )
        except Exception:
            pass
        return bool(webbrowser.open(url, new=2))


def _run_legacy_app_shell(icon: pystray.Icon) -> int:
    if not _launch_legacy_app_window():
        diag.log_event("win7_legacy_shell_no_window", url=_current_url())
    icon.run()
    return 0


def _run_browser_mode(icon: pystray.Icon) -> int:
    _open_browser()
    icon.run()
    return 0


def _run_embedded_window(icon: pystray.Icon) -> int:
    global _window

    try:
        import webview
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
    except Exception as exc:
        diag.log_event("embedded_window_create_failed", error=str(exc),
                       fallback="default_browser")
        return _run_browser_mode(icon)

    tray_thread = threading.Thread(
        target=icon.run,
        name="pt2vhf-tray",
        daemon=True,
    )
    tray_thread.start()

    gui = str(os.getenv("PT2VHF_WEBVIEW_GUI", "edgechromium") or "edgechromium").strip()
    try:
        webview.start(gui=gui, debug=False, private_mode=False)
        _shutdown_components()
        return 0
    except Exception as exc:
        legacy = os.getenv("PT2VHF_WIN7_LEGACY") == "1"
        netfx_failure = (
            "default .net runtime" in str(exc).lower()
            or "pythonnet" in str(exc).lower()
            or "set_runtime_from_env" in str(exc).lower()
        )
        diag.log_event("embedded_window_failed", gui=gui, legacy=legacy,
                       netfx_failure=netfx_failure, error=str(exc),
                       fallback="default_browser" if not legacy else "disabled")
        try:
            # On systems where pythonnet cannot initialize CLR, blocking
            # MessageBox dialogs prevent a seamless usable Web fallback.
            if os.name == "nt" and not netfx_failure:
                message = (
                    "Não foi possível iniciar a janela integrada do PT2VHF APRS Client.\n\n"
                    + ("Windows 7 Legacy permanece em modo desktop; o navegador não será aberto automaticamente.\n\n"
                       if legacy else
                       "A interface será aberta no navegador padrão.\n\n")
                    + f"Detalhes: {exc}"
                )
                ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x30)
        except Exception:
            pass
        if legacy:
            _shutdown_components()
            return 3
        _open_browser()
        tray_thread.join()
        return 0


def main() -> int:
    global _browser_mode, _tray_icon, _server_handle, PORT, URL
    _browser_mode = "--browser" in sys.argv[1:]

    if os.name == "nt":
        try:
            # Faz o Windows usar de forma consistente o ícone do executável na
            # barra de tarefas, Alt+Tab e agrupamento de janelas.
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PT2VHF.APRS.Client")
        except Exception:
            pass

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
    runtime_config = db.get_config()
    server_host = "0.0.0.0" if bool(runtime_config.get("web_lan_enabled")) else HOST
    app = create_app()
    service.start_if_configured()
    tnc_service.start_if_configured()

    try:
        _server_handle = start_local_server(
            app,
            host=server_host,
            start_port=PORT,
            runtime_file=runtime_file_for(db.DB_PATH.parent),
        )
        PORT = int(_server_handle.port)
        URL = _server_handle.url
        diag.log_event(
            "local_server_started",
            host=server_host,
            port=PORT,
            url=URL,
            share_url=_server_handle.share_url,
            scope=_server_handle.scope,
            fallback_count=_server_handle.fallback_count,
        )
        print(f"{APP_NAME} — Interface local: {URL}")
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
    _mark_updated_instance_ready()
    if os.getenv("PT2VHF_WIN7_LEGACY") == "1":
        diag.start_legacy_window_diagnostics()


    if not _browser_mode:
        try:
            if bool(db.get_config().get("open_browser_on_start")):
                _open_browser()
        except Exception:
            pass

    _tray_icon = _create_tray_icon()

    if _browser_mode:
        return _run_browser_mode(_tray_icon)

    if os.getenv("PT2VHF_WIN7_LEGACY") == "1":
        return _run_legacy_app_shell(_tray_icon)

    return _run_embedded_window(_tray_icon)


if __name__ == "__main__":
    raise SystemExit(main())
