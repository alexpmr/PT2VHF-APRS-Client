from __future__ import annotations

import io
import json
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file

from . import database as db
from .aprs_service import service


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["JSON_SORT_KEYS"] = False
    db.init_db()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/status")
    def api_status():
        return jsonify(service.status())

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

    @app.post("/api/config")
    def api_save_config():
        try:
            saved = db.save_config(request.get_json(force=True) or {})
            return jsonify({"ok": True, "config": saved})
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

    @app.get("/api/stations")
    def api_stations():
        return jsonify(db.list_stations(request.args.get("filter", "")))

    @app.get("/api/messages")
    def api_messages():
        return jsonify(db.list_messages(request.args.get("from", "")))

    @app.post("/api/messages/send")
    def api_send_message():
        try:
            data = request.get_json(force=True) or {}
            message_id = service.send_message(data.get("to", ""), data.get("message", ""))
            return jsonify({"ok": True, "id": message_id})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

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
