from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v141_only_iss_is_default_when_selection_key_is_missing():
    js = read("pt2vhf_aprs/static/js/v112.js")
    assert "if(raw===null)return new Set([25544])" in js
    assert "Array.isArray(a)?a:[]" in js
    assert "a.length?a:[25544]" not in js
    assert "satelliteResetDefaults" in js
    assert "state.selected.add(25544)" in js


def test_v141_selected_satellite_renders_without_waiting_for_status_poll():
    js = read("pt2vhf_aprs/static/js/v112.js")
    assert "function showSatelliteImmediately" in js
    assert "enqueueTrack(id,center)" in js
    assert "trackActive<4" in js
    assert "trackPromises.has(id)" in js
    assert "if(!state.status.length)return" not in js
    assert "hasPosition(pos)" in js
    assert "TLE indisponível" in js
    assert "Carregando posição" in js
    assert "removeSatelliteLayers(id)" in js


def test_v141_satellite_menu_is_sat_but_internal_title_is_full():
    html = read("pt2vhf_aprs/templates/index.html")
    assert '<button class="tab satellite-tab-button" data-tab="satellites">SAT</button>' in html
    assert '<h2>Satélites / ISS</h2>' in html


def test_v141_satellite_operational_layout_keeps_primary_content_visible():
    html = read("pt2vhf_aprs/templates/index.html")
    css = read("pt2vhf_aprs/static/css/v141.css")
    assert 'id="satelliteMap"' in html
    assert 'class="satellite-card satellite-stations-card"' in html
    assert 'class="satellite-card satellite-message-card"' in html
    for key in ("detail", "alerts", "tle", "station-filters", "beacon", "agenda"):
        assert f'data-sat-collapsible="{key}"' in html
    assert "grid-template-columns:minmax(0," in css
    assert "minmax(340px,.85fr)" in css
    assert ".satellite-secondary-panel>summary" in css


def test_v141_collapsed_panels_persist_without_affecting_services():
    js = read("pt2vhf_aprs/static/js/v141.js")
    assert "pt2vhf_v141_sat_panel_" in js
    assert "panel.open=saved==='1'" in js
    assert "localStorage.setItem(key(id),panel.open?'1':'0')" in js


def test_v141_countdown_is_left_aligned_and_identifies_satellite():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/v113.js")
    css = read("pt2vhf_aprs/static/css/v141.css")
    assert 'class="satellite-operation-bar"' in html
    assert 'id="satelliteTabNextName"' in html
    assert "satName+' / '+callsign" in js
    assert "EM PASSAGEM" in js
    assert "LOS em" in js
    assert "justify-content:flex-start" in css


def test_v141_top_notification_bell_removed_but_center_remains_available():
    js = read("pt2vhf_aprs/static/js/v111.js")
    assert "v111Bell" not in js
    assert "🔔" not in js
    assert "v111NotifyOpen" in js
    assert "Centro de notificações" in js
    assert "/api/v111/notifications" in js


def test_v141_new_station_alert_uses_persisted_setting_as_source_of_truth():
    js = read("pt2vhf_aprs/static/js/v190.js")
    assert "window.__pt2vhfV190AlertSettingsDirty" in js
    assert "const settings=window.__pt2vhfV190AlertSettingsDirty" in js
    assert ": {...serverSettings};" in js
    assert "if(settings.station_appeared)" in js
    assert "void saveAlertSettings(false)" in js
