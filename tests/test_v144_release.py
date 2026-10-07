from __future__ import annotations

from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v144_version_metadata():
    assert text("VERSION").strip() == "1.14.4"
    assert '__version__ = "1.14.4"' in text("pt2vhf_aprs/__init__.py")
    win = text("windows/version_info.txt")
    for marker in (
        "filevers=(1, 14, 4, 0)", "prodvers=(1, 14, 4, 0)",
        "FileVersion', '1.14.4'", "ProductVersion', '1.14.4'",
    ):
        assert marker in win


def test_v144_modal_uses_real_save_restore_and_target_navigation():
    js = text("pt2vhf_aprs/static/js/app.js")
    html = text("pt2vhf_aprs/templates/index.html")
    assert "async function resolveUnsavedConfig(mode)" in js
    assert "async function saveConfigForm()" in js
    assert "saved = await saveConfigForm()" in js
    assert "if (!await loadConfig())" in js
    assert "activateTab(target)" in js
    assert "pendingConfigFeedback" in js
    assert "state.configTransitionBusy" in js
    assert 'id="unsavedConfigActionStatus"' in html
    assert "role=\"status\"" in html
    assert "void resolveUnsavedConfig('save')" in js
    assert "void resolveUnsavedConfig('discard')" in js
    assert "void resolveUnsavedConfig('cancel')" in js


def test_v144_right_click_reuses_message_safety_and_composer():
    js = text("pt2vhf_aprs/static/js/app.js")
    start = js.index("$('#stationsTable tbody')?.addEventListener('contextmenu'")
    body = js[start: start + 420]
    assert "event.preventDefault()" in body
    assert "event.stopPropagation()" in body
    assert "openStationQuickMessage(row.dataset.callsign || '')" in body
    assert "const safety = stationMessagingSafety(station)" in js


def test_v144_icon_compact_and_brand_kept():
    import pytest
    pytest.importorskip("PIL")
    from tools.compact_icon import render_compact_icon
    icon = render_compact_icon(256)
    assert icon.size == (256, 256)
    assert icon.getpixel((0, 0))[3] == 0
    assert icon.getpixel((128, 128))[3] == 255
    assert "app_logo.png" in text("windows/make_icon.py")
    assert "app_logo.png" in text("macos/make_icon.py")
    assert "render_compact_icon(256)" in text("linux/build_linux.sh")
    assert "img/app_logo.png" in text("pt2vhf_aprs/templates/index.html")


def test_v144_real_aprsis_path_is_igate_and_rf_is_not_internet():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "v144.db"
            db.init_db()
            for call, lat, lon in (
                ("PY2NET-9", -15.72, -47.72),
                ("PT2IGT-15", -15.81, -47.91),
                ("PY2RF-9", -15.88, -47.82),
                ("PT2DGI", -15.85, -47.75),
            ):
                db.upsert_station({
                    "from": call, "format": "uncompressed",
                    "latitude": lat, "longitude": lon, "symbol_table": "/",
                    "symbol": ">", "altitude": 1000, "comment": "Teste v1.14.4",
                    "path": [], "raw": f"{call}>APRS:>teste",
                })
            db.record_topology_from_raw(
                "PY2NET-9>APRS,TCPIP*,qAr,PT2IGT-15:>internet",
                medium="APRS-IS",
            )
            db.record_topology_from_raw(
                "PY2RF-9>APRS,PT2DGI*,WIDE2-1,qAR,PT2IGT-15:>rf",
                medium="RF",
            )
            rows = db.list_topology_edges(hours=24)
            edges = {(r["source"], r["target"]): r for r in rows}
            internet = edges["PY2NET-9", "PT2IGT-15"]
            assert internet["kind"] == "igate"
            assert internet["internet_confirmed_count"] >= 1
            assert float(internet["target_lat"]) == -15.81
            assert edges["PY2RF-9", "PT2DGI"]["kind"] == "rf"
            assert edges["PT2DGI", "PT2IGT-15"]["kind"] == "rf"
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_v144_igate_link_layer_is_independent_of_hidden_markers():
    js = text("pt2vhf_aprs/static/js/app.js")
    start = js.index("async function loadTopology()")
    end = js.index("function locateBrowser(", start)
    body = js[start:end]
    assert "if (edge.kind === 'igate' && !state.igateLinksEnabled) continue" in body
    assert "if (edge.kind !== 'igate') {" in body
    assert "state.mapVisibleCallsigns.has(sourceCall)" in body
    assert "dashArray: edge.kind === 'igate' ? '7 5' : null" in body
    assert "edge.kind === 'igate' ? 'Internet/APRS-IS'" in body


def test_v144_alert_settings_use_collection_selector():
    import re
    js = text("pt2vhf_aprs/static/js/v190.js")
    assert "$$('[data-v190-alert]',card).forEach" in js
    assert not re.search(r"(?<!\$)\$\([^\n;]+?\)\.(?:forEach|map|filter|find|some|every)\(", js)


def test_v144_map_has_15_and_30_minute_periods_end_to_end():
    html = text("pt2vhf_aprs/templates/index.html")
    js = text("pt2vhf_aprs/static/js/app.js")
    db_source = text("pt2vhf_aprs/database.py")
    web = text("pt2vhf_aprs/web.py")
    coverage = text("pt2vhf_aprs/v142_features.py")
    assert '<option value="0.25">15 min</option>' in html
    assert '<option value="0.5">30 min</option>' in html
    assert "[0, 0.25, 0.5, 1, 6, 12, 24, 168]" in js
    assert 'hours = float(request.args.get("hours", 0))' in web
    assert "hours = max(0.25, min(hours, 24 * 30))" in db_source
    assert 'hours = float(request.args.get("hours", 24))' in coverage


def test_v144_light_database_health_avoids_deep_scans_on_config_open():
    from pt2vhf_aprs.v111_features import db_health
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "health.db"
            db.init_db()
            light = db_health(deep=False)
            assert light["integrity"] == "operacional"
            assert light["tables"] == {}
            deep = db_health()
            assert deep["integrity"] == "ok"
            assert "packets" in deep["tables"]
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_v144_satellite_layout_switches_before_sidebar_becomes_illegible():
    css = text("pt2vhf_aprs/static/css/v141.css")
    js = text("pt2vhf_aprs/static/js/v112.js")
    assert "minmax(340px,.85fr)" in css
    assert "@media(max-width:1320px)" in css
    assert "overflow-wrap:anywhere" in css
    assert "white-space:normal!important" in css
    assert "ResizeObserver" in js
    assert "state.map?.invalidateSize({animate:false})" in js
