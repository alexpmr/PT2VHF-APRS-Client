"""v2.0.7: GPS (NMEA/gpsd) e SmartBeaconing."""
import socket
import threading
import time

import pytest

from pt2vhf_aprs import aprs_service, database as db, gps_service as gps


def _nmea(body: str) -> str:
    calc = 0
    for char in body:
        calc ^= ord(char)
    return f"${body}*{calc:02X}"


RMC = _nmea("GNRMC,123519,A,2330.000,S,04637.800,W,054.0,090.0,230394,003.1,W")
GGA = _nmea("GPGGA,123519,2330.000,S,04637.800,W,1,08,0.9,760.0,M,46.9,M,,")


def test_nmea_rmc_and_gga():
    fix = gps.GpsFix()
    assert gps.parse_nmea(RMC, fix, now=100.0)
    assert fix.latitude == pytest.approx(-23.5) and fix.longitude == pytest.approx(-46.63)
    assert fix.speed_kmh == pytest.approx(54 * 1.852) and fix.course == 90.0
    assert gps.parse_nmea(GGA, fix, now=101.0)
    assert fix.altitude_m == 760.0 and fix.satellites == 8
    assert fix.fresh(now=120.0) and not fix.fresh(now=200.0)


def test_nmea_rejects_bad_checksum_and_void_fix():
    fix = gps.GpsFix()
    assert not gps.parse_nmea(RMC[:-2] + "00", fix)
    void = _nmea("GPRMC,123519,V,,,,,,,230394,,")
    assert not gps.parse_nmea(void, fix) and not fix.valid


def test_gpsd_tpv():
    fix = gps.GpsFix()
    line = '{"class":"TPV","mode":3,"lat":-15.8,"lon":-47.9,"altMSL":1100.0,"speed":10.0,"track":270.5}'
    assert gps.parse_gpsd(line, fix, now=5.0)
    assert fix.speed_kmh == pytest.approx(36.0) and fix.course == 270.5 and fix.altitude_m == 1100.0
    assert not gps.parse_gpsd('{"class":"TPV","mode":1}', fix)


CFG = {"sb_fast_speed": 90, "sb_fast_rate": 60, "sb_slow_speed": 5, "sb_slow_rate": 1800,
       "sb_min_turn_angle": 28, "sb_turn_slope": 255, "sb_min_turn_time": 15}


def test_smartbeacon_rates_and_corner():
    fix = gps.GpsFix(latitude=1, longitude=1, valid=True, received_at=0, speed_kmh=0, course=0)
    assert gps.smartbeacon_due(CFG, fix, 0, None, now=10)[0]  # nunca transmitiu
    # Parado: só após 1800 s
    assert not gps.smartbeacon_due(CFG, fix, 1000, 0, now=2000)[0]
    assert gps.smartbeacon_due(CFG, fix, 1000, 0, now=2800)[0]
    # 120 km/h: a cada 60 s
    fix.speed_kmh = 120
    assert not gps.smartbeacon_due(CFG, fix, 1000, 0, now=1050)[0]
    assert gps.smartbeacon_due(CFG, fix, 1000, 0, now=1061) == (True, "interval")
    # 45 km/h: 60*90/45 = 120 s
    fix.speed_kmh = 45
    assert not gps.smartbeacon_due(CFG, fix, 1000, 0, now=1100)[0]
    assert gps.smartbeacon_due(CFG, fix, 1000, 0, now=1121)[0]
    # Curva de 90° a 45 km/h (28 mph): limite 28 + 255/28 ≈ 37°
    fix.course = 90
    assert gps.smartbeacon_due(CFG, fix, 1000, 0, now=1016) == (True, "corner")
    assert not gps.smartbeacon_due(CFG, fix, 1000, 0, now=1010)[0]  # antes do tempo mínimo
    assert gps.heading_change(350, 10) == 20


def test_beacon_packet_uses_gps_with_course_speed(monkeypatch):
    service = gps.GpsService()
    service.fix = gps.GpsFix(latitude=-23.5, longitude=-46.63, altitude_m=760, speed_kmh=100, course=0.4,
                             valid=True, received_at=time.monotonic())
    cfg = {"callsign": "PY2ABC", "ssid": 9, "latitude": -15.0, "longitude": -47.0, "symbol_table": "/",
           "symbol": ">", "comment": "Teste", "altitude": None, "gps_enabled": 1}
    merged = {**cfg, **service.beacon_overrides(cfg)}
    packet = aprs_service.build_beacon_packet(merged)
    assert ":=2330.00S/04637.80W>360/054Teste www.PT2VHF.com /A=002493" in packet
    assert service.beacon_overrides({**cfg, "gps_enabled": 0}) is None
    service.fix.received_at = time.monotonic() - 120
    assert service.beacon_overrides(cfg) is None


def test_gpsd_reader_end_to_end():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def serve():
        conn, _ = server.accept()
        conn.recv(100)
        conn.sendall(b'{"class":"VERSION"}\n{"class":"TPV","mode":3,"lat":-10.5,"lon":-50.25,"speed":0,"track":0}\n')
        time.sleep(1.5)
        conn.close()

    threading.Thread(target=serve, daemon=True).start()
    service = gps.GpsService()
    service.apply_config({"gps_enabled": 1, "gps_source": "gpsd", "gps_gpsd_host": "127.0.0.1", "gps_gpsd_port": port})
    try:
        for _ in range(40):
            if service.status()["state"] == "fix":
                break
            time.sleep(0.05)
        status = service.status()
        assert status["state"] == "fix" and status["fix"]["latitude"] == -10.5 and status["fix"]["fresh"]
    finally:
        service.stop()
        server.close()


def test_config_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "g.db")
    db.init_db()
    with pytest.raises(ValueError):
        db.save_config({"gps_enabled": True, "gps_source": "serial", "gps_serial_port": ""})
    with pytest.raises(ValueError):
        db.save_config({"sb_slow_speed": 100, "sb_fast_speed": 90})
    saved = db.save_config({"gps_enabled": True, "gps_source": "gpsd", "smartbeacon_enabled": False})
    assert saved["gps_enabled"] == 1 and saved["gps_source"] == "gpsd" and saved["smartbeacon_enabled"] == 0
