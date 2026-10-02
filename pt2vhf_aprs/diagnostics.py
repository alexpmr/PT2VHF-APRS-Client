from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psutil
except Exception:
    psutil = None

_lock = threading.RLock()
_active: dict[str, dict[str, Any]] = {}
_counter = 0
_log_path: Path | None = None
_watchdog_thread: threading.Thread | None = None
_watchdog_stop = threading.Event()
_last_dump_at = 0.0
_max_log_bytes = 8 * 1024 * 1024
_metrics_lock = threading.Lock()
_metrics_started = time.monotonic()
_metrics_prev_wall: float | None = None
_metrics_prev_cpu: float | None = None
_resource_alert_lock = threading.Lock()
_resource_alert_state: dict[str, dict[str, Any]] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def configure(data_dir: Path) -> Path:
    global _log_path
    path = Path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    with _lock:
        _log_path = path / "diagnostics.log"
        try:
            if _log_path.exists() and _log_path.stat().st_size > _max_log_bytes:
                previous = path / "diagnostics.previous.log"
                try:
                    previous.unlink(missing_ok=True)
                except Exception:
                    pass
                _log_path.replace(previous)
        except Exception:
            pass
    log_event("diagnostics_configured", pid=os.getpid(), python=sys.version.split()[0])
    return _log_path


def log_path() -> Path:
    with _lock:
        if _log_path is not None:
            return _log_path
    return Path.cwd() / "diagnostics.log"


def log_event(event: str, **fields: Any) -> None:
    payload = {
        "ts": _utc_now(),
        "event": str(event),
        "thread_id": threading.get_ident(),
        "thread_name": threading.current_thread().name,
        **fields,
    }
    line = json.dumps(payload, ensure_ascii=False, default=str)
    try:
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            with path.open("a", encoding="utf-8", errors="replace") as handle:
                handle.write(line + "\n")
                handle.flush()
    except Exception:
        pass


def begin_request(method: str, path: str) -> str:
    global _counter
    now = time.monotonic()
    with _lock:
        _counter += 1
        token = f"{threading.get_ident()}-{_counter}"
        _active[token] = {
            "token": token,
            "method": str(method),
            "path": str(path),
            "started": now,
            "started_at": _utc_now(),
            "thread_id": threading.get_ident(),
            "thread_name": threading.current_thread().name,
        }
        active_count = len(_active)
    log_event("request_start", request_id=token, method=method, path=path, active_requests=active_count)
    return token


def end_request(token: str | None, status: int | None = None, error: str | None = None) -> None:
    if not token:
        return
    with _lock:
        info = _active.pop(token, None)
        active_count = len(_active)
    if not info:
        return
    duration_ms = round((time.monotonic() - float(info["started"])) * 1000, 1)
    log_event(
        "request_end",
        request_id=token,
        method=info["method"],
        path=info["path"],
        status=status,
        duration_ms=duration_ms,
        active_requests=active_count,
        error=error,
    )


def active_requests() -> list[dict[str, Any]]:
    now = time.monotonic()
    with _lock:
        values = [dict(item) for item in _active.values()]
    for item in values:
        item["age_ms"] = round((now - float(item.pop("started", now))) * 1000, 1)
    return sorted(values, key=lambda item: float(item.get("age_ms") or 0), reverse=True)


def log_sqlite_slow(duration_ms: float, error: str | None = None) -> None:
    stack = traceback.extract_stack(limit=8)
    callers = [
        f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}"
        for frame in stack[:-1]
        if "contextlib.py" not in frame.filename
    ][-5:]
    log_event(
        "sqlite_slow",
        duration_ms=round(float(duration_ms), 1),
        error=error,
        callers=callers,
        active_requests=len(active_requests()),
    )


def dump_threads(reason: str) -> None:
    global _last_dump_at
    now = time.monotonic()
    with _lock:
        if now - _last_dump_at < 12.0:
            return
        _last_dump_at = now

    frames = sys._current_frames()
    lines = [
        "",
        "=" * 88,
        f"THREAD DUMP {_utc_now()} reason={reason}",
        "Active requests:",
        json.dumps(active_requests(), ensure_ascii=False, indent=2, default=str),
    ]
    for thread in threading.enumerate():
        lines.append("-" * 88)
        lines.append(f"Thread name={thread.name!r} ident={thread.ident} daemon={thread.daemon} alive={thread.is_alive()}")
        frame = frames.get(thread.ident)
        if frame is None:
            lines.append("<no Python frame>")
        else:
            lines.extend(traceback.format_stack(frame))
    lines.append("=" * 88)
    try:
        path = log_path()
        with _lock:
            with path.open("a", encoding="utf-8", errors="replace") as handle:
                handle.write("\n".join(lines) + "\n")
                handle.flush()
    except Exception:
        pass
    log_event("thread_dump_written", reason=reason)


def _watchdog_loop(base_url: str) -> None:
    failures = 0
    _watchdog_stop.wait(5.0)
    while not _watchdog_stop.is_set():
        snapshot = active_requests()
        oldest_ms = float(snapshot[0].get("age_ms") or 0) if snapshot else 0.0
        if len(snapshot) >= 7:
            dump_threads(f"waitress_saturation active={len(snapshot)} oldest_ms={oldest_ms:.0f}")
        elif oldest_ms >= 8000:
            dump_threads(f"slow_request oldest_ms={oldest_ms:.0f}")

        ok = False
        error = ""
        started = time.monotonic()
        try:
            req = urllib.request.Request(
                base_url.rstrip("/") + "/api/diagnostics/ping",
                headers={"User-Agent": "PT2VHF-diagnostic-watchdog"},
            )
            with urllib.request.urlopen(req, timeout=2.0) as response:
                ok = int(response.status) == 200
                response.read(64)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"

        elapsed_ms = round((time.monotonic() - started) * 1000, 1)
        if ok:
            if failures:
                log_event("watchdog_recovered", previous_failures=failures, elapsed_ms=elapsed_ms)
            failures = 0
        else:
            failures += 1
            log_event("watchdog_probe_failed", failures=failures, elapsed_ms=elapsed_ms, error=error, active_requests=len(active_requests()))
            if failures >= 2:
                dump_threads(f"health_probe_failed_{failures}")

        _watchdog_stop.wait(3.0)


def start_watchdog(base_url: str) -> None:
    global _watchdog_thread
    with _lock:
        if _watchdog_thread and _watchdog_thread.is_alive():
            return
        _watchdog_stop.clear()
        _watchdog_thread = threading.Thread(
            target=_watchdog_loop,
            args=(str(base_url),),
            name="pt2vhf-diagnostic-watchdog",
            daemon=True,
        )
        _watchdog_thread.start()
    log_event("watchdog_started", base_url=base_url)


def stop_watchdog() -> None:
    _watchdog_stop.set()
    thread = _watchdog_thread
    if thread and thread.is_alive() and thread is not threading.current_thread():
        thread.join(timeout=1.0)
    log_event("watchdog_stopped")


def system_metrics() -> dict[str, Any]:
    """CPU/RAM do processo principal somadas aos processos filhos do WebView2."""
    global _metrics_prev_wall, _metrics_prev_cpu
    if psutil is None:
        return {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "memory_percent": 0.0,
            "app_cpu_percent": 0.0,
            "app_memory_mb": 0.0,
            "app_memory_percent": 0.0,
            "system_cpu_percent": 0.0,
            "system_memory_percent": 0.0,
            "system_memory_available_mb": 0.0,
            "process_count": 1,
            "thread_count": len(threading.enumerate()),
            "uptime_seconds": max(0.0, time.monotonic() - _metrics_started),
            "available": False,
        }

    root = psutil.Process(os.getpid())
    try:
        processes = [root, *root.children(recursive=True)]
    except Exception:
        processes = [root]

    cpu_total = 0.0
    rss_total = 0
    thread_total = 0
    alive = 0
    for proc in processes:
        try:
            times = proc.cpu_times()
            cpu_total += float(times.user) + float(times.system)
            rss_total += int(proc.memory_info().rss)
            thread_total += int(proc.num_threads())
            alive += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    now = time.monotonic()
    cpu_percent = 0.0
    with _metrics_lock:
        if _metrics_prev_wall is not None and _metrics_prev_cpu is not None:
            wall_delta = max(0.001, now - _metrics_prev_wall)
            cpu_delta = max(0.0, cpu_total - _metrics_prev_cpu)
            cores = max(1, int(psutil.cpu_count(logical=True) or 1))
            cpu_percent = min(100.0, (cpu_delta / wall_delta / cores) * 100.0)
        _metrics_prev_wall = now
        _metrics_prev_cpu = cpu_total

    system_cpu_percent = 0.0
    system_memory_percent = 0.0
    system_memory_available_mb = 0.0
    try:
        system_cpu_percent = min(100.0, max(0.0, float(psutil.cpu_percent(interval=None))))
    except Exception:
        system_cpu_percent = 0.0
    try:
        vm = psutil.virtual_memory()
        total_memory = max(1, int(vm.total))
        memory_percent = min(100.0, (rss_total / total_memory) * 100.0)
        system_memory_percent = min(100.0, max(0.0, float(vm.percent)))
        system_memory_available_mb = max(0.0, float(vm.available) / (1024 * 1024))
    except Exception:
        memory_percent = 0.0
    app_memory_mb = rss_total / (1024 * 1024)
    return {
        "cpu_percent": round(cpu_percent, 1),
        "memory_mb": round(app_memory_mb, 1),
        "memory_percent": round(memory_percent, 1),
        "app_cpu_percent": round(cpu_percent, 1),
        "app_memory_mb": round(app_memory_mb, 1),
        "app_memory_percent": round(memory_percent, 1),
        "system_cpu_percent": round(system_cpu_percent, 1),
        "system_memory_percent": round(system_memory_percent, 1),
        "system_memory_available_mb": round(system_memory_available_mb, 1),
        "process_count": alive,
        "thread_count": thread_total,
        "uptime_seconds": round(max(0.0, now - _metrics_started), 1),
        "available": True,
    }


def evaluate_resource_alerts(
    metrics: dict[str, Any], *, enabled: bool = True,
    cpu_threshold: float = 90.0, memory_threshold: float = 90.0,
    sustain_seconds: float = 30.0, cooldown_seconds: float = 600.0,
    hysteresis_points: float = 5.0, now: float | None = None,
    tracker_state: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Avalia alertas críticos sustentados com cooldown e histerese."""
    current = float(time.monotonic() if now is None else now)
    sustain = max(1.0, float(sustain_seconds))
    cooldown = max(0.0, float(cooldown_seconds))
    hysteresis = max(0.0, float(hysteresis_points))
    store = tracker_state if tracker_state is not None else _resource_alert_state
    specs = (
        ("app_cpu", "cpu", "app", "app_cpu_percent", float(cpu_threshold)),
        ("system_cpu", "cpu", "system", "system_cpu_percent", float(cpu_threshold)),
        ("app_memory", "memory", "app", "app_memory_percent", float(memory_threshold)),
        ("system_memory", "memory", "system", "system_memory_percent", float(memory_threshold)),
    )
    due: list[dict[str, Any]] = []
    with _resource_alert_lock:
        if not enabled:
            store.clear()
            return due
        for key, resource, scope, metric_key, threshold in specs:
            value = max(0.0, float(metrics.get(metric_key) or 0.0))
            item = store.setdefault(key, {"since": None, "last_alert": None, "critical": False})
            since = item.get("since")
            last_alert = item.get("last_alert")
            critical = bool(item.get("critical"))
            recovery_threshold = max(0.0, threshold - hysteresis)
            if value >= threshold:
                if since is None:
                    since = current
                    item["since"] = current
                sustained_for = max(0.0, current - float(since))
                cooldown_ready = last_alert is None or (current - float(last_alert)) >= cooldown
                if sustained_for >= sustain and cooldown_ready:
                    item["critical"] = True
                    item["last_alert"] = current
                    due.append({"key": key, "resource": resource, "scope": scope, "value": round(value, 1), "threshold": round(threshold, 1), "sustained_seconds": round(sustained_for, 1)})
                continue
            if critical:
                if value <= recovery_threshold:
                    item["since"] = None
                    item["last_alert"] = None
                    item["critical"] = False
            else:
                item["since"] = None
    return due
