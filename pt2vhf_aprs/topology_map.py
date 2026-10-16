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


RF_TEMPORARY_TTL = timedelta(hours=3)
# Two RF contacts at least three hours apart establish recurring (ordinary) RF.
# Transient contacts do not become permanent merely because time passed.
RF_ESTABLISHED_MIN_SPAN = timedelta(hours=3)


def _event_time(raw: Any) -> datetime | None:
    try:
        value = datetime.fromisoformat(str(raw or "").replace("Z", "+00:00"))
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def _rf_pair(source: Any, target: Any) -> tuple[str, str]:
    return tuple(sorted((str(source or "").strip().upper(), str(target or "").strip().upper())))


def _established_rf_pairs(rows: list[Any]) -> set[tuple[str, str]]:
    """Repeated *directly received* RF contacts separated in time are established.

    Packet duplicates/bursts cannot establish a persistent RF link.
    Inferred APRS-IS paths cannot renew or establish it.
    """
    bounds: dict[tuple[str, str], tuple[datetime, datetime]] = {}
    for raw in rows:
        row = dict(raw)
        if (str(row.get("kind") or "").lower() != "rf"
                or str(row.get("medium") or "").upper() != "RF"
                or str(row.get("evidence_level") or "").lower() != "direct"):
            continue
        if (_validated_position(row.get("source_lat"), row.get("source_lon")) is None
                or _validated_position(row.get("target_lat"), row.get("target_lon")) is None):
            continue
        when = _event_time(row.get("timestamp"))
        pair = _rf_pair(row.get("source"), row.get("target"))
        if when is None or not all(pair) or pair[0] == pair[1]:
            continue
        lo, hi = bounds.get(pair, (when, when))
        bounds[pair] = min(lo, when), max(hi, when)
    return {pair for pair, (lo, hi) in bounds.items() if hi - lo >= RF_ESTABLISHED_MIN_SPAN}


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


def moving_rf_repeaters(rows: list[Any], tracks: list[Any] = ()) -> set[str]:
    """Find repeaters or stations with corroborated displaced RF/GPS positions.

    Process RF source AND target snapshots as well as independent tracklogs.
    A single spurious faraway coordinate is insufficient evidence of movement.
    Call+SSID identity is preserved; time-filtered map rows may be supplied
    alongside longer retained history/tracklog evidence.
    """
    positions: dict[str, dict[tuple[int, int], list[float]]] = defaultdict(dict)

    def observe(callsign: Any, lat: Any, lon: Any) -> None:
        call = str(callsign or "").strip().upper()
        pos = _validated_position(lat, lon)
        if not call or pos is None:
            return
        bucket = (math.floor(pos[0] / 0.05), math.floor(pos[1] / 0.05))
        entry = positions[call].setdefault(bucket, [pos[0], pos[1], 0])
        entry[2] += 1

    for raw in rows:
        row = dict(raw)
        if str(row.get("kind") or "").lower() != "rf":
            continue
        observe(row.get("source"), row.get("source_lat"), row.get("source_lon"))
        observe(row.get("target"), row.get("target_lat"), row.get("target_lon"))

    for raw in tracks:
        row = dict(raw)
        observe(row.get("callsign"), row.get("latitude"), row.get("longitude"))

    moving = set()
    for call, bins in positions.items():
        established = [item for item in bins.values() if item[2] >= 2]
        if any(db.haversine_km(a[0], a[1], b[0], b[1]) >= 25.0
               for i, a in enumerate(established) for b in established[i + 1:]):
            moving.add(call)
    return moving



def _segments_from_events(rows: list[Any], max_segments: int = MAP_SEGMENT_LIMIT, *,
                          mobile_callsigns: set[str] | None = None,
                          established_rf_pairs: set[tuple[str, str]] | None = None,
                          now: datetime | None = None) -> list[dict[str, Any]]:
    """Group near-coincident event geometries while keeping true GPS snapshots.

    The packet-level source/target positions MUST come from topology_events;
    no join to stations.latest is allowed, including for older/historic rows.
    """
    segments: dict[tuple[Any, ...], dict[str, Any]] = {}
    media_by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)
    mobile_repeaters = mobile_callsigns if mobile_callsigns is not None else moving_rf_repeaters(rows)
    established = established_rf_pairs if established_rf_pairs is not None else _established_rf_pairs(rows)
    instant = now or datetime.now(timezone.utc)
    for raw in rows:
        row = dict(raw)
        src = str(row.get("source") or "").strip().upper()
        dst = str(row.get("target") or "").strip().upper()
        kind = str(row.get("kind") or "").strip().lower()
        if not src or not dst or src == dst or kind not in {"rf", "igate"}:
            continue
        # Preserve real RF events for history/coverage, but never draw
        # spider lines for a repeater observed in multiple distinct regions.
        if src in mobile_repeaters or dst in mobile_repeaters:
            continue
        source_pos = _validated_position(row.get("source_lat"), row.get("source_lon"))
        target_pos = _validated_position(row.get("target_lat"), row.get("target_lon"))
        if source_pos is None or target_pos is None:
            # Do not manufacture a VHF link to the latest GPS of a moving digi.
            continue
        time_text = str(row.get("timestamp") or "")
        medium = str(row.get("medium") or "").upper().strip()
        evidence = str(row.get("evidence_level") or "").lower().strip()
        # Only TNC-confirmed, geographically sound RF contacts qualify for
        # temporary display; APRS-IS-only reports cannot reset its 3h TTL.
        temporary = kind == "rf" and medium == "RF" and evidence == "direct" and _rf_pair(src, dst) not in established
        if temporary:
            observed = _event_time(row.get("timestamp"))
            if observed is None or observed > instant + timedelta(minutes=5) or observed + RF_TEMPORARY_TTL <= instant:
                continue
            kind = "rf_temp"
        src_bin = _rounded_bin(*source_pos)
        dst_bin = _rounded_bin(*target_pos)
        key = (src, dst, kind, *src_bin, *dst_bin)
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
                "rf_direct_count": 0,
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
        if kind in {"rf", "rf_temp"}:
            if medium == "RF" and evidence != "inferred":
                segment["rf_transport_count"] += 1
                if evidence == "direct":
                    segment["rf_direct_count"] += 1
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
            "RF temporário (válido por 3h após último contato)" if edge["kind"] == "rf_temp" else
            "RF recebido pelo TNC (posição histórica)" if edge["rf_transport_count"] > 0 else
            "RF inferido do path (posição histórica)"
        )
        # APRS path evidence is not proof of a verified direct RF hop.
        edge["direct_rf_confirmed"] = bool(
            edge["kind"] in {"rf", "rf_temp"} and edge["rf_direct_count"] > 0
        )
        edge["rf_inferred"] = edge["kind"] in {"rf", "rf_temp"} and not edge["direct_rf_confirmed"]
        if edge["kind"] == "rf_temp":
            expiry = _event_time(edge["last_seen"])
            edge["expires_at"] = (expiry + RF_TEMPORARY_TTL).isoformat() if expiry else None
            edge["ttl_hours"] = 3
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
        # Fixed/mobile classification is global to retained history, not
        # bounded by the currently selected map period.
        if period:
            reference = conn.execute(
                """SELECT source,target,kind,source_lat,source_lon,
                          target_lat,target_lon FROM topology_events
                   WHERE kind='rf' ORDER BY timestamp DESC,id DESC LIMIT ?""",
                (MAP_EVENT_SCAN_LIMIT,),
            ).fetchall()
        else:
            reference = rows
        tracks = conn.execute(
            """SELECT callsign,latitude,longitude FROM tracks
               ORDER BY timestamp DESC,id DESC LIMIT ?""",
            (MAP_EVENT_SCAN_LIMIT,),
        ).fetchall()
        mobile = moving_rf_repeaters(reference, tracks)
        established = _established_rf_pairs(reference)
        if mobile:
            diag.log_event("topology_map_mobile_status",
                           mobile_count=len(mobile), period_hours=period)
    return _segments_from_events(rows, mobile_callsigns=mobile, established_rf_pairs=established)


def list_mobile_rf_coverage(hours: float = 0, limit: int = 1200) -> list[dict[str, Any]]:
    """Observed RF repeater activity locations, not predicted continuous coverage.

    Return spatial cells as points; do not interpolate the unmeasured areas.
    APRS-IS-only events ('igate' kind) never become RF coverage evidence.
    """
    try:
        period = float(hours or 0)
    except (TypeError, ValueError):
        period = 0.0
    period = min(max(period, 0.25), 720.0) if math.isfinite(period) and period > 0 else 0.0
    where = "WHERE kind='rf' AND target_lat IS NOT NULL AND target_lon IS NOT NULL"
    params: list[Any] = []
    if period:
        where += " AND timestamp>=?"
        params.append((datetime.now(timezone.utc) - timedelta(hours=period)).isoformat(timespec="seconds"))
    params.append(MAP_EVENT_SCAN_LIMIT)
    with db.connection() as conn:
        rows = [dict(row) for row in conn.execute(
            f"""SELECT timestamp,source,target,kind,medium,evidence_level,
                       source_lat,source_lon,target_lat,target_lon
                  FROM topology_events {where}
                 ORDER BY timestamp DESC,id DESC LIMIT ?""", params
        ).fetchall()]
        # For a short visible period, detect mobility across the retained
        # history too, not only from the currently filtered local snapshots.
        if period:
            reference = [dict(row) for row in conn.execute(
                """SELECT source,target,kind,medium,evidence_level,
                          source_lat,source_lon,target_lat,target_lon
                   FROM topology_events WHERE kind='rf'
                   ORDER BY timestamp DESC,id DESC LIMIT ?""",
                (MAP_EVENT_SCAN_LIMIT,)
            ).fetchall()]
        else:
            reference = rows
    with db.connection() as conn:
        tracks = conn.execute(
            """SELECT callsign,latitude,longitude FROM tracks
               ORDER BY timestamp DESC,id DESC LIMIT ?""",
            (MAP_EVENT_SCAN_LIMIT,),
        ).fetchall()
    mobile = moving_rf_repeaters(reference, tracks)
    cells: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    for row in rows:
        direct = str(row.get("medium") or "").upper() == "RF" and str(row.get("evidence_level") or "").lower() != "inferred"
        evidence = "direct" if direct else "inferred"
        # Both endpoints may be the moving participant. Distinguish the
        # transmitter's observed position from the mobile digi's own activity.
        for role, field in (("source", "source"), ("target", "target")):
            call = str(row.get(field) or "").strip().upper()
            if call not in mobile:
                continue
            pos = _validated_position(row.get(field + "_lat"), row.get(field + "_lon"))
            if pos is None:
                continue
            a, b = int(math.floor(pos[0] / 0.02)), int(math.floor(pos[1] / 0.02))
            key = (call, role, a, b, evidence)
            item = cells.get(key)
            if item is None:
                item = {"callsign": call, "latitude": pos[0], "longitude": pos[1],
                        "role": role, "count": 0,
                        "first_seen": row.get("timestamp"),
                        "last_seen": row.get("timestamp"), "evidence": evidence,
                        "label": "RF observado" if direct else "RF inferido pelo path"}
                cells[key] = item
            item["count"] += 1
            timestamp = str(row.get("timestamp") or "")
            item["first_seen"] = min(str(item["first_seen"] or timestamp), timestamp)
            item["last_seen"] = max(str(item["last_seen"] or timestamp), timestamp)
    return sorted(cells.values(), key=lambda x: (x["last_seen"], x["count"]), reverse=True)[:max(1, min(int(limit), 3000))]
