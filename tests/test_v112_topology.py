from __future__ import annotations

from pathlib import Path

from pt2vhf_aprs import database as db


def read(rel: str) -> str:
    return (Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")


def test_v112_rf_transport_forces_last_hop_to_igate_to_remain_rf():
    source, edges = db._observed_topology_edges(
        "PU2AKM-7>APRS,PT2DGI*,WIDE2-1,qAr,PT2PAG-15:>received by local TNC",
        "RF",
    )
    assert source == "PU2AKM-7"
    assert ("PU2AKM-7", "PT2DGI", "rf", None) in edges
    assert ("PT2DGI", "PT2PAG-15", "rf", "PT2PAG-15") in edges
    assert not any(kind == "igate" for _a, _b, kind, _igate in edges)

    _source, internet_edges = db._observed_topology_edges(
        "PU2AKM-7>APRS,PT2DGI*,WIDE2-1,qAr,PT2PAG-15:>from aprs-is",
        "APRS-IS",
    )
    assert ("PT2DGI", "PT2PAG-15", "igate", "PT2PAG-15") in internet_edges


def test_v112_topology_pipeline_persists_transport_evidence(tmp_path):
    original = db.DB_PATH
    try:
        db.DB_PATH = tmp_path / "v112.db"
        db.init_db()
        parsed = {"from": "PU2AKM-7", "format": "status", "path": ["PT2DGI*", "qAr", "PT2PAG-15"]}
        raw = "PU2AKM-7>APRS,PT2DGI*,qAr,PT2PAG-15:>rf"
        db.process_received_packet(raw, parsed, "PU2AKM-7", "status", medium="RF")

        with db.connection() as conn:
            row = conn.execute(
                """SELECT kind,rf_transport_count,rf_path_count,internet_confirmed_count
                   FROM topology_edges
                   WHERE source='PT2DGI' AND target='PT2PAG-15'"""
            ).fetchone()
        assert row is not None
        assert row["kind"] == "rf"
        assert row["rf_transport_count"] >= 1
        assert row["internet_confirmed_count"] == 0
    finally:
        db.DB_PATH = original


def test_v112_old_destructive_igate_migration_is_gone():
    source = read("pt2vhf_aprs/database.py")
    assert "DELETE FROM topology_edges WHERE kind='rf' AND igate IS NOT NULL" not in source
    assert "_repair_topology_rf_evidence_v112" in source
    assert '_record_topology_from_raw_conn(conn, raw, medium)' in source
    assert '"RF direto do transporte"' in source
    assert '"APRS-IS confirmado"' in source


def test_v112_windows_style_floating_panels_include_logs_and_restore():
    js = read("pt2vhf_aprs/static/js/v190.js")
    css = read("pt2vhf_aprs/static/css/v190.css")
    assert "floatPanel('tab-messages','Mensagens')" in js
    assert "floatPanel('tab-stations','Estações')" in js
    assert "floatPanel('tab-log','Logs')" in js
    assert "v190-window-button v190-minimize" in js
    assert "v190-window-button v190-maximize" in js
    assert "v190-window-button v190-close" in js
    assert "restoreRect" in js
    assert "_pt2vhfResetFloatGeometry" in js
    assert ".v190-floating.v190-minimized" in css
    assert ".v190-floating.v190-maximized" in css
    assert ".v190-window-button.v190-close:hover" in css


def test_v112_top_left_search_field_is_not_installed():
    js = read("pt2vhf_aprs/static/js/v190.js")
    boot = js[js.rfind("function boot()"):]
    assert "installGlobalSearch();" not in boot
    assert "document.querySelector('.v1818-search')?.remove();" in boot
