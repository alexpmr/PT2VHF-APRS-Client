"""Guard the compact CPU/RAM header arrangement (#109)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_header_metrics_are_stacked_and_keep_their_values_and_bars():
    css = _source("pt2vhf_aprs/static/css/app.css")
    html = _source("pt2vhf_aprs/templates/index.html")
    script = _source("pt2vhf_aprs/static/js/app.js")
    block = css.split(".system-resource-meter {", 1)[1].split("}", 1)[0]
    assert "flex-direction: column;" in block
    assert "width: 98px;" in block
    assert "gap: 2px;" in block
    assert html.index('id="cpuResourceMetric"') < html.index('id="memoryResourceMetric"')
    for id_ in ("headerCpuUsage", "headerMemoryUsage", "headerCpuBar", "headerMemoryBar"):
        assert f'id="{id_}"' in html
        assert f"$('#{id_}')" in script
    assert '.resource-metric[data-level="critical"] .resource-fill' in css
    assert '.resource-metric[data-level="warn"] .resource-fill' in css
    assert '@media (max-width: 980px) { .system-resource-meter { display: none; } }' in css
