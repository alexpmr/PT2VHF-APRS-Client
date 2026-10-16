"""Maidenhead input regression: conversion, explicit apply and persistence."""
from pathlib import Path
import subprocess
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js unavailable")
def test_maidenhead_algorithm_and_boundary_handling():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    first = js.index("  const maidenheadLonSteps =")
    end = js.index("  function updateMaidenheadPreview()", first)
    source = js[first:end]
    script = source + r"""
const assert = require('assert');
assert.equal(maidenheadEncode(-15.8, -47.9, 6).length, 6);
for (const n of [4, 6, 8, 10]) {
  for (const p of [[-15.8,-47.9],[0,0],[51.5074,-0.1278],[-33.8688,151.2093],[90,180],[-90,-180]]) {
    const g = maidenheadEncode(p[0], p[1], n);
    assert.equal(g.length,n);
    const point = maidenheadDecode(g);
    assert(point);
    assert(Math.abs(p[0] - point.lat) <= point.latCell / 2 + 1e-6);
    assert(Math.abs(p[1] - point.lon) <= point.lonCell / 2 + 1e-6);
    assert.equal(maidenheadDecode(g.toLowerCase()).grid,g);
  }
}
for (const invalid of ['','AA','SS00','AB12YZ','XX00','AB1C','AB12ABQ','AB12AB12Z']) {
  assert.equal(maidenheadDecode(invalid), null, invalid);
}
console.log('Maidenhead conversions OK');
"""
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_grid_ui_requires_explicit_apply_and_does_not_change_decimals_on_toggle():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    for identifier in ("maidenheadInput","maidenheadStatus","maidenheadApply",
                       "maidenheadPrecision","coordinateGridFields"):
        assert 'id="' + identifier + '"' in html
    assert 'option value="grid"' in html
    mode = js[js.index("  function applyCoordinateMode("):js.index("  $('#coordinateInputMode')?.addEventListener",js.index("  function applyCoordinateMode("))]
    assert "syncMaidenheadFromDecimal()" in mode
    assert "maidenheadDecode(" not in mode
    apply_block = js[js.index("  $('#maidenheadApply')?.addEventListener"):js.index("  $('#maidenheadInput')?.addEventListener")]
    assert "$('#latitudeDecimal').value = cell.lat.toFixed(6)" in apply_block
    assert "syncDmsFromDecimal();" in apply_block
    assert "markConfigDirty();" in apply_block
