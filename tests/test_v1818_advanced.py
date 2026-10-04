from __future__ import annotations

import tempfile
from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs.advanced_features import _period_comparison, _quality
from pt2vhf_aprs.agwpe_transport import AGWPEStreamDecoder, enable_raw_command, raw_tx_frame


def test_agwpe_header_roundtrip_raw_frame():
    raw = bytes(range(32))
    decoder = AGWPEStreamDecoder()
    frames = decoder.feed(raw_tx_frame(raw, port=2))
    assert len(frames) == 1
    assert frames[0].kind == "K"
    assert frames[0].port == 2
    assert frames[0].data == raw
    assert len(enable_raw_command()) == 36


def test_advanced_quality_and_comparison_on_empty_db():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "v1818.db"
            db.init_db()
            quality = _quality(24)
            comparison = _period_comparison(24)
            assert quality["packets"] == 0
            assert quality["stations"] == 0
            assert comparison["hours"] == 24
            assert "changes" in comparison
    finally:
        db.DB_PATH = original
        db.invalidate_map_data_cache(drop_payload=True)
