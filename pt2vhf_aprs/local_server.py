from __future__ import annotations

import json
import os
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

DEFAULT_HOST = "127.0.0.1"
DEFAULT_START_PORT = 8080
DEFAULT_PORT_ATTEMPTS = 100

_runtime_lock = threading.Lock()
_runtime: dict[str, Any] = {
    "host": DEFAULT_HOST,
    "port": None,
    "url": "",
    "server": "",
    "fallback_count": 0,
}


def configured_start_port() -> int:
    raw = str(os.getenv("PT2VHF_PORT", str(DEFAULT_START_PORT)) or "").strip()
    try:
        port = int(raw)
    except Exception as exc:
        raise ValueError(f"PT2VHF_PORT inválida: {raw!r}") from exc
    if not (1 <= port <= 65535):
        raise ValueError("PT2VHF_PORT deve ficar entre 1 e 65535.")
    return port


def configured_host() -> str:
    return str(os.getenv("PT2VHF_HOST", DEFAULT_HOST) or DEFAULT_HOST).strip() or DEFAULT_HOST


def _default_server_factory(app: Any, host: str, port: int, threads: int) -> tuple[str, Any]:
    """Cria e faz bind do servidor antes de retornar.

    O bind real dentro de create_server/make_server evita a condição de corrida
    de testar uma porta, liberá-la e só depois tentar abrir o servidor.
    """
    try:
        from waitress import create_server

        server = create_server(
            app,
            host=host,
            port=port,
            threads=max(1, int(threads)),
            url_scheme="http",
        )
        return "waitress", server
    except ImportError:
        from werkzeug.serving import make_server

        server = make_server(host, port, app, threaded=True)
        return "werkzeug", server


@dataclass
class LocalServerHandle:
    server: Any
    server_kind: str
    host: str
    port: int
    start_port: int
    thread: threading.Thread | None = None
    runtime_file: Path | None = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def fallback_count(self) -> int:
        return max(0, int(self.port) - int(self.start_port))

    def start(self) -> "LocalServerHandle":
        if self.thread and self.thread.is_alive():
            return self

        def _run() -> None:
            if hasattr(self.server, "run"):
                self.server.run()
            else:
                self.server.serve_forever()

        self.thread = threading.Thread(
            target=_run,
            name="pt2vhf-http",
            daemon=True,
        )
        self.thread.start()
        _set_runtime(self)
        if self.runtime_file:
            _write_runtime_file(self.runtime_file, self)
        return self

    def wait_ready(self, timeout: float = 12.0) -> bool:
        deadline = time.time() + max(0.1, float(timeout))
        while time.time() < deadline:
            try:
                with socket.create_connection((self.host, self.port), timeout=0.4):
                    return True
            except OSError:
                time.sleep(0.12)
        return False

    def close(self) -> None:
        try:
            if hasattr(self.server, "close"):
                self.server.close()
            elif hasattr(self.server, "shutdown"):
                self.server.shutdown()
        except Exception:
            pass
        try:
            if hasattr(self.server, "server_close"):
                self.server.server_close()
        except Exception:
            pass

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)

        if self.runtime_file:
            _remove_runtime_file(self.runtime_file)
        _clear_runtime(self)


def allocate_local_server(
    app: Any,
    *,
    host: str | None = None,
    start_port: int | None = None,
    attempts: int = DEFAULT_PORT_ATTEMPTS,
    threads: int = 8,
    runtime_file: Path | None = None,
    server_factory: Callable[[Any, str, int, int], tuple[str, Any]] | None = None,
) -> LocalServerHandle:
    host = str(host or configured_host()).strip() or DEFAULT_HOST
    start = int(start_port if start_port is not None else configured_start_port())
    attempts = max(1, min(int(attempts or DEFAULT_PORT_ATTEMPTS), 1000))
    factory = server_factory or _default_server_factory

    last_error: BaseException | None = None
    for offset in range(attempts):
        port = start + offset
        if port > 65535:
            break
        try:
            kind, server = factory(app, host, port, threads)
            return LocalServerHandle(
                server=server,
                server_kind=str(kind or "server"),
                host=host,
                port=port,
                start_port=start,
                runtime_file=runtime_file,
            )
        except OSError as exc:
            last_error = exc
            continue

    suffix = f": {last_error}" if last_error else ""
    raise OSError(
        f"Nenhuma porta local disponível entre {start} e "
        f"{min(65535, start + attempts - 1)}{suffix}"
    )


def start_local_server(
    app: Any,
    *,
    host: str | None = None,
    start_port: int | None = None,
    attempts: int = DEFAULT_PORT_ATTEMPTS,
    threads: int = 8,
    runtime_file: Path | None = None,
) -> LocalServerHandle:
    handle = allocate_local_server(
        app,
        host=host,
        start_port=start_port,
        attempts=attempts,
        threads=threads,
        runtime_file=runtime_file,
    )
    handle.start()
    return handle


def runtime_info() -> dict[str, Any]:
    with _runtime_lock:
        return dict(_runtime)


def _set_runtime(handle: LocalServerHandle) -> None:
    with _runtime_lock:
        _runtime.update({
            "host": handle.host,
            "port": int(handle.port),
            "url": handle.url,
            "server": handle.server_kind,
            "fallback_count": handle.fallback_count,
        })


def _clear_runtime(handle: LocalServerHandle) -> None:
    with _runtime_lock:
        if int(_runtime.get("port") or 0) == int(handle.port):
            _runtime.update({
                "host": DEFAULT_HOST,
                "port": None,
                "url": "",
                "server": "",
                "fallback_count": 0,
            })


def runtime_file_for(data_dir: Path) -> Path:
    return Path(data_dir) / "local_server.json"


def _write_runtime_file(path: Path, handle: LocalServerHandle) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pid": os.getpid(),
            "host": handle.host,
            "port": int(handle.port),
            "url": handle.url,
            "started_at": int(time.time()),
        }
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _remove_runtime_file(path: Path) -> None:
    try:
        if not path.exists():
            return
        payload = json.loads(path.read_text(encoding="utf-8"))
        if int(payload.get("pid") or 0) == os.getpid():
            path.unlink(missing_ok=True)
    except Exception:
        pass


def read_runtime_url(data_dir: Path) -> str:
    path = runtime_file_for(data_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        host = str(payload.get("host") or DEFAULT_HOST)
        port = int(payload.get("port") or 0)
        if not (1 <= port <= 65535):
            return ""
        with socket.create_connection((host, port), timeout=0.25):
            return f"http://{host}:{port}"
    except Exception:
        return ""
