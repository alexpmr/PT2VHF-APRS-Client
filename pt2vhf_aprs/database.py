from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable

from . import APP_TOCALL
from . import diagnostics as diag

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

BRAZIL_FILTER = "p/PP/PQ/PR/PS/PT/PU/PV/PW/PX/PY/ZV/ZW/ZX/ZY/ZZ"

PACKET_RETENTION = 100_000
APRS_LOG_RETENTION = 100_000
TOPOLOGY_EVENT_RETENTION = 200_000
RETENTION_SWEEP_EVERY = 1_000
RETENTION_SWEEP_SECONDS = 300.0

_retention_lock = threading.Lock()
_retention_state = {
    "packets": {"pending": 0, "last": time.monotonic()},
    "aprs_log": {"pending": 0, "last": time.monotonic()},
    "topology_events": {"pending": 0, "last": time.monotonic()},
}

_topology_query_lock = threading.Lock()
_topology_cache_lock = threading.Lock()
_topology_cache: dict[int, tuple[float, list[dict[str, Any]]]] = {}
TOPOLOGY_CACHE_SECONDS = 2.0
TOPOLOGY_QUERY_MAX_SECONDS = 2.5

APRS_DEVICE_ID_PATH = Path(__file__).resolve().parent / "data" / "aprs_device_ids.json"
_aprs_device_id_lock = threading.Lock()
_aprs_device_id_entries: list[dict[str, Any]] | None = None

TRACK_OUTLIER_MIN_KM = 75.0
TRACK_OUTLIER_MAX_SPEED_KMH = 1200.0
TRACK_RELOCATION_CONFIRMATIONS = 3
TRACK_RELOCATION_CLUSTER_KM = 25.0
RF_POSITION_MAX_DISTANCE_KM = 2500.0
POSITION_ZERO_EPSILON = 1e-9
_track_relocation_lock = threading.Lock()
_track_relocation_candidates: dict[str, dict[str, Any]] = {}


def _retention_due(name: str, added: int = 1) -> bool:
    """Executa housekeeping apenas em lotes, nunca a cada pacote recebido."""
    now = time.monotonic()
    with _retention_lock:
        state = _retention_state[name]
        state["pending"] = int(state["pending"]) + max(1, int(added or 1))
        if int(state["pending"]) < RETENTION_SWEEP_EVERY and now - float(state["last"]) < RETENTION_SWEEP_SECONDS:
            return False
        state["pending"] = 0
        state["last"] = now
        return True


def _trim_history_table(conn: sqlite3.Connection, table: str, keep: int) -> int:
    """Remove somente o excedente usando a PK; chamada esporadicamente."""
    if table not in {"packets", "aprs_log", "topology_events"}:
        raise ValueError("Tabela de retenção inválida.")
    keep = max(1, int(keep))
    row = conn.execute(
        f"SELECT id FROM {table} ORDER BY id DESC LIMIT 1 OFFSET ?",
        (keep - 1,),
    ).fetchone()
    if not row:
        return 0
    cutoff = int(row[0])
    cur = conn.execute(f"DELETE FROM {table} WHERE id < ?", (cutoff,))
    return max(0, int(cur.rowcount or 0))


DEFAULT_CONFIG = {
    "callsign": "",
    "ssid": 0,
    "comment": "PT2VHF APRS Client",
    "latitude": None,
    "longitude": None,
    "altitude": None,
    "altitude_source": "manual",
    "symbol_table": "/",
    "symbol": ">",
    "beacon_minutes": 10,
    "email": "",
    "server": "soam.aprs2.net",
    "port": 14580,
    "passcode": "",
    "aprs_filter": BRAZIL_FILTER,
    "connect_on_start": 1,
    "open_browser_on_start": 0,
    "check_updates_on_start": 1,
    "auto_download_updates": 0,
    "install_updates_on_exit": 0,
    "message_retry_seconds": 60,
    "message_retry_attempts": 2,
    "respond_to_queries": 1,
    "language": "pt-BR",
    "map_type": "osm",
    "track_color": "#3ba6ff",
    "track_width": 2,
    "topology_rf_color": "#ffff00",
    "topology_igate_color": "#ffff00",
    "topology_width": 1,
    "map_brightness": 100,
    "sound_on_personal_message": 1,
    "sound_on_station_activity": 1,
    "highlight_station_activity": 1,
    "traffic_animation_enabled": 1,
    "message_popup_seconds": 5,
    "app_theme": "dark",
    "messages_font_family": "system",
    "messages_font_size": 12,
    "messages_font_weight": "normal",
    "messages_line_height": 1.35,
    "stations_font_family": "system",
    "stations_font_size": 12,
    "stations_font_weight": "normal",
    "stations_line_height": 1.25,
    "logs_font_family": "consolas",
    "logs_font_size": 12,
    "logs_font_weight": "normal",
    "logs_line_height": 1.30,
    "statistics_font_size": 13,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _configure_database_runtime() -> None:
    """Configura pragmas globais uma vez, antes de iniciar threads e requests."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.commit()
    finally:
        conn.close()


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    conn = None
    error_text = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        yield conn
        conn.commit()
    except Exception as exc:
        error_text = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if conn is not None:
            conn.close()
        duration_ms = (time.monotonic() - started) * 1000
        if duration_ms >= 750 or error_text:
            diag.log_sqlite_slow(duration_ms, error=error_text)


def init_db() -> None:
    _configure_database_runtime()
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
                altitude_source TEXT NOT NULL DEFAULT 'manual',
                symbol_table TEXT NOT NULL DEFAULT '/',
                symbol TEXT NOT NULL DEFAULT '>',
                beacon_minutes INTEGER NOT NULL DEFAULT 10,
                email TEXT NOT NULL DEFAULT '',
                server TEXT NOT NULL DEFAULT 'soam.aprs2.net',
                port INTEGER NOT NULL DEFAULT 14580,
                passcode TEXT NOT NULL DEFAULT '',
                aprs_filter TEXT NOT NULL DEFAULT 'p/PP/PQ/PR/PS/PT/PU/PV/PW/PX/PY/ZV/ZW/ZX/ZY/ZZ',
                connect_on_start INTEGER NOT NULL DEFAULT 1,
                open_browser_on_start INTEGER NOT NULL DEFAULT 0,
                check_updates_on_start INTEGER NOT NULL DEFAULT 1,
                auto_download_updates INTEGER NOT NULL DEFAULT 0,
                install_updates_on_exit INTEGER NOT NULL DEFAULT 0,
                message_retry_seconds INTEGER NOT NULL DEFAULT 60,
                message_retry_attempts INTEGER NOT NULL DEFAULT 2,
                respond_to_queries INTEGER NOT NULL DEFAULT 1,
                language TEXT NOT NULL DEFAULT 'pt-BR',
                map_type TEXT NOT NULL DEFAULT 'osm',
                track_color TEXT NOT NULL DEFAULT '#3ba6ff',
                track_width INTEGER NOT NULL DEFAULT 2,
                topology_rf_color TEXT NOT NULL DEFAULT '#ffff00',
                topology_igate_color TEXT NOT NULL DEFAULT '#ffff00',
                topology_width INTEGER NOT NULL DEFAULT 1,
                map_brightness INTEGER NOT NULL DEFAULT 100,
                sound_on_personal_message INTEGER NOT NULL DEFAULT 1,
                sound_on_station_activity INTEGER NOT NULL DEFAULT 1,
                highlight_station_activity INTEGER NOT NULL DEFAULT 1,
                traffic_animation_enabled INTEGER NOT NULL DEFAULT 1,
                message_popup_seconds INTEGER NOT NULL DEFAULT 5,
                app_theme TEXT NOT NULL DEFAULT 'dark',
                messages_font_family TEXT NOT NULL DEFAULT 'system',
                messages_font_size INTEGER NOT NULL DEFAULT 12,
                messages_font_weight TEXT NOT NULL DEFAULT 'normal',
                messages_line_height REAL NOT NULL DEFAULT 1.35,
                stations_font_family TEXT NOT NULL DEFAULT 'system',
                stations_font_size INTEGER NOT NULL DEFAULT 12,
                stations_font_weight TEXT NOT NULL DEFAULT 'normal',
                stations_line_height REAL NOT NULL DEFAULT 1.25,
                logs_font_family TEXT NOT NULL DEFAULT 'consolas',
                logs_font_size INTEGER NOT NULL DEFAULT 12,
                logs_font_weight TEXT NOT NULL DEFAULT 'normal',
                logs_line_height REAL NOT NULL DEFAULT 1.30,
                statistics_font_size INTEGER NOT NULL DEFAULT 13,
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

            CREATE TABLE IF NOT EXISTS favorites (
                callsign TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_favorites_created ON favorites(created_at);

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
                message_group_id TEXT,
                part_index INTEGER,
                part_count INTEGER,
                retry_count INTEGER NOT NULL DEFAULT 0,
                read_at TEXT,
                timestamp TEXT NOT NULL,
                raw TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_call);

            CREATE TABLE IF NOT EXISTS aprs_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                direction TEXT NOT NULL CHECK(direction IN ('in','out')),
                peer TEXT NOT NULL,
                query_type TEXT NOT NULL,
                query_payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '',
                sent_at TEXT NOT NULL,
                response_at TEXT,
                rtt_ms REAL,
                response_text TEXT,
                response_raw TEXT,
                trace_path TEXT,
                message_id TEXT,
                raw TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_aprs_queries_peer_time ON aprs_queries(peer, id DESC);
            CREATE INDEX IF NOT EXISTS idx_aprs_queries_pending ON aprs_queries(direction, status, peer, query_type);

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
            CREATE INDEX IF NOT EXISTS idx_topology_source_target ON topology_edges(source, target);
            CREATE INDEX IF NOT EXISTS idx_topology_target ON topology_edges(target);

            CREATE TABLE IF NOT EXISTS topology_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                kind TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_topology_events_time ON topology_events(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_topology_events_source_target ON topology_events(source, target);

            CREATE TABLE IF NOT EXISTS station_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                callsign TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                details TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_station_anomalies_call_time ON station_anomalies(callsign, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_station_anomalies_time ON station_anomalies(timestamp DESC);
            """
        )
        # Migração v1.7.7: o nó após um qA* pertence à transição para
        # APRS-IS/Internet. Versões anteriores chegaram a converter esse trecho
        # para RF, produzindo linhas continentais/intercontinentais falsas.
        old_internet_rows = conn.execute(
            """SELECT source,target,packet_count,first_seen,last_seen,igate
               FROM topology_edges
               WHERE kind='rf' AND igate IS NOT NULL"""
        ).fetchall()
        for old_edge in old_internet_rows:
            conn.execute(
                """INSERT INTO topology_edges(source,target,kind,packet_count,first_seen,last_seen,igate)
                   VALUES(?,?, 'igate', ?,?,?,?)
                   ON CONFLICT(source,target,kind) DO UPDATE SET
                     packet_count=topology_edges.packet_count + excluded.packet_count,
                     first_seen=MIN(topology_edges.first_seen, excluded.first_seen),
                     last_seen=MAX(topology_edges.last_seen, excluded.last_seen),
                     igate=COALESCE(excluded.igate, topology_edges.igate)""",
                (
                    old_edge["source"],
                    old_edge["target"],
                    int(old_edge["packet_count"] or 0),
                    old_edge["first_seen"],
                    old_edge["last_seen"],
                    old_edge["igate"],
                ),
            )
        if old_internet_rows:
            conn.execute("DELETE FROM topology_edges WHERE kind='rf' AND igate IS NOT NULL")

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
            conn.execute("ALTER TABLE config ADD COLUMN topology_rf_color TEXT NOT NULL DEFAULT '#ffff00'")
        if "topology_igate_color" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN topology_igate_color TEXT NOT NULL DEFAULT '#ffff00'")
        if "topology_width" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN topology_width INTEGER NOT NULL DEFAULT 1")
        if "map_brightness" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN map_brightness INTEGER NOT NULL DEFAULT 100")
        if "sound_on_personal_message" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN sound_on_personal_message INTEGER NOT NULL DEFAULT 1")
        if "sound_on_station_activity" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN sound_on_station_activity INTEGER NOT NULL DEFAULT 1")
        if "highlight_station_activity" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN highlight_station_activity INTEGER NOT NULL DEFAULT 1")
        if "traffic_animation_enabled" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN traffic_animation_enabled INTEGER NOT NULL DEFAULT 1")
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
        if "messages_font_weight" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN messages_font_weight TEXT NOT NULL DEFAULT 'normal'")
        if "messages_line_height" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN messages_line_height REAL NOT NULL DEFAULT 1.35")
        if "stations_font_weight" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN stations_font_weight TEXT NOT NULL DEFAULT 'normal'")
        if "stations_line_height" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN stations_line_height REAL NOT NULL DEFAULT 1.25")
        if "logs_font_family" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN logs_font_family TEXT NOT NULL DEFAULT 'consolas'")
        if "logs_font_size" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN logs_font_size INTEGER NOT NULL DEFAULT 12")
        if "logs_font_weight" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN logs_font_weight TEXT NOT NULL DEFAULT 'normal'")
        if "logs_line_height" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN logs_line_height REAL NOT NULL DEFAULT 1.30")
        if "statistics_font_size" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN statistics_font_size INTEGER NOT NULL DEFAULT 13")
        if "altitude_source" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN altitude_source TEXT NOT NULL DEFAULT 'manual'")
        if "check_updates_on_start" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN check_updates_on_start INTEGER NOT NULL DEFAULT 1")
        if "auto_download_updates" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN auto_download_updates INTEGER NOT NULL DEFAULT 1")
        if "install_updates_on_exit" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN install_updates_on_exit INTEGER NOT NULL DEFAULT 1")
        if "message_retry_seconds" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN message_retry_seconds INTEGER NOT NULL DEFAULT 60")
        if "message_retry_attempts" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN message_retry_attempts INTEGER NOT NULL DEFAULT 2")
        if "respond_to_queries" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN respond_to_queries INTEGER NOT NULL DEFAULT 1")

        # Corrige o antigo padrão v1.2, que combinava brazil.aprs2.net com 14580.
        # Mantém configurações personalizadas intactas.
        legacy = conn.execute("SELECT server, port FROM config WHERE id=1").fetchone()
        if legacy and str(legacy["server"] or "").lower() == "brazil.aprs2.net" and int(legacy["port"] or 0) == 14580:
            conn.execute(
                "UPDATE config SET server='soam.aprs2.net', updated_at=? WHERE id=1",
                (utc_now_iso(),),
            )

        message_columns = {row["name"] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
        if "message_type" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN message_type TEXT NOT NULL DEFAULT 'message'")
        if "message_group_id" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN message_group_id TEXT")
        if "part_index" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN part_index INTEGER")
        if "part_count" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN part_count INTEGER")
        if "retry_count" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0")
        if "read_at" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN read_at TEXT")
            conn.execute("UPDATE messages SET read_at=timestamp WHERE direction='in'")

        row = conn.execute("SELECT id FROM config WHERE id=1").fetchone()
        if not row:
            now = utc_now_iso()
            cols = ", ".join(DEFAULT_CONFIG.keys())
            placeholders = ", ".join("?" for _ in DEFAULT_CONFIG)
            conn.execute(
                f"INSERT INTO config (id, {cols}, updated_at) VALUES (1, {placeholders}, ?)",
                [*DEFAULT_CONFIG.values(), now],
            )
        conn.execute("UPDATE config SET auto_download_updates=0, install_updates_on_exit=0 WHERE id=1")
        row = conn.execute("SELECT id FROM map_state WHERE id=1").fetchone()
        if not row:
            conn.execute(
                "INSERT INTO map_state (id, latitude, longitude, zoom, updated_at) VALUES (1, -14.2350, -51.9253, 4, ?)",
                (utc_now_iso(),),
            )


def validate_required_station_config(config: dict[str, Any]) -> None:
    missing: list[str] = []
    callsign = str(config.get("callsign") or "").strip().upper()
    if not callsign:
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
    if not re.fullmatch(r"[A-Z0-9]{1,6}", callsign):
        raise ValueError("Indicativo inválido. Use de 1 a 6 letras ou números, sem SSID.")


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
    merged["server"] = str(merged["server"] or "soam.aprs2.net").strip()
    merged["port"] = int(merged["port"] or 14580)
    merged["altitude_source"] = str(merged["altitude_source"] or "manual").lower().strip()
    merged["beacon_minutes"] = max(1, int(merged["beacon_minutes"] or 10))
    merged["connect_on_start"] = 1 if bool(merged["connect_on_start"]) else 0
    merged["open_browser_on_start"] = 1 if bool(merged["open_browser_on_start"]) else 0
    merged["check_updates_on_start"] = 1 if bool(merged["check_updates_on_start"]) else 0
    merged["auto_download_updates"] = 0
    merged["install_updates_on_exit"] = 0
    merged["message_retry_seconds"] = max(15, min(3600, int(merged["message_retry_seconds"] or 60)))
    merged["message_retry_attempts"] = max(0, min(10, int(merged["message_retry_attempts"] or 0)))
    merged["respond_to_queries"] = 1 if bool(merged["respond_to_queries"]) else 0
    merged["language"] = str(merged["language"] or "pt-BR").strip()
    merged["aprs_filter"] = str(merged["aprs_filter"] or "").strip()
    merged["map_type"] = str(merged["map_type"] or "osm").lower().strip()
    merged["track_color"] = str(merged["track_color"] or "#3ba6ff").lower().strip()
    merged["track_width"] = int(merged["track_width"] or 2)
    merged["topology_rf_color"] = str(merged["topology_rf_color"] or "#ffff00").lower().strip()
    merged["topology_igate_color"] = str(merged["topology_igate_color"] or "#ffff00").lower().strip()
    merged["topology_width"] = int(merged["topology_width"] or 1)
    merged["map_brightness"] = int(merged["map_brightness"] or 100)
    merged["sound_on_personal_message"] = 1 if bool(merged["sound_on_personal_message"]) else 0
    merged["sound_on_station_activity"] = 1 if bool(merged["sound_on_station_activity"]) else 0
    merged["highlight_station_activity"] = 1 if bool(merged["highlight_station_activity"]) else 0
    merged["traffic_animation_enabled"] = 1 if bool(merged["traffic_animation_enabled"]) else 0
    merged["message_popup_seconds"] = int(merged["message_popup_seconds"] or 5)
    merged["app_theme"] = str(merged["app_theme"] or "dark").lower().strip()
    merged["messages_font_family"] = str(merged["messages_font_family"] or "system").lower().strip()
    merged["messages_font_size"] = int(merged["messages_font_size"] or 12)
    merged["messages_font_weight"] = str(merged["messages_font_weight"] or "normal").lower().strip()
    merged["messages_line_height"] = float(merged["messages_line_height"] or 1.35)
    merged["stations_font_family"] = str(merged["stations_font_family"] or "system").lower().strip()
    merged["stations_font_size"] = int(merged["stations_font_size"] or 12)
    merged["stations_font_weight"] = str(merged["stations_font_weight"] or "normal").lower().strip()
    merged["stations_line_height"] = float(merged["stations_line_height"] or 1.25)
    merged["logs_font_family"] = str(merged["logs_font_family"] or "consolas").lower().strip()
    merged["logs_font_size"] = int(merged["logs_font_size"] or 12)
    merged["logs_font_weight"] = str(merged["logs_font_weight"] or "normal").lower().strip()
    merged["logs_line_height"] = float(merged["logs_line_height"] or 1.30)
    merged["statistics_font_size"] = int(merged["statistics_font_size"] or 13)
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
    if not merged["server"]:
        raise ValueError("Servidor APRS-IS não pode ficar vazio.")
    if not (1 <= merged["port"] <= 65535):
        raise ValueError("Porta inválida.")
    if merged["altitude_source"] not in {"manual", "geolocation", "fallback_zero"}:
        merged["altitude_source"] = "manual"
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
    if merged["language"] not in {"pt-BR", "en", "es", "fr"}:
        raise ValueError("Idioma da aplicação inválido.")

    allowed_fonts = {"system", "segoe", "arial", "verdana", "tahoma", "consolas"}
    if merged["messages_font_family"] not in allowed_fonts:
        raise ValueError("Fonte da tela de mensagens inválida.")
    if merged["stations_font_family"] not in allowed_fonts:
        raise ValueError("Fonte da tela de estações inválida.")
    if merged["logs_font_family"] not in allowed_fonts:
        raise ValueError("Fonte da tela de logs inválida.")
    if merged["messages_font_weight"] not in {"normal", "bold"}:
        raise ValueError("Peso da fonte de mensagens inválido.")
    if merged["stations_font_weight"] not in {"normal", "bold"}:
        raise ValueError("Peso da fonte de estações inválido.")
    if merged["logs_font_weight"] not in {"normal", "bold"}:
        raise ValueError("Peso da fonte de logs inválido.")
    if not (10 <= merged["messages_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de mensagens deve estar entre 10 e 20 px.")
    if not (10 <= merged["stations_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de estações deve estar entre 10 e 20 px.")
    if not (10 <= merged["logs_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de logs deve estar entre 10 e 20 px.")
    if not (11 <= merged["statistics_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de estatísticas deve estar entre 11 e 20 px.")
    for key, label in (
        ("messages_line_height", "mensagens"),
        ("stations_line_height", "estações"),
        ("logs_line_height", "logs"),
    ):
        if not (1.0 <= float(merged[key]) <= 2.0):
            raise ValueError(f"Espaçamento de linha de {label} deve estar entre 1,0 e 2,0.")

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


def _valid_geo_position(latitude: Any, longitude: Any) -> bool:
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(lat) or not math.isfinite(lon):
        return False
    if lat < -90.0 or lat > 90.0 or lon < -180.0 or lon > 180.0:
        return False
    if abs(lat) <= POSITION_ZERO_EPSILON and abs(lon) <= POSITION_ZERO_EPSILON:
        return False
    return True


def _path_tokens(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        raw = value
    else:
        try:
            raw = json.loads(str(value or "[]"))
        except Exception:
            raw = []
    if not isinstance(raw, list):
        return []
    # Preserve q-construct case: qAR and qAr have different APRS-IS meanings.
    return [str(item or "").strip() for item in raw if str(item or "").strip()]


def _rf_igate_from_path(value: Any) -> str:
    path = _path_tokens(value)
    for index, token in enumerate(path[:-1]):
        if token not in {"qAR", "qAO"}:
            continue
        prior = {item.rstrip("*").upper() for item in path[:index]}
        if prior & {"TCPIP", "TCPXX"}:
            continue
        relay = path[index + 1].rstrip("*").upper().strip()
        if relay and relay not in {"TCPIP", "TCPXX"}:
            return relay
    return ""


def _record_station_anomaly_conn(
    conn: sqlite3.Connection,
    callsign: str,
    issue_type: str,
    latitude: Any = None,
    longitude: Any = None,
    details: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """INSERT INTO station_anomalies(callsign,timestamp,issue_type,latitude,longitude,details)
           VALUES(?,?,?,?,?,?)""",
        (
            str(callsign or "").upper().strip(),
            utc_now_iso(),
            str(issue_type or "unknown"),
            latitude,
            longitude,
            json.dumps(details or {}, ensure_ascii=False, separators=(",", ":")),
        ),
    )


def _rf_relay_position_issue_conn(
    conn: sqlite3.Connection,
    path_value: Any,
    latitude: float,
    longitude: float,
) -> tuple[str | None, dict[str, Any]]:
    relay = _rf_igate_from_path(path_value)
    if not relay:
        return None, {}
    row = conn.execute(
        "SELECT callsign,latitude,longitude FROM stations WHERE UPPER(callsign)=?",
        (relay,),
    ).fetchone()
    if not row or not _valid_geo_position(row["latitude"], row["longitude"]):
        return None, {}
    distance = haversine_km(
        float(latitude),
        float(longitude),
        float(row["latitude"]),
        float(row["longitude"]),
    )
    if distance <= RF_POSITION_MAX_DISTANCE_KM:
        return None, {"relay": relay, "relay_distance_km": distance}
    return "rf_relay_distance", {
        "relay": relay,
        "relay_distance_km": distance,
        "limit_km": RF_POSITION_MAX_DISTANCE_KM,
    }


def _station_position_issues_conn(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        "SELECT callsign,latitude,longitude,path,last_heard FROM stations"
    ).fetchall()
    valid_coords: dict[str, tuple[float, float]] = {}
    for row in rows:
        if _valid_geo_position(row["latitude"], row["longitude"]):
            valid_coords[str(row["callsign"] or "").upper().strip()] = (
                float(row["latitude"]),
                float(row["longitude"]),
            )

    issues: dict[str, dict[str, Any]] = {}
    for row in rows:
        call = str(row["callsign"] or "").upper().strip()
        lat, lon = row["latitude"], row["longitude"]
        if lat is None or lon is None:
            continue
        if not _valid_geo_position(lat, lon):
            issue = "zero_position" if (
                lat is not None and lon is not None
                and abs(float(lat)) <= POSITION_ZERO_EPSILON
                and abs(float(lon)) <= POSITION_ZERO_EPSILON
            ) else "invalid_position"
            issues[call] = {"issue_type": issue, "latitude": lat, "longitude": lon}
            continue

        relay = _rf_igate_from_path(row["path"])
        relay_coords = valid_coords.get(relay)
        if relay and relay_coords:
            distance = haversine_km(float(lat), float(lon), relay_coords[0], relay_coords[1])
            if distance > RF_POSITION_MAX_DISTANCE_KM:
                issues[call] = {
                    "issue_type": "rf_relay_distance",
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "relay": relay,
                    "relay_distance_km": round(distance, 1),
                }
    return issues


def _position_issue_label(issue_type: str) -> str:
    return {
        "zero_position": "Coordenadas 0,0",
        "invalid_position": "Coordenadas inválidas",
        "rf_relay_distance": "Posição incompatível com o iGate RF",
        "implied_speed": "Salto geográfico / velocidade implícita",
    }.get(str(issue_type or ""), "Posição suspeita")


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _position_is_plausible(
    callsign: str,
    current: sqlite3.Row | None,
    last_valid_track: sqlite3.Row | None,
    latitude: float,
    longitude: float,
    now: datetime,
) -> tuple[bool, dict[str, float | str | int | bool]]:
    reference = last_valid_track or current
    if reference is None or reference["latitude"] is None or reference["longitude"] is None:
        with _track_relocation_lock:
            _track_relocation_candidates.pop(callsign, None)
        return True, {"distance_km": 0.0, "speed_kmh": 0.0, "relocation": False}

    timestamp_key = "timestamp" if last_valid_track is not None else "last_heard"
    previous_time = _parse_timestamp(reference[timestamp_key])
    if previous_time is None:
        return True, {"distance_km": 0.0, "speed_kmh": 0.0, "relocation": False}

    distance = haversine_km(float(reference["latitude"]), float(reference["longitude"]), latitude, longitude)
    elapsed_hours = max((now - previous_time).total_seconds() / 3600.0, 1.0 / 3600.0)
    speed = distance / elapsed_hours

    # Long gaps are allowed: the station may genuinely have travelled or been moved.
    if elapsed_hours >= 6.0 or distance < TRACK_OUTLIER_MIN_KM or speed <= TRACK_OUTLIER_MAX_SPEED_KMH:
        with _track_relocation_lock:
            _track_relocation_candidates.pop(callsign, None)
        return True, {"distance_km": distance, "speed_kmh": speed, "relocation": False}

    with _track_relocation_lock:
        candidate = _track_relocation_candidates.get(callsign)
        if candidate is not None:
            cluster_distance = haversine_km(
                float(candidate["latitude"]), float(candidate["longitude"]), latitude, longitude
            )
        else:
            cluster_distance = float("inf")

        if candidate is not None and cluster_distance <= TRACK_RELOCATION_CLUSTER_KM:
            count = int(candidate.get("count") or 1) + 1
        else:
            count = 1

        _track_relocation_candidates[callsign] = {
            "latitude": latitude,
            "longitude": longitude,
            "count": count,
        }

        if count >= TRACK_RELOCATION_CONFIRMATIONS:
            _track_relocation_candidates.pop(callsign, None)
            diag.log_event(
                "track_position_relocation_confirmed",
                callsign=callsign,
                distance_km=round(distance, 2),
                elapsed_hours=round(elapsed_hours, 3),
                implied_speed_kmh=round(speed, 1),
                confirmations=count,
            )
            return True, {
                "distance_km": distance,
                "speed_kmh": speed,
                "relocation": True,
                "confirmations": count,
            }

    diag.log_event(
        "track_position_outlier_rejected",
        callsign=callsign,
        distance_km=round(distance, 2),
        elapsed_hours=round(elapsed_hours, 3),
        implied_speed_kmh=round(speed, 1),
        latitude=latitude,
        longitude=longitude,
        confirmations=count,
    )
    return False, {
        "distance_km": distance,
        "speed_kmh": speed,
        "relocation": False,
        "confirmations": count,
    }



def _record_packet_conn(conn: sqlite3.Connection, raw: str, from_call: str | None = None,
                        packet_format: str | None = None) -> None:
    conn.execute(
        "INSERT INTO packets(timestamp, from_call, packet_format, raw) VALUES (?, ?, ?, ?)",
        (utc_now_iso(), from_call, packet_format, raw),
    )
    if _retention_due("packets"):
        deleted = _trim_history_table(conn, "packets", PACKET_RETENTION)
        if deleted:
            diag.log_event("retention_sweep", table="packets", deleted=deleted)


def record_packet(raw: str, from_call: str | None = None, packet_format: str | None = None) -> None:
    with connection() as conn:
        _record_packet_conn(conn, raw, from_call, packet_format)


def _upsert_station_conn(conn: sqlite3.Connection, packet: dict[str, Any]) -> None:
    callsign = str(packet.get("from") or "").upper().strip()
    if not callsign:
        return
    now = utc_now_iso()
    fmt = str(packet.get("format") or "")
    name = callsign
    info = _extract_info(packet)
    is_object = fmt in {"object", "item"}
    path = json.dumps(packet.get("path") or [], ensure_ascii=False)

    current = conn.execute("SELECT * FROM stations WHERE callsign=?", (callsign,)).fetchone()
    previous = current
    last_valid_track = conn.execute(
        "SELECT timestamp,latitude,longitude FROM tracks WHERE callsign=? ORDER BY id DESC LIMIT 1",
        (callsign,),
    ).fetchone()
    packet_lat = packet.get("latitude")
    packet_lon = packet.get("longitude")
    position_valid = True
    relocation_confirmed = False

    # Object/item coordinates describe the advertised object, not necessarily the
    # transmitting station. They must never overwrite the sender's own position.
    if not is_object and (packet_lat is not None or packet_lon is not None):
        if not _valid_geo_position(packet_lat, packet_lon):
            position_valid = False
            issue_type = "zero_position" if (
                packet_lat is not None
                and packet_lon is not None
                and abs(float(packet_lat)) <= POSITION_ZERO_EPSILON
                and abs(float(packet_lon)) <= POSITION_ZERO_EPSILON
            ) else "invalid_position"
            _record_station_anomaly_conn(
                conn,
                callsign,
                issue_type,
                packet_lat,
                packet_lon,
                {"format": fmt, "path": packet.get("path") or []},
            )
            diag.log_event(
                "station_position_rejected",
                callsign=callsign,
                reason=issue_type,
                latitude=packet_lat,
                longitude=packet_lon,
            )
        else:
            lat = float(packet_lat)
            lon = float(packet_lon)
            relay_issue, relay_meta = _rf_relay_position_issue_conn(
                conn,
                packet.get("path") or [],
                lat,
                lon,
            )
            if relay_issue:
                position_valid = False
                _record_station_anomaly_conn(
                    conn,
                    callsign,
                    relay_issue,
                    lat,
                    lon,
                    {"format": fmt, **relay_meta},
                )
                diag.log_event(
                    "station_position_rejected",
                    callsign=callsign,
                    reason=relay_issue,
                    latitude=lat,
                    longitude=lon,
                    **relay_meta,
                )
            else:
                try:
                    position_valid, position_meta = _position_is_plausible(
                        callsign,
                        current,
                        last_valid_track,
                        lat,
                        lon,
                        datetime.now(timezone.utc),
                    )
                    relocation_confirmed = bool(position_meta.get("relocation"))
                    if not position_valid:
                        _record_station_anomaly_conn(
                            conn,
                            callsign,
                            "implied_speed",
                            lat,
                            lon,
                            {
                                "format": fmt,
                                "distance_km": round(float(position_meta.get("distance_km") or 0.0), 2),
                                "implied_speed_kmh": round(float(position_meta.get("speed_kmh") or 0.0), 1),
                                "confirmations": int(position_meta.get("confirmations") or 0),
                            },
                        )
                except Exception as exc:
                    diag.log_event("track_position_filter_error", callsign=callsign, error=str(exc))
                    position_valid = True

    def choose(key: str, fallback=None):
        value = None if is_object and key in {
            "latitude", "longitude", "speed", "course", "altitude", "symbol_table", "symbol"
        } else packet.get(key, None)
        if key in {"latitude", "longitude"} and not position_valid:
            value = None
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
    if (
        not is_object
        and position_valid
        and _valid_geo_position(lat, lon)
    ):
        should_add = True
        if (
            previous
            and _valid_geo_position(previous["latitude"], previous["longitude"])
        ):
            should_add = relocation_confirmed or haversine_km(
                float(previous["latitude"]), float(previous["longitude"]), float(lat), float(lon)
            ) >= 0.01
        if should_add or previous is None:
            conn.execute(
                "INSERT INTO tracks(callsign,timestamp,latitude,longitude,speed,course,altitude) VALUES(?,?,?,?,?,?,?)",
                (callsign, now, float(lat), float(lon), packet.get("speed"), packet.get("course"), packet.get("altitude")),
            )


def upsert_station(packet: dict[str, Any]) -> None:
    with connection() as conn:
        _upsert_station_conn(conn, packet)

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
            SELECT s.*, CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
            FROM stations s
            LEFT JOIN favorites f ON UPPER(f.callsign)=UPPER(s.callsign)
            WHERE UPPER(s.callsign) LIKE ? OR UPPER(COALESCE(s.name,'')) LIKE ? OR UPPER(COALESCE(s.info,'')) LIKE ?
            ORDER BY favorite DESC, s.last_heard DESC
            """,
            (q, q, q),
        ).fetchall()
        issues = _station_position_issues_conn(conn)
    result = []
    own_valid = _valid_geo_position(own_lat, own_lon)
    for row in rows:
        item = dict(row)
        call = str(item.get("callsign") or "").upper().strip()
        issue = issues.get(call)
        valid = _valid_geo_position(item.get("latitude"), item.get("longitude")) and issue is None
        item["position_valid"] = bool(valid)
        item["position_issue"] = str(issue.get("issue_type") or "") if issue else ""
        item["position_issue_label"] = _position_issue_label(item["position_issue"]) if issue else ""
        if own_valid and valid:
            item["distance_km"] = round(
                haversine_km(
                    float(own_lat),
                    float(own_lon),
                    float(item["latitude"]),
                    float(item["longitude"]),
                ),
                2,
            )
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


def _observed_topology_edges(raw: str) -> tuple[str, list[tuple[str, str, str, str | None]]]:
    """Retorna a origem e os enlaces observáveis no path APRS/TNC2."""
    line = str(raw or "").strip()
    if ">" not in line or ":" not in line:
        return "", []
    source = line.split(">", 1)[0].upper().strip()
    if not _is_topology_callsign(source):
        return "", []

    header = line.split(":", 1)[0]
    route = header.split(">", 1)[1].split(",")
    if len(route) < 2:
        return source, []

    # Preserve q-construct case. In APRS-IS, qAR and qAr are distinct:
    # qAR is a direct RF gate, while qAr is a remote IGate reached through APRS-IS.
    path = [part.strip() for part in route[1:] if part.strip()]
    edges: list[tuple[str, str, str, str | None]] = []
    previous = source

    for token in path:
        if re.fullmatch(r"qA[A-Za-z]", token):
            break
        if not token.endswith("*"):
            continue
        node = token.rstrip("*").upper()
        if _is_topology_callsign(node) and node != previous:
            edges.append((previous, node, "rf", None))
            previous = node

    for i, token in enumerate(path):
        if not re.fullmatch(r"qA[A-Za-z]", token) or i + 1 >= len(path):
            continue
        candidate = path[i + 1].rstrip("*").upper()
        if not _is_topology_callsign(candidate) or candidate == previous:
            break

        prior = {item.rstrip("*").upper() for item in path[:i]}
        direct_rf_gate = token in {"qAR", "qAO"} and not (prior & {"TCPIP", "TCPXX"})
        kind = "rf" if direct_rf_gate else "igate"
        edges.append((previous, candidate, kind, candidate))
        break
    return source, edges



def _record_topology_from_raw_conn(conn: sqlite3.Connection, raw: str) -> None:
    """Registra relações observáveis usando a transação já aberta."""
    _source, edges = _observed_topology_edges(raw)
    if not edges:
        return
    now = utc_now_iso()

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
        conn.execute(
            "INSERT INTO topology_events(timestamp,source,target,kind) VALUES(?,?,?,?)",
            (now, edge_source, target, kind),
        )
    if _retention_due("topology_events", len(edges)):
        deleted = _trim_history_table(conn, "topology_events", TOPOLOGY_EVENT_RETENTION)
        if deleted:
            diag.log_event("retention_sweep", table="topology_events", deleted=deleted)


def record_topology_from_raw(raw: str) -> None:
    """Registra somente relações observáveis no path APRS/TNC2."""
    with connection() as conn:
        _record_topology_from_raw_conn(conn, raw)

def list_topology_edges(hours: int = 0) -> list[dict[str, Any]]:
    """Retorna enlaces observados sem permitir que uma consulta monopolize workers HTTP."""
    hours = int(hours or 0)
    if hours > 0:
        hours = max(1, min(hours, 24 * 30))
    else:
        hours = 0

    now = time.monotonic()
    with _topology_cache_lock:
        cached = _topology_cache.get(hours)
        if cached and now - cached[0] <= TOPOLOGY_CACHE_SECONDS:
            return [dict(item) for item in cached[1]]
        stale = [dict(item) for item in cached[1]] if cached else []

    # Nunca deixa várias threads do Waitress executarem a mesma consulta pesada.
    if not _topology_query_lock.acquire(blocking=False):
        diag.log_event("topology_query_coalesced", hours=hours, cached=bool(stale))
        return stale

    try:
        # Outro request pode ter preenchido o cache enquanto aguardávamos o lock.
        now = time.monotonic()
        with _topology_cache_lock:
            cached = _topology_cache.get(hours)
            if cached and now - cached[0] <= TOPOLOGY_CACHE_SECONDS:
                return [dict(item) for item in cached[1]]
            stale = [dict(item) for item in cached[1]] if cached else stale

        params: list[Any] = []
        where = ""
        if hours > 0:
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
            where = "AND e.last_seen >= ?"
            params.append(cutoff)

        started = time.monotonic()
        deadline = started + TOPOLOGY_QUERY_MAX_SECONDS
        rows: list[sqlite3.Row] = []
        interrupted = False

        with connection() as conn:
            # Proteção adicional: mesmo um plano ruim/DB legado nunca fica minutos
            # segurando uma thread do servidor.
            conn.set_progress_handler(
                lambda: 1 if time.monotonic() >= deadline else 0,
                20_000,
            )
            try:
                rows = conn.execute(
                    f"""
                    SELECT e.source,e.target,e.kind,e.packet_count,e.first_seen,e.last_seen,e.igate,
                           s1.latitude AS source_lat,s1.longitude AS source_lon,
                           s2.latitude AS target_lat,s2.longitude AS target_lon
                    FROM topology_edges e
                    JOIN stations s1 ON s1.callsign = e.source
                    JOIN stations s2 ON s2.callsign = e.target
                    WHERE s1.latitude IS NOT NULL AND s1.longitude IS NOT NULL
                      AND s2.latitude IS NOT NULL AND s2.longitude IS NOT NULL
                      {where}
                    ORDER BY e.packet_count DESC, e.last_seen DESC
                    LIMIT 5000
                    """,
                    params,
                ).fetchall()
            except sqlite3.OperationalError as exc:
                if "interrupted" in str(exc).lower():
                    interrupted = True
                    diag.log_event(
                        "topology_query_timeout",
                        hours=hours,
                        duration_ms=round((time.monotonic() - started) * 1000, 1),
                    )
                else:
                    raise
            finally:
                conn.set_progress_handler(None, 0)
            issues = _station_position_issues_conn(conn)

        if interrupted:
            return stale

        result = []
        for row in rows:
            item = dict(row)
            source = str(item.get("source") or "").upper().strip()
            target = str(item.get("target") or "").upper().strip()
            if source in issues or target in issues:
                continue
            if not _valid_geo_position(item.get("source_lat"), item.get("source_lon")):
                continue
            if not _valid_geo_position(item.get("target_lat"), item.get("target_lon")):
                continue
            result.append(item)
        with _topology_cache_lock:
            _topology_cache[hours] = (time.monotonic(), result)

        elapsed_ms = (time.monotonic() - started) * 1000
        if elapsed_ms >= 250:
            diag.log_event("topology_query_slow", hours=hours, duration_ms=round(elapsed_ms, 1), rows=len(result))
        return [dict(item) for item in result]
    finally:
        _topology_query_lock.release()


def _aprs_tocall_from_raw(raw: str) -> str:
    """Extrai o destination/TOCALL do cabeçalho TNC2."""
    match = re.match(r"^[^>\r\n]+>([^,:>\r\n]+)", str(raw or "").strip())
    return str(match.group(1) if match else "").upper().strip()


def _load_aprs_device_ids() -> list[dict[str, Any]]:
    global _aprs_device_id_entries
    if _aprs_device_id_entries is not None:
        return _aprs_device_id_entries
    with _aprs_device_id_lock:
        if _aprs_device_id_entries is not None:
            return _aprs_device_id_entries
        try:
            payload = json.loads(APRS_DEVICE_ID_PATH.read_text(encoding="utf-8"))
            entries = payload.get("entries", []) if isinstance(payload, dict) else []
            _aprs_device_id_entries = [dict(item) for item in entries if isinstance(item, dict) and item.get("tocall")]
        except Exception as exc:
            diag.log_event("aprs_device_id_load_failed", error=str(exc))
            _aprs_device_id_entries = []
    return _aprs_device_id_entries


def _tocall_pattern_regex(pattern: str) -> str:
    out: list[str] = []
    for char in str(pattern or ""):
        if char == "?":
            out.append(".")
        elif char == "*":
            out.append(".*")
        elif char == "n":
            out.append("[0-9]")
        else:
            out.append(re.escape(char.upper()))
    return "^" + "".join(out) + "$"


def resolve_aprs_device_id(tocall: str) -> dict[str, Any]:
    """Resolve TOCALL pelo snapshot oficial aprs-deviceid, preferindo padrões específicos."""
    code = str(tocall or "").upper().strip()
    if not code:
        return {"identifier": "", "friendly_name": "Não identificado", "identified": False}

    best: dict[str, Any] | None = None
    best_score: tuple[int, int, int] = (-1, -1, -999)
    for item in _load_aprs_device_ids():
        raw_pattern = str(item.get("tocall") or "").strip()
        pattern = raw_pattern.upper()
        if not raw_pattern:
            continue
        try:
            if not re.fullmatch(_tocall_pattern_regex(raw_pattern), code):
                continue
        except re.error:
            continue
        wildcard_count = raw_pattern.count("?") + raw_pattern.count("*") + raw_pattern.count("n")
        literal_count = len(raw_pattern) - wildcard_count
        exact = 1 if wildcard_count == 0 and pattern == code else 0
        score = (exact, literal_count, -wildcard_count)
        if score > best_score:
            best = item
            best_score = score

    if not best:
        return {
            "identifier": code,
            "friendly_name": "Não identificado",
            "identified": False,
            "vendor": "",
            "model": "",
            "class": "",
            "os": "",
            "pattern": "",
        }

    model = str(best.get("model") or "").strip()
    vendor = str(best.get("vendor") or "").strip()
    pattern = str(best.get("tocall") or "").upper().strip()
    friendly = model or vendor or ("Experimental" if pattern.startswith("APZ") else "Não identificado")

    # Dire Wolf codifica a versão nos dois dígitos finais de APDWxx.
    if model.lower() == "direwolf" and re.fullmatch(r"APDW[0-9]{2}", code):
        suffix = code[-2:]
        friendly = f"Dire Wolf {suffix[0]}.{suffix[1]}"
    elif model.lower() == "direwolf":
        friendly = "Dire Wolf"

    if pattern.startswith("APZ") and not bool(best.get("local_override")) and not model and not vendor:
        friendly = "Experimental"

    return {
        "identifier": code,
        "friendly_name": friendly,
        "identified": friendly not in {"Não identificado", ""},
        "vendor": vendor,
        "model": model,
        "class": str(best.get("class") or ""),
        "os": str(best.get("os") or ""),
        "pattern": pattern,
        "local_override": bool(best.get("local_override")),
    }


APRS_CLIENT_CANONICAL_NAMES = {
    "aprsdroid": "APRSdroid",
    "brandmeister dmr": "BrandMeister DMR",
    "dire wolf": "Dire Wolf",
    "direwolf": "Dire Wolf",
    "esp32idf aprs": "esp32idf_APRS",
    "ircddb gateway": "ircDDB Gateway",
    "svxlink": "SvxLink",
    "tinytrak": "TinyTrak",
    "ui view32": "UI-View32",
    "uiview32": "UI-View32",
    "vp digi": "VP-Digi",
    "vpdigi": "VP-Digi",
}


def _canonical_client_family(value: str) -> tuple[str, str]:
    """Retorna (chave, nome) consolidando aliases e versões do mesmo cliente."""
    original = re.sub(r"\s+", " ", str(value or "").strip())
    if not original:
        return "", ""

    # O ranking é de clientes/produtos, não de builds. Mantém a versão
    # disponível em aliases, mas agrupa sufixos semânticos como 1.8 / v1.9.2.
    family = re.sub(
        r"\s+(?:v(?:ersion)?\s*)?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.-]+)?$",
        "",
        original,
        flags=re.IGNORECASE,
    ).strip() or original

    key = re.sub(r"[^0-9a-z]+", " ", family.casefold()).strip()
    display = APRS_CLIENT_CANONICAL_NAMES.get(key, family)
    display_key = re.sub(r"[^0-9a-z]+", " ", display.casefold()).strip()
    return display_key, display


def client_version_stats(hours: int = 0) -> dict[str, Any]:
    """Distribuição de software/dispositivo APRS consolidada por família de cliente."""
    hours = int(hours or 0)
    params: list[Any] = []
    where = ""
    if hours > 0:
        hours = max(1, min(hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        where = "WHERE last_heard >= ?"
        params.append(cutoff)

    with connection() as conn:
        rows = conn.execute(
            f"SELECT callsign, raw FROM stations {where} ORDER BY last_heard DESC",
            params,
        ).fetchall()

    grouped: dict[str, dict[str, Any]] = {}
    unidentified = 0

    for row in rows:
        tocall = _aprs_tocall_from_raw(row["raw"])
        if not tocall or tocall == "APRS":
            unidentified += 1
            continue

        resolved = resolve_aprs_device_id(tocall)
        if not resolved.get("identified"):
            unidentified += 1
            continue

        source_name = re.sub(
            r"\s+", " ", str(resolved.get("friendly_name") or tocall).strip()
        )
        friendly_key, friendly_name = _canonical_client_family(source_name)
        if not friendly_key:
            unidentified += 1
            continue

        bucket = grouped.get(friendly_key)
        if bucket is None:
            bucket = {
                "friendly_name": friendly_name,
                "stations": 0,
                "identifiers": set(),
                "aliases": set(),
                "meta": resolved,
                "is_own_client": False,
            }
            grouped[friendly_key] = bucket

        bucket["stations"] = int(bucket["stations"]) + 1
        bucket["identifiers"].add(tocall)
        bucket["aliases"].add(source_name)
        if tocall == APP_TOCALL:
            # Quando o próprio cliente fizer parte de um grupo consolidado,
            # seus metadados passam a ser a referência visual desse grupo.
            bucket["meta"] = resolved
            bucket["is_own_client"] = True

    identified_total = sum(int(bucket["stations"]) for bucket in grouped.values())
    ranked = sorted(
        grouped.values(),
        key=lambda bucket: (-int(bucket["stations"]), str(bucket["friendly_name"]).casefold()),
    )

    items: list[dict[str, Any]] = []
    for rank, bucket in enumerate(ranked, start=1):
        identifiers = sorted(str(value) for value in bucket["identifiers"])
        is_own = bool(bucket["is_own_client"]) or APP_TOCALL in identifiers
        identifier = APP_TOCALL if is_own and APP_TOCALL in identifiers else identifiers[0]
        meta = dict(bucket["meta"] or {})
        count = int(bucket["stations"])
        items.append({
            "rank": rank,
            "identifier": identifier,
            "identifiers": identifiers,
            "aliases": sorted(str(value) for value in bucket["aliases"]),
            "friendly_name": bucket["friendly_name"],
            "vendor": meta.get("vendor") or "",
            "model": meta.get("model") or "",
            "class": meta.get("class") or "",
            "os": meta.get("os") or "",
            "stations": count,
            "percent": round((count / identified_total) * 100.0, 1) if identified_total else 0.0,
            "is_own_client": is_own,
        })

    own_client = next((dict(item) for item in items if item["is_own_client"]), None)
    if own_client is None:
        own_meta = resolve_aprs_device_id(APP_TOCALL)
        own_client = {
            "rank": None,
            "identifier": APP_TOCALL,
            "identifiers": [APP_TOCALL],
            "aliases": [own_meta.get("friendly_name") or "PT2VHF APRS Client"],
            "friendly_name": own_meta.get("friendly_name") or "PT2VHF APRS Client",
            "vendor": own_meta.get("vendor") or "PT2VHF",
            "model": own_meta.get("model") or "PT2VHF APRS Client",
            "class": own_meta.get("class") or "software",
            "os": own_meta.get("os") or "",
            "stations": 0,
            "percent": 0.0,
            "is_own_client": True,
        }

    return {
        "hours": 0 if hours <= 0 else hours,
        "total_stations": len(rows),
        "identified_stations": identified_total,
        "unidentified_stations": unidentified,
        "top_limit": 20,
        "own_identifier": APP_TOCALL,
        "own_client": own_client,
        "items": items,
        "device_id_source": "aprsorg/aprs-deviceid (CC BY-SA 2.0)",
    }

def station_problem_stats(hours: int = 0, limit: int = 20) -> list[dict[str, Any]]:
    hours = int(hours or 0)
    params: list[Any] = []
    where = ""
    if hours > 0:
        hours = max(1, min(hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        where = "WHERE timestamp >= ?"
        params.append(cutoff)

    combined: dict[tuple[str, str], dict[str, Any]] = {}
    with connection() as conn:
        rows = conn.execute(
            f"""
            SELECT UPPER(TRIM(callsign)) AS callsign,
                   issue_type,
                   COUNT(*) AS occurrences,
                   MAX(timestamp) AS last_occurrence
            FROM station_anomalies
            {where}
            GROUP BY UPPER(TRIM(callsign)), issue_type
            """,
            params,
        ).fetchall()
        for row in rows:
            call = str(row["callsign"] or "").upper().strip()
            issue_type = str(row["issue_type"] or "")
            combined[(call, issue_type)] = {
                "callsign": call,
                "issue_type": issue_type,
                "problem": _position_issue_label(issue_type),
                "occurrences": int(row["occurrences"] or 0),
                "last_occurrence": row["last_occurrence"],
            }

        # Também detecta problemas legados já armazenados antes da tabela de
        # anomalias, inclusive posições 0,0 e posições incompatíveis com qAR/qAO.
        dynamic_issues = _station_position_issues_conn(conn)
        last_seen_rows = {
            str(r["callsign"] or "").upper().strip(): r["last_heard"]
            for r in conn.execute("SELECT callsign,last_heard FROM stations").fetchall()
        }
        for call, issue in dynamic_issues.items():
            issue_type = str(issue.get("issue_type") or "invalid_position")
            key = (call, issue_type)
            existing = combined.get(key)
            if existing:
                existing["occurrences"] = max(1, int(existing["occurrences"]))
            else:
                combined[key] = {
                    "callsign": call,
                    "issue_type": issue_type,
                    "problem": _position_issue_label(issue_type),
                    "occurrences": 1,
                    "last_occurrence": last_seen_rows.get(call),
                }
            combined[key]["details"] = {
                key: value
                for key, value in issue.items()
                if key not in {"issue_type"}
            }

    items = list(combined.values())
    for item in items:
        count = int(item.get("occurrences") or 0)
        item["recurrence"] = "alta" if count >= 5 else ("média" if count >= 2 else "baixa")
    items.sort(
        key=lambda item: (
            -int(item.get("occurrences") or 0),
            str(item.get("last_occurrence") or ""),
            str(item.get("callsign") or ""),
        )
    )
    return items[: max(1, min(int(limit or 20), 100))]


def network_improvement_suggestions(hours: int = 0, limit: int = 12) -> list[dict[str, Any]]:
    hours = int(hours or 0)
    cutoff: str | None = None
    if hours > 0:
        hours = max(1, min(hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")

    suggestions: list[dict[str, Any]] = []
    with connection() as conn:
        issues = _station_position_issues_conn(conn)
        position_rows = conn.execute(
            "SELECT callsign,latitude,longitude,last_heard FROM stations"
        ).fetchall()
        valid_positions = {
            str(row["callsign"] or "").upper().strip(): (
                float(row["latitude"]),
                float(row["longitude"]),
            )
            for row in position_rows
            if str(row["callsign"] or "").upper().strip() not in issues
            and _valid_geo_position(row["latitude"], row["longitude"])
        }

        packet_where = "WHERE from_call IS NOT NULL AND TRIM(from_call) <> ''"
        packet_params: list[Any] = []
        if cutoff:
            packet_where += " AND timestamp >= ?"
            packet_params.append(cutoff)
        packet_counts = {
            str(row["callsign"] or "").upper().strip(): int(row["packets"] or 0)
            for row in conn.execute(
                f"""
                SELECT UPPER(TRIM(from_call)) AS callsign, COUNT(*) AS packets
                FROM packets
                {packet_where}
                GROUP BY UPPER(TRIM(from_call))
                """,
                packet_params,
            ).fetchall()
        }

        edge_where = ""
        edge_params: list[Any] = []
        if cutoff:
            edge_where = "WHERE last_seen >= ?"
            edge_params.append(cutoff)
        degree: dict[str, set[str]] = {}
        for row in conn.execute(
            f"SELECT source,target FROM topology_edges {edge_where}",
            edge_params,
        ).fetchall():
            a = str(row["source"] or "").upper().strip()
            b = str(row["target"] or "").upper().strip()
            if not a or not b:
                continue
            degree.setdefault(a, set()).add(b)
            degree.setdefault(b, set()).add(a)

        isolated = []
        for call, packet_count in packet_counts.items():
            if call not in valid_positions or packet_count < 5:
                continue
            neighbors = len(degree.get(call, set()))
            if neighbors <= 1:
                isolated.append((packet_count, neighbors, call))
        isolated.sort(reverse=True)
        for packet_count, neighbors, call in isolated[:5]:
            lat, lon = valid_positions[call]
            suggestions.append({
                "type": "isolated_station",
                "title": "Estação com pouca redundância",
                "callsign": call,
                "detail": f"{packet_count} pacotes no período e {neighbors} enlace(s) distinto(s) observado(s).",
                "evidence": "alta" if packet_count >= 25 else "média",
                "latitude": lat,
                "longitude": lon,
            })

        igate_rows = conn.execute(
            f"""
            SELECT UPPER(TRIM(igate)) AS callsign, SUM(packet_count) AS packets
            FROM topology_edges
            WHERE igate IS NOT NULL
            {"AND last_seen >= ?" if cutoff else ""}
            GROUP BY UPPER(TRIM(igate))
            ORDER BY packets DESC
            """,
            ([cutoff] if cutoff else []),
        ).fetchall()
        igate_total = sum(int(row["packets"] or 0) for row in igate_rows)
        if igate_rows and igate_total >= 20:
            top = igate_rows[0]
            top_packets = int(top["packets"] or 0)
            share = top_packets / igate_total if igate_total else 0.0
            if share >= 0.60:
                suggestions.append({
                    "type": "igate_concentration",
                    "title": "Dependência elevada de um único iGate",
                    "callsign": str(top["callsign"] or "").upper().strip(),
                    "detail": f"{share * 100.0:.1f}% do tráfego encaminhado por iGate no período passou por esta estação.",
                    "evidence": "alta" if share >= 0.80 else "média",
                })

        # Heurística deliberadamente conservadora: um grande intervalo entre
        # posições sucessivas de uma estação móvel é apenas uma possível sombra.
        track_where = ""
        track_params: list[Any] = []
        if cutoff:
            track_where = "WHERE timestamp >= ?"
            track_params.append(cutoff)
        track_rows = conn.execute(
            f"""
            SELECT callsign,timestamp,latitude,longitude
            FROM tracks
            {track_where}
            ORDER BY callsign, timestamp
            LIMIT 30000
            """,
            track_params,
        ).fetchall()
        previous_by_call: dict[str, sqlite3.Row] = {}
        gaps: list[tuple[float, str, dict[str, Any]]] = []
        for row in track_rows:
            call = str(row["callsign"] or "").upper().strip()
            if call in issues or not _valid_geo_position(row["latitude"], row["longitude"]):
                continue
            previous = previous_by_call.get(call)
            previous_by_call[call] = row
            if previous is None:
                continue
            t1 = _parse_timestamp(previous["timestamp"])
            t2 = _parse_timestamp(row["timestamp"])
            if not t1 or not t2:
                continue
            elapsed_minutes = (t2 - t1).total_seconds() / 60.0
            if elapsed_minutes < 30.0 or elapsed_minutes > 360.0:
                continue
            distance = haversine_km(
                float(previous["latitude"]),
                float(previous["longitude"]),
                float(row["latitude"]),
                float(row["longitude"]),
            )
            if distance < 10.0 or distance > 300.0:
                continue
            gaps.append((distance, call, {
                "type": "possible_coverage_gap",
                "title": "Possível trecho de baixa cobertura",
                "callsign": call,
                "detail": f"Intervalo de {elapsed_minutes:.0f} min entre posições separadas por {distance:.1f} km; requer validação antes de concluir que há sombra RF.",
                "evidence": "baixa",
                "latitude": (float(previous["latitude"]) + float(row["latitude"])) / 2.0,
                "longitude": (float(previous["longitude"]) + float(row["longitude"])) / 2.0,
            }))
        gaps.sort(key=lambda value: value[0], reverse=True)
        suggestions.extend(item for _distance, _call, item in gaps[:4])

    return suggestions[: max(1, min(int(limit or 12), 50))]


def manual_conversation_stats(hours: int = 0, limit: int = 20) -> list[dict[str, Any]]:
    """Rank stations by human APRS message interactions, excluding automated traffic."""
    hours = int(hours or 0)
    params: list[Any] = []
    where = [
        "message_type='message'",
        "COALESCE(retry_count,0)=0",
        "TRIM(COALESCE(message,'')) <> ''",
    ]
    if hours > 0:
        hours = max(1, min(hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        where.append("timestamp >= ?")
        params.append(cutoff)

    cfg = get_config()
    own_base = str(cfg.get("callsign") or "").upper().strip()
    own_ssid = str(cfg.get("ssid") or "").strip()
    own_call = own_base
    if own_base and own_ssid and own_ssid not in {"0", "None", "none"}:
        own_call = f"{own_base}-{own_ssid}"

    callsign_re = re.compile(r"^[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?$")
    reserved_targets = {
        "CQ", "ALL", "APRS", "BEACON", "BLN", "NWS", "SKY", "WX",
    }
    auto_patterns = (
        re.compile(r"^\s*\?", re.IGNORECASE),
        re.compile(r"^\s*(?:ACK|REJ)[A-Z0-9]{1,5}\s*$", re.IGNORECASE),
        re.compile(r"^\s*DIRECTS=", re.IGNORECASE),
        re.compile(r"(?:^|\s)[A-Z0-9-]*_?HEARD:", re.IGNORECASE),
        re.compile(r"^\s*[A-Z0-9-]+>[^:]+:\s*$", re.IGNORECASE),
    )

    with connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id,direction,from_call,to_call,message,msg_id,message_group_id,
                   part_index,part_count,retry_count,timestamp
            FROM messages
            WHERE {" AND ".join(where)}
            ORDER BY timestamp ASC, id ASC
            """,
            params,
        ).fetchall()

    counts: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for row in rows:
        source = str(row["from_call"] or "").upper().strip()
        target = str(row["to_call"] or "").upper().strip()
        message = str(row["message"] or "").strip()
        if not callsign_re.fullmatch(source) or not callsign_re.fullmatch(target):
            continue
        if target in reserved_targets or source in reserved_targets:
            continue
        if any(pattern.search(message) for pattern in auto_patterns):
            continue

        group_id = str(row["message_group_id"] or "").strip()
        msg_id = str(row["msg_id"] or "").strip()
        direction = str(row["direction"] or "").lower().strip()
        if group_id:
            unique_key = f"group:{direction}:{source}:{target}:{group_id}"
        elif msg_id:
            unique_key = f"msg:{direction}:{source}:{target}:{msg_id}"
        else:
            unique_key = (
                f"text:{direction}:{source}:{target}:"
                f"{message.casefold()}:{str(row['timestamp'] or '')}"
            )
        if unique_key in seen:
            continue
        seen.add(unique_key)

        for call, sent_delta, recv_delta, peer in (
            (source, 1, 0, target),
            (target, 0, 1, source),
        ):
            if own_call and call == own_call:
                continue
            item = counts.setdefault(call, {
                "callsign": call,
                "interactions": 0,
                "sent": 0,
                "received": 0,
                "peers": set(),
            })
            item["interactions"] += 1
            item["sent"] += sent_delta
            item["received"] += recv_delta
            item["peers"].add(peer)

    total_participations = sum(int(item["interactions"]) for item in counts.values())
    result: list[dict[str, Any]] = []
    for item in counts.values():
        interactions = int(item["interactions"])
        result.append({
            "callsign": item["callsign"],
            "interactions": interactions,
            "sent": int(item["sent"]),
            "received": int(item["received"]),
            "peers": len(item["peers"]),
            "percent": round(interactions * 100.0 / total_participations, 1) if total_participations else 0.0,
        })
    result.sort(key=lambda item: (-int(item["interactions"]), str(item["callsign"])))
    for index, item in enumerate(result[: max(1, min(int(limit or 20), 100))], start=1):
        item["rank"] = index
    return result[: max(1, min(int(limit or 20), 100))]


def topology_stats(hours: int = 0) -> dict[str, Any]:
    """Resumo agregado da topologia observada para diagnóstico rápido."""
    hours = int(hours or 0)
    complete = hours <= 0
    params: list[Any] = []
    time_filter = ""
    cutoff: str | None = None
    if not complete:
        hours = max(1, min(hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        time_filter = "AND last_seen >= ?"
        params = [cutoff]
    stale_threshold = (datetime.now(timezone.utc) - timedelta(hours=(24 if complete else hours))).isoformat(timespec="seconds")
    with connection() as conn:
        digis = [dict(r) for r in conn.execute(
            f"""
            SELECT target AS callsign, SUM(packet_count) AS packets, MAX(last_seen) AS last_seen
            FROM topology_edges
            WHERE kind='rf' AND igate IS NULL {time_filter}
            GROUP BY target ORDER BY packets DESC, callsign LIMIT 20
            """, params
        ).fetchall()]
        igates = [dict(r) for r in conn.execute(
            f"""
            SELECT igate AS callsign, SUM(packet_count) AS packets, MAX(last_seen) AS last_seen
            FROM topology_edges
            WHERE igate IS NOT NULL {time_filter}
            GROUP BY igate ORDER BY packets DESC, callsign LIMIT 20
            """, params
        ).fetchall()]

        # Exclui qualquer indicativo já observado como infraestrutura, mesmo que
        # a função de digi/IGate não tenha aparecido novamente no período atual.
        infrastructure_rows = conn.execute(
            """
            SELECT DISTINCT callsign
            FROM (
                SELECT UPPER(TRIM(target)) AS callsign
                FROM topology_edges
                WHERE kind='rf' AND igate IS NULL
                UNION
                SELECT UPPER(TRIM(igate)) AS callsign
                FROM topology_edges
                WHERE igate IS NOT NULL
            )
            WHERE callsign IS NOT NULL AND callsign <> ''
            """
        ).fetchall()
        excluded_calls = sorted({str(r["callsign"] or "").upper().strip() for r in infrastructure_rows if r["callsign"]})

        active_clauses = [
            "p.from_call IS NOT NULL",
            "TRIM(p.from_call) <> ''",
            "LOWER(COALESCE(p.packet_format,'')) NOT LIKE 'telemetry%'",
        ]
        active_params: list[Any] = []
        if cutoff:
            active_clauses.append("p.timestamp >= ?")
            active_params.append(cutoff)
        if excluded_calls:
            placeholders = ",".join("?" for _ in excluded_calls)
            active_clauses.append(f"UPPER(TRIM(p.from_call)) NOT IN ({placeholders})")
            active_params.extend(excluded_calls)

        active_rows = conn.execute(
            f"""
            SELECT UPPER(TRIM(p.from_call)) AS callsign,
                   COUNT(*) AS packets,
                   MAX(p.timestamp) AS last_seen
            FROM packets p
            WHERE {" AND ".join(active_clauses)}
            GROUP BY UPPER(TRIM(p.from_call))
            ORDER BY packets DESC, callsign
            """,
            active_params,
        ).fetchall()
        eligible_packets = sum(int(r["packets"] or 0) for r in active_rows)
        active_stations = []
        for rank, row in enumerate(active_rows[:20], start=1):
            packet_count = int(row["packets"] or 0)
            active_stations.append({
                "rank": rank,
                "callsign": row["callsign"],
                "packets": packet_count,
                "percent": round((packet_count * 100.0 / eligible_packets), 1) if eligible_packets else 0.0,
                "last_seen": row["last_seen"],
            })

        stale = [dict(r) for r in conn.execute(
            """
            SELECT source,target,kind,packet_count,last_seen
            FROM topology_edges
            WHERE last_seen < ?
            ORDER BY last_seen DESC LIMIT 50
            """, (stale_threshold,)
        ).fetchall()]
        totals = conn.execute(
            f"SELECT COUNT(*) AS edges, COALESCE(SUM(packet_count),0) AS packets FROM topology_edges WHERE 1=1 {time_filter}",
            params,
        ).fetchone()
    return {
        "hours": 0 if complete else hours,
        "complete": complete,
        "edges": int(totals["edges"] or 0),
        "packets": int(totals["packets"] or 0),
        "active_stations": active_stations,
        "active_station_packets": eligible_packets,
        "manual_conversations": manual_conversation_stats(0 if complete else hours),
        "digipeaters": digis,
        "igates": igates,
        "recently_disappeared": stale,
        "problem_stations": station_problem_stats(0 if complete else hours),
        "improvement_suggestions": network_improvement_suggestions(0 if complete else hours),
        "client_versions": client_version_stats(0 if complete else hours),
    }


def topology_timeline(hours: int = 0, limit: int = 2500) -> list[dict[str, Any]]:
    hours = int(hours or 0)
    limit = max(100, min(int(limit or 2500), 20000))
    params: list[Any] = []
    where = ""
    if hours > 0:
        hours = max(1, min(hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        where = "AND e.timestamp >= ?"
        params.append(cutoff)
    params.append(limit)
    with connection() as conn:
        rows = conn.execute(
            f"""
            SELECT e.timestamp,e.source,e.target,e.kind,
                   s1.latitude AS source_lat,s1.longitude AS source_lon,
                   s2.latitude AS target_lat,s2.longitude AS target_lon
            FROM topology_events e
            JOIN stations s1 ON s1.callsign = e.source
            JOIN stations s2 ON s2.callsign = e.target
            WHERE s1.latitude IS NOT NULL AND s1.longitude IS NOT NULL
              AND s2.latitude IS NOT NULL AND s2.longitude IS NOT NULL
              {where}
            ORDER BY e.timestamp ASC, e.id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def topology_period_comparison(hours: int = 0) -> dict[str, Any]:
    hours = int(hours or 0)
    with connection() as conn:
        if hours <= 0:
            total = int(conn.execute("SELECT COUNT(*) FROM topology_events").fetchone()[0])
            return {
                "hours": 0,
                "complete": True,
                "current_events": total,
                "previous_events": 0,
                "delta": 0,
                "percent": None,
            }

        hours = max(1, min(hours, 24 * 30))
        now = datetime.now(timezone.utc)
        current_start = (now - timedelta(hours=hours)).isoformat(timespec="seconds")
        previous_start = (now - timedelta(hours=hours * 2)).isoformat(timespec="seconds")
        now_iso = now.isoformat(timespec="seconds")
        current = int(conn.execute(
            "SELECT COUNT(*) FROM topology_events WHERE timestamp >= ? AND timestamp <= ?",
            (current_start, now_iso),
        ).fetchone()[0])
        previous = int(conn.execute(
            "SELECT COUNT(*) FROM topology_events WHERE timestamp >= ? AND timestamp < ?",
            (previous_start, current_start),
        ).fetchone()[0])
    delta = current - previous
    pct = None if previous == 0 else round((delta / previous) * 100.0, 1)
    return {"hours": hours, "complete": False, "current_events": current, "previous_events": previous, "delta": delta, "percent": pct}


def latest_packet_id() -> int:
    with connection() as conn:
        row = conn.execute("SELECT COALESCE(MAX(id),0) FROM packets").fetchone()
    return int(row[0] or 0)


def packet_traffic_overview(
    hours: int = 0,
    bins: int = 120,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """Faixa temporal e densidade agregada para a timeline do Replay da Rede."""
    hours = int(hours or 0)
    bins = max(20, min(int(bins or 120), 240))
    clauses: list[str] = []
    params: list[Any] = []

    if start:
        clauses.append("timestamp >= ?")
        params.append(str(start))
    if end:
        clauses.append("timestamp <= ?")
        params.append(str(end))
    if not start and hours > 0:
        hours = max(1, min(hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        clauses.append("timestamp >= ?")
        params.append(cutoff)

    where = "WHERE " + " AND ".join(clauses) if clauses else ""

    with connection() as conn:
        row = conn.execute(
            f"SELECT MIN(timestamp) AS first_ts, MAX(timestamp) AS last_ts, COUNT(*) AS total FROM packets {where}",
            params,
        ).fetchone()
        first_ts = row["first_ts"] if row else None
        last_ts = row["last_ts"] if row else None
        total = int(row["total"] or 0) if row else 0
        density = [0 for _ in range(bins)]

        if first_ts and last_ts and total:
            try:
                first_dt = datetime.fromisoformat(str(first_ts).replace("Z", "+00:00"))
                last_dt = datetime.fromisoformat(str(last_ts).replace("Z", "+00:00"))
                first_epoch = int(first_dt.timestamp())
                last_epoch = int(last_dt.timestamp())
                span = max(1, last_epoch - first_epoch + 1)
                bucket_seconds = max(1.0, span / bins)
                rows = conn.execute(
                    f"""
                    SELECT CAST((CAST(strftime('%s', timestamp) AS INTEGER) - ?) / ? AS INTEGER) AS bucket,
                           COUNT(*) AS packet_count
                    FROM packets
                    {where}
                    GROUP BY bucket
                    """,
                    [first_epoch, bucket_seconds, *params],
                ).fetchall()
                for item in rows:
                    bucket = int(item["bucket"] or 0)
                    if 0 <= bucket < bins:
                        density[bucket] += int(item["packet_count"] or 0)
                    elif bucket >= bins:
                        density[-1] += int(item["packet_count"] or 0)
            except Exception:
                # A timeline continua utilizável mesmo se uma versão antiga do
                # SQLite não interpretar algum formato ISO no strftime().
                density = [0 for _ in range(bins)]

    return {
        "hours": hours if hours > 0 and not start else 0,
        "requested_start": start,
        "requested_end": end,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "total": total,
        "bins": density,
    }



def packet_traffic_events(
    after_id: int = 0,
    hours: int = 0,
    limit: int = 1000,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    """Pacotes APRS com segmentos observáveis e coordenadas conhecidas para animação."""
    after_id = max(0, int(after_id or 0))
    hours = int(hours or 0)
    limit = max(1, min(int(limit or 1000), 5000))
    params: list[Any] = []
    clauses: list[str] = []

    if after_id > 0:
        clauses.append("id > ?")
        params.append(after_id)
        if end:
            clauses.append("timestamp <= ?")
            params.append(str(end))
    else:
        if start:
            clauses.append("timestamp >= ?")
            params.append(str(start))
        if end:
            clauses.append("timestamp <= ?")
            params.append(str(end))
        if not start and hours > 0:
            hours = max(1, min(hours, 24 * 30))
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
            clauses.append("timestamp >= ?")
            params.append(cutoff)

    where = "WHERE " + " AND ".join(clauses) if clauses else ""

    with connection() as conn:
        # Replays e seeks trabalham sempre em ordem cronológica.
        if after_id > 0 or start or end:
            rows = conn.execute(
                f"SELECT id,timestamp,from_call,packet_format,raw FROM packets {where} ORDER BY id ASC LIMIT ?",
                (*params, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT id,timestamp,from_call,packet_format,raw FROM packets {where} ORDER BY id DESC LIMIT ?",
                (*params, limit),
            ).fetchall()
            rows = list(reversed(rows))

        parsed: list[tuple[sqlite3.Row, str, list[tuple[str, str, str, str | None]]]] = []
        calls: set[str] = set()
        for row in rows:
            source, edges = _observed_topology_edges(row["raw"])
            source = source or str(row["from_call"] or "").upper().strip()
            if source:
                calls.add(source)
            for a, b, _kind, _igate in edges:
                calls.add(a)
                calls.add(b)
            parsed.append((row, source, edges))

        coords: dict[str, tuple[float, float]] = {}
        position_issues = _station_position_issues_conn(conn)
        if calls:
            placeholders = ",".join("?" for _ in calls)
            station_rows = conn.execute(
                f"SELECT callsign,latitude,longitude FROM stations WHERE UPPER(callsign) IN ({placeholders})",
                [call.upper() for call in calls],
            ).fetchall()
            for station in station_rows:
                call = str(station["callsign"] or "").upper().strip()
                if call in position_issues:
                    continue
                if _valid_geo_position(station["latitude"], station["longitude"]):
                    coords[call] = (float(station["latitude"]), float(station["longitude"]))

    events: list[dict[str, Any]] = []
    for row, source, edges in parsed:
        segments = []
        incomplete = False
        for a, b, kind, _igate in edges:
            ca, cb = coords.get(a.upper()), coords.get(b.upper())
            if not ca or not cb:
                incomplete = True
                continue
            segments.append({
                "source": a,
                "target": b,
                "kind": kind,
                "source_lat": ca[0],
                "source_lon": ca[1],
                "target_lat": cb[0],
                "target_lon": cb[1],
            })
        events.append({
            "id": int(row["id"]),
            "timestamp": row["timestamp"],
            "source": source,
            "packet_format": row["packet_format"],
            "raw": row["raw"],
            "segments": segments,
            "incomplete": incomplete,
        })

    return {
        "events": events,
        "last_id": max([int(row["id"]) for row in rows], default=latest_packet_id()),
        "complete": hours <= 0 and after_id == 0 and not start and not end,
        "has_more": len(rows) >= limit,
    }



def list_favorites() -> list[str]:
    with connection() as conn:
        rows = conn.execute("SELECT callsign FROM favorites ORDER BY created_at, callsign").fetchall()
    return [str(row["callsign"]).upper() for row in rows]


def set_favorite(callsign: str, favorite: bool) -> bool:
    call = str(callsign or "").upper().strip()
    if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", call):
        raise ValueError("Indicativo inválido para Favoritos.")
    with connection() as conn:
        if favorite:
            conn.execute(
                "INSERT INTO favorites(callsign,created_at) VALUES(?,?) ON CONFLICT(callsign) DO NOTHING",
                (call, utc_now_iso()),
            )
        else:
            conn.execute("DELETE FROM favorites WHERE UPPER(callsign)=UPPER(?)", (call,))
    return favorite


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
        station_rows = conn.execute(
            """
            SELECT s.*, CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
            FROM stations s
            LEFT JOIN favorites f ON UPPER(f.callsign)=UPPER(s.callsign)
            WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
            ORDER BY favorite DESC, s.last_heard DESC
            """
        ).fetchall()
        issues = _station_position_issues_conn(conn)
        stations = []
        valid_calls: set[str] = set()
        for row in station_rows:
            item = dict(row)
            call = str(item.get("callsign") or "").upper().strip()
            if call in issues or not _valid_geo_position(item.get("latitude"), item.get("longitude")):
                continue
            item["position_valid"] = True
            item["position_issue"] = ""
            stations.append(item)
            valid_calls.add(call)

        # Últimos 10 mil pontos; o frontend agrupa por estação. Evita travar após meses de operação.
        tracks = [
            dict(r)
            for r in conn.execute(
                "SELECT callsign,timestamp,latitude,longitude,speed,course,altitude FROM tracks ORDER BY id DESC LIMIT 10000"
            ).fetchall()
        ]
    tracks = [
        row
        for row in reversed(tracks)
        if str(row.get("callsign") or "").upper().strip() in valid_calls
        and _valid_geo_position(row.get("latitude"), row.get("longitude"))
    ]
    return {"stations": stations, "tracks": tracks}


def geographic_export_data(hours: int = 0) -> dict[str, Any]:
    hours = int(hours or 0)
    if hours > 0:
        hours = max(1, min(hours, 24 * 30))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    else:
        cutoff = None

    data = map_data()
    tracks = []
    for row in data.get("tracks") or []:
        if cutoff:
            timestamp = _parse_timestamp(row.get("timestamp"))
            if timestamp is None or timestamp < cutoff:
                continue
        tracks.append(row)

    return {
        "hours": 0 if hours <= 0 else hours,
        "stations": data.get("stations") or [],
        "tracks": tracks,
        "topology": list_topology_edges(hours),
    }


def add_aprs_query(
    direction: str,
    peer: str,
    query_type: str,
    query_payload: str,
    status: str = "Aguardando resposta",
    raw: str | None = None,
    message_id: str | None = None,
) -> int:
    direction = str(direction or "").lower().strip()
    if direction not in {"in", "out"}:
        raise ValueError("Direção de query APRS inválida.")
    peer = str(peer or "").upper().strip()
    query_type = str(query_type or "").upper().strip()
    with connection() as conn:
        cur = conn.execute(
            """INSERT INTO aprs_queries(direction,peer,query_type,query_payload,status,sent_at,message_id,raw)
               VALUES(?,?,?,?,?,?,?,?)""",
            (direction, peer, query_type, str(query_payload or ""), str(status or ""), utc_now_iso(), message_id, raw),
        )
        return int(cur.lastrowid)


def update_aprs_query_result(
    query_id: int,
    status: str,
    response_text: str | None = None,
    response_raw: str | None = None,
    trace_path: list[str] | None = None,
) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM aprs_queries WHERE id=?", (int(query_id),)).fetchone()
        if not row:
            return None
        sent = datetime.fromisoformat(str(row["sent_at"]))
        now = datetime.now(timezone.utc)
        rtt_ms = max(0.0, (now - sent).total_seconds() * 1000.0)
        conn.execute(
            """UPDATE aprs_queries
               SET status=?, response_at=?, rtt_ms=?, response_text=?, response_raw=?, trace_path=?
               WHERE id=?""",
            (
                str(status or ""),
                now.isoformat(timespec="seconds"),
                rtt_ms,
                response_text,
                response_raw,
                json.dumps(trace_path or [], ensure_ascii=False) if trace_path is not None else row["trace_path"],
                int(query_id),
            ),
        )
    return get_aprs_query(query_id)


def resolve_aprs_query_response(
    peer: str,
    query_types: Iterable[str],
    response_text: str,
    response_raw: str,
    trace_path: list[str] | None = None,
) -> dict[str, Any] | None:
    peer = str(peer or "").upper().strip()
    types = [str(item or "").upper().strip() for item in query_types if str(item or "").strip()]
    if not peer or not types:
        return None
    placeholders = ",".join("?" for _ in types)
    with connection() as conn:
        row = conn.execute(
            f"""SELECT id FROM aprs_queries
                WHERE direction='out' AND UPPER(peer)=UPPER(?)
                  AND query_type IN ({placeholders})
                  AND status='Aguardando resposta'
                ORDER BY id DESC LIMIT 1""",
            [peer, *types],
        ).fetchone()
    if not row:
        return None
    return update_aprs_query_result(
        int(row["id"]),
        "Respondida",
        response_text=response_text,
        response_raw=response_raw,
        trace_path=trace_path,
    )


def resolve_ping_ack(msg_id: str, peer: str) -> dict[str, Any] | None:
    msg_id = str(msg_id or "").strip()
    peer = str(peer or "").upper().strip()
    if not msg_id or not peer:
        return None
    with connection() as conn:
        row = conn.execute(
            """SELECT id FROM aprs_queries
               WHERE direction='out' AND query_type='PINGACK'
                 AND status='Aguardando resposta'
                 AND message_id=? AND UPPER(peer)=UPPER(?)
               ORDER BY id DESC LIMIT 1""",
            (msg_id, peer),
        ).fetchone()
    if not row:
        return None
    return update_aprs_query_result(
        int(row["id"]),
        "Respondida",
        response_text=f"ACK {msg_id}",
        response_raw=f"ack{msg_id}",
    )


def expire_aprs_queries(timeout_seconds: int = 30) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=max(5, int(timeout_seconds or 30)))).isoformat(timespec="seconds")
    with connection() as conn:
        cur = conn.execute(
            """UPDATE aprs_queries SET status='Sem resposta / timeout'
               WHERE direction='out' AND status='Aguardando resposta' AND sent_at < ?""",
            (cutoff,),
        )
        return max(0, int(cur.rowcount or 0))


def list_aprs_queries(peer: str = "", limit: int = 100) -> list[dict[str, Any]]:
    expire_aprs_queries()
    peer = str(peer or "").upper().strip()
    limit = max(1, min(int(limit or 100), 1000))
    with connection() as conn:
        if peer:
            rows = conn.execute(
                "SELECT * FROM aprs_queries WHERE UPPER(peer)=UPPER(?) ORDER BY id DESC LIMIT ?",
                (peer, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM aprs_queries ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(row) for row in rows]


def get_aprs_query(query_id: int) -> dict[str, Any] | None:
    expire_aprs_queries()
    with connection() as conn:
        row = conn.execute("SELECT * FROM aprs_queries WHERE id=?", (int(query_id),)).fetchone()
    return dict(row) if row else None


def aprs_query_detail(query_id: int) -> dict[str, Any] | None:
    row = get_aprs_query(query_id)
    if not row:
        return None
    try:
        trace = json.loads(row.get("trace_path") or "[]")
    except Exception:
        trace = []
    trace = [str(call or "").upper().strip().rstrip("*") for call in trace if str(call or "").strip()]
    positions: dict[str, dict[str, Any]] = {}
    if trace:
        placeholders = ",".join("?" for _ in trace)
        with connection() as conn:
            rows = conn.execute(
                f"""SELECT callsign,latitude,longitude,last_heard
                    FROM stations
                    WHERE UPPER(callsign) IN ({placeholders})""",
                [call.upper() for call in trace],
            ).fetchall()
        positions = {str(item["callsign"]).upper(): dict(item) for item in rows}

    cfg = get_config()
    own = str(cfg.get("callsign") or "").upper().strip()
    ssid = int(cfg.get("ssid") or 0)
    own = f"{own}-{ssid}" if own and ssid else own

    nodes = []
    for call in trace:
        item = positions.get(call.upper(), {})
        lat = item.get("latitude")
        lon = item.get("longitude")
        if call.upper() == own.upper() and (lat is None or lon is None):
            lat, lon = cfg.get("latitude"), cfg.get("longitude")
        nodes.append({
            "callsign": call,
            "latitude": lat,
            "longitude": lon,
            "known": lat is not None and lon is not None,
            "last_heard": item.get("last_heard"),
        })
    row["trace_nodes"] = nodes
    row["trace_path_list"] = trace
    return row


def add_message(direction: str, from_call: str, to_call: str, message: str, msg_id: str | None = None,
                status: str = "", raw: str | None = None, message_type: str = "message",
                message_group_id: str | None = None, part_index: int | None = None,
                part_count: int | None = None, retry_count: int = 0) -> int:
    message_type = str(message_type or "message").strip().lower()
    if message_type not in {"message", "bulletin", "group_bulletin"}:
        message_type = "message"
    with connection() as conn:
        cur = conn.execute(
            """INSERT INTO messages(direction,from_call,to_call,message,message_type,msg_id,status,
                                    message_group_id,part_index,part_count,retry_count,timestamp,raw)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                direction, from_call.upper(), to_call.upper(), message, message_type, msg_id, status,
                message_group_id, part_index, part_count, max(0, int(retry_count or 0)), utc_now_iso(), raw,
            ),
        )
        return int(cur.lastrowid)


def add_outgoing_message_parts(rows: list[dict[str, Any]]) -> list[int]:
    """Insere todas as partes de uma mensagem APRS na mesma transação SQLite."""
    if not rows:
        return []
    ids: list[int] = []
    with connection() as conn:
        for row in rows:
            cur = conn.execute(
                """INSERT INTO messages(direction,from_call,to_call,message,message_type,msg_id,status,
                                        message_group_id,part_index,part_count,retry_count,timestamp,raw)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "out",
                    str(row.get("from_call") or "").upper(),
                    str(row.get("to_call") or "").upper(),
                    str(row.get("message") or ""),
                    "message",
                    row.get("msg_id"),
                    str(row.get("status") or "Na fila"),
                    row.get("message_group_id"),
                    row.get("part_index"),
                    row.get("part_count"),
                    max(0, int(row.get("retry_count") or 0)),
                    utc_now_iso(),
                    row.get("raw"),
                ),
            )
            ids.append(int(cur.lastrowid))
    return ids


def get_message(row_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id=?", (int(row_id),)).fetchone()
    return dict(row) if row else None


def reset_config() -> dict[str, Any]:
    """Restaura somente preferências/configuração; não apaga dados operacionais."""
    with connection() as conn:
        assignments = ", ".join(f"{key}=?" for key in DEFAULT_CONFIG)
        conn.execute(
            f"UPDATE config SET {assignments}, updated_at=? WHERE id=1",
            [*DEFAULT_CONFIG.values(), utc_now_iso()],
        )
    return get_config()


def mark_message_retried(row_id: int) -> None:
    with connection() as conn:
        conn.execute("UPDATE messages SET status='Substituída por retry' WHERE id=?", (int(row_id),))


def list_retry_candidates(timeout_seconds: int, max_retries: int, limit: int = 20) -> list[dict[str, Any]]:
    timeout_seconds = max(15, int(timeout_seconds or 60))
    max_retries = max(0, int(max_retries or 0))
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)).isoformat(timespec="seconds")
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM messages
            WHERE direction='out'
              AND message_type='message'
              AND status IN ('Enviada','Reenviada')
              AND COALESCE(retry_count,0) < ?
              AND timestamp <= ?
            ORDER BY id ASC LIMIT ?
            """,
            (max_retries, cutoff, int(limit)),
        ).fetchall()
    return [dict(r) for r in rows]


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


def mark_message_read(row_id: int) -> int:
    with connection() as conn:
        cur = conn.execute(
            "UPDATE messages SET read_at=COALESCE(read_at, ?) WHERE id=? AND direction='in'",
            (utc_now_iso(), int(row_id)),
        )
        return max(0, int(cur.rowcount or 0))


def mark_conversation_read(contact: str, own_callsign: str = "") -> int:
    contact = str(contact or "").upper().strip()
    own = str(own_callsign or "").upper().strip()
    if not contact:
        return 0
    with connection() as conn:
        if own:
            cur = conn.execute(
                """
                UPDATE messages SET read_at=COALESCE(read_at, ?)
                WHERE direction='in' AND message_type='message'
                  AND UPPER(from_call)=UPPER(?) AND UPPER(to_call)=UPPER(?)
                """,
                (utc_now_iso(), contact, own),
            )
        else:
            cur = conn.execute(
                """
                UPDATE messages SET read_at=COALESCE(read_at, ?)
                WHERE direction='in' AND message_type='message' AND UPPER(from_call)=UPPER(?)
                """,
                (utc_now_iso(), contact),
            )
        return max(0, int(cur.rowcount or 0))


def clear_messages() -> int:
    with connection() as conn:
        cur = conn.execute("DELETE FROM messages")
        return max(0, int(cur.rowcount or 0))


def callsign_suggestions(prefix: str = "", limit: int = 30) -> list[str]:
    p = prefix.upper().strip() + "%"
    with connection() as conn:
        rows = conn.execute(
            """
            WITH calls AS (
                SELECT callsign AS callsign FROM stations
                UNION SELECT from_call FROM messages
                UNION SELECT to_call FROM messages
            )
            SELECT c.callsign
            FROM calls c
            LEFT JOIN favorites f ON UPPER(f.callsign)=UPPER(c.callsign)
            WHERE UPPER(c.callsign) LIKE ?
            ORDER BY CASE WHEN f.callsign IS NULL THEN 1 ELSE 0 END, UPPER(c.callsign)
            LIMIT ?
            """,
            (p, int(limit)),
        ).fetchall()
    return [r[0] for r in rows if r[0]]



def _add_aprs_log_conn(conn: sqlite3.Connection, direction: str, raw: str) -> int:
    direction = str(direction or "").upper().strip()
    if direction not in {"RX", "TX"}:
        raise ValueError("Direção do log APRS-IS deve ser RX ou TX.")
    cur = conn.execute(
        "INSERT INTO aprs_log(timestamp, direction, raw) VALUES (?, ?, ?)",
        (utc_now_iso(), direction, str(raw)),
    )
    if _retention_due("aprs_log"):
        deleted = _trim_history_table(conn, "aprs_log", APRS_LOG_RETENTION)
        if deleted:
            diag.log_event("retention_sweep", table="aprs_log", deleted=deleted)
    return int(cur.lastrowid)


def add_aprs_log(direction: str, raw: str) -> int:
    with connection() as conn:
        return _add_aprs_log_conn(conn, direction, raw)


def process_received_packet(
    raw: str,
    parsed: dict[str, Any],
    from_call: str | None = None,
    packet_format: str | None = None,
) -> None:
    """Persiste o pipeline RX principal em uma única conexão/transação SQLite."""
    started = time.monotonic()
    with connection() as conn:
        _add_aprs_log_conn(conn, "RX", raw)
        _record_packet_conn(conn, raw, from_call, packet_format)
        _record_topology_from_raw_conn(conn, raw)
        if parsed and parsed.get("from"):
            _upsert_station_conn(conn, parsed)
    elapsed_ms = (time.monotonic() - started) * 1000
    if elapsed_ms >= 250:
        diag.log_event(
            "rx_transaction_slow",
            duration_ms=round(elapsed_ms, 1),
            from_call=from_call or "",
            packet_format=packet_format or "",
        )

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


def shutdown_maintenance() -> dict[str, int]:
    """Manutenção leve e segura ao encerrar a aplicação."""
    cancelled = 0
    with connection() as conn:
        cur = conn.execute(
            "UPDATE messages SET status='Cancelada no encerramento' "
            "WHERE direction='out' AND status='Na fila'"
        )
        cancelled = max(0, int(cur.rowcount or 0))
        conn.execute("PRAGMA optimize")

    checkpointed = 0
    try:
        raw = sqlite3.connect(DB_PATH, timeout=5)
        try:
            row = raw.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            checkpointed = int(row[1] if row and len(row) > 1 else 0)
        finally:
            raw.close()
    except Exception:
        checkpointed = 0

    return {
        "cancelled_queued_messages": cancelled,
        "checkpointed_frames": checkpointed,
    }
