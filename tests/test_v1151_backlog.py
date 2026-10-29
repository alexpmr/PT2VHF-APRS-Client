"""v1.15.1: gateways de voz digital não são RF, abortar processamento, Configuração em sub-abas."""
import sqlite3
from pathlib import Path

import pytest

from pt2vhf_aprs import database as db, rf_coverage

ROOT = Path(__file__).resolve().parents[1]
DMR = "PT2XYZ-9>APBM1D,PT2XYZ,DMR*,qAR,PT2XYZ:=1549.00S/04753.00W["
DSTAR = "PU2ABC-7>API51,DSTAR*,qAR,PY2KJP-10:!1549.00S/04753.00W>"
YSF = "PY2XX-9>APY03D,WIRES*,qAR,PY2XX-1:=1549.00S/04753.00W>"
RF_DIGI = "PT2AB-9>APDR16,PT2DIG-1*,WIDE2-1,qAR,PT2IG-10:=1549.00S/04753.00W>"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


@pytest.mark.parametrize("raw,mode", [(DMR, "DMR"), (DSTAR, "D-STAR"), (YSF, "C4FM"),
                                      ("PU2Z-5>APDPRS,qAR,PY2Z-B:!x", "D-STAR"),
                                      ("PP5A-9>APDR16,NXDN*,qAR,PP5A:=x", "NXDN"),
                                      ("PP5A-9>APX200,qAS,BM_7240:=x", "DMR"),
                                      (RF_DIGI, ""), ("PT2AB-9>APDR16,TCPIP*,qAC,T2BRAZIL:=x", "")])
def test_digital_voice_origin(raw, mode):
    assert db.digital_voice_origin(raw) == mode


def test_digital_voice_never_creates_rf_edges():
    for raw in (DMR, DSTAR, YSF):
        _source, edges = db._observed_topology_edges(raw, "APRS-IS")
        assert all(kind != "rf" for _s, _t, kind, _i in edges), raw
    _source, edges = db._observed_topology_edges(RF_DIGI, "APRS-IS")
    assert [kind for _s, _t, kind, _i in edges] == ["rf", "rf"]
    # Recebido pelo nosso TNC continua sendo RF de fato.
    _source, edges = db._observed_topology_edges(YSF, "RF")
    assert edges and edges[0][2] == "rf"
    assert db._rf_igate_from_path('["PT2XYZ","DMR*","qAR","PT2XYZ"]') == ""


def test_station_metadata_reports_origin():
    assert db.aprs_map_device_metadata(DMR)["digital_origin"] == "DMR"
    assert db.aprs_map_device_metadata(RF_DIGI)["digital_origin"] == ""
    assert "s.digital_origin ?" in read("pt2vhf_aprs/static/js/app.js")


def test_purge_reclassifies_old_digital_voice_rf(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "dv.db")
    db.init_db()
    now = "2026-10-29T12:00:00+00:00"
    with db.connection() as conn:
        conn.execute("DELETE FROM schema_migrations_v112 WHERE migration_key=?", (rf_coverage.DIGITAL_VOICE_PURGE_KEY,))
        for raw, source, target in ((DMR, "PT2XYZ-9", "PT2XYZ"), (RF_DIGI, "PT2AB-9", "PT2DIG-1")):
            conn.execute("""INSERT INTO topology_events(timestamp,source,target,kind,medium,evidence_level,
                            source_lat,source_lon,target_lat,target_lon,raw)
                            VALUES(?,?,?,'rf','APRS-IS','inferred',-15.8,-47.9,-15.81,-47.91,?)""",
                         (now, source, target, raw))
            conn.execute("INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen) VALUES(?,?,'rf',1,?,?)",
                         (source, target, now, now))
            rf_coverage.record_event_conn(conn, now, source, target, (-15.8, -47.9), (-15.81, -47.91), direct=False)
        assert rf_coverage.purge_digital_voice_once(conn) == 1
        assert rf_coverage.purge_digital_voice_once(conn) == 0          # uma única vez
        kinds = dict(conn.execute("SELECT source,kind FROM topology_events").fetchall())
        assert kinds == {"PT2XYZ-9": "igate", "PT2AB-9": "rf"}
        edges = {(r[0], r[1]) for r in conn.execute("SELECT source,kind FROM topology_edges")}
        assert ("PT2XYZ-9", "rf") not in edges and ("PT2XYZ-9", "igate") in edges and ("PT2AB-9", "rf") in edges
        tx, rx = conn.execute("SELECT SUM(tx),SUM(rx) FROM rf_coverage_cells").fetchone()
        assert (tx, rx) == (1, 1)                                     # só o salto RF real ficou


def test_processing_can_be_cancelled_and_timeout_applies_with_signal():
    js = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    html = read("pt2vhf_aprs/templates/index.html")
    assert "cancelable: options?.cancelable !== false" in js
    assert "onCancel: typeof options?.onCancel === 'function'" in js
    assert "$('#globalProcessingCancel')?.addEventListener('click', () => cancelCurrentProcessing());" in js
    assert "{ blocking: false, onCancel: () => controller.abort() }" in js      # topologia RF
    # O limite de tempo vale também quando quem chama passa o próprio signal.
    api = js[js.index("async function api(url, options = {})"):js.index("async function refreshVersionStatus")]
    assert "if (!requestOptions.signal &&" not in api and "external.addEventListener('abort'" in api
    assert "reportClientEvent('processing_slow'" in js and 'id="globalProcessingElapsed"' in html
    assert ".global-processing-overlay.nonblocking .global-processing-cancel { pointer-events: auto;" in css


def test_config_subtabs_markup():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/config_tabs.js")
    for key in ("station", "aprsis", "map", "app", "database", "backup"):
        assert f'data-config-tab="{key}"' in html
    for key in ("station", "aprsis", "tnc", "map", "app", "integrations", "database", "backup"):
        assert f"['{key}'," in js
    assert "tncConfigBlock: 'tnc'" in js and "v110ExternalConfig: 'integrations'" in js
    assert "v111DbHealth: 'database'" in js and "v190ConfigCard: 'backup'" in js
    assert "addEventListener('invalid'" in js and "MutationObserver" in js
    assert html.index("js/config_tabs.js") > html.index("js/tnc.js")
    assert "window.pt2vhfConfigTabs?.show(section === 'aprs' ? 'station' : section)" in read("pt2vhf_aprs/static/js/app.js")
