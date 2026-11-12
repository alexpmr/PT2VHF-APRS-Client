"""v1.15.8: mapa de calor sem descartar áreas pouco densas; aviso de boas-vindas como no Sat Tool."""
import json
import math
from pathlib import Path

from pt2vhf_aprs import database as db, rf_coverage

ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-11-06T12:00:00+00:00"


def seed(cells):
    with db.connection() as conn:
        for (cl, cn), count in cells.items():
            lat, lon = (cl + .5) * rf_coverage.CELL_DEGREES, (cn + .5) * rf_coverage.CELL_DEGREES
            conn.execute(
                "INSERT INTO rf_coverage_cells(day,cell_lat,cell_lon,lat_sum,lon_sum,tx,rx,direct,callsigns,first_seen,last_seen)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                ("2026-11-06", cl, cn, lat * count, lon * count, count, 0, 1, json.dumps(["PY2ABC"]), NOW, NOW))


def test_sparse_cells_are_merged_not_dropped_when_over_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "heat.db")
    db.init_db()
    dense = {(-1500 + i, -4700): 500 for i in range(20)}                       # poucas áreas muito densas
    sparse = {(-1600 - i // 60 * 3, -4800 - i % 60 * 3): 1 for i in range(3000)}  # muitas bordas com 1 recepção
    seed({**dense, **sparse})
    points = rf_coverage.list_points(0, limit=1000)
    assert len(points) <= 1000
    assert sum(p["count"] for p in points) == sum(dense.values()) + sum(sparse.values())  # nada descartado
    # A borda mais distante continua representada perto de onde foi observada.
    far = ((-1600 - 49 * 3 + .5) * .01, (-4800 - 59 * 3 + .5) * .01)
    assert min(math.dist(far, (p["latitude"], p["longitude"])) for p in points) < .1
    # Sem estourar o limite, nada muda.
    assert len(rf_coverage.list_points(0)) == len(dense) + len(sparse)


def test_single_observation_weight_has_visible_floor():
    assert rf_coverage._weight(1) >= .55 and rf_coverage._weight(10_000) == 1.0


def test_welcome_notice_matches_sat_tool():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    notice = html[html.index('id="officialSiteNotice"'):html.index('id="whatsNewModal"')]
    assert "Feito por radioamadores, para radioamadores" in notice
    assert "Sat Tool, Prop Tool, Mesh Analyzer, Prog Tool, QSL Manager" in notice
    assert ">Fechar</button>" in notice and 'href="https://www.pt2vhf.com"' in notice  # texto: reserva do splash
    table = js[js.index("const OFFICIAL_SITE_NOTICE"):js.index("let officialSiteNoticeShown")]
    for lang in ("pt", "en", "es", "fr", "de", "it", "ja", "pl", "nl", "zh"):
        assert f"    {lang}: [" in table
