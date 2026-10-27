from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import shlex
import ssl
import shutil
import subprocess
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import __version__
from . import database as db
from . import diagnostics as diag
from . import release_check

UPDATE_DIR = db.DB_PATH.parent / "updates"
PENDING_FILE = UPDATE_DIR / "pending_update.json"
APPLY_LOG = UPDATE_DIR / "update_apply.log"
UPDATE_LOCK_FILE = UPDATE_DIR / "update.lock"
HELPER_READY_FILE = UPDATE_DIR / "helper_ready"
UPDATE_RESULT_FILE = UPDATE_DIR / "last_update_result.txt"
SETUP_LOG_FILE = UPDATE_DIR / "installer_setup.log"

# AppId do Inno Setup (windows/installer*.iss); usado para localizar no
# registro a pasta onde o Setup realmente instalou o programa.
INNO_APP_IDS = {
    "windows-installer": "{4A513928-71DA-4DD7-9C06-13D0D8E90FEA}",
    "windows-legacy-installer": "{0CE6C737-4D5A-4B9C-BACE-71406DFA1425}",
}

_update_operation_lock = threading.Lock()
_exit_handler_lock = threading.Lock()
_exit_handler: Callable[[], None] | None = None


def _machine() -> str:
    value = platform.machine().lower()
    if value in {"amd64", "x86_64"}:
        return "x86_64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    return value


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def current_update_mode() -> str:
    exe = Path(sys.executable)
    if sys.platform == "win32":
        name = exe.name.lower()
        legacy = os.getenv("PT2VHF_WIN7_LEGACY") == "1" or "win7_legacy" in name
        if legacy:
            return "windows-legacy-portable" if "portable" in name else "windows-legacy-installer"
        return "windows-portable" if "portable" in name else "windows-installer"
    if sys.platform == "darwin":
        return "macos-dmg"
    if os.getenv("APPIMAGE"):
        return "linux-appimage"
    if shutil.which("dpkg-query"):
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", "pt2vhf-aprs-client"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0 and "install ok installed" in result.stdout.lower():
                return "linux-deb"
        except Exception:
            pass
    return "linux-tar"


def desired_asset_name(version: str) -> str:
    version = str(version or "").lstrip("vV")
    mode = current_update_mode()
    machine = _machine()
    if mode == "windows-legacy-portable":
        return f"PT2VHF_APRS_Client_Win7_Legacy_Portable_x64_v{version}.exe"
    if mode == "windows-legacy-installer":
        return f"PT2VHF_APRS_Client_Setup_Win7_Legacy_x64_v{version}.exe"
    if mode in {"windows-portable", "windows-legacy-portable"}:
        arch = "ARM64" if machine == "arm64" else "x64"
        return f"PT2VHF_APRS_Client_Portable_{arch}_v{version}.exe"
    if mode == "windows-installer":
        arch = "ARM64" if machine == "arm64" else "x64"
        return f"PT2VHF_APRS_Client_Setup_{arch}_v{version}.exe"
    if mode == "macos-dmg":
        arch = "arm64" if machine == "arm64" else "x86_64"
        return f"PT2VHF_APRS_Client_macOS_{arch}_v{version}.dmg"
    if mode == "linux-appimage":
        arch = "arm64" if machine == "arm64" else "x86_64"
        return f"PT2VHF_APRS_Client_{arch}_v{version}.AppImage"
    if mode == "linux-deb":
        arch = "arm64" if machine == "arm64" else "amd64"
        return f"pt2vhf-aprs-client_{version}_{arch}.deb"
    arch = "arm64" if machine == "arm64" else "x86_64"
    return f"PT2VHF_APRS_Client_Linux_{arch}_v{version}.tar.gz"


def install_supported(mode: str | None = None) -> bool:
    mode = str(mode or current_update_mode())
    if not _is_frozen() and os.getenv("PT2VHF_ALLOW_SOURCE_UPDATE") != "1":
        return False
    machine = _machine()
    if mode in {"windows-legacy-portable", "windows-legacy-installer"}:
        return sys.platform == "win32" and machine == "x86_64"
    if mode.startswith("windows-"):
        return sys.platform == "win32" and machine in {"x86_64", "arm64"}
    if mode == "macos-dmg":
        return sys.platform == "darwin" and machine in {"arm64", "x86_64"} and bool(shutil.which("hdiutil"))
    if mode in {"linux-appimage", "linux-tar"}:
        return sys.platform.startswith("linux") and machine in {"x86_64", "arm64"}
    if mode == "linux-deb":
        if not sys.platform.startswith("linux") or machine not in {"x86_64", "arm64"}:
            return False
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            return True
        return bool(shutil.which("pkexec"))
    return False


def select_asset(release: dict[str, Any], version: str) -> dict[str, Any] | None:
    wanted = desired_asset_name(version)
    for asset in release.get("assets") or []:
        if str(asset.get("name") or "") == wanted:
            return {
                "name": wanted,
                "url": str(asset.get("browser_download_url") or ""),
                "size": int(asset.get("size") or 0),
                "digest": str(asset.get("digest") or ""),
            }
    return None


def pending_update() -> dict[str, Any] | None:
    try:
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
        path = Path(str(data.get("path") or ""))
        if not path.is_file():
            return None
        return data
    except Exception:
        return None


def last_update_result() -> dict[str, str] | None:
    """Resultado da última instalação via Setup gravado pelo helper (#103).

    status: ok, version_mismatch (falso sucesso) ou unconfirmed.
    """
    try:
        text = UPDATE_RESULT_FILE.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    result: dict[str, str] = {}
    for token in text.split():
        key, sep, value = token.partition("=")
        if sep and key in {"status", "target", "found"}:
            result[key] = value
    if text.count("exe="):
        result["exe"] = text.split("exe=", 1)[1].strip()
    if "status" not in result:
        return None
    result["running_version"] = __version__
    try:
        result["recorded_at"] = datetime.fromtimestamp(
            UPDATE_RESULT_FILE.stat().st_mtime, timezone.utc
        ).replace(microsecond=0).isoformat()
    except OSError:
        pass
    return result


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers: list[int] = []
    for piece in str(value or "").lstrip("vV").split("."):
        try:
            numbers.append(int(piece))
        except ValueError:
            numbers.append(0)
    return tuple(numbers)


def _is_downloaded_update_file(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(".download"):
        return True
    if name.startswith("pt2vhf_aprs_client_") and name.endswith((".exe", ".dmg", ".appimage", ".tar.gz")):
        return True
    if name.startswith("pt2vhf-aprs-client_") and name.endswith(".deb"):
        return True
    return False


def cleanup_obsolete_downloads(current_version: str | None = None) -> list[str]:
    """Remove pacotes antigos apenas depois que uma versão já iniciou com sucesso.

    Uma atualização pendente mais nova que a versão em execução é preservada.
    Arquivos auxiliares, logs e backups de rollback não são tocados.
    """
    current = str(current_version or __version__).lstrip("vV")
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    pending = pending_update()
    keep_path: Path | None = None
    if pending and _version_tuple(str(pending.get("version") or "")) > _version_tuple(current):
        try:
            keep_path = Path(str(pending.get("path") or "")).resolve()
        except Exception:
            keep_path = None
    elif pending:
        clear_pending_update()

    removed: list[str] = []
    for path in UPDATE_DIR.iterdir():
        if not path.is_file() or not _is_downloaded_update_file(path):
            continue
        try:
            if keep_path is not None and path.resolve() == keep_path:
                continue
            path.unlink(missing_ok=True)
            removed.append(path.name)
        except Exception as exc:
            diag.log_event("update_cleanup_file_error", path=str(path), error=str(exc))
    if removed:
        diag.log_event("update_cleanup_completed", current_version=current, removed=removed)
    return removed


def clear_pending_update() -> None:
    try:
        PENDING_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _current_executable_path() -> Path:
    appimage = str(os.getenv("APPIMAGE") or "").strip()
    if appimage and sys.platform.startswith("linux"):
        return Path(appimage).expanduser().resolve()
    return Path(sys.executable).resolve()


def _current_macos_bundle() -> Path | None:
    if sys.platform != "darwin":
        return None
    exe = Path(sys.executable).resolve()
    for parent in [exe, *exe.parents]:
        if parent.suffix.lower() == ".app":
            return parent
    return None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def _acquire_update_lock_file() -> None:
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(str(UPDATE_LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(str(os.getpid()))
            return
        except FileExistsError:
            try:
                existing_pid = int(UPDATE_LOCK_FILE.read_text(encoding="utf-8").strip() or "0")
            except Exception:
                existing_pid = 0
            if existing_pid and _pid_alive(existing_pid):
                raise RuntimeError("Já existe uma atualização em andamento em outra instância.")
            UPDATE_LOCK_FILE.unlink(missing_ok=True)
    raise RuntimeError("Não foi possível adquirir o lock da atualização.")


def _release_update_lock_file() -> None:
    try:
        UPDATE_LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def register_exit_handler(handler: Callable[[], None] | None) -> None:
    global _exit_handler
    with _exit_handler_lock:
        _exit_handler = handler


def _request_exit_after(delay: float = 1.25) -> None:
    def worker() -> None:
        time.sleep(max(0.2, float(delay)))
        with _exit_handler_lock:
            handler = _exit_handler
        try:
            if handler is not None:
                handler()
                time.sleep(1.0)
        except Exception as exc:
            diag.log_event("update_exit_handler_error", error=str(exc))
        os._exit(0)

    threading.Thread(target=worker, name="pt2vhf-update-exit", daemon=True).start()


def _is_tls_certificate_error(exc: BaseException) -> bool:
    """Restrict Windows fallback to TLS certificate validation/handshake errors."""
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    return isinstance(reason, (ssl.SSLError, ssl.CertificateError))


def _record_site_download_count() -> None:
    """Conta uma atualização baixada e validada, sem bloquear a instalação."""
    if not _is_frozen():
        return
    names = {
        "windows-installer": "win-setup",
        "windows-portable": "win-portable",
        "linux-appimage": "linux-appimage",
        "linux-deb": "linux-deb",
        "linux-tar": "linux-tar",
        "macos-dmg": "mac-dmg",
        # v1.14.61: atualizações OTA do Windows 7 Legacy também contam.
        "windows-legacy-installer": "win7-setup",
        "windows-legacy-portable": "win7-portable",
    }
    prefix = names.get(current_update_mode())
    if not prefix:
        return
    category = prefix + ("-arm64" if _machine() == "arm64" else "-x64")
    url = "https://www.pt2vhf.com/download.php"
    body = urllib.parse.urlencode({
        "action": "count", "product": "aprs", "category": category,
    }).encode("ascii")
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "PT2VHF-APRS-Client-Updater",
        },
    )
    try:
        with urllib.request.build_opener(release_check.NoRedirect()).open(request, timeout=3) as response:
            if response.geturl() != url or response.status != 204:
                raise RuntimeError("Contador do site não confirmou o registro.")
    except Exception as exc:
        diag.log_event("update_download_counter_unavailable", error=type(exc).__name__)


def _windows_native_download(url: str, target: Path, timeout: int = 150) -> None:
    """Download with the Windows trusted certificate store, keeping TLS validation enabled.

    PowerShell follows PT2VHF's HTTPS transfers without redirects using Windows/.NET trust. It does
    not disable verification or accept untrusted certificates. Caller verifies
    release metadata, byte length and site SHA-256 after download.
    """
    if sys.platform != "win32":
        raise RuntimeError("O download TLS nativo está disponível somente no Windows.")
    quoted_url = url.replace("'", "''")
    quoted_path = str(target).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop';"
        "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;"
        "Invoke-WebRequest -UseBasicParsing -Uri '" + quoted_url + "' "
        "-OutFile '" + quoted_path + "' -MaximumRedirection 0 "
        "-TimeoutSec " + str(int(timeout)) + " "
        "-Headers @{'User-Agent'='PT2VHF-APRS-Client-Updater'};"
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True,
            check=False,
            timeout=int(timeout) + 15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            "O download HTTPS com os certificados do Windows não respondeu. "
            "Verifique relógio, atualizações de certificados raiz, proxy e antivírus."
        ) from exc
    if result.returncode != 0 or not target.is_file():
        stderr = result.stderr.decode("utf-8", errors="replace")[-700:]
        diag.log_event(
            "update_download_windows_tls_failed",
            exit_code=result.returncode,
            stderr=stderr,
        )
        raise RuntimeError(
            "Falha de certificado HTTPS/TLS também ao usar os certificados do Windows. "
            "Não foi ignorada a validação de segurança. "
            "Verifique data/hora, certificados raiz, proxy ou inspeção HTTPS; "
            "como alternativa, acesse www.pt2vhf.com/aprs pelo navegador."
        )


def download_asset(version: str, asset: dict[str, Any]) -> dict[str, Any]:
    url = str(asset.get("url") or "").strip()
    name = str(asset.get("name") or "").strip()
    if not release_check.is_official_asset(url, name):
        raise ValueError("Pacote de atualização fora do domínio www.pt2vhf.com.")
    if not name:
        raise ValueError("A Release não informou um arquivo compatível com esta plataforma.")

    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    target = UPDATE_DIR / name
    temp = target.with_suffix(target.suffix + ".download")
    # Repetir o download nunca cria cópias "(1)", "(2)" etc. O temporário
    # anterior é descartado e o nome oficial da Release é sempre reutilizado.
    temp.unlink(missing_ok=True)
    digest = hashlib.sha256()
    expected_size = int(asset.get("size") or 0)
    expected = str(asset.get("digest") or "").strip().lower()
    if expected_size <= 0 or not expected.startswith("sha256:") or not release_check.HASH_RE.fullmatch(expected[7:]):
        raise ValueError("Atualização sem tamanho e SHA-256 obrigatórios.")

    diag.log_event(
        "update_download_started",
        current_version=__version__,
        target_version=str(version).lstrip("vV"),
        asset=name,
        mode=current_update_mode(),
        url=url,
        target=str(target),
        expected_size=expected_size,
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"PT2VHF-APRS-Client/{__version__}"},
        )
        try:
            with urllib.request.build_opener(release_check.NoRedirect()).open(req, timeout=45) as response, temp.open("wb") as out:
                if response.geturl() != url:
                    raise ValueError("Redirecionamento do download não permitido.")
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    digest.update(chunk)
        except Exception as exc:
            if sys.platform != "win32" or not _is_tls_certificate_error(exc):
                raise
            # A certificate failure in Python must not disable HTTPS checks.
            # Windows may have a valid enterprise/system CA that the bundled
            # Python runtime cannot see. Reuse the native trusted store.
            temp.unlink(missing_ok=True)
            diag.log_event(
                "update_download_windows_tls_fallback",
                reason=type(exc).__name__,
                asset=name,
            )
            _windows_native_download(url, temp)
            with temp.open("rb") as downloaded:
                for chunk in iter(lambda: downloaded.read(1024 * 1024), b""):
                    digest.update(chunk)

        actual_size = temp.stat().st_size
        if expected_size > 0 and actual_size != expected_size:
            raise ValueError(
                f"Tamanho inesperado da atualização: recebido {actual_size} bytes; esperado {expected_size}."
            )

        sha256 = digest.hexdigest()
        if sha256.lower() != expected[7:]:
            raise ValueError("O SHA-256 da atualização baixada não corresponde ao publicado no site PT2VHF.")

        # No Windows, remover explicitamente o pacote antigo torna a semântica
        # de sobrescrita inequívoca antes do replace atômico do novo download.
        target.unlink(missing_ok=True)
        temp.replace(target)
        _record_site_download_count()
        if target.suffix.lower() == ".appimage":
            target.chmod(target.stat().st_mode | 0o111)

        payload = {
            "version": str(version).lstrip("vV"),
            "asset_name": name,
            "path": str(target),
            "sha256": sha256,
            "expected_digest": expected or None,
            "mode": current_update_mode(),
            "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "current_executable": str(_current_executable_path()),
            "current_bundle": str(_current_macos_bundle() or ""),
            "pid": os.getpid(),
        }
        PENDING_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        diag.log_event(
            "update_download_validated",
            target_version=payload["version"],
            asset=name,
            sha256=sha256,
            size=actual_size,
            path=str(target),
        )
        return payload
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _portable_backup_path(executable: Path | None = None) -> Path:
    exe = (executable or _current_executable_path()).resolve()
    return exe.parent / "PT2VHF_APRS_Client_previous.exe"


def rollback_available() -> dict[str, Any] | None:
    if sys.platform != "win32":
        return None
    exe = _current_executable_path()
    backup = _portable_backup_path(exe)
    if backup.is_file():
        return {"path": str(backup), "current": str(exe)}
    return None


def _ps_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _cmd_value(value: str | Path) -> str:
    # Values are assigned with SET "name=value"; percent signs must be doubled
    # so paths such as C:\100%\... are not interpreted as environment variables.
    return str(value).replace("%", "%%")


def _write_windows_cmd_helper(pending: dict[str, Any]) -> Path:
    downloaded = Path(str(pending["path"])).resolve()
    current = Path(str(pending.get("current_executable") or _current_executable_path())).resolve()
    mode = str(pending.get("mode") or current_update_mode())
    script = UPDATE_DIR / "apply_update.cmd"
    log = APPLY_LOG.resolve()
    pending_path = PENDING_FILE.resolve()
    lock_path = UPDATE_LOCK_FILE.resolve()
    ready_path = HELPER_READY_FILE.resolve()

    previous_pid = max(0, int(pending.get("pid") or 0))
    marker = (UPDATE_DIR / "update_ready.flag").resolve()
    lines = [
        "@echo off",
        "setlocal DisableDelayedExpansion",
        # A replacement onefile EXE must unpack its own Python/DLL runtime.
        'set "PYINSTALLER_RESET_ENVIRONMENT=1"',
        'set "_MEIPASS2="',
        *[f'set "{key}="' for key in os.environ if key.startswith("_PYI_")],
        "chcp 65001 >nul",
        f'set "oldpid={previous_pid}"',
        f'set "marker={_cmd_value(marker)}"',
        f'set "downloaded={_cmd_value(downloaded)}"',
        f'set "current={_cmd_value(current)}"',
        f'set "pending={_cmd_value(pending_path)}"',
        f'set "lockfile={_cmd_value(lock_path)}"',
        f'set "logfile={_cmd_value(log)}"',
        f'set "ready={_cmd_value(ready_path)}"',
        'if exist "%marker%" del /F /Q "%marker%" >nul 2>&1',
        '> "%ready%" echo ready',
        '>> "%logfile%" echo %date% %time% updater cmd helper started oldpid=%oldpid%',
        # The caller shuts down after receiving this helper-ready file.
        # Never assume that a fixed sleep proves Windows released the EXE.
        'ping 127.0.0.1 -n 6 >nul',
    ]

    if mode in {"windows-portable", "windows-legacy-portable"}:
        destination = current
        backup = _portable_backup_path(current)
        lines += [
            f'set "destination={_cmd_value(destination)}"',
            f'set "backup={_cmd_value(backup)}"',
            'set /a tries=0',
            ':backup_retry',
            'if not exist "%current%" goto update_failed',
            'copy /Y "%current%" "%backup%" >nul 2>&1',
            'if not errorlevel 1 goto backup_ok',
            'set /a tries+=1',
            '>> "%logfile%" echo %date% %time% backup retry %tries% (oldpid=%oldpid%)',
            'if %tries% GEQ 30 goto update_failed',
            'ping 127.0.0.1 -n 2 >nul',
            'goto backup_retry',
            ':backup_ok',
            '>> "%logfile%" echo %date% %time% portable backup secured',
            'set /a tries=0',
            ':portable_retry',
            'if /I not "%current%"=="%destination%" if exist "%current%" del /F /Q "%current%" >nul 2>&1',
            'move /Y "%downloaded%" "%destination%" >nul 2>&1',
            'if not errorlevel 1 goto portable_installed',
            'set /a tries+=1',
            '>> "%logfile%" echo %date% %time% executable still locked; retry %tries% (oldpid=%oldpid%)',
            'if %tries% GEQ 30 goto update_failed',
            'ping 127.0.0.1 -n 2 >nul',
            'goto portable_retry',
            ':portable_installed',
            'if not exist "%destination%" goto update_failed',
            '>> "%logfile%" echo %date% %time% portable update installed',
            # The new instance signals health only after its local APRS HTTP
            # server has actually started. A failed _MEI bootstrap never does.
            'set "PT2VHF_UPDATE_READY_MARKER=%marker%"',
            'start "" "%destination%"',
            'if errorlevel 1 goto update_failed',
            'set /a tries=0',
            ':wait_new_instance',
            'if exist "%marker%" goto portable_healthy',
            'set /a tries+=1',
            'if %tries% GEQ 35 goto portable_unhealthy',
            'ping 127.0.0.1 -n 2 >nul',
            'goto wait_new_instance',
            ':portable_healthy',
            '>> "%logfile%" echo %date% %time% new portable backend confirmed healthy',
            'del /F /Q "%pending%" "%lockfile%" >nul 2>&1',
            'exit /b 0',
            ':portable_unhealthy',
            '>> "%logfile%" echo %date% %time% new portable did not signal readiness; attempting rollback',
            'set /a tries=0',
            ':rollback_retry',
            'copy /Y "%backup%" "%destination%" >nul 2>&1',
            'if not errorlevel 1 goto rollback_restored',
            'set /a tries+=1',
            'if %tries% GEQ 25 goto update_failed',
            'ping 127.0.0.1 -n 2 >nul',
            'goto rollback_retry',
            ':rollback_restored',
            '>> "%logfile%" echo %date% %time% previous portable restored',
            'set "PT2VHF_UPDATE_READY_MARKER="',
            'start "" "%destination%"',
            'exit /b 1',
        ]
    else:
        # #103: código de saída 0 do Setup não prova que a versão nova está em
        # uso. Relança a partir da pasta registrada pelo Inno Setup e só
        # declara sucesso quando a instância nova confirma a versão alvo.
        target = "".join(ch for ch in str(pending.get("version") or "") if ch.isdigit() or ch == ".")
        app_id = INNO_APP_IDS.get(mode, INNO_APP_IDS["windows-installer"])
        uninstall_key = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_id}_is1"
        lines += [
            f'set "target={target}"',
            f'set "exename={_cmd_value(current.name)}"',
            f'set "result={_cmd_value(UPDATE_RESULT_FILE.resolve())}"',
            f'set "setuplog={_cmd_value(SETUP_LOG_FILE.resolve())}"',
            'if exist "%result%" del /F /Q "%result%" >nul 2>&1',
            '>> "%logfile%" echo %date% %time% setup target=%target% running_exe="%current%"',
            'start "" /wait "%downloaded%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS /LOG="%setuplog%"',
            'if errorlevel 1 goto update_failed',
            'del /F /Q "%pending%" "%lockfile%" >nul 2>&1',
            '>> "%logfile%" echo %date% %time% installer exit code 0; setup log="%setuplog%"',
            'set "installdir="',
            *[
                f'if not defined installdir for /f "tokens=2,*" %%A in (\'reg query "{hive}\\{uninstall_key}" /v InstallLocation{view} 2^>nul ^| findstr /I "InstallLocation"\') do set "installdir=%%B"'
                for hive, view in (("HKLM", " /reg:64"), ("HKLM", ""), ("HKCU", ""))
            ],
            'set "relaunch=%current%"',
            'if defined installdir if exist "%installdir%%exename%" set "relaunch=%installdir%%exename%"',
            '>> "%logfile%" echo %date% %time% registry install dir="%installdir%" relaunch="%relaunch%"',
            'if /I not "%relaunch%"=="%current%" >> "%logfile%" echo %date% %time% WARNING running executable differs from installed path',
            'set "PT2VHF_UPDATE_READY_MARKER=%marker%"',
            'start "" "%relaunch%"',
            'set "PT2VHF_UPDATE_READY_MARKER="',
            'set /a tries=0',
            ':wait_setup_instance',
            'if exist "%marker%" goto setup_ready',
            'set /a tries+=1',
            'if %tries% GEQ 45 goto setup_unconfirmed',
            'ping 127.0.0.1 -n 3 >nul',
            'goto wait_setup_instance',
            ':setup_ready',
            'findstr /C:"version=%target% " "%marker%" >nul 2>&1',
            'if errorlevel 1 goto setup_version_mismatch',
            '>> "%logfile%" echo %date% %time% installed backend confirmed version %target%',
            '> "%result%" echo status=ok target=%target% exe=%relaunch%',
            'exit /b 0',
            ':setup_version_mismatch',
            'set "found="',
            'for /f "usebackq tokens=3 delims== " %%V in ("%marker%") do if not defined found set "found=%%V"',
            '>> "%logfile%" echo %date% %time% FALSE SUCCESS installer exit 0 but running version=%found% target=%target%',
            '> "%result%" echo status=version_mismatch target=%target% found=%found% exe=%relaunch%',
            'exit /b 1',
            ':setup_unconfirmed',
            '>> "%logfile%" echo %date% %time% installed instance did not confirm readiness',
            '> "%result%" echo status=unconfirmed target=%target% exe=%relaunch%',
            'exit /b 1',
        ]

    lines += [
        ':update_failed',
        '>> "%logfile%" echo %date% %time% update failed in cmd helper; previous binary kept if possible',
        'if defined backup if exist "%backup%" if not exist "%current%" copy /Y "%backup%" "%current%" >nul 2>&1',
        'set "PT2VHF_UPDATE_READY_MARKER="',
        'if exist "%current%" start "" "%current%"',
        'exit /b 1',
    ]

    script.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return script


def _write_windows_helper(pending: dict[str, Any]) -> Path:
    path = Path(str(pending["path"])).resolve()
    current = Path(str(pending.get("current_executable") or _current_executable_path())).resolve()
    mode = str(pending.get("mode") or current_update_mode())
    pid = int(pending.get("pid") or os.getpid())
    script = UPDATE_DIR / "apply_update.ps1"
    log = APPLY_LOG.resolve()
    pending_path = PENDING_FILE.resolve()
    lock_path = UPDATE_LOCK_FILE.resolve()
    ready_path = HELPER_READY_FILE.resolve()

    common = (
        "$ErrorActionPreference='Stop'\n"
        f"$pidToWait={pid}\n"
        f"$downloaded={_ps_quote(path)}\n"
        f"$current={_ps_quote(current)}\n"
        f"$pendingFile={_ps_quote(pending_path)}\n"
        f"$lockFile={_ps_quote(lock_path)}\n"
        f"$logFile={_ps_quote(log)}\n"
        f"$readyFile={_ps_quote(ready_path)}\n"
        "function Log([string]$m) { Add-Content -LiteralPath $logFile -Value ((Get-Date).ToString('o') + ' ' + $m) -Encoding UTF8 }\n"
        "Set-Content -LiteralPath $readyFile -Value $PID -Encoding ASCII\n"
        "Log 'updater helper started'\n"
        "$deadline=(Get-Date).AddSeconds(8)\n"
        "while ((Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) -and ((Get-Date) -lt $deadline)) { Start-Sleep -Milliseconds 250 }\n"
        "if (Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) { Log 'forcing previous process to stop'; Stop-Process -Id $pidToWait -Force -ErrorAction SilentlyContinue }\n"
        "Start-Sleep -Milliseconds 500\n"
    )

    if mode in {"windows-portable", "windows-legacy-portable"}:
        destination = current.parent / path.name
        backup = _portable_backup_path(current)
        body = (
            common
            + f"$destination={_ps_quote(destination)}\n"
            + f"$backup={_ps_quote(backup)}\n"
            + "try {\n"
            + "  if (Test-Path -LiteralPath $current) { Copy-Item -LiteralPath $current -Destination $backup -Force; Log 'backup created' }\n"
            + "  if (($current -ne $destination) -and (Test-Path -LiteralPath $current)) { Remove-Item -LiteralPath $current -Force }\n"
            + "  Move-Item -LiteralPath $downloaded -Destination $destination -Force\n"
            + "  Remove-Item -LiteralPath $pendingFile -Force -ErrorAction SilentlyContinue\n"
            + "  Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue\n"
            + "  Log 'portable update installed'\n"
            + "  Start-Process -FilePath $destination\n"
            + "} catch { Log ('update failed: ' + $_.Exception.Message); throw }\n"
        )
    else:
        body = (
            common
            + "try {\n"
            + "  Log 'starting installer'\n"
            + "  $p=Start-Process -FilePath $downloaded -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Verb RunAs -PassThru -Wait\n"
            + "  if ($p.ExitCode -ne 0) { throw ('installer exit code ' + $p.ExitCode) }\n"
            + "  Remove-Item -LiteralPath $pendingFile -Force -ErrorAction SilentlyContinue\n"
            + "  Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue\n"
            + "  Log 'installer completed'\n"
            + "  if (Test-Path -LiteralPath $current) { Start-Process -FilePath $current }\n"
            + "} catch { Log ('update failed: ' + $_.Exception.Message); throw }\n"
        )

    # Windows PowerShell 5.1 does not reliably treat UTF-8 without BOM as
    # UTF-8. Keep the fallback helper BOM-marked for non-ASCII user paths.
    script.write_text(body, encoding="utf-8-sig")
    return script


def _prepare_linux_tar(pending: dict[str, Any]) -> Path:
    source = Path(str(pending["path"])).resolve()
    stage = UPDATE_DIR / f"stage-{pending['version']}"
    if stage.exists():
        shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True, exist_ok=True)
    with tarfile.open(source, "r:gz") as archive:
        archive.extractall(stage, filter="data")
    candidates = sorted(stage.glob("PT2VHF_APRS_Client_Linux_x86_64_v*"))
    if not candidates:
        raise ValueError("O pacote Linux TAR.GZ não contém o executável esperado.")
    candidate = candidates[0]
    candidate.chmod(candidate.stat().st_mode | 0o111)
    return candidate


def _write_posix_helper(pending: dict[str, Any]) -> Path:
    mode = str(pending.get("mode") or current_update_mode())
    downloaded = Path(str(pending["path"])).resolve()
    current = Path(str(pending.get("current_executable") or _current_executable_path())).resolve()
    pid = int(pending.get("pid") or os.getpid())
    script = UPDATE_DIR / "apply_update.sh"
    pending_file = PENDING_FILE.resolve()
    lock_file = UPDATE_LOCK_FILE.resolve()
    log = APPLY_LOG.resolve()
    ready_file = HELPER_READY_FILE.resolve()

    q = shlex.quote
    lines = [
        "#!/usr/bin/env bash",
        "set -e",
        f"pid={pid}",
        f"log={q(str(log))}",
        f"pending={q(str(pending_file))}",
        f"lockfile={q(str(lock_file))}",
        f"ready={q(str(ready_file))}",
        "logmsg(){ printf '%s %s\\n' \"$(date -Iseconds)\" \"$1\" >> \"$log\"; }",
        "printf '%s\\n' \"$$\" > \"$ready\"",
        "logmsg 'updater helper started'",
        "for _ in $(seq 1 32); do",
        "  if ! kill -0 \"$pid\" 2>/dev/null; then break; fi",
        "  sleep 0.25",
        "done",
        "if kill -0 \"$pid\" 2>/dev/null; then logmsg 'forcing previous process to stop'; kill -TERM \"$pid\" 2>/dev/null || true; sleep 1; fi",
        "if kill -0 \"$pid\" 2>/dev/null; then kill -KILL \"$pid\" 2>/dev/null || true; fi",
        "sleep 0.4",
    ]

    if mode == "linux-appimage":
        destination = current.parent / downloaded.name
        backup = current.parent / "PT2VHF_APRS_Client_previous.AppImage"
        lines += [
            f"current={q(str(current))}",
            f"downloaded={q(str(downloaded))}",
            f"destination={q(str(destination))}",
            f"backup={q(str(backup))}",
            'if [ -f "$current" ]; then cp -f "$current" "$backup"; fi',
            'if [ "$current" != "$destination" ]; then rm -f "$current"; fi',
            'mv -f "$downloaded" "$destination"',
            'chmod +x "$destination"',
            'rm -f "$pending" "$lockfile"',
            "logmsg 'AppImage update installed'",
            'nohup "$destination" >/dev/null 2>&1 &',
        ]
    elif mode == "linux-deb":
        relaunch = "/usr/local/bin/pt2vhf-aprs-client"
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            install_cmd = f"dpkg -i {q(str(downloaded))}"
        else:
            install_cmd = f"pkexec dpkg -i {q(str(downloaded))}"
        lines += [
            f"downloaded={q(str(downloaded))}",
            install_cmd,
            'rm -f "$pending" "$lockfile"',
            "logmsg 'DEB update installed'",
            f"nohup {q(relaunch)} >/dev/null 2>&1 &",
        ]
    elif mode == "linux-tar":
        staged = _prepare_linux_tar(pending)
        destination = current.parent / staged.name
        backup = current.parent / "PT2VHF_APRS_Client_Linux_previous"
        lines += [
            f"current={q(str(current))}",
            f"staged={q(str(staged))}",
            f"destination={q(str(destination))}",
            f"backup={q(str(backup))}",
            'if [ -f "$current" ]; then cp -f "$current" "$backup"; fi',
            'if [ "$current" != "$destination" ]; then rm -f "$current"; fi',
            'mv -f "$staged" "$destination"',
            'chmod +x "$destination"',
            'rm -f "$pending" "$lockfile"',
            "logmsg 'Linux TAR update installed'",
            'nohup "$destination" >/dev/null 2>&1 &',
        ]
    elif mode == "macos-dmg":
        bundle_text = str(pending.get("current_bundle") or "").strip()
        if not bundle_text:
            raise ValueError("Não foi possível localizar o aplicativo .app atual para atualização.")
        target = Path(bundle_text).resolve()
        user_target = Path.home() / "Applications" / target.name
        mount = UPDATE_DIR / f"mount-{pending['version']}"
        lines += [
            f"dmg={q(str(downloaded))}",
            f"target={q(str(target))}",
            f"user_target={q(str(user_target))}",
            f"mount={q(str(mount))}",
            'rm -rf "$mount"; mkdir -p "$mount"',
            'hdiutil attach "$dmg" -nobrowse -readonly -mountpoint "$mount" >/dev/null',
            "source_app=\"$(find \"$mount\" -maxdepth 1 -name '*.app' -print -quit)\"",
            'if [ -z "$source_app" ]; then hdiutil detach "$mount" >/dev/null 2>&1 || true; logmsg "DMG has no app bundle"; exit 3; fi',
            'dest="$target"',
            'if [ ! -w "$(dirname "$target")" ]; then mkdir -p "$(dirname "$user_target")"; dest="$user_target"; fi',
            'backup="${dest%.app} previous.app"',
            'rm -rf "$backup"',
            'if [ -d "$dest" ]; then /usr/bin/ditto "$dest" "$backup"; fi',
            'rm -rf "$dest"',
            '/usr/bin/ditto "$source_app" "$dest"',
            'hdiutil detach "$mount" >/dev/null 2>&1 || true',
            'rm -f "$pending" "$lockfile"',
            "logmsg 'macOS update installed'",
            'open "$dest"',
        ]
    else:
        raise ValueError(f"Modo de atualização não suportado: {mode}")

    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
    script.chmod(0o700)
    return script


def _wait_for_helper_ready(process: subprocess.Popen, timeout: float = 12.0) -> bool:
    deadline = time.monotonic() + max(1.0, float(timeout))
    while time.monotonic() < deadline:
        if HELPER_READY_FILE.exists():
            return True
        if process.poll() is not None:
            return False
        time.sleep(0.1)
    return HELPER_READY_FILE.exists()


def launch_pending_update(force: bool = False) -> bool:
    if not force:
        cfg = db.get_config()
        if not bool(cfg.get("install_updates_on_exit")):
            return False
    pending = pending_update()
    if not pending:
        return False

    mode = str(pending.get("mode") or current_update_mode())
    if not install_supported(mode):
        raise ValueError("A instalação automática não é suportada neste ambiente.")

    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    HELPER_READY_FILE.unlink(missing_ok=True)

    if sys.platform == "win32":
        # Use the native CMD helper as the primary Windows updater. This avoids
        # depending on PowerShell execution policy/profile/security products just
        # to replace the executable or launch the signed Setup package.
        helper = _write_windows_cmd_helper(pending)
        flags = (
            getattr(subprocess, "CREATE_NO_WINDOW", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
        # PyInstaller changes the process DLL directory. Native helpers must
        # use Windows DLL lookup, then restore our runtime for the running app.
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.SetDllDirectoryW.argtypes = [ctypes.c_wchar_p]
        kernel32.SetDllDirectoryW.restype = ctypes.c_int
        if not kernel32.SetDllDirectoryW(None):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            process = subprocess.Popen(
                [os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"), "/d", "/c", str(helper)],
                creationflags=flags,
                close_fds=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            kernel32.SetDllDirectoryW(getattr(sys, "_MEIPASS", None))
    else:
        helper = _write_posix_helper(pending)
        process = subprocess.Popen(
            ["/bin/bash", str(helper)],
            start_new_session=True,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    if not _wait_for_helper_ready(process):
        diag.log_event(
            "update_helper_start_failed",
            mode=mode,
            target_version=pending.get("version"),
            helper=str(helper),
            helper_pid=process.pid,
            returncode=process.poll(),
        )
        try:
            process.terminate()
        except Exception:
            pass
        fallback_note = ""
        if sys.platform == "win32":
            fallback_note = " O helper CMD não confirmou a inicialização."
        raise RuntimeError(
            "O atualizador auxiliar não iniciou corretamente."
            + fallback_note
            + " A aplicação permanecerá aberta. Consulte update_apply.log/diagnostics.log."
        )

    diag.log_event(
        "update_helper_launched",
        mode=mode,
        target_version=pending.get("version"),
        helper=str(helper),
        helper_pid=process.pid,
        ready_file=str(HELPER_READY_FILE),
    )
    return True

def download_and_install(version: str, asset: dict[str, Any]) -> dict[str, Any]:
    diag.log_event(
        "update_install_requested",
        current_version=__version__,
        target_version=str(version).lstrip("vV"),
        asset=str(asset.get("name") or ""),
        mode=current_update_mode(),
    )
    if not _update_operation_lock.acquire(blocking=False):
        raise RuntimeError("Já existe uma atualização em andamento.")
    lock_acquired = False
    helper_started = False
    try:
        _acquire_update_lock_file()
        lock_acquired = True
        mode = current_update_mode()
        if not install_supported(mode):
            raise ValueError("A instalação automática não é suportada nesta execução/plataforma.")
        payload = download_asset(version, asset)
        if not launch_pending_update(force=True):
            raise RuntimeError("Não foi possível iniciar o instalador auxiliar.")
        helper_started = True
        _request_exit_after(delay=2.5)
        return {
            "ok": True,
            "version": payload["version"],
            "asset_name": payload["asset_name"],
            "sha256": payload["sha256"],
            "mode": payload["mode"],
            "message": "Atualização baixada, validada e helper confirmado. A aplicação será reiniciada para concluir a instalação.",
        }
    except Exception as exc:
        diag.log_event("update_install_failed", target_version=version, error=str(exc))
        if lock_acquired and not helper_started:
            _release_update_lock_file()
        raise
    finally:
        _update_operation_lock.release()


def restore_windows_portable_backup() -> bool:
    if sys.platform != "win32":
        return False
    exe = _current_executable_path()
    backup = _portable_backup_path(exe)
    if not backup.is_file():
        return False
    rollback = UPDATE_DIR / "rollback_portable.ps1"
    pid = os.getpid()
    rollback.write_text(
        "$ErrorActionPreference='Stop'\n"
        f"$pidToWait={pid}\n"
        f"$current={_ps_quote(exe)}\n"
        f"$backup={_ps_quote(backup)}\n"
        "$deadline=(Get-Date).AddSeconds(8)\n"
        "while ((Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) -and ((Get-Date) -lt $deadline)) { Start-Sleep -Milliseconds 250 }\n"
        "if (Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) { Stop-Process -Id $pidToWait -Force -ErrorAction SilentlyContinue }\n"
        "Start-Sleep -Milliseconds 400\n"
        "Copy-Item -LiteralPath $backup -Destination $current -Force\n"
        "Start-Process -FilePath $current\n",
        encoding="utf-8",
    )
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(rollback)],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0),
        close_fds=True,
    )
    _request_exit_after()
    return True
