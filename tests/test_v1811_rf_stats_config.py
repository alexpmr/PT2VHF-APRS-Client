from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db
from pt2vhf_aprs import tnc_service as tnc

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def use_temp_db():
    td = tempfile.TemporaryDirectory()
    original = db.DB_PATH
    db.DB_PATH = Path(td.name) / "v1811.db"
    db.init_db()
    tnc._ensure_schema()
    return td, original


def restore_db(td, original):
    db.DB_PATH = original
    db.invalidate_map_data_cache(drop_payload=True)
    td.cleanup()


def test_v1811_packets_persist_reception_medium_and_fingerprint():
    td, original = use_temp_db()
    try:
        rf_raw = "PT2AAA>APRS,WIDE1-1:>teste"
        is_raw = "PT2AAA>APRS,WIDE1-1,qAR,PT2IGT:>teste"
        db.record_packet(rf_raw, "PT2AAA", "status", medium="RF")
        db.record_packet(is_raw, "PT2AAA", "status", medium="APRS-IS")
        with db.connection() as conn:
            rows = conn.execute(
                "SELECT medium,rx_fingerprint FROM packets ORDER BY id"
            ).fetchall()
        assert [row["medium"] for row in rows] == ["RF", "APRS-IS"]
        assert rows[0]["rx_fingerprint"]
        assert rows[0]["rx_fingerprint"] == rows[1]["rx_fingerprint"]
    finally:
        restore_db(td, original)


def test_v1811_rf_heard_falls_back_to_persistent_packet_evidence():
    td, original = use_temp_db()
    try:
        db.record_packet("PT2RF1>APRS:>RF only", "PT2RF1", "status", medium="RF")
        rows = tnc.heard_stations()
        row = next(item for item in rows if item["callsign"] == "PT2RF1")
        assert row["rf_packet_count"] == 1
        assert row["rf_evidence"] == "packets"
        assert row["direct_known"] is False
    finally:
        restore_db(td, original)


def test_v1811_reception_stats_preserve_both_media_and_deduplicate_logical_packet():
    td, original = use_temp_db()
    try:
        db.record_packet("PT2AAA>APRS,WIDE1-1:>same", "PT2AAA", "status", medium="RF")
        db.record_packet("PT2AAA>APRS,WIDE1-1,qAR,PT2IGT:>same", "PT2AAA", "status", medium="APRS-IS")
        db.record_packet("PT2BBB>APRS:>rf-only", "PT2BBB", "status", medium="RF")
        stats = tnc.tnc_reception_stats(24)
        assert stats["rf_packets"] == 2
        assert stats["aprsis_packets"] == 1
        assert stats["rf_unique_stations"] >= 2
        assert stats["both_media_stations"] == 1
        assert stats["logical_packets_deduplicated"] == 2
    finally:
        restore_db(td, original)


def test_v1811_aprs_service_tags_rf_ingress_explicitly():
    source = read("pt2vhf_aprs/aprs_service.py")
    assert 'medium="APRS-IS"' in source
    assert 'medium="RF"' in source


def test_v1811_statistics_expose_rf_and_aprsis_columns_and_summary():
    db_source = read("pt2vhf_aprs/database.py")
    js = read("pt2vhf_aprs/static/js/app.js")
    web = read("pt2vhf_aprs/web.py")
    assert "AS rf_packets" in db_source
    assert "AS aprsis_packets" in db_source
    assert '"rf_packets": rf_packets' in db_source
    assert '"aprsis_packets": aprsis_packets' in db_source
    assert 'payload["reception_media"] = tnc_reception_stats(hours)' in web
    assert "Recepção RF × APRS-IS" in js
    assert "rf_unique_stations" in js
    assert "logical_packets_deduplicated" in js
    assert "data.reception_media?.logical_packets_deduplicated" in js


def test_v1811_tnc_rf_table_shows_persistent_counts_and_distance():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/tnc.js")
    assert "<th>Pacotes RF</th>" in html
    assert "<th>Distância</th>" in html
    assert 'colspan="8"' in html
    assert "row.rf_packet_count" in js
    assert "row.distance_km" in js
    assert "row.direct_known" in js


def test_v1811_settings_section_titles_are_larger_and_orange():
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "#tab-config .config-card > h3" in css
    assert "color: #ff8a3d;" in css
    assert "font-size: 18px;" in css
    assert "html[data-theme=\"light\"] #tab-config .config-card > h3" in css
    assert "color: #c85f00;" in css


def test_v1811_diagnostics_include_rf_station_and_summary_events():
    source = read("pt2vhf_aprs/tnc_service.py")
    assert '"tnc_rf_station_heard"' in source
    assert '"tnc_rf_rx_summary"' in source


def test_v1811_version():
    version = read("VERSION").strip()
    parts = tuple(int(item) for item in version.split("."))
    assert parts >= (1, 8, 11)
    assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")
