from __future__ import annotations

import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import __version__
from . import database as db
from . import diagnostics as diag

UPDATE_DIR = db.DB_PATH.parent / "updates"
PENDING_FILE = UPDATE_DIR / "pending_update.json"
APPLY_LOG = UPDATE_DIR / "update_apply.log"
UPDATE_LOCK_FILE = UPDATE_DIR / "update.lock"
HELPER_READY_FILE = UPDATE_DIR / "helper_ready"

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
        return "windows-portable" if "portable" in exe.name.lower() else "windows-installer"
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
    if mode == "windows-portable":
        return f"PT2VHF_APRS_Client_Portable_x64_v{version}.exe"
    if mode == "windows-installer":
        return f"PT2VHF_APRS_Client_Setup_x64_v{version}.exe"
    if mode == "macos-dmg":
        arch = "arm64" if machine == "arm64" else "x86_64"
        return f"PT2VHF_APRS_Client_macOS_{arch}_v{version}.dmg"
    if mode == "linux-appimage":
        return f"PT2VHF_APRS_Client_x86_64_v{version}.AppImage"
    if mode == "linux-deb":
        return f"pt2vhf-aprs-client_{version}_amd64.deb"
    return f"PT2VHF_APRS_Client_Linux_x86_64_v{version}.tar.gz"


def install_supported(mode: str | None = None) -> bool:
    mode = str(mode or current_update_mode())
    if not _is_frozen() and os.getenv("PT2VHF_ALLOW_SOURCE_UPDATE") != "1":
        return False
    machine = _machine()
    if mode.startswith("windows-"):
        return sys.platform == "win32" and machine == "x86_64"
    if mode == "macos-dmg":
        return sys.platform == "darwin" and machine in {"arm64", "x86_64"} and bool(shutil.which("hdiutil"))
    if mode in {"linux-appimage", "linux-tar"}:
        return sys.platform.startswith("linux") and machine == "x86_64"
    if mode == "linux-deb":
        if not sys.platform.startswith("linux") or machine != "x86_64":
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


def download_asset(version: str, asset: dict[str, Any]) -> dict[str, Any]:
    url = str(asset.get("url") or "").strip()
    name = str(asset.get("name") or "").strip()
    if not url.startswith("https://github.com/") or "/alexpmr/PT2VHF-APRS-Client/" not in url:
        raise ValueError("A atualização não pertence à Release oficial do PT2VHF APRS Client.")
    if not name:
        raise ValueError("A Release não informou um arquivo compatível com esta plataforma.")

    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    target = UPDATE_DIR / name
    temp = target.with_suffix(target.suffix + ".download")
    digest = hashlib.sha256()
    expected_size = int(asset.get("size") or 0)

    diag.log_event(
        "update_download_started",
        current_version=__version__,
        target_version=str(version).lstrip("vV"),
        asset=name,
        mode=current_update_mode(),
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"PT2VHF-APRS-Client/{__version__}"},
        )
        with urllib.request.urlopen(req, timeout=45) as response, temp.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)

        actual_size = temp.stat().st_size
        if expected_size > 0 and actual_size != expected_size:
            raise ValueError(
                f"Tamanho inesperado da atualização: recebido {actual_size} bytes; esperado {expected_size}."
            )

        sha256 = digest.hexdigest()
        expected = str(asset.get("digest") or "").strip().lower()
        if expected.startswith("sha256:") and sha256.lower() != expected.split(":", 1)[1]:
            raise ValueError("O SHA-256 da atualização baixada não corresponde ao publicado no GitHub.")

        temp.replace(target)
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
        "$ErrorActionPreference='Stop'\\n"
        f"$pidToWait={pid}\\n"
        f"$downloaded={_ps_quote(path)}\\n"
        f"$current={_ps_quote(current)}\\n"
        f"$pendingFile={_ps_quote(pending_path)}\\n"
        f"$lockFile={_ps_quote(lock_path)}\\n"
        f"$logFile={_ps_quote(log)}\\n"
        f"$readyFile={_ps_quote(ready_path)}\\n"
        "function Log([string]$m) { Add-Content -LiteralPath $logFile -Value ((Get-Date).ToString('o') + ' ' + $m) -Encoding UTF8 }\\n"
        "Set-Content -LiteralPath $readyFile -Value $PID -Encoding ASCII\\n"
        "Log 'updater helper started'\\n"
        "$deadline=(Get-Date).AddSeconds(8)\\n"
        "while ((Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) -and ((Get-Date) -lt $deadline)) { Start-Sleep -Milliseconds 250 }\\n"
        "if (Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) { Log 'forcing previous process to stop'; Stop-Process -Id $pidToWait -Force -ErrorAction SilentlyContinue }\\n"
        "Start-Sleep -Milliseconds 500\\n"
    )

    if mode == "windows-portable":
        destination = current.parent / path.name
        backup = _portable_backup_path(current)
        body = (
            common
            + f"$destination={_ps_quote(destination)}\\n"
            + f"$backup={_ps_quote(backup)}\\n"
            + "try {\\n"
            + "  if (Test-Path -LiteralPath $current) { Copy-Item -LiteralPath $current -Destination $backup -Force; Log 'backup created' }\\n"
            + "  if (($current -ne $destination) -and (Test-Path -LiteralPath $current)) { Remove-Item -LiteralPath $current -Force }\\n"
            + "  Move-Item -LiteralPath $downloaded -Destination $destination -Force\\n"
            + "  Remove-Item -LiteralPath $pendingFile -Force -ErrorAction SilentlyContinue\\n"
            + "  Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue\\n"
            + "  Log 'portable update installed'\\n"
            + "  Start-Process -FilePath $destination\\n"
            + "} catch { Log ('update failed: ' + $_.Exception.Message); throw }\\n"
        )
    else:
        body = (
            common
            + "try {\\n"
            + "  Log 'starting installer'\\n"
            + "  $p=Start-Process -FilePath $downloaded -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Verb RunAs -PassThru -Wait\\n"
            + "  if ($p.ExitCode -ne 0) { throw ('installer exit code ' + $p.ExitCode) }\\n"
            + "  Remove-Item -LiteralPath $pendingFile -Force -ErrorAction SilentlyContinue\\n"
            + "  Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue\\n"
            + "  Log 'installer completed'\\n"
            + "  if (Test-Path -LiteralPath $current) { Start-Process -FilePath $current }\\n"
            + "} catch { Log ('update failed: ' + $_.Exception.Message); throw }\\n"
        )

    script.write_text(body, encoding="utf-8")
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
        "logmsg(){ printf '%s %s\\\\n' \"$(date -Iseconds)\" \"$1\" >> \"$log\"; }",
        "printf '%s\\\\n' \"$$\" > \"$ready\"",
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

    script.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    script.chmod(0o700)
    return script


def _wait_for_helper_ready(process: subprocess.Popen, timeout: float = 4.0) -> bool:
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
        helper = _write_windows_helper(pending)
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        process = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(helper)],
            creationflags=flags,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
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
        raise RuntimeError("O atualizador auxiliar não iniciou corretamente. A aplicação permanecerá aberta.")

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
        "$ErrorActionPreference='Stop'\\n"
        f"$pidToWait={pid}\\n"
        f"$current={_ps_quote(exe)}\\n"
        f"$backup={_ps_quote(backup)}\\n"
        "$deadline=(Get-Date).AddSeconds(8)\\n"
        "while ((Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) -and ((Get-Date) -lt $deadline)) { Start-Sleep -Milliseconds 250 }\\n"
        "if (Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) { Stop-Process -Id $pidToWait -Force -ErrorAction SilentlyContinue }\\n"
        "Start-Sleep -Milliseconds 400\\n"
        "Copy-Item -LiteralPath $backup -Destination $current -Force\\n"
        "Start-Process -FilePath $current\\n",
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
