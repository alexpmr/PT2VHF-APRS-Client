"""Verificação do banco SQLite sem apagar nada (Configurações → Verificar banco).

Explica por que enlaces podem não aparecer no mapa: estrutura incompleta após
atualização, eventos sem geometria, corrupção do arquivo ou banco vazio.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

from . import database as db
from . import diagnostics as diag

# Colunas que o mapa exige; sem elas list_map_edges devolve zero enlaces.
REQUIRED_COLUMNS = {
    "topology_events": ("medium", "evidence_level", "source_lat", "source_lon",
                        "target_lat", "target_lon", "raw", "rx_fingerprint"),
    "topology_edges": ("source", "target", "kind", "last_seen", "igate"),
    "stations": ("callsign", "latitude", "longitude", "last_heard"),
    "tracks": ("callsign", "latitude", "longitude", "timestamp"),
}
REQUIRED_TABLES = ("stations", "tracks", "packets", "topology_edges",
                   "topology_events", "rf_coverage_cells")
_STATUS_RANK = {"ok": 0, "info": 0, "warning": 1, "error": 2}


def _item(key: str, label: str, status: str, detail: str) -> dict[str, str]:
    return {"key": key, "label": label, "status": status, "detail": detail}


def _tables(conn) -> set[str]:
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _count(conn, sql: str, args: tuple = ()) -> int:
    return int(conn.execute(sql, args).fetchone()[0] or 0)


def run_check() -> dict[str, Any]:
    started = time.monotonic()
    checks: list[dict[str, str]] = []
    stats: dict[str, Any] = {"path": str(db.DB_PATH)}
    try:
        stats["size_bytes"] = db.DB_PATH.stat().st_size
    except OSError:
        stats["size_bytes"] = 0
    day_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(timespec="seconds")
    with db.connection() as conn:
        rows = [r[0] for r in conn.execute("PRAGMA quick_check(20)").fetchall()]
        if rows == ["ok"]:
            checks.append(_item("integrity", "Integridade do arquivo", "ok", "Nenhuma corrupção encontrada (quick_check)."))
        else:
            checks.append(_item("integrity", "Integridade do arquivo", "error",
                                "SQLite encontrou problemas: " + "; ".join(rows[:5]) +
                                ". Faça backup do arquivo antes de qualquer ação."))

        tables = _tables(conn)
        missing_tables = [t for t in REQUIRED_TABLES if t not in tables]
        missing_cols: list[str] = []
        for table, columns in REQUIRED_COLUMNS.items():
            if table not in tables:
                continue
            present = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            missing_cols += [f"{table}.{c}" for c in columns if c not in present]
        if missing_tables or missing_cols:
            checks.append(_item("schema", "Estrutura (tabelas e colunas)", "error",
                                "Faltando: " + ", ".join(missing_tables + missing_cols) +
                                ". Sem isso o mapa não desenha enlaces. Use “Reparar estrutura”."))
        else:
            checks.append(_item("schema", "Estrutura (tabelas e colunas)", "ok", "Todas as tabelas e colunas do mapa existem."))

        stats["journal_mode"] = str(conn.execute("PRAGMA journal_mode").fetchone()[0])
        page_count = _count(conn, "PRAGMA page_count")
        freelist = _count(conn, "PRAGMA freelist_count")
        stats["free_ratio"] = round(freelist / page_count, 3) if page_count else 0.0

        for table in ("stations", "tracks", "packets", "topology_edges", "topology_events", "rf_coverage_cells"):
            stats[table] = _count(conn, f"SELECT COUNT(*) FROM {table}") if table in tables else None

        if "topology_events" in tables and not missing_cols:
            geo = "source_lat IS NOT NULL AND source_lon IS NOT NULL AND target_lat IS NOT NULL AND target_lon IS NOT NULL"
            total = _count(conn, "SELECT COUNT(*) FROM topology_events WHERE kind IN ('rf','igate')")
            with_geo = _count(conn, f"SELECT COUNT(*) FROM topology_events WHERE kind IN ('rf','igate') AND {geo}")
            recent = _count(conn, f"SELECT COUNT(*) FROM topology_events WHERE kind IN ('rf','igate') AND {geo} AND timestamp>=?", (day_ago,))
            stats.update(link_events=total, link_events_with_position=with_geo, link_events_24h_with_position=recent)
            if total == 0:
                checks.append(_item("link_events", "Eventos de enlace", "info",
                                    "Nenhum evento de enlace registrado ainda; enlaces aparecem após receber pacotes digipeados ou via iGate."))
            elif with_geo == 0:
                checks.append(_item("link_events", "Eventos de enlace", "error",
                                    f"{total} evento(s), nenhum com posição das duas pontas: o mapa não tem o que desenhar. "
                                    "Comum em banco migrado de versão antiga; “Reparar estrutura” refaz o preenchimento."))
            else:
                share = with_geo / total
                checks.append(_item("link_events", "Eventos de enlace", "ok" if share >= 0.3 else "warning",
                                    f"{with_geo} de {total} evento(s) ({share:.0%}) têm posição para o mapa; {recent} nas últimas 24 h. "
                                    "Eventos sem posição (estação que nunca enviou coordenadas) ficam só no histórico."))

        if "topology_edges" in tables and "stations" in tables:
            orphan = _count(conn, """
                SELECT COUNT(*) FROM topology_edges e
                WHERE e.kind='rf' AND NOT EXISTS (
                    SELECT 1 FROM stations s WHERE UPPER(s.callsign)=UPPER(e.source) AND s.latitude IS NOT NULL)""")
            rf_edges = _count(conn, "SELECT COUNT(*) FROM topology_edges WHERE kind='rf'")
            stats.update(rf_edges=rf_edges, rf_edges_source_without_station=orphan)
            if rf_edges:
                checks.append(_item("edges", "Enlaces RF registrados", "ok" if orphan < rf_edges else "warning",
                                    f"{rf_edges} enlace(s) RF; {orphan} com origem sem posição conhecida na tabela de estações."))

        if "packets" in tables:
            last = conn.execute("SELECT MAX(timestamp) FROM packets").fetchone()[0]
            stats["last_packet"] = last or ""
            checks.append(_item("activity", "Último pacote recebido", "ok" if last else "info",
                                str(last) if last else "Nenhum pacote no banco."))

        if stats["free_ratio"] >= 0.25:
            checks.append(_item("free_space", "Espaço livre interno", "info",
                                f"{stats['free_ratio']:.0%} do arquivo está livre após limpezas; não é erro."))

    if not missing_cols and "topology_events" in tables:
        checks.extend(_map_link_checks(stats))

    worst = max((c["status"] for c in checks), key=lambda s: _STATUS_RANK.get(s, 0), default="ok")
    status = {"error": "error", "warning": "warning"}.get(worst, "ok")
    result = {
        "ok": status == "ok",
        "status": status,
        "checks": checks,
        "stats": stats,
        "can_repair": any(c["key"] in {"schema", "link_events"} and c["status"] == "error" for c in checks),
        "elapsed_ms": round((time.monotonic() - started) * 1000.0, 1),
    }
    diag.log_event("db_check", status=status, elapsed_ms=result["elapsed_ms"],
                   **{k: v for k, v in stats.items() if k != "path"})
    return result


def _map_link_checks(stats: dict[str, Any]) -> list[dict[str, str]]:
    """Explica quantos enlaces o mapa recebe e por que alguns ficam ocultos."""
    from . import topology_map  # import tardio: evita ciclo na carga do módulo

    try:
        edges = topology_map.list_map_edges(0)
    except Exception as exc:
        return [_item("map_links", "Enlaces no mapa", "error", f"Falha ao montar os enlaces do mapa: {exc}")]
    by_kind: dict[str, int] = {}
    hidden: dict[str, int] = {"marker": 0, "moved": 0}
    long_inferred = 0
    for edge in edges:
        kind = str(edge.get("kind") or "")
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if edge.get("render_on_overview") is False:
            warning = str(edge.get("endpoint_geometry_warning") or "")
            hidden["marker" if "indisponível" in warning else "moved"] += 1
        elif kind != "igate" and not edge.get("direct_rf_confirmed") and float(edge.get("distance_km") or 0) > 250:
            long_inferred += 1
    fixed = by_kind.get("rf", 0) + by_kind.get("rf_temp", 0)
    shown_fixed = fixed - hidden["marker"] - hidden["moved"] - long_inferred
    stats.update(map_rf_fixed=fixed, map_rf_fixed_visible=shown_fixed, map_rf_mobile=by_kind.get("rf_mobile", 0),
                 map_igate=by_kind.get("igate", 0), map_hidden_marker=hidden["marker"],
                 map_hidden_moved=hidden["moved"], map_hidden_long=long_inferred)
    with db.connection() as conn:
        last_rf = conn.execute(
            "SELECT MAX(timestamp) FROM topology_events WHERE kind='rf' "
            "AND source_lat IS NOT NULL AND target_lat IS NOT NULL").fetchone()[0]
        reference = conn.execute(
            """SELECT source,target,kind,source_lat,source_lon,target_lat,target_lon
               FROM topology_events WHERE kind='rf' ORDER BY timestamp DESC,id DESC LIMIT ?""",
            (topology_map.MAP_EVENT_SCAN_LIMIT,)).fetchall()
        tracks = conn.execute(
            "SELECT callsign,latitude,longitude,speed FROM tracks ORDER BY timestamp DESC,id DESC LIMIT ?",
            (topology_map.MAP_EVENT_SCAN_LIMIT,)).fetchall()
    mobile = sorted(topology_map.moving_rf_repeaters(reference, tracks))
    stats["map_mobile_stations"] = len(mobile)
    stats["last_rf_event_with_position"] = last_rf or ""
    parts = [f"{shown_fixed} de {fixed} enlace(s) RF fixo(s) visíveis",
             f"{by_kind.get('rf_mobile', 0)} RF móvel(is) dentro das últimas horas",
             f"{by_kind.get('igate', 0)} iGate"]
    reasons = []
    if hidden["marker"]:
        reasons.append(f"{hidden['marker']} oculto(s) porque uma das pontas não tem posição gravada no enlace")
    if hidden["moved"]:
        reasons.append(f"{hidden['moved']} oculto(s) porque a estação está hoje a mais de 5 km da posição do enlace")
    if long_inferred:
        reasons.append(f"{long_inferred} oculto(s) por serem inferidos com mais de 250 km")
    if mobile:
        reasons.append(f"{len(mobile)} estação(ões) tratada(s) como móvel(is) — mostram só o último contato por 3 h "
                       "(ex.: " + ", ".join(mobile[:8]) + ")")
    detail = "; ".join(parts) + "." + (" " + "; ".join(reasons) + "." if reasons else "")
    detail += f" Último evento RF com posição: {last_rf or 'nenhum'}."
    status = "ok" if shown_fixed > 0 or fixed == 0 else "warning"
    if fixed == 0 and by_kind.get("rf_mobile", 0) == 0 and last_rf:
        status = "warning"
    return [_item("map_links", "Enlaces no mapa", status, detail)]


def repair() -> dict[str, Any]:
    """Recria tabelas/colunas/índices ausentes e refaz índices. Não apaga dados."""
    from . import spacetime_topology  # import tardio: evita ciclo na carga do módulo
    started = time.monotonic()
    db.init_db()
    with db.connection() as conn:
        # Permite que o preenchimento de geometria rode outra vez neste banco.
        if "schema_migrations_v1419" in _tables(conn):
            conn.execute("DELETE FROM schema_migrations_v1419 WHERE migration_key='v1.14.19-topology-event-spacetime'")
    filled = spacetime_topology._ensure_schema_and_backfill()
    with db.connection() as conn:
        # Só preenche pontas ainda sem posição; repetir não duplica nada.
        conn.execute("DELETE FROM schema_migrations_v1419 WHERE migration_key='v1.14.57-fixed-station-event-geometry'")
        filled += spacetime_topology._backfill_fixed_station_geometry(conn)
        conn.execute("REINDEX")
        conn.execute("ANALYZE")
    diag.log_event("db_repair", backfilled=filled, elapsed_ms=round((time.monotonic() - started) * 1000.0, 1))
    report = run_check()
    report["repaired"] = True
    report["backfilled_events"] = int(filled or 0)
    return report
