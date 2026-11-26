"""v2.0.6: parse APRS com os ajustes que o aprslib não faz (pedido do Alex, LoRa APRS).

Trackers e iGates LoRa APRS (ex.: CA2RXU, destino APLRG1/APLRT1) usam quase sempre a
posição comprimida (Base91), como ``=LXc#7C\\1ha !GLoRa APRS``. O aprslib já decodifica
posição, rumo/velocidade, altitude e alcance comprimidos; aqui ficam só as lacunas:

- Na posição comprimida, o overlay numérico 0-9 vem codificado como ``a``-``j`` (spec APRS
  1.01, cap. 9). O aprslib devolve a letra; o mapa mostrava "a" em vez de "0" sobre o ícone.
- Item (``)NOME!posição`` / ``)NOME_posição``), comprimido ou não: o aprslib recusa o
  formato e o pacote era descartado. Aqui ele vira um objeto (``format = "item"``).
"""
from __future__ import annotations

import re
from typing import Any

try:  # pragma: no cover - o app sempre empacota o aprslib
    import aprslib
except Exception:  # pragma: no cover
    aprslib = None

_COMPRESSED_OVERLAY = {chr(ord("a") + n): str(n) for n in range(10)}
_ITEM = re.compile(r"^\)(?P<name>[^!_]{3,9})(?P<state>[!_])(?P<position>.+)$", re.S)


def _fix_compressed_overlay(parsed: dict[str, Any]) -> dict[str, Any]:
    table = parsed.get("symbol_table")
    if isinstance(table, str) and table in _COMPRESSED_OVERLAY:
        parsed["symbol_table"] = _COMPRESSED_OVERLAY[table]
    return parsed


def _parse_item(line: str) -> dict[str, Any] | None:
    if aprslib is None or ":" not in line:
        return None
    header, info = line.split(":", 1)
    match = _ITEM.match(info)
    if not match:
        return None
    # A posição do item tem o mesmo formato de um relatório "!" (comprimido ou não).
    parsed = aprslib.parse(f"{header}:!{match['position']}")
    parsed["raw"] = line
    parsed["format"] = "item"
    parsed["item_name"] = parsed["object_name"] = match["name"].strip()
    parsed["alive"] = match["state"] == "!"
    parsed.pop("messagecapable", None)
    return parsed


def parse(line: str) -> dict[str, Any]:
    """Como ``aprslib.parse``; levanta a mesma exceção quando nem o item resolve."""
    if aprslib is None:
        return {}
    try:
        parsed = aprslib.parse(line)
    except Exception:
        item = _parse_item(str(line or ""))
        if item is None:
            raise
        parsed = item
    return _fix_compressed_overlay(parsed)
