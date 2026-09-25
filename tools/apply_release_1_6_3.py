from pathlib import Path

root = Path(__file__).resolve().parents[1]
html_path = root / "pt2vhf_aprs/templates/index.html"
js_path = root / "pt2vhf_aprs/static/js/app.js"
css_path = root / "pt2vhf_aprs/static/css/app.css"

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
if old not in html:
    raise SystemExit("Bloco antigo do intervalo de replay não encontrado")
html = html.replace(old, new, 1)
html_path.write_text(html, encoding="utf-8")

js = js_path.read_text(encoding="utf-8")
old_overview = """    const startInput = $('#trafficRangeStart');
    const endInput = $('#trafficRangeEnd');
    if (startInput) startInput.value = state.replayWindowStart ? isoToDatetimeLocal(state.replayWindowStart) : '';
    if (endInput) endInput.value = state.replayWindowEnd ? isoToDatetimeLocal(state.replayWindowEnd) : '';"""
if old_overview not in js:
    raise SystemExit("Sincronizacao antiga dos campos De/Ate nao encontrada")
js = js.replace(old_overview, """    const quickRange = $('#trafficQuickRange');
    if (quickRange && !state.replayWindowStart && !state.replayWindowEnd) {
      const analysisHours = Number(topologyPeriodValue(state.topologyHours) || 0);
      quickRange.value = ['1','12','24','168'].includes(String(analysisHours)) ? String(analysisHours) : '0';
    }""", 1)

needle = """  async function animateTrafficEvent(event) {
    if (!event) return;
    stationActivity(event.source);"""
replacement = """  function updateReplayMobileStation(event) {
    if (!state.map || !event?.source) return;
    const call = normalizedCall(event.source);
    const segments = event.segments || [];
    const sourceSegment = segments.find(segment => normalizedCall(segment.source) === call) || segments[0];
    if (!sourceSegment) return;
    const lat = Number(sourceSegment.source_lat);
    const lon = Number(sourceSegment.source_lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;

    const marker = state.markers.get(call);
    if (marker) marker.setLatLng([lat, lon]);

    if (!state.replayMobileTracks) state.replayMobileTracks = new Map();
    let entry = state.replayMobileTracks.get(call);
    if (!entry) {
      const line = L.polyline([[lat, lon]], {
        color: state.mapConfig.track_color,
        weight: state.mapConfig.track_width,
        opacity: .9
      }).addTo(state.map);
      entry = { line, points: [[lat, lon]] };
      state.replayMobileTracks.set(call, entry);
      state.trafficReplayLayers.add(line);
    } else {
      const previous = entry.points[entry.points.length - 1];
      if (!previous || previous[0] !== lat || previous[1] !== lon) {
        entry.points.push([lat, lon]);
        entry.line.setLatLngs(entry.points);
      }
      entry.line.setStyle({
        color: state.mapConfig.track_color,
        weight: state.mapConfig.track_width,
        opacity: .9
      });
    }
  }

  async function animateTrafficEvent(event) {
    if (!event) return;
    stationActivity(event.source);
    updateReplayMobileStation(event);"""
if needle not in js:
    raise SystemExit("Ponto de injecao da animacao nao encontrado")
js = js.replace(needle, replacement, 1)

clear_old = """    state.trafficReplayLayers.clear();
    updateMapLegend();"""
clear_new = """    state.trafficReplayLayers.clear();
    if (state.replayMobileTracks) state.replayMobileTracks.clear();
    updateMapLegend();"""
if clear_old not in js:
    raise SystemExit("Limpeza do replay nao encontrada")
js = js.replace(clear_old, clear_new, 1)

inject = """
  $('#trafficQuickRange')?.addEventListener('change', async event => {
    const hours = Number(event.target.value || 0);
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.timelineReplayActive = false;
    clearTrafficReplayLayers();
    state.replayWindowEnd = null;
    state.replayWindowStart = hours > 0
      ? new Date(Date.now() - hours * 3600000).toISOString()
      : null;
    try {
      await loadTrafficOverview();
      await loadTrafficHistory(true);
      updateTrafficAnimationUi();
    } catch (err) {
      toast(err.message, 'error');
    }
  });

"""
idx = js.rfind("})();")
if idx < 0:
    raise SystemExit("Fechamento do app.js nao encontrado")
js = js[:idx] + inject + js[idx:]
js_path.write_text(js, encoding="utf-8")

css = css_path.read_text(encoding="utf-8")
css += """
/* v1.6.3 - seletor compacto do periodo de replay */
.traffic-replay-range.traffic-quick-range {
  margin: 0 0 5px;
  gap: 6px;
  min-height: 0;
}
.traffic-replay-range.traffic-quick-range .field.compact {
  min-width: 170px;
  max-width: 220px;
  gap: 3px;
}
.traffic-replay-range.traffic-quick-range select {
  min-height: 30px;
  padding-top: 4px;
  padding-bottom: 4px;
}
.map-traffic-panel {
  padding-top: 7px;
  padding-bottom: 7px;
}
"""
css_path.write_text(css, encoding="utf-8")
