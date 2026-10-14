"""Explorador de caminhos RF hipotéticos, separado da topologia comprovada.

Somente relações RF já registradas entram na busca. Resultados hipotéticos NUNCA
são inseridos no SQLite nem promovidos a enlaces desenháveis no mapa.
"""
from __future__ import annotations

import heapq
from typing import Any

from . import database as db
from . import spacetime_topology as st


def _event_distance(edge: dict[str, Any]) -> float:
    values = [
        float(event.get("distance_km") or 0.0)
        for event in edge.get("events") or []
        if float(event.get("distance_km") or 0.0) > 0.0
    ]
    return min(values) if values else float(edge.get("distance_km") or 0.0)


def _path_evidence(nodes: tuple[str, ...], graph: dict) -> dict[str, Any]:
    """Descreve obstáculos verificáveis sem deduzir uma rota física dos nós."""
    blockers: list[dict[str, Any]] = []
    hops: list[dict[str, Any]] = []
    total_km = 0.0
    for a, b in zip(nodes, nodes[1:]):
        edge = graph[a][b]
        level, _ = db._rf_route_evidence(edge)
        distance = _event_distance(edge)
        total_km += distance
        hops.append({
            "source": a,
            "target": b,
            "evidence_level": level,
            "distance_km": round(distance, 2),
            "last_seen": str(edge.get("last_seen") or ""),
        })
        if level == "inferred" and distance >= st.INFERRED_LONG_HOP_KM:
            blockers.append({
                "code": "long_inferred_hop",
                "node": a + " → " + b,
                "distance_km": round(distance, 1),
            })
        if not edge.get("events"):
            blockers.append({"code": "missing_event_geometry", "node": a + " → " + b})

    # É importante comparar as posições HISTÓRICAS do nó compartilhado.
    # O GPS atual de uma estação móvel jamais pode servir de ponte.
    for i, shared in enumerate(nodes[1:-1], start=1):
        left = graph[nodes[i - 1]][shared]
        right = graph[shared][nodes[i + 1]]
        left_events = st._sample_route_events(list(left.get("events") or []))
        right_events = st._sample_route_events(list(right.get("events") or []))
        matches: list[tuple[float, float]] = []
        for before in left_events:
            p1 = st._event_position(shared, left, before)
            t1 = st._event_epoch(before)
            if p1 is None or t1 is None:
                continue
            for after in right_events:
                p2 = st._event_position(shared, right, after)
                t2 = st._event_epoch(after)
                if p2 is None or t2 is None:
                    continue
                delta_km = db.haversine_km(*p1, *p2)
                delta_minutes = abs(t1 - t2) / 60.0
                matches.append((delta_km, delta_minutes))
        if not matches:
            blockers.append({"code": "missing_shared_node_position", "node": shared})
            continue
        closest_km, closest_time = min(matches, key=lambda x: (x[0], x[1]))
        if closest_km > st.SHARED_NODE_COMPATIBILITY_KM:
            blockers.append({
                "code": "mobile_spatial_bridge",
                "node": shared,
                "position_gap_km": round(closest_km, 1),
            })
        else:
            closest_in_time = min(
                (minutes for km, minutes in matches
                 if km <= st.SHARED_NODE_COMPATIBILITY_KM),
                default=float("inf"),
            )
            if closest_in_time > st.ROUTE_TEMPORAL_WINDOW_MINUTES:
                blockers.append({
                    "code": "different_observation_times",
                    "node": shared,
                    "time_gap_minutes": round(closest_in_time, 1),
                })

    return {
        "edges": hops,
        "sum_hops_km": round(total_km, 2),
        "blockers": blockers,
    }


def explore_possible_routes(
    source: str,
    target: str,
    *,
    hours: float = 0.0,
    max_hops: int = 12,
    limit: int = 12,
) -> dict[str, Any]:
    """Consulta por origem/destino independentemente dos top-N de recordes.

    Três classes: mesmo pacote, alcançabilidade histórica validada e hipótese
    topológica bloqueada/não comprovada. Mesmo pacote não implica RF direto em
    cada salto; o nível de evidência de cada enlace é mantido.
    """
    origin = db._rf_route_callsign(source)
    destination = db._rf_route_callsign(target)
    response: dict[str, Any] = {
        "source": origin, "target": destination, "possible_routes": [],
        "searched_without_ranking_limit": True, "search_truncated": False,
        "semantics": "rf_topological_hypothesis_not_a_packet_traceroute",
        "draw_hypotheses_on_map": False,
    }
    if not origin or not destination or origin == destination:
        return response

    graph, positions = st._route_graph(hours)
    if origin not in graph or destination not in graph:
        return response
    hop_limit = max(1, min(int(max_hops or 12), 12))
    route_limit = max(1, min(int(limit or 12), 20))
    # Guardião contra explosão combinatória em malhas RF grandes.
    max_expansions = 30000
    expanded = 0
    queue: list[tuple[float, int, tuple[str, ...]]] = [(0.0, 0, (origin,))]
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    while queue and len(found) < route_limit:
        cost, count, path = heapq.heappop(queue)
        if path[-1] == destination:
            if path in seen:
                continue
            seen.add(path)
            evidence = _path_evidence(path, graph)
            validated = st._route_payload(
                list(path), graph, positions, refine_inferred=True
            )
            if validated and validated.get("spatiotemporal_validated"):
                cls = str(validated.get("reachability_class") or "historical")
                status = (
                    "same_packet" if cls == "same_packet"
                    else "contemporary" if cls == "contemporary"
                    else "historical_compatible"
                )
                # A análise certificada escolhe eventos coerentes para TODOS
                # os hops; as verificações independentes são apenas alertas.
                blockers = []
            else:
                status = "hypothesis_only"
                blockers = evidence["blockers"] or [
                    {"code": "no_joint_event_proof", "node": ""}
                ]
            found.append({
                "nodes": list(path),
                "hops": len(path) - 1,
                "status": status,
                "draw_as_rf": False,
                "direct_rf_confirmed": False,
                "sum_hops_km": evidence["sum_hops_km"],
                "observed_edges": evidence["edges"],
                "blockers": blockers,
                "time_span_minutes": (
                    validated.get("temporal_span_minutes") if validated else None
                ),
                "route_cost": round(cost, 3),
            })
            continue
        if count >= hop_limit:
            continue
        expanded += 1
        if expanded > max_expansions:
            response["search_truncated"] = True
            break
        for nxt, edge in sorted(graph.get(path[-1], {}).items()):
            if nxt in path:
                continue
            next_cost = cost + db._rf_route_edge_cost(edge)
            heapq.heappush(queue, (next_cost, count + 1, path + (nxt,)))

    priority = {"same_packet": 0, "contemporary": 1,
                "historical_compatible": 2, "hypothesis_only": 3}
    found.sort(key=lambda row: (
        priority.get(row["status"], 4),
        len(row["blockers"]), row["hops"], row["route_cost"]
    ))
    response["possible_routes"] = found
    response["search_expansions"] = expanded
    response["search_truncated"] = bool(response["search_truncated"] or queue)
    return response
