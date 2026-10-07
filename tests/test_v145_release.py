from __future__ import annotations

from pathlib import Path
import re
import tempfile

import pytest

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v145_version_metadata():
    assert text("VERSION").strip() == "1.14.5"
    assert '__version__ = "1.14.5"' in text("pt2vhf_aprs/__init__.py")
    win = text("windows/version_info.txt")
    for marker in (
        "filevers=(1, 14, 5, 0)", "prodvers=(1, 14, 5, 0)",
        "FileVersion', '1.14.5'", "ProductVersion', '1.14.5'",
    ):
        assert marker in win


def test_v145_config_dirty_state_is_recomputed_and_slow_load_preserves_edits():
    js = text("pt2vhf_aprs/static/js/app.js")
    assert "configEditGeneration: 0" in js
    assert "configTouchedFields: new Set()" in js
    assert "const editedDuringLoad = state.configEditGeneration !== editGenerationAtStart" in js
    assert "applyConfigToForm(cfg, { preserveTouched: !force && editedDuringLoad })" in js
    assert "state.configDirty = configFormSnapshot() !== state.configBaseline" in js
    assert "if (state.activeTab === 'config' && tab !== 'config') markConfigDirty();" in js
    assert "Uma resposta GET lenta nunca pode apagar/rebaselinar uma edição local." in js


def test_v145_footer_saves_only_real_changes_without_reload_race():
    js = text("pt2vhf_aprs/static/js/app.js")
    start = js.index("async function saveConfigForm()")
    end = js.index("$('#configForm').addEventListener('submit'", start)
    body = js[start:end]
    assert "const payload = configChangedPayload();" in body
    assert "JSON.stringify(payload)" in body
    assert "state.configBaseline = configSnapshotFromConfig(savedConfig)" in body
    assert "loadConfig()" not in body
    assert "return { ok: true, unchanged: true }" in body
    assert "return { ok: false, error: message }" in body


def test_v145_discard_is_local_and_continue_is_network_free():
    js = text("pt2vhf_aprs/static/js/app.js")
    start = js.index("async function resolveUnsavedConfig(mode)")
    end = js.index("async function sendManualBeacon()", start)
    body = js[start:end]
    discard_start = body.index("} else if (mode === 'discard')")
    cancel_start = body.index("} else {", discard_start)
    discard_body = body[discard_start:cancel_start]
    assert "restoreConfigBaselineLocally()" in discard_body
    assert "loadConfig(" not in discard_body
    assert "api(" not in discard_body
    assert "pendingConfigFeedback();" in body
    assert "activateTab(target)" in body


def test_v145_modal_surfaces_real_backend_error():
    js = text("pt2vhf_aprs/static/js/app.js")
    assert "result?.error || ui('Não foi possível salvar.'" in js
    assert "const message = String(err?.message || err" in js
    assert "setConfigDirtyStatus(message, true)" in js
    assert "pendingConfigFeedback(" in js


def test_v145_partial_config_save_tolerates_legacy_unrelated_value():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "legacy.db"
            db.init_db()
            db.save_config({"callsign": "PT2VHF", "comment": "antes", "map_zoom_step": 0.25})
            with db.connection() as conn:
                conn.execute("UPDATE config SET map_zoom_step=0.33 WHERE id=1")

            saved = db.save_config({"comment": "depois"})
            assert saved["comment"] == "depois"
            assert float(saved["map_zoom_step"]) == pytest.approx(0.33)

            with pytest.raises(ValueError):
                db.save_config({"map_zoom_step": 0.33})
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_v145_satellite_service_controls_use_collection_and_do_not_masquerade_as_orbit_error():
    js = text("pt2vhf_aprs/static/js/v112.js")
    assert "host.querySelectorAll('[data-satellite-service]').forEach" in js
    assert "$('[data-satellite-service]',host).forEach" not in js
    assert "function safeRenderDetail(norad)" in js
    assert "Satellite detail rendering error" in js
    assert "if(id===state.activeNorad){safeRenderDetail(id);renderLiveStrip(id);}" in js
    assert not re.search(r"(?<!\$)\$\([^\n;]+?\)\.(?:forEach|map|filter|find|some|every)\(", js)


def test_v145_import_and_reset_force_clean_reload():
    js = text("pt2vhf_aprs/static/js/app.js")
    assert js.count("loadConfig({ force:true })") >= 2
