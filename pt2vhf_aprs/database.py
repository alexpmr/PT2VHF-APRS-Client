from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
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

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PT2VHF APRS Client" / "data"

    xdg_data_home = os.getenv("XDG_DATA_HOME")
    linux_base = Path(xdg_data_home).expanduser() if xdg_data_home else Path.home() / ".local" / "share"
    return linux_base / "PT2VHF-APRS-Client" / "data"


DB_PATH = _default_data_dir() / "pt2vhf_aprs.db"

DEFAULT_CONFIG = {
    "callsign": "",
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
    "aprs_filter": "r/2000",
    "connect_on_start": 0,
    "open_browser_on_start": 0,
    "language": "pt-BR",
    "map_type": "osm",
    "track_color": "#3ba6ff",
    "track_width": 2,
    "topology_rf_color": "#35a7ff",
    "topology_igate_color": "#b06cff",
    "topology_width": 2,
    "map_brightness": 100,
    "sound_on_personal_message": 1,
    "message_popup_seconds": 5,
    "app_theme": "dark",
    "messages_font_family": "system",
    "messages_font_size": 12,
    "stations_font_family": "system",
    "stations_font_size": 12,
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
                aprs_filter TEXT NOT NULL DEFAULT 'r/2000',
                connect_on_start INTEGER NOT NULL DEFAULT 0,
                open_browser_on_start INTEGER NOT NULL DEFAULT 0,
                language TEXT NOT NULL DEFAULT 'pt-BR',
                map_type TEXT NOT NULL DEFAULT 'osm',
                track_color TEXT NOT NULL DEFAULT '#3ba6ff',
                track_width INTEGER NOT NULL DEFAULT 2,
                topology_rf_color TEXT NOT NULL DEFAULT '#35a7ff',
                topology_igate_color TEXT NOT NULL DEFAULT '#b06cff',
                topology_width INTEGER NOT NULL DEFAULT 2,
                map_brightness INTEGER NOT NULL DEFAULT 100,
                sound_on_personal_message INTEGER NOT NULL DEFAULT 1,
                message_popup_seconds INTEGER NOT NULL DEFAULT 5,
                app_theme TEXT NOT NULL DEFAULT 'dark',
                messages_font_family TEXT NOT NULL DEFAULT 'system',
                messages_font_size INTEGER NOT NULL DEFAULT 12,
                stations_font_family TEXT NOT NULL DEFAULT 'system',
                stations_font_size INTEGER NOT NULL DEFAULT 12,
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

            CREATE TABLE IF NOT EXISTS topology_edges (
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                kind TEXT NOT NULL,
                packet_count INTEGER NOT NULL DEFAULT 1,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                igate TEXT,
                PRIMARY KEY(source, target, kind)
            );
            CREATE INDEX IF NOT EXISTS idx_topology_last_seen ON topology_edges(last_seen DESC);
            """
        )
        config_columns = {row["name"] for row in conn.execute("PRAGMA table_info(config)").fetchall()}
        if "open_browser_on_start" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN open_browser_on_start INTEGER NOT NULL DEFAULT 0")
        if "language" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN language TEXT NOT NULL DEFAULT 'pt-BR'")
        if "map_type" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN map_type TEXT NOT NULL DEFAULT 'osm'")
        if "track_color" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN track_color TEXT NOT NULL DEFAULT '#3ba6ff'")
        if "track_width" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN track_width INTEGER NOT NULL DEFAULT 2")
        if "topology_rf_color" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN topology_rf_color TEXT NOT NULL DEFAULT '#35a7ff'")
        if "topology_igate_color" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN topology_igate_color TEXT NOT NULL DEFAULT '#b06cff'")
        if "topology_width" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN topology_width INTEGER NOT NULL DEFAULT 2")
        if "map_brightness" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN map_brightness INTEGER NOT NULL DEFAULT 100")
        if "sound_on_personal_message" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN sound_on_personal_message INTEGER NOT NULL DEFAULT 1")
        if "message_popup_seconds" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN message_popup_seconds INTEGER NOT NULL DEFAULT 5")
        if "app_theme" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN app_theme TEXT NOT NULL DEFAULT 'dark'")
        if "messages_font_family" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN messages_font_family TEXT NOT NULL DEFAULT 'system'")
        if "messages_font_size" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN messages_font_size INTEGER NOT NULL DEFAULT 12")
        if "stations_font_family" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN stations_font_family TEXT NOT NULL DEFAULT 'system'")
        if "stations_font_size" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN stations_font_size INTEGER NOT NULL DEFAULT 12")

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


def validate_required_station_config(config: dict[str, Any]) -> None:
    missing: list[str] = []
    if not str(config.get("callsign") or "").strip():
        missing.append("Indicativo")
    if config.get("latitude") in ("", None):
        missing.append("Latitude")
    if config.get("longitude") in ("", None):
        missing.append("Longitude")
    if config.get("altitude") in ("", None):
        missing.append("Altitude")

    if missing:
        raise ValueError(
            "Preencha os campos obrigatórios antes de continuar: " + ", ".join(missing) + "."
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
    merged["open_browser_on_start"] = 1 if bool(merged["open_browser_on_start"]) else 0
    merged["language"] = str(merged["language"] or "pt-BR").strip()
    merged["aprs_filter"] = str(merged["aprs_filter"] or "").strip()
    merged["map_type"] = str(merged["map_type"] or "osm").lower().strip()
    merged["track_color"] = str(merged["track_color"] or "#3ba6ff").lower().strip()
    merged["track_width"] = int(merged["track_width"] or 2)
    merged["topology_rf_color"] = str(merged["topology_rf_color"] or "#35a7ff").lower().strip()
    merged["topology_igate_color"] = str(merged["topology_igate_color"] or "#b06cff").lower().strip()
    merged["topology_width"] = int(merged["topology_width"] or 2)
    merged["map_brightness"] = int(merged["map_brightness"] or 100)
    merged["sound_on_personal_message"] = 1 if bool(merged["sound_on_personal_message"]) else 0
    merged["message_popup_seconds"] = int(merged["message_popup_seconds"] or 5)
    merged["app_theme"] = str(merged["app_theme"] or "dark").lower().strip()
    merged["messages_font_family"] = str(merged["messages_font_family"] or "system").lower().strip()
    merged["messages_font_size"] = int(merged["messages_font_size"] or 12)
    merged["stations_font_family"] = str(merged["stations_font_family"] or "system").lower().strip()
    merged["stations_font_size"] = int(merged["stations_font_size"] or 12)
    merged["symbol_table"] = (str(merged["symbol_table"] or "/")[:1])
    merged["symbol"] = (str(merged["symbol"] or ">")[:1])
    for field in ("latitude", "longitude", "altitude"):
        if merged[field] in ("", None):
            merged[field] = None
        else:
            merged[field] = float(merged[field])

    # Salvar preferências não exige uma estação completa. A validação dos
    # campos obrigatórios acontece no momento da conexão ao APRS-IS.
    if not (0 <= merged["ssid"] <= 15):
        raise ValueError("SSID deve estar entre 0 e 15.")
    if merged["latitude"] is not None and not (-90 <= merged["latitude"] <= 90):
        raise ValueError("Latitude inválida.")
    if merged["longitude"] is not None and not (-180 <= merged["longitude"] <= 180):
        raise ValueError("Longitude inválida.")
    if not (1 <= merged["port"] <= 65535):
        raise ValueError("Porta inválida.")
    if merged["map_type"] not in {"osm", "topo", "satellite"}:
        raise ValueError("Tipo de mapa inválido.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", merged["track_color"]):
        raise ValueError("Cor do tracklog inválida.")
    if not (1 <= merged["track_width"] <= 10):
        raise ValueError("Espessura do tracklog deve estar entre 1 e 10.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", merged["topology_rf_color"]):
        raise ValueError("Cor dos enlaces RF da topologia inválida.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", merged["topology_igate_color"]):
        raise ValueError("Cor dos enlaces IGate da topologia inválida.")
    if not (1 <= merged["topology_width"] <= 10):
        raise ValueError("Espessura da topologia deve estar entre 1 e 10.")
    if not (30 <= merged["map_brightness"] <= 150):
        raise ValueError("Brilho do mapa deve estar entre 30% e 150%.")
    if not (1 <= merged["message_popup_seconds"] <= 60):
        raise ValueError("Duração do aviso de mensagem deve estar entre 1 e 60 segundos.")

    if merged["app_theme"] not in {"dark", "light"}:
        raise ValueError("Tema da aplicação inválido.")
    if merged["language"] not in {"pt-BR", "en"}:
        raise ValueError("Idioma da aplicação inválido.")

    allowed_fonts = {"system", "segoe", "arial", "verdana", "tahoma", "consolas"}
    if merged["messages_font_family"] not in allowed_fonts:
        raise ValueError("Fonte da tela de mensagens inválida.")
    if merged["stations_font_family"] not in allowed_fonts:
        raise ValueError("Fonte da tela de estações inválida.")
    if not (10 <= merged["messages_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de mensagens deve estar entre 10 e 20 px.")
    if not (10 <= merged["stations_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de estações deve estar entre 10 e 20 px.")

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


def _is_topology_callsign(value: str) -> bool:
    value = str(value or "").upper().strip().rstrip("*")
    if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", value):
        return False
    blocked = ("WIDE", "TRACE", "RELAY", "TCPIP", "TCPXX", "NOGATE", "RFONLY")
    return not value.startswith(blocked)


def record_topology_from_raw(raw: str) -> None:
    """Registra somente relações observáveis no path APRS/TNC2."""
    line = str(raw or "").strip()
    if ">" not in line or ":" not in line:
        return
    source = line.split(">", 1)[0].upper().strip()
    if not _is_topology_callsign(source):
        return

    header = line.split(":", 1)[0]
    route = header.split(">", 1)[1].split(",")
    if len(route) < 2:
        return

    path = [part.strip().upper() for part in route[1:] if part.strip()]
    now = utc_now_iso()
    edges: list[tuple[str, str, str, str | None]] = []
    previous = source

    for token in path:
        if token.lower().startswith("q"):
            break
        if not token.endswith("*"):
            continue
        node = token.rstrip("*")
        if _is_topology_callsign(node) and node != previous:
            edges.append((previous, node, "rf", None))
            previous = node

    igate = None
    for i, token in enumerate(path):
        if token in {"QAR", "QAO"} and i + 1 < len(path):
            candidate = path[i + 1].rstrip("*")
            if _is_topology_callsign(candidate):
                igate = candidate
                if igate != previous:
                    edges.append((previous, igate, "igate", igate))
            break

    if not edges:
        return

    with connection() as conn:
        for edge_source, target, kind, edge_igate in edges:
            conn.execute(
                """
                INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen,igate)
                VALUES(?,?,?,1,?,?,?)
                ON CONFLICT(source,target,kind) DO UPDATE SET
                    packet_count=topology_edges.packet_count+1,
                    last_seen=excluded.last_seen,
                    igate=COALESCE(excluded.igate, topology_edges.igate)
                """,
                (edge_source, target, kind, now, now, edge_igate),
            )


def list_topology_edges(hours: int = 24) -> list[dict[str, Any]]:
    hours = max(1, min(int(hours or 24), 24 * 30))
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT e.source,e.target,e.kind,e.packet_count,e.first_seen,e.last_seen,e.igate,
                   s1.latitude AS source_lat,s1.longitude AS source_lon,
                   s2.latitude AS target_lat,s2.longitude AS target_lon
            FROM topology_edges e
            JOIN stations s1 ON UPPER(s1.callsign)=UPPER(e.source)
            JOIN stations s2 ON UPPER(s2.callsign)=UPPER(e.target)
            WHERE e.last_seen >= ?
              AND s1.latitude IS NOT NULL AND s1.longitude IS NOT NULL
              AND s2.latitude IS NOT NULL AND s2.longitude IS NOT NULL
            ORDER BY e.packet_count DESC, e.last_seen DESC
            LIMIT 1500
            """,
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


def summary_counts() -> dict[str, int]:
    with connection() as conn:
        stations = int(conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0])
        messages = int(conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
    return {"stations": stations, "messages": messages}


def clear_tracklogs() -> int:
    with connection() as conn:
        cur = conn.execute("DELETE FROM tracks")
        return max(0, int(cur.rowcount or 0))


def clear_stations() -> dict[str, int]:
    with connection() as conn:
        tracks_cur = conn.execute("DELETE FROM tracks")
        topology_cur = conn.execute("DELETE FROM topology_edges")
        stations_cur = conn.execute("DELETE FROM stations")
        return {
            "stations": max(0, int(stations_cur.rowcount or 0)),
            "tracks": max(0, int(tracks_cur.rowcount or 0)),
            "topology": max(0, int(topology_cur.rowcount or 0)),
        }


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


def list_messages(from_filter: str = "", station_filter: str = "", limit: int = 5000) -> list[dict[str, Any]]:
    station = str(station_filter or "").upper().strip()
    q = "%" + str(from_filter or "").upper().strip() + "%"
    with connection() as conn:
        if station:
            rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE message_type='message'
                  AND (UPPER(from_call)=? OR UPPER(to_call)=?)
                ORDER BY timestamp DESC LIMIT ?
                """,
                (station, station, int(limit)),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM messages WHERE UPPER(from_call) LIKE ? ORDER BY timestamp DESC LIMIT ?""",
                (q, int(limit)),
            ).fetchall()
    return [dict(r) for r in rows]


def clear_messages() -> int:
    with connection() as conn:
        cur = conn.execute("DELETE FROM messages")
        return max(0, int(cur.rowcount or 0))


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
            SELECT id, timestamp, direction, raw
            FROM aprs_log
            WHERE (? = 'ALL' OR direction = ?)
              AND UPPER(raw) LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (direction, direction, q, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def clear_aprs_log() -> None:
    with connection() as conn:
        conn.execute("DELETE FROM aprs_log")
