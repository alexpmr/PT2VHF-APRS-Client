from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from . import database as db

UPDATE_DIR = db.DB_PATH.parent / "updates"
PENDING_FILE = UPDATE_DIR / "pending_update.json"


def _machine() -> str:
    value = platform.machine().lower()
    if value in {"amd64", "x86_64"}:
        return "x86_64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    return value


def current_update_mode() -> str:
    exe = Path(sys.executable)
    if sys.platform == "win32":
        return "windows-portable" if "portable" in exe.name.lower() else "windows-installer"
    if sys.platform == "darwin":
        return "macos-dmg"
    if os.getenv("APPIMAGE"):
        return "linux-appimage"
    if str(exe).startswith(("/usr/bin/", "/usr/local/bin/")):
        return "linux-deb"
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

    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"PT2VHF-APRS-Client/{__version__}"},
    )
    with urllib.request.urlopen(req, timeout=30) as response, temp.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            digest.update(chunk)

    sha256 = digest.hexdigest()
    expected = str(asset.get("digest") or "").strip().lower()
    if expected.startswith("sha256:") and sha256.lower() != expected.split(":", 1)[1]:
        temp.unlink(missing_ok=True)
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
        "current_executable": str(Path(sys.executable).resolve()),
    }
    PENDING_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _portable_backup_path(executable: Path | None = None) -> Path:
    exe = (executable or Path(sys.executable)).resolve()
    return exe.parent / "PT2VHF_APRS_Client_previous.exe"


def rollback_available() -> dict[str, Any] | None:
    if sys.platform != "win32":
        return None
    exe = Path(sys.executable).resolve()
    backup = _portable_backup_path(exe)
    if backup.is_file():
        return {"path": str(backup), "current": str(exe)}
    return None


def launch_pending_update() -> bool:
    cfg = db.get_config()
    if not bool(cfg.get("install_updates_on_exit")):
        return False
    pending = pending_update()
    if not pending:
        return False

    path = Path(str(pending["path"])).resolve()
    mode = str(pending.get("mode") or current_update_mode())

    try:
        if sys.platform == "win32" and mode == "windows-portable":
            current = Path(sys.executable).resolve()
            destination = current.parent / path.name
            backup = _portable_backup_path(current)
            script = UPDATE_DIR / "apply_portable_update.ps1"
            pid = os.getpid()
            script.write_text(
                "$ErrorActionPreference='Stop'\n"
                f"$pidToWait={pid}\n"
                f"$current='{str(current).replace(chr(39), chr(39)*2)}'\n"
                f"$downloaded='{str(path).replace(chr(39), chr(39)*2)}'\n"
                f"$destination='{str(destination).replace(chr(39), chr(39)*2)}'\n"
                f"$backup='{str(backup).replace(chr(39), chr(39)*2)}'\n"
                "try { Wait-Process -Id $pidToWait -ErrorAction SilentlyContinue } catch {}\n"
                "Start-Sleep -Milliseconds 700\n"
                "Copy-Item -LiteralPath $current -Destination $backup -Force\n"
                "if ($destination -ne $current) { Remove-Item -LiteralPath $current -Force -ErrorAction SilentlyContinue }\n"
                "Move-Item -LiteralPath $downloaded -Destination $destination -Force\n"
                "Start-Process -FilePath $destination\n",
                encoding="utf-8",
            )
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            clear_pending_update()
            return True

        if sys.platform == "win32" and mode == "windows-installer":
            subprocess.Popen([str(path), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"])
            clear_pending_update()
            return True

        if sys.platform == "darwin" and path.suffix.lower() == ".dmg":
            subprocess.Popen(["open", str(path)])
            clear_pending_update()
            return True

        if mode == "linux-appimage":
            subprocess.Popen([str(path)])
            clear_pending_update()
            return True

        # Para .deb/.tar.gz não há instalação silenciosa segura sem privilégios.
        return False
    except Exception:
        return False


def restore_windows_portable_backup() -> bool:
    if sys.platform != "win32":
        return False
    exe = Path(sys.executable).resolve()
    backup = _portable_backup_path(exe)
    if not backup.is_file():
        return False
    rollback = UPDATE_DIR / "rollback_portable.ps1"
    pid = os.getpid()
    rollback.write_text(
        "$ErrorActionPreference='Stop'\n"
        f"$pidToWait={pid}\n"
        f"$current='{str(exe).replace(chr(39), chr(39)*2)}'\n"
        f"$backup='{str(backup).replace(chr(39), chr(39)*2)}'\n"
        "try { Wait-Process -Id $pidToWait -ErrorAction SilentlyContinue } catch {}\n"
        "Start-Sleep -Milliseconds 700\n"
        "Copy-Item -LiteralPath $backup -Destination $current -Force\n"
        "Start-Process -FilePath $current\n",
        encoding="utf-8",
    )
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(rollback)],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return True
