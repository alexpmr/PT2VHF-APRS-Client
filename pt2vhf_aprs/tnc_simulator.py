from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable

from .tnc_service import encode_ax25, kiss_encode


@dataclass
class SimulatedHop:
    callsign: str
    repeated: bool = False


@dataclass
class SimulatedPacket:
    source: str
    destination: str
    info: str
    path: list[str] = field(default_factory=list)

    def ax25(self) -> bytes:
        return encode_ax25(self.source, self.destination, self.info, self.path)

    def kiss(self) -> bytes:
        return kiss_encode(self.ax25())


class KISSSimulator:
    """Gerador determinístico de cenários KISS para regressão sem rádio físico."""

    def __init__(self, *, fragment_size: int = 0, duplicate_every: int = 0, drop_every: int = 0) -> None:
        self.fragment_size = max(0, int(fragment_size))
        self.duplicate_every = max(0, int(duplicate_every))
        self.drop_every = max(0, int(drop_every))

    def scenario(self, packets: Iterable[SimulatedPacket]) -> list[bytes]:
        chunks: list[bytes] = []
        for index, packet in enumerate(packets, start=1):
            if self.drop_every and index % self.drop_every == 0:
                continue
            frame = packet.kiss()
            copies = 2 if self.duplicate_every and index % self.duplicate_every == 0 else 1
            for _ in range(copies):
                if self.fragment_size:
                    chunks.extend(frame[i:i+self.fragment_size] for i in range(0, len(frame), self.fragment_size))
                else:
                    chunks.append(frame)
        return chunks

    @staticmethod
    def multi_hop_demo() -> list[SimulatedPacket]:
        return [
            SimulatedPacket("PT2AAA-7", "APZVHF", "!1550.00S/04750.00W>demo", ["WIDE1-1", "WIDE2-1"]),
            SimulatedPacket("PT2BBB", "APZVHF", ":PT2AAA-7:teste{01", ["PT2DIGI-1*", "WIDE2-1"]),
            SimulatedPacket("PT2AAA-7", "APZVHF", ":PT2BBB  :ack01", ["PT2DIGI-1*", "PT2IGATE*"]),
        ]
