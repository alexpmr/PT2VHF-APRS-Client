"""Rotas das ferramentas de planejamento no mapa (enlace entre 2 pontos e melhor ponto)."""
from __future__ import annotations

from flask import Response, jsonify, request

from . import database as db
from . import planning

_elevations: list[planning.Elevations] = []
_tiles_cache: list[planning.TerrainTiles] = []
# v1.15.0: últimas coberturas calculadas, reaproveitadas pelo PDF sem recalcular.
_coverage_cache: dict[str, dict] = {}
COVERAGE_CACHE_SIZE = 4


def _data_dir():
    return db.DB_PATH.parent


def _elev() -> planning.Elevations:
    if not _elevations:
        _elevations.append(planning.Elevations(cache_dir=_data_dir() / "terrain-tiles"))
    return _elevations[0]




def _tiles() -> planning.TerrainTiles:
    if not _tiles_cache:
        _tiles_cache.append(planning.TerrainTiles(_data_dir() / "terrain-tiles"))
    return _tiles_cache[0]


def _known_stations() -> list[dict]:
    """Estações com posição válida, no formato usado por coverage.classify_nodes."""
    out = []
    for st in db.list_stations(""):
        lat, lon = st.get("latitude"), st.get("longitude")
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        if abs(lat) < 1e-6 and abs(lon) < 1e-6:
            continue
        call = str(st.get("callsign") or "").upper()
        out.append({"node_num": call, "name": call, "lat": lat, "lon": lon,
                    "symbol": st.get("symbol") or "", "last_heard": st.get("last_heard")})
    return out


def _heard_from(call: str) -> list[dict]:
    """Estações que comprovadamente ouviram `call` diretamente por RF (topologia do cliente)."""
    call = str(call or "").upper().strip()
    if not call:
        return []
    with db.connection() as conn:
        rows = conn.execute(
            """SELECT UPPER(TRIM(target)) AS callsign, SUM(packet_count) AS packets, MAX(last_seen) AS last_seen
                 FROM topology_edges
                WHERE UPPER(TRIM(source))=? AND kind='rf' AND UPPER(TRIM(source)) <> UPPER(TRIM(target))
                GROUP BY UPPER(TRIM(target)) ORDER BY packets DESC LIMIT 500""", (call,)).fetchall()
    return [dict(r) for r in rows]


def _coverage(payload: dict) -> dict:
    import json as _json
    from . import coverage
    center, params = payload.get("center"), payload.get("params") or {}
    key = _json.dumps([center, params], sort_keys=True, default=str)
    result = _coverage_cache.get(key)
    if result is None:
        result = coverage.coverage(_tiles(), center, params)
        while len(_coverage_cache) >= COVERAGE_CACHE_SIZE:
            _coverage_cache.pop(next(iter(_coverage_cache)))
        _coverage_cache[key] = result
    return result


def _observed(result: dict) -> dict | None:
    """Cobertura prevista × real: estações que ouviram o transmissor por RF, com o sinal previsto."""
    from . import coverage
    call = result["params"].get("station")
    if not call:
        return None
    positions = {s["name"]: s for s in _known_stations()}
    sens = result["params"]["rx_sensitivity_dbm"]
    items = []
    for row in _heard_from(call):
        st = positions.get(row["callsign"])
        if not st:
            continue
        dbm = coverage.value_at(result, st["lat"], st["lon"])
        items.append({"callsign": row["callsign"], "lat": st["lat"], "lon": st["lon"],
                      "packets": int(row.get("packets") or 0), "last_seen": row.get("last_seen"),
                      "predicted_dbm": dbm, "agrees": dbm is not None and dbm >= sens})
    agree = sum(1 for x in items if x["agrees"])
    return {"station": call, "items": items, "agree": agree, "total": len(items),
            "accuracy_pct": round(100 * agree / len(items)) if items else None}


def _observed_cells(result: dict, limit: int = 800) -> dict:
    """Atividade RF real (células de ~1 km do mapa de calor de Cobertura RF) dentro do raio, com o sinal previsto."""
    import math
    from . import coverage, rf_coverage
    c, p = result["center"], result["params"]
    sens, max_km = p["rx_sensitivity_dbm"], p["max_km"]
    items = []
    for pt in rf_coverage.list_points(0, 8000):
        if pt.get("evidence") != "direct":
            continue
        lat, lon = pt["latitude"], pt["longitude"]
        km = 6371 * math.hypot(math.radians(lat - c["lat"]), math.radians(lon - c["lon"]) * math.cos(math.radians(c["lat"])))
        if km > max_km:
            continue
        dbm = coverage.value_at(result, lat, lon)
        items.append({"lat": lat, "lon": lon, "count": pt["count"], "predicted_dbm": dbm,
                      "agrees": dbm is not None and dbm >= sens})
    agree = sum(1 for x in items if x["agrees"])
    items.sort(key=lambda x: x["count"], reverse=True)
    return {"items": items[:limit], "agree": agree, "total": len(items),
            "accuracy_pct": round(100 * agree / len(items)) if items else None}


def _public(result: dict) -> dict:
    return {k: v for k, v in result.items() if not k.startswith("_")}


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

    @app.post("/api/planning/coverage")
    def api_planning_coverage():
        try:
            result = _coverage(request.get_json(force=True) or {})
            return jsonify({"ok": True, "data": {**_public(result), "observed": _observed(result),
                                                 "observed_cells": _observed_cells(result)}})
        except (ValueError, TypeError, LookupError) as exc:
            return _error(exc)
        except RuntimeError as exc:
            return _error(exc, 502)

    @app.post("/api/planning/highest")
    def api_planning_highest():
        from . import coverage
        try:
            payload = request.get_json(force=True) or {}
            return jsonify({"ok": True, "data": coverage.highest_point(_tiles(), payload.get("center"),
                                                                         payload.get("radius_km"))})
        except (ValueError, TypeError, LookupError) as exc:
            return _error(exc)
        except RuntimeError as exc:
            return _error(exc, 502)

    @app.post("/api/planning/best-coverage")
    def api_planning_best_coverage():
        """Melhor ponto avaliado pela cobertura: área coberta e estações alcançadas por candidato."""
        from . import coverage
        try:
            payload = request.get_json(force=True) or {}
            points = (payload.get("points") or [])[:5]
            if not points:
                raise ValueError("Nenhum ponto para avaliar")
            params = dict(payload.get("params") or {})
            params["max_km"] = float(payload.get("radius_km") or 15)
            params["hires"] = False
            if not 1 <= params["max_km"] <= 30:
                raise ValueError("Raio da avaliação: 1 a 30 km")
            stations = _known_stations()
            out = []
            for i, pt in enumerate(points):
                result = coverage.coverage(_tiles(), [pt.get("lat"), pt.get("lon")], params)
                covered, uncovered, _outside = coverage.classify_nodes(result, stations)
                out.append({"rank": pt.get("rank", i + 1), "lat": result["center"]["lat"], "lon": result["center"]["lon"],
                            "ground_m": result["center"]["ground_m"], "covered_km2": result["covered_km2"],
                            "stations": len(covered), "stations_names": [x["name"] for x in covered[:30]]})
            best = max(out, key=lambda x: (x["stations"], x["covered_km2"]))
            return jsonify({"ok": True, "data": {"radius_km": params["max_km"], "items": out, "best": best["rank"]}})
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
                return _pdf(planning_pdf.link_pdf(_link(payload), name, tile_dir=_data_dir() / "map-tiles"),
                            "PT2VHF-APRS-Analise-de-Enlace.pdf")
            if payload.get("kind") == "coverage":
                from . import coverage
                result = _coverage(payload)                   # reaproveita o último cálculo
                groups = coverage.classify_nodes(result, _known_stations(), result["params"].get("station") or None)
                body = planning_pdf.coverage_pdf(result, payload.get("display"), name, *groups,
                                                 observed=_observed(result), tile_dir=_data_dir() / "map-tiles")
                return _pdf(body, "PT2VHF-APRS-Analise-de-Cobertura.pdf")
            result = planning.best_points(_elev(), payload.get("polygon"), payload.get("reference"),
                                          payload.get("count") or 10)
            links = [{"rank": item.get("rank"), "target": str(item.get("target") or "B")[:40], "link": _link(item)}
                     for item in (payload.get("links") or [])[:20]]
            body = planning_pdf.survey_pdf(result, name, links,
                                           planning_pdf.nearby_stations(db.list_stations(""), result),
                                           tile_dir=_data_dir() / "map-tiles")
            return _pdf(body, "PT2VHF-APRS-Survey-Melhor-Ponto.pdf")
        except (ValueError, TypeError, LookupError) as exc:
            return _error(exc)
        except RuntimeError as exc:
            return _error(exc, 502)
