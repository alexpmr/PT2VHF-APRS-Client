"""Teste de escuta do TNC: recebe bytes durante alguns segundos e explica o resultado.

Nunca transmite. Com o TNC já conectado, apenas observa a sessão atual (sem
disputar a porta); desconectado, abre o transporte configurado só para ler.
"""
from __future__ import annotations

import socket
import time
from typing import Any

from . import diagnostics as diag
from . import tnc_service as tnc
from .agwpe_transport import AGWPEStreamDecoder, AGWPETransport, enable_raw_command

MIN_SECONDS = 3
MAX_SECONDS = 30
COMMON_BAUDS = (1200, 4800, 9600, 19200, 38400, 57600, 115200)


def _clamp_seconds(value: Any) -> int:
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        seconds = 10
    return max(MIN_SECONDS, min(seconds, MAX_SECONDS))


def _printable_ratio(data: bytes) -> float:
    if not data:
        return 0.0
    printable = sum(1 for b in data if 32 <= b <= 126 or b in (9, 10, 13))
    return printable / len(data)


def _analyse(data: bytes, transport: str) -> dict[str, Any]:
    """Decodifica KISS/AX.25 de um bloco capturado."""
    kiss = 0
    valid: list[str] = []
    invalid: list[str] = []
    if transport == "agwpe":
        payloads = [f.data for f in AGWPEStreamDecoder().feed(data) if f.kind == "K" and f.data]
    else:
        payloads = [p for cmd, p in tnc.KissStreamDecoder().feed(data) if (cmd & 0x0F) == 0 and p]
    for payload in payloads:
        kiss += 1
        try:
            valid.append(tnc.decode_ax25(payload)["tnc2"])
        except Exception as exc:
            invalid.append(str(exc))
    return {"kiss_frames": kiss, "packets": valid, "invalid": invalid}


def diagnose(*, bytes_rx: int, kiss_frames: int, valid: int, invalid: int,
             printable: float, protocol: str, seconds: int, serial_baud: int,
             transport: str, error: str = "") -> tuple[str, list[str]]:
    """Retorna (veredito, dicas em português) a partir do que foi observado."""
    if error:
        hints = [f"Não foi possível abrir o transporte: {error}"]
        if transport == "serial":
            hints += [
                "Confira se a porta COM é a do cabo/interface do rádio (aba TNC → Reescanear).",
                "Feche outros programas que usam a mesma porta (UI-View, APRSIS32, Dire Wolf, programa do rádio).",
            ]
        else:
            hints.append("Confira host/porta e se o software TNC (ex.: Dire Wolf) está em execução.")
        return "error", hints
    if valid:
        hints = [f"Recepção OK: {valid} pacote(s) AX.25 válido(s) em {seconds} s."]
        if invalid:
            hints.append(f"Também houve {invalid} frame(s) inválido(s) — normal com sinal fraco.")
        return "ok", hints
    if bytes_rx == 0:
        hints = [f"Nenhum byte chegou em {seconds} s: o TNC não está enviando nada ao programa."]
        if transport == "serial":
            hints += [
                "Cabo e porta: confirme a COM correta e o cabo de dados (não só de carga).",
                "Rádio/TNC precisa estar em modo KISS (ou PKT) — no modo normal ele não manda pacotes pela serial.",
                f"Velocidade serial ({serial_baud} bps) deve ser a mesma configurada no TNC/rádio.",
                "Linhas RTS/DTR: em alguns cabos elas travam o rádio; teste ambas “Desativadas”.",
            ]
        hints += [
            "Frequência APRS com tráfego (Brasil: 145.570 MHz) e squelch/volume do TNC ajustados.",
            "Se não houver estações por perto, aumente o tempo do teste — silêncio no ar também dá zero bytes.",
        ]
        return "no_bytes", hints
    if protocol == "terminal":
        return "terminal_bytes", [
            f"{bytes_rx} byte(s) recebidos em modo terminal/texto, como esperado para o perfil escolhido.",
        ]
    if kiss_frames == 0:
        if printable >= 0.85:
            return "text_not_kiss", [
                f"Chegaram {bytes_rx} byte(s) de texto legível, mas não em KISS: o TNC está em modo terminal/comando.",
                "Coloque o TNC em KISS (ex.: comando KISS ON + RESTART, ou menu do rádio) "
                "ou escolha o protocolo “terminal” se for esse o modo desejado.",
            ]
        others = ", ".join(str(b) for b in COMMON_BAUDS if b != serial_baud)
        return "garbage_not_kiss", [
            f"Chegaram {bytes_rx} byte(s) ilegíveis e nenhum frame KISS: velocidade serial provavelmente errada.",
            f"Atual: {serial_baud} bps. Tente as velocidades comuns: {others}.",
        ]
    return "invalid_ax25", [
        f"{kiss_frames} frame(s) KISS chegaram, mas nenhum AX.25 válido.",
        "Verifique se o TNC está em 1200 baud APRS (AFSK) e se o nível de áudio não está saturado.",
    ]


def _capture(cfg: dict[str, Any], seconds: int) -> tuple[bytes, str]:
    """Abre o transporte configurado só para ler durante `seconds`."""
    transport = str(cfg.get("transport") or "")
    deadline = time.monotonic() + seconds
    chunks: list[bytes] = []
    if transport == "serial":
        if tnc.serial is None:
            raise RuntimeError("pyserial não está instalado.")
        if not cfg.get("serial_port"):
            raise ValueError("Porta serial não configurada.")
        handle = tnc.open_serial_port(cfg, timeout=0.25, write_timeout=1.0)
        endpoint = f"{cfg['serial_port']} @ {cfg['serial_baud']}"
        try:
            while time.monotonic() < deadline:
                waiting = int(getattr(handle, "in_waiting", 0) or 0)
                chunk = handle.read(max(1, min(waiting or 1, 8192)))
                if chunk:
                    chunks.append(bytes(chunk))
        finally:
            handle.close()
        return b"".join(chunks), endpoint
    if transport == "tcp":
        endpoint = f"{cfg['tcp_host']}:{cfg['tcp_port']}"
        handle = socket.create_connection((cfg["tcp_host"], int(cfg["tcp_port"])), timeout=3.0)
    elif transport == "agwpe":
        endpoint = f"{cfg['agwpe_host']}:{cfg['agwpe_port']}"
        handle = AGWPETransport(cfg["agwpe_host"], int(cfg["agwpe_port"]), timeout=3.0)
        handle.sendall(enable_raw_command())
    else:
        raise ValueError(f"Transporte não suportado: {transport}")
    try:
        handle.settimeout(0.25)
        while time.monotonic() < deadline:
            try:
                chunk = handle.recv(8192)
            except socket.timeout:
                continue
            if not chunk:
                break
            chunks.append(bytes(chunk))
    finally:
        handle.close()
    return b"".join(chunks), endpoint


def listen_test(seconds: Any = 10, *, service: Any = None, sleep=time.sleep) -> dict[str, Any]:
    seconds = _clamp_seconds(seconds)
    cfg = tnc.normalize_tnc_config(tnc.get_tnc_config(), strict=False)
    transport = str(cfg.get("transport") or "")
    protocol = str(cfg.get("serial_protocol") or "kiss") if transport == "serial" else "kiss"
    service = service if service is not None else tnc.service
    result: dict[str, Any] = {
        "seconds": seconds, "transport": transport, "protocol": protocol,
        "serial_baud": int(cfg.get("serial_baud") or 9600),
        "mode": "", "endpoint": "", "bytes_rx": 0, "kiss_frames": 0,
        "valid_packets": 0, "invalid_frames": 0, "packets": [],
        "sample_hex": "", "sample_ascii": "", "error": "",
    }
    printable = 0.0
    live = service.status()
    if live.get("connected"):
        # Sessão ativa: observa contadores e o monitor, sem abrir a porta de novo.
        result["mode"] = "session"
        result["endpoint"] = str(live.get("endpoint") or "")
        start_seq = service.rx_monitor(10 ** 12)["seq"]
        sleep(seconds)
        monitor = service.rx_monitor(start_seq)
        entries = monitor["entries"]
        raw = [e for e in entries if e["kind"] == "bytes"]
        result["bytes_rx"] = sum(int(e["size"]) for e in raw)
        result["packets"] = [e["text"] for e in entries if e["kind"] == "ax25"][:10]
        result["valid_packets"] = sum(1 for e in entries if e["kind"] == "ax25")
        result["invalid_frames"] = sum(1 for e in entries if e["kind"] == "invalid")
        result["kiss_frames"] = result["valid_packets"] + result["invalid_frames"]
        if raw:
            result["sample_hex"] = raw[0]["hex"]
            result["sample_ascii"] = raw[0]["ascii"]
            printable = _printable_ratio(bytes.fromhex("".join(e["hex"].replace(" ", "") for e in raw)))
    else:
        result["mode"] = "standalone"
        try:
            data, result["endpoint"] = _capture(cfg, seconds)
        except Exception as exc:
            data = b""
            result["error"] = str(exc)
        analysis = _analyse(data, transport)
        result["bytes_rx"] = len(data)
        result["kiss_frames"] = analysis["kiss_frames"]
        result["valid_packets"] = len(analysis["packets"])
        result["invalid_frames"] = len(analysis["invalid"])
        result["packets"] = analysis["packets"][:10]
        safe = data[:128]
        result["sample_hex"] = safe.hex(" ")
        result["sample_ascii"] = "".join(chr(b) if 32 <= b <= 126 else "." for b in safe)
        printable = _printable_ratio(data)
    verdict, hints = diagnose(
        bytes_rx=result["bytes_rx"], kiss_frames=result["kiss_frames"],
        valid=result["valid_packets"], invalid=result["invalid_frames"],
        printable=printable, protocol=protocol, seconds=seconds,
        serial_baud=result["serial_baud"], transport=transport, error=result["error"],
    )
    result.update({"ok": verdict in {"ok", "terminal_bytes"}, "verdict": verdict, "hints": hints})
    diag.log_event("tnc_listen_test", **{k: v for k, v in result.items() if k not in {"packets", "hints"}})
    return result
