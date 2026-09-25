from __future__ import annotations

import io
import json
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file

from . import __version__
from . import database as db
from .aprs_service import full_callsign, service
from . import updater


GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/alexpmr/PT2VHF-APRS-Client/releases/latest"
UPDATE_CACHE_SECONDS = 15 * 60
_update_cache: dict[str, object] = {"timestamp": 0.0, "payload": None}
_update_cache_lock = threading.Lock()


def version_tuple(value: str) -> tuple[int, ...]:
    text = str(value or "").strip().lower()
    if text.startswith("v"):
        text = text[1:]
    parts: list[int] = []
    for part in text.split("."):
        match = re.match(r"(\d+)", part)
        if not match:
            break
        parts.append(int(match.group(1)))
    return tuple(parts or [0])


def get_update_status(force: bool = False) -> dict:
    now = time.monotonic()
    with _update_cache_lock:
        cached = _update_cache.get("payload")
        cached_at = float(_update_cache.get("timestamp") or 0.0)
        if not force and cached and now - cached_at < UPDATE_CACHE_SECONDS:
            return dict(cached)

    payload = {
        "current_version": __version__,
        "latest_version": None,
        "update_available": False,
        "release_url": None,
        "release_notes": "",
        "asset_name": None,
        "asset_url": None,
        "asset_size": 0,
        "asset_digest": None,
        "update_mode": updater.current_update_mode(),
        "install_supported": updater.current_update_mode() in {"windows-portable", "windows-installer", "macos-dmg", "linux-appimage"},
        "downloaded": False,
        "status": "unknown",
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "error": None,
    }

    try:
        req = urllib.request.Request(
            GITHUB_LATEST_RELEASE_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"PT2VHF-APRS-Client/{__version__}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            release = json.loads(response.read().decode("utf-8"))

        latest = str(release.get("tag_name") or "").strip().lstrip("vV")
        release_url = str(release.get("html_url") or "").strip() or None
        current_v = version_tuple(__version__)
        latest_v = version_tuple(latest)
        asset = updater.select_asset(release, latest) if latest else None
        pending = updater.pending_update()

        payload["latest_version"] = latest or None
        payload["release_url"] = release_url
        payload["release_notes"] = str(release.get("body") or "")
        payload["asset_name"] = asset.get("name") if asset else None
        payload["asset_url"] = asset.get("url") if asset else None
        payload["asset_size"] = int(asset.get("size") or 0) if asset else 0
        payload["asset_digest"] = asset.get("digest") if asset else None
        payload["downloaded"] = bool(pending and str(pending.get("version") or "") == latest)
        payload["update_available"] = latest_v > current_v
        if latest_v > current_v:
            payload["status"] = "update_available"
        elif latest_v == current_v:
            payload["status"] = "latest"
        else:
            payload["status"] = "ahead"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        payload["status"] = "error"
        payload["error"] = str(exc)

    with _update_cache_lock:
        _update_cache["timestamp"] = now
        _update_cache["payload"] = dict(payload)
    return payload


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["JSON_SORT_KEYS"] = False
    db.init_db()

    @app.get("/")
    def index():
        return render_template("index.html", app_version=__version__)

    @app.get("/api/status")
    def api_status():
        payload = service.status()
        payload.update(db.summary_counts())
        return jsonify(payload)

    @app.get("/api/update-status")
    def api_update_status():
        force = str(request.args.get("force", "")).lower() in {"1", "true", "yes"}
        return jsonify(get_update_status(force=force))

    @app.post("/api/update/download")
    def api_update_download():
        try:
            status = get_update_status(force=True)
            if status.get("status") != "update_available":
                raise ValueError("Não há uma versão mais recente disponível.")
            if not status.get("asset_url") or not status.get("asset_name"):
                raise ValueError("A Release não possui um pacote compatível com esta plataforma.")
            result = updater.download_asset(
                str(status.get("latest_version") or ""),
                {
                    "name": status["asset_name"],
                    "url": status["asset_url"],
                    "size": status.get("asset_size") or 0,
                    "digest": status.get("asset_digest") or "",
                },
            )
            with _update_cache_lock:
                _update_cache["timestamp"] = 0.0
                _update_cache["payload"] = None
            return jsonify({"ok": True, "update": result})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/update/pending")
    def api_update_pending():
        return jsonify({
            "pending": updater.pending_update(),
            "rollback": updater.rollback_available(),
        })

    @app.post("/api/update/rollback")
    def api_update_rollback():
        if updater.restore_windows_portable_backup():
            return jsonify({"ok": True, "message": "Rollback preparado. Feche o aplicativo para concluir."})
        return jsonify({"ok": False, "error": "Não há backup portátil disponível para rollback nesta plataforma."}), 400

    @app.post("/api/connect")
    def api_connect():
        try:
            service.connect()
            return jsonify({"ok": True, "status": service.status()})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/disconnect")
    def api_disconnect():
        service.disconnect()
        return jsonify({"ok": True, "status": service.status()})

    @app.get("/api/config")
    def api_get_config():
        cfg = db.get_config()
        cfg["passcode_set"] = bool(cfg.get("passcode"))
        return jsonify(cfg)

    @app.post("/api/config/reset")
    def api_reset_config():
        try:
            service.disconnect()
            cfg = db.reset_config()
            return jsonify({"ok": True, "config": cfg})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/config")
    def api_save_config():
        try:
            before = db.get_config()
            saved = db.save_config(request.get_json(force=True) or {})

            connection_keys = {
                "callsign", "ssid", "server", "port", "passcode",
                "aprs_filter", "latitude", "longitude",
            }
            changed = any(before.get(key) != saved.get(key) for key in connection_keys)
            status = service.status()
            reconnected = False
            if changed and status.get("wanted"):
                service.reconnect()
                reconnected = True

            return jsonify({"ok": True, "config": saved, "reconnected": reconnected})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/config/export")
    def api_export_config():
        payload = json.dumps(db.export_config(), indent=2, ensure_ascii=False).encode("utf-8")
        return send_file(
            io.BytesIO(payload),
            as_attachment=True,
            download_name="pt2vhf_aprs_config.json",
            mimetype="application/json",
        )

    @app.post("/api/config/import")
    def api_import_config():
        try:
            if "file" not in request.files:
                raise ValueError("Selecione um arquivo JSON.")
            data = json.load(request.files["file"].stream)
            cfg = db.import_config(data)
            return jsonify({"ok": True, "config": cfg})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/map-state")
    def api_get_map_state():
        return jsonify(db.get_map_state())

    @app.post("/api/map-state")
    def api_save_map_state():
        try:
            data = request.get_json(force=True)
            db.save_map_state(data["latitude"], data["longitude"], data["zoom"])
            return jsonify({"ok": True})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/map-data")
    def api_map_data():
        return jsonify(db.map_data())

    @app.get("/api/topology")
    def api_topology():
        try:
            hours = int(request.args.get("hours", 0))
        except (TypeError, ValueError):
            hours = 0
        return jsonify(db.list_topology_edges(hours))

    @app.get("/api/topology/stats")
    def api_topology_stats():
        try:
            hours = int(request.args.get("hours", 0))
        except (TypeError, ValueError):
            hours = 0
        payload = db.topology_stats(hours)
        payload["comparison"] = db.topology_period_comparison(hours)
        return jsonify(payload)

    @app.get("/api/topology/timeline")
    def api_topology_timeline():
        try:
            hours = int(request.args.get("hours", 0))
            limit = int(request.args.get("limit", 2500))
        except (TypeError, ValueError):
            hours, limit = 0, 2500
        return jsonify(db.topology_timeline(hours, limit))

    @app.get("/api/traffic/events")
    def api_traffic_events():
        try:
            if str(request.args.get("bootstrap", "")).lower() in {"1", "true", "yes"}:
                return jsonify({"events": [], "last_id": db.latest_packet_id(), "complete": False})
            after_id = int(request.args.get("after_id", 0))
            hours = int(request.args.get("hours", 0))
            limit = int(request.args.get("limit", 1000))
            return jsonify(db.packet_traffic_events(after_id=after_id, hours=hours, limit=limit))
        except Exception as exc:
            return jsonify({"events": [], "last_id": db.latest_packet_id(), "error": str(exc)}), 400

    @app.get("/api/favorites")
    def api_favorites():
        return jsonify(db.list_favorites())

    @app.post("/api/favorites/<callsign>")
    def api_set_favorite(callsign: str):
        try:
            data = request.get_json(silent=True) or {}
            favorite = bool(data.get("favorite", True))
            db.set_favorite(callsign, favorite)
            return jsonify({"ok": True, "callsign": callsign.upper(), "favorite": favorite})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/stations")
    def api_stations():
        return jsonify(db.list_stations(request.args.get("filter", "")))

    @app.post("/api/tracks/clear")
    def api_clear_tracklogs():
        deleted = db.clear_tracklogs()
        return jsonify({"ok": True, "deleted": deleted})

    @app.post("/api/stations/clear")
    def api_clear_stations():
        deleted = db.clear_stations()
        return jsonify({"ok": True, "deleted": deleted})

    @app.get("/api/messages")
    def api_messages():
        mine = str(request.args.get("mine", "")).lower() in {"1", "true", "yes"}
        station = full_callsign(db.get_config()) if mine else ""
        return jsonify(db.list_messages(
            request.args.get("from", ""),
            station_filter=station,
        ))

    @app.post("/api/messages/<int:row_id>/read")
    def api_mark_message_read(row_id: int):
        return jsonify({"ok": True, "updated": db.mark_message_read(row_id)})

    @app.post("/api/messages/conversation/read")
    def api_mark_conversation_read():
        data = request.get_json(silent=True) or {}
        contact = str(data.get("contact") or "").upper().strip()
        own = full_callsign(db.get_config())
        return jsonify({"ok": True, "updated": db.mark_conversation_read(contact, own)})

    @app.post("/api/messages/<int:row_id>/retry")
    def api_retry_message(row_id: int):
        try:
            result = service.retry_message(row_id)
            return jsonify({"ok": True, **result})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.post("/api/messages/clear")
    def api_clear_messages():
        deleted = db.clear_messages()
        return jsonify({"ok": True, "deleted": deleted})

    @app.post("/api/messages/send")
    def api_send_message():
        try:
            data = request.get_json(force=True) or {}
            message_type = str(data.get("type") or "message").lower()

            if message_type == "message":
                result = service.send_message_parts(data.get("to", ""), data.get("message", ""))
            elif message_type in {"bulletin", "group_bulletin"}:
                group = data.get("group", "") if message_type == "group_bulletin" else ""
                row_id = service.send_bulletin(
                    data.get("message", ""),
                    bulletin_id=data.get("bulletin_id", "0"),
                    group=group,
                )
            else:
                raise ValueError("Tipo de mensagem APRS inválido.")

            if message_type == "message":
                return jsonify({
                    "ok": True,
                    "ids": result["row_ids"],
                    "message_ids": result["message_ids"],
                    "part_count": result["part_count"],
                    "type": message_type,
                })
            return jsonify({"ok": True, "id": row_id, "type": message_type})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/log")
    def api_log():
        return jsonify(db.list_aprs_log(
            request.args.get("filter", ""),
            request.args.get("direction", "ALL"),
            request.args.get("limit", 1000),
        ))

    @app.post("/api/log/clear")
    def api_clear_log():
        db.clear_aprs_log()
        return jsonify({"ok": True})

    @app.get("/api/callsigns")
    def api_callsigns():
        return jsonify(db.callsign_suggestions(request.args.get("prefix", "")))

    @app.post("/api/beacon")
    def api_beacon():
        try:
            service.send_beacon()
            return jsonify({"ok": True})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    return app
