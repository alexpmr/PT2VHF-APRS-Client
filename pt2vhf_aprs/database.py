from __future__ import annotations

import hashlib
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
_topology_cache_db_path = ""
TOPOLOGY_CACHE_SECONDS = 2.0
TOPOLOGY_QUERY_MAX_SECONDS = 2.5

# SQLite operational tuning for growing local databases. These values are
# intentionally conservative: WAL still provides concurrency, while temporary
# grouping/sort work stays off disk without reserving a large cache per worker.
SQLITE_BUSY_TIMEOUT_MS = 5000
SQLITE_CACHE_KIB = 8192
SQLITE_WAL_AUTOCHECKPOINT_PAGES = 1000

# /api/map-data is one of the most requested and expensive read paths.
# Keep one builder at a time for the whole process; concurrent callers receive
# the latest valid snapshot instead of starting identical SQLite work.
_map_data_build_lock = threading.Lock()
_map_data_cache_lock = threading.Lock()
_map_data_cache_payload: dict[str, Any] | None = None
_map_data_cache_at = 0.0
_map_data_cache_build_ms = 0.0
_map_data_cache_db_path = ""
MAP_DATA_CACHE_SECONDS = 30.0
MAP_DATA_INITIAL_WAIT_SECONDS = 0.75

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
    "update_check_minutes": 15,
    "auto_download_updates": 0,
    "install_updates_on_exit": 0,
    "message_retry_seconds": 60,
    "message_retry_attempts": 2,
    "respond_to_queries": 1,
    "auto_reply_enabled": 0,
    "auto_reply_text": "Mensagem recebida. Retornarei assim que possível.",
    "auto_reply_cooldown_seconds": 300,
    "language": "pt-BR",
    "map_type": "osm",
    "track_color": "#3ba6ff",
    "track_width": 2,
    "topology_rf_color": "#ffff00",
    "topology_igate_color": "#ffff00",
    "topology_width": 1,
    "map_brightness": 100,
    "map_zoom_step": 0.10,
    "weather_radar_opacity": 55,
    "elevation_threshold": 1000,
    "elevation_slider_max": 3000,
    "elevation_opacity": 55,
    "sound_on_personal_message": 1,
    "sound_on_station_activity": 1,
    "highlight_station_activity": 1,
    "traffic_animation_enabled": 1,
    "message_popup_seconds": 5,
    "resource_alert_enabled": 1,
    "resource_cpu_critical_percent": 90,
    "resource_memory_critical_percent": 90,
    "resource_alert_sustain_seconds": 30,
    "resource_alert_cooldown_minutes": 10,
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
        conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        conn.execute(f"PRAGMA wal_autocheckpoint={SQLITE_WAL_AUTOCHECKPOINT_PAGES}")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute(f"PRAGMA cache_size=-{SQLITE_CACHE_KIB}")
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
        conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute(f"PRAGMA cache_size=-{SQLITE_CACHE_KIB}")
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
        # Preflight de schema: índices do bloco principal podem referenciar
        # colunas adicionadas em versões posteriores. Em bancos legados,
        # crie essas colunas antes de executar CREATE INDEX IF NOT EXISTS.
        existing_tables = {
            row["name"] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "messages" in existing_tables:
            pre_message_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(messages)").fetchall()
            }
            if "message_type" not in pre_message_columns:
                conn.execute(
                    "ALTER TABLE messages ADD COLUMN message_type TEXT NOT NULL DEFAULT 'message'"
                )

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
                update_check_minutes INTEGER NOT NULL DEFAULT 15,
                auto_download_updates INTEGER NOT NULL DEFAULT 0,
                install_updates_on_exit INTEGER NOT NULL DEFAULT 0,
                message_retry_seconds INTEGER NOT NULL DEFAULT 60,
                message_retry_attempts INTEGER NOT NULL DEFAULT 2,
                respond_to_queries INTEGER NOT NULL DEFAULT 1,
                auto_reply_enabled INTEGER NOT NULL DEFAULT 0,
                auto_reply_text TEXT NOT NULL DEFAULT 'Mensagem recebida. Retornarei assim que possível.',
                auto_reply_cooldown_seconds INTEGER NOT NULL DEFAULT 300,
                language TEXT NOT NULL DEFAULT 'pt-BR',
                map_type TEXT NOT NULL DEFAULT 'osm',
                track_color TEXT NOT NULL DEFAULT '#3ba6ff',
                track_width INTEGER NOT NULL DEFAULT 2,
                topology_rf_color TEXT NOT NULL DEFAULT '#ffff00',
                topology_igate_color TEXT NOT NULL DEFAULT '#ffff00',
                topology_width INTEGER NOT NULL DEFAULT 1,
                map_brightness INTEGER NOT NULL DEFAULT 100,
                map_zoom_step REAL NOT NULL DEFAULT 0.10,
                weather_radar_opacity INTEGER NOT NULL DEFAULT 55,
                elevation_threshold INTEGER NOT NULL DEFAULT 1000,
                elevation_slider_max INTEGER NOT NULL DEFAULT 3000,
                elevation_opacity INTEGER NOT NULL DEFAULT 55,
                sound_on_personal_message INTEGER NOT NULL DEFAULT 1,
                sound_on_station_activity INTEGER NOT NULL DEFAULT 1,
                highlight_station_activity INTEGER NOT NULL DEFAULT 1,
                traffic_animation_enabled INTEGER NOT NULL DEFAULT 1,
                message_popup_seconds INTEGER NOT NULL DEFAULT 5,
                resource_alert_enabled INTEGER NOT NULL DEFAULT 1,
                resource_cpu_critical_percent INTEGER NOT NULL DEFAULT 90,
                resource_memory_critical_percent INTEGER NOT NULL DEFAULT 90,
                resource_alert_sustain_seconds INTEGER NOT NULL DEFAULT 30,
                resource_alert_cooldown_minutes INTEGER NOT NULL DEFAULT 10,
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
                zoom REAL NOT NULL DEFAULT 4,
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

            CREATE INDEX IF NOT EXISTS idx_stations_last_heard ON stations(last_heard DESC);

            CREATE TABLE IF NOT EXISTS aprs_objects (
                name TEXT PRIMARY KEY,
                source_callsign TEXT,
                first_heard TEXT,
                last_heard TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                altitude REAL,
                max_altitude REAL,
                speed REAL,
                course REAL,
                symbol_table TEXT,
                symbol TEXT,
                info TEXT,
                comment TEXT,
                status TEXT,
                path TEXT,
                weather_json TEXT,
                alive INTEGER NOT NULL DEFAULT 1,
                packet_format TEXT,
                raw TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_aprs_objects_last_heard ON aprs_objects(last_heard DESC);

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
                altitude REAL,
                path TEXT,
                raw TEXT,
                rssi REAL,
                snr REAL
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
                tx_medium TEXT,
                tx_path TEXT,
                automated INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                raw TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_call);
            CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_call);
            CREATE INDEX IF NOT EXISTS idx_messages_interaction_in ON messages(direction,message_type,from_call);
            CREATE INDEX IF NOT EXISTS idx_messages_interaction_out ON messages(direction,status,to_call);

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
            CREATE INDEX IF NOT EXISTS idx_aprs_queries_interaction ON aprs_queries(direction,status,response_at,peer);

            CREATE TABLE IF NOT EXISTS packets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                from_call TEXT,
                packet_format TEXT,
                raw TEXT NOT NULL,
                medium TEXT NOT NULL DEFAULT 'APRS-IS',
                rx_fingerprint TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_packets_time ON packets(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_packets_time_from_call ON packets(timestamp DESC, from_call);
            CREATE INDEX IF NOT EXISTS idx_packets_from_call_norm_time
                ON packets(UPPER(TRIM(from_call)), timestamp DESC);

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
            CREATE INDEX IF NOT EXISTS idx_topology_kind_target_seen
                ON topology_edges(kind, target, last_seen DESC);
            CREATE INDEX IF NOT EXISTS idx_topology_igate_seen
                ON topology_edges(igate, last_seen DESC);

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
        # Migração v1.7.7:
        # Marcador histórico preservado para testes de compatibilidade do schema.
        # v1.12.0: a antiga conversão destrutiva RF -> iGate foi aposentada.
        # O papel de iGate não define o meio físico do enlace; a evidência real
        # de transporte/path passa a ser preservada explicitamente abaixo.

        track_columns = {row["name"] for row in conn.execute("PRAGMA table_info(tracks)").fetchall()}
        if "path" not in track_columns:
            conn.execute("ALTER TABLE tracks ADD COLUMN path TEXT")
        if "raw" not in track_columns:
            conn.execute("ALTER TABLE tracks ADD COLUMN raw TEXT")
        if "rssi" not in track_columns:
            conn.execute("ALTER TABLE tracks ADD COLUMN rssi REAL")
        if "snr" not in track_columns:
            conn.execute("ALTER TABLE tracks ADD COLUMN snr REAL")

        packet_columns = {row["name"] for row in conn.execute("PRAGMA table_info(packets)").fetchall()}
        if "medium" not in packet_columns:
            conn.execute("ALTER TABLE packets ADD COLUMN medium TEXT NOT NULL DEFAULT 'APRS-IS'")
        if "rx_fingerprint" not in packet_columns:
            conn.execute("ALTER TABLE packets ADD COLUMN rx_fingerprint TEXT")
        # Indexes that depend on migrated columns must remain after ALTER TABLE
        # so databases created before medium/rx_fingerprint continue to upgrade.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_packets_medium_time ON packets(medium, timestamp DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_packets_medium_call_time ON packets(medium, from_call, timestamp DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_packets_fingerprint_time ON packets(rx_fingerprint, timestamp DESC)")

        topology_columns = {row["name"] for row in conn.execute("PRAGMA table_info(topology_edges)").fetchall()}
        if "rf_transport_count" not in topology_columns:
            conn.execute("ALTER TABLE topology_edges ADD COLUMN rf_transport_count INTEGER NOT NULL DEFAULT 0")
        if "rf_path_count" not in topology_columns:
            conn.execute("ALTER TABLE topology_edges ADD COLUMN rf_path_count INTEGER NOT NULL DEFAULT 0")
        if "internet_confirmed_count" not in topology_columns:
            conn.execute("ALTER TABLE topology_edges ADD COLUMN internet_confirmed_count INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations_v112 (
                   migration_key TEXT PRIMARY KEY,
                   applied_at TEXT NOT NULL
               )"""
        )
        _repair_topology_rf_evidence_v112(conn)

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS recipient_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                callsigns_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                schedule_type TEXT NOT NULL DEFAULT 'once',
                run_at_utc TEXT,
                weekday INTEGER,
                time_local TEXT,
                target_type TEXT NOT NULL DEFAULT 'station',
                target TEXT NOT NULL DEFAULT '',
                targets_json TEXT NOT NULL DEFAULT '[]',
                retry_targets_json TEXT NOT NULL DEFAULT '[]',
                recipient_group_id INTEGER,
                message_type TEXT NOT NULL DEFAULT 'message',
                message TEXT NOT NULL DEFAULT '',
                route TEXT NOT NULL DEFAULT 'auto',
                path TEXT NOT NULL DEFAULT '',
                bulletin_id TEXT NOT NULL DEFAULT '0',
                aprs_group TEXT NOT NULL DEFAULT '',
                interval_seconds INTEGER NOT NULL DEFAULT 3,
                retry_policy TEXT NOT NULL DEFAULT 'skip',
                retry_minutes INTEGER NOT NULL DEFAULT 10,
                continue_on_error INTEGER NOT NULL DEFAULT 1,
                next_run_at TEXT,
                last_run_at TEXT,
                last_status TEXT NOT NULL DEFAULT '',
                last_error TEXT NOT NULL DEFAULT '',
                last_summary TEXT NOT NULL DEFAULT '',
                last_occurrence_key TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(recipient_group_id) REFERENCES recipient_groups(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_scheduled_messages_due
                ON scheduled_messages(enabled, next_run_at);
            """
        )

        scheduled_columns = {row["name"] for row in conn.execute("PRAGMA table_info(scheduled_messages)").fetchall()}
        if "retry_targets_json" not in scheduled_columns:
            conn.execute("ALTER TABLE scheduled_messages ADD COLUMN retry_targets_json TEXT NOT NULL DEFAULT '[]'")

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
        if "map_zoom_step" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN map_zoom_step REAL NOT NULL DEFAULT 0.10")
        if "weather_radar_opacity" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN weather_radar_opacity INTEGER NOT NULL DEFAULT 55")
        if "elevation_threshold" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN elevation_threshold INTEGER NOT NULL DEFAULT 1000")
        if "elevation_slider_max" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN elevation_slider_max INTEGER NOT NULL DEFAULT 3000")
        if "elevation_opacity" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN elevation_opacity INTEGER NOT NULL DEFAULT 55")
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
        if "resource_alert_enabled" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN resource_alert_enabled INTEGER NOT NULL DEFAULT 1")
        if "resource_cpu_critical_percent" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN resource_cpu_critical_percent INTEGER NOT NULL DEFAULT 90")
        if "resource_memory_critical_percent" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN resource_memory_critical_percent INTEGER NOT NULL DEFAULT 90")
        if "resource_alert_sustain_seconds" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN resource_alert_sustain_seconds INTEGER NOT NULL DEFAULT 30")
        if "resource_alert_cooldown_minutes" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN resource_alert_cooldown_minutes INTEGER NOT NULL DEFAULT 10")
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
        if "update_check_minutes" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN update_check_minutes INTEGER NOT NULL DEFAULT 15")
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
        if "auto_reply_enabled" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN auto_reply_enabled INTEGER NOT NULL DEFAULT 0")
        if "auto_reply_text" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN auto_reply_text TEXT NOT NULL DEFAULT 'Mensagem recebida. Retornarei assim que possível.'")
        if "auto_reply_cooldown_seconds" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN auto_reply_cooldown_seconds INTEGER NOT NULL DEFAULT 300")

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
        if "tx_medium" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN tx_medium TEXT")
        if "tx_path" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN tx_path TEXT")
        if "automated" not in message_columns:
            conn.execute("ALTER TABLE messages ADD COLUMN automated INTEGER NOT NULL DEFAULT 0")

        object_columns = {row["name"] for row in conn.execute("PRAGMA table_info(aprs_objects)").fetchall()}
        object_migrations = {
            "first_heard": "TEXT",
            "max_altitude": "REAL",
            "speed": "REAL",
            "course": "REAL",
            "comment": "TEXT",
            "status": "TEXT",
            "path": "TEXT",
            "weather_json": "TEXT",
            "alive": "INTEGER NOT NULL DEFAULT 1",
        }
        for column, definition in object_migrations.items():
            if column not in object_columns:
                conn.execute(f"ALTER TABLE aprs_objects ADD COLUMN {column} {definition}")
        conn.execute(
            "UPDATE aprs_objects SET first_heard=COALESCE(first_heard,last_heard), "
            "max_altitude=COALESCE(max_altitude,altitude) "
            "WHERE first_heard IS NULL OR max_altitude IS NULL"
        )

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

        # Refresh planner statistics after schema/index migrations. PRAGMA
        # optimize is incremental and avoids the blocking full VACUUM path.
        conn.execute("PRAGMA optimize")


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
    provided = set(data) & allowed
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
    merged["update_check_minutes"] = max(5, min(1440, int(merged["update_check_minutes"] or 15)))
    merged["auto_download_updates"] = 0
    merged["install_updates_on_exit"] = 0
    merged["message_retry_seconds"] = max(15, min(3600, int(merged["message_retry_seconds"] or 60)))
    merged["message_retry_attempts"] = max(0, min(10, int(merged["message_retry_attempts"] or 0)))
    merged["respond_to_queries"] = 1 if bool(merged["respond_to_queries"]) else 0
    merged["auto_reply_enabled"] = 1 if bool(merged["auto_reply_enabled"]) else 0
    merged["auto_reply_text"] = " ".join(str(merged["auto_reply_text"] or "").replace("\r", " ").replace("\n", " ").split())[:240]
    merged["auto_reply_cooldown_seconds"] = max(30, min(86400, int(merged["auto_reply_cooldown_seconds"] or 300)))
    merged["language"] = str(merged["language"] or "pt-BR").strip()
    merged["aprs_filter"] = str(merged["aprs_filter"] or "").strip()
    merged["map_type"] = str(merged["map_type"] or "osm").lower().strip()
    merged["track_color"] = str(merged["track_color"] or "#3ba6ff").lower().strip()
    merged["track_width"] = int(merged["track_width"] or 2)
    merged["topology_rf_color"] = str(merged["topology_rf_color"] or "#ffff00").lower().strip()
    merged["topology_igate_color"] = str(merged["topology_igate_color"] or "#ffff00").lower().strip()
    merged["topology_width"] = int(merged["topology_width"] or 1)
    merged["map_brightness"] = int(merged["map_brightness"] or 100)
    merged["map_zoom_step"] = round(float(merged["map_zoom_step"] if merged["map_zoom_step"] not in ("", None) else 0.10), 2)
    merged["weather_radar_opacity"] = int(merged["weather_radar_opacity"] or 55)
    merged["elevation_threshold"] = int(merged["elevation_threshold"] if merged["elevation_threshold"] not in ("", None) else 1000)
    merged["elevation_slider_max"] = int(merged["elevation_slider_max"] if merged["elevation_slider_max"] not in ("", None) else 3000)
    merged["elevation_opacity"] = int(merged["elevation_opacity"] if merged["elevation_opacity"] not in ("", None) else 55)
    merged["sound_on_personal_message"] = 1 if bool(merged["sound_on_personal_message"]) else 0
    merged["sound_on_station_activity"] = 1 if bool(merged["sound_on_station_activity"]) else 0
    merged["highlight_station_activity"] = 1 if bool(merged["highlight_station_activity"]) else 0
    merged["traffic_animation_enabled"] = 1 if bool(merged["traffic_animation_enabled"]) else 0
    merged["message_popup_seconds"] = int(merged["message_popup_seconds"] or 5)
    merged["resource_alert_enabled"] = 1 if bool(merged["resource_alert_enabled"]) else 0
    merged["resource_cpu_critical_percent"] = int(merged["resource_cpu_critical_percent"] or 90)
    merged["resource_memory_critical_percent"] = int(merged["resource_memory_critical_percent"] or 90)
    merged["resource_alert_sustain_seconds"] = int(merged["resource_alert_sustain_seconds"] or 30)
    merged["resource_alert_cooldown_minutes"] = int(merged["resource_alert_cooldown_minutes"] or 10)
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
    if "ssid" in provided and not (0 <= merged["ssid"] <= 15):
        raise ValueError("SSID deve estar entre 0 e 15.")
    if "latitude" in provided and merged["latitude"] is not None and not (-90 <= merged["latitude"] <= 90):
        raise ValueError("Latitude inválida.")
    if "longitude" in provided and merged["longitude"] is not None and not (-180 <= merged["longitude"] <= 180):
        raise ValueError("Longitude inválida.")
    if "server" in provided and not merged["server"]:
        raise ValueError("Servidor APRS-IS não pode ficar vazio.")
    if "port" in provided and not (1 <= merged["port"] <= 65535):
        raise ValueError("Porta inválida.")
    if merged["altitude_source"] not in {"manual", "geolocation", "fallback_zero"}:
        merged["altitude_source"] = "manual"
    if "map_type" in provided and merged["map_type"] not in {"osm", "topo", "light", "dark", "cyclosm", "humanitarian", "osmde", "opnv", "satellite"}:
        raise ValueError("Tipo de mapa inválido.")
    if "track_color" in provided and not re.fullmatch(r"#[0-9a-fA-F]{6}", merged["track_color"]):
        raise ValueError("Cor do tracklog inválida.")
    if "track_width" in provided and not (1 <= merged["track_width"] <= 10):
        raise ValueError("Espessura do tracklog deve estar entre 1 e 10.")
    if "map_zoom_step" in provided and merged["map_zoom_step"] not in {0.05, 0.10, 0.25, 0.50, 1.00}:
        raise ValueError("Step do zoom deve ser 0,05, 0,10, 0,25, 0,50 ou 1,00.")
    if "topology_rf_color" in provided and not re.fullmatch(r"#[0-9a-fA-F]{6}", merged["topology_rf_color"]):
        raise ValueError("Cor dos enlaces RF da topologia inválida.")
    if "topology_igate_color" in provided and not re.fullmatch(r"#[0-9a-fA-F]{6}", merged["topology_igate_color"]):
        raise ValueError("Cor dos enlaces IGate da topologia inválida.")
    if "topology_width" in provided and not (1 <= merged["topology_width"] <= 10):
        raise ValueError("Espessura da topologia deve estar entre 1 e 10.")
    if "map_brightness" in provided and not (30 <= merged["map_brightness"] <= 150):
        raise ValueError("Brilho do mapa deve estar entre 30% e 150%.")
    if "weather_radar_opacity" in provided and not (10 <= merged["weather_radar_opacity"] <= 100):
        raise ValueError("Opacidade do radar deve estar entre 10% e 100%.")
    if "elevation_slider_max" in provided and not (100 <= merged["elevation_slider_max"] <= 9000):
        raise ValueError("Máximo do slider de relevo deve estar entre 100 m e 9.000 m.")
    if ("elevation_threshold" in provided or "elevation_slider_max" in provided) and not (0 <= merged["elevation_threshold"] <= merged["elevation_slider_max"]):
        raise ValueError("Cota do relevo deve ficar entre 0 m e o máximo configurado.")
    if "elevation_opacity" in provided and not (10 <= merged["elevation_opacity"] <= 100):
        raise ValueError("Opacidade do relevo deve estar entre 10% e 100%.")
    if "message_popup_seconds" in provided and not (1 <= merged["message_popup_seconds"] <= 60):
        raise ValueError("Duração do aviso de mensagem deve estar entre 1 e 60 segundos.")
    if "resource_cpu_critical_percent" in provided and not (70 <= merged["resource_cpu_critical_percent"] <= 100):
        raise ValueError("Limite crítico de CPU deve estar entre 70% e 100%.")
    if "resource_memory_critical_percent" in provided and not (70 <= merged["resource_memory_critical_percent"] <= 100):
        raise ValueError("Limite crítico de memória deve estar entre 70% e 100%.")
    if "resource_alert_sustain_seconds" in provided and not (10 <= merged["resource_alert_sustain_seconds"] <= 300):
        raise ValueError("Persistência do alerta deve estar entre 10 e 300 segundos.")
    if "resource_alert_cooldown_minutes" in provided and not (1 <= merged["resource_alert_cooldown_minutes"] <= 120):
        raise ValueError("Cooldown do alerta deve estar entre 1 e 120 minutos.")

    if "app_theme" in provided and merged["app_theme"] not in {"dark", "light"}:
        raise ValueError("Tema da aplicação inválido.")
    if "language" in provided and merged["language"] not in {"pt-BR", "en", "es", "fr"}:
        raise ValueError("Idioma da aplicação inválido.")

    allowed_fonts = {"system", "segoe", "arial", "verdana", "tahoma", "consolas"}
    if "messages_font_family" in provided and merged["messages_font_family"] not in allowed_fonts:
        raise ValueError("Fonte da tela de mensagens inválida.")
    if "stations_font_family" in provided and merged["stations_font_family"] not in allowed_fonts:
        raise ValueError("Fonte da tela de estações inválida.")
    if "logs_font_family" in provided and merged["logs_font_family"] not in allowed_fonts:
        raise ValueError("Fonte da tela de logs inválida.")
    if "messages_font_weight" in provided and merged["messages_font_weight"] not in {"normal", "bold"}:
        raise ValueError("Peso da fonte de mensagens inválido.")
    if "stations_font_weight" in provided and merged["stations_font_weight"] not in {"normal", "bold"}:
        raise ValueError("Peso da fonte de estações inválido.")
    if "logs_font_weight" in provided and merged["logs_font_weight"] not in {"normal", "bold"}:
        raise ValueError("Peso da fonte de logs inválido.")
    if "messages_font_size" in provided and not (10 <= merged["messages_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de mensagens deve estar entre 10 e 20 px.")
    if "stations_font_size" in provided and not (10 <= merged["stations_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de estações deve estar entre 10 e 20 px.")
    if "logs_font_size" in provided and not (10 <= merged["logs_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de logs deve estar entre 10 e 20 px.")
    if "statistics_font_size" in provided and not (11 <= merged["statistics_font_size"] <= 20):
        raise ValueError("Tamanho da fonte de estatísticas deve estar entre 11 e 20 px.")
    for key, label in (
        ("messages_line_height", "mensagens"),
        ("stations_line_height", "estações"),
        ("logs_line_height", "logs"),
    ):
        if key in provided and not (1.0 <= float(merged[key]) <= 2.0):
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


def save_map_state(latitude: float, longitude: float, zoom: float) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE map_state SET latitude=?, longitude=?, zoom=?, updated_at=? WHERE id=1",
            (float(latitude), float(longitude), float(zoom), utc_now_iso()),
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
        # qAR/qAO preserve case and explicitly identify the station that
        # gated the packet from RF. Do not downgrade this evidence merely
        # because TCPIP/TCPXX also appears elsewhere in the APRS-IS path.
        if token not in {"qAR", "qAO"}:
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


def _station_position_issues_conn(
    conn: sqlite3.Connection,
    station_rows: Iterable[sqlite3.Row] | None = None,
) -> dict[str, dict[str, Any]]:
    # Callers that already loaded the complete station set can reuse it and
    # avoid a second full stations scan in the same HTTP request.
    rows = list(station_rows) if station_rows is not None else conn.execute(
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



def _packet_reception_fingerprint(raw: str, from_call: str | None = None) -> str:
    """Impressão lógica que ignora path APRS para correlacionar RF e APRS-IS próximos."""
    text = str(raw or "").strip()
    header, sep, info = text.partition(":")
    source = str(from_call or "").upper().strip()
    destination = ""
    if ">" in header:
        left, right = header.split(">", 1)
        source = source or left.upper().strip()
        destination = right.split(",", 1)[0].upper().strip()
    canonical = f"{source}>{destination}:{info if sep else text}"
    return hashlib.sha1(canonical.encode("utf-8", errors="replace")).hexdigest()


def _record_packet_conn(
    conn: sqlite3.Connection,
    raw: str,
    from_call: str | None = None,
    packet_format: str | None = None,
    *,
    medium: str = "APRS-IS",
) -> None:
    medium = str(medium or "APRS-IS").upper().strip()
    if medium not in {"RF", "APRS-IS"}:
        medium = "APRS-IS"
    conn.execute(
        """INSERT INTO packets(timestamp, from_call, packet_format, raw, medium, rx_fingerprint)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            utc_now_iso(),
            from_call,
            packet_format,
            raw,
            medium,
            _packet_reception_fingerprint(raw, from_call),
        ),
    )
    if _retention_due("packets"):
        deleted = _trim_history_table(conn, "packets", PACKET_RETENTION)
        if deleted:
            diag.log_event("retention_sweep", table="packets", deleted=deleted)


def record_packet(
    raw: str,
    from_call: str | None = None,
    packet_format: str | None = None,
    *,
    medium: str = "APRS-IS",
) -> None:
    with connection() as conn:
        _record_packet_conn(conn, raw, from_call, packet_format, medium=medium)


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

    if is_object and _valid_geo_position(packet.get("latitude"), packet.get("longitude")):
        object_name = str(
            packet.get("object_name")
            or packet.get("item_name")
            or packet.get("name")
            or ""
        ).strip()
        if object_name:
            weather = packet.get("weather") if isinstance(packet.get("weather"), dict) else {}
            alive_raw = packet.get("alive")
            alive = 1 if alive_raw is None else (1 if bool(alive_raw) else 0)
            altitude = packet.get("altitude")
            conn.execute(
                """INSERT INTO aprs_objects(
                       name,source_callsign,first_heard,last_heard,latitude,longitude,
                       altitude,max_altitude,speed,course,symbol_table,symbol,info,
                       comment,status,path,weather_json,alive,packet_format,raw
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(name) DO UPDATE SET
                       source_callsign=excluded.source_callsign,
                       first_heard=COALESCE(aprs_objects.first_heard,excluded.first_heard),
                       last_heard=excluded.last_heard,
                       latitude=excluded.latitude,
                       longitude=excluded.longitude,
                       altitude=excluded.altitude,
                       max_altitude=CASE
                           WHEN excluded.altitude IS NULL THEN aprs_objects.max_altitude
                           WHEN aprs_objects.max_altitude IS NULL THEN excluded.altitude
                           ELSE MAX(aprs_objects.max_altitude,excluded.altitude)
                       END,
                       speed=excluded.speed,
                       course=excluded.course,
                       symbol_table=excluded.symbol_table,
                       symbol=excluded.symbol,
                       info=excluded.info,
                       comment=excluded.comment,
                       status=excluded.status,
                       path=excluded.path,
                       weather_json=excluded.weather_json,
                       alive=excluded.alive,
                       packet_format=excluded.packet_format,
                       raw=excluded.raw""",
                (
                    object_name,
                    callsign,
                    now,
                    now,
                    float(packet.get("latitude")),
                    float(packet.get("longitude")),
                    altitude,
                    altitude,
                    packet.get("speed"),
                    packet.get("course"),
                    packet.get("symbol_table"),
                    packet.get("symbol"),
                    _extract_info(packet),
                    str(packet.get("comment") or ""),
                    str(packet.get("status") or ""),
                    json.dumps(packet.get("path") or [], ensure_ascii=False),
                    json.dumps(weather, ensure_ascii=False, default=str),
                    alive,
                    fmt,
                    str(packet.get("raw") or ""),
                ),
            )

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
                """INSERT INTO tracks(
                       callsign,timestamp,latitude,longitude,speed,course,altitude,path,raw,rssi,snr
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    callsign, now, float(lat), float(lon),
                    packet.get("speed"), packet.get("course"), packet.get("altitude"),
                    values["path"], values["raw"], packet.get("rssi"), packet.get("snr"),
                ),
            )


def upsert_station(packet: dict[str, Any]) -> None:
    with connection() as conn:
        _upsert_station_conn(conn, packet)
    invalidate_map_data_cache(drop_payload=False)

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


def _interaction_calls_conn(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        """
        SELECT from_call AS callsign
          FROM messages
         WHERE direction='in' AND message_type='message'
        UNION
        SELECT to_call AS callsign
          FROM messages
         WHERE direction='out' AND status IN ('ACK','REJ')
        UNION
        SELECT peer AS callsign
          FROM aprs_queries
         WHERE direction='in'
            OR (direction='out' AND response_at IS NOT NULL AND status='RESPONDIDA')
        """
    ).fetchall()
    return {
        str(row["callsign"] or "").upper().strip()
        for row in rows
        if str(row["callsign"] or "").strip()
    }


def _infrastructure_calls_conn(conn: sqlite3.Connection) -> set[str]:
    """Retorna somente indicativos observados exercendo papel de digi/iGate.

    O path solicitado pela estação de origem (ex.: WIDE1-1,WIDE2-1) não entra
    nesta evidência. Um indicativo só aparece aqui quando foi observado como
    hop intermediário efetivamente usado ou como iGate de um q-construct.
    """
    rows = conn.execute(
        """
        SELECT DISTINCT callsign
          FROM (
                SELECT UPPER(TRIM(target)) AS callsign
                  FROM topology_edges
                 WHERE kind='rf' AND target IS NOT NULL AND TRIM(target) <> ''
                UNION
                SELECT UPPER(TRIM(igate)) AS callsign
                  FROM topology_edges
                 WHERE igate IS NOT NULL AND TRIM(igate) <> ''
               )
         WHERE callsign IS NOT NULL AND callsign <> ''
        """
    ).fetchall()
    return {
        str(row["callsign"] or "").upper().strip()
        for row in rows
        if str(row["callsign"] or "").strip()
    }


def list_stations(filter_text: str = "") -> list[dict[str, Any]]:
    cfg = get_config()
    own_lat = cfg.get("latitude")
    own_lon = cfg.get("longitude")
    q = "%" + filter_text.upper().strip() + "%"
    with connection() as conn:
        interaction_calls = _interaction_calls_conn(conn)
        infrastructure_calls = _infrastructure_calls_conn(conn)
        rows = conn.execute(
            """
            SELECT s.*,
                   CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
              FROM stations s
              LEFT JOIN favorites f ON f.callsign=s.callsign
             WHERE UPPER(s.callsign) LIKE ?
                OR UPPER(COALESCE(s.name,'')) LIKE ?
                OR UPPER(COALESCE(s.info,'')) LIKE ?
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
        item["interaction_evidence"] = 1 if (
            bool(item.get("message_capable")) or call in interaction_calls
        ) else 0
        item["infrastructure_evidence"] = 1 if call in infrastructure_calls else 0
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


def _observed_topology_edges(
    raw: str,
    medium: str | None = None,
) -> tuple[str, list[tuple[str, str, str, str | None]]]:
    """Retorna a origem e os enlaces observáveis no path APRS/TNC2.

    Quando o transporte que entregou o pacote é conhecido como RF, essa
    evidência prevalece sobre o papel de iGate/q-construct: um iGate continua
    sendo um nó, não um meio de transporte.
    """
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

        # q-construct case is semantically significant. qAR/qAO are
        # direct RF gate evidence; qAr and the remaining qA* variants are
        # Internet/APRS-IS routing evidence. TCPIP/TCPXX elsewhere in the
        # header must not erase an RF hop already proven by qAR/qAO.
        direct_rf_gate = token in {"qAR", "qAO"}
        observed_medium = str(medium or "").upper().strip()
        kind = "rf" if observed_medium == "RF" or direct_rf_gate else "igate"
        edges.append((previous, candidate, kind, candidate))
        break
    return source, edges



def _record_topology_from_raw_conn(
    conn: sqlite3.Connection,
    raw: str,
    medium: str = "APRS-IS",
) -> None:
    """Registra relações observáveis preservando a evidência real do transporte."""
    observed_medium = str(medium or "APRS-IS").upper().strip()
    if observed_medium not in {"RF", "APRS-IS"}:
        observed_medium = "APRS-IS"
    _source, edges = _observed_topology_edges(raw, observed_medium)
    if not edges:
        return
    now = utc_now_iso()

    for edge_source, target, kind, edge_igate in edges:
        rf_transport = 1 if observed_medium == "RF" and kind == "rf" else 0
        rf_path = 1 if observed_medium != "RF" and kind == "rf" else 0
        internet_confirmed = 1 if observed_medium == "APRS-IS" and kind == "igate" else 0
        conn.execute(
            """
            INSERT INTO topology_edges(
                source,target,kind,packet_count,first_seen,last_seen,igate,
                rf_transport_count,rf_path_count,internet_confirmed_count
            )
            VALUES(?,?,?,1,?,?,?,?,?,?)
            ON CONFLICT(source,target,kind) DO UPDATE SET
                packet_count=topology_edges.packet_count+1,
                last_seen=excluded.last_seen,
                igate=COALESCE(excluded.igate, topology_edges.igate),
                rf_transport_count=topology_edges.rf_transport_count+excluded.rf_transport_count,
                rf_path_count=topology_edges.rf_path_count+excluded.rf_path_count,
                internet_confirmed_count=topology_edges.internet_confirmed_count+excluded.internet_confirmed_count
            """,
            (
                edge_source, target, kind, now, now, edge_igate,
                rf_transport, rf_path, internet_confirmed,
            ),
        )
        conn.execute(
            "INSERT INTO topology_events(timestamp,source,target,kind) VALUES(?,?,?,?)",
            (now, edge_source, target, kind),
        )
    if _retention_due("topology_events", len(edges)):
        deleted = _trim_history_table(conn, "topology_events", TOPOLOGY_EVENT_RETENTION)
        if deleted:
            diag.log_event("retention_sweep", table="topology_events", deleted=deleted)


def record_topology_from_raw(raw: str, medium: str = "APRS-IS") -> None:
    """Registra relações observáveis preservando o meio de recepção conhecido."""
    with connection() as conn:
        _record_topology_from_raw_conn(conn, raw, medium)

def _consolidate_topology_edges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Consolida duplicatas sem apagar evidência APRS-IS confirmada.

    Um mesmo par origem→destino pode ter sido observado fisicamente por RF e,
    em outro momento, ter chegado por APRS-IS. Esses fatos não são mutuamente
    exclusivos. A consolidação mantém uma linha por meio observado:

    - rf continua sendo enlace físico e nunca vira Internet por o destino
      exercer papel de iGate;
    - igate existe somente quando houve evidência positiva APRS-IS;
    - pares mistos preservam ambos os enlaces e seus contadores, permitindo à
      interface desenhar RF sólido e Internet tracejado sem esconder nenhum.
    """
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_kind: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    for raw in rows:
        item = dict(raw)
        source = str(item.get("source") or "").upper().strip()
        target = str(item.get("target") or "").upper().strip()
        if not source or not target:
            continue
        kind = "igate" if str(item.get("kind") or "").lower() == "igate" else "rf"
        item["source"] = source
        item["target"] = target
        item["kind"] = kind
        by_pair.setdefault((source, target), []).append(item)
        by_kind.setdefault((source, target, kind), []).append(item)

    result: list[dict[str, Any]] = []
    for (source, target, kind), same_kind_rows in by_kind.items():
        pair_rows = by_pair[(source, target)]
        rf_rows = [row for row in pair_rows if row["kind"] == "rf"]
        internet_rows = [row for row in pair_rows if row["kind"] == "igate"]

        base = dict(max(same_kind_rows, key=lambda row: str(row.get("last_seen") or "")))
        base["source"] = source
        base["target"] = target
        base["kind"] = kind
        base["packet_count"] = sum(int(row.get("packet_count") or 0) for row in same_kind_rows)
        base["rf_packet_count"] = sum(int(row.get("packet_count") or 0) for row in rf_rows)
        base["internet_packet_count"] = sum(int(row.get("packet_count") or 0) for row in internet_rows)
        base["rf_transport_count"] = sum(int(row.get("rf_transport_count") or 0) for row in pair_rows)
        base["rf_path_count"] = sum(int(row.get("rf_path_count") or 0) for row in pair_rows)
        base["internet_confirmed_count"] = sum(int(row.get("internet_confirmed_count") or 0) for row in pair_rows)
        base["mixed_evidence"] = bool(rf_rows and internet_rows)
        base["observed_kinds"] = [
            observed_kind
            for observed_kind, kind_rows in (("rf", rf_rows), ("igate", internet_rows))
            if kind_rows
        ]

        if kind == "igate":
            base["classification_source"] = "APRS-IS confirmado"
        elif base["rf_transport_count"] > 0:
            base["classification_source"] = "RF direto do transporte"
        else:
            base["classification_source"] = "RF inferido do path"

        first_values = [
            str(row.get("first_seen") or "")
            for row in same_kind_rows
            if row.get("first_seen")
        ]
        last_values = [
            str(row.get("last_seen") or "")
            for row in same_kind_rows
            if row.get("last_seen")
        ]
        if first_values:
            base["first_seen"] = min(first_values)
        if last_values:
            base["last_seen"] = max(last_values)
        result.append(base)

    # RF primeiro, APRS-IS depois para que o tracejado permaneça visível em
    # pares mistos. O frontend reforça a mesma ordem ao renderizar.
    result.sort(
        key=lambda item: (
            str(item.get("source") or ""),
            str(item.get("target") or ""),
            1 if str(item.get("kind") or "") == "igate" else 0,
        )
    )
    return result

def _repair_topology_rf_evidence_v112(conn: sqlite3.Connection) -> int:
    """Reconstrói uma vez a evidência RF usando o histórico de packets.medium=RF."""
    key = "v1.12.0-topology-rf-medium-repair"
    if conn.execute(
        "SELECT 1 FROM schema_migrations_v112 WHERE migration_key=?",
        (key,),
    ).fetchone():
        return 0

    aggregated: dict[tuple[str, str, str, str | None], int] = {}
    rows = conn.execute(
        """SELECT raw FROM packets
           WHERE UPPER(COALESCE(medium,''))='RF'
           ORDER BY id ASC"""
    ).fetchall()
    for row in rows:
        _source, edges = _observed_topology_edges(str(row["raw"] or ""), "RF")
        for edge in edges:
            aggregated[edge] = aggregated.get(edge, 0) + 1

    now = utc_now_iso()
    for (edge_source, target, kind, edge_igate), count in aggregated.items():
        if kind != "rf" or count <= 0:
            continue
        existing = conn.execute(
            """SELECT packet_count,first_seen,last_seen,rf_transport_count
               FROM topology_edges WHERE source=? AND target=? AND kind='rf'""",
            (edge_source, target),
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE topology_edges
                   SET packet_count=MAX(packet_count,?),
                       rf_transport_count=MAX(rf_transport_count,?),
                       igate=COALESCE(igate,?),
                       last_seen=MAX(last_seen,?)
                   WHERE source=? AND target=? AND kind='rf'""",
                (count, count, edge_igate, now, edge_source, target),
            )
        else:
            conn.execute(
                """INSERT INTO topology_edges(
                       source,target,kind,packet_count,first_seen,last_seen,igate,
                       rf_transport_count,rf_path_count,internet_confirmed_count
                   ) VALUES(?,?,'rf',?,?,?,?,?,0,0)""",
                (edge_source, target, count, now, now, edge_igate, count),
            )

    conn.execute(
        "INSERT INTO schema_migrations_v112(migration_key,applied_at) VALUES(?,?)",
        (key, now),
    )
    return len(aggregated)


def list_topology_edges(hours: float = 0) -> list[dict[str, Any]]:
    """Retorna enlaces observados sem permitir que uma consulta monopolize workers HTTP."""
    global _topology_cache_db_path
    try:
        hours = float(hours or 0)
    except (TypeError, ValueError):
        hours = 0.0
    if hours > 0:
        hours = max(0.25, min(hours, 24 * 30))
    else:
        hours = 0.0

    now = time.monotonic()
    with _topology_cache_lock:
        if _topology_cache_db_path != str(DB_PATH):
            # Não reutilizar resultado de outro banco (testes, restauração,
            # seleção de diretório de dados ou migração).
            _topology_cache.clear()
            _topology_cache_db_path = str(DB_PATH)
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
                           e.rf_transport_count,e.rf_path_count,e.internet_confirmed_count,
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

        valid_rows = []
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
            valid_rows.append(item)

        # RF e APRS-IS são evidências independentes. Um par observado pelos
        # dois meios deve retornar as duas linhas; nenhum meio apaga o outro.
        result = _consolidate_topology_edges(valid_rows)
        with _topology_cache_lock:
            _topology_cache[hours] = (time.monotonic(), result)

        elapsed_ms = (time.monotonic() - started) * 1000
        if elapsed_ms >= 250:
            diag.log_event("topology_query_slow", hours=hours, duration_ms=round(elapsed_ms, 1), rows=len(result))
        return [dict(item) for item in result]
    finally:
        _topology_query_lock.release()



def _rf_route_callsign(value: Any) -> str:
    """Normaliza indicativos usados pela análise de rotas RF."""
    call = str(value or "").upper().strip()
    if not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", call):
        return ""
    return call



RF_CONFIRMED_SHORT_KM = float(os.getenv("PT2VHF_RF_CONFIRMED_SHORT_KM", "250"))
RF_CONFIRMED_MEDIUM_KM = float(os.getenv("PT2VHF_RF_CONFIRMED_MEDIUM_KM", "600"))
RF_CONFIRMED_LONG_KM = float(os.getenv("PT2VHF_RF_CONFIRMED_LONG_KM", "1000"))
RF_CONFIRMED_MEDIUM_OBS = int(os.getenv("PT2VHF_RF_CONFIRMED_MEDIUM_OBS", "2"))
RF_CONFIRMED_LONG_OBS = int(os.getenv("PT2VHF_RF_CONFIRMED_LONG_OBS", "5"))
RF_CONFIRMED_EXCEPTIONAL_OBS = int(os.getenv("PT2VHF_RF_CONFIRMED_EXCEPTIONAL_OBS", "20"))
RF_PATH_CONFIRMED_MAX_KM = float(os.getenv("PT2VHF_RF_PATH_CONFIRMED_MAX_KM", "80"))
RF_PATH_CONFIRMED_OBS = int(os.getenv("PT2VHF_RF_PATH_CONFIRMED_OBS", "3"))


def _rf_edge_confidence(raw: dict[str, Any], distance_km: float) -> dict[str, Any]:
    """Classifica a confiança RF sem apagar a evidência bruta observada."""
    rf_transport = int(raw.get("rf_transport_count") or 0)
    rf_path = int(raw.get("rf_path_count") or 0)
    internet = int(raw.get("internet_confirmed_count") or 0)
    packets = int(raw.get("packet_count") or 0)
    evidence = max(rf_transport, rf_path, packets)

    if internet > 0 and rf_transport <= 0 and rf_path <= 0:
        return {
            "level": "internet",
            "label": "Internet/APRS-IS",
            "confirmed": False,
            "score": 0,
            "reason": "evidência explícita de transporte APRS-IS",
        }

    if rf_transport > 0:
        if distance_km <= RF_CONFIRMED_SHORT_KM:
            return {
                "level": "confirmed",
                "label": "RF confirmado",
                "confirmed": True,
                "score": 100,
                "reason": f"recebido via TNC/RF; trecho de {distance_km:.1f} km",
            }
        if distance_km <= RF_CONFIRMED_MEDIUM_KM:
            if rf_transport >= RF_CONFIRMED_MEDIUM_OBS:
                return {
                    "level": "confirmed",
                    "label": "RF confirmado",
                    "confirmed": True,
                    "score": 92,
                    "reason": f"{rf_transport} recepções via TNC/RF; trecho de {distance_km:.1f} km",
                }
            return {
                "level": "probable",
                "label": "RF provável",
                "confirmed": False,
                "score": 68,
                "reason": f"trecho de {distance_km:.1f} km com apenas {rf_transport} evidência direta",
            }
        if distance_km <= RF_CONFIRMED_LONG_KM:
            if rf_transport >= RF_CONFIRMED_LONG_OBS:
                return {
                    "level": "confirmed",
                    "label": "RF confirmado",
                    "confirmed": True,
                    "score": 86,
                    "reason": f"{rf_transport} recepções diretas sustentam trecho longo de {distance_km:.1f} km",
                }
            return {
                "level": "inconsistent",
                "label": "RF inconsistente",
                "confirmed": False,
                "score": 38,
                "reason": f"{distance_km:.1f} km sem evidência direta repetida suficiente",
            }
        if rf_transport >= RF_CONFIRMED_EXCEPTIONAL_OBS:
            return {
                "level": "confirmed",
                "label": "RF confirmado",
                "confirmed": True,
                "score": 80,
                "reason": f"propagação excepcional sustentada por {rf_transport} recepções diretas",
            }
        return {
            "level": "inconsistent",
            "label": "RF inconsistente",
            "confirmed": False,
            "score": 20,
            "reason": f"{distance_km:.1f} km com somente {rf_transport} evidências diretas; requer confirmação excepcional",
        }

    if rf_path > 0:
        if distance_km <= RF_PATH_CONFIRMED_MAX_KM and rf_path >= RF_PATH_CONFIRMED_OBS:
            return {
                "level": "confirmed",
                "label": "RF confirmado",
                "confirmed": True,
                "score": 82,
                "reason": f"path RF repetido {rf_path} vezes em trecho curto de {distance_km:.1f} km",
            }
        if distance_km <= RF_CONFIRMED_SHORT_KM:
            return {
                "level": "probable",
                "label": "RF provável",
                "confirmed": False,
                "score": 60,
                "reason": f"RF inferido do path; {rf_path} observações em {distance_km:.1f} km",
            }
        return {
            "level": "inconsistent",
            "label": "RF inconsistente",
            "confirmed": False,
            "score": 25,
            "reason": f"RF apenas inferido do path em trecho de {distance_km:.1f} km",
        }

    return {
        "level": "inconsistent",
        "label": "RF inconsistente",
        "confirmed": False,
        "score": 10,
        "reason": f"sem evidência RF positiva suficiente ({evidence} observações legadas)",
    }


def _rf_route_graph(hours: float = 0) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, tuple[float, float]]]:
    """Monta grafo não-direcional apenas com enlaces que possuem evidência RF real."""
    graph: dict[str, dict[str, dict[str, Any]]] = {}
    positions: dict[str, tuple[float, float]] = {}
    merged: dict[tuple[str, str], dict[str, Any]] = {}

    for raw in list_topology_edges(hours):
        if str(raw.get("kind") or "").lower() == "igate":
            continue
        source = _rf_route_callsign(raw.get("source"))
        target = _rf_route_callsign(raw.get("target"))
        if not source or not target or source == target:
            continue
        if int(raw.get("rf_transport_count") or 0) <= 0 and int(raw.get("rf_path_count") or 0) <= 0:
            # Linhas RF antigas podem não ter os novos contadores; nesse caso a
            # própria classificação kind='rf' continua sendo a evidência legada.
            if str(raw.get("kind") or "").lower() != "rf":
                continue

        slat = raw.get("source_lat")
        slon = raw.get("source_lon")
        tlat = raw.get("target_lat")
        tlon = raw.get("target_lon")
        if not (_valid_geo_position(slat, slon) and _valid_geo_position(tlat, tlon)):
            continue
        positions[source] = (float(slat), float(slon))
        positions[target] = (float(tlat), float(tlon))

        a, b = sorted((source, target))
        item = merged.get((a, b))
        distance = round(haversine_km(*positions[source], *positions[target]), 3)
        confidence = _rf_edge_confidence(raw, distance)
        candidate = {
            "a": a,
            "b": b,
            "packet_count": int(raw.get("packet_count") or 0),
            "first_seen": str(raw.get("first_seen") or ""),
            "last_seen": str(raw.get("last_seen") or ""),
            "distance_km": distance,
            "classification_source": str(raw.get("classification_source") or "RF observado"),
            "rf_transport_count": int(raw.get("rf_transport_count") or 0),
            "rf_path_count": int(raw.get("rf_path_count") or 0),
            "internet_confirmed_count": int(raw.get("internet_confirmed_count") or 0),
            "rf_confidence": confidence["level"],
            "rf_confidence_label": confidence["label"],
            "rf_confidence_score": confidence["score"],
            "rf_confidence_reason": confidence["reason"],
            "rf_confirmed": bool(confidence["confirmed"]),
        }
        if item is None:
            merged[(a, b)] = candidate
        else:
            item["packet_count"] = int(item.get("packet_count") or 0) + candidate["packet_count"]
            item["rf_transport_count"] = int(item.get("rf_transport_count") or 0) + candidate["rf_transport_count"]
            item["rf_path_count"] = int(item.get("rf_path_count") or 0) + candidate["rf_path_count"]
            item["internet_confirmed_count"] = int(item.get("internet_confirmed_count") or 0) + candidate["internet_confirmed_count"]
            merged_confidence = _rf_edge_confidence(item, float(item.get("distance_km") or distance))
            item["rf_confidence"] = merged_confidence["level"]
            item["rf_confidence_label"] = merged_confidence["label"]
            item["rf_confidence_score"] = merged_confidence["score"]
            item["rf_confidence_reason"] = merged_confidence["reason"]
            item["rf_confirmed"] = bool(merged_confidence["confirmed"])
            first_values = [x for x in (item.get("first_seen"), candidate["first_seen"]) if x]
            last_values = [x for x in (item.get("last_seen"), candidate["last_seen"]) if x]
            item["first_seen"] = min(first_values) if first_values else ""
            item["last_seen"] = max(last_values) if last_values else ""

    for (a, b), edge in merged.items():
        if not bool(edge.get("rf_confirmed")):
            continue
        graph.setdefault(a, {})[b] = edge
        graph.setdefault(b, {})[a] = edge
    return graph, positions


def list_rf_route_candidates(source: str, hours: float = 0, query: str = "", limit: int = 80) -> list[dict[str, Any]]:
    """Estações alcançáveis por um caminho composto exclusivamente por enlaces RF observados."""
    source_call = _rf_route_callsign(source)
    if not source_call:
        return []
    query_norm = str(query or "").upper().strip()
    graph, _positions = _rf_route_graph(hours)
    if source_call not in graph:
        return []

    queue: list[tuple[str, int]] = [(source_call, 0)]
    visited = {source_call}
    candidates: list[dict[str, Any]] = []
    while queue:
        node, hops = queue.pop(0)
        neighbors = sorted(
            graph.get(node, {}).items(),
            key=lambda pair: (str(pair[1].get("last_seen") or ""), int(pair[1].get("packet_count") or 0)),
            reverse=True,
        )
        for nxt, edge in neighbors:
            if nxt in visited:
                continue
            visited.add(nxt)
            next_hops = hops + 1
            queue.append((nxt, next_hops))
            if query_norm and query_norm not in nxt:
                continue
            candidates.append({
                "callsign": nxt,
                "hops": next_hops,
                "last_seen": str(edge.get("last_seen") or ""),
                "packet_count": int(edge.get("packet_count") or 0),
            })

    candidates.sort(key=lambda item: (
        0 if query_norm and str(item["callsign"]).startswith(query_norm) else 1,
        -int(item.get("packet_count") or 0),
        int(item.get("hops") or 0),
        str(item.get("callsign") or ""),
    ))
    return candidates[: max(1, min(int(limit or 80), 200))]



def list_rf_route_origins(hours: float = 0, query: str = "", limit: int = 80) -> list[dict[str, Any]]:
    """Indicativos conhecidos que participam do grafo RF observável no período."""
    graph, _positions = _rf_route_graph(hours)
    query_norm = str(query or "").upper().strip()
    rows: list[dict[str, Any]] = []
    for callsign, neighbors in graph.items():
        if query_norm and query_norm not in callsign:
            continue
        packet_count = sum(int(edge.get("packet_count") or 0) for edge in neighbors.values())
        latest = max((str(edge.get("last_seen") or "") for edge in neighbors.values()), default="")
        rows.append({
            "callsign": callsign,
            "links": len(neighbors),
            "packet_count": packet_count,
            "last_seen": latest,
        })
    rows.sort(key=lambda item: (
        0 if query_norm and str(item["callsign"]).startswith(query_norm) else 1,
        -int(item.get("packet_count") or 0),
        -int(item.get("links") or 0),
        str(item.get("callsign") or ""),
    ))
    return rows[: max(1, min(int(limit or 80), 200))]


def _rf_route_payload(
    nodes: list[str],
    graph: dict[str, dict[str, dict[str, Any]]],
    positions: dict[str, tuple[float, float]],
) -> dict[str, Any] | None:
    if len(nodes) < 2:
        return None
    route_edges: list[dict[str, Any]] = []
    total = 0.0
    latest_values: list[str] = []
    observations = 0
    for index in range(len(nodes) - 1):
        a, b = nodes[index], nodes[index + 1]
        edge = graph.get(a, {}).get(b)
        if not edge or a not in positions or b not in positions:
            return None
        distance = float(edge.get("distance_km") or 0.0)
        total += distance
        observations += int(edge.get("packet_count") or 0)
        if edge.get("last_seen"):
            latest_values.append(str(edge["last_seen"]))
        route_edges.append({
            "source": a,
            "target": b,
            "source_lat": positions[a][0],
            "source_lon": positions[a][1],
            "target_lat": positions[b][0],
            "target_lon": positions[b][1],
            "distance_km": round(distance, 3),
            "packet_count": int(edge.get("packet_count") or 0),
            "first_seen": edge.get("first_seen") or "",
            "last_seen": edge.get("last_seen") or "",
            "classification_source": edge.get("classification_source") or "RF observado",
            "rf_confidence": edge.get("rf_confidence") or "confirmed",
            "rf_confidence_label": edge.get("rf_confidence_label") or "RF confirmado",
            "rf_confidence_score": int(edge.get("rf_confidence_score") or 0),
            "rf_confidence_reason": edge.get("rf_confidence_reason") or "",
        })
    direct = round(haversine_km(*positions[nodes[0]], *positions[nodes[-1]]), 3)
    return {
        "source": nodes[0],
        "target": nodes[-1],
        "nodes": nodes,
        "hops": len(nodes) - 1,
        "distance_km": round(total, 3),
        "direct_distance_km": direct,
        "route_evidence_at": min(latest_values) if latest_values else "",
        "observations": observations,
        "rf_confidence": "confirmed",
        "rf_confidence_label": "RF confirmado",
        "rf_confidence_reason": "todos os trechos da rota possuem evidência RF confirmada",
        "edges": route_edges,
    }


def list_rf_route_records(
    hours: float = 0,
    limit: int = 10,
    max_hops: int = 6,
    beam_width: int = 500,
) -> list[dict[str, Any]]:
    """Ranking de pares de estações mais distantes ligados por RF completo.

    O critério do ranking é a distância geográfica direta entre as duas estações
    extremas. A distância percorrida pela sequência de hops permanece apenas como
    informação complementar. Cada par origem/destino aparece uma única vez.
    """
    graph, positions = _rf_route_graph(hours)
    route_limit = max(1, min(int(limit or 10), 50))
    hop_limit = max(1, min(int(max_hops or 6), 10))

    candidates: list[tuple[float, int, int, str, list[str]]] = []

    # Uma BFS por origem produz um caminho RF completo de menor número de hops para
    # cada destino alcançável dentro do limite. Como o grafo é não-direcional,
    # mantemos somente source < target para não duplicar A↔B e B↔A.
    for source in sorted(graph):
        if source not in positions:
            continue
        queue: list[list[str]] = [[source]]
        visited = {source}
        while queue:
            path = queue.pop(0)
            node = path[-1]
            hops = len(path) - 1
            if hops >= hop_limit:
                continue

            neighbors = sorted(
                graph.get(node, {}).items(),
                key=lambda pair: (
                    str(pair[1].get("last_seen") or ""),
                    int(pair[1].get("packet_count") or 0),
                ),
                reverse=True,
            )
            for nxt, _edge in neighbors:
                if nxt in visited:
                    continue
                visited.add(nxt)
                next_path = path + [nxt]
                queue.append(next_path)

                if nxt not in positions or source >= nxt:
                    continue

                payload = _rf_route_payload(next_path, graph, positions)
                if not payload:
                    continue
                candidates.append((
                    float(payload.get("direct_distance_km") or 0.0),
                    int(payload.get("observations") or 0),
                    -int(payload.get("hops") or 0),
                    str(payload.get("route_evidence_at") or ""),
                    next_path,
                ))

    candidates.sort(
        key=lambda item: (item[0], item[1], item[2], item[3]),
        reverse=True,
    )

    result: list[dict[str, Any]] = []
    emitted_pairs: set[tuple[str, str]] = set()
    for _direct, _obs, _neg_hops, _evidence, path in candidates:
        pair = tuple(sorted((path[0], path[-1])))
        if pair in emitted_pairs:
            continue
        payload = _rf_route_payload(path, graph, positions)
        if not payload:
            continue
        emitted_pairs.add(pair)
        payload["rank"] = len(result) + 1
        result.append(payload)
        if len(result) >= route_limit:
            break
    return result

def list_rf_routes(
    source: str,
    target: str,
    hours: float = 0,
    max_routes: int = 12,
    max_hops: int = 8,
) -> dict[str, Any]:
    """Lista caminhos simples entre dois indicativos usando somente enlaces RF observados."""
    source_call = _rf_route_callsign(source)
    target_call = _rf_route_callsign(target)
    if not source_call or not target_call or source_call == target_call:
        return {"source": source_call, "target": target_call, "direct_distance_km": None, "routes": []}

    graph, positions = _rf_route_graph(hours)
    if source_call not in graph or target_call not in graph:
        direct = None
        if source_call in positions and target_call in positions:
            direct = round(haversine_km(*positions[source_call], *positions[target_call]), 3)
        return {"source": source_call, "target": target_call, "direct_distance_km": direct, "routes": []}

    route_limit = max(1, min(int(max_routes or 12), 25))
    hop_limit = max(1, min(int(max_hops or 8), 12))
    found: list[list[str]] = []

    def walk(node: str, path: list[str]) -> None:
        if len(found) >= route_limit * 4:
            return
        hops = len(path) - 1
        if hops >= hop_limit:
            return
        neighbors = sorted(
            graph.get(node, {}).items(),
            key=lambda pair: (str(pair[1].get("last_seen") or ""), int(pair[1].get("packet_count") or 0)),
            reverse=True,
        )
        for nxt, _edge in neighbors:
            if nxt in path:
                continue
            next_path = path + [nxt]
            if nxt == target_call:
                found.append(next_path)
                continue
            walk(nxt, next_path)

    walk(source_call, [source_call])

    routes: list[dict[str, Any]] = []
    for nodes in found:
        payload = _rf_route_payload(nodes, graph, positions)
        if payload:
            routes.append(payload)

    # Rotas mais recentes/consistentes primeiro; em empate, menos hops e menor distância.
    routes.sort(key=lambda item: (
        str(item.get("route_evidence_at") or ""),
        -int(item.get("observations") or 0),
        -int(item.get("hops") or 0),
        -float(item.get("distance_km") or 0.0),
    ), reverse=True)

    direct_distance = None
    if source_call in positions and target_call in positions:
        direct_distance = round(haversine_km(*positions[source_call], *positions[target_call]), 3)

    return {
        "source": source_call,
        "target": target_call,
        "direct_distance_km": direct_distance,
        "routes": routes[:route_limit],
    }


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
        return {"identifier": "", "friendly_name": "Não identificado", "identified": False, "features": []}

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
            "features": [],
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
        "features": [str(item) for item in (best.get("features") or []) if str(item).strip()],
    }


def _aprs_map_family(resolved: dict[str, Any], descriptor: str, role: str) -> tuple[str, str]:
    """Normaliza o tipo/família usado no filtro Ver do mapa."""
    model = str(resolved.get("model") or resolved.get("friendly_name") or "").strip()
    vendor = str(resolved.get("vendor") or "").strip()
    device_class = str(resolved.get("class") or "").strip().lower()
    text = " ".join(part for part in (model, vendor, descriptor) if part).upper()

    # Famílias funcionais amplas que o usuário precisa conseguir ocultar de uma vez.
    if re.search(r"RDZ|SONDE|RADIOSONDE", text):
        return "rdzsonde", "RDZSonDe"
    if "BRAVO TRACKER" in text:
        return "bravo-tracker", "Bravo Tracker"
    if device_class == "dstar" or re.search(r"\bD-?STAR\b|DSTAR|D-APRS", text):
        # HBLink é mais útil como família própria do que escondido em D-Star.
        if "HBLINK" in text:
            return "hblink-daprs-gateway", "HBLink D-APRS Gateway"
        return "d-star", "D-Star"
    if re.search(r"\bDMR\b|BRANDMEISTER|MOTOTRBO", text):
        return "dmr", "DMR"
    if "HBLINK" in text:
        return "hblink-daprs-gateway", "HBLink D-APRS Gateway"

    if model:
        _, display = _canonical_client_family(model)
        display = re.sub(r"\s+", " ", display).strip()
        if display:
            key = re.sub(r"[^0-9a-z]+", "-", display.casefold()).strip("-") or "unknown"
            return key, display

    if vendor:
        display = re.sub(r"\s+", " ", vendor).strip()
        key = re.sub(r"[^0-9a-z]+", "-", display.casefold()).strip("-") or "unknown"
        return key, display

    class_labels = {
        "network": "Equipamento de rede",
        "rig": "Rádio / Rig",
        "software": "Software",
        "app": "Aplicativo móvel",
        "daemon": "Software em segundo plano",
        "digi": "Digipeater",
        "gadget": "Gadget",
        "wx": "Estação meteorológica",
        "igate": "iGate",
        "satellite": "Satélite",
        "service": "Serviço / Bot",
        "ht": "HT",
        "tracker": "Tracker",
    }
    label = class_labels.get(device_class) or ("Digipeater" if role == "digi" else ("iGate" if role == "igate" else "Não identificado"))
    key = re.sub(r"[^0-9a-z]+", "-", label.casefold()).strip("-") or "unknown"
    return key, label


def aprs_map_device_metadata(raw: str, info: str = "", symbol: str = "") -> dict[str, Any]:
    """Classificação leve para filtros hierárquicos do mapa."""
    tocall = _aprs_tocall_from_raw(raw)
    resolved = resolve_aprs_device_id(tocall)
    device_class = str(resolved.get("class") or "").strip().lower()
    vendor = str(resolved.get("vendor") or "").strip()
    model = str(resolved.get("model") or resolved.get("friendly_name") or "").strip()
    features = [str(item) for item in (resolved.get("features") or []) if str(item).strip()]

    descriptor = " ".join(
        part for part in (
            device_class,
            vendor,
            model,
            str(info or ""),
            str(raw or ""),
        ) if part
    ).upper()

    has_digi = device_class == "digi" or bool(
        re.search(r"\bDIGI(?:PEATER)?\b|\bDIGI\b|UIDIGI|VP-DIGI|DIGI_NED", descriptor)
    )
    has_igate = device_class == "igate" or bool(
        re.search(
            r"\bI-?GATE\b|\bIGATE\b|APRS[- ]?IS GATEWAY|"
            r"\bLORA\b.*\bGATEWAY\b|\bGATEWAY\b.*\bDIGI",
            descriptor,
        )
    )
    is_lora = "LORA" in descriptor

    # A classe oficial do aprs-deviceid é o critério principal para híbridos.
    if device_class == "digi" or (has_digi and not has_igate):
        role = "digi"
    elif device_class == "igate" or (has_igate and not has_digi):
        role = "igate"
    elif has_digi and has_igate:
        role = "digi" if str(symbol or "") == "#" else "igate"
    else:
        role = "station"

    if role in {"digi", "igate"}:
        if has_digi and has_igate:
            subtype = "hybrid"
        elif is_lora:
            subtype = "lora"
        elif resolved.get("identified"):
            subtype = "conventional"
        else:
            subtype = "unknown"
    else:
        subtype = device_class or "unknown"

    family_key, family_label = _aprs_map_family(resolved, descriptor, role)

    return {
        "device_tocall": tocall,
        "device_identified": bool(resolved.get("identified")),
        "device_class": device_class or "unknown",
        "device_vendor": vendor,
        "device_model": model,
        "device_os": str(resolved.get("os") or "").strip(),
        "device_features": features,
        "map_role": role,
        "map_subtype": subtype,
        "map_family_key": family_key,
        "map_family_label": family_label,
    }


def aprs_object_map_metadata(
    name: str,
    info: str = "",
    symbol_table: str = "/",
    symbol: str = "",
    packet_format: str = "object",
) -> dict[str, Any]:
    """Classifica um objeto APRS pela semântica do próprio objeto.

    Não usa o TOCALL/cliente da estação publicadora para evitar que software
    como Dire Wolf, D-Star gateway etc. apareça simultaneamente em Estações e
    Objetos apenas por ter publicado o objeto.
    """
    object_name = re.sub(r"\s+", " ", str(name or "").strip())
    object_info = re.sub(r"\s+", " ", str(info or "").strip())
    descriptor = f"{object_name} {object_info}".upper()
    sym = str(symbol or "")[:1]
    fmt = str(packet_format or "").lower().strip()

    if re.search(r"\bAIS\b|AIS[-_ ]?APRS|AIS2APRS|AISGATE|AISHUB|\bMMSI\s*[:=#-]?\s*\d{7,9}\b", descriptor):
        key, label = "ais", "AIS"
    elif re.search(r"\bRDZ\b|RDZSONDE", descriptor):
        key, label = "rdzsonde", "RDZSonDe"
    elif re.search(r"RADIOSONDE|SONDE|\bBALLOON\b|\bBALAO\b|\bBALÃO\b", descriptor) or sym == "O":
        key, label = "balloon", "Balão / Radiossonda"
    elif re.search(r"\bDMR\b|BRANDMEISTER|MOTOTRBO", descriptor):
        key, label = "dmr", "DMR"
    elif re.search(r"\bD-?STAR\b|DSTAR|D-APRS", descriptor):
        key, label = "d-star", "D-Star"
    elif re.search(r"\bREPEATER\b|\bREPETIDOR\b|\bRPT\b", descriptor):
        key, label = "repeater", "Repetidor"
    elif re.search(r"\bWEATHER\b|\bWX\b|METEO", descriptor) or sym == "_":
        key, label = "weather", "Estação meteorológica"
    elif re.search(r"\bALERT\b|\bALERTA\b|\bNWS\b|EMERGENCY", descriptor):
        key, label = "alert", "Alerta"
    elif fmt == "item":
        key, label = "aprs-item", "Item APRS"
    else:
        key, label = "other-object", "Outros objetos"

    return {
        "device_tocall": "",
        "device_identified": False,
        "device_class": "object",
        "device_vendor": "",
        "device_model": "",
        "device_os": "",
        "device_features": [],
        "map_role": "object",
        "map_subtype": key,
        "map_family_key": key,
        "map_family_label": label,
    }


def _object_first_number(text: str, patterns: list[str]) -> float | None:
    source = str(text or "")
    for pattern in patterns:
        match = re.search(pattern, source, re.I)
        if not match:
            continue
        try:
            return float(str(match.group(1)).replace(",", "."))
        except (TypeError, ValueError):
            continue
    return None


def _object_first_text(text: str, patterns: list[str]) -> str:
    source = str(text or "")
    for pattern in patterns:
        match = re.search(pattern, source, re.I)
        if match:
            return re.sub(r"\s+", " ", str(match.group(1) or "").strip())
    return ""


def _object_path(value: Any, raw: str = "") -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return [item.strip() for item in value.split(",") if item.strip()]
    line = str(raw or "").strip()
    if ">" in line and ":" in line:
        header = line.split(":", 1)[0].split(">", 1)[1]
        parts = [part.strip() for part in header.split(",") if part.strip()]
        return parts[1:] if len(parts) > 1 else []
    return []


def aprs_object_friendly_details(item: dict[str, Any]) -> dict[str, Any]:
    """Normaliza metadados úteis de objetos APRS para apresentação amigável."""
    info = str(item.get("info") or "")
    comment = str(item.get("comment") or "")
    status = str(item.get("status") or "")
    raw = str(item.get("raw") or "")
    text = " | ".join(part for part in (info, comment, status, raw) if part)
    subtype = str(item.get("map_family_key") or item.get("map_subtype") or "other-object")

    try:
        weather = json.loads(str(item.get("weather_json") or "{}"))
        if not isinstance(weather, dict):
            weather = {}
    except Exception:
        weather = {}

    frequency = _object_first_number(text, [
        r"\b(?:FREQ(?:UENCY)?|FRQ)\s*[:=#-]?\s*(\d{2,4}(?:[.,]\d{1,5})?)\s*(?:MHZ)?\b",
        r"\b(\d{3}(?:[.,]\d{2,5}))\s*MHZ\b",
    ])
    vertical_speed = _object_first_number(text, [
        r"\b(?:VSPD|VSPEED|VERTICAL(?:\s+SPEED)?|CLB|ASCENT|SUBIDA)\s*[:=]?\s*([+-]?\d+(?:[.,]\d+)?)\s*(?:M/S|MPS)?\b",
    ])
    descent = _object_first_number(text, [
        r"\b(?:DESCENT|DESCIDA)\s*[:=]?\s*([+-]?\d+(?:[.,]\d+)?)\s*(?:M/S|MPS)?\b",
    ])
    if vertical_speed is None and descent is not None:
        vertical_speed = -abs(descent)

    mmsi = _object_first_text(text, [r"\bMMSI\s*[:=#-]?\s*(\d{7,9})\b"])
    imo = _object_first_text(text, [r"\bIMO\s*[:=#-]?\s*(\d{7})\b"])
    vessel_name = _object_first_text(text, [
        r"\b(?:VESSEL(?:\s+NAME)?|SHIP(?:\s+NAME)?|NAVIO|EMBARCA(?:CAO|ÇÃO)|NAME|NOME)\s*[:=]\s*([^|;,]+)"
    ])
    vessel_callsign = _object_first_text(text, [
        r"\b(?:CALLSIGN|CALL\s*SIGN|INDICATIVO)\s*[:=]\s*([A-Z0-9-]{3,10})\b"
    ])
    vessel_type = _object_first_text(text, [
        r"\b(?:SHIP\s*TYPE|VESSEL\s*TYPE|TYPE|TIPO)\s*[:=]\s*([^|;,]+)"
    ])
    nav_status = _object_first_text(text, [
        r"\b(?:NAV(?:IGATION)?\s*STATUS|NAVSTAT|STATUS\s*NAV|ESTADO\s*NAV)\s*[:=]\s*([^|;,]+)"
    ])
    destination = _object_first_text(text, [
        r"\b(?:DEST(?:INATION)?|DESTINO)\s*[:=]\s*([^|;,]+)"
    ])
    eta = _object_first_text(text, [
        r"\bETA\s*[:=]\s*([^|;,]+)"
    ])
    draught = _object_first_number(text, [
        r"\b(?:DRAUGHT|DRAFT|CALADO)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:M|METERS?|METROS?)?\b"
    ])
    heading = _object_first_number(text, [
        r"\b(?:HEADING|HDG|PROA)\s*[:=]?\s*(\d{1,3}(?:[.,]\d+)?)\b"
    ])
    ship_length = _object_first_number(text, [
        r"\b(?:LENGTH|LEN|COMPRIMENTO)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:M|METERS?|METROS?)?\b"
    ])
    ship_width = _object_first_number(text, [
        r"\b(?:WIDTH|BEAM|LARGURA|BOCA)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:M|METERS?|METROS?)?\b"
    ])
    sog_knots = _object_first_number(text, [
        r"\bSOG\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:KT|KTS|KNOTS?|NOS|NÓS)?\b"
    ])
    offset = _object_first_number(text, [
        r"\b(?:OFFSET|OFF)\s*[:=]?\s*([+-]?\d+(?:[.,]\d+)?)\s*(?:KHZ)?\b"
    ])
    tone = _object_first_number(text, [
        r"\b(?:CTCSS|TONE|TOM)\s*[:=]?\s*(\d{2,3}(?:[.,]\d+)?)\b"
    ])

    speed = item.get("speed")
    course = item.get("course")
    if speed in (None, ""):
        speed = _object_first_number(text, [
            r"\b(?:SOG|SPEED|SPD|VELOCIDADE)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:KM/H|KPH)?\b"
        ])
    if course in (None, ""):
        course = _object_first_number(text, [
            r"\b(?:COG|COURSE|HEADING|HDG|CURSO)\s*[:=]?\s*(\d{1,3}(?:[.,]\d+)?)\b"
        ])

    temperature = weather.get("temperature")
    humidity = weather.get("humidity")
    pressure = weather.get("pressure")
    wind_speed = weather.get("wind_speed")
    wind_gust = weather.get("wind_gust")
    wind_direction = weather.get("wind_direction")
    rain_1h = weather.get("rain_1h")
    rain_24h = weather.get("rain_24h")

    if temperature in (None, ""):
        temperature = _object_first_number(text, [
            r"\b(?:TEMP(?:ERATURE)?|TEMPERATURA)\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)"
        ])
    if humidity in (None, ""):
        humidity = _object_first_number(text, [
            r"\b(?:HUM(?:IDITY)?|UMIDADE|UR)\s*[:=]?\s*(\d{1,3}(?:[.,]\d+)?)"
        ])
    if pressure in (None, ""):
        pressure = _object_first_number(text, [
            r"\b(?:PRESS(?:URE)?|PRESSAO|PRESSÃO)\s*[:=]?\s*(\d{1,4}(?:[.,]\d+)?)"
        ])

    flight_state = ""
    if vertical_speed is not None:
        if vertical_speed > 0.2:
            flight_state = "ascending"
        elif vertical_speed < -0.2:
            flight_state = "descending"
        else:
            flight_state = "level"
    elif int(item.get("alive") if item.get("alive") is not None else 1) == 0:
        flight_state = "inactive"

    return {
        "subtype": subtype,
        "frequency_mhz": frequency,
        "vertical_speed_ms": vertical_speed,
        "flight_state": flight_state,
        "speed_kmh": speed,
        "course_deg": course,
        "mmsi": mmsi,
        "imo": imo,
        "vessel_name": vessel_name,
        "vessel_callsign": vessel_callsign,
        "vessel_type": vessel_type,
        "nav_status": nav_status,
        "destination": destination,
        "eta": eta,
        "draught_m": draught,
        "heading_deg": heading,
        "length_m": ship_length,
        "width_m": ship_width,
        "speed_knots": sog_knots,
        "offset_khz": offset,
        "tone_hz": tone,
        "temperature_c": temperature,
        "humidity_percent": humidity,
        "pressure_hpa": pressure,
        "wind_speed_kmh": wind_speed,
        "wind_gust_kmh": wind_gust,
        "wind_direction_deg": wind_direction,
        "rain_1h_mm": rain_1h,
        "rain_24h_mm": rain_24h,
        "path": _object_path(item.get("path"), raw),
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


APRS_APPLICATION_CLASSES = {"software", "app", "daemon", "service"}
APRS_DEVICE_CLASSES = {
    "network", "rig", "dstar", "digi", "gadget", "wx",
    "igate", "satellite", "ht", "tracker",
}
APRS_APPLICATION_NAME_HINTS = (
    "dire wolf", "direwolf", "ui-view", "uiview", "winaprs",
    "aprsdroid", "xastir", "yaac", "aprsisce", "pinpoint",
    "pt2vhf aprs client",
)


def _aprs_client_category(resolved: dict[str, Any]) -> str:
    """Classifica uma identificação APRS sem misturar software e hardware."""
    device_class = str(resolved.get("class") or "").strip().lower()
    os_name = str(resolved.get("os") or "").strip().lower()
    friendly = " ".join(
        part for part in (
            str(resolved.get("friendly_name") or ""),
            str(resolved.get("model") or ""),
            str(resolved.get("vendor") or ""),
        ) if part
    ).casefold()

    if device_class in APRS_APPLICATION_CLASSES:
        return "application"
    if device_class in APRS_DEVICE_CLASSES:
        return "device"

    if os_name:
        if "embedded" in os_name or "firmware" in os_name:
            return "device"
        if any(token in os_name for token in ("windows", "linux", "android", "ios", "mac", "cross-platform")):
            return "application"

    if any(hint in friendly for hint in APRS_APPLICATION_NAME_HINTS):
        return "application"

    return "unknown"


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
                "categories": set(),
                "is_own_client": False,
            }
            grouped[friendly_key] = bucket

        bucket["stations"] = int(bucket["stations"]) + 1
        bucket["identifiers"].add(tocall)
        bucket["aliases"].add(source_name)
        bucket["categories"].add(_aprs_client_category(resolved))
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

    category_counts = {"application": 0, "device": 0, "unknown": 0}
    items: list[dict[str, Any]] = []
    for rank, bucket in enumerate(ranked, start=1):
        identifiers = sorted(str(value) for value in bucket["identifiers"])
        is_own = bool(bucket["is_own_client"]) or APP_TOCALL in identifiers
        identifier = APP_TOCALL if is_own and APP_TOCALL in identifiers else identifiers[0]
        meta = dict(bucket["meta"] or {})
        count = int(bucket["stations"])
        concrete_categories = {str(value) for value in bucket.get("categories", set()) if str(value) in {"application", "device"}}
        if len(concrete_categories) == 1:
            category = next(iter(concrete_categories))
        elif len(concrete_categories) > 1:
            category = "unknown"
        else:
            category = "unknown"
        category_counts[category] += count
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
            "category": category,
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
            "category": "application",
            "stations": 0,
            "percent": 0.0,
            "is_own_client": True,
        }

    return {
        "hours": 0 if hours <= 0 else hours,
        "total_stations": len(rows),
        "identified_stations": identified_total,
        "unidentified_stations": unidentified,
        "category_counts": {
            **category_counts,
            "unidentified": unidentified,
        },
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
        excluded_set = {
            str(r["callsign"] or "").upper().strip()
            for r in infrastructure_rows
            if r["callsign"]
        }

        # Também classifica pelo próprio pacote mais recente da estação. Isso
        # elimina iGates/digis que ainda não apareceram como alvo de um enlace
        # no banco de topologia, evitando que sejam misturados no ranking.
        station_meta: dict[str, dict[str, Any]] = {}
        station_last_heard: dict[str, str] = {}
        for station_row in conn.execute(
            "SELECT callsign,raw,info,symbol,last_heard FROM stations"
        ).fetchall():
            call = str(station_row["callsign"] or "").upper().strip()
            if not call:
                continue
            meta = aprs_map_device_metadata(
                str(station_row["raw"] or ""),
                str(station_row["info"] or ""),
                str(station_row["symbol"] or ""),
            )
            station_meta[call] = meta
            station_last_heard[call] = str(station_row["last_heard"] or "")
            if str(meta.get("map_role") or "") in {"digi", "igate"}:
                excluded_set.add(call)

        excluded_calls = sorted(call for call in excluded_set if call)

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
                   SUM(CASE WHEN UPPER(COALESCE(p.medium,'APRS-IS'))='RF' THEN 1 ELSE 0 END) AS rf_packets,
                   SUM(CASE WHEN UPPER(COALESCE(p.medium,'APRS-IS'))='APRS-IS' THEN 1 ELSE 0 END) AS aprsis_packets,
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
                "rf_packets": int(row["rf_packets"] or 0),
                "aprsis_packets": int(row["aprsis_packets"] or 0),
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
    manual_rows = [
        item for item in manual_conversation_stats(0 if complete else hours, limit=100)
        if str(item.get("callsign") or "").upper().strip() not in excluded_set
    ]
    manual_by_call = {
        str(item.get("callsign") or "").upper().strip(): item
        for item in manual_rows
        if str(item.get("callsign") or "").strip()
    }
    active_by_call = {
        str(row["callsign"] or "").upper().strip(): row
        for row in active_rows
        if str(row["callsign"] or "").strip()
    }

    station_calls = sorted(set(active_by_call) | set(manual_by_call))
    station_rankings: list[dict[str, Any]] = []
    for call in station_calls:
        if call in excluded_set:
            continue
        active = active_by_call.get(call)
        manual = manual_by_call.get(call) or {}
        packets = int(active["packets"] or 0) if active is not None else 0
        rf_packets = int(active["rf_packets"] or 0) if active is not None else 0
        aprsis_packets = int(active["aprsis_packets"] or 0) if active is not None else 0
        interactions = int(manual.get("interactions") or 0)
        meta = station_meta.get(call) or {}
        application = str(
            meta.get("map_family_label")
            or meta.get("device_model")
            or meta.get("device_class")
            or ""
        ).strip()
        last_seen = (
            str(active["last_seen"] or "") if active is not None
            else str(station_last_heard.get(call) or "")
        )
        station_rankings.append({
            "callsign": call,
            "packets": packets,
            "rf_packets": rf_packets,
            "aprsis_packets": aprsis_packets,
            "media": (
                "RF + APRS-IS" if rf_packets and aprsis_packets
                else "RF" if rf_packets
                else "APRS-IS" if aprsis_packets
                else ""
            ),
            "interactions": interactions,
            "sent": int(manual.get("sent") or 0),
            "received": int(manual.get("received") or 0),
            "peers": int(manual.get("peers") or 0),
            "last_seen": last_seen,
            "application": application,
        })

    station_rankings.sort(
        key=lambda item: (
            -int(item.get("packets") or 0),
            -int(item.get("interactions") or 0),
            str(item.get("callsign") or ""),
        )
    )
    for rank, item in enumerate(station_rankings[:50], start=1):
        item["rank"] = rank
    station_rankings = station_rankings[:50]

    return {
        "hours": 0 if complete else hours,
        "complete": complete,
        "edges": int(totals["edges"] or 0),
        "packets": int(totals["packets"] or 0),
        "active_stations": active_stations,
        "active_station_packets": eligible_packets,
        "manual_conversations": manual_rows[:20],
        "station_rankings": station_rankings,
        "digipeaters": digis,
        "igates": igates,
        "recently_disappeared": stale,
        "problem_stations": station_problem_stats(0 if complete else hours),
        "improvement_suggestions": network_improvement_suggestions(0 if complete else hours),
        "rf_route_records": list_rf_route_records(0 if complete else hours, limit=10, max_hops=6),
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

        # APRS-IS is a network service, not a geographic point. When a q-construct
        # identifies the receiving iGate, add a logical handoff anchored at the
        # iGate itself so the UI can animate the Internet transition without
        # inventing a fake map coordinate.
        raw_text = str(row["raw"] or "")
        header = raw_text.split(":", 1)[0] if ":" in raw_text else raw_text
        route = header.split(">", 1)[1].split(",")[1:] if ">" in header else []
        for idx, token in enumerate(route):
            token = token.strip()
            if not re.fullmatch(r"qA[A-Za-z]", token) or idx + 1 >= len(route):
                continue
            gate = route[idx + 1].strip().rstrip("*").upper()
            gate_coord = coords.get(gate)
            if gate_coord:
                segments.append({
                    "source": gate,
                    "target": "APRS-IS",
                    "kind": "igate",
                    "internet_handoff": True,
                    "source_lat": gate_coord[0],
                    "source_lon": gate_coord[1],
                    "target_lat": None,
                    "target_lon": None,
                })
            break
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
        deleted = max(0, int(cur.rowcount or 0))
    invalidate_map_data_cache(drop_payload=True)
    return deleted


def clear_stations() -> dict[str, int]:
    with connection() as conn:
        tracks_cur = conn.execute("DELETE FROM tracks")
        topology_cur = conn.execute("DELETE FROM topology_edges")
        stations_cur = conn.execute("DELETE FROM stations")
        result = {
            "stations": max(0, int(stations_cur.rowcount or 0)),
            "tracks": max(0, int(tracks_cur.rowcount or 0)),
            "topology": max(0, int(topology_cur.rowcount or 0)),
        }
    invalidate_map_data_cache(drop_payload=True)
    return result


def _map_data_result(payload: dict[str, Any], *, source: str, age_ms: float = 0.0, busy: bool = False) -> dict[str, Any]:
    result = dict(payload)
    result["_meta"] = {
        "source": source,
        "cache_age_ms": round(max(0.0, age_ms), 1),
        "build_ms": round(max(0.0, float(_map_data_cache_build_ms)), 1),
        "busy": bool(busy),
    }
    return result


def invalidate_map_data_cache(*, drop_payload: bool = False, coalesce: bool = False) -> None:
    """Invalidate explicit changes immediately; coalesce only continuous RX.

    Position/track changes from APRS RX arrive continuously. Resetting the
    cache age for every received packet forced a full map rebuild on virtually
    every frontend poll. The RX pipeline may request coalescing until the short
    cache TTL, while explicit station edits and destructive operations remain
    immediately visible.
    """
    global _map_data_cache_payload, _map_data_cache_at, _map_data_cache_build_ms, _map_data_cache_db_path
    with _map_data_cache_lock:
        db_key = str(DB_PATH)
        if _map_data_cache_db_path != db_key:
            _map_data_cache_payload = None
            _map_data_cache_at = 0.0
            _map_data_cache_build_ms = 0.0
        _map_data_cache_db_path = db_key
        if drop_payload:
            _map_data_cache_payload = None
            _map_data_cache_at = 0.0
            _map_data_cache_build_ms = 0.0
        elif not coalesce:
            _map_data_cache_at = 0.0


def _build_map_data_uncached() -> dict[str, Any]:
    with connection() as conn:
        # Resolve interaction evidence once for the whole dataset. The previous
        # query ran three correlated EXISTS subqueries for every station, which
        # becomes very expensive as messages/aprs_queries grow.
        interaction_calls = _interaction_calls_conn(conn)
        infrastructure_calls = _infrastructure_calls_conn(conn)

        station_rows = conn.execute(
            """
            SELECT s.*,
                   CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
              FROM stations s
              LEFT JOIN favorites f ON f.callsign=s.callsign
             WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
             ORDER BY favorite DESC, s.last_heard DESC
            """
        ).fetchall()

        issues = _station_position_issues_conn(conn, station_rows)
        stations: list[dict[str, Any]] = []
        valid_calls: set[str] = set()
        for row in station_rows:
            item = dict(row)
            call = str(item.get("callsign") or "").upper().strip()
            if call in issues or not _valid_geo_position(item.get("latitude"), item.get("longitude")):
                continue
            item["interaction_evidence"] = 1 if (
                bool(item.get("message_capable")) or call in interaction_calls
            ) else 0
            item["infrastructure_evidence"] = 1 if call in infrastructure_calls else 0
            item["position_valid"] = True
            item["position_issue"] = ""
            item.update(aprs_map_device_metadata(
                str(item.get("raw") or ""),
                str(item.get("info") or ""),
                str(item.get("symbol") or ""),
            ))
            stations.append(item)
            valid_calls.add(call)

        # Últimos 10 mil pontos; o frontend agrupa por estação.
        tracks = [
            dict(row)
            for row in conn.execute(
                """SELECT callsign,timestamp,latitude,longitude,speed,course,altitude,
                          path,raw,rssi,snr
                     FROM tracks
                    ORDER BY id DESC
                    LIMIT 10000"""
            ).fetchall()
        ]

        objects: list[dict[str, Any]] = []
        for row in conn.execute(
            """SELECT name,source_callsign,first_heard,last_heard,latitude,longitude,
                      altitude,max_altitude,speed,course,symbol_table,symbol,info,
                      comment,status,path,weather_json,alive,packet_format,raw
                 FROM aprs_objects
                ORDER BY last_heard DESC
                LIMIT 5000"""
        ).fetchall():
            if not _valid_geo_position(row["latitude"], row["longitude"]):
                continue
            item = dict(row)
            item.update(aprs_object_map_metadata(
                str(item.get("name") or ""),
                str(item.get("info") or ""),
                str(item.get("symbol_table") or "/"),
                str(item.get("symbol") or ""),
                str(item.get("packet_format") or "object"),
            ))
            item["friendly_details"] = aprs_object_friendly_details(item)
            objects.append(item)

    tracks = [
        row
        for row in reversed(tracks)
        if str(row.get("callsign") or "").upper().strip() in valid_calls
        and _valid_geo_position(row.get("latitude"), row.get("longitude"))
    ]
    return {"stations": stations, "objects": objects, "tracks": tracks}


def map_data(*, force: bool = False) -> dict[str, Any]:
    global _map_data_cache_payload, _map_data_cache_at, _map_data_cache_build_ms, _map_data_cache_db_path

    now = time.monotonic()
    db_key = str(DB_PATH)
    with _map_data_cache_lock:
        if _map_data_cache_db_path != db_key:
            cached = None
            cached_at = 0.0
        else:
            cached = _map_data_cache_payload
            cached_at = float(_map_data_cache_at)
    age = now - cached_at if cached is not None and cached_at > 0 else float("inf")
    if not force and cached is not None and age < MAP_DATA_CACHE_SECONDS:
        return _map_data_result(cached, source="cache", age_ms=age * 1000.0)

    owner = _map_data_build_lock.acquire(blocking=False)
    if not owner:
        # Never queue another expensive map query behind an existing one.
        # Serving a stale snapshot is preferable to consuming another Waitress worker.
        if cached is not None:
            return _map_data_result(cached, source="stale-cache", age_ms=age * 1000.0, busy=True)
        owner = _map_data_build_lock.acquire(timeout=MAP_DATA_INITIAL_WAIT_SECONDS)
        if not owner:
            diag.log_event("map_data_singleflight_busy", cache_available=False)
            return _map_data_result(
                {"stations": [], "objects": [], "tracks": []},
                source="busy-empty",
                busy=True,
            )

    try:
        # Another thread may have completed the build while this caller waited.
        now = time.monotonic()
        with _map_data_cache_lock:
            if _map_data_cache_db_path != db_key:
                cached = None
                cached_at = 0.0
            else:
                cached = _map_data_cache_payload
                cached_at = float(_map_data_cache_at)
        age = now - cached_at if cached is not None and cached_at > 0 else float("inf")
        if not force and cached is not None and age < MAP_DATA_CACHE_SECONDS:
            return _map_data_result(cached, source="cache-after-wait", age_ms=age * 1000.0)

        started = time.monotonic()
        payload = _build_map_data_uncached()
        build_ms = (time.monotonic() - started) * 1000.0
        with _map_data_cache_lock:
            _map_data_cache_payload = payload
            _map_data_cache_at = time.monotonic()
            _map_data_cache_build_ms = build_ms
            _map_data_cache_db_path = db_key
        diag.log_event(
            "map_data_build",
            duration_ms=round(build_ms, 1),
            stations=len(payload.get("stations") or []),
            objects=len(payload.get("objects") or []),
            tracks=len(payload.get("tracks") or []),
        )
        return _map_data_result(payload, source="fresh", age_ms=0.0)
    finally:
        _map_data_build_lock.release()


def geographic_export_data(hours: float = 0) -> dict[str, Any]:
    try:
        hours = float(hours or 0)
    except (TypeError, ValueError):
        hours = 0.0
    if hours > 0:
        hours = max(0.25, min(hours, 24 * 30))
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



def list_rf_received_by(receiver: str, hours: float = 0, limit: int = 100) -> list[dict[str, Any]]:
    """Estações comprovadamente observadas chegando ao nó por enlace RF."""
    receiver = str(receiver or "").upper().strip()
    if not receiver:
        return []
    limit = max(1, min(int(limit or 100), 500))
    params: list[Any] = [receiver]
    where = ""
    try:
        safe_hours = float(hours or 0)
    except (TypeError, ValueError):
        safe_hours = 0.0
    if safe_hours > 0:
        safe_hours = max(0.25, min(safe_hours, 24 * 30))
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=safe_hours)).isoformat(timespec="seconds")
        where = "AND last_seen >= ?"
        params.append(cutoff)
    params.append(limit)
    with connection() as conn:
        rows = conn.execute(
            f"""
            SELECT UPPER(TRIM(source)) AS callsign,
                   SUM(packet_count) AS packets,
                   MAX(last_seen) AS last_seen
            FROM topology_edges
            WHERE UPPER(TRIM(target))=?
              AND kind='rf'
              AND UPPER(TRIM(source)) <> UPPER(TRIM(target))
              {where}
            GROUP BY UPPER(TRIM(source))
            ORDER BY packets DESC, last_seen DESC, callsign
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


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
                part_count: int | None = None, retry_count: int = 0,
                tx_medium: str | None = None, tx_path: str | None = None,
                automated: bool = False) -> int:
    message_type = str(message_type or "message").strip().lower()
    if message_type not in {"message", "bulletin", "group_bulletin"}:
        message_type = "message"
    with connection() as conn:
        cur = conn.execute(
            """INSERT INTO messages(direction,from_call,to_call,message,message_type,msg_id,status,
                                    message_group_id,part_index,part_count,retry_count,tx_medium,tx_path,automated,timestamp,raw)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                direction, from_call.upper(), to_call.upper(), message, message_type, msg_id, status,
                message_group_id, part_index, part_count, max(0, int(retry_count or 0)),
                str(tx_medium or "").upper() or None, str(tx_path or "").upper() or None,
                1 if automated else 0, utc_now_iso(), raw,
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
                                        message_group_id,part_index,part_count,retry_count,tx_medium,tx_path,automated,timestamp,raw)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
                    str(row.get("tx_medium") or "").upper() or None,
                    str(row.get("tx_path") or "").upper() or None,
                    1 if bool(row.get("automated")) else 0,
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
    *,
    medium: str = "APRS-IS",
) -> None:
    """Persiste o pipeline RX principal em uma única conexão/transação SQLite."""
    started = time.monotonic()
    with connection() as conn:
        _add_aprs_log_conn(conn, "RX", raw)
        _record_packet_conn(conn, raw, from_call, packet_format, medium=medium)
        _record_topology_from_raw_conn(conn, raw, medium)
        if parsed and parsed.get("from"):
            _upsert_station_conn(conn, parsed)
    if parsed and parsed.get("from"):
        invalidate_map_data_cache(drop_payload=False, coalesce=True)
    elapsed_ms = (time.monotonic() - started) * 1000
    if elapsed_ms >= 250:
        diag.log_event(
            "rx_transaction_slow",
            duration_ms=round(elapsed_ms, 1),
            from_call=from_call or "",
            packet_format=packet_format or "",
            medium=str(medium or "APRS-IS").upper(),
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


# --- Scheduled APRS messages (v1.8.17) ---

def _json_callsigns(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            value = re.split(r"[,;\s]+", value)
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value:
        call = str(item or "").upper().strip()
        if not call or not re.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", call):
            continue
        if call not in result:
            result.append(call)
    return result[:200]


def list_recipient_groups() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM recipient_groups ORDER BY name COLLATE NOCASE").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["callsigns"] = _json_callsigns(item.pop("callsigns_json", "[]"))
        result.append(item)
    return result


def save_recipient_group(data: dict[str, Any], group_id: int | None = None) -> dict[str, Any]:
    name = str(data.get("name") or "").strip()
    callsigns = _json_callsigns(data.get("callsigns") or data.get("callsigns_json") or [])
    if not name:
        raise ValueError("Informe um nome para a lista de destinatários.")
    if not callsigns:
        raise ValueError("Informe pelo menos um indicativo válido.")
    now = utc_now_iso()
    payload = json.dumps(callsigns, ensure_ascii=False)
    with connection() as conn:
        if group_id:
            cur = conn.execute(
                "UPDATE recipient_groups SET name=?,callsigns_json=?,updated_at=? WHERE id=?",
                (name, payload, now, int(group_id)),
            )
            if not cur.rowcount:
                raise ValueError("Lista de destinatários não encontrada.")
            ident = int(group_id)
        else:
            cur = conn.execute(
                "INSERT INTO recipient_groups(name,callsigns_json,created_at,updated_at) VALUES(?,?,?,?)",
                (name, payload, now, now),
            )
            ident = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM recipient_groups WHERE id=?", (ident,)).fetchone()
    item = dict(row)
    item["callsigns"] = _json_callsigns(item.pop("callsigns_json", "[]"))
    return item


def delete_recipient_group(group_id: int) -> int:
    with connection() as conn:
        cur = conn.execute("DELETE FROM recipient_groups WHERE id=?", (int(group_id),))
        return int(cur.rowcount or 0)


def _scheduled_row(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    item["enabled"] = bool(item.get("enabled"))
    item["continue_on_error"] = bool(item.get("continue_on_error"))
    item["targets"] = _json_callsigns(item.pop("targets_json", "[]"))
    item["retry_targets"] = _json_callsigns(item.pop("retry_targets_json", "[]"))
    return item


def list_scheduled_messages() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_messages ORDER BY enabled DESC, COALESCE(next_run_at,'9999') ASC, id DESC"
        ).fetchall()
    return [_scheduled_row(row) for row in rows]


def get_scheduled_message(schedule_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM scheduled_messages WHERE id=?", (int(schedule_id),)).fetchone()
    return _scheduled_row(row) if row else None


def save_scheduled_message(data: dict[str, Any], schedule_id: int | None = None) -> dict[str, Any]:
    now = utc_now_iso()
    schedule_type = str(data.get("schedule_type") or "once").lower().strip()
    target_type = str(data.get("target_type") or "station").lower().strip()
    message_type = str(data.get("message_type") or "message").lower().strip()
    route = str(data.get("route") or "auto").lower().strip()
    retry_policy = str(data.get("retry_policy") or "skip").lower().strip()
    if schedule_type not in {"once", "weekly"}:
        raise ValueError("Tipo de agendamento inválido.")
    if target_type not in {"station", "list", "bulletin", "group"}:
        raise ValueError("Tipo de destino inválido.")
    if message_type not in {"message", "bulletin", "announcement", "group_bulletin"}:
        raise ValueError("Tipo de mensagem inválido.")
    if route not in {"auto", "aprs_is", "rf_direct", "rf_custom"}:
        raise ValueError("Rota de envio inválida.")
    if retry_policy not in {"skip", "retry"}:
        raise ValueError("Política de falha inválida.")
    message = str(data.get("message") or "").strip()
    if not message:
        raise ValueError("Informe a mensagem.")
    target = str(data.get("target") or "").upper().strip()
    targets = _json_callsigns(data.get("targets") or [])
    recipient_group_id = data.get("recipient_group_id") or None
    if target_type == "station" and not _json_callsigns([target]):
        raise ValueError("Informe um destino APRS válido.")
    if target_type == "list" and not targets and not recipient_group_id:
        raise ValueError("Informe os destinatários ou selecione uma lista salva.")
    if target_type == "group":
        aprs_group = str(data.get("aprs_group") or target or "").upper().strip()
        bulletin_id = str(data.get("bulletin_id") or "0").upper().strip()[:1]
        if not re.fullmatch(r"[A-Z0-9]{1,5}", aprs_group):
            raise ValueError("Informe um grupo APRS válido com 1 a 5 caracteres.")
        if not bulletin_id.isdigit():
            raise ValueError("Boletim de grupo deve usar linha BLN0 a BLN9; anúncios BLN[A-Z] não usam grupo.")
    run_at_utc = str(data.get("run_at_utc") or "").strip() or None
    weekday = data.get("weekday")
    weekday = int(weekday) if weekday not in ("", None) else None
    time_local = str(data.get("time_local") or "").strip() or None
    if schedule_type == "once" and not run_at_utc:
        raise ValueError("Informe a data e hora do envio único.")
    if schedule_type == "weekly":
        if weekday is None or weekday < 0 or weekday > 6:
            raise ValueError("Dia da semana inválido.")
        if not time_local or not re.fullmatch(r"\d{2}:\d{2}", time_local):
            raise ValueError("Horário semanal inválido.")

    fields = {
        "name": str(data.get("name") or "").strip(),
        "enabled": 1 if bool(data.get("enabled", True)) else 0,
        "schedule_type": schedule_type,
        "run_at_utc": run_at_utc,
        "weekday": weekday,
        "time_local": time_local,
        "target_type": target_type,
        "target": target,
        "targets_json": json.dumps(targets, ensure_ascii=False),
        "retry_targets_json": "[]",
        "recipient_group_id": int(recipient_group_id) if recipient_group_id else None,
        "message_type": message_type,
        "message": message,
        "route": route,
        "path": str(data.get("path") or "").upper().strip(),
        "bulletin_id": str(data.get("bulletin_id") or "0").upper().strip()[:1],
        "aprs_group": str(data.get("aprs_group") or "").upper().strip()[:5],
        "interval_seconds": max(1, min(120, int(data.get("interval_seconds") or 3))),
        "retry_policy": retry_policy,
        "retry_minutes": max(1, min(1440, int(data.get("retry_minutes") or 10))),
        "continue_on_error": 1 if bool(data.get("continue_on_error", True)) else 0,
        "next_run_at": str(data.get("next_run_at") or "").strip() or None,
    }
    with connection() as conn:
        if schedule_id:
            assignments = ",".join(f"{key}=?" for key in fields)
            cur = conn.execute(
                f"UPDATE scheduled_messages SET {assignments},updated_at=? WHERE id=?",
                [*fields.values(), now, int(schedule_id)],
            )
            if not cur.rowcount:
                raise ValueError("Agendamento não encontrado.")
            ident = int(schedule_id)
        else:
            keys = list(fields)
            cur = conn.execute(
                f"INSERT INTO scheduled_messages({','.join(keys)},created_at,updated_at) "
                f"VALUES({','.join('?' for _ in keys)},?,?)",
                [*fields.values(), now, now],
            )
            ident = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM scheduled_messages WHERE id=?", (ident,)).fetchone()
    return _scheduled_row(row)


def delete_scheduled_message(schedule_id: int) -> int:
    with connection() as conn:
        cur = conn.execute("DELETE FROM scheduled_messages WHERE id=?", (int(schedule_id),))
        return int(cur.rowcount or 0)


def set_scheduled_enabled(schedule_id: int, enabled: bool, next_run_at: str | None = None) -> int:
    with connection() as conn:
        cur = conn.execute(
            "UPDATE scheduled_messages SET enabled=?,next_run_at=?,updated_at=? WHERE id=?",
            (1 if enabled else 0, next_run_at, utc_now_iso(), int(schedule_id)),
        )
        return int(cur.rowcount or 0)


def claim_due_scheduled_message(now_iso: str) -> dict[str, Any] | None:
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM scheduled_messages WHERE enabled=1 AND next_run_at IS NOT NULL "
            "AND next_run_at<=? ORDER BY next_run_at,id LIMIT 1",
            (str(now_iso),),
        ).fetchone()
        if not row:
            return None
        schedule_id = int(row["id"])
        occurrence = str(row["next_run_at"] or "")
        conn.execute(
            "UPDATE scheduled_messages SET next_run_at=NULL,last_occurrence_key=?,last_status='running',"
            "last_error='',updated_at=? WHERE id=? AND next_run_at=?",
            (occurrence, utc_now_iso(), schedule_id, occurrence),
        )
        fresh = conn.execute("SELECT * FROM scheduled_messages WHERE id=?", (schedule_id,)).fetchone()
    return _scheduled_row(fresh) if fresh else None


def complete_scheduled_message(
    schedule_id: int,
    *,
    status: str,
    error: str = "",
    summary: str = "",
    next_run_at: str | None = None,
    enabled: bool | None = None,
    retry_targets: list[str] | None = None,
) -> None:
    now = utc_now_iso()
    fields = ["last_run_at=?", "last_status=?", "last_error=?", "last_summary=?", "next_run_at=?", "updated_at=?"]
    values: list[Any] = [now, str(status), str(error)[:1000], str(summary)[:4000], next_run_at, now]
    if retry_targets is not None:
        fields.append("retry_targets_json=?")
        values.append(json.dumps(_json_callsigns(retry_targets), ensure_ascii=False))
    if enabled is not None:
        fields.append("enabled=?")
        values.append(1 if enabled else 0)
    values.append(int(schedule_id))
    with connection() as conn:
        conn.execute(f"UPDATE scheduled_messages SET {','.join(fields)} WHERE id=?", values)
