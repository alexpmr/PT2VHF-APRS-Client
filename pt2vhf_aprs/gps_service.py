"""GPS e SmartBeaconing (v2.0.7).

Lê a posição de um GPS em porta serial (sentenças NMEA RMC/GGA, padrão 4800 baud) ou do gpsd
(TCP 2947, JSON). Com GPS ativo e posição válida, o beacon sai com a posição, rumo, velocidade e
altitude do GPS. O SmartBeaconing (algoritmo do HamHUD, o mesmo dos trackers e do APRSdroid) decide
quando transmitir: intervalo curto em alta velocidade, longo parado, e beacon extra nas curvas.
"""
from __future__ import annotations

import json
import socket
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable

from . import diagnostics as diag

FIX_MAX_AGE_SECONDS = 30.0
KNOTS_TO_KMH = 1.852


@dataclass
class GpsFix:
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    speed_kmh: float | None = None
    course: float | None = None
    satellites: int | None = None
    valid: bool = False
    received_at: float = 0.0  # time.monotonic()
    source: str = ""

    def fresh(self, now: float | None = None, max_age: float = FIX_MAX_AGE_SECONDS) -> bool:
        if not self.valid or self.latitude is None or self.longitude is None:
            return False
        return ((now if now is not None else time.monotonic()) - self.received_at) <= max_age

    def public(self) -> dict[str, Any]:
        data = asdict(self)
        data["age_seconds"] = round(time.monotonic() - self.received_at, 1) if self.received_at else None
        data["fresh"] = self.fresh()
        data.pop("received_at", None)
        return data


# ----------------------------------------------------------------------------- NMEA

def nmea_checksum_ok(sentence: str) -> bool:
    line = sentence.strip()
    if not line.startswith("$") or "*" not in line:
        return False
    body, _, given = line[1:].partition("*")
    calc = 0
    for char in body:
        calc ^= ord(char)
    try:
        return calc == int(given[:2], 16)
    except ValueError:
        return False


def _nmea_coord(value: str, hemisphere: str, degree_digits: int) -> float | None:
    if not value or not hemisphere:
        return None
    try:
        degrees = int(value[:degree_digits])
        minutes = float(value[degree_digits:])
    except ValueError:
        return None
    coord = degrees + minutes / 60.0
    return -coord if hemisphere.upper() in {"S", "W"} else coord


def parse_nmea(sentence: str, fix: GpsFix, now: float | None = None) -> bool:
    """Atualiza ``fix`` com uma sentença RMC ou GGA (qualquer talker: GP, GN, GL, GA, BD).
    Devolve True quando a sentença trouxe posição válida."""
    if not nmea_checksum_ok(sentence):
        return False
    fields = sentence.strip()[1:].split("*", 1)[0].split(",")
    kind = fields[0][2:] if len(fields[0]) >= 5 else ""
    stamp = now if now is not None else time.monotonic()
    if kind == "RMC" and len(fields) >= 9:
        if fields[2] != "A":
            fix.valid = False
            return False
        lat = _nmea_coord(fields[3], fields[4], 2)
        lon = _nmea_coord(fields[5], fields[6], 3)
        if lat is None or lon is None:
            return False
        fix.latitude, fix.longitude = lat, lon
        fix.speed_kmh = float(fields[7]) * KNOTS_TO_KMH if fields[7] else 0.0
        fix.course = float(fields[8]) % 360 if fields[8] else None
        fix.valid = True
        fix.received_at = stamp
        return True
    if kind == "GGA" and len(fields) >= 10:
        quality = int(fields[6] or 0) if fields[6].isdigit() else 0
        if quality <= 0:
            fix.valid = False
            return False
        lat = _nmea_coord(fields[2], fields[3], 2)
        lon = _nmea_coord(fields[4], fields[5], 3)
        if lat is None or lon is None:
            return False
        fix.latitude, fix.longitude = lat, lon
        fix.satellites = int(fields[7]) if fields[7].isdigit() else fix.satellites
        try:
            fix.altitude_m = float(fields[9]) if fields[9] else fix.altitude_m
        except ValueError:
            pass
        fix.valid = True
        fix.received_at = stamp
        return True
    return False


def parse_gpsd(line: str, fix: GpsFix, now: float | None = None) -> bool:
    """Atualiza ``fix`` com um objeto TPV do gpsd (modo 2 = 2D, 3 = 3D)."""
    try:
        data = json.loads(line)
    except ValueError:
        return False
    if not isinstance(data, dict) or data.get("class") != "TPV":
        return False
    if int(data.get("mode") or 0) < 2 or data.get("lat") is None or data.get("lon") is None:
        fix.valid = False
        return False
    fix.latitude = float(data["lat"])
    fix.longitude = float(data["lon"])
    if data.get("speed") is not None:
        fix.speed_kmh = float(data["speed"]) * 3.6  # m/s
    if data.get("track") is not None:
        fix.course = float(data["track"]) % 360
    alt = data.get("altMSL", data.get("alt"))
    if alt is not None:
        fix.altitude_m = float(alt)
    fix.valid = True
    fix.received_at = now if now is not None else time.monotonic()
    return True


# ----------------------------------------------------------------------------- SmartBeaconing

def heading_change(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 0.0
    diff = abs(a - b) % 360
    return 360 - diff if diff > 180 else diff


def smartbeacon_due(cfg: dict[str, Any], fix: GpsFix, last_beacon_at: float, last_course: float | None,
                    now: float | None = None) -> tuple[bool, str]:
    """(transmitir agora?, motivo). Velocidades em km/h, tempos em segundos.

    Abaixo da velocidade baixa: intervalo lento. Acima da alta: intervalo rápido. Entre as duas:
    intervalo = rápido × velocidade alta / velocidade. Curva: se o rumo mudou mais que
    ângulo mínimo + inclinação / velocidade (mph) e já passou o tempo mínimo de curva.
    """
    now = now if now is not None else time.monotonic()
    elapsed = now - last_beacon_at if last_beacon_at else float("inf")
    speed = max(0.0, float(fix.speed_kmh or 0.0))
    fast_speed = float(cfg.get("sb_fast_speed") or 90)
    slow_speed = float(cfg.get("sb_slow_speed") or 5)
    fast_rate = float(cfg.get("sb_fast_rate") or 60)
    slow_rate = float(cfg.get("sb_slow_rate") or 1800)
    if speed < slow_speed:
        rate = slow_rate
    elif speed >= fast_speed:
        rate = fast_rate
    else:
        rate = min(slow_rate, fast_rate * fast_speed / speed)
    if elapsed >= rate:
        return True, "interval"
    if speed >= slow_speed and last_course is not None and fix.course is not None:
        mph = speed / 1.609344
        threshold = float(cfg.get("sb_min_turn_angle") or 28) + float(cfg.get("sb_turn_slope") or 255) / max(mph, 1.0)
        if heading_change(fix.course, last_course) > threshold and elapsed >= float(cfg.get("sb_min_turn_time") or 15):
            return True, "corner"
    return False, ""


# ----------------------------------------------------------------------------- serviço

class GpsService:
    def __init__(self) -> None:
        self.fix = GpsFix()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._cfg_key: tuple | None = None
        self.state = "off"
        self.last_error = ""
        self.sentences = 0
        self.last_beacon_at = 0.0
        self.last_beacon_course: float | None = None

    # Chamado a cada configuração salva e na abertura.
    def apply_config(self, cfg: dict[str, Any]) -> None:
        key = (int(cfg.get("gps_enabled") or 0), cfg.get("gps_source"), cfg.get("gps_serial_port"),
               cfg.get("gps_serial_baud"), cfg.get("gps_gpsd_host"), cfg.get("gps_gpsd_port"))
        if key == self._cfg_key and (not key[0] or (self._thread and self._thread.is_alive())):
            return
        self.stop()
        self._cfg_key = key
        if not key[0]:
            self.state = "off"
            return
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(dict(cfg), self._stop), name="gps-reader", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=3)
        self._thread = None
        with self._lock:
            self.fix = GpsFix()
        self.state = "off"

    def current_fix(self) -> GpsFix:
        with self._lock:
            return GpsFix(**asdict(self.fix))

    def status(self) -> dict[str, Any]:
        with self._lock:
            fix = self.fix.public()
        return {"state": self.state, "error": self.last_error, "sentences": self.sentences, "fix": fix}

    def _feed(self, parser: Callable[[str, GpsFix], bool], line: str) -> None:
        with self._lock:
            if parser(line, self.fix):
                self.sentences += 1
                self.state = "fix"
            elif self.state == "fix" and not self.fix.fresh():
                self.state = "no_fix"

    def _run(self, cfg: dict[str, Any], stop: threading.Event) -> None:
        backoff = 2.0
        while not stop.is_set():
            try:
                if cfg.get("gps_source") == "gpsd":
                    self._run_gpsd(cfg, stop)
                else:
                    self._run_serial(cfg, stop)
                backoff = 2.0
            except Exception as exc:
                self.state = "error"
                self.last_error = str(exc)
                diag.log_event("gps_error", error=str(exc), source=cfg.get("gps_source"))
            stop.wait(backoff)
            backoff = min(30.0, backoff * 2)

    def _run_serial(self, cfg: dict[str, Any], stop: threading.Event) -> None:
        import serial  # pyserial, já usado pelo TNC

        port = str(cfg.get("gps_serial_port") or "")
        if not port:
            raise ValueError("Informe a porta serial do GPS.")
        self.state = "connecting"
        with serial.Serial(port, int(cfg.get("gps_serial_baud") or 4800), timeout=1.0) as handle:
            self.state = "no_fix"
            self.last_error = ""
            buffer = b""
            while not stop.is_set():
                chunk = handle.read(512)
                if not chunk:
                    if self.state == "fix" and not self.fix.fresh():
                        self.state = "no_fix"
                    continue
                buffer += chunk
                while b"\n" in buffer:
                    raw, buffer = buffer.split(b"\n", 1)
                    self._feed(parse_nmea, raw.decode("ascii", "ignore"))
                buffer = buffer[-1024:]

    def _run_gpsd(self, cfg: dict[str, Any], stop: threading.Event) -> None:
        host = str(cfg.get("gps_gpsd_host") or "127.0.0.1")
        port = int(cfg.get("gps_gpsd_port") or 2947)
        self.state = "connecting"
        with socket.create_connection((host, port), timeout=10) as sock:
            sock.settimeout(2.0)
            sock.sendall(b'?WATCH={"enable":true,"json":true};\n')
            self.state = "no_fix"
            self.last_error = ""
            buffer = b""
            while not stop.is_set():
                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    raise ConnectionError("gpsd encerrou a conexão.")
                buffer += chunk
                while b"\n" in buffer:
                    raw, buffer = buffer.split(b"\n", 1)
                    self._feed(parse_gpsd, raw.decode("utf-8", "ignore"))
                buffer = buffer[-65536:]

    # ------------------------------------------------------------------ beacon

    def beacon_overrides(self, cfg: dict[str, Any]) -> dict[str, Any] | None:
        """Campos que substituem a posição fixa no beacon, ou None sem GPS/posição válida."""
        if not int(cfg.get("gps_enabled") or 0):
            return None
        fix = self.current_fix()
        if not fix.fresh():
            return None
        out: dict[str, Any] = {"latitude": fix.latitude, "longitude": fix.longitude}
        if fix.altitude_m is not None:
            out["altitude"] = fix.altitude_m
        if fix.speed_kmh is not None and fix.course is not None:
            out["_course"] = int(round(fix.course)) % 360 or 360
            out["_speed_knots"] = max(0, min(999, int(round(fix.speed_kmh / KNOTS_TO_KMH))))
        return out

    def smartbeacon_due(self, cfg: dict[str, Any], now: float | None = None) -> tuple[bool, str]:
        fix = self.current_fix()
        if not fix.fresh(now):
            return False, ""
        return smartbeacon_due(cfg, fix, self.last_beacon_at, self.last_beacon_course, now)

    def note_beacon_sent(self, now: float | None = None) -> None:
        fix = self.current_fix()
        self.last_beacon_at = now if now is not None else time.monotonic()
        self.last_beacon_course = fix.course


service = GpsService()

