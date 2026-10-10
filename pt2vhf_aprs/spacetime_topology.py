from __future__ import annotations

"""v1.14.19 — correção espaço-temporal de topologia RF.

Este módulo é um overlay de compatibilidade sobre database.py. Ele mantém as
APIs existentes, mas passa a tratar cada enlace RF como um evento com posição
histórica e timestamp. Isso impede que um digi/tracker móvel conecte, no mesmo
caminho lógico, redes que visitou em momentos e locais diferentes.
"""

from bisect import bisect_left
from datetime import datetime, timedelta, timezone
import threading
import time
from typing import Any

from . import database as db
from . import diagnostics as diag


EVENT_POSITION_MAX_AGE_HOURS = 12.0
ROUTE_TEMPORAL_WINDOW_MINUTES = 30.0
SHARED_NODE_COMPATIBILITY_KM = 25.0
ROUTE_EVENT_SAMPLE_LIMIT = 160
ROUTE_EVENT_BEAM_WIDTH = 24
INFERRED_LONG_HOP_KM = 250.0
GRAPH_CACHE_SECONDS = 20.0

_graph_cache_lock = threading.RLock()
_graph_cache: dict[tuple[float, str], tuple[float, tuple[dict[str, dict[str, dict[str, Any]]], dict[str, tuple[float, float]]]]] = {}
_graph_builds: dict[tuple[float, str], threading.Event] = {}
_graph_build_errors: dict[tuple[float, str], BaseException] = {}


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _invalidate_graph_cache() -> None:
    """Mantém uma pequena janela de cache mesmo durante ingestão APRS contínua.

    Antes, cada pacote novo limpava o cache imediatamente. Em tráfego ativo isso
    fazia várias requisições reconstruírem o mesmo grafo quase ao mesmo tempo.
    Entradas expiram por TTL; dados novos aparecem em até GRAPH_CACHE_SECONDS.
    """
    cutoff = time.monotonic() - GRAPH_CACHE_SECONDS
    with _graph_cache_lock:
        stale = [key for key, value in _graph_cache.items() if value[0] < cutoff]
        for key in stale:
            _graph_cache.pop(key, None)


def _position_at_event_conn(
    conn: Any,
    callsign: str,
    timestamp: str,
) -> tuple[float, float] | None:
    """Retorna a posição mais próxima do instante do evento, nunca a atual."""
    call = str(callsign or "").upper().strip()
    when = _parse_dt(timestamp)
    if not call or when is None:
        return None

    before = conn.execute(
        """SELECT timestamp,latitude,longitude
           FROM tracks
           WHERE UPPER(TRIM(callsign))=? AND timestamp<=?
           ORDER BY timestamp DESC,id DESC LIMIT 1""",
        (call, timestamp),
    ).fetchone()
    after = conn.execute(
        """SELECT timestamp,latitude,longitude
           FROM tracks
           WHERE UPPER(TRIM(callsign))=? AND timestamp>?
           ORDER BY timestamp ASC,id ASC LIMIT 1""",
        (call, timestamp),
    ).fetchone()

    candidates: list[tuple[float, Any]] = []
    for row in (before, after):
        if row is None or not db._valid_geo_position(row["latitude"], row["longitude"]):
            continue
        observed_at = _parse_dt(row["timestamp"])
        if observed_at is None:
            continue
        candidates.append((abs((observed_at - when).total_seconds()) / 3600.0, row))
    if not candidates:
        return None

    age_hours, row = min(candidates, key=lambda item: item[0])
    if age_hours > EVENT_POSITION_MAX_AGE_HOURS:
        return None
    return float(row["latitude"]), float(row["longitude"])


def _ensure_schema_and_backfill() -> int:
    """Adiciona geometria/evidência aos eventos antigos e executa uma única vez."""
    with db.connection() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(topology_events)").fetchall()}
        for column, ddl in (
            ("medium", "TEXT"),
            ("evidence_level", "TEXT"),
            ("source_lat", "REAL"),
            ("source_lon", "REAL"),
            ("target_lat", "REAL"),
            ("target_lon", "REAL"),
            ("raw", "TEXT"),
            ("rx_fingerprint", "TEXT"),
        ):
            if column not in columns:
                conn.execute(f"ALTER TABLE topology_events ADD COLUMN {column} {ddl}")

        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_topology_events_pair_time
               ON topology_events(source,target,kind,timestamp DESC)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations_v1419 (
                   migration_key TEXT PRIMARY KEY,
                   applied_at TEXT NOT NULL
               )"""
        )
        key = "v1.14.19-topology-event-spacetime"
        if conn.execute(
            "SELECT 1 FROM schema_migrations_v1419 WHERE migration_key=?",
            (key,),
        ).fetchone():
            return 0

        track_rows = conn.execute(
            """SELECT UPPER(TRIM(callsign)) AS callsign,timestamp,latitude,longitude
               FROM tracks
               WHERE latitude IS NOT NULL AND longitude IS NOT NULL
               ORDER BY UPPER(TRIM(callsign)),timestamp,id"""
        ).fetchall()
        timelines: dict[str, dict[str, list[Any]]] = {}
        for row in track_rows:
            call = str(row["callsign"] or "")
            when = _parse_dt(row["timestamp"])
            if not call or when is None or not db._valid_geo_position(row["latitude"], row["longitude"]):
                continue
            bucket = timelines.setdefault(call, {"times": [], "positions": []})
            bucket["times"].append(when.timestamp())
            bucket["positions"].append((float(row["latitude"]), float(row["longitude"])))

        edge_rows = conn.execute(
            """SELECT source,target,kind,rf_transport_count,rf_path_count
               FROM topology_edges"""
        ).fetchall()
        evidence: dict[tuple[str, str, str], str] = {}
        for row in edge_rows:
            kind = str(row["kind"] or "").lower()
            direct = int(row["rf_transport_count"] or 0)
            inferred = int(row["rf_path_count"] or 0)
            level = "internet" if kind == "igate" else (
                "direct" if direct > 0 and inferred <= 0 else
                "inferred" if inferred > 0 and direct <= 0 else
                "legacy"
            )
            evidence[(
                str(row["source"] or "").upper().strip(),
                str(row["target"] or "").upper().strip(),
                kind,
            )] = level

        def nearest(call: str, epoch: float) -> tuple[float, float] | None:
            bucket = timelines.get(call)
            if not bucket:
                return None
            times = bucket["times"]
            positions = bucket["positions"]
            index = bisect_left(times, epoch)
            candidates: list[int] = []
            if index < len(times):
                candidates.append(index)
            if index > 0:
                candidates.append(index - 1)
            if not candidates:
                return None
            best = min(candidates, key=lambda idx: abs(times[idx] - epoch))
            if abs(times[best] - epoch) > EVENT_POSITION_MAX_AGE_HOURS * 3600.0:
                return None
            return positions[best]

        rows = conn.execute(
            """SELECT id,timestamp,source,target,kind
               FROM topology_events
               WHERE source_lat IS NULL OR source_lon IS NULL
                  OR target_lat IS NULL OR target_lon IS NULL
                  OR evidence_level IS NULL
               ORDER BY id"""
        ).fetchall()

        updated = 0
        batch: list[tuple[Any, ...]] = []
        for row in rows:
            when = _parse_dt(row["timestamp"])
            if when is None:
                continue
            source = str(row["source"] or "").upper().strip()
            target = str(row["target"] or "").upper().strip()
            kind = str(row["kind"] or "").lower()
            source_pos = nearest(source, when.timestamp())
            target_pos = nearest(target, when.timestamp())
            level = evidence.get((source, target, kind), "legacy" if kind == "rf" else "internet")
            medium = "RF" if level == "direct" else ("APRS-IS" if level in {"inferred", "internet"} else None)
            batch.append((
                medium,
                level,
                source_pos[0] if source_pos else None,
                source_pos[1] if source_pos else None,
                target_pos[0] if target_pos else None,
                target_pos[1] if target_pos else None,
                row["id"],
            ))
            if len(batch) >= 5000:
                conn.executemany(
                    """UPDATE topology_events
                       SET medium=COALESCE(medium,?),
                           evidence_level=COALESCE(evidence_level,?),
                           source_lat=COALESCE(source_lat,?),
                           source_lon=COALESCE(source_lon,?),
                           target_lat=COALESCE(target_lat,?),
                           target_lon=COALESCE(target_lon,?)
                       WHERE id=?""",
                    batch,
                )
                updated += len(batch)
                batch.clear()
        if batch:
            conn.executemany(
                """UPDATE topology_events
                   SET medium=COALESCE(medium,?),
                       evidence_level=COALESCE(evidence_level,?),
                       source_lat=COALESCE(source_lat,?),
                       source_lon=COALESCE(source_lon,?),
                       target_lat=COALESCE(target_lat,?),
                       target_lon=COALESCE(target_lon,?)
                   WHERE id=?""",
                batch,
            )
            updated += len(batch)

        conn.execute(
            "INSERT INTO schema_migrations_v1419(migration_key,applied_at) VALUES(?,?)",
            (key, db.utc_now_iso()),
        )
    diag.log_event("topology_spacetime_backfill", events=updated)
    _invalidate_graph_cache()
    return updated


def _record_topology_from_raw_conn(conn: Any, raw: str, medium: str = "APRS-IS") -> None:
    observed_medium = str(medium or "APRS-IS").upper().strip()
    if observed_medium not in {"RF", "APRS-IS"}:
        observed_medium = "APRS-IS"
    _source, edges = db._observed_topology_edges(raw, observed_medium)
    if not edges:
        return
    now = db.utc_now_iso()

    for edge_source, target, kind, edge_igate in edges:
        rf_transport = 1 if observed_medium == "RF" and kind == "rf" else 0
        rf_path = 1 if observed_medium != "RF" and kind == "rf" else 0
        internet_confirmed = 1 if observed_medium == "APRS-IS" and kind == "igate" else 0
        conn.execute(
            """INSERT INTO topology_edges(
                   source,target,kind,packet_count,first_seen,last_seen,igate,
                   rf_transport_count,rf_path_count,internet_confirmed_count
               ) VALUES(?,?,?,1,?,?,?,?,?,?)
               ON CONFLICT(source,target,kind) DO UPDATE SET
                   packet_count=topology_edges.packet_count+1,
                   last_seen=excluded.last_seen,
                   igate=COALESCE(excluded.igate,topology_edges.igate),
                   rf_transport_count=topology_edges.rf_transport_count+excluded.rf_transport_count,
                   rf_path_count=topology_edges.rf_path_count+excluded.rf_path_count,
                   internet_confirmed_count=topology_edges.internet_confirmed_count+excluded.internet_confirmed_count""",
            (
                edge_source, target, kind, now, now, edge_igate,
                rf_transport, rf_path, internet_confirmed,
            ),
        )
        source_pos = _position_at_event_conn(conn, edge_source, now)
        target_pos = _position_at_event_conn(conn, target, now)
        evidence_level = (
            "internet" if kind == "igate" else
            "direct" if observed_medium == "RF" else
            "inferred"
        )
        conn.execute(
            """INSERT INTO topology_events(
                   timestamp,source,target,kind,medium,evidence_level,
                   source_lat,source_lon,target_lat,target_lon,raw,rx_fingerprint
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                now, edge_source, target, kind, observed_medium, evidence_level,
                source_pos[0] if source_pos else None,
                source_pos[1] if source_pos else None,
                target_pos[0] if target_pos else None,
                target_pos[1] if target_pos else None,
                str(raw or ""),
                db._packet_reception_fingerprint(raw, edge_source),
            ),
        )

    if db._retention_due("topology_events", len(edges)):
        deleted = db._trim_history_table(conn, "topology_events", db.TOPOLOGY_EVENT_RETENTION)
        if deleted:
            diag.log_event("retention_sweep", table="topology_events", deleted=deleted)
    _invalidate_graph_cache()


def _process_received_packet(
    raw: str,
    parsed: dict[str, Any],
    from_call: str | None = None,
    packet_format: str | None = None,
    *,
    medium: str = "APRS-IS",
) -> None:
    """Persiste primeiro a posição do remetente e depois congela o evento RF."""
    started = time.monotonic()
    with db.connection() as conn:
        db._add_aprs_log_conn(conn, "RX", raw)
        db._record_packet_conn(conn, raw, from_call, packet_format, medium=medium)
        if parsed and parsed.get("from"):
            db._upsert_station_conn(conn, parsed)
        _record_topology_from_raw_conn(conn, raw, medium)
    if parsed and parsed.get("from"):
        db.invalidate_map_data_cache(drop_payload=False, coalesce=True)
    elapsed_ms = (time.monotonic() - started) * 1000.0
    if elapsed_ms >= 250:
        diag.log_event(
            "rx_transaction_slow",
            duration_ms=round(elapsed_ms, 1),
            from_call=from_call or "",
            packet_format=packet_format or "",
            medium=str(medium or "APRS-IS").upper(),
        )


def _route_graph(hours: float = 0):
    """Retorna o grafo RF com cache TTL e single-flight por período/banco.

    Se várias requisições perderem o cache simultaneamente, somente uma delas
    monta o grafo. As demais aguardam o mesmo resultado em vez de saturar todos
    os workers do servidor com reconstruções idênticas.
    """
    try:
        normalized_hours = float(hours or 0)
    except (TypeError, ValueError):
        normalized_hours = 0.0
    normalized_hours = max(0.25, min(normalized_hours, 24 * 30)) if normalized_hours > 0 else 0.0

    # Extensões/testes podem substituir a fonte legada de topologia. Nesse
    # cenário o cache normal não é válido, porque a função substituta pode
    # representar um snapshot diferente a cada chamada.
    if db.list_topology_edges is not _original_list_topology_edges:
        return _build_route_graph_uncached(normalized_hours)

    key = (normalized_hours, str(db.DB_PATH))
    started = time.monotonic()

    with _graph_cache_lock:
        cached = _graph_cache.get(key)
        if cached and started - cached[0] <= GRAPH_CACHE_SECONDS:
            return cached[1]
        waiter = _graph_builds.get(key)
        if waiter is None:
            waiter = threading.Event()
            _graph_builds[key] = waiter
            _graph_build_errors.pop(key, None)
            owner = True
        else:
            owner = False

    if not owner:
        wait_started = time.monotonic()
        waiter.wait(timeout=60.0)
        waited_ms = (time.monotonic() - wait_started) * 1000.0
        with _graph_cache_lock:
            cached = _graph_cache.get(key)
            error = _graph_build_errors.get(key)
        if cached:
            if waited_ms >= 250:
                diag.log_event(
                    "rf_route_graph_singleflight_wait",
                    hours=normalized_hours,
                    duration_ms=round(waited_ms, 1),
                )
            return cached[1]
        if error is not None:
            raise RuntimeError(f"Falha ao construir grafo RF: {error}") from error
        # Proteção caso o owner morra ou ultrapasse o timeout.
        diag.log_event(
            "rf_route_graph_singleflight_timeout",
            hours=normalized_hours,
            duration_ms=round(waited_ms, 1),
        )
        return _build_route_graph_uncached(normalized_hours)

    try:
        payload = _build_route_graph_uncached(normalized_hours)
        with _graph_cache_lock:
            _graph_cache[key] = (time.monotonic(), payload)
        elapsed_ms = (time.monotonic() - started) * 1000.0
        if elapsed_ms >= 250:
            diag.log_event(
                "rf_route_graph_build",
                hours=normalized_hours,
                duration_ms=round(elapsed_ms, 1),
                nodes=len(payload[0]),
            )
        return payload
    except BaseException as exc:
        with _graph_cache_lock:
            _graph_build_errors[key] = exc
        raise
    finally:
        with _graph_cache_lock:
            event = _graph_builds.pop(key, None)
            if event is not None:
                event.set()


def _build_route_graph_uncached(hours: float = 0):
    try:
        hours = float(hours or 0)
    except (TypeError, ValueError):
        hours = 0.0
    hours = max(0.25, min(hours, 24 * 30)) if hours > 0 else 0.0
    graph: dict[str, dict[str, dict[str, Any]]] = {}
    positions: dict[str, tuple[float, float]] = {}
    position_seen: dict[str, float] = {}
    merged: dict[tuple[str, str], dict[str, Any]] = {}

    params: list[Any] = []
    where = "WHERE te.kind='rf'"
    if hours > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
        where += " AND te.timestamp>=?"
        params.append(cutoff)

    try:
        with db.connection() as conn:
            rows = conn.execute(
                f"""SELECT te.id,te.timestamp,te.source,te.target,te.medium,
                           te.evidence_level,te.source_lat,te.source_lon,
                           te.target_lat,te.target_lon,te.raw,te.rx_fingerprint,
                           e.rf_transport_count,e.rf_path_count
                    FROM topology_events te
                    LEFT JOIN topology_edges e
                      ON e.source=te.source AND e.target=te.target AND e.kind=te.kind
                    {where}
                    ORDER BY te.timestamp ASC,te.id ASC""",
                params,
            ).fetchall()
    except Exception as exc:
        # Compatibilidade com bancos/testes que ainda não executaram init_db().
        # O fallback conserva o comportamento legado sem afetar bancos já
        # migrados para o modelo espaço-temporal.
        if "no such table" in str(exc).lower() or "no such column" in str(exc).lower():
            return _original_route_graph(hours)
        raise

    for row in rows:
        source = db._rf_route_callsign(row["source"])
        target = db._rf_route_callsign(row["target"])
        if not source or not target or source == target:
            continue
        if not (
            db._valid_geo_position(row["source_lat"], row["source_lon"])
            and db._valid_geo_position(row["target_lat"], row["target_lon"])
        ):
            continue
        when = _parse_dt(row["timestamp"])
        if when is None:
            continue
        epoch = when.timestamp()
        a, b = sorted((source, target))
        if source == a:
            a_lat, a_lon = float(row["source_lat"]), float(row["source_lon"])
            b_lat, b_lon = float(row["target_lat"]), float(row["target_lon"])
        else:
            a_lat, a_lon = float(row["target_lat"]), float(row["target_lon"])
            b_lat, b_lon = float(row["source_lat"]), float(row["source_lon"])

        level = str(row["evidence_level"] or "").lower().strip()
        if level not in {"direct", "inferred", "legacy"}:
            direct = int(row["rf_transport_count"] or 0)
            inferred = int(row["rf_path_count"] or 0)
            level = (
                "direct" if direct > 0 and inferred <= 0 else
                "inferred" if inferred > 0 and direct <= 0 else
                "legacy"
            )

        event = {
            "id": int(row["id"]),
            "timestamp": str(row["timestamp"] or ""),
            "_epoch": epoch,
            "a_lat": a_lat,
            "a_lon": a_lon,
            "b_lat": b_lat,
            "b_lon": b_lon,
            "distance_km": round(db.haversine_km(a_lat, a_lon, b_lat, b_lon), 3),
            "evidence_level": level,
            "medium": str(row["medium"] or ""),
            "raw": str(row["raw"] or ""),
            "rx_fingerprint": str(row["rx_fingerprint"] or ""),
            "position_quality": "event_time",
        }
        item = merged.setdefault((a, b), {
            "a": a,
            "b": b,
            "packet_count": 0,
            "first_seen": event["timestamp"],
            "last_seen": event["timestamp"],
            "distance_km": event["distance_km"],
            "classification_source": "RF observado",
            "rf_transport_count": 0,
            "rf_path_count": 0,
            "events": [],
        })
        item["events"].append(event)
        item["packet_count"] = int(item["packet_count"]) + 1
        item["first_seen"] = min(str(item["first_seen"]), event["timestamp"])
        item["last_seen"] = max(str(item["last_seen"]), event["timestamp"])
        item["distance_km"] = event["distance_km"]
        if level == "direct":
            item["rf_transport_count"] = int(item["rf_transport_count"]) + 1
        elif level == "inferred":
            item["rf_path_count"] = int(item["rf_path_count"]) + 1

        for call, lat, lon in ((a, a_lat, a_lon), (b, b_lat, b_lon)):
            if epoch >= position_seen.get(call, float("-inf")):
                positions[call] = (lat, lon)
                position_seen[call] = epoch

    # Preserva enlaces históricos legados que existam em topology_edges mas
    # não possuam eventos espaço-temporais utilizáveis. Isso evita que um enlace
    # antigo simplesmente desapareça do período Completo após uma migração.
    try:
        legacy_rows = _original_list_topology_edges(hours)
    except Exception:
        legacy_rows = []
    for raw in legacy_rows:
        if str(raw.get("kind") or "").lower() == "igate":
            continue
        source = db._rf_route_callsign(raw.get("source"))
        target = db._rf_route_callsign(raw.get("target"))
        if not source or not target or source == target:
            continue
        a, b = sorted((source, target))
        if (a, b) in merged:
            continue
        slat, slon = raw.get("source_lat"), raw.get("source_lon")
        tlat, tlon = raw.get("target_lat"), raw.get("target_lon")
        if not (db._valid_geo_position(slat, slon) and db._valid_geo_position(tlat, tlon)):
            continue
        if source == a:
            a_lat, a_lon = float(slat), float(slon)
            b_lat, b_lon = float(tlat), float(tlon)
        else:
            a_lat, a_lon = float(tlat), float(tlon)
            b_lat, b_lon = float(slat), float(slon)
        when = _parse_dt(raw.get("last_seen")) or datetime.now(timezone.utc)
        epoch = when.timestamp()
        event = {
            "id": 0,
            "timestamp": str(raw.get("last_seen") or when.isoformat(timespec="seconds")),
            "_epoch": epoch,
            "a_lat": a_lat,
            "a_lon": a_lon,
            "b_lat": b_lat,
            "b_lon": b_lon,
            "distance_km": round(db.haversine_km(a_lat, a_lon, b_lat, b_lon), 3),
            "evidence_level": "legacy",
            "medium": "RF",
            "raw": "",
            "rx_fingerprint": "",
            "position_quality": "legacy_current_fallback",
        }
        merged[(a, b)] = {
            "a": a,
            "b": b,
            "packet_count": int(raw.get("packet_count") or 0),
            "first_seen": str(raw.get("first_seen") or ""),
            "last_seen": str(raw.get("last_seen") or ""),
            "distance_km": event["distance_km"],
            "classification_source": "RF histórico legado",
            "rf_transport_count": int(raw.get("rf_transport_count") or 0),
            "rf_path_count": int(raw.get("rf_path_count") or 0),
            "events": [event],
            "legacy_fallback": True,
        }
        for call, lat, lon in ((a, a_lat, a_lon), (b, b_lat, b_lon)):
            if epoch >= position_seen.get(call, float("-inf")):
                positions[call] = (lat, lon)
                position_seen[call] = epoch

    for (a, b), edge in merged.items():
        edge["events"].sort(key=lambda event: (float(event.get("_epoch") or 0.0), int(event.get("id") or 0)))
        if edge.get("legacy_fallback"):
            edge["classification_source"] = "RF histórico legado"
        elif int(edge["rf_transport_count"]) > 0:
            edge["classification_source"] = "RF direto do transporte"
        elif int(edge["rf_path_count"]) > 0:
            edge["classification_source"] = "RF inferido do path"
        else:
            edge["classification_source"] = "RF observado (legado)"
        graph.setdefault(a, {})[b] = edge
        graph.setdefault(b, {})[a] = edge

    return graph, positions


def _event_epoch(event: dict[str, Any]) -> float | None:
    value = event.get("_epoch")
    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            pass
    when = _parse_dt(event.get("timestamp"))
    return when.timestamp() if when is not None else None


def _event_position(node: str, edge: dict[str, Any], event: dict[str, Any]) -> tuple[float, float] | None:
    if node == str(edge.get("a") or ""):
        lat, lon = event.get("a_lat"), event.get("a_lon")
    elif node == str(edge.get("b") or ""):
        lat, lon = event.get("b_lat"), event.get("b_lon")
    else:
        return None
    if not db._valid_geo_position(lat, lon):
        return None
    return float(lat), float(lon)


def _sample_route_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Amostra o histórico sem privilegiar apenas a posição atual de um móvel."""
    ordered = sorted(
        [event for event in events if _event_epoch(event) is not None],
        key=lambda event: (float(_event_epoch(event) or 0.0), int(event.get("id") or 0)),
    )
    if len(ordered) <= ROUTE_EVENT_SAMPLE_LIMIT:
        return ordered
    last = len(ordered) - 1
    indexes = {
        round(index * last / (ROUTE_EVENT_SAMPLE_LIMIT - 1))
        for index in range(ROUTE_EVENT_SAMPLE_LIMIT)
    }
    return [ordered[index] for index in sorted(indexes)]


def _compatible_events(nodes: list[str], graph: dict[str, dict[str, dict[str, Any]]]):
    """Seleciona uma evidência histórica por hop preservando o local do nó intermediário.

    Os hops podem ter sido observados em momentos diferentes. A composição só é
    aceita quando o mesmo nó intermediário aparece em coordenadas compatíveis
    nas duas evidências adjacentes. Assim, um tracker que viajou centenas de
    quilômetros não conecta artificialmente as redes visitadas durante a viagem.
    """
    if len(nodes) < 2:
        return []

    edges: list[dict[str, Any]] = []
    event_lists: list[list[dict[str, Any]]] = []
    for a, b in zip(nodes, nodes[1:]):
        edge = graph.get(a, {}).get(b)
        if not edge:
            return None
        events = _sample_route_events(list(edge.get("events") or []))
        if not events:
            return None
        edges.append(edge)
        event_lists.append(events)

    # Beam search: minimiza a divergência espacial nos nós compartilhados.
    states: list[tuple[float, float, list[dict[str, Any]]]] = []
    for event in event_lists[0]:
        epoch = float(_event_epoch(event) or 0.0)
        states.append((0.0, -epoch, [event]))
    states.sort(key=lambda item: (item[0], item[1]))
    states = states[:ROUTE_EVENT_BEAM_WIDTH]

    for edge_index in range(1, len(edges)):
        shared_node = nodes[edge_index]
        next_states: list[tuple[float, float, list[dict[str, Any]]]] = []
        for score, _recency, chosen in states:
            previous_event = chosen[-1]
            previous_pos = _event_position(shared_node, edges[edge_index - 1], previous_event)
            if previous_pos is None:
                continue
            for event in event_lists[edge_index]:
                current_pos = _event_position(shared_node, edges[edge_index], event)
                if current_pos is None:
                    continue
                mismatch_km = db.haversine_km(*previous_pos, *current_pos)
                if mismatch_km > SHARED_NODE_COMPATIBILITY_KM:
                    continue
                epochs = [float(_event_epoch(item) or 0.0) for item in chosen]
                epochs.append(float(_event_epoch(event) or 0.0))
                newest = max(epochs)
                next_states.append((
                    score + mismatch_km,
                    -newest,
                    chosen + [event],
                ))
        if not next_states:
            return None
        next_states.sort(key=lambda item: (item[0], item[1]))
        states = next_states[:ROUTE_EVENT_BEAM_WIDTH]

    return states[0][2] if states else None


def _reachability_class(selected_events: list[dict[str, Any]]) -> tuple[str, float | None]:
    if not selected_events:
        return "legacy", None
    epochs = [float(_event_epoch(event) or 0.0) for event in selected_events]
    span_minutes = (max(epochs) - min(epochs)) / 60.0 if epochs else 0.0
    raws = [str(event.get("raw") or "") for event in selected_events]
    timestamps = [str(event.get("timestamp") or "") for event in selected_events]
    same_packet = bool(raws and all(raws) and len(set(raws)) == 1 and len(set(timestamps)) == 1)
    if same_packet:
        return "same_packet", round(span_minutes, 2)
    if span_minutes <= ROUTE_TEMPORAL_WINDOW_MINUTES:
        return "contemporary", round(span_minutes, 2)
    return "historical", round(span_minutes, 2)



def _edge_payload(source: str, target: str, edge: dict[str, Any], positions, event=None):
    selected = event or ((edge.get("events") or [None])[-1])
    if selected is not None:
        a, b = str(edge.get("a") or ""), str(edge.get("b") or "")
        if source == a and target == b:
            source_lat, source_lon = selected.get("a_lat"), selected.get("a_lon")
            target_lat, target_lon = selected.get("b_lat"), selected.get("b_lon")
        elif source == b and target == a:
            source_lat, source_lon = selected.get("b_lat"), selected.get("b_lon")
            target_lat, target_lon = selected.get("a_lat"), selected.get("a_lon")
        else:
            return None
        if not (db._valid_geo_position(source_lat, source_lon) and db._valid_geo_position(target_lat, target_lon)):
            return None
        level = str(selected.get("evidence_level") or "legacy")
        label = {
            "direct": "RF direto observado",
            "inferred": "RF inferido do path",
            "legacy": "RF observado (legado)",
        }.get(level, "RF observado (legado)")
        observed_at = str(selected.get("timestamp") or edge.get("last_seen") or "")
        return {
            "source": source,
            "target": target,
            "source_lat": float(source_lat),
            "source_lon": float(source_lon),
            "target_lat": float(target_lat),
            "target_lon": float(target_lon),
            "distance_km": round(db.haversine_km(float(source_lat), float(source_lon), float(target_lat), float(target_lon)), 3),
            "packet_count": int(edge.get("packet_count") or 0),
            "first_seen": edge.get("first_seen") or "",
            "last_seen": observed_at,
            "event_at": observed_at,
            "classification_source": label,
            "rf_transport_count": int(edge.get("rf_transport_count") or 0),
            "rf_path_count": int(edge.get("rf_path_count") or 0),
            "evidence_level": level,
            "evidence_label": label,
            "event_id": selected.get("id"),
            "position_quality": str(selected.get("position_quality") or "event_time"),
        }

    if source not in positions or target not in positions:
        return None
    level, label = db._rf_route_evidence(edge)
    return {
        "source": source,
        "target": target,
        "source_lat": positions[source][0],
        "source_lon": positions[source][1],
        "target_lat": positions[target][0],
        "target_lon": positions[target][1],
        "distance_km": round(float(edge.get("distance_km") or 0.0), 3),
        "packet_count": int(edge.get("packet_count") or 0),
        "first_seen": edge.get("first_seen") or "",
        "last_seen": edge.get("last_seen") or "",
        "classification_source": edge.get("classification_source") or label,
        "rf_transport_count": int(edge.get("rf_transport_count") or 0),
        "rf_path_count": int(edge.get("rf_path_count") or 0),
        "evidence_level": level,
        "evidence_label": label,
    }


def _route_payload(nodes, graph, positions, *, refine_inferred=True):
    if len(nodes) < 2:
        return None

    original_nodes = list(nodes)
    reconstructed: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    reconstructed_pairs: dict[tuple[str, str], str] = {}
    if refine_inferred:
        nodes, reconstructed, unresolved, reconstructed_pairs = db._rf_refine_route_nodes(list(nodes), graph, positions)

    route_graph_edges = [graph.get(a, {}).get(b) for a, b in zip(nodes, nodes[1:])]
    if any(edge is None for edge in route_graph_edges):
        return None

    # Um hop inferido longo sem intermediários conhecidos não pode ser tratado
    # como um único enlace físico. A busca de rotas deve continuar procurando
    # uma cadeia histórica A->B->C... no grafo.
    unresolved_long: list[dict[str, Any]] = []
    reconstructed_original_pairs = {
        tuple(sorted((str(item.get("source") or ""), str(item.get("target") or ""))))
        for item in reconstructed
    }
    for a, b, edge in zip(nodes, nodes[1:], route_graph_edges):
        level, _label = db._rf_route_evidence(edge)
        events = list(edge.get("events") or [])
        event_distances = [
            float(event.get("distance_km") or 0.0)
            for event in events
            if float(event.get("distance_km") or 0.0) > 0
        ]
        edge_distance = min(event_distances) if event_distances else float(edge.get("distance_km") or 0.0)
        pair = tuple(sorted((a, b)))
        if level == "inferred" and edge_distance >= INFERRED_LONG_HOP_KM and pair not in reconstructed_original_pairs:
            unresolved_long.append({
                "source": a,
                "target": b,
                "distance_km": round(edge_distance, 3),
                "reason": "cadeia RF incompleta",
            })
    if unresolved_long:
        return None

    event_graph = all(bool(edge.get("events")) for edge in route_graph_edges if edge)
    selected_events = _compatible_events(nodes, graph) if event_graph else None
    if event_graph and selected_events is None:
        return None

    route_edges: list[dict[str, Any]] = []
    total = 0.0
    observations = 0
    latest_values: list[str] = []
    counts = {"direct": 0, "inferred": 0, "legacy": 0}
    for index, (a, b) in enumerate(zip(nodes, nodes[1:])):
        edge = graph.get(a, {}).get(b)
        event = selected_events[index] if selected_events is not None else None
        payload = _edge_payload(a, b, edge, positions, event)
        if not payload:
            return None
        pair = tuple(sorted((a, b)))
        payload["reconstructed"] = pair in reconstructed_pairs
        if pair in reconstructed_pairs:
            payload["reconstructed_from"] = reconstructed_pairs[pair]
        total += float(payload.get("distance_km") or 0.0)
        observations += int(payload.get("packet_count") or 0)
        if payload.get("last_seen"):
            latest_values.append(str(payload["last_seen"]))
        level = str(payload.get("evidence_level") or "legacy")
        counts[level] = counts.get(level, 0) + 1
        route_edges.append(payload)

    if selected_events is not None:
        epochs = [float(_event_epoch(event) or 0.0) for event in selected_events]
        start_epoch, end_epoch = min(epochs), max(epochs)
        route_start = datetime.fromtimestamp(start_epoch, timezone.utc).replace(microsecond=0).isoformat()
        route_end = datetime.fromtimestamp(end_epoch, timezone.utc).replace(microsecond=0).isoformat()
        reachability_class, span_minutes = _reachability_class(selected_events)
        direct = round(db.haversine_km(
            float(route_edges[0]["source_lat"]), float(route_edges[0]["source_lon"]),
            float(route_edges[-1]["target_lat"]), float(route_edges[-1]["target_lon"]),
        ), 3)
    else:
        route_start = min(latest_values) if latest_values else ""
        route_end = max(latest_values) if latest_values else ""
        span_minutes = None
        reachability_class = "legacy"
        direct = round(db.haversine_km(*positions[nodes[0]], *positions[nodes[-1]]), 3)

    evidence_class = (
        "mixed" if counts["direct"] and (counts["inferred"] or counts["legacy"])
        else "inferred" if counts["inferred"] or counts["legacy"]
        else "direct"
    )
    reconstructed_nodes: list[str] = []
    for item in reconstructed:
        for call in item.get("intermediate_nodes") or []:
            call = str(call or "")
            if call and call not in reconstructed_nodes:
                reconstructed_nodes.append(call)

    return {
        "source": nodes[0],
        "target": nodes[-1],
        "nodes": nodes,
        "original_nodes": original_nodes,
        "hops": len(nodes) - 1,
        "distance_km": round(total, 3),
        "direct_distance_km": direct,
        "route_evidence_at": route_end,
        "route_evidence_start": route_start,
        "route_evidence_end": route_end,
        "temporal_span_minutes": span_minutes,
        "temporal_window_minutes": ROUTE_TEMPORAL_WINDOW_MINUTES,
        "spatiotemporal_validated": selected_events is not None,
        "reachability_class": reachability_class,
        "historical_reachability": reachability_class == "historical",
        "same_packet_observed": reachability_class == "same_packet",
        "observations": observations,
        "direct_edges": counts["direct"],
        "inferred_edges": counts["inferred"],
        "legacy_edges": counts["legacy"],
        "route_evidence_class": evidence_class,
        "refinement_applied": bool(reconstructed),
        "reconstructed_intermediate_nodes": reconstructed_nodes,
        "reconstructed_segments": reconstructed,
        "unresolved_inferred_edges": [],
        "edges": route_edges,
    }



def _list_rf_route_candidates(source: str, hours: float = 0, query: str = "", limit: int = 80):
    """Destinos realmente alcançáveis por uma cadeia RF espacialmente compatível."""
    source_call = db._rf_route_callsign(source)
    if not source_call:
        return []
    query_norm = str(query or "").upper().strip()
    graph, positions = _route_graph(hours)
    if source_call not in graph:
        return []

    queue: list[list[str]] = [[source_call]]
    best_hops: dict[str, int] = {source_call: 0}
    candidates: dict[str, dict[str, Any]] = {}
    max_hops = 12

    while queue:
        path = queue.pop(0)
        node = path[-1]
        if len(path) - 1 >= max_hops:
            continue
        neighbors = sorted(
            graph.get(node, {}).items(),
            key=lambda pair: (
                -int(pair[1].get("packet_count") or 0),
                str(pair[1].get("last_seen") or ""),
                pair[0],
            ),
        )
        for nxt, edge in neighbors:
            if nxt in path:
                continue
            next_path = path + [nxt]
            payload = _route_payload(next_path, graph, positions, refine_inferred=False)
            if not payload:
                continue
            hops = len(next_path) - 1
            previous_hops = best_hops.get(nxt)
            if previous_hops is None or hops < previous_hops:
                best_hops[nxt] = hops
                queue.append(next_path)
            if query_norm and query_norm not in nxt:
                continue
            current = candidates.get(nxt)
            candidate = {
                "callsign": nxt,
                "hops": hops,
                "last_seen": str(payload.get("route_evidence_end") or edge.get("last_seen") or ""),
                "packet_count": int(payload.get("observations") or edge.get("packet_count") or 0),
                "reachability_class": str(payload.get("reachability_class") or "historical"),
            }
            if current is None or hops < int(current.get("hops") or 999):
                candidates[nxt] = candidate

    rows = list(candidates.values())
    rows.sort(key=lambda item: (
        0 if query_norm and str(item["callsign"]).startswith(query_norm) else 1,
        int(item.get("hops") or 0),
        -int(item.get("packet_count") or 0),
        str(item.get("callsign") or ""),
    ))
    return rows[: max(1, min(int(limit or 80), 200))]


def _route_records(hours: float = 0, limit: int = 10, max_hops: int = 6, beam_width: int = 500):
    """Ranking de alcançabilidade RF, incluindo rotas multi-hop históricas."""
    graph, positions = _route_graph(hours)
    route_limit = max(1, min(int(limit or 10), 50))
    hop_limit = max(1, min(int(max_hops or 6), 12))
    per_state_limit = 3
    max_expansions = max(4000, min(50000, int(beam_width or 500) * 40))

    # Mantém a melhor rota conhecida para cada par de extremidades. Diferente da
    # antiga BFS com visited global, caminhos alternativos podem alcançar o mesmo
    # nó e continuar a partir dele, o que é necessário em malhas multi-hop.
    best_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    expansions = 0

    for source in sorted(graph):
        if source not in positions:
            continue
        queue: list[list[str]] = [[source]]
        state_counts: dict[tuple[str, int], int] = {(source, 0): 1}

        while queue and expansions < max_expansions:
            path = queue.pop(0)
            node = path[-1]
            hops = len(path) - 1
            if hops >= hop_limit:
                continue

            neighbors = sorted(
                graph.get(node, {}).items(),
                key=lambda pair: (
                    int(pair[1].get("packet_count") or 0),
                    str(pair[1].get("last_seen") or ""),
                ),
                reverse=True,
            )
            for nxt, _edge in neighbors:
                if nxt in path:
                    continue
                next_path = path + [nxt]
                expansions += 1
                if expansions >= max_expansions:
                    break

                payload = _route_payload(next_path, graph, positions, refine_inferred=False)
                if not payload:
                    continue

                next_hops = len(next_path) - 1
                state_key = (nxt, next_hops)
                count = state_counts.get(state_key, 0)
                if count < per_state_limit:
                    state_counts[state_key] = count + 1
                    queue.append(next_path)

                if nxt not in positions or source >= nxt:
                    continue
                pair = (source, nxt)
                candidate = dict(payload)
                candidate["_path"] = list(next_path)
                candidate["_sort"] = (
                    float(payload.get("direct_distance_km") or 0.0),
                    int(payload.get("observations") or 0),
                    int(payload.get("hops") or 0),
                    str(payload.get("route_evidence_end") or ""),
                )
                current = best_by_pair.get(pair)
                if current is None:
                    best_by_pair[pair] = candidate
                else:
                    # Para o mesmo par, prefere evidência mais forte/recorrente e
                    # depois menos hops. A distância entre extremidades é a mesma.
                    current_quality = (
                        int(current.get("direct_edges") or 0),
                        -int(current.get("inferred_edges") or 0),
                        int(current.get("observations") or 0),
                        -int(current.get("hops") or 0),
                    )
                    candidate_quality = (
                        int(candidate.get("direct_edges") or 0),
                        -int(candidate.get("inferred_edges") or 0),
                        int(candidate.get("observations") or 0),
                        -int(candidate.get("hops") or 0),
                    )
                    if candidate_quality > current_quality:
                        best_by_pair[pair] = candidate

    candidates = list(best_by_pair.values())
    candidates.sort(
        key=lambda item: (
            float(item.get("direct_distance_km") or 0.0),
            int(item.get("hops") or 0),
            int(item.get("observations") or 0),
            str(item.get("route_evidence_end") or ""),
        ),
        reverse=True,
    )

    result: list[dict[str, Any]] = []
    for candidate in candidates[:route_limit]:
        candidate.pop("_path", None)
        candidate.pop("_sort", None)
        candidate["rank"] = len(result) + 1
        candidate["multi_hop"] = int(candidate.get("hops") or 0) > 1
        result.append(candidate)
    return result


_original_init_db = db.init_db
_original_route_graph = db._rf_route_graph
_original_list_topology_edges = db.list_topology_edges
_original_list_rf_routes = db.list_rf_routes


def _init_db() -> None:
    _original_init_db()
    _ensure_schema_and_backfill()


def _list_rf_routes(*args: Any, **kwargs: Any) -> dict[str, Any]:
    payload = _original_list_rf_routes(*args, **kwargs)
    routes = payload.get("routes") or []
    if routes:
        payload["direct_distance_km"] = routes[0].get("direct_distance_km")

    # Não mostrar como corredor físico uma aresta inferida longa que não tenha
    # sido decomposta em uma rota válida com nós intermediários.
    allowed_pairs = {
        tuple(sorted((str(edge.get("source") or ""), str(edge.get("target") or ""))))
        for route in routes
        for edge in (route.get("edges") or [])
    }
    filtered_edges = []
    for edge in payload.get("eligible_edges") or []:
        pair = tuple(sorted((str(edge.get("source") or ""), str(edge.get("target") or ""))))
        level = str(edge.get("evidence_level") or "legacy")
        distance = float(edge.get("distance_km") or 0.0)
        if level == "inferred" and distance >= INFERRED_LONG_HOP_KM and pair not in allowed_pairs:
            continue
        filtered_edges.append(edge)
    payload["eligible_edges"] = filtered_edges
    payload["eligible_edge_count"] = len(filtered_edges)
    payload["temporal_window_minutes"] = ROUTE_TEMPORAL_WINDOW_MINUTES
    payload["route_semantics"] = "historical_reachability"
    return payload


def install() -> None:
    """Instala o modelo v1.14.22 de alcançabilidade RF histórica."""
    # Refinamento pode usar enlaces observados em momentos distintos; a
    # validação espacial por coordenadas históricas é feita em _route_payload.
    db.RF_INFERRED_REFINEMENT_WINDOW_HOURS = 24.0 * 3650.0
    db.RF_INFERRED_REFINEMENT_MAX_HOPS = max(int(getattr(db, "RF_INFERRED_REFINEMENT_MAX_HOPS", 5)), 12)
    db.init_db = _init_db
    db._record_topology_from_raw_conn = _record_topology_from_raw_conn
    db.process_received_packet = _process_received_packet
    db._rf_route_graph = _route_graph
    db._rf_route_edge_payload = _edge_payload
    db._rf_route_payload = _route_payload
    db.list_rf_route_candidates = _list_rf_route_candidates
    db.list_rf_route_records = _route_records
    db.list_rf_routes = _list_rf_routes
