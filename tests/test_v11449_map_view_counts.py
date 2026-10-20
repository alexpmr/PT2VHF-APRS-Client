"""v1.14.49: contagem das camadas de enlaces e tracklogs no menu Ver."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_map_view_tree_shows_layer_counts():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    for node, key in (("root:tracklogs", "tracklogs"), ("root:rf", "rf"),
                      ("root:mobile-rf", "mobile"), ("root:igate-links", "igate")):
        line = next(l for l in js.splitlines() if f"id: '{node}'" in l)
        assert f"count: state.mapLayerCounts.{key}" in line
    assert "Object.assign(state.mapLayerCounts, countTopologyLayers(state.topologyEdges));" in js
    assert "state.mapLayerCounts.tracklogs = [...trackPoints.values()].filter(points => points >= 2).length;" in js
    # A contagem usa os mesmos filtros da visão geral (expiração, coordenadas,
    # inferido > 250 km), independentemente da caixa estar marcada.
    helper = js[js.index("function topologyEdgeShownOnOverview("):js.index("function countTopologyLayers(")]
    assert "edge.render_on_overview === false" in helper
    assert "topologyEdgeDistanceKm(edge) > 250" in helper
    assert "rfLinksEnabled" not in helper
