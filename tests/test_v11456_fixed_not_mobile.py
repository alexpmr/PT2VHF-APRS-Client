"""v1.14.56: estações fixas (meteorológicas, GPS parado) não viram "móveis".

Relato: na v1.14.55 o mapa recebia só 5 enlaces RF fixos com 158 digis e
290 iGates. O aprslib entrega o vento "DDD/SSS" como course/speed e a regra
de velocidade da v1.14.50 tratava a estação como móvel, sumindo os enlaces.
"""
import tempfile
from datetime import datetime, timedelta, timezone

import aprslib

from pt2vhf_aprs import database as db, topology_map


def ingest(raw):
    p = aprslib.parse(raw)
    db.process_received_packet(raw, p, p.get("from"), p.get("format"), medium="APRS-IS")


def test_weather_wind_is_not_stored_as_speed(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "wx.db")
    db.init_db()
    ingest("PY2WX>APRS,TCPIP*,qAC,T2BRAZIL:@241200z2330.00S/04630.00W_090/012g020t077r000p000P000h50b10132")
    with db.connection() as conn:
        assert conn.execute("SELECT speed,course FROM stations WHERE callsign='PY2WX'").fetchone()[:] == (None, None)
        assert conn.execute("SELECT speed FROM tracks WHERE callsign='PY2WX'").fetchone()[0] is None


def test_speed_without_displacement_is_not_mobile():
    tracks = [  # iGate meteorológico antigo/GPS parado: velocidade alta, mesmo lugar (±20 m)
        {"callsign": "PY2IGT-10", "latitude": -23.5000, "longitude": -46.6000, "speed": 22.2},
        {"callsign": "PY2IGT-10", "latitude": -23.5001, "longitude": -46.6002, "speed": 14.8},
        {"callsign": "PY2IGT-10", "latitude": -23.5002, "longitude": -46.6001, "speed": 18.5},
        # Tracker de verdade circulando pela cidade.
        {"callsign": "PY2CAR-9", "latitude": -23.50, "longitude": -46.60, "speed": 40},
        {"callsign": "PY2CAR-9", "latitude": -23.52, "longitude": -46.63, "speed": 45},
    ]
    mobile = topology_map.moving_rf_repeaters([], tracks)
    assert "PY2IGT-10" not in mobile
    assert "PY2CAR-9" in mobile


def test_fixed_weather_igate_keeps_its_links_on_the_map(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "map.db")
    db.init_db()
    ingest("PY2DIG-1>APRS,TCPIP*,qAC,T2BRAZIL:!2332.00S/04632.00W#PHG5360/digi")
    ingest("PY2FIX>APRS,PY2DIG-1*,WIDE2-1,qAR,PY2DIG-1:!2335.00S/04635.00W-casa")
    # Banco antigo: tracklog da estação com "velocidade" vinda do vento, sem sair do lugar.
    now = datetime.now(timezone.utc)
    with db.connection() as conn:
        for i, speed in enumerate((22.2, 14.8, 18.5)):
            conn.execute("INSERT INTO tracks(callsign,timestamp,latitude,longitude,speed) VALUES(?,?,?,?,?)",
                         ("PY2DIG-1", (now - timedelta(minutes=10 * (i + 1))).isoformat(timespec="seconds"),
                          -23.5333 + i * 0.0001, -46.5333, speed))
    edges = topology_map.list_map_edges(0)
    kinds = {(e["source"], e["target"]): e["kind"] for e in edges}
    assert kinds.get(("PY2FIX", "PY2DIG-1")) == "rf"
