from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile

from pt2vhf_aprs import database as db
from pt2vhf_aprs.v142_features import rf_coverage_points

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v142_version_metadata():
    version = read("VERSION").strip()
    parts = tuple(int(part) for part in version.split("."))
    assert parts >= (1, 14, 2)
    assert f'__version__ = "{version}"' in read("pt2vhf_aprs/__init__.py")


def test_v142_template_loads_incremental_assets_and_backend_route():
    html = read("pt2vhf_aprs/templates/index.html")
    web = read("pt2vhf_aprs/web.py")
    assert "css/v142.css" in html
    assert "js/v142.js" in html
    assert "register_v142_routes" in web
    assert "/api/v142/rf-coverage" in read("pt2vhf_aprs/v142_features.py")


def test_v142_rf_heatmap_uses_zoom_period_and_shared_view_controls():
    js = read("pt2vhf_aprs/static/js/v142.js")
    assert "v142-rf-heatmap-canvas" in js
    assert "createRadialGradient" in js
    assert "const radius =" in js
    assert "this._map.getZoom()" in js
    assert "mapPeriodHours" in js
    assert "pt2vhf_rf_coverage_enabled" in js
    assert "mapViewSelectAllButton" in js
    assert "mapViewClearAllButton" in js
    assert "/api/v142/rf-coverage" in js


def test_v142_rf_coverage_uses_confirmed_rf_and_quality_then_density_fallback():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "v142.db"
            db.init_db()
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            with db.connection() as conn:
                conn.execute(
                    """INSERT INTO stations(callsign,name,last_heard,latitude,longitude,info,symbol_table,symbol,raw)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    ("PY2RF1", "", now, -23.5, -47.5, "", "/", ">", "PY2RF1>APRS:>RF"),
                )
                conn.execute(
                    """INSERT INTO stations(callsign,name,last_heard,latitude,longitude,info,symbol_table,symbol,raw)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    ("PY2RF2", "", now, -23.6, -47.6, "", "/", ">", "PY2RF2>APRS:>RF"),
                )
                conn.execute(
                    "INSERT INTO packets(timestamp,from_call,packet_format,raw,medium) VALUES(?,?,?,?,?)",
                    (now, "PY2RF1", "position", "PY2RF1>APRS:!2350.00S/04750.00W", "RF"),
                )
                conn.execute(
                    "INSERT INTO packets(timestamp,from_call,packet_format,raw,medium) VALUES(?,?,?,?,?)",
                    (now, "PY2RF2", "position", "PY2RF2>APRS:!2360.00S/04760.00W", "RF"),
                )
                conn.execute(
                    """INSERT INTO tracks(callsign,timestamp,latitude,longitude,rssi,snr)
                       VALUES(?,?,?,?,?,?)""",
                    ("PY2RF1", now, -23.5, -47.5, -89.0, 7.0),
                )
            result = rf_coverage_points(hours=24, limit=500)
            assert result["rf_stations"] == 2
            assert result["quality_points"] >= 1
            assert result["density_points"] >= 1
            by_call = {item["callsign"]: item for item in result["points"]}
            assert by_call["PY2RF1"]["source"] == "rf_quality"
            assert by_call["PY2RF1"]["rssi"] == -89.0
            assert by_call["PY2RF2"]["source"] == "rf_density"
            assert 0.0 < float(by_call["PY2RF1"]["weight"]) <= 1.0
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)


def test_v142_ais_parser_extracts_extended_fields():
    item = {
        "map_family_key": "ais",
        "info": "MMSI:123456789 | IMO:7654321 | VESSEL NAME:SEA TEST | CALLSIGN:PY2SEA | SHIP TYPE:70 | NAV STATUS:5 | DEST:RIO | ETA:10/07 12:00 | DRAUGHT:4.2 M | HEADING:123 | LENGTH:80 M | WIDTH:14 M | SOG:12.5 KTS",
        "comment": "",
        "status": "",
        "raw": "",
        "weather_json": "{}",
        "speed": None,
        "course": 121,
        "alive": 1,
    }
    details = db.aprs_object_friendly_details(item)
    assert details["mmsi"] == "123456789"
    assert details["imo"] == "7654321"
    assert details["vessel_name"] == "SEA TEST"
    assert details["vessel_callsign"] == "PY2SEA"
    assert details["vessel_type"] == "70"
    assert details["nav_status"] == "5"
    assert details["destination"] == "RIO"
    assert details["draught_m"] == 4.2
    assert details["heading_deg"] == 123.0
    assert details["length_m"] == 80.0
    assert details["width_m"] == 14.0
    assert details["speed_knots"] == 12.5


def test_v142_ais_popup_and_async_enrichment_are_explicitly_labeled():
    app = read("pt2vhf_aprs/static/js/app.js")
    js = read("pt2vhf_aprs/static/js/v142.js")
    assert "function aisShipTypeLabel(value)" in app
    assert "function aisNavigationStatusLabel(value)" in app
    for label in (
        "Nome da embarcação", "Tipo de embarcação", "Status de navegação",
        "Velocidade sobre o fundo", "Rumo sobre o fundo", "Calado", "Dimensões",
    ):
        assert label in app
    assert "/api/v110/ais-profile/" in js
    assert "Imagem ilustrativa do tipo" in js
    assert "Fonte externa" in js
    assert "profile?.image_url" in js
