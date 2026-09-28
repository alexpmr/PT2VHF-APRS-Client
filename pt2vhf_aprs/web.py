from __future__ import annotations

import io
import json
import re
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, Response, g, jsonify, render_template, request, send_file

from . import __version__
from . import database as db
from . import diagnostics as diag
from . import updater
from .aprs_service import full_callsign, service
from .version_notes import notes_for


GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/alexpmr/PT2VHF-APRS-Client/releases/latest"
UPDATE_CACHE_SECONDS = 5 * 60
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
        "asset_ready": False,
        "update_mode": updater.current_update_mode(),
        "install_supported": updater.install_supported(),
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
        if not latest:
            raise ValueError("Release mais recente sem tag de versão.")
        release_url = str(release.get("html_url") or "").strip() or None
        current_v = version_tuple(__version__)
        latest_v = version_tuple(latest)

        payload["latest_version"] = latest
        payload["release_url"] = release_url
        payload["release_notes"] = str(release.get("body") or "")
        payload["update_available"] = latest_v > current_v

        asset = updater.select_asset(release, latest)
        if asset:
            payload["asset_name"] = asset["name"]
            payload["asset_url"] = asset["url"]
            payload["asset_size"] = asset["size"]
            payload["asset_digest"] = asset["digest"] or None
            payload["asset_ready"] = bool(asset["url"])
        pending = updater.pending_update()
        payload["downloaded"] = bool(
            pending
            and str(pending.get("version") or "") == latest
            and str(pending.get("asset_name") or "") == str(payload.get("asset_name") or "")
        )

        if latest_v > current_v:
            payload["status"] = "update_available"
            if not asset:
                payload["error"] = "A nova Release existe, mas o pacote desta plataforma ainda não foi publicado."
        elif latest_v == current_v:
            payload["status"] = "latest"
        else:
            payload["status"] = "ahead"

        # Somente resultados válidos entram no cache. Falhas nunca bloqueiam o
        # próximo ciclo de verificação.
        with _update_cache_lock:
            _update_cache["timestamp"] = now
            _update_cache["payload"] = dict(payload)
        return payload
    except Exception as exc:
        payload["status"] = "error"
        payload["error"] = str(exc)
        return payload


KML_NS = "http://www.opengis.net/kml/2.2"


def _kml_document(
    data: dict,
    include_stations: bool = True,
    include_positions: bool = True,
    include_tracklogs: bool = True,
    include_topology: bool = True,
) -> bytes:
    ET.register_namespace("", KML_NS)
    root = ET.Element(f"{{{KML_NS}}}kml")
    document = ET.SubElement(root, f"{{{KML_NS}}}Document")
    ET.SubElement(document, f"{{{KML_NS}}}name").text = "PT2VHF APRS Client export"

    def folder(name: str):
        node = ET.SubElement(document, f"{{{KML_NS}}}Folder")
        ET.SubElement(node, f"{{{KML_NS}}}name").text = name
        return node

    def point(parent, name: str, lat: float, lon: float, altitude: float | None = None, description: str = ""):
        placemark = ET.SubElement(parent, f"{{{KML_NS}}}Placemark")
        ET.SubElement(placemark, f"{{{KML_NS}}}name").text = name
        if description:
            ET.SubElement(placemark, f"{{{KML_NS}}}description").text = description
        point_node = ET.SubElement(placemark, f"{{{KML_NS}}}Point")
        alt = 0.0 if altitude is None else float(altitude)
        ET.SubElement(point_node, f"{{{KML_NS}}}coordinates").text = f"{float(lon):.7f},{float(lat):.7f},{alt:.1f}"

    stations = list(data.get("stations") or [])
    tracks = list(data.get("tracks") or [])
    topology = list(data.get("topology") or [])

    if include_stations:
        station_folder = folder("Stations")
        for station in stations:
            description = "\n".join(
                item for item in [
                    f"Last heard: {station.get('last_heard') or ''}",
                    f"Info: {station.get('info') or ''}",
                    f"Path: {station.get('path') or ''}",
                ] if item.split(": ", 1)[-1]
            )
            point(
                station_folder,
                str(station.get("callsign") or "Station"),
                float(station["latitude"]),
                float(station["longitude"]),
                station.get("altitude"),
                description,
            )

    if include_positions:
        positions_folder = folder("Positions")
        for row in tracks:
            description = f"Timestamp: {row.get('timestamp') or ''}"
            point(
                positions_folder,
                f"{row.get('callsign') or 'Station'} @ {row.get('timestamp') or ''}",
                float(row["latitude"]),
                float(row["longitude"]),
                row.get("altitude"),
                description,
            )

    if include_tracklogs:
        track_folder = folder("Tracklogs")
        grouped: dict[str, list[dict]] = {}
        for row in tracks:
            call = str(row.get("callsign") or "").upper().strip()
            if call:
                grouped.setdefault(call, []).append(row)
        for call, rows in grouped.items():
            if len(rows) < 2:
                continue
            placemark = ET.SubElement(track_folder, f"{{{KML_NS}}}Placemark")
            ET.SubElement(placemark, f"{{{KML_NS}}}name").text = call
            line = ET.SubElement(placemark, f"{{{KML_NS}}}LineString")
            ET.SubElement(line, f"{{{KML_NS}}}tessellate").text = "1"
            coordinates = []
            for row in rows:
                alt = float(row.get("altitude") or 0.0)
                coordinates.append(f"{float(row['longitude']):.7f},{float(row['latitude']):.7f},{alt:.1f}")
            ET.SubElement(line, f"{{{KML_NS}}}coordinates").text = " ".join(coordinates)

    if include_topology:
        topology_folder = folder("Topology")
        for edge in topology:
            placemark = ET.SubElement(topology_folder, f"{{{KML_NS}}}Placemark")
            source = str(edge.get("source") or "")
            target = str(edge.get("target") or "")
            ET.SubElement(placemark, f"{{{KML_NS}}}name").text = f"{source} → {target}"
            ET.SubElement(placemark, f"{{{KML_NS}}}description").text = (
                f"Kind: {edge.get('kind') or ''}\n"
                f"Packets: {edge.get('packet_count') or 0}\n"
                f"Last seen: {edge.get('last_seen') or ''}"
            )
            line = ET.SubElement(placemark, f"{{{KML_NS}}}LineString")
            ET.SubElement(line, f"{{{KML_NS}}}tessellate").text = "1"
            ET.SubElement(line, f"{{{KML_NS}}}coordinates").text = (
                f"{float(edge['source_lon']):.7f},{float(edge['source_lat']):.7f},0 "
                f"{float(edge['target_lon']):.7f},{float(edge['target_lat']):.7f},0"
            )

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["JSON_SORT_KEYS"] = False
    db.init_db()
    diag.configure(db.DB_PATH.parent)
    diag.log_event("flask_app_created", version=__version__)

    @app.before_request
    def diagnostics_request_start():
        g._pt2vhf_diag_request = diag.begin_request(request.method, request.path)

    @app.after_request
    def diagnostics_request_end(response):
        token = getattr(g, "_pt2vhf_diag_request", None)
        diag.end_request(token, status=int(response.status_code))
        g._pt2vhf_diag_request = None
        return response

    @app.teardown_request
    def diagnostics_request_teardown(exc):
        token = getattr(g, "_pt2vhf_diag_request", None)
        if token:
            diag.end_request(token, status=500 if exc else None, error=f"{type(exc).__name__}: {exc}" if exc else None)
            g._pt2vhf_diag_request = None

    @app.get("/api/diagnostics/ping")
    def api_diagnostics_ping():
        return jsonify({"ok": True, "version": __version__, "active_requests": len(diag.active_requests())})

    @app.get("/api/diagnostics/status")
    def api_diagnostics_status():
        return jsonify({
            "ok": True,
            "version": __version__,
            "active_requests": diag.active_requests(),
            "log_path": str(diag.log_path()),
            "threads": [{"name": t.name, "ident": t.ident, "daemon": t.daemon} for t in threading.enumerate()],
        })

    @app.get("/api/diagnostics/log")
    def api_diagnostics_log():
        path = diag.log_path()
        if not path.exists():
            diag.log_event("diagnostics_log_requested")
        return send_file(path, as_attachment=True, download_name=f"PT2VHF_APRS_Client_diagnostics_v{__version__}.log", mimetype="text/plain")

    @app.get("/")
    def index():
        return render_template("index.html", app_version=__version__)

    @app.get("/api/system-metrics")
    def api_system_metrics():
        payload = diag.system_metrics()
        payload["active_requests"] = len(diag.active_requests())
        try:
            payload["tx_queue"] = int(service._tx_queue.qsize())
        except Exception:
            payload["tx_queue"] = 0
        return jsonify(payload)

    @app.get("/api/status")
    def api_status():
        payload = service.status()
        payload.update(db.summary_counts())
        return jsonify(payload)

    @app.get("/api/current-version-info")
    def api_current_version_info():
        cfg = db.get_config()
        counts = db.summary_counts()
        info = notes_for(__version__)
        info["existing_install"] = bool(
            str(cfg.get("callsign") or "").strip()
            or int(counts.get("stations") or 0)
            or int(counts.get("messages") or 0)
        )
        return jsonify(info)

    @app.get("/api/update-status")
    def api_update_status():
        force = str(request.args.get("force", "")).lower() in {"1", "true", "yes"}
        return jsonify(get_update_status(force=force))

    def _install_latest_update():
        try:
            diag.log_event(
                "update_install_http_requested",
                current_version=__version__,
                method=request.method,
                path=request.path,
            )
            status = get_update_status(force=True)
            if not status.get("update_available"):
                return jsonify({"ok": False, "error": "Não há uma versão mais recente disponível."}), 409
            if not status.get("asset_ready") or not status.get("asset_url") or not status.get("asset_name"):
                return jsonify({
                    "ok": False,
                    "error": status.get("error") or "O pacote compatível com esta plataforma ainda não está disponível.",
                }), 409
            if not status.get("install_supported"):
                return jsonify({
                    "ok": False,
                    "error": "Esta execução não permite instalação automática. Use a página oficial da Release.",
                    "release_url": status.get("release_url"),
                }), 409

            result = updater.download_and_install(
                str(status["latest_version"]),
                {
                    "name": status["asset_name"],
                    "url": status["asset_url"],
                    "size": status.get("asset_size") or 0,
                    "digest": status.get("asset_digest") or "",
                },
            )
            return jsonify(result)
        except RuntimeError as exc:
            diag.log_event("update_install_http_failed", error=str(exc), kind="runtime")
            return jsonify({"ok": False, "error": str(exc)}), 409
        except Exception as exc:
            diag.log_event("update_install_http_failed", error=str(exc), kind=type(exc).__name__)
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.post("/api/update/install")
    def api_update_install():
        return _install_latest_update()

    @app.post("/api/update/download")
    def api_update_download():
        # Compatibilidade com versões que ainda chamam a rota antiga.
        return _install_latest_update()

    @app.get("/api/update/pending")
    def api_update_pending():
        return jsonify({
            "pending": updater.pending_update(),
            "rollback": updater.rollback_available(),
            "auto_update": True,
            "mode": updater.current_update_mode(),
            "install_supported": updater.install_supported(),
        })

    @app.post("/api/update/rollback")
    def api_update_rollback():
        try:
            if not updater.rollback_available():
                return jsonify({"ok": False, "error": "Não existe backup portátil disponível para restauração."}), 404
            if not updater.restore_windows_portable_backup():
                return jsonify({"ok": False, "error": "Não foi possível iniciar o rollback."}), 500
            return jsonify({"ok": True, "message": "Rollback iniciado. A aplicação será reiniciada."})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

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

    @app.get("/api/export/kml")
    def api_export_kml():
        try:
            def enabled(name: str) -> bool:
                return str(request.args.get(name, "1")).lower() not in {"0", "false", "no", "off"}

            try:
                hours = int(request.args.get("hours", 0))
            except (TypeError, ValueError):
                hours = 0

            options = {
                "include_stations": enabled("stations"),
                "include_positions": enabled("positions"),
                "include_tracklogs": enabled("tracklogs"),
                "include_topology": enabled("topology"),
            }
            if not any(options.values()):
                return jsonify({"error": "Selecione pelo menos uma camada para exportar."}), 400

            payload = db.geographic_export_data(hours)
            content = _kml_document(payload, **options)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"PT2VHF_APRS_Client_{stamp}.kml"
            return Response(
                content,
                mimetype="application/vnd.google-earth.kml+xml",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception as exc:
            diag.log_event("kml_export_failed", error=str(exc))
            return jsonify({"error": str(exc)}), 400

    @app.post("/api/queries/send")
    def api_send_query():
        try:
            data = request.get_json(force=True) or {}
            result = service.send_query(
                data.get("to", ""),
                data.get("query_type", ""),
                data.get("heard_callsign", ""),
            )
            return jsonify({"ok": True, **result})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

    @app.get("/api/queries")
    def api_queries():
        try:
            peer = str(request.args.get("station") or "").upper().strip()
            limit = int(request.args.get("limit", 100))
            return jsonify(db.list_aprs_queries(peer, limit))
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

    @app.get("/api/queries/<int:query_id>")
    def api_query_detail(query_id: int):
        payload = db.aprs_query_detail(query_id)
        if not payload:
            return jsonify({"error": "Query APRS não encontrada."}), 404
        return jsonify(payload)

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

    @app.get("/api/traffic/overview")
    def api_traffic_overview():
        try:
            hours = int(request.args.get("hours", 0))
            bins = int(request.args.get("bins", 120))
            start = str(request.args.get("start") or "").strip() or None
            end = str(request.args.get("end") or "").strip() or None
            return jsonify(db.packet_traffic_overview(hours=hours, bins=bins, start=start, end=end))
        except Exception as exc:
            return jsonify({"first_timestamp": None, "last_timestamp": None, "total": 0, "bins": [], "error": str(exc)}), 400

    @app.get("/api/traffic/events")
    def api_traffic_events():
        try:
            if str(request.args.get("bootstrap", "")).lower() in {"1", "true", "yes"}:
                return jsonify({"events": [], "last_id": db.latest_packet_id(), "complete": False})
            after_id = int(request.args.get("after_id", 0))
            hours = int(request.args.get("hours", 0))
            limit = int(request.args.get("limit", 1000))
            start = str(request.args.get("start") or "").strip() or None
            end = str(request.args.get("end") or "").strip() or None
            return jsonify(db.packet_traffic_events(
                after_id=after_id,
                hours=hours,
                limit=limit,
                start=start,
                end=end,
            ))
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
                result = service.queue_message_parts(data.get("to", ""), data.get("message", ""))
            elif message_type in {"bulletin", "group_bulletin", "announcement"}:
                group = data.get("group", "") if message_type == "group_bulletin" else ""
                bulletin_id = data.get("bulletin_id", "A" if message_type == "announcement" else "0")
                row_id = service.send_bulletin(
                    data.get("message", ""),
                    bulletin_id=bulletin_id,
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
                    "queued": bool(result.get("queued")),
                    "duplicate": bool(result.get("duplicate")),
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
