"""v1.15.0: menu Ferramentas, análise de cobertura (como no PT2VHF Mesh Analyzer) e TNC / RF em Configuração."""
import io
import sqlite3
from pathlib import Path

import pytest
from flask import Flask
from PIL import Image

from pt2vhf_aprs import coverage, database as db, pdf_map, planning, planning_routes, rf_coverage

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def flat_tile(elevation=1000.0):
    v = int(round((elevation + 32768) * 256))
    color = (v >> 16, (v >> 8) & 255, v & 255)
    out = io.BytesIO()
    Image.new("RGB", (256, 256), color).save(out, format="PNG")
    return out.getvalue()


FLAT = flat_tile()


@pytest.fixture()
def tiles():
    return planning.TerrainTiles(None, getter=lambda url: FLAT)


def test_coverage_defaults_for_aprs(tiles):
    r = coverage.coverage(tiles, [-15.79, -47.88], {"max_km": 10})
    p = r["params"]
    assert p["tx_power_w"] == 50 and p["tx_power_dbm"] == 47.0
    assert p["freq_mhz"] == planning.APRS_FREQ_MHZ == 145.570
    assert p["rx_sensitivity_dbm"] == -113
    assert r["sensitivity_uv"] == pytest.approx(0.5, abs=0.01) and r["sensitivity_s"].startswith("S")
    assert r["center"]["ground_m"] == pytest.approx(1000, abs=1)
    assert r["covered_km2"] > 0 and r["farthest_km"] <= 10
    assert coverage.coverage_params({})["max_km"] == 50
    with pytest.raises(ValueError):
        coverage.coverage_params({"max_km": 101})
    with pytest.raises(ValueError):
        coverage.coverage_params({"tx_power_w": 0})
    with pytest.raises(ValueError):
        coverage.coverage_params({"hires": True, "max_km": 60})


def test_coverage_classifies_stations(tiles):
    r = coverage.coverage(tiles, [-15.79, -47.88], {"max_km": 10, "tx_power_w": 50})
    near = {"node_num": "PT2NEAR", "name": "PT2NEAR", "lat": -15.76, "lon": -47.86}
    far = {"node_num": "PT2FAR", "name": "PT2FAR", "lat": -16.5, "lon": -48.6}
    covered, uncovered, outside = coverage.classify_nodes(r, [near, far])
    assert [x["name"] for x in covered] == ["PT2NEAR"]
    assert [x["name"] for x in outside] == ["PT2FAR"] and not uncovered
    assert coverage.value_at(r, -15.76, -47.86) >= -113


@pytest.fixture()
def client(tmp_path, monkeypatch, tiles):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "tools.db")
    db.init_db()
    monkeypatch.setattr(planning_routes, "_tiles_cache", [tiles])
    monkeypatch.setattr(planning_routes, "_coverage_cache", {})
    monkeypatch.setattr(pdf_map, "_http_tile", lambda url, timeout=8: (_ for _ in ()).throw(OSError("offline")))
    now = "2026-10-29T12:00:00+00:00"
    with sqlite3.connect(db.DB_PATH) as conn:
        for call, lat, lon in [("PT2TX", -15.79, -47.88), ("PT2ABC", -15.76, -47.86), ("PT2FAR", -16.6, -48.7)]:
            conn.execute("INSERT OR REPLACE INTO stations(callsign,last_heard,latitude,longitude) VALUES(?,?,?,?)",
                         (call, now, lat, lon))
        for target in ("PT2ABC", "PT2FAR"):
            conn.execute("INSERT OR REPLACE INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen)"
                         " VALUES(?,?,?,?,?,?)", ("PT2TX", target, "rf", 7, now, now))
        rf_coverage.ensure_schema(conn)
        for i, (lat, lon, direct) in enumerate([(-15.77, -47.87, 1), (-16.9, -49.0, 1), (-15.80, -47.89, 0)]):
            conn.execute("INSERT INTO rf_coverage_cells(day,cell_lat,cell_lon,lat_sum,lon_sum,tx,rx,direct,first_seen,last_seen)"
                         " VALUES(?,?,?,?,?,?,?,?,?,?)", ("2026-10-29", i, i, lat * 3, lon * 3, 1, 2, direct, now, now))
    app = Flask(__name__)
    planning_routes.register_planning_routes(app)
    return app.test_client()


def test_coverage_route_observed_and_pdf_reuses_cache(client, monkeypatch):
    body = {"center": [-15.79, -47.88], "params": {"max_km": 10, "station": "PT2TX"}}
    r = client.post("/api/planning/coverage", json=body).get_json()
    assert r["ok"] and r["data"]["grid"] and "_bytes" not in r["data"]
    obs = r["data"]["observed"]
    assert obs["station"] == "PT2TX" and obs["total"] == 2 and obs["agree"] == 1 and obs["accuracy_pct"] == 50
    cells = r["data"]["observed_cells"]        # só recepção direta e dentro do raio
    assert cells["total"] == 1 and cells["agree"] == 1 and cells["accuracy_pct"] == 100
    calls = []
    monkeypatch.setattr(coverage, "coverage", lambda *a, **k: calls.append(1))
    pdf = client.post("/api/planning/pdf", json={"kind": "coverage", **body, "display": {"style": "contours"}})
    assert pdf.status_code == 200 and pdf.data[:4] == b"%PDF" and not calls


def test_highest_and_best_coverage_routes(client):
    h = client.post("/api/planning/highest", json={"center": [-15.79, -47.88], "radius_km": 2}).get_json()
    assert h["ok"] and h["data"]["ground_m"] == pytest.approx(1000, abs=1)
    assert client.post("/api/planning/highest", json={"center": [-15.79, -47.88], "radius_km": 80}).status_code == 400
    best = client.post("/api/planning/best-coverage", json={"radius_km": 5, "points": [
        {"rank": 1, "lat": -15.79, "lon": -47.88}, {"rank": 2, "lat": -16.0, "lon": -48.2}]}).get_json()
    assert best["ok"] and best["data"]["best"] == 1
    assert best["data"]["items"][0]["stations"] >= 1
    assert client.post("/api/planning/best-coverage", json={"points": []}).status_code == 400


def test_pdf_base_map_and_offline_fallback(tmp_path):
    tile = io.BytesIO()
    Image.new("RGB", (256, 256), (200, 220, 200)).save(tile, format="PNG")
    base = pdf_map.render((-15.9, -48.0, -15.7, -47.8), 600, tmp_path, fetch=lambda url: tile.getvalue())
    assert base is not None and base.image.size[0] == 600
    x, y = base.project(-15.8, -47.9)
    assert 0 < x < 600 and 0 < y < base.image.size[1]
    assert any((tmp_path).rglob("*.png"))                  # tiles guardados no computador
    assert pdf_map.render((-15.9, -48.0, -15.7, -47.8), 600, None, fetch=lambda url: 1 / 0) is None


def test_despike_removes_isolated_terrain_spike():
    grid = [1000.0] * (16 * 16)
    grid[8 * 16 + 8] = 3418.0
    planning.despike(grid, 16)
    assert grid[8 * 16 + 8] == pytest.approx(1000, abs=1)


def test_tools_menu_and_tnc_block_markup():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/planning.js")
    tnc = read("pt2vhf_aprs/static/js/tnc.js")
    nav = html[html.index('<nav class="tabs"'):html.index("</nav>")]
    assert nav.index('data-tab="automations"') < nav.index('id="toolsMenuButton"') < nav.index('data-tab="config"')
    assert 'data-tab="tnc"' not in html
    menu = html[html.index('<div id="toolsMenu"'):html.index('<div id="mapContextBar"')]
    for needle in ("Planejamento de RF", "Análise de cobertura", "Analisar enlace entre 2 pontos",
                   "Melhor ponto para instalar estação", "Relevo com corte", 'id="elevationToggle"',
                   "Relatório (PDF)", "Diagnóstico para suporte"):
        assert needle in menu
    assert html.count('id="elevationToggle"') == 1
    config = html[html.index('<section id="tab-config"'):html.index('<section id="tab-about"')]
    assert '<details id="tncConfigBlock"' in config and '<details id="tncConfigBlock" class="config-card tnc-config-block" open' not in config
    assert 'id="tab-tnc"' in config and 'id="tncSave"' in config and '<details id="tncMonitorsBlock"' in config
    assert config.index('</form>') < config.index('id="tncConfigBlock"')    # sem formulário dentro de formulário
    assert "function openCoverage(" in js and "tx_power_w: 50" in js and "max_km: 50" in js
    assert "/api/planning/best-coverage" in js and "/api/diagnostics/log" in js and "Voltar à cobertura" in js
    assert "planningSection" not in js
    assert "function tncVisible()" in tnc and "$('#tncHeaderStatus')" in tnc and "openTncBlock" in tnc
    assert '.tab.active[data-tab="tnc"]' not in tnc
