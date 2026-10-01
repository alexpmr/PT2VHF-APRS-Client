from __future__ import annotations

from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs import local_server


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v182_dynamic_port_falls_forward_without_probe_race():
    calls = []

    class FakeServer:
        def run(self):
            return None
        def close(self):
            return None

    def factory(app, host, port, threads):
        calls.append((host, port, threads))
        if port in {8080, 8081}:
            raise OSError("address already in use")
        return "fake", FakeServer()

    handle = local_server.allocate_local_server(
        object(),
        host="127.0.0.1",
        start_port=8080,
        attempts=5,
        server_factory=factory,
    )
    assert handle.port == 8082
    assert handle.url == "http://127.0.0.1:8082"
    assert handle.fallback_count == 2
    assert [item[1] for item in calls] == [8080, 8081, 8082]


def test_v182_dynamic_port_respects_configured_start(monkeypatch):
    monkeypatch.setenv("PT2VHF_PORT", "8095")
    assert local_server.configured_start_port() == 8095


def test_v182_ais_object_classification_is_conservative():
    ais = db.aprs_object_map_metadata(
        "AIS-257123456",
        "MMSI: 257123456 vessel position",
        "/",
        "s",
        "object",
    )
    assert ais["map_family_key"] == "ais"
    assert ais["map_family_label"] == "AIS"

    sonde = db.aprs_object_map_metadata(
        "RS41-TEST",
        "radiosonde 403 MHz",
        "/",
        "O",
        "object",
    )
    assert sonde["map_family_key"] in {"rdzsonde", "balloon"}

    generic_boat = db.aprs_object_map_metadata(
        "BOAT-01",
        "marina local",
        "/",
        "s",
        "object",
    )
    assert generic_boat["map_family_key"] != "ais"


def test_v182_map_ver_defaults_all_enabled_and_persist_user_choices():
    js = read("pt2vhf_aprs/static/js/app.js")

    for key in (
        "pt2vhf_map_item_stations",
        "pt2vhf_map_item_digis",
        "pt2vhf_map_item_igates",
        "pt2vhf_map_item_objects",
        "pt2vhf_map_item_tracklogs",
        "pt2vhf_map_item_rf",
        "pt2vhf_map_item_igate",
        "pt2vhf_map_item_packets",
    ):
        assert f"localStorage.getItem('{key}') !== '0'" in js

    assert "state.mapViewFilters[String(key || '')] !== false" in js
    assert "localStorage.setItem(MAP_VIEW_STATE_STORAGE[key], state[key] ? '1' : '0')" in js
    assert "localStorage.setItem('pt2vhf_map_view_filters_v2'" in js


def test_v182_settings_large_flag_removed_but_quick_language_flags_remain():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")

    assert 'id="languageFlag"' not in html
    assert "function syncLanguageFlag()" not in js
    assert 'id="languageQuickCurrentFlag"' in html
    assert 'class="language-quick-img"' in html
    assert 'id="appLanguage"' in html


def test_v182_local_interface_is_exposed_and_displayed():
    web = read("pt2vhf_aprs/web.py")
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")

    assert "local_server_runtime_info()" in web
    assert 'id="localInterfaceStatus"' in html
    assert "s.local_interface || {}" in js
    assert "Interface local" in js


def test_v182_desktop_launchers_use_reserved_dynamic_server():
    for rel in ("windows_app.py", "linux_app.py", "macos_app.py"):
        text = read(rel)
        assert "start_local_server(" in text
        assert "configured_start_port()" in text
        assert "runtime_file_for(db.DB_PATH.parent)" in text
        assert "serve(app, host=HOST, port=PORT" not in text


def test_v182_version():
    assert read("VERSION").strip() == "1.8.2"
