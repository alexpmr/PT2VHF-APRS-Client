from pathlib import Path

import pytest

from pt2vhf_aprs.tnc_service import normalize_message_rf_path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v185_rf_path_validation_accepts_standard_paths():
    assert normalize_message_rf_path("") == []
    assert normalize_message_rf_path("wide1-1") == ["WIDE1-1"]
    assert normalize_message_rf_path("WIDE1-1,WIDE2-1") == ["WIDE1-1", "WIDE2-1"]


def test_v185_rf_path_validation_rejects_invalid_or_repeated_markers():
    with pytest.raises(ValueError):
        normalize_message_rf_path("WIDE1-1*")
    with pytest.raises(ValueError):
        normalize_message_rf_path("INVALID-99")
    with pytest.raises(ValueError):
        normalize_message_rf_path(",".join(["WIDE1-1"] * 9))


def test_v185_message_route_controls_and_api_are_wired():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    web = read("pt2vhf_aprs/web.py")
    service = read("pt2vhf_aprs/aprs_service.py")

    for value in ("auto", "aprs_is", "rf_direct", "rf_custom"):
        assert f'value="{value}"' in html
    assert 'id="messagePath"' in html
    assert "updateMessageRouteMode" in js
    assert "route=data.get(\"route\", \"auto\")" in web
    assert "path=data.get(\"path\", \"\")" in web
    assert 'route: str = "auto"' in service
    assert "queue_local_message" in service


def test_v185_message_history_persists_transport_and_path():
    database = read("pt2vhf_aprs/database.py")
    app = read("pt2vhf_aprs/static/js/app.js")
    assert "tx_medium TEXT" in database
    assert "tx_path TEXT" in database
    assert "ALTER TABLE messages ADD COLUMN tx_medium TEXT" in database
    assert "ALTER TABLE messages ADD COLUMN tx_path TEXT" in database
    assert "messageTransportLabel" in app
    assert "message-transport-badge" in app


def test_v185_auto_route_preserves_aprs_is_priority():
    service = read("pt2vhf_aprs/aprs_service.py")
    assert 'selected_route = "aprs_is" if aprs_ready else ("rf_direct" if rf_ready else "auto")' in service
    assert "Mantém o comportamento histórico: APRS-IS é a primeira escolha." in service


def test_v185_low_height_layout_targets_1360x768_class_displays():
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "@media (max-height: 800px) and (min-width: 901px)" in css
    assert "max-height: min(500px, calc(100dvh - 230px));" in css
    assert "position: sticky;" in css
    assert "body.map-context-visible main { height: calc(100vh - 162px); }" in css
    assert ".messages-table-wrap { min-height: 80px; }" in css


def test_v185_version():
    assert read("VERSION").strip() == "1.8.5"
    assert '__version__ = "1.8.5"' in read("pt2vhf_aprs/__init__.py")
