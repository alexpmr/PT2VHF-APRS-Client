from __future__ import annotations

from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v143_version_metadata():
    assert read("VERSION").strip() == "1.14.3"
    assert '__version__ = "1.14.3"' in read("pt2vhf_aprs/__init__.py")
    win = read("windows/version_info.txt")
    assert "filevers=(1, 14, 3, 0)" in win
    assert "prodvers=(1, 14, 3, 0)" in win
    assert "FileVersion', '1.14.3'" in win
    assert "ProductVersion', '1.14.3'" in win


def test_v143_header_manual_beacon_uses_existing_pipeline():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    assert 'id="headerSendBeaconButton"' in html
    assert ">Enviar Beacon</button>" in html
    assert "async function sendManualBeacon()" in js
    assert "await api('/api/beacon', { method:'POST' });" in js
    assert "$('#sendBeaconButton')?.addEventListener('click', () => { void sendManualBeacon(); });" in js
    assert "$('#headerSendBeaconButton')?.addEventListener('click', () => { void sendManualBeacon(); });" in js
    assert "buttons.some(button => button.disabled)" in js


def test_v143_interaction_classifier_does_not_use_raw_path_as_role_evidence():
    js = read("pt2vhf_aprs/static/js/app.js")
    start = js.index("function stationInteractionProfile(s)")
    end = js.index("function stationInteractionDisabledAttrs", start)
    profile = js[start:end]
    assert "infrastructure_evidence" in profile
    assert "s?.raw" not in profile
    assert "WIDE[1-7]" not in profile
    assert "const digiSymbol = String(s?.symbol || '') === '#';" in profile
    assert "DIGI(?:PEATER)?" in profile


def test_v143_wide_path_source_is_not_infrastructure_but_real_hop_is():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "v143.db"
            db.init_db()
            now = db.utc_now_iso()
            with db.connection() as conn:
                conn.execute(
                    """INSERT INTO stations(
                           callsign,name,last_heard,latitude,longitude,info,
                           symbol_table,symbol,path,packet_format,raw
                       ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "PU2AKM-9", "PU2AKM-9", now, -15.8, -47.9,
                        "TYT APRS TEST", "/", "n",
                        '["WIDE1-1","WIDE2-1"]', "position",
                        "PU2AKM-9>APRS,WIDE1-1,WIDE2-1:!1548.00S/04754.00W>TYT APRS TEST",
                    ),
                )
                conn.execute(
                    """INSERT INTO stations(
                           callsign,name,last_heard,latitude,longitude,info,
                           symbol_table,symbol,path,packet_format,raw
                       ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "PT2DGI", "PT2DGI", now, -15.7, -47.8,
                        "DIGI", "/", "#", "[]", "status",
                        "PT2DGI>APRS:>DIGI",
                    ),
                )
            db.record_topology_from_raw(
                "PU2SRC>APRS,PT2DGI*,WIDE2-1,qAR,PT2IGT:>teste"
            )
            rows = {row["callsign"]: row for row in db.list_stations()}
            assert rows["PU2AKM-9"]["infrastructure_evidence"] == 0
            assert rows["PT2DGI"]["infrastructure_evidence"] == 1
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)
