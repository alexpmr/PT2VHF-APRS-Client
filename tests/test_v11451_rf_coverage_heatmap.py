"""v1.14.51: Cobertura RF em mapa de calor com todo ponto de TX/RX RF."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pt2vhf_aprs import database as db, topology_map

ROOT = Path(__file__).resolve().parents[1]


def _event(conn, minutes_ago, source, target, src, dst, kind="rf", medium="APRS-IS",
           evidence="inferred", raw=""):
    ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).replace(microsecond=0).isoformat()
    conn.execute(
        """INSERT INTO topology_events(timestamp,source,target,kind,medium,evidence_level,
               source_lat,source_lon,target_lat,target_lon,raw)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (ts, source, target, kind, medium, evidence, src[0], src[1], dst[0], dst[1], raw),
    )


def test_every_rf_transmit_and_receive_position_becomes_a_heat_point(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "cov.db")
    db.init_db()
    digi = (-15.75, -47.88)
    with db.connection() as conn:
        _event(conn, 30, "PT2CAR-9", "PT2DIG-1", (-15.803, -48.113), digi)
        _event(conn, 20, "PT2CAR-9", "PT2DIG-1", (-15.8032, -48.1134), digi)  # mesma célula
        _event(conn, 10, "PT2FIX", "PT2DIG-1", (-15.60, -47.70), digi, medium="RF", evidence="direct")
        # APRS-IS puro não é RF; coordenada APRS inválida (#121) é ignorada.
        _event(conn, 5, "PT2NET", "T2BRAZIL", (-16.0, -48.0), (-16.1, -48.1), kind="igate")
        _event(conn, 5, "PP5BLU-15", "PT2DIG-1", (-27.29, -49.0), digi,
               raw="PP5BLU-15>APBK20,WIDE1-1,qAR,PT2DIG-1:!2677.84S/04900.03W#bad")
    points = topology_map.list_rf_activity_points(24)
    by_pos = {(round(p["latitude"], 2), round(p["longitude"], 2)): p for p in points}
    assert set(by_pos) == {(-15.80, -48.11), (-15.60, -47.70), (-15.75, -47.88)}
    assert by_pos[(-15.80, -48.11)]["tx"] == 2 and by_pos[(-15.80, -48.11)]["rx"] == 0
    assert by_pos[(-15.75, -47.88)]["rx"] == 3
    assert by_pos[(-15.60, -47.70)]["evidence"] == "direct"
    assert all(0 < p["weight"] <= 1 for p in points)
    assert by_pos[(-15.75, -47.88)]["weight"] > by_pos[(-15.60, -47.70)]["weight"]


def test_map_uses_single_heatmap_coverage_option():
    app = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    v142 = (ROOT / "pt2vhf_aprs/static/js/v142.js").read_text(encoding="utf-8")
    web = (ROOT / "pt2vhf_aprs/web.py").read_text(encoding="utf-8")
    assert "rf_coverage.list_points(hours)" in web  # v1.14.53: tabela própria
    assert "Cobertura RF (mapa de calor)" in app
    assert "window.pt2vhfCreateHeatLayer?.()" in app
    assert "count: state.mapLayerCounts.coverage" in app
    # A opção duplicada do v142 não é mais instalada no menu Ver.
    boot = v142[v142.index("window.pt2vhfCreateHeatLayer"):]
    assert "installCoverage();" not in v142.split("function boot")[-1]
    assert "createHeatLayer()" in boot
