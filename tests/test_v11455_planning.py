"""v1.14.55: planejamento no mapa — enlace entre 2 pontos e melhor ponto (portado do PT2VHF Mesh Analyzer)."""
import math

import pytest
from flask import Flask

from pt2vhf_aprs import database as db, planning, planning_routes


def hills(points):
    out = []
    for la, lo in points:
        out.append(800 + 300 * math.exp(-((la + 15.80) ** 2 + (lo + 47.90) ** 2) / 0.01 ** 2)
                   + 150 * math.exp(-((la + 15.77) ** 2 + (lo + 47.87) ** 2) / 0.006 ** 2)
                   + 40 * math.exp(-((la + 15.83) ** 2 + (lo + 47.93) ** 2) / 0.004 ** 2))
    return out


SQUARE = [(-15.75, -47.95), (-15.75, -47.85), (-15.85, -47.85), (-15.85, -47.95)]


def flat(points):
    return [800.0] * len(points)


def test_vhf_defaults_and_budget():
    r = planning.link_analysis(planning.Elevations(flat), (-15.80, -48.00), (-15.80, -47.90), {"height_a": 20, "height_b": 20})
    p = r["params"]
    assert p["freq_mhz"] == planning.APRS_FREQ_MHZ == 145.570
    assert p["tx_power_w"] == 25 and p["tx_power_dbm"] == 44.0
    assert p["sensitivity_dbm"] == -113.0
    fspl = 20 * math.log10(r["distance_m"] / 1000) + 20 * math.log10(145.57) + 32.44
    assert r["budget"]["fspl_db"] == pytest.approx(fspl, abs=0.1)
    assert r["budget"]["rx_uv"] == pytest.approx(planning.microvolts(r["budget"]["rx_dbm"]), rel=0.02)
    assert r["verdict"] == "viable"


def test_s_meter_and_microvolts():
    assert planning.s_units(-93) == "S9"
    assert planning.s_units(-80) == "S9+13 dB"
    assert planning.s_units(-105) == "S7"
    assert planning.s_units(-150) == "S0"
    assert planning.microvolts(-113) == pytest.approx(0.5, abs=0.01)


def test_hill_blocks_the_path_and_is_located():
    r = planning.link_analysis(planning.Elevations(hills), (-15.80, -47.96), (-15.80, -47.84), {})
    assert r["verdict"] in ("marginal", "unviable")
    assert abs(r["worst"]["lon"] + 47.90) < 0.01
    assert r["budget"]["diffraction_db"] > 20


def test_parameter_limits():
    e = planning.Elevations(flat)
    with pytest.raises(ValueError):
        planning.link_analysis(e, (-15.8, -48), (-15.8, -47.9), {"tx_power_w": 0})
    with pytest.raises(ValueError):
        planning.link_analysis(e, (-15.8, -48), (-15.8, -47.9), {"sensitivity_dbm": -10})
    with pytest.raises(ValueError):
        planning.link_analysis(e, (-15.8, -48), (-10, -40), {})


def test_observed_rf_between_stations():
    o = planning.observed_link([{"callsign": "PY2X", "packets": 4, "last_seen": "2026-10-20T10:00"}], [], "pt2vhf", "py2x")
    assert o["a_heard_b"] == {"packets": 4, "last_seen": "2026-10-20T10:00"}
    assert o["b_heard_a"] is None
    assert planning.observed_link([], [], "", "PY2X") is None


def test_best_points_distinct_hills_highest_first():
    r = planning.best_points(planning.Elevations(hills), SQUARE, count=10)
    elev = [p["elevation_m"] for p in r["points"]]
    assert elev == sorted(elev, reverse=True)
    assert len(elev) == 3 and elev[0] > 1090
    assert [p["rank"] for p in r["points"]] == [1, 2, 3]


def test_saved_surveys_in_data_dir(tmp_path):
    planning.save_survey(tmp_path, {"name": "Serra", "polygon": SQUARE, "count": 5})
    planning.save_survey(tmp_path, {"name": "Serra", "polygon": SQUARE[:3], "count": 7})
    saved = planning.saved_surveys(tmp_path)
    assert len(saved) == 1 and saved[0]["count"] == 7
    planning.delete_survey(tmp_path, saved[0]["id"])
    assert planning.saved_surveys(tmp_path) == []
    with pytest.raises(LookupError):
        planning.delete_survey(tmp_path, 1)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "planning.db")
    db.init_db()
    monkeypatch.setattr(planning_routes, "_elevations", [planning.Elevations(hills)])
    app = Flask(__name__)
    planning_routes.register_planning_routes(app)
    return app.test_client()


def test_routes_link_best_save_and_pdf(client, tmp_path):
    d = client.get("/api/planning/defaults").get_json()
    assert d["freq_mhz"] == 145.57 and d["saved"] == []
    r = client.post("/api/planning/link", json={"a": [-15.80, -47.96], "b": [-15.80, -47.84], "params": {}}).get_json()
    assert r["ok"] and r["data"]["worst"]
    bad = client.post("/api/planning/link", json={"a": [95, 0], "b": [0, 0]})
    assert bad.status_code == 400
    best = client.post("/api/planning/best", json={"polygon": SQUARE, "count": 5}).get_json()
    assert best["ok"] and best["data"]["points"][0]["rank"] == 1
    saved = client.post("/api/planning/save", json={"name": "DF", "polygon": SQUARE}).get_json()
    assert saved["ok"] and (tmp_path / "planning_surveys.json").exists()
    pdf = client.post("/api/planning/pdf", json={"kind": "survey", "polygon": SQUARE, "count": 5,
                                                 "links": [{"rank": 1, "target": "ref", "a": [-15.80, -47.90], "b": [-15.77, -47.87]}]})
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF-")
    pdf = client.post("/api/planning/pdf", json={"kind": "link", "a": [-15.80, -47.96], "b": [-15.80, -47.84]})
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf"


def test_terrain_tiles_png_decoder_roundtrip():
    import struct
    import zlib
    size = 8
    raw = b"".join(b"\x00" + bytes(v for x in range(size) for v in divmod(1000 + x + y + 32768, 256) + (0,)) for y in range(size))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xffffffff)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    width, bpp, rows = planning._png_rgb(png)
    assert width == size and rows[3][0] * 256 + rows[3][1] - 32768 == 1003
