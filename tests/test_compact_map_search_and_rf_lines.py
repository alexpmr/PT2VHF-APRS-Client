"""Regression checks for compact map search layout and route-edge rendering safety."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_search_toolbar_is_one_row_and_clear_does_not_create_second_row():
    css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    tail = css[css.index("/* #94 / #98: one-row RF search"):]
    assert "display: flex;" in tail
    assert "flex-wrap: nowrap;" in tail
    assert ".rf-route-search label > span" in tail
    assert 'id="rfRouteClear"' in html
    assert 'placeholder="Destino RF"' in html
    for name in ("rfRouteSource", "rfRouteTarget", "rfRouteApply", "rfPossibleRoutes", "rfRouteClear"):
        assert f'id="{name}"' in html


def test_route_focus_uses_server_filtered_edges_and_no_synthetic_geometry():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    start = js.index("  async function loadTopology()")
    end = js.index("  function locateBrowser(", start)
    body = js[start:end]
    assert "const renderEdges = [...edges];" in body
    assert "const geometryEdge = edge;" in body
    assert "synthetic_route_edge: true" not in body
    assert "renderEdges.push({" not in body
