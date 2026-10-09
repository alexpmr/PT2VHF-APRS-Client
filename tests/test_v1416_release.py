from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1416_version_metadata():
    assert read("VERSION").strip() == "1.14.16"
    assert '__version__ = "1.14.16"' in read("pt2vhf_aprs/__init__.py")
    win = read("windows/version_info.txt")
    assert "(1, 14, 16, 0)" in win
    assert "'1.14.16'" in win


def test_v1416_tracklog_follow_mode_preserves_zoom():
    js = read("pt2vhf_aprs/static/js/app.js")
    assert "trackFollowCallsign" in js
    assert "function followTracklog(" in js
    assert "function centerFollowedTrack(" in js
    assert "state.map.panTo(point" in js
    assert "state.map.on('dragstart'" in js
    assert "clearTrackFollow();" in js
    assert "state.map.on('zoomend'" in js
    assert "centerFollowedTrack(call, line._pt2vhfTrackRows || [], { force: true, animate: false })" in js
    assert "line.on('click', () => {" in js
    assert "followTracklog(line._pt2vhfTrackCall, line._pt2vhfTrackRows || []);" in js


def test_v1416_ranking_route_fit_uses_maximum_possible_zoom():
    js = read("pt2vhf_aprs/static/js/app.js")
    start = js.index("function fitRfRouteBounds(")
    end = js.index("async function focusRfRecordRoute", start)
    body = js[start:end]
    assert "L.latLngBounds(valid)" in body
    assert "paddingTopLeft" in body
    assert "paddingBottomRight" in body
    assert "maxZoom: 13" not in body
    assert "rfRouteFitPadding()" in body
    assert "state.map.invalidateSize({ animate: false })" in body


def test_v1416_route_panel_area_is_reserved_during_fit():
    js = read("pt2vhf_aprs/static/js/app.js")
    start = js.index("function rfRouteFitPadding()")
    end = js.index("function fitRfRouteBounds(", start)
    body = js[start:end]
    assert "panel.getBoundingClientRect()" in body
    assert "mapContainer.getBoundingClientRect()" in body
    assert "panelRect.width + 18" in body
    assert "bottomRight[0] += reserve" in body
    assert "topLeft[0] += reserve" in body


def test_v1416_all_route_nodes_receive_visible_overlay():
    js = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "function rfRouteNodeCoordinates()" in js
    assert "for (const callValue of route.nodes || [])" in js
    assert "const hasNormalMarker = !!(normal && state.map.hasLayer(normal));" in js
    assert "rf-route-node-temp-wrap" in js
    assert "hasNormalMarker ? ' has-normal' : ''" in js
    assert "state.rfRouteNodeMarkers.set(call, marker);" in js
    assert ".rf-route-node-temp" in css
    assert ".rf-route-node-temp.has-normal" in css
    assert ".rf-route-node-temp.has-normal .rf-route-node-dot" in css


def test_v1416_backlog_items_are_closed():
    backlog = read("BACKLOG.md")
    assert "## Implementado na v1.14.16 — Mapa: seguir tracklog selecionado" in backlog
    assert "## Implementado na v1.14.16 — Estatísticas > Ranking: enquadramento automático do trajeto no mapa" in backlog
    assert "## Implementado na v1.14.16 — Mapa: exibir todos os nós envolvidos na rota analisada" in backlog
