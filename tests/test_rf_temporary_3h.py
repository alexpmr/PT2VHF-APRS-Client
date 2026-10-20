"""Acceptance for expiring 3h RF links with independent style and no mobile regression."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile

import pytest

from pt2vhf_aprs import database as db, topology_map

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)


def ev(before_h, *, source="PT2FIX-1", target="PT2FIX-2", kind="rf",
       medium="RF", evidence="direct"):
    t = (NOW - timedelta(hours=before_h)).isoformat()
    return {
        "timestamp": t, "source": source, "target": target, "kind": kind,
        "medium": medium, "evidence_level": evidence,
        "source_lat": -15.80, "source_lon": -47.90,
        "target_lat": -15.81, "target_lon": -47.91,
    }


def edges(rows, *, now=NOW, mobile=frozenset(), established=None):
    return topology_map._segments_from_events(
        rows, now=now, mobile_callsigns=set(mobile),
        established_rf_pairs=established,
    )


def test_first_direct_rf_contact_is_temporary():
    result = edges([ev(0.25)])
    assert len(result) == 1
    item = result[0]
    assert item["kind"] == "rf_temp"
    assert item["ttl_hours"] == 3
    assert item["direct_rf_confirmed"] is True
    assert item["expires_at"] == (NOW + timedelta(hours=2, minutes=45)).isoformat()


def test_temporary_expires_at_three_hours_not_rounded():
    assert len(edges([ev(2.999)])) == 1
    assert edges([ev(3)]) == []
    assert edges([ev(3.001)]) == []


def test_new_direct_contact_renews_temporary_expiration():
    result = edges([ev(2.8), ev(0.1)])
    assert len(result) == 1
    assert result[0]["packet_count"] == 2
    assert result[0]["expires_at"] == (NOW + timedelta(hours=2, minutes=54)).isoformat()


def test_bursts_of_packets_cannot_promote_to_permanent():
    rows = [ev(2.6), ev(2.4), ev(0.1)]
    assert topology_map._established_rf_pairs(rows) == set()
    assert all(row["kind"] == "rf_temp" for row in edges(rows))


def test_repeated_contacts_three_hours_apart_establish_rf():
    rows = [ev(26), ev(5), ev(0.1)]
    assert topology_map._rf_pair("PT2FIX-1", "PT2FIX-2") in topology_map._established_rf_pairs(rows)
    result = edges(rows)
    assert result and all(row["kind"] == "rf" for row in result)


def test_reverse_direction_is_same_pair_for_recurrence():
    rows = [ev(4), ev(0.1, source="PT2FIX-2", target="PT2FIX-1")]
    assert len(topology_map._established_rf_pairs(rows)) == 1
    assert all(r["kind"] == "rf" for r in edges(rows))


def test_only_real_rf_renews_transient_not_aprs_is():
    rows = [ev(4), ev(0.1, medium="APRS-IS", evidence="inferred")]
    result = edges(rows)
    assert all(x["kind"] != "rf_temp" for x in result)
    assert len([x for x in result if x["kind"] == "rf"]) == 1
    assert not topology_map._established_rf_pairs(rows)


def test_internet_edges_are_not_reclassified_temporary():
    result = edges([ev(0.1, kind="igate", medium="APRS-IS", evidence="internet")])
    assert len(result) == 1 and result[0]["kind"] == "igate"


def test_mobile_trackers_use_mobile_style_not_temporary_rf():
    assert edges([ev(0.1, target="PT2TRACK-9")], mobile={"PT2TRACK-9"})[0]['kind'] == 'rf_mobile'
    # v1.14.49: a tracker as source also keeps its latest link, as rf_mobile.
    assert edges([ev(0.1, source="PT2TRACK-9")], mobile={"PT2TRACK-9"})[0]['kind'] == 'rf_mobile'


def test_missing_historical_geometry_does_not_make_temporary_rf():
    event = ev(0.1)
    event["target_lon"] = None
    assert edges([event]) == []


def test_future_timestamp_far_beyond_clock_skew_rejected():
    assert edges([ev(-1)]) == []


def test_config_schema_defaults_and_validation():
    with tempfile.TemporaryDirectory() as directory:
        old = db.DB_PATH
        try:
            db.DB_PATH = Path(directory) / "config.sqlite3"
            db.init_db()
            cfg = db.get_config()
            assert cfg["topology_rf_temporary_color"] == "#00d9ef"
            assert cfg["topology_rf_temporary_width"] == 3
            updated = db.save_config({
                "topology_rf_temporary_color": "#55aaff",
                "topology_rf_temporary_width": 5,
            })
            assert updated["topology_rf_temporary_color"] == "#55aaff"
            assert updated["topology_rf_temporary_width"] == 5
            with pytest.raises(ValueError):
                db.save_config({"topology_rf_temporary_width": 11})
            with pytest.raises(ValueError):
                db.save_config({"topology_rf_temporary_color": "red"})
        finally:
            db.DB_PATH = old


def test_ui_styles_and_expiration_present():
    root = Path(__file__).resolve().parents[1]
    js = (root / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    html = (root / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    assert 'temporaryRf = edge.kind === \'rf_temp\'' in js
    assert 'edge.expires_at' in js
    assert "state.mapConfig.topology_rf_temporary_color" in js
    assert "state.mapConfig.topology_rf_temporary_width" in js
    assert "}, 30000);" in js
    assert 'name="topology_rf_temporary_color"' in html
    assert 'name="topology_rf_temporary_width"' in html
