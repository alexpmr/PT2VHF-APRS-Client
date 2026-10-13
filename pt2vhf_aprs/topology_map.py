"""Spatially anchored topology segments for the ordinary APRS map.

The historical RF event belongs where and when the digi/iGate actually
heard/repeated the packet. Never draw an event with the current location of
a mobile callsign from the stations table. This is intentionally separate
from aggregate historical topology and from route/ranking calculations.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
import math

from . import database as db
from . import diagnostics as diag


MAP_EVENT_SCAN_LIMIT = 30000
MAP_SEGMENT_LIMIT = 5000
# ~11 km latitude per geographic bucket; each event keeps its exact coordinates.
# Two encounters by the same mobile in different regions never become one line.
MAP_SPATIAL_BUCKET_DEGREES = 0.10


def _rounded_bin(lat: float, lon: float) -> tuple[int, int]:
    return (math.floor((lat + 90.0) / MAP_SPATIAL_BUCKET_DEGREES),
            math.floor((lon + 180.0) / MAP_SPATIAL_BUCKET_DEGREES))


def _validated_position(lat: Any, lon: Any) -> tuple[float, float] | None:
    if lat is None or lon is None or not db._valid_geo_position(lat, lon):
        return None
    return float(lat), float(lon)


def _segments_from_events(rows: list[Any], max_segments: int = MAP_SEGMENT_LIMIT) -> list[dict[str, Any]]:
    """Group near-coincident event geometries while keeping true GPS snapshots.

    The packet-level source/target positions MUST come from topology_events;
    no join to stations.latest is allowed, including for older/historic rows.
    """
    segments: dict[tuple[Any, ...], dict[str, Any]] = {}
    media_by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)
    for raw in rows:
        row = dict(raw)
        src = str(row.get("source") or "").strip().upper()
        dst = str(row.get("target") or "").strip().upper()
        kind = str(row.get("kind") or "").strip().lower()
        if not src or not dst or src == dst or kind not in {"rf", "igate"}:
            continue
        source_pos = _validated_position(row.get("source_lat"), row.get("source_lon"))
        target_pos = _validated_position(row.get("target_lat"), row.get("target_lon"))
        if source_pos is None or target_pos is None:
            # Do not manufacture a VHF link to the latest GPS of a moving digi.
            continue
        time_text = str(row.get("timestamp") or "")
        src_bin = _rounded_bin(*source_pos)
        dst_bin = _rounded_bin(*target_pos)
        key = (src, dst, kind, *src_bin, *dst_bin)
        medium = str(row.get("medium") or "").upper().strip()
        evidence = str(row.get("evidence_level") or "").lower().strip()
        pair = (src, dst)
        media_by_pair[pair].add(kind)

        segment = segments.get(key)
        if segment is None:
            segment = {
                "source": src, "target": dst, "kind": kind,
                "source_lat": source_pos[0], "source_lon": source_pos[1],
                "target_lat": target_pos[0], "target_lon": target_pos[1],
                "first_seen": time_text, "last_seen": time_text,
                "event_timestamp": time_text,
                "packet_count": 0,
                "rf_transport_count": 0, "rf_path_count": 0,
                "internet_confirmed_count": 0,
                "igate": dst if kind == "igate" else None,
                "evidence_level": evidence if evidence in {"direct", "inferred", "legacy", "internet"} else ("internet" if kind == "igate" else "legacy"),
                "historical_geometry": True,
                "geometry_source": "topology_events",
                "segment_id": (
                    "{}>{}:{}:{}:{}:{}:{}".format(
                        src, dst, kind, src_bin[0], src_bin[1], dst_bin[0], dst_bin[1]
                    )
                ),
            }
            segments[key] = segment
        segment["packet_count"] += 1
        segment["first_seen"] = min(segment["first_seen"], time_text)
        segment["last_seen"] = max(segment["last_seen"], time_text)
        if kind == "rf":
            if medium == "RF" and evidence != "inferred":
                segment["rf_transport_count"] += 1
            else:
                segment["rf_path_count"] += 1
        else:
            segment["internet_confirmed_count"] += 1

    totals: dict[tuple[str, str, str], int] = defaultdict(int)
    for segment in segments.values():
        totals[(segment["source"], segment["target"], segment["kind"])] += segment["packet_count"]
    ordered = sorted(segments.values(), key=lambda item: item["last_seen"], reverse=True)
    if len(ordered) > max_segments:
        diag.log_event("topology_map_segment_limit", total=len(ordered), shown=max_segments)
        ordered = ordered[:max_segments]
    for edge in ordered:
        mixed = len(media_by_pair[(edge["source"], edge["target"])]) > 1
        edge["mixed_evidence"] = mixed
        edge["rf_packet_count"] = totals[(edge["source"], edge["target"], "rf")]
        edge["internet_packet_count"] = totals[(edge["source"], edge["target"], "igate")]
        edge["classification_source"] = (
            "APRS-IS confirmado" if edge["kind"] == "igate" else
            "RF recebido pelo TNC (posição histórica)" if edge["rf_transport_count"] > 0 else
            "RF inferido do path (posição histórica)"
        )
        # APRS path evidence is not proof of a verified direct RF hop.
        edge["direct_rf_confirmed"] = bool(
            edge["kind"] == "rf" and edge["rf_transport_count"] > 0
            and edge["evidence_level"] == "direct"
        )
        edge["rf_inferred"] = edge["kind"] == "rf" and not edge["direct_rf_confirmed"]
        edge["distance_km"] = round(db.haversine_km(
            edge["source_lat"], edge["source_lon"],
            edge["target_lat"], edge["target_lon"],
        ), 3)
    return ordered


def list_map_edges(hours: float = 0) -> list[dict[str, Any]]:
    """Map-only topology: immutable event locations, never latest station GPS.

    A lack of event geometry keeps the historical record in SQLite and JSON
    diagnostics, but suppresses its geographically ungrounded line on the map.
    """
    try:
        period = float(hours or 0)
    except (TypeError, ValueError):
        period = 0
    if not math.isfinite(period):
        period = 0.0
    period = min(max(period, 0.25), 24 * 30) if period > 0 else 0.0
    params: list[Any] = []
    where = """WHERE kind IN ('rf', 'igate')
            AND source_lat IS NOT NULL AND source_lon IS NOT NULL
            AND target_lat IS NOT NULL AND target_lon IS NOT NULL"""
    if period:
        where += " AND timestamp>=?"
        params.append((datetime.now(timezone.utc) - timedelta(hours=period)).isoformat(timespec="seconds"))
    params.append(MAP_EVENT_SCAN_LIMIT)
    with db.connection() as conn:
        try:
            rows = conn.execute(
                f"""SELECT timestamp,source,target,kind,medium,evidence_level,
                           source_lat,source_lon,target_lat,target_lon
                    FROM topology_events {where}
                    ORDER BY timestamp DESC,id DESC LIMIT ?""",
                params,
            ).fetchall()
        except Exception as exc:
            if "no such column" in str(exc).lower() or "no such table" in str(exc).lower():
                diag.log_event("topology_map_event_geometry_unavailable", error=str(exc))
                return []
            raise
    return _segments_from_events(rows)
