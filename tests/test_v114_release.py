from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v114_tnc_health_component_is_owned_by_tnc_tab_only():
    js = read("pt2vhf_aprs/static/js/v111.js")
    start = js.index("function installTncOperations")
    end = js.index("function installDatabaseHealth", start)
    block = js[start:end]
    assert "const tab=$('#tab-tnc')" in block
    assert "tab.insertBefore(host" in block
    assert "host.parentElement!==tab" in block
    assert "#tab-config" not in block
    assert "#tab-about" not in block
