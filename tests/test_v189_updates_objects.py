from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v189_update_interval_default_and_bounds():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "v189.db"
            db.init_db()
            assert db.get_config()["update_check_minutes"] == 15
            assert db.save_config({"update_check_minutes": 1})["update_check_minutes"] == 5
            assert db.save_config({"update_check_minutes": 2000})["update_check_minutes"] == 1440
            assert db.save_config({"update_check_minutes": 15})["update_check_minutes"] == 15
    finally:
        db.DB_PATH = original


def test_v189_update_scheduler_is_dynamic_and_no_30_minute_literal():
    js = read("pt2vhf_aprs/static/js/app.js")
    html = read("pt2vhf_aprs/templates/index.html")
    assert "function updateCheckMinutes()" in js
    assert "function rescheduleUpdateChecks()" in js
    assert "updateCheckTimer" in js
    assert "updateCheckIntervalMs()" in js
    assert "30 * 60 * 1000" not in js
    assert 'name="update_check_minutes"' in html
    assert 'value="15"' in html
    assert 'min="5"' in html and 'max="1440"' in html


def test_v189_object_normalization_balloon_and_ais():
    balloon = db.aprs_object_friendly_details({
        "map_family_key": "balloon",
        "info": "Radiosonde FREQ 403.500 MHz VSPD -5.2 m/s TEMP -42.5 C HUM 18 PRESS 12.4",
        "raw": "PT2ABC>APRS,WIDE1-1,qAR,PT2IGT:;SONDE",
        "path": '["WIDE1-1","qAR","PT2IGT"]',
        "alive": 1,
    })
    assert balloon["frequency_mhz"] == 403.5
    assert balloon["vertical_speed_ms"] == -5.2
    assert balloon["flight_state"] == "descending"
    assert balloon["temperature_c"] == -42.5
    assert balloon["humidity_percent"] == 18
    assert balloon["pressure_hpa"] == 12.4
    assert balloon["path"] == ["WIDE1-1", "qAR", "PT2IGT"]

    ais = db.aprs_object_friendly_details({
        "map_family_key": "ais",
        "info": "AIS MMSI 710123456 SOG 22.5 COG 135 DEST=RIO DE JANEIRO",
        "raw": "",
        "alive": 1,
    })
    assert ais["mmsi"] == "710123456"
    assert ais["speed_kmh"] == 22.5
    assert ais["course_deg"] == 135
    assert ais["destination"] == "RIO DE JANEIRO"


def test_v189_object_storage_keeps_structured_fields_and_history():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "objects.db"
            db.init_db()
            packet = {
                "from": "PT2WX",
                "format": "object",
                "object_name": "SONDE-1",
                "latitude": -15.8,
                "longitude": -47.9,
                "altitude": 12000.0,
                "speed": 55.0,
                "course": 180.0,
                "symbol_table": "/",
                "symbol": "O",
                "comment": "Radiosonde FREQ 403.500 MHz VSPD 5.0 m/s",
                "path": ["WIDE1-1", "qAR", "PT2IGT"],
                "weather": {"temperature": -35.0, "humidity": 20, "pressure": 180.0},
                "raw": "PT2WX>APRS,WIDE1-1,qAR,PT2IGT:;SONDE-1",
            }
            db.upsert_station(packet)
            packet["altitude"] = 13000.0
            db.upsert_station(packet)
            obj = next(row for row in db.map_data(force=True)["objects"] if row["name"] == "SONDE-1")
            assert obj["speed"] == 55.0
            assert obj["course"] == 180.0
            assert obj["max_altitude"] == 13000.0
            assert obj["first_heard"]
            assert obj["friendly_details"]["temperature_c"] == -35.0
            assert obj["friendly_details"]["flight_state"] == "ascending"
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_v189_friendly_popup_replaces_legacy_object_popup():
    js = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "function friendlyObjectPopupHtml(object, objectSymbol)" in js
    assert "Estado do voo" in js
    assert "Altitude máxima observada" in js
    assert "Dados técnicos" in js
    assert "Pacote bruto" in js
    assert "AIS / Embarcação" in js
    assert "Estação meteorológica" in js
    assert "marker.bindPopup(friendlyObjectPopupHtml(object, objectSymbol)" in js
    assert "object-popup-technical" in css
    assert "object-popup-primary-value" in css


def test_v189_version():
    assert read("VERSION").strip() == "1.8.9"
    assert '__version__ = "1.8.9"' in read("pt2vhf_aprs/__init__.py")
