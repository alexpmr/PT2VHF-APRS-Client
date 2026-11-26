"""Cópia automática do banco (v2.0.7).

Uma vez por dia o app copia o banco com a API de backup do SQLite (cópia consistente mesmo com o
programa em uso), confere a cópia com ``quick_check``, compacta em ``data/backups/*.db.gz`` e guarda
as N mais recentes (padrão 7). "Restaurar" agenda a troca para a próxima abertura do programa: o banco
atual vai para ``data/before_restore/`` e a cópia escolhida entra no lugar, antes de o banco ser aberto.
"""
from __future__ import annotations

import gzip
import json
import random
import re
import shutil
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import database as db
from . import diagnostics as diag

BACKUP_DIR_NAME = "backups"
PENDING_FILE = "restore_pending.json"
NAME_RE = re.compile(r"^pt2vhf_aprs_(\d{8}-\d{6})(?:_manual)?\.db\.gz$")
DAY_SECONDS = 24 * 3600

_lock = threading.Lock()
_worker_started = False


def backup_dir() -> Path:
    return db.DB_PATH.parent / BACKUP_DIR_NAME


def list_backups() -> list[dict[str, Any]]:
    folder = backup_dir()
    items = []
    if folder.is_dir():
        for path in folder.iterdir():
            match = NAME_RE.match(path.name)
            if not match or not path.is_file():
                continue
            try:
                created = datetime.strptime(match.group(1), "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            items.append({
                "name": path.name,
                "created_at": created.isoformat(timespec="seconds"),
                "bytes": path.stat().st_size,
                "manual": "_manual" in path.name,
            })
    items.sort(key=lambda item: item["name"][12:27], reverse=True)
    return items


def _prune(keep: int) -> list[str]:
    removed = []
    for item in list_backups()[max(1, keep):]:
        try:
            (backup_dir() / item["name"]).unlink()
            removed.append(item["name"])
        except OSError:
            pass
    return removed


def make_backup(*, manual: bool = False, keep: int | None = None) -> dict[str, Any]:
    """Cria uma cópia conferida e compactada. Não lança exceção: devolve ok/erro."""
    with _lock:
        folder = backup_dir()
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        name = f"pt2vhf_aprs_{stamp}{'_manual' if manual else ''}.db.gz"
        raw_tmp = folder / f".{stamp}.db.tmp"
        gz_tmp = folder / f".{stamp}.gz.tmp"
        started = time.monotonic()
        try:
            source = sqlite3.connect(db.DB_PATH, timeout=30)
            target = sqlite3.connect(raw_tmp)
            try:
                source.backup(target, pages=4096, sleep=0.01)
                check = target.execute("PRAGMA quick_check").fetchone()[0]
            finally:
                target.close()
                source.close()
            if str(check).lower() != "ok":
                raise RuntimeError(f"cópia não passou no quick_check: {check}")
            with open(raw_tmp, "rb") as src, gzip.open(gz_tmp, "wb", compresslevel=6) as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            gz_tmp.replace(folder / name)
        except Exception as exc:
            diag.log_event("db_backup_failed", error=str(exc))
            return {"ok": False, "error": str(exc)}
        finally:
            for tmp in (raw_tmp, gz_tmp):
                try:
                    tmp.unlink()
                except OSError:
                    pass
        if keep is None:
            try:
                keep = int(db.get_config().get("db_backup_keep") or 7)
            except Exception:
                keep = 7
        removed = _prune(keep)
        info = {"ok": True, "name": name, "bytes": (folder / name).stat().st_size,
                "seconds": round(time.monotonic() - started, 2), "removed": removed}
        diag.log_event("db_backup_created", **info)
        return info


def backup_due(now: float | None = None) -> bool:
    automatic = [item for item in list_backups() if not item["manual"]]
    if not automatic:
        return True
    newest = datetime.fromisoformat(automatic[0]["created_at"]).timestamp()
    return (now if now is not None else time.time()) - newest >= DAY_SECONDS


def start_worker() -> bool:
    """Confere a cada hora (a primeira, 10 a 20 min após abrir) se a cópia do dia já foi feita."""
    global _worker_started
    if _worker_started:
        return False
    _worker_started = True

    def loop() -> None:
        time.sleep(random.uniform(600, 1200))
        while True:
            try:
                cfg = db.get_config()
                if int(cfg.get("db_backup_enabled", 1)) and backup_due():
                    make_backup(keep=int(cfg.get("db_backup_keep") or 7))
            except Exception as exc:
                diag.log_event("db_backup_worker_error", error=str(exc))
            time.sleep(3600)

    threading.Thread(target=loop, name="db-backup", daemon=True).start()
    return True


# ----------------------------------------------------------------------------- restauração

def schedule_restore(name: str) -> dict[str, Any]:
    if not NAME_RE.match(str(name or "")) or not (backup_dir() / name).is_file():
        raise ValueError("Cópia do banco não encontrada.")
    pending = {"name": name, "requested_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (backup_dir() / PENDING_FILE).write_text(json.dumps(pending), encoding="utf-8")
    diag.log_event("db_restore_scheduled", name=name)
    return pending


def cancel_restore() -> bool:
    try:
        (backup_dir() / PENDING_FILE).unlink()
        return True
    except OSError:
        return False


def pending_restore() -> dict[str, Any] | None:
    try:
        return json.loads((backup_dir() / PENDING_FILE).read_text(encoding="utf-8"))
    except Exception:
        return None


def apply_pending_restore() -> dict[str, Any] | None:
    """Roda na abertura, antes de o banco ser aberto. Nunca impede o app de abrir."""
    pending = pending_restore()
    if not pending:
        return None
    marker = backup_dir() / PENDING_FILE
    name = str(pending.get("name") or "")
    source = backup_dir() / name
    result: dict[str, Any] = {"name": name, "ok": False}
    try:
        if not NAME_RE.match(name) or not source.is_file():
            raise FileNotFoundError(name)
        data_dir = db.DB_PATH.parent
        staging = data_dir / "restore_staging.db"
        with gzip.open(source, "rb") as src, open(staging, "wb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
        check_conn = sqlite3.connect(staging)
        try:
            check = check_conn.execute("PRAGMA quick_check").fetchone()[0]
        finally:
            check_conn.close()
        if str(check).lower() != "ok":
            raise RuntimeError(f"cópia não passou no quick_check: {check}")
        keep_dir = data_dir / "before_restore" / datetime.now().strftime("%Y%m%d-%H%M%S")
        keep_dir.mkdir(parents=True, exist_ok=True)
        for suffix in ("", "-wal", "-shm"):
            current = Path(str(db.DB_PATH) + suffix)
            if current.exists():
                shutil.move(str(current), str(keep_dir / current.name))
        staging.replace(db.DB_PATH)
        result.update(ok=True, previous=str(keep_dir))
    except Exception as exc:
        result["error"] = str(exc)
        try:
            (db.DB_PATH.parent / "restore_staging.db").unlink()
        except OSError:
            pass
    finally:
        try:
            marker.unlink()
        except OSError:
            pass
    diag.log_event("db_restore_applied", **result)
    global LAST_RESTORE
    LAST_RESTORE = result
    return result


LAST_RESTORE: dict[str, Any] | None = None
