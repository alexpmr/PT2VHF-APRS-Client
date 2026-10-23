"""Rotas das ferramentas de planejamento no mapa (enlace entre 2 pontos e melhor ponto)."""
from __future__ import annotations

from flask import Response, jsonify, request

from . import database as db
from . import planning

_elevations: list[planning.Elevations] = []


def _data_dir():
    return db.DB_PATH.parent


def _elev() -> planning.Elevations:
    if not _elevations:
        _elevations.append(planning.Elevations(cache_dir=_data_dir() / "terrain-tiles"))
    return _elevations[0]




def _link(payload: dict) -> dict:
    a, b = payload.get("a"), payload.get("b")
    call_a = str(payload.get("station_a") or "").upper().strip() or None
    call_b = str(payload.get("station_b") or "").upper().strip() or None
    observed = None
    if call_a and call_b:
        observed = planning.observed_link(db.list_rf_received_by(call_a), db.list_rf_received_by(call_b), call_a, call_b)
    return planning.link_analysis(_elev(), a, b, payload.get("params") or {}, observed)


def _pdf(body: bytes, filename: str) -> Response:
    response = Response(body, mimetype="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=" + filename
    response.headers["Cache-Control"] = "no-store"
    return response


def _error(exc, status=400):
    return jsonify({"ok": False, "error": str(exc)}), status


def register_planning_routes(app) -> None:
    @app.get("/api/planning/defaults")
    def api_planning_defaults():
        cfg = db.get_config()
        own = None
        if cfg.get("latitude") not in (None, "") and cfg.get("longitude") not in (None, ""):
            own = {"callsign": str(cfg.get("callsign") or "").upper(),
                   "lat": float(cfg["latitude"]), "lon": float(cfg["longitude"])}
        return jsonify({"ok": True, "freq_mhz": planning.APRS_FREQ_MHZ, "tx_power_w": 25,
                        "sensitivity_dbm": planning.DEFAULT_SENSITIVITY_DBM, "own": own,
                        "saved": planning.saved_surveys(_data_dir())})

    @app.post("/api/planning/link")
    def api_planning_link():
        try:
            return jsonify({"ok": True, "data": _link(request.get_json(force=True) or {})})
        except (ValueError, TypeError, LookupError) as exc:
            return _error(exc)
        except RuntimeError as exc:
            return _error(exc, 502)

    @app.post("/api/planning/best")
    def api_planning_best():
        try:
            payload = request.get_json(force=True) or {}
            return jsonify({"ok": True, "data": planning.best_points(
                _elev(), payload.get("polygon"), payload.get("reference"), payload.get("count") or 10)})
        except (ValueError, TypeError, LookupError) as exc:
            return _error(exc)
        except RuntimeError as exc:
            return _error(exc, 502)

    @app.post("/api/planning/save")
    def api_planning_save():
        try:
            item = planning.save_survey(_data_dir(), request.get_json(force=True) or {})
            return jsonify({"ok": True, "item": item, "saved": planning.saved_surveys(_data_dir())})
        except (ValueError, TypeError) as exc:
            return _error(exc)

    @app.post("/api/planning/delete")
    def api_planning_delete():
        try:
            planning.delete_survey(_data_dir(), (request.get_json(force=True) or {}).get("id"))
            return jsonify({"ok": True, "saved": planning.saved_surveys(_data_dir())})
        except (ValueError, TypeError, LookupError) as exc:
            return _error(exc)

    @app.post("/api/planning/pdf")
    def api_planning_pdf():
        try:
            from . import planning_pdf
        except ImportError:
            return _error("Exportação em PDF indisponível nesta instalação (biblioteca reportlab ausente).", 501)
        try:
            payload = request.get_json(force=True) or {}
            name = str(payload.get("name") or "")[:60]
            if payload.get("kind") == "link":
                return _pdf(planning_pdf.link_pdf(_link(payload), name), "PT2VHF-APRS-Analise-de-Enlace.pdf")
            result = planning.best_points(_elev(), payload.get("polygon"), payload.get("reference"),
                                          payload.get("count") or 10)
            links = [{"rank": item.get("rank"), "target": str(item.get("target") or "B")[:40], "link": _link(item)}
                     for item in (payload.get("links") or [])[:20]]
            body = planning_pdf.survey_pdf(result, name, links,
                                           planning_pdf.nearby_stations(db.list_stations(""), result))
            return _pdf(body, "PT2VHF-APRS-Survey-Melhor-Ponto.pdf")
        except (ValueError, TypeError, LookupError) as exc:
            return _error(exc)
        except RuntimeError as exc:
            return _error(exc, 502)
