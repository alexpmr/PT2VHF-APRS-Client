"""v1.14.45: enlaces RF ficam contínuos e obedecem às cores configuradas (#122)."""
from pathlib import Path

APP = (Path(__file__).resolve().parents[1]
       / "pt2vhf_aprs" / "static" / "js" / "app.js")


def _topology_style_source() -> str:
    js = APP.read_text(encoding="utf-8")
    start = js.index("const inferredRouteEdge = edge.kind !== 'igate'")
    return js[start:js.index("if (!line) {", start)]


def test_rf_inferred_uses_same_configurable_color_as_direct_rf():
    block = _topology_style_source()
    assert ("edge.kind === 'igate' ? state.mapConfig.topology_igate_color"
            " : state.mapConfig.topology_rf_color") in block
    assert "inferredRouteEdge ? '#9ca3af'" not in block
    assert "topology_rf_color" in block
    assert ": state.mapConfig.topology_width" in block


def test_rf_links_are_solid_while_internet_stays_dashed():
    block = _topology_style_source()
    assert ("dashArray: edge.kind === 'igate' ? '7 5' "
            ": mobileRf ? '2 5' : null") in block
    assert "inferredRouteEdge ? '5 6'" not in block
    assert "opacity: edge.kind === 'igate' ? .72 : .84" in block


def test_distinct_temporary_and_mobile_styles_are_preserved():
    block = _topology_style_source()
    for item in (
        "state.mapConfig.topology_rf_mobile_color",
        "state.mapConfig.topology_rf_temporary_color",
        "state.mapConfig.topology_rf_mobile_width",
        "state.mapConfig.topology_rf_temporary_width",
    ):
        assert item in block


def test_inferred_evidence_remains_labeled_not_promoted_to_direct():
    js = APP.read_text(encoding="utf-8")
    assert "RF inferido (não confirmado diretamente)" in js
    assert "RF recebido pelo TNC" in js
    assert "const inferredRouteEdge = edge.kind !== 'igate'" in js
    assert "if (!routeAllowedPairs && edge.render_on_overview === false) continue" in js
