"""Maidenhead coordinate input tests: bounds, precision, confirmation, no silent overwrite."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "pt2vhf_aprs/static/js/maidenhead.js"


def _node(script):
    if not shutil.which("node"):
        pytest.skip("Node.js is not installed in this runner")
    output = subprocess.run(["node", "-e", script], cwd=ROOT,
                            capture_output=True, text=True, check=True, timeout=12)
    return json.loads(output.stdout.strip())


def test_grid_four_character_known_centers_and_bounds():
    result = _node(
        "const m=require(" + json.dumps(str(MODULE)) + ");"
        "console.log(JSON.stringify([m.decode('AA00'),m.decode('rr99')]))"
    )
    assert result[0]["latitude"] == -89.5
    assert result[0]["longitude"] == -179
    assert result[1]["latitude"] == 89.5
    assert result[1]["longitude"] == 179
    assert result[0]["latitudeSpan"] == 1
    assert result[0]["longitudeSpan"] == 2


def test_grid_precision_and_hemispheres_round_trip():
    test_code = """
const m=require(REQUIRED);
const samples=[[0,0],[-15.8,-47.9],[-33.8688,151.2093],[51.5,-0.12],
               [35.65,139.69],[-89.9999,-179.9999],[89.9999,179.9999]];
const output=[];
for (const precision of [4,6,8,10]) {
  for(const [lat,lon] of samples) {
    const grid=m.encode(lat,lon,precision);
    const result=m.decode(grid.toLowerCase());
    const centerGrid=m.encode(result.latitude,result.longitude,precision);
    output.push({grid,result,centerGrid,precision,lat,lon});
  }
}
console.log(JSON.stringify(output));
""".replace("REQUIRED", json.dumps(str(MODULE)))
    result = _node(test_code)
    assert len(result) == 28
    for entry in result:
        loc = entry["result"]
        assert entry["grid"] == loc["locator"] == entry["centerGrid"]
        assert len(entry["grid"]) == entry["precision"]
        assert abs(entry["lat"] - loc["latitude"]) <= loc["latitudeSpan"] / 2 + 1e-7
        assert abs(entry["lon"] - loc["longitude"]) <= loc["longitudeSpan"] / 2 + 1e-7


def test_grid_rejects_invalid_inputs():
    code = """
const m=require(REQUIRED);
const rejected = ['','GH','A00A','SZ00','GH6','GH64a','GH64YZ',
                  'GH64aa1','GH64aa12x','GH64aa12yy12','GH64!@',
                  'GH64ab1a','GH64ab1a23'];
const failures = rejected.map(x=>{try{m.decode(x);return false}catch(e){return true}});
const coordinates = [[91,0],[-91,0],[0,181],[0,-181],[null,0]];
const coordinateRejected=coordinates.map(x=>{try{m.encode(x[0],x[1]);return false}catch(e){return true}});
console.log(JSON.stringify({failures,coordinateRejected}));
""".replace("REQUIRED", json.dumps(str(MODULE)))
    result = _node(code)
    assert all(result["failures"])
    # Null converts to zero in Number(null); the UI handles empty text separately.
    assert result["coordinateRejected"][:4] == [True] * 4


def test_station_grid_mode_and_explicit_apply_are_wired():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    for marker in ('value="grid"', 'id="gridLocatorInput"',
                   'id="gridLocatorApply"', 'id="gridLocatorPrecision"',
                   'id="gridLocatorStatus"', 'js/maidenhead.js'):
        assert marker in html
    assert "['decimal', 'dms', 'grid'].includes(mode)" in js
    assert "$('#gridLocatorInput').dataset.pending = 'false'" in js
    assert "grid-not-applied" in js
    assert "grid.latitude.toFixed(6)" in js
    assert "grid.longitude.toFixed(6)" in js
    assert "syncDmsFromDecimal();" in js
