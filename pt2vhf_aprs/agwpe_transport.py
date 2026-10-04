from __future__ import annotations

import socket
import struct
from dataclasses import dataclass
from typing import Iterable

AGWPE_HEADER = struct.Struct("<II10s10sII")
AGWPE_HEADER_SIZE = AGWPE_HEADER.size
AGWPE_MAX_DATA = 1024 * 1024


def _call_field(value: str) -> bytes:
    raw = str(value or "").encode("ascii", errors="ignore")[:9]
    return raw + b"\x00" * (10 - len(raw))


def encode_frame(kind: str, data: bytes = b"", *, port: int = 0, call_from: str = "", call_to: str = "", user: int = 0) -> bytes:
    if len(kind) != 1:
        raise ValueError("AGWPE kind deve ter um caractere.")
    payload = bytes(data or b"")
    if len(payload) > AGWPE_MAX_DATA:
        raise ValueError("Frame AGWPE excede o limite de segurança.")
    return AGWPE_HEADER.pack(
        int(port) & 0xFFFFFFFF,
        ord(kind) & 0xFF,
        _call_field(call_from),
        _call_field(call_to),
        len(payload),
        int(user) & 0xFFFFFFFF,
    ) + payload


def enable_raw_command() -> bytes:
    return encode_frame("k")


def radio_ports_command() -> bytes:
    return encode_frame("G")


def raw_tx_frame(ax25: bytes, *, port: int = 0) -> bytes:
    return encode_frame("K", bytes(ax25), port=port)


@dataclass(frozen=True)
class AGWPEFrame:
    port: int
    kind: str
    call_from: str
    call_to: str
    user: int
    data: bytes


class AGWPEStreamDecoder:
    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, chunk: bytes) -> list[AGWPEFrame]:
        if chunk:
            self._buffer.extend(chunk)
        out: list[AGWPEFrame] = []
        while len(self._buffer) >= AGWPE_HEADER_SIZE:
            port, kind_value, from_raw, to_raw, data_len, user = AGWPE_HEADER.unpack_from(self._buffer)
            if data_len < 0 or data_len > AGWPE_MAX_DATA:
                self._buffer.clear()
                raise ValueError(f"Comprimento AGWPE inválido: {data_len}")
            total = AGWPE_HEADER_SIZE + data_len
            if len(self._buffer) < total:
                break
            payload = bytes(self._buffer[AGWPE_HEADER_SIZE:total])
            del self._buffer[:total]
            out.append(AGWPEFrame(
                port=int(port),
                kind=chr(kind_value & 0xFF),
                call_from=from_raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore"),
                call_to=to_raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore"),
                user=int(user),
                data=payload,
            ))
        return out


class AGWPETransport:
    def __init__(self, host: str, port: int, timeout: float = 8.0) -> None:
        self.sock = socket.create_connection((host, int(port)), timeout=timeout)
        self.sock.settimeout(1.0)

    def recv(self, size: int = 8192) -> bytes:
        return self.sock.recv(size)

    def sendall(self, data: bytes) -> None:
        self.sock.sendall(data)

    def shutdown(self, how: int = socket.SHUT_RDWR) -> None:
        self.sock.shutdown(how)

    def close(self) -> None:
        self.sock.close()
