"""Validação do indicativo de radioamador da Configuração (v2.0.3).

Antes bastava "1 a 6 letras ou números", o que deixava passar coisas como PQP2TF,
que não existe. Agora o indicativo precisa ter a estrutura ITU de um indicativo
de radioamador: prefixo, um dígito e um sufixo terminado em letra. Indicativos
brasileiros (PP–PY e ZV–ZZ) seguem o formato da Anatel: duas letras, um dígito
de 0 a 9 e de uma a três letras (PY2ABC, PU2MUS, PP5AU, ZV2A).

A mesma regra existe em static/js/app.js (isValidAmateurCallsign); mantenha as
duas iguais.
"""
from __future__ import annotations

import re
from typing import Any

# Prefixo ITU: uma ou duas letras, dígito+letra (2E, 9A) ou letra+dígito (E7, H4);
# depois o dígito da região e o sufixo (até 4 caracteres, terminando em letra).
ITU_CALLSIGN_RE = re.compile(r"(?:[A-Z]{1,2}|[0-9][A-Z]|[A-Z][0-9])[0-9][A-Z0-9]{0,3}[A-Z]")
# Séries brasileiras de radioamador.
BRAZIL_PREFIX_RE = re.compile(r"P[P-Y]|Z[V-Z]")
BRAZIL_CALLSIGN_RE = re.compile(r"(?:P[P-Y]|Z[V-Z])[0-9][A-Z]{1,3}")


def normalize(callsign: Any) -> str:
    return str(callsign or "").strip().upper()


def is_valid_amateur_callsign(callsign: Any) -> bool:
    """True se for um indicativo-base de radioamador plausível (sem SSID), até 6 caracteres."""
    call = normalize(callsign)
    if not 3 <= len(call) <= 6 or not ITU_CALLSIGN_RE.fullmatch(call):
        return False
    if BRAZIL_PREFIX_RE.match(call):
        return bool(BRAZIL_CALLSIGN_RE.fullmatch(call))
    return True
