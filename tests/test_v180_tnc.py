from __future__ import annotations

from pathlib import Path

import pytest

from pt2vhf_aprs import database as db
from pt2vhf_aprs.tnc_service import (
    FEND,
    FESC,
    KissStreamDecoder,
    add_igate_q_construct,
    decode_ax25,
    digipeat_frame,
    direct_heard_recent,
    encode_ax25,
    get_tnc_config,
    kiss_encode,
    normalize_tnc_config,
    save_tnc_config,
    strip_internet_path,
    tnc2_to_ax25,
    update_heard,
)


def test_kiss_escape_roundtrip():
    payload = bytes([0x00, FEND, 0x45, FESC, 0x7F])
    encoded = kiss_encode(payload)
    decoder = KissStreamDecoder()
    frames = []
    for chunk in (encoded[:2], encoded[2:5], encoded[5:]):
        frames.extend(decoder.feed(chunk))
    assert frames == [(0, payload)]


def test_ax25_tnc2_roundtrip_and_path_flags():
    frame = encode_ax25(
        "PT2ABC-9",
        "APRS",
        "!1545.00S/04748.00W-Teste",
        ["WIDE1-1", "PT2DGI-1*"],
    )
    decoded = decode_ax25(frame)
    assert decoded["source"] == "PT2ABC-9"
    assert decoded["destination"] == "APRS"
    assert decoded["path_text"] == ["WIDE1-1", "PT2DGI-1*"]
    assert decoded["tnc2"].startswith("PT2ABC-9>APRS,WIDE1-1,PT2DGI-1*:")
    rebuilt = decode_ax25(tnc2_to_ax25(decoded["tnc2"]))
    assert rebuilt["source"] == decoded["source"]
    assert rebuilt["destination"] == decoded["destination"]
    assert rebuilt["path_text"] == decoded["path_text"]
    assert rebuilt["info"] == decoded["info"]


def test_fill_in_digi_consumes_wide1_1():
    frame = encode_ax25("PT2ABC-9", "APRS", ">status", ["WIDE1-1", "WIDE2-1"])
    cfg = normalize_tnc_config({"digi_profile": "fill"}, strict=False)
    repeated, reason = digipeat_frame(frame, "PT2VHF-3", cfg)
    assert repeated is not None
    decoded = decode_ax25(repeated)
    assert decoded["path_text"] == ["PT2VHF-3*", "WIDE2-1"]
    assert "WIDE1-1" in reason


def test_wide_digi_decrements_remaining_hops():
    frame = encode_ax25("PT2ABC", "APRS", ">status", ["WIDE2-2"])
    cfg = normalize_tnc_config({"digi_profile": "wide"}, strict=False)
    repeated, _ = digipeat_frame(frame, "PT2VHF-3", cfg)
    assert repeated is not None
    decoded = decode_ax25(repeated)
    assert decoded["path_text"] == ["PT2VHF-3*", "WIDE2-1"]


def test_digi_blocks_loop_when_own_call_already_in_path():
    frame = encode_ax25("PT2ABC", "APRS", ">status", ["PT2VHF-3*", "WIDE2-1"])
    cfg = normalize_tnc_config({"digi_profile": "wide"}, strict=False)
    repeated, reason = digipeat_frame(frame, "PT2VHF-3", cfg)
    assert repeated is None
    assert "Loop" in reason


def test_igate_q_construct_and_internet_path_cleanup():
    raw = "PT2ABC>APRS,WIDE1-1*:>teste"
    gated = add_igate_q_construct(raw, "PT2VHF-15")
    assert gated == "PT2ABC>APRS,WIDE1-1*,qAR,PT2VHF-15:>teste"

    internet = "PT2ABC>APRS,WIDE1-1*,qAR,PT2IGATE:>teste"
    assert strip_internet_path(internet) == "PT2ABC>APRS,WIDE1-1*:>teste"


def test_automatic_rf_tx_requires_explicit_confirmation():
    with pytest.raises(ValueError, match="Confirme explicitamente"):
        normalize_tnc_config({"auto_tx_enabled": True}, strict=True)
    cfg = normalize_tnc_config(
        {"auto_tx_enabled": True, "tx_confirmed": True, "digi_enabled": True},
        strict=True,
    )
    assert cfg["auto_tx_enabled"] == 1
    assert cfg["tx_confirmed"] == 1
    assert cfg["digi_enabled"] == 1


def test_recent_direct_hearing_has_own_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "tnc-test.db")
    cfg = get_tnc_config()
    assert cfg["auto_tx_enabled"] == 0
    assert cfg["igate_tx_enabled"] == 0
    save_tnc_config(cfg)

    direct_packet = {
        "source": "PT2ABC",
        "path": [{"value": "WIDE1-1", "repeated": False}],
        "info_text": ">direct",
    }
    update_heard(direct_packet, "PT2ABC>APRS,WIDE1-1:>direct")
    assert direct_heard_recent("PT2ABC", 30)

    via_digi_packet = {
        "source": "PT2ABC",
        "path": [{"value": "PT2DGI", "repeated": True}],
        "info_text": ">via digi",
    }
    update_heard(via_digi_packet, "PT2ABC>APRS,PT2DGI*:>via digi")
    # A última recepção pode ter vindo via digi, mas a audição direta recente não é perdida.
    assert direct_heard_recent("PT2ABC", 30)


def test_v180_tnc_interface_and_api_are_present():
    root = Path(__file__).resolve().parents[1]
    html = (root / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs/static/js/tnc.js").read_text(encoding="utf-8")
    web = (root / "pt2vhf_aprs/web.py").read_text(encoding="utf-8")
    service = (root / "pt2vhf_aprs/tnc_service.py").read_text(encoding="utf-8")

    assert 'data-tab="tnc"' in html
    assert 'id="tncTransport"' in html
    assert 'id="tncEmergencyStop"' in html
    assert 'id="tncOptimizerMode"' in html
    assert "Quem fala com quem" in html
    assert "/api/tnc/connect" in web
    assert "/api/tnc/optimizer" in web
    assert "KissStreamDecoder" in service
    assert "digipeat_frame" in service
    assert "direct_heard_recent" in service
    assert "optimizer_report" in service
    assert "/api/tnc/tx/stop" in js


def test_rf_to_is_policy_blocks_nogate_rfonly_and_internet_markers(monkeypatch, tmp_path):
    from pt2vhf_aprs import tnc_service as mod

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "tnc-gate.db")
    cfg = normalize_tnc_config({"igate_rx_enabled": True}, strict=False)
    svc = mod.TNCService()

    decisions = []
    monkeypatch.setattr(mod, "record_decision", lambda *args, **kwargs: decisions.append((args, kwargs)))

    for marker in ("NOGATE", "RFONLY", "TCPIP", "qAR"):
        packet = {
            "source": "PT2ABC",
            "destination": "APRS",
            "path_text": [marker],
            "tnc2": f"PT2ABC>APRS,{marker}:>teste",
        }
        svc._handle_rf_to_is(packet, cfg)

    assert len(decisions) == 4
    assert all(item[0][0] == "igate_rf_is" for item in decisions)
    assert all(item[0][1] == "blocked" for item in decisions)


def test_v180_no_rf_auto_tx_defaults():
    cfg = normalize_tnc_config({}, strict=False)
    assert cfg["auto_tx_enabled"] == 0
    assert cfg["digi_enabled"] == 0
    assert cfg["igate_tx_enabled"] == 0
    assert cfg["optimizer_mode"] == "observe"
