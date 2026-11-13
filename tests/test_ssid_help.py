"""Sugestões de SSID (WB4APR) na Configuração → Estação."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_ssid_help_is_loaded_after_config_tabs():
    html = read("pt2vhf_aprs/templates/index.html")
    assert "css/ssid_help.css" in html
    assert html.index("js/ssid_help.js") > html.index("js/config_tabs.js")


def test_ssid_help_lists_all_16_ssids_and_respects_opt_out():
    js = read("pt2vhf_aprs/static/js/ssid_help.js")
    numbers = [int(n) for n in re.findall(r"^\s*\[(\d+), '", js, re.M)]
    assert numbers == list(range(16))
    assert "Móvel principal" in js and "Estações meteorológicas" in js
    assert "pt2vhf_ssid_help_hidden" in js
    assert "#configForm [name=\"ssid\"]" in js
