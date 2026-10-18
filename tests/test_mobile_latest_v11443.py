"""v1.14.43: mobile RF links retain only the last valid observation (#116)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

import pytest

from pt2vhf_aprs import database as db, topology_map


NOW = datetime(2026, 10, 18, 15, 0, tzinfo=timezone.utc)


def row(age, source, target, from_pos, to_pos, medium="RF", level="direct",
        kind="rf"):
    return {
        "timestamp": (NOW - timedelta(hours=age)).isoformat(),
        "source": source, "target": target, "kind": kind, "medium": medium,
        "evidence_level": level, "source_lat": from_pos[0],
        "source_lon": from_pos[1], "target_lat": to_pos[0],
        "target_lon": to_pos[1],
    }


def mobile(rows, ttl=3):
    return topology_map._segments_from_events(
        rows, now=NOW, mobile_callsigns={"PT2CAR-9"},
        mobile_ttl_hours=ttl,
    )


def test_one_latest_mobile_edge_after_three_displaced_contacts():
    old = row(2.5, "PY5SUL", "PT2CAR-9", (-25.4, -49.2), (-25.39, -49.19))
    middle = row(1.5, "PY4UBA", "PT2CAR-9", (-19.7, -47.9), (-19.71, -47.91))
    newest = row(0.2, "PT2CAR-9", "PT2BSB", (-15.8, -47.9), (-15.79, -47.91))
    edges = mobile([middle, newest, old])
    assert len(edges) == 1
    assert edges[0]["kind"] == "rf_mobile"
    assert edges[0]["source"] == "PT2CAR-9"
    assert edges[0]["target"] == "PT2BSB"
    assert edges[0]["source_lat"] == -15.8
    assert edges[0]["segment_id"] == "mobile:PT2CAR-9"
    assert edges[0]["expires_at"] == (NOW + timedelta(hours=2.8)).isoformat()
    assert edges[0]["packet_count"] == 1


def test_out_of_order_old_packet_and_duplicates_cannot_revive_old_link():
    latest = row(0.1, "PT2CAR-9", "PT2BSB", (-15.8, -47.9), (-15.79, -47.91))
    older = row(0.5, "PY5SUL", "PT2CAR-9", (-25.4, -49.2), (-25.39, -49.19))
    assert mobile([older, older.copy(), latest]) == mobile([latest, older, older.copy()])


def test_mobile_expiration_independent_of_rf_temporary_ttl():
    old = row(4, "PT2CAR-9", "PT2BSB", (-15.8, -47.9), (-15.79, -47.91))
    assert mobile([old]) == []
    assert mobile([old], ttl=6)[0]["ttl_hours"] == 6
    assert mobile([row(0.1, "PT2CAR-9", "PT2BSB", (-15.8, -47.9), (-15.79, -47.91))])[0]["ttl_hours"] == 3


def test_invalid_newest_does_not_create_orphan_or_use_latest_station_gps():
    valid = row(1, "PT2CAR-9", "PT2BSB", (-15.8, -47.9), (-15.79, -47.91))
    invalid = row(0.1, "PT2CAR-9", "PT2OTH", (-15.6, -47.7), (None, None))
    assert mobile([valid, invalid])[0]["target"] == "PT2BSB"
    assert mobile([invalid]) == []


def test_aprs_is_igate_not_mobile_contact_but_path_evidence_is_labeled_inferred():
    old = row(0.5, "PY5SUL", "PT2CAR-9", (-15.8, -47.9), (-15.79, -47.91))
    igate = row(0.1, "PT2CAR-9", "GATE", (-15.8, -47.9), (-15.79, -47.91),
                medium="APRS-IS", level="internet", kind="igate")
    result = mobile([old, igate])
    assert len(result) == 1 and result[0]["kind"] == "rf_mobile"
    inferred = row(0.1, "PY5SUL", "PT2CAR-9", (-15.8, -47.9), (-15.79, -47.91),
                   medium="APRS-IS", level="inferred")
    result = mobile([inferred])
    assert result[0]["rf_inferred"] is True
    assert result[0]["direct_rf_confirmed"] is False
    assert "inferida" in result[0]["classification_source"]


def test_one_link_max_per_mobile_even_with_two_mobiles_in_same_hop():
    x = row(0.1, "PT2CAR-9", "OTHER-MOBILE", (-15.8, -47.9), (-15.79, -47.91))
    y = row(0.2, "FIXED", "OTHER-MOBILE", (-15.77, -47.90), (-15.79, -47.91))
    edges = topology_map._segments_from_events(
        [y, x], now=NOW,
        mobile_callsigns={"PT2CAR-9", "OTHER-MOBILE"})
    assert len(edges) == 1
    assert edges[0]["mobile_callsigns"] == ["OTHER-MOBILE", "PT2CAR-9"]


def test_sparse_trip_with_three_separated_events_is_mobile_but_one_outlier_is_not():
    rows = [
        row(2, "STATION-A", "PT2CAR-9", (-25.4, -49.2), (-25.39, -49.19)),
        row(1, "STATION-B", "PT2CAR-9", (-19.8, -47.9), (-19.79, -47.89)),
        row(0.1, "STATION-C", "PT2CAR-9", (-15.8, -47.9), (-15.79, -47.91)),
    ]
    assert "PT2CAR-9" in topology_map.moving_rf_repeaters(rows)
    assert len(topology_map._segments_from_events(rows, now=NOW)) == 1
    assert "PT2CAR-9" not in topology_map.moving_rf_repeaters(rows[:2])



def test_config_mobile_ttl_and_style_persist_with_validation():
    with tempfile.TemporaryDirectory() as d:
        previous = db.DB_PATH
        try:
            db.DB_PATH = Path(d) / "mobile.sqlite3"
            db.init_db()
            assert db.get_config()["topology_rf_mobile_ttl_hours"] == 3
            result = db.save_config({
                "topology_rf_mobile_ttl_hours": 5.5,
                "topology_rf_mobile_color": "#ddaa33",
                "topology_rf_mobile_width": 4,
            })
            assert result["topology_rf_mobile_ttl_hours"] == 5.5
            assert result["topology_rf_mobile_color"] == "#ddaa33"
            assert result["topology_rf_mobile_width"] == 4
            for invalid in (0, 0.1, 169, float("inf"), float("nan")):
                with pytest.raises(ValueError):
                    db.save_config({"topology_rf_mobile_ttl_hours": invalid})
            with pytest.raises(ValueError):
                db.save_config({"topology_rf_mobile_color": "orange"})
            with pytest.raises(ValueError):
                db.save_config({"topology_rf_mobile_width": 11})
        finally:
            db.DB_PATH = previous


def test_ver_ui_and_map_settings_are_independent():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    html = (root / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    assert "mobileLinksEnabled: 'pt2vhf_map_item_mobile_rf'" in js
    assert "edge.kind === 'rf_mobile' && !state.mobileLinksEnabled" in js
    assert 'data-legend="rf-mobile"' in js
    assert "topology_rf_mobile_ttl_hours" in html
    assert "topologyRfMobileWidth" in html
