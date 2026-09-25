from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html_path = ROOT / "pt2vhf_aprs/templates/index.html"
js_path = ROOT / "pt2vhf_aprs/static/js/app.js"
css_path = ROOT / "pt2vhf_aprs/static/css/app.css"
tests_path = ROOT / "tests/test_core.py"

html = html_path.read_text(encoding="utf-8")
old = """        <div class="traffic-replay-range">
          <label class="field compact">
            <span>De</span>
            <input id="trafficRangeStart" type="datetime-local" step="1">
          </label>
          <label class="field compact">
            <span>Até</span>
            <input id="trafficRangeEnd" type="datetime-local" step="1">
          </label>
          <button id="trafficApplyRangeButton" type="button" class="btn secondary">Aplicar intervalo</button>
          <button id="trafficClearRangeButton" type="button" class="btn secondary">Usar período da Análise</button>
        </div>"""
new = """        <div class="traffic-replay-range traffic-quick-range">
          <label class="field compact">
            <span>Período do replay</span>
            <select id="trafficQuickRange">
              <option value="1">1 h</option>
              <option value="12">12 h</option>
              <option value="24" selected>24 h</option>
              <option value="168">7 dias</option>
              <option value="0">Todo o histórico</option>
            </select>
          </label>
        </div>"""
if old in html:
    html = html.replace(old, new, 1)
html = html.replace(
    '<button id="sendMessageButton" class="btn primary send-btn" title="Enviar mensagem">Enviar</button>',
    '<button id="sendMessageButton" type="button" class="btn primary send-btn" title="Enviar mensagem">Enviar</button>',
)
html_path.write_text(html, encoding="utf-8")

js = js_path.read_text(encoding="utf-8")
js = js.replace(
    "    trafficReplayLayers: new Set(),\n",
    "    trafficReplayLayers: new Set(),\n    replayMobileTracks: new Map(),\n",
    1,
)
js = js.replace(
    "    versionCheckInProgress: false,\n",
    "    versionCheckInProgress: false,\n    messageLoadSeq: 0,\n    messageSending: false,\n",
    1,
)
js = js.replace(
    "    state.trafficReplayLayers.clear();\n    updateMapLegend();",
    "    state.trafficReplayLayers.clear();\n    state.replayMobileTracks.clear();\n    updateMapLegend();",
    1,
)

old = """    const particle = L.circleMarker(from, {
      radius: 6,
      color: '#ffffff',
      weight: 1,
      fillColor: segment.kind === 'igate' ? state.mapConfig.topology_igate_color : '#ffd54a',
      fillOpacity: .95,
      opacity: .95,
      pane: 'markerPane'
    }).addTo(state.map);
    particle.bindPopup(trafficEventDetails(event), { maxWidth: 440 });
    state.trafficReplayLayers.add(particle);
    updateMapLegend();

    const start = performance.now();
    return new Promise(resolve => {
      const tick = now => {
        const t = Math.min(1, (now - start) / Math.max(120, durationMs));
        const eased = t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
        particle.setLatLng([
          from[0] + (to[0] - from[0]) * eased,
          from[1] + (to[1] - from[1]) * eased
        ]);
        if (t < 1) {
          requestAnimationFrame(tick);
        } else {
          setTimeout(() => {
            try { state.map?.removeLayer(particle); } catch (_) {}
            state.trafficReplayLayers.delete(particle);
            updateMapLegend();
          }, 650);
          resolve();
        }
      };
      requestAnimationFrame(tick);
    });"""
new = """    const packetColor = segment.kind === 'igate' ? state.mapConfig.topology_igate_color : '#ffd54a';
    const trail = L.polyline([from, from], {
      color: packetColor,
      weight: Math.max(3, Number(state.mapConfig.topology_width || 2) + 1),
      opacity: .9,
      dashArray: '8 6'
    }).addTo(state.map);
    const particle = L.circleMarker(from, {
      radius: 7,
      color: '#ffffff',
      weight: 2,
      fillColor: packetColor,
      fillOpacity: 1,
      opacity: 1
    }).addTo(state.map);
    particle.bindPopup(trafficEventDetails(event), { maxWidth: 440 });
    state.trafficReplayLayers.add(trail);
    state.trafficReplayLayers.add(particle);
    updateMapLegend();

    const start = performance.now();
    return new Promise(resolve => {
      const tick = now => {
        const t = Math.min(1, (now - start) / Math.max(180, durationMs));
        const eased = t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
        const current = [
          from[0] + (to[0] - from[0]) * eased,
          from[1] + (to[1] - from[1]) * eased
        ];
        particle.setLatLng(current);
        trail.setLatLngs([from, current]);
        if (t < 1) {
          requestAnimationFrame(tick);
        } else {
          setTimeout(() => {
            try { state.map?.removeLayer(particle); } catch (_) {}
            try { state.map?.removeLayer(trail); } catch (_) {}
            state.trafficReplayLayers.delete(particle);
            state.trafficReplayLayers.delete(trail);
            updateMapLegend();
          }, 700);
          resolve();
        }
      };
      requestAnimationFrame(tick);
    });"""
if old not in js:
    raise SystemExit("animateTrafficSegment block not found")
js = js.replace(old, new, 1)

old = """    const startInput = $('#trafficRangeStart');
    const endInput = $('#trafficRangeEnd');
    if (startInput) startInput.value = state.replayWindowStart ? isoToDatetimeLocal(state.replayWindowStart) : '';
    if (endInput) endInput.value = state.replayWindowEnd ? isoToDatetimeLocal(state.replayWindowEnd) : '';"""
new = """    const quickRange = $('#trafficQuickRange');
    if (quickRange && !state.replayWindowStart && !state.replayWindowEnd) {
      const analysisHours = Number(topologyPeriodValue(state.topologyHours) || 0);
      quickRange.value = ['1','12','24','168'].includes(String(analysisHours)) ? String(analysisHours) : '0';
    }"""
if old in js:
    js = js.replace(old, new, 1)

needle = """  async function animateTrafficEvent(event) {
    if (!event) return;
    stationActivity(event.source);"""
replacement = """  function updateReplayMobileStation(event) {
    if (!state.map || !event?.source) return;
    const call = normalizedCall(event.source);
    const sourceSegment = (event.segments || []).find(segment => normalizedCall(segment.source) === call);
    const lat = Number(sourceSegment?.source_lat);
    const lon = Number(sourceSegment?.source_lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
    const marker = state.markers.get(call);
    if (marker) marker.setLatLng([lat, lon]);
    let item = state.replayMobileTracks.get(call);
    if (!item) {
      const line = L.polyline([[lat, lon]], {
        color: state.mapConfig.track_color,
        weight: Math.max(2, Number(state.mapConfig.track_width || 2)),
        opacity: .95
      }).addTo(state.map);
      item = { line, points: [[lat, lon]] };
      state.replayMobileTracks.set(call, item);
      state.trafficReplayLayers.add(line);
      return;
    }
    const previous = item.points[item.points.length - 1];
    if (!previous || previous[0] !== lat || previous[1] !== lon) {
      item.points.push([lat, lon]);
      item.line.setLatLngs(item.points);
    }
  }

  async function animateTrafficEvent(event) {
    if (!event) return;
    updateReplayMobileStation(event);
    stationActivity(event.source);"""
if needle not in js:
    raise SystemExit("animateTrafficEvent hook not found")
js = js.replace(needle, replacement, 1)

start = js.find("  $('#trafficApplyRangeButton')?.addEventListener('click', async () => {")
end = js.find("  $('#trafficMode')?.addEventListener('change', async event => {", start)
if start >= 0 and end > start:
    quick = """  $('#trafficQuickRange')?.addEventListener('change', async event => {
    const hours = Math.max(0, Number(event.target.value || 0));
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.trafficMode = 'history';
    state.timelineReplayActive = false;
    state.replayWindowEnd = null;
    state.replayWindowStart = hours > 0 ? new Date(Date.now() - hours * 3600000).toISOString() : null;
    if ($('#trafficMode')) $('#trafficMode').value = 'history';
    clearTrafficReplayLayers();
    try {
      await loadTrafficHistory(true, state.replayWindowStart || '');
      updateTrafficAnimationUi();
    } catch (err) {
      toast(err.message, 'error');
    }
  });

"""
    js = js[:start] + quick + js[end:]

old = """      const filter = $('#messageFilter').value.trim();
      const mine = state.myMessagesOnly ? '&mine=1' : '';
      state.messages = await api(`/api/messages?from=${encodeURIComponent(filter)}${mine}`);
      renderMessages();
      updateUnread();"""
new = """      const filter = String($('#messageFilter')?.value || '').trim().toUpperCase();
      const mine = state.myMessagesOnly ? '&mine=1' : '';
      const requestSeq = ++state.messageLoadSeq;
      const rows = await api(`/api/messages?from=${encodeURIComponent(filter)}${mine}`);
      if (requestSeq !== state.messageLoadSeq) return;
      state.messages = rows || [];
      renderMessages();
      updateUnread();"""
if old not in js:
    raise SystemExit("message filter block not found")
js = js.replace(old, new, 1)

js = js.replace(
    "  $('#sendMessageButton').addEventListener('click', sendMessage);",
    "  $('#sendMessageButton')?.addEventListener('click', event => { event.preventDefault(); void sendMessage(); });",
    1,
)
js = js.replace("      sendMessage();\n", "      void sendMessage();\n", 1)

js_path.write_text(js, encoding="utf-8")

css = css_path.read_text(encoding="utf-8")
css += """
/* v1.6.4 */
.traffic-replay-range.traffic-quick-range { margin: 0 0 5px; gap: 6px; min-height: 0; }
.traffic-replay-range.traffic-quick-range .field.compact { min-width: 170px; max-width: 220px; gap: 3px; }
.traffic-replay-range.traffic-quick-range select { min-height: 30px; padding-top: 4px; padding-bottom: 4px; }
.map-traffic-panel { padding-top: 7px; padding-bottom: 7px; }
"""
css_path.write_text(css, encoding="utf-8")

tests = tests_path.read_text(encoding="utf-8")
if "test_v164_message_and_replay_regressions" not in tests:
    tests += """

def test_v164_message_and_replay_regressions():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert 'id="sendMessageButton" type="button"' in html
    assert "void sendMessage()" in js
    assert "messageLoadSeq" in js
    assert 'id="trafficQuickRange"' in html
    assert 'id="trafficRangeStart"' not in html
    assert "updateReplayMobileStation(event)" in js
    assert "animateTrafficSegment(segment, event, duration)" in js
    assert "trail.setLatLngs([from, current])" in js
"""
tests_path.write_text(tests, encoding="utf-8")
