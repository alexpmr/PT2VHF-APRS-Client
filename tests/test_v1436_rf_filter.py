"""v1.14.36: RF inferred map semantics and new APRS-IS radius default."""
from datetime import datetime, timezone

from pt2vhf_aprs import database as db, topology_map
from pt2vhf_aprs.aprs_service import expand_filter


def test_default_aprs_is_radius_has_configured_station_as_center():
    assert db.DEFAULT_APRS_FILTER == "r/4000"
    assert db.DEFAULT_CONFIG["aprs_filter"] == "r/4000"
    actual = expand_filter("r/4000", {"latitude": -15.7939, "longitude": -47.8828})
    assert actual == "r/-15.79390/-47.88280/4000"
    assert expand_filter("p/PT/PY", {"latitude": -15.8, "longitude": -47.9}) == "p/PT/PY"


def test_aprs_is_radius_requires_location():
    try:
        expand_filter("r/4000", {"latitude": None, "longitude": None})
    except ValueError as exc:
        assert "latitude e longitude" in str(exc)
    else:
        assert False, "abridged radius must require station coordinates"


def test_inferred_long_rf_hop_is_not_direct_even_with_historical_geometry():
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "LU9DCE", "target": "PU2XTC-4", "kind": "rf",
        "medium": "APRS-IS", "evidence_level": "inferred",
        "source_lat": -34.6, "source_lon": -58.4,
        "target_lat": -22.9, "target_lon": -47.1,
    }
    item = topology_map._segments_from_events([row])[0]
    assert item["distance_km"] > 1000
    assert item["rf_path_count"] == 1
    assert item["rf_direct_count"] == 0
    assert item["direct_rf_confirmed"] is False
    assert item["rf_inferred"] is True


def test_mixed_inferred_then_direct_events_produce_auditable_aggregate():
    ts = datetime.now(timezone.utc).isoformat()
    base = {
        "timestamp": ts, "source": "PY2A-9", "target": "PT2AP-10",
        "kind": "rf", "source_lat": -23.54, "source_lon": -46.62,
        "target_lat": -23.53, "target_lon": -46.61,
    }
    rows = [dict(base, medium="APRS-IS", evidence_level="inferred"),
            dict(base, medium="RF", evidence_level="direct")]
    result = topology_map._segments_from_events(rows)
    # Inferred APRS-IS and direct TNC observations remain distinct records;
    # they must not inflate each other's direct RF evidence.
    by_kind = {edge["kind"]: edge for edge in result}
    assert set(by_kind) == {"rf", "rf_temp"}
    assert by_kind["rf"]["rf_path_count"] == 1
    assert by_kind["rf"]["direct_rf_confirmed"] is False
    assert by_kind["rf_temp"]["rf_transport_count"] == 1
    assert by_kind["rf_temp"]["rf_direct_count"] == 1
    assert by_kind["rf_temp"]["direct_rf_confirmed"] is True


def test_frontend_does_not_display_unverified_long_hops_as_normal_rf():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    js = (root / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "inferredRouteEdge ? '#94a3b8'" not in js
    assert "style.dashArray = '5 7'" not in js
    assert "if (edge.kind !== 'igate' && legacyRouteEdge) style.dashArray" not in js
    assert "state.mapConfig.topology_igate_color : state.mapConfig.topology_rf_color" in js
    assert "temporaryRf ? state.mapConfig.topology_rf_temporary_color" in js
    assert "dashArray: edge.kind === 'igate' ? '7 5' : mobileRf ? '2 5' : null" in js
    assert "topologyEdgeDistanceKm(geometryEdge) > 250" in js
    assert "if (!window.isSecureContext)" in js
