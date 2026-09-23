from __future__ import annotations

import json
import math
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

def _default_data_dir() -> Path:
    override = os.getenv("PT2VHF_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA")
        if base:
            return Path(base) / "PT2VHF APRS Client" / "data"
        return Path.home() / "AppData" / "Local" / "PT2VHF APRS Client" / "data"
    return Path(__file__).resolve().parent.parent / "data"


DB_PATH = _default_data_dir() / "pt2vhf_aprs.db"

DEFAULT_CONFIG = {
    "callsign": "PT2VHF",
    "ssid": 0,
    "comment": "PT2VHF APRS Client",
    "latitude": None,
    "longitude": None,
    "altitude": None,
    "symbol_table": "/",
    "symbol": ">",
    "beacon_minutes": 10,
    "email": "",
    "server": "brazil.aprs2.net",
    "port": 14580,
    "passcode": "",
    "aprs_filter": "",
    "connect_on_start": 0,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                callsign TEXT NOT NULL,
                ssid INTEGER NOT NULL DEFAULT 0,
                comment TEXT NOT NULL DEFAULT '',
                latitude REAL,
                longitude REAL,
                altitude REAL,
                symbol_table TEXT NOT NULL DEFAULT '/',
                symbol TEXT NOT NULL DEFAULT '>',
                beacon_minutes INTEGER NOT NULL DEFAULT 10,
                email TEXT NOT NULL DEFAULT '',
                server TEXT NOT NULL DEFAULT 'brazil.aprs2.net',
                port INTEGER NOT NULL DEFAULT 14580,
                passcode TEXT NOT NULL DEFAULT '',
                aprs_filter TEXT NOT NULL DEFAULT '',
                connect_on_start INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS map_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                latitude REAL NOT NULL DEFAULT -14.2350,
                longitude REAL NOT NULL DEFAULT -51.9253,
                zoom INTEGER NOT NULL DEFAULT 4,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stations (
                callsign TEXT PRIMARY KEY,
                name TEXT,
                last_heard TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                speed REAL,
                course REAL,
                altitude REAL,
                info TEXT,
                symbol_table TEXT,
                symbol TEXT,
                message_capable INTEGER NOT NULL DEFAULT 0,
                path TEXT,
                packet_format TEXT,
                raw TEXT
            );

            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                callsign TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                speed REAL,
                course REAL,
                altitude REAL
            );
            CREATE INDEX IF NOT EXISTS idx_tracks_callsign_time ON tracks(callsign, timestamp);
            CREATE INDEX IF NOT EXISTS idx_tracks_time ON tracks(timestamp);

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                direction TEXT NOT NULL,
                from_call TEXT NOT NULL,
                to_call TEXT NOT NULL,
                message TEXT NOT NULL,
                message_type TEXT NOT NULL DEFAULT 'message',
                msg_id TEXT,
                status TEXT NOT NULL DEFAULT '',
                timestamp TEXT NOT NULL,
                raw TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_call);

            CREATE TABLE IF NOT EXISTS packets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                from_call TEXT,
                packet_format TEXT,
                raw TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_packets_time ON packets(timestamp DESC);

            CREATE TABLE IF NOT EXISTS aprs_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('RX','TX')),
                raw TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_aprs_log_time ON aprs_log(id DESC);
            CREATE INDEX IF NOT EXISTS idx_aprs_log_direction ON aprs_log(direction, id DESC);
            """
        )
        message_columns = {row["name"] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
        if "message_type" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN message_type TEXT NOT NULL DEFAULT 'message'")

        row = conn.execute("SELECT id FROM config WHERE id=1").fetchone()
        if not row:
            now = utc_now_iso()
            cols = ", ".join(DEFAULT_CONFIG.keys())
            placeholders = ", ".join("?" for _ in DEFAULT_CONFIG)
            conn.execute(
                f"INSERT INTO config (id, {cols}, updated_at) VALUES (1, {placeholders}, ?)",
                [*DEFAULT_CONFIG.values(), now],
            )
        row = conn.execute("SELECT id FROM map_state WHERE id=1").fetchone()
        if not row:
            conn.execute(
                "INSERT INTO map_state (id, latitude, longitude, zoom, updated_at) VALUES (1, -14.2350, -51.9253, 4, ?)",
                (utc_now_iso(),),
            )


def get_config() -> dict[str, Any]:
    with connection() as conn:
        row = conn.execute("SELECT * FROM config WHERE id=1").fetchone()
        return dict(row) if row else dict(DEFAULT_CONFIG)


def save_config(data: dict[str, Any]) -> dict[str, Any]:
    current = get_config()
    allowed = set(DEFAULT_CONFIG)
    merged = {key: data.get(key, current.get(key, DEFAULT_CONFIG[key])) for key in allowed}

    merged["callsign"] = str(merged["callsign"] or "").upper().strip()
    merged["ssid"] = int(merged["ssid"] or 0)
    merged["port"] = int(merged["port"] or 14580)
    merged["beacon_minutes"] = max(1, int(merged["beacon_minutes"] or 10))
    merged["connect_on_start"] = 1 if bool(merged["connect_on_start"]) else 0
    merged["symbol_table"] = (str(merged["symbol_table"] or "/")[:1])
    merged["symbol"] = (str(merged["symbol"] or ">")[:1])
    for field in ("latitude", "longitude", "altitude"):
        if merged[field] in ("", None):
            merged[field] = None
        else:
            merged[field] = float(merged[field])

    if not merged["callsign"]:
        raise ValueError("Indicativo é obrigatório.")
    if not (0 <= merged["ssid"] <= 15):
        raise ValueError("SSID deve estar entre 0 e 15.")
    if merged["latitude"] is not None and not (-90 <= merged["latitude"] <= 90):
        raise ValueError("Latitude inválida.")
    if merged["longitude"] is not None and not (-180 <= merged["longitude"] <= 180):
        raise ValueError("Longitude inválida.")
    if not (1 <= merged["port"] <= 65535):
        raise ValueError("Porta inválida.")

    sets = ", ".join(f"{key}=?" for key in sorted(allowed))
    values = [merged[key] for key in sorted(allowed)]
    with connection() as conn:
        conn.execute(f"UPDATE config SET {sets}, updated_at=? WHERE id=1", [*values, utc_now_iso()])
    return get_config()


def export_config() -> dict[str, Any]:
    cfg = get_config()
    cfg.pop("id", None)
    cfg.pop("updated_at", None)
    return cfg


def import_config(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Arquivo de configuração inválido.")
    return save_config(data)


def get_map_state() -> dict[str, Any]:
    with connection() as conn:
        row = conn.execute("SELECT latitude, longitude, zoom FROM map_state WHERE id=1").fetchone()
        return dict(row)


def save_map_state(latitude: float, longitude: float, zoom: int) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE map_state SET latitude=?, longitude=?, zoom=?, updated_at=? WHERE id=1",
            (float(latitude), float(longitude), int(zoom), utc_now_iso()),
        )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def record_packet(raw: str, from_call: str | None = None, packet_format: str | None = None) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO packets(timestamp, from_call, packet_format, raw) VALUES (?, ?, ?, ?)",
            (utc_now_iso(), from_call, packet_format, raw),
        )
        # Retém os últimos 100 mil pacotes para evitar crescimento sem limite.
        conn.execute(
            "DELETE FROM packets WHERE id NOT IN (SELECT id FROM packets ORDER BY id DESC LIMIT 100000)"
        )


def upsert_station(packet: dict[str, Any]) -> None:
    callsign = str(packet.get("from") or "").upper().strip()
    if not callsign:
        return
    now = utc_now_iso()
    fmt = str(packet.get("format") or "")
    name = callsign
    info = _extract_info(packet)
    is_object = fmt in {"object", "item"}
    path = json.dumps(packet.get("path") or [], ensure_ascii=False)

    with connection() as conn:
        previous = conn.execute(
            "SELECT latitude, longitude FROM stations WHERE callsign=?", (callsign,)
        ).fetchone()
        current = conn.execute("SELECT * FROM stations WHERE callsign=?", (callsign,)).fetchone()

        def choose(key: str, fallback=None):
            value = None if is_object and key in {"latitude", "longitude", "speed", "course", "altitude", "symbol_table", "symbol"} else packet.get(key, None)
            if value is None and current is not None:
                return current[key]
            return fallback if value is None else value

        values = {
            "name": name or callsign,
            "last_heard": now,
            "latitude": choose("latitude"),
            "longitude": choose("longitude"),
            "speed": choose("speed"),
            "course": choose("course"),
            "altitude": choose("altitude"),
            "info": info if info else (current["info"] if current else ""),
            "symbol_table": choose("symbol_table"),
            "symbol": choose("symbol"),
            "message_capable": 1 if packet.get("messagecapable") else (current["message_capable"] if current else 0),
            "path": path,
            "packet_format": fmt,
            "raw": str(packet.get("raw") or ""),
        }

        conn.execute(
            """
            INSERT INTO stations(callsign,name,last_heard,latitude,longitude,speed,course,altitude,info,
                                 symbol_table,symbol,message_capable,path,packet_format,raw)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(callsign) DO UPDATE SET
                name=excluded.name,last_heard=excluded.last_heard,latitude=excluded.latitude,
                longitude=excluded.longitude,speed=excluded.speed,course=excluded.course,
                altitude=excluded.altitude,info=excluded.info,symbol_table=excluded.symbol_table,
                symbol=excluded.symbol,message_capable=excluded.message_capable,path=excluded.path,
                packet_format=excluded.packet_format,raw=excluded.raw
            """,
            (
                callsign, values["name"], values["last_heard"], values["latitude"], values["longitude"],
                values["speed"], values["course"], values["altitude"], values["info"],
                values["symbol_table"], values["symbol"], values["message_capable"], values["path"],
                values["packet_format"], values["raw"],
            ),
        )

        lat, lon = packet.get("latitude"), packet.get("longitude")
        if not is_object and lat is not None and lon is not None:
            should_add = True
            if previous and previous["latitude"] is not None and previous["longitude"] is not None:
                should_add = haversine_km(previous["latitude"], previous["longitude"], float(lat), float(lon)) >= 0.01
            if should_add or previous is None:
                conn.execute(
                    "INSERT INTO tracks(callsign,timestamp,latitude,longitude,speed,course,altitude) VALUES(?,?,?,?,?,?,?)",
                    (callsign, now, float(lat), float(lon), packet.get("speed"), packet.get("course"), packet.get("altitude")),
                )


def _extract_info(packet: dict[str, Any]) -> str:
    for key in ("comment", "status"):
        if packet.get(key):
            return str(packet[key]).strip()
    if packet.get("weather"):
        wx = packet["weather"]
        parts = []
        labels = {
            "temperature": "Temp",
            "humidity": "UR",
            "pressure": "Pressão",
            "wind_speed": "Vento",
            "wind_gust": "Rajada",
        }
        for key, label in labels.items():
            if key in wx and wx[key] is not None:
                parts.append(f"{label}: {wx[key]}")
        return " | ".join(parts)
    return ""


def list_stations(filter_text: str = "") -> list[dict[str, Any]]:
    cfg = get_config()
    own_lat = cfg.get("latitude")
    own_lon = cfg.get("longitude")
    q = "%" + filter_text.upper().strip() + "%"
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM stations
            WHERE UPPER(callsign) LIKE ? OR UPPER(COALESCE(name,'')) LIKE ? OR UPPER(COALESCE(info,'')) LIKE ?
            ORDER BY last_heard DESC
            """,
            (q, q, q),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        if own_lat is not None and own_lon is not None and item["latitude"] is not None and item["longitude"] is not None:
            item["distance_km"] = round(haversine_km(float(own_lat), float(own_lon), item["latitude"], item["longitude"]), 2)
        else:
            item["distance_km"] = None
        result.append(item)
    return result


def map_data() -> dict[str, Any]:
    with connection() as conn:
        stations = [dict(r) for r in conn.execute(
            "SELECT * FROM stations WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY last_heard DESC"
        ).fetchall()]
        # Últimos 10 mil pontos; o frontend agrupa por estação. Evita travar após meses de operação.
        tracks = [dict(r) for r in conn.execute(
            "SELECT callsign,timestamp,latitude,longitude,speed,course,altitude FROM tracks ORDER BY id DESC LIMIT 10000"
        ).fetchall()]
    tracks.reverse()
    return {"stations": stations, "tracks": tracks}


def add_message(direction: str, from_call: str, to_call: str, message: str, msg_id: str | None = None,
                status: str = "", raw: str | None = None, message_type: str = "message") -> int:
    message_type = str(message_type or "message").strip().lower()
    if message_type not in {"message", "bulletin", "group_bulletin"}:
        message_type = "message"
    with connection() as conn:
        cur = conn.execute(
            """INSERT INTO messages(direction,from_call,to_call,message,message_type,msg_id,status,timestamp,raw)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (direction, from_call.upper(), to_call.upper(), message, message_type, msg_id, status, utc_now_iso(), raw),
        )
        return int(cur.lastrowid)


def mark_message_status(msg_id: str, status: str, peer: str | None = None) -> None:
    with connection() as conn:
        if peer:
            conn.execute(
                "UPDATE messages SET status=? WHERE direction='out' AND msg_id=? AND UPPER(to_call)=UPPER(?)",
                (status, msg_id, peer),
            )
        else:
            conn.execute(
                "UPDATE messages SET status=? WHERE direction='out' AND msg_id=?",
                (status, msg_id),
            )


def list_messages(from_filter: str = "", limit: int = 5000) -> list[dict[str, Any]]:
    q = "%" + from_filter.upper().strip() + "%"
    with connection() as conn:
        rows = conn.execute(
            """SELECT * FROM messages WHERE UPPER(from_call) LIKE ? ORDER BY timestamp DESC LIMIT ?""",
            (q, int(limit)),
        ).fetchall()
    return [dict(r) for r in rows]


def callsign_suggestions(prefix: str = "", limit: int = 30) -> list[str]:
    p = prefix.upper().strip() + "%"
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT callsign FROM (
                SELECT callsign AS callsign FROM stations
                UNION SELECT from_call FROM messages
                UNION SELECT to_call FROM messages
            )
            WHERE UPPER(callsign) LIKE ?
            ORDER BY callsign LIMIT ?
            """,
            (p, int(limit)),
        ).fetchall()
    return [r[0] for r in rows if r[0]]


def add_aprs_log(direction: str, raw: str) -> int:
    direction = str(direction or "").upper().strip()
    if direction not in {"RX", "TX"}:
        raise ValueError("Direção do log APRS-IS deve ser RX ou TX.")
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO aprs_log(timestamp, direction, raw) VALUES (?, ?, ?)",
            (utc_now_iso(), direction, str(raw)),
        )
        # Retém os 100 mil registros mais recentes.
        conn.execute(
            "DELETE FROM aprs_log WHERE id NOT IN (SELECT id FROM aprs_log ORDER BY id DESC LIMIT 100000)"
        )
        return int(cur.lastrowid)


def list_aprs_log(filter_text: str = "", direction: str = "ALL", limit: int = 1000) -> list[dict[str, Any]]:
    direction = str(direction or "ALL").upper().strip()
    if direction not in {"ALL", "RX", "TX"}:
        direction = "ALL"
    q = "%" + str(filter_text or "").upper().strip() + "%"
    limit = max(1, min(int(limit or 1000), 10000))
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM (
                SELECT id, timestamp, direction, raw
                FROM aprs_log
                WHERE (? = 'ALL' OR direction = ?)
                  AND UPPER(raw) LIKE ?
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (direction, direction, q, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def clear_aprs_log() -> None:
    with connection() as conn:
        conn.execute("DELETE FROM aprs_log")
