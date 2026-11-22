"""v2.0.3: validação do indicativo de radioamador na Configuração (caso PQP2TF)."""
import re
from pathlib import Path

import pytest

from pt2vhf_aprs.callsign_rules import is_valid_amateur_callsign

ROOT = Path(__file__).resolve().parents[1]
VALID = ["PY2ABC", "PU2MUS", "PT2VHF", "PP5AU", "ZV2A", "PY0F", "W1AW", "K1A", "2E0ABC",
         "VK2ABC", "9A1AA", "E73A", "DL1ABC", "JA1ABC", "N0CALL", "py2abc"]
INVALID = ["PQP2TF", "PY2ABCD", "PY22AB", "PY2AB1", "ABC", "123", "PY2", "TESTE", "A1",
           "PYABCD", "PY2-ABC", "", "PY2ABC-9"]


@pytest.mark.parametrize("call", VALID)
def test_valid_callsigns(call):
    assert is_valid_amateur_callsign(call)


@pytest.mark.parametrize("call", INVALID)
def test_invalid_callsigns(call):
    assert not is_valid_amateur_callsign(call)


def test_js_rule_matches_python():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "function isValidAmateurCallsign" in js
    assert "[A-Z]{1,2}|[0-9][A-Z]|[A-Z][0-9])[0-9][A-Z0-9]{0,3}[A-Z]$" in js
    assert "(?:P[P-Y]|Z[V-Z])[0-9][A-Z]{1,3}$" in js
    assert not re.search(r"\^\[A-Z0-9\]\{1,6\}\$/\.test\(callsign\)", js)
