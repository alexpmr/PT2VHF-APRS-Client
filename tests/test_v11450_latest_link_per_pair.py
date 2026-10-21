"""v1.14.50: tracker que circula numa cidade não deixa enlaces órfãos."""
from datetime import datetime, timedelta, timezone

from pt2vhf_aprs import topology_map

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
DIGI = (-15.75, -47.88)  # digi fixo na Asa Norte


def ev(minutes_ago, src_pos, source="PT2CAR-9", target="PT2DIG-1"):
    return {
        "timestamp": (NOW - timedelta(minutes=minutes_ago)).isoformat(),
        "source": source, "target": target, "kind": "rf", "medium": "APRS-IS",
        "evidence_level": "inferred",
        "source_lat": src_pos[0], "source_lon": src_pos[1],
        "target_lat": DIGI[0], "target_lon": DIGI[1],
    }


# Trajeto em Ceilândia: pontos a poucos km, sempre ouvidos pelo mesmo digi.
TRIP = [ev(50, (-15.80, -48.11)), ev(30, (-15.83, -48.15)), ev(10, (-15.86, -48.09))]


def test_speed_in_tracklog_marks_local_tracker_as_mobile():
    tracks = [{"callsign": "PT2CAR-9", "latitude": lat, "longitude": lon, "speed": 42.0}
              for lat, lon in ((-15.80, -48.11), (-15.83, -48.15), (-15.86, -48.09))]
    assert "PT2CAR-9" in topology_map.moving_rf_repeaters(TRIP, tracks)
    edges = topology_map._segments_from_events(
        TRIP, now=NOW, mobile_callsigns=topology_map.moving_rf_repeaters(TRIP, tracks))
    assert len(edges) == 1 and edges[0]["kind"] == "rf_mobile"
    assert (edges[0]["source_lat"], edges[0]["source_lon"]) == (-15.86, -48.09)


def test_fixed_station_reporting_zero_speed_is_not_mobile():
    tracks = [{"callsign": "PT2FIX", "latitude": -15.8, "longitude": -47.9, "speed": 0}] * 5
    assert "PT2FIX" not in topology_map.moving_rf_repeaters([], tracks)


def test_without_speed_still_only_latest_line_per_pair():
    # Mesmo sem ser classificado como móvel, sobra uma única linha: a mais recente.
    edges = topology_map._segments_from_events(list(reversed(TRIP)), now=NOW, mobile_callsigns=set())
    assert len(edges) == 1 and edges[0]["kind"] == "rf"
    assert (edges[0]["source_lat"], edges[0]["source_lon"]) == (-15.86, -48.09)
    assert edges[0]["rf_packet_count"] == 3
