from __future__ import annotations

import io
import json
import os
import shutil
import sqlite3
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import jsonify, request, send_file

from . import __version__
from . import database as db
from .aprs_service import service
from .tnc_service import get_tnc_config, probe_transport, service as tnc_service


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_schema() -> None:
    with db.connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS station_groups_v190 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                color TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS station_meta_v190 (
                callsign TEXT PRIMARY KEY,
                friendly_name TEXT NOT NULL DEFAULT '',
                color TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                group_id INTEGER,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(group_id) REFERENCES station_groups_v190(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS settings_v190 (
                key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


def _json_setting(key: str, default: dict[str, Any]) -> dict[str, Any]:
    _ensure_schema()
    with db.connection() as conn:
        row = conn.execute("SELECT payload FROM settings_v190 WHERE key=?", (key,)).fetchone()
    if not row:
        return dict(default)
    try:
        value = json.loads(row["payload"])
        return value if isinstance(value, dict) else dict(default)
    except Exception:
        return dict(default)


def _save_json_setting(key: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_schema()
    clean = dict(payload or {})
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO settings_v190(key,payload,updated_at) VALUES(?,?,?)
               ON CONFLICT(key) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at""",
            (key, json.dumps(clean, ensure_ascii=False, sort_keys=True), _utc()),
        )
    return clean


def _global_search(query: str, limit: int = 30) -> list[dict[str, Any]]:
    _ensure_schema()
    q = str(query or "").strip()
    if not q:
        return []
    like = f"%{q.upper()}%"
    exact = q.upper()
    max_rows = max(1, min(int(limit or 30), 100))
    out: list[dict[str, Any]] = []
    with db.connection() as conn:
        station_rows = conn.execute(
            """SELECT s.callsign,s.name,s.last_heard,s.latitude,s.longitude,s.info,s.path,
                      s.message_capable,COALESCE(m.friendly_name,'') AS friendly_name,
                      COALESCE(m.color,'') AS color,COALESCE(m.note,'') AS note,
                      g.name AS group_name,
                      CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
               FROM stations s
               LEFT JOIN favorites f ON f.callsign=s.callsign
               LEFT JOIN station_meta_v190 m ON m.callsign=s.callsign
               LEFT JOIN station_groups_v190 g ON g.id=m.group_id
               WHERE UPPER(s.callsign) LIKE ?
                  OR UPPER(COALESCE(s.name,'')) LIKE ?
                  OR UPPER(COALESCE(s.info,'')) LIKE ?
                  OR UPPER(COALESCE(m.friendly_name,'')) LIKE ?
                  OR UPPER(COALESCE(m.note,'')) LIKE ?
                  OR UPPER(COALESCE(g.name,'')) LIKE ?
               ORDER BY CASE WHEN UPPER(s.callsign)=? THEN 0 ELSE 1 END,
                        favorite DESC,s.last_heard DESC
               LIMIT ?""",
            (like, like, like, like, like, like, exact, max_rows),
        ).fetchall()
        for row in station_rows:
            item = dict(row)
            item["entity_type"] = "station"
            item["key"] = item["callsign"]
            out.append(item)

        remain = max(0, max_rows - len(out))
        if remain:
            object_rows = conn.execute(
                """SELECT name,source_callsign,last_heard,latitude,longitude,info,comment,status,
                          packet_format,symbol_table,symbol
                   FROM aprs_objects
                   WHERE UPPER(name) LIKE ?
                      OR UPPER(COALESCE(source_callsign,'')) LIKE ?
                      OR UPPER(COALESCE(info,'')) LIKE ?
                      OR UPPER(COALESCE(comment,'')) LIKE ?
                      OR UPPER(COALESCE(status,'')) LIKE ?
                   ORDER BY CASE WHEN UPPER(name)=? THEN 0 ELSE 1 END,last_heard DESC
                   LIMIT ?""",
                (like, like, like, like, like, exact, remain),
            ).fetchall()
            for row in object_rows:
                item = dict(row)
                fmt = str(item.get("packet_format") or "").lower()
                info = " ".join(str(item.get(k) or "") for k in ("info", "comment", "status")).lower()
                if "ais" in fmt or "mmsi" in info:
                    etype = "ais"
                elif "weather" in fmt or "wx" in fmt:
                    etype = "weather"
                elif "repeater" in info or "repetidor" in info:
                    etype = "repeater"
                else:
                    etype = "object"
                item["entity_type"] = etype
                item["key"] = item["name"]
                out.append(item)
    return out[:max_rows]


def _list_groups() -> list[dict[str, Any]]:
    _ensure_schema()
    with db.connection() as conn:
        rows = conn.execute(
            """SELECT g.*,COUNT(m.callsign) AS members
               FROM station_groups_v190 g
               LEFT JOIN station_meta_v190 m ON m.group_id=g.id
               GROUP BY g.id ORDER BY g.name COLLATE NOCASE"""
        ).fetchall()
    return [dict(row) for row in rows]


def _save_group(payload: dict[str, Any], group_id: int | None = None) -> dict[str, Any]:
    _ensure_schema()
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("Informe o nome do grupo.")
    color = str(payload.get("color") or "").strip()[:32]
    note = str(payload.get("note") or "").strip()[:500]
    now = _utc()
    with db.connection() as conn:
        if group_id:
            conn.execute(
                "UPDATE station_groups_v190 SET name=?,color=?,note=?,updated_at=? WHERE id=?",
                (name, color, note, now, int(group_id)),
            )
            gid = int(group_id)
        else:
            cur = conn.execute(
                "INSERT INTO station_groups_v190(name,color,note,created_at,updated_at) VALUES(?,?,?,?,?)",
                (name, color, note, now, now),
            )
            gid = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM station_groups_v190 WHERE id=?", (gid,)).fetchone()
    return dict(row)


def _group_callsigns(group_id: int) -> list[str]:
    _ensure_schema()
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT callsign FROM station_meta_v190 WHERE group_id=? ORDER BY callsign",
            (int(group_id),),
        ).fetchall()
    return [str(row["callsign"]).upper() for row in rows if str(row["callsign"] or "").strip()]


def _sync_group_to_recipient_group(group_id: int) -> dict[str, Any]:
    _ensure_schema()
    with db.connection() as conn:
        row = conn.execute("SELECT name FROM station_groups_v190 WHERE id=?", (int(group_id),)).fetchone()
    if not row:
        raise ValueError("Grupo de estações não encontrado.")
    callsigns = _group_callsigns(group_id)
    if not callsigns:
        raise ValueError("O grupo não possui estações.")
    name = str(row["name"])
    existing = next((g for g in db.list_recipient_groups() if str(g.get("name") or "").lower() == name.lower()), None)
    return db.save_recipient_group({"name": name, "callsigns": callsigns}, int(existing["id"]) if existing else None)


def _get_station_meta(callsign: str) -> dict[str, Any]:
    _ensure_schema()
    call = str(callsign or "").upper().strip()
    with db.connection() as conn:
        row = conn.execute(
            """SELECT m.*,g.name AS group_name,
                      CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
               FROM station_meta_v190 m
               LEFT JOIN station_groups_v190 g ON g.id=m.group_id
               LEFT JOIN favorites f ON f.callsign=m.callsign
               WHERE m.callsign=?""",
            (call,),
        ).fetchone()
        if row:
            return dict(row)
        favorite = conn.execute("SELECT 1 FROM favorites WHERE callsign=?", (call,)).fetchone() is not None
    return {
        "callsign": call, "friendly_name": "", "color": "", "note": "", "group_id": None, "group_name": None,
        "favorite": int(favorite),
    }


def _save_station_meta(callsign: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_schema()
    call = str(callsign or "").upper().strip()
    if not call:
        raise ValueError("Indicativo inválido.")
    friendly = str(payload.get("friendly_name") or "").strip()[:120]
    color = str(payload.get("color") or "").strip()[:32]
    note = str(payload.get("note") or "").strip()[:1000]
    group_id = payload.get("group_id")
    group_id = int(group_id) if str(group_id or "").strip() else None
    with db.connection() as conn:
        conn.execute(
            """INSERT INTO station_meta_v190(callsign,friendly_name,color,note,group_id,updated_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(callsign) DO UPDATE SET
                 friendly_name=excluded.friendly_name,color=excluded.color,note=excluded.note,
                 group_id=excluded.group_id,updated_at=excluded.updated_at""",
            (call, friendly, color, note, group_id, _utc()),
        )
    return _get_station_meta(call)


def _timeline(limit: int = 300, kind: str = "", hours: int = 0) -> list[dict[str, Any]]:
    _ensure_schema()
    limit = max(10, min(int(limit or 300), 2000))
    events: list[dict[str, Any]] = []
    with db.connection() as conn:
        for row in conn.execute(
            """SELECT id,timestamp,direction,from_call,to_call,message,status
               FROM messages ORDER BY timestamp DESC LIMIT ?""", (limit,)
        ):
            events.append({
                "time": row["timestamp"], "kind": "message", "id": row["id"],
                "title": f"{row['from_call']} → {row['to_call']}",
                "detail": row["message"], "status": row["status"], "direction": row["direction"],
            })
        for row in conn.execute(
            """SELECT id,timestamp,callsign,latitude,longitude,speed,course
               FROM tracks ORDER BY timestamp DESC LIMIT ?""", (limit,)
        ):
            events.append({
                "time": row["timestamp"], "kind": "position", "id": row["id"],
                "title": row["callsign"], "detail": f"{row['latitude']}, {row['longitude']}",
                "speed": row["speed"], "course": row["course"],
            })
        for row in conn.execute(
            """SELECT id,sent_at,response_at,peer,query_type,status,rtt_ms,response_text
               FROM aprs_queries ORDER BY sent_at DESC LIMIT ?""", (limit,)
        ):
            events.append({
                "time": row["response_at"] or row["sent_at"], "kind": "query", "id": row["id"],
                "title": f"{row['query_type']} · {row['peer']}", "detail": row["response_text"] or "",
                "status": row["status"], "rtt_ms": row["rtt_ms"],
            })
        try:
            for row in conn.execute(
                """SELECT id,timestamp,direction,medium,source,destination,packet_type,raw_tnc2,reason
                   FROM tnc_frames ORDER BY timestamp DESC LIMIT ?""", (limit,)
            ):
                events.append({
                    "time": row["timestamp"], "kind": "rf", "id": row["id"],
                    "title": f"{row['source']} → {row['destination']}",
                    "detail": row["raw_tnc2"], "direction": row["direction"], "medium": row["medium"],
                })
        except sqlite3.OperationalError:
            pass
    events.sort(key=lambda x: str(x.get("time") or ""), reverse=True)
    kind = str(kind or "").strip().lower()
    if kind:
        events = [event for event in events if str(event.get("kind") or "").lower() == kind]
    if int(hours or 0) > 0:
        cutoff = datetime.now(timezone.utc).timestamp() - max(1, min(int(hours), 24 * 365)) * 3600
        cutoff_iso = datetime.fromtimestamp(cutoff, timezone.utc).replace(microsecond=0).isoformat()
        events = [event for event in events if str(event.get("time") or "") >= cutoff_iso]
    return events[:limit]


def _snapshot_bytes() -> bytes:
    memory = io.BytesIO()
    with tempfile.TemporaryDirectory() as td:
        db_file = Path(td) / "pt2vhf_aprs.db"
        source = sqlite3.connect(db.DB_PATH, timeout=10)
        dest = sqlite3.connect(db_file)
        try:
            source.backup(dest)
        finally:
            dest.close()
            source.close()
        manifest = {
            "format": "PT2VHF-APRS-Client-FullBackup",
            "version": __version__,
            "created_at": _utc(),
            "database": "pt2vhf_aprs.db",
        }
        with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            archive.write(db_file, "pt2vhf_aprs.db")
    memory.seek(0)
    return memory.getvalue()


def _restore_backup(upload) -> dict[str, Any]:
    if upload is None:
        raise ValueError("Selecione um arquivo de backup.")
    raw = upload.read(256 * 1024 * 1024)
    if not raw:
        raise ValueError("Backup vazio.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre_restore = Path(db.DB_PATH).with_name(f"pt2vhf_aprs_pre_restore_{stamp}.db")
    if Path(db.DB_PATH).exists():
        shutil.copy2(db.DB_PATH, pre_restore)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
            names = set(archive.namelist())
            if "manifest.json" not in names or "pt2vhf_aprs.db" not in names:
                raise ValueError("Arquivo não é um backup completo válido do PT2VHF APRS Client.")
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            if manifest.get("format") != "PT2VHF-APRS-Client-FullBackup":
                raise ValueError("Formato de backup incompatível.")
            archive.extract("pt2vhf_aprs.db", root)
        src_path = root / "pt2vhf_aprs.db"
        src = sqlite3.connect(src_path)
        try:
            check = src.execute("PRAGMA quick_check").fetchone()[0]
            if str(check).lower() != "ok":
                raise ValueError(f"Backup SQLite inválido: {check}")
            dst = sqlite3.connect(db.DB_PATH, timeout=30)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
    db.init_db()
    return {
        "ok": True,
        "source_version": manifest.get("version"),
        "restored_at": _utc(),
        "pre_restore_backup": str(pre_restore),
        "restart_recommended": True,
    }


_integrity_cache: dict[str, Any] = {"at": 0.0, "value": "unknown"}


def _cached_integrity() -> str:
    now = time.monotonic()
    if now - float(_integrity_cache.get("at") or 0.0) < 300:
        return str(_integrity_cache.get("value") or "unknown")
    try:
        with db.connection() as conn:
            value = str(conn.execute("PRAGMA quick_check").fetchone()[0])
    except Exception as exc:
        value = f"error: {exc}"
    _integrity_cache["at"] = now
    _integrity_cache["value"] = value
    return value


ALERT_DEFAULTS = {
    "station_appeared": True,
    "station_disappeared": False,
    "favorite_appeared": True,
    "new_message": True,
    "tnc_down": True,
    "aprsis_down": True,
    "database_problem": True,
    "disappear_minutes": 60,
}


def _alert_state(since: str = "", disappear_minutes: int = 60) -> dict[str, Any]:
    disappear_minutes = max(5, min(int(disappear_minutes or 60), 1440))
    cutoff = datetime.now(timezone.utc).timestamp() - disappear_minutes * 60
    cutoff_iso = datetime.fromtimestamp(cutoff, timezone.utc).replace(microsecond=0).isoformat()
    with db.connection() as conn:
        if since:
            stations = [dict(row) for row in conn.execute(
                """SELECT s.callsign,s.last_heard,
                          CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
                   FROM stations s LEFT JOIN favorites f ON f.callsign=s.callsign
                   WHERE s.last_heard>? ORDER BY s.last_heard DESC LIMIT 100""",
                (since,),
            ).fetchall()]
            messages = [dict(row) for row in conn.execute(
                """SELECT id,timestamp,from_call,to_call,message
                   FROM messages
                   WHERE direction='RX' AND timestamp>?
                   ORDER BY timestamp DESC LIMIT 100""",
                (since,),
            ).fetchall()]
        else:
            stations = []
            messages = []
        disappeared = [dict(row) for row in conn.execute(
            """SELECT s.callsign,s.last_heard,
                      CASE WHEN f.callsign IS NULL THEN 0 ELSE 1 END AS favorite
               FROM stations s LEFT JOIN favorites f ON f.callsign=s.callsign
               WHERE s.last_heard<? ORDER BY s.last_heard DESC LIMIT 100""",
            (cutoff_iso,),
        ).fetchall()]
    integrity = _cached_integrity()
    return {
        "now": _utc(),
        "stations_since": stations,
        "messages_since": messages,
        "disappeared": disappeared,
        "disappear_minutes": disappear_minutes,
        "aprs_is": service.status(),
        "tnc": tnc_service.status(),
        "database_integrity": integrity,
    }


def register_v190_routes(app) -> None:
    _ensure_schema()

    @app.get("/api/v190/search")
    def api_v190_search():
        return jsonify(_global_search(request.args.get("q", ""), request.args.get("limit", 30)))

    @app.get("/api/v190/groups")
    def api_v190_groups():
        return jsonify(_list_groups())

    @app.post("/api/v190/groups")
    def api_v190_create_group():
        try:
            return jsonify({"ok": True, "group": _save_group(request.get_json(force=True) or {})})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.put("/api/v190/groups/<int:group_id>")
    def api_v190_update_group(group_id: int):
        try:
            return jsonify({"ok": True, "group": _save_group(request.get_json(force=True) or {}, group_id)})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.delete("/api/v190/groups/<int:group_id>")
    def api_v190_delete_group(group_id: int):
        with db.connection() as conn:
            conn.execute("UPDATE station_meta_v190 SET group_id=NULL WHERE group_id=?", (group_id,))
            cur = conn.execute("DELETE FROM station_groups_v190 WHERE id=?", (group_id,))
        return jsonify({"ok": bool(cur.rowcount), "deleted": int(cur.rowcount or 0)})

    @app.get("/api/v190/groups/<int:group_id>/members")
    def api_v190_group_members(group_id: int):
        return jsonify({"group_id": group_id, "callsigns": _group_callsigns(group_id)})

    @app.post("/api/v190/groups/<int:group_id>/sync-recipient-group")
    def api_v190_sync_group(group_id: int):
        try:
            return jsonify({"ok": True, "recipient_group": _sync_group_to_recipient_group(group_id)})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/v190/stations/<callsign>/meta")
    def api_v190_station_meta(callsign: str):
        return jsonify(_get_station_meta(callsign))

    @app.post("/api/v190/stations/<callsign>/meta")
    def api_v190_save_station_meta(callsign: str):
        try:
            return jsonify({"ok": True, "meta": _save_station_meta(callsign, request.get_json(force=True) or {})})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/v190/timeline")
    def api_v190_timeline():
        try:
            limit = int(request.args.get("limit", 300))
            hours = int(request.args.get("hours", 0))
        except (TypeError, ValueError):
            limit, hours = 300, 0
        return jsonify(_timeline(limit, request.args.get("kind", ""), hours))

    @app.get("/api/v190/backup/full")
    def api_v190_backup_full():
        payload = io.BytesIO(_snapshot_bytes())
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return send_file(
            payload, mimetype="application/zip", as_attachment=True,
            download_name=f"PT2VHF_APRS_Client_Backup_v{__version__}_{stamp}.zip",
        )

    @app.post("/api/v190/backup/restore")
    def api_v190_backup_restore():
        try:
            return jsonify(_restore_backup(request.files.get("backup")))
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/v190/alerts/settings")
    def api_v190_alert_settings():
        return jsonify(_json_setting("alerts", ALERT_DEFAULTS))

    @app.post("/api/v190/alerts/settings")
    def api_v190_save_alert_settings():
        data = dict(ALERT_DEFAULTS)
        data.update(request.get_json(force=True) or {})
        data["disappear_minutes"] = max(5, min(int(data.get("disappear_minutes") or 60), 1440))
        return jsonify({"ok": True, "settings": _save_json_setting("alerts", data)})

    @app.get("/api/v190/alerts/state")
    def api_v190_alert_state():
        settings = _json_setting("alerts", ALERT_DEFAULTS)
        return jsonify(_alert_state(str(request.args.get("since") or ""), int(settings.get("disappear_minutes") or 60)))

    @app.post("/api/v190/tnc/test")
    def api_v190_tnc_test():
        try:
            cfg = get_tnc_config()
            result = probe_transport(cfg)
            return jsonify({"ok": bool(result.get("ok")), **result})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
