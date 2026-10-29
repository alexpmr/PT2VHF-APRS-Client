// Planejamento no mapa: análise de cobertura, enlace entre 2 pontos e melhor ponto para instalar estação/digi.
// Portado do PT2VHF Mesh Analyzer (v0.6.41/v0.6.42) e adaptado ao APRS (145,570 MHz, FM 1200 bps).
(() => {
'use strict';

const $ = (s, r = document) => r.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const lang = () => String(document.documentElement.lang || localStorage.getItem('pt2vhf_language') || 'pt-BR').toLowerCase();
const tr = (pt, en, es) => {
  const l = lang();
  const locale = l.startsWith('de') ? 'de-DE' : l.startsWith('it') ? 'it-IT' : l.startsWith('ja') ? 'ja-JP'
    : l.startsWith('pl') ? 'pl-PL' : l.startsWith('nl') ? 'nl-NL' : l.startsWith('zh') ? 'zh-CN' : '';
  const extended = locale ? window.PT2VHF_I18N?.[locale]?.[pt] : '';
  if (extended) return extended;
  return l.startsWith('pt') ? pt : l.startsWith('es') ? (es || en) : en;
};
const VERDICT_COLOR = {viable: '#2fbf71', marginal: '#f3b33d', unviable: '#e5484d'};
const VERDICT_LABEL = () => ({viable: tr('Viável', 'Viable', 'Viable'), marginal: tr('Marginal', 'Marginal', 'Marginal'),
  unviable: tr('Inviável', 'Not viable', 'Inviable')});
const fmtNum = (v, u = '', d = 1) => v === null || v === undefined ? '—'
  : Number(v).toLocaleString(lang().startsWith('pt') ? 'pt-BR' : undefined, {maximumFractionDigits: d}) + u;
const fmtKm = m => fmtNum(m / 1000, ' km', 2);
const fmtCoord = (lat, lon) => Number(lat).toFixed(6) + ', ' + Number(lon).toFixed(6);

let tool = null, layer = null, defaults = null, stations = [], runSeq = 0, runTimer = null;

async function api(path, body) {
  const opts = body === undefined ? {cache: 'no-store'}
    : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)};
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) throw new Error(data.error || res.statusText);
  return data;
}
function notify(text, bad = false) {
  let box = $('#planningToast');
  if (!box) { box = document.createElement('div'); box.id = 'planningToast'; document.body.appendChild(box); }
  box.textContent = text; box.className = bad ? 'bad' : ''; box.hidden = false;
  clearTimeout(notify.timer); notify.timer = setTimeout(() => { box.hidden = true; }, 5000);
}
function mapRef() { return window.pt2vhfMainMap || window.map || null; }
function parseCoord(text) {
  const m = String(text || '').trim().match(/^(-?\d+(?:[.,]\d+)?)\s*[,;\s]\s*(-?\d+(?:[.,]\d+)?)$/);
  if (!m) return null;
  const lat = Number(m[1].replace(',', '.')), lon = Number(m[2].replace(',', '.'));
  return Math.abs(lat) <= 90 && Math.abs(lon) <= 180 ? [lat, lon] : null;
}
async function loadDefaults() {
  try { defaults = await api('/api/planning/defaults'); }
  catch (e) { defaults = {freq_mhz: 145.57, tx_power_w: 25, sensitivity_dbm: -113, own: null, saved: []}; }
  try {
    const list = await api('/api/stations');
    stations = (Array.isArray(list) ? list : list.stations || [])
      .filter(s => s && s.latitude != null && s.longitude != null && !(Math.abs(s.latitude) < .01 && Math.abs(s.longitude) < .01))
      .slice(0, 3000);
  } catch (e) { stations = []; }
  let dl = $('#planningStations');
  if (!dl) { dl = document.createElement('datalist'); dl.id = 'planningStations'; document.body.appendChild(dl); }
  dl.innerHTML = stations.map(s => '<option value="' + esc(String(s.callsign).toUpperCase()) + '">').join('');
}
function stationPos(call) {
  const c = String(call || '').toUpperCase().trim();
  if (!c) return null;
  if (defaults?.own && defaults.own.callsign && defaults.own.callsign === c) return [defaults.own.lat, defaults.own.lon];
  const s = stations.find(x => String(x.callsign).toUpperCase() === c);
  return s ? [Number(s.latitude), Number(s.longitude)] : null;
}
function icon(label, cls) {
  return L.divIcon({className: 'planning-icon ' + cls, html: '<span>' + esc(label) + '</span>', iconSize: [26, 26], iconAnchor: [13, 13]});
}
function closeTool() {
  const map = mapRef();
  if (!tool) return;
  if (map) {
    map.off('click', onMapClick); map.off('mousemove', onMapMove); map.off('dblclick', onMapDblClick);
    map.doubleClickZoom.enable(); map.getContainer().classList.remove('planning-active');
  }
  layer?.clearLayers(); $('#coverageLegend')?.remove(); tool = null; clearTimeout(runTimer);
  $('#planningPanel').hidden = true; $('#planningBody').innerHTML = '';
}
function startTool(kind, extra = {}) {
  const map = mapRef();
  if (!map || !window.L) { notify(tr('Mapa indisponível.', 'Map unavailable.', 'Mapa no disponible.'), true); return false; }
  closeTool(); showMap(); toggleToolsMenu(false);
  $('#mapItemsMenu')?.classList.add('hidden'); $('#mapItemsButton')?.setAttribute('aria-expanded', 'false');
  layer = layer || L.layerGroup().addTo(map);
  if (!map.hasLayer(layer)) layer.addTo(map);
  tool = {kind, ...extra};
  map.on('click', onMapClick); map.on('mousemove', onMapMove); map.on('dblclick', onMapDblClick);
  map.getContainer().classList.add('planning-active');
  $('#planningPanel').hidden = false;
  $('#planningTitle').textContent = kind === 'link' ? tr('Análise de enlace', 'Link analysis', 'Análisis de enlace')
    : kind === 'coverage' ? tr('Análise de cobertura', 'Coverage analysis', 'Análisis de cobertura')
    : tr('Melhor ponto para instalar estação', 'Best spot to install a station', 'Mejor punto para instalar una estación');
  return true;
}
function onMapClick(e) {
  if (!tool) return;
  const p = [e.latlng.lat, e.latlng.lng];
  if (tool.kind === 'link') { if (!tool.a) setEnd('a', p); else if (!tool.b) setEnd('b', p); }
  else if (tool.kind === 'coverage') { if (tool.pickTx || !tool.tx) setCoverageTx(p, null); }
  else surveyClick(p);
}
function onMapMove(e) {
  if (tool?.kind !== 'survey' || tool.closed || !tool.vertices.length || tool.pickRef) return;
  const last = tool.vertices.at(-1);
  if (!tool.guide) tool.guide = L.polyline([last, last], {color: '#f3cf48', weight: 2, dashArray: '4 6', interactive: false}).addTo(layer);
  tool.guide.setLatLngs([last, [e.latlng.lat, e.latlng.lng]]);
}
function onMapDblClick(e) {
  if (tool?.kind !== 'survey' || tool.closed) return;
  L.DomEvent.stop(e);
  const map = mapRef(), v = tool.vertices;
  while (v.length > 1 && map.latLngToContainerPoint(v.at(-1)).distanceTo(map.latLngToContainerPoint(v.at(-2))) < 6) v.pop();
  finishPolygon();
}
async function savePdf(body, filename, button) {
  if (button) button.disabled = true;
  try {
    notify(tr('Gerando PDF…', 'Generating PDF…', 'Generando PDF…'));
    const res = await fetch('/api/planning/pdf', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    if (!res.ok) { let msg = 'HTTP ' + res.status; try { msg = (await res.json()).error || msg; } catch (e) {} throw new Error(msg); }
    const blob = await res.blob();
    const nativeSave = window.pywebview?.api?.save_binary_file;
    if (nativeSave) {
      const b64 = await new Promise((ok, bad) => { const r = new FileReader(); r.onerror = bad; r.onload = () => ok(String(r.result).split(',')[1]); r.readAsDataURL(blob); });
      const result = await nativeSave(filename, b64);
      if (result?.saved) notify(tr('PDF salvo: ', 'PDF saved: ', 'PDF guardado: ') + result.path);
      else if (!result?.cancelled) throw new Error(result?.error || 'PDF');
      return;
    }
    const url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
    notify(tr('Download do PDF solicitado.', 'PDF download requested.', 'Descarga del PDF solicitada.'));
  } catch (e) { notify('PDF: ' + e.message, true); }
  finally { if (button) button.disabled = false; }
}
async function saveText(filename, text) {
  const nativeSave = window.pywebview?.api?.save_text_file;
  if (nativeSave) {
    const r = await nativeSave(filename, text);
    if (r?.saved) notify(tr('Arquivo salvo: ', 'File saved: ', 'Archivo guardado: ') + r.path);
    else if (!r?.cancelled) notify(r?.error || 'CSV', true);
    return;
  }
  const url = URL.createObjectURL(new Blob([text], {type: 'text/csv;charset=utf-8'})), a = document.createElement('a');
  a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 5000);
}
function copyText(text) {
  (navigator.clipboard?.writeText(text) || Promise.reject()).then(() => notify(tr('Copiado: ', 'Copied: ', 'Copiado: ') + text)).catch(() => notify(text));
}
function profileSvg(t, {width = 440, height = 210} = {}) {
  const P = t.profile, maxD = t.distance_m || 1;
  const hi = Math.max(...P.map(p => Math.max(p.terrain_m, p.los_m + p.fresnel_m))), lo = Math.min(...P.map(p => Math.min(p.ground_m, p.los_m - p.fresnel_m)));
  const pad = (hi - lo) * .08 || 10, top = hi + pad, bot = lo - pad, L0 = 46, B0 = height - 22;
  const X = d => L0 + d / maxD * (width - L0 - 8), Y = v => B0 - (v - bot) / ((top - bot) || 1) * (B0 - 8);
  const pts = f => P.map(p => X(p.distance_m).toFixed(1) + ',' + Y(f(p)).toFixed(1)).join(' ');
  let grid = '';
  for (let i = 0; i < 5; i++) { const v = bot + (top - bot) * i / 4; grid += '<line x1="' + L0 + '" x2="' + (width - 8) + '" y1="' + Y(v).toFixed(1) + '" y2="' + Y(v).toFixed(1) + '" stroke="#8aa0ad33"/><text x="' + (L0 - 4) + '" y="' + (Y(v) + 3).toFixed(1) + '" text-anchor="end" font-size="10" fill="#8aa0ad">' + Math.round(v) + ' m</text>'; }
  for (let i = 0; i <= 5; i++) { const d = maxD * i / 5; grid += '<text x="' + X(d).toFixed(1) + '" y="' + (height - 6) + '" text-anchor="middle" font-size="10" fill="#8aa0ad">' + (d / 1000).toFixed(1) + ' km</text>'; }
  const ground = 'M' + X(0) + ',' + B0 + ' ' + P.map(p => 'L' + X(p.distance_m).toFixed(1) + ',' + Y(p.terrain_m).toFixed(1)).join(' ') + ' L' + X(maxD) + ',' + B0 + ' Z';
  const w = t.worst, wp = w && w.ratio < 0.6 ? P.reduce((a, p) => Math.abs(p.distance_m - w.distance_m) < Math.abs(a.distance_m - w.distance_m) ? p : a, P[0]) : null;
  return '<svg class="planning-profile" viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-label="' + esc(tr('Perfil de altimetria entre A e B', 'Elevation profile between A and B', 'Perfil de altimetría entre A y B')) + '">' + grid +
    '<path d="' + ground + '" fill="#8d6a43" opacity=".9"/>' +
    '<polyline points="' + pts(p => p.los_m + p.fresnel_m) + '" fill="none" stroke="#4fc3f7" stroke-dasharray="5 4"/>' +
    '<polyline points="' + pts(p => p.los_m - p.fresnel_m) + '" fill="none" stroke="#4fc3f7" stroke-dasharray="5 4"/>' +
    '<polyline points="' + pts(p => p.los_m - p.fresnel_m * .6) + '" fill="none" stroke="#f3cf48" stroke-dasharray="2 4"/>' +
    '<line x1="' + X(0) + '" y1="' + Y(P[0].los_m).toFixed(1) + '" x2="' + X(maxD) + '" y2="' + Y(P.at(-1).los_m).toFixed(1) + '" stroke="#51d887" stroke-width="2"/>' +
    '<line x1="' + X(0) + '" y1="' + Y(P[0].los_m).toFixed(1) + '" x2="' + X(0) + '" y2="' + Y(P[0].ground_m).toFixed(1) + '" stroke="#e9eef2" stroke-width="2"/>' +
    '<line x1="' + X(maxD) + '" y1="' + Y(P.at(-1).los_m).toFixed(1) + '" x2="' + X(maxD) + '" y2="' + Y(P.at(-1).ground_m).toFixed(1) + '" stroke="#e9eef2" stroke-width="2"/>' +
    '<text x="' + (X(0) + 4) + '" y="' + (Y(P[0].los_m) - 5).toFixed(1) + '" font-size="12" font-weight="700" fill="#e9eef2">A</text>' +
    '<text x="' + (X(maxD) - 12) + '" y="' + (Y(P.at(-1).los_m) - 5).toFixed(1) + '" font-size="12" font-weight="700" fill="#e9eef2">B</text>' +
    (wp ? '<circle cx="' + X(wp.distance_m).toFixed(1) + '" cy="' + Y(wp.terrain_m).toFixed(1) + '" r="5" fill="#e5484d" stroke="#fff"></circle>' : '') + '</svg>';
}
const badge = t => '<span class="planning-badge" style="background:' + VERDICT_COLOR[t.verdict] + '">' + esc(VERDICT_LABEL()[t.verdict]) + '</span>';
function observedHtml(o) {
  if (!o) return '';
  const seen = x => x ? fmtNum(x.packets, ' ' + tr('pacotes', 'packets', 'paquetes'), 0) : tr('nunca', 'never', 'nunca');
  return '<p><b>' + esc(tr('Já observado por RF', 'Already observed over RF', 'Ya observado por RF')) + ':</b> ' +
    esc(o.b) + ' ' + esc(tr('ouviu', 'heard', 'escuchó')) + ' ' + esc(o.a) + ': ' + esc(seen(o.b_heard_a)) + ' · ' +
    esc(o.a) + ' ' + esc(tr('ouviu', 'heard', 'escuchó')) + ' ' + esc(o.b) + ': ' + esc(seen(o.a_heard_b)) + '</p>';
}
function resultHtml(t) {
  const b = t.budget, s = t.suggestion, h = v => v === null || v === undefined ? tr('acima de 300 m', 'above 300 m', 'más de 300 m') : fmtNum(v, ' m');
  return '<p class="planning-verdict">' + badge(t) + ' ' + esc(t.reason) + '</p><p>' + esc(t.obstruction) + '</p>' + profileSvg(t) +
    '<p class="planning-small">' + esc(tr('Terreno com curvatura da Terra (k = 4/3) · verde: linha de visada · azul: 1ª zona de Fresnel · amarelo: 60% da zona · vermelho: pior obstrução.',
      'Terrain with Earth curvature (k = 4/3) · green: line of sight · blue: 1st Fresnel zone · yellow: 60% of the zone · red: worst obstruction.',
      'Terreno con curvatura terrestre (k = 4/3) · verde: línea de vista · azul: 1.ª zona de Fresnel · amarillo: 60% de la zona · rojo: peor obstrucción.')) + '</p>' +
    '<table class="planning-table"><tbody>' +
    '<tr><th>' + esc(tr('Distância', 'Distance', 'Distancia')) + '</th><td>' + fmtKm(t.distance_m) + '</td><th>' + esc(tr('Azimute A→B / B→A', 'Azimuth A→B / B→A', 'Azimut A→B / B→A')) + '</th><td>' + fmtNum(t.azimuth_ab, '°') + ' / ' + fmtNum(t.azimuth_ba, '°') + '</td></tr>' +
    '<tr><th>' + esc(tr('Terreno em A', 'Ground at A', 'Terreno en A')) + '</th><td>' + fmtNum(t.a.ground_m, ' m', 0) + '</td><th>' + esc(tr('Terreno em B', 'Ground at B', 'Terreno en B')) + '</th><td>' + fmtNum(t.b.ground_m, ' m', 0) + '</td></tr>' +
    '<tr><th>' + esc(tr('Espaço livre', 'Free space', 'Espacio libre')) + '</th><td>' + fmtNum(b.fspl_db, ' dB') + '</td><th>' + esc(tr('Obstrução (difração)', 'Obstruction (diffraction)', 'Obstrucción (difracción)')) + '</th><td>' + fmtNum(b.diffraction_db, ' dB') + '</td></tr>' +
    '<tr><th>' + esc(tr('Sinal estimado', 'Estimated signal', 'Señal estimada')) + '</th><td>' + fmtNum(b.rx_dbm, ' dBm') + ' · ' + fmtNum(b.rx_uv, ' µV', 2) + ' · ' + esc(b.s_meter) + '</td><th>' + esc(tr('Margem', 'Margin', 'Margen')) + '</th><td><b>' + fmtNum(b.margin_db, ' dB') + '</b></td></tr>' +
    (t.worst ? '<tr><th>' + esc(tr('Pior ponto', 'Worst point', 'Peor punto')) + '</th><td>' + fmtKm(t.worst.distance_m) + ' ' + esc(tr('de A', 'from A', 'de A')) + '</td><th>' + esc(tr('Fresnel livre', 'Fresnel clear', 'Fresnel libre')) + '</th><td>' + (t.worst.ratio < 0 ? '0% (' + esc(tr('sem visada', 'no line of sight', 'sin línea de vista')) + ')' : Math.round(t.worst.ratio * 100) + '%') + '</td></tr>' : '') +
    '</tbody></table>' +
    (s ? '<p><b>' + esc(tr('Para liberar 60% da zona de Fresnel:', 'To clear 60% of the Fresnel zone:', 'Para liberar el 60% de la zona de Fresnel:')) + '</b> A ' + h(s.height_a_m) + ' · B ' + h(s.height_b_m) + ' · ' + esc(tr('as duas', 'both', 'ambas')) + ' ' + h(s.height_both_m) + '</p>' : '') +
    observedHtml(t.observed) + '<p class="planning-small">' + esc(t.notes) + '</p>';
}
// --- enlace entre 2 pontos ------------------------------------------------------
const LINK_FIELDS = () => [
  ['height_a', tr('Antena A acima do solo (m)', 'Antenna A above ground (m)', 'Antena A sobre el suelo (m)'), 0, 300, .5],
  ['height_b', tr('Antena B acima do solo (m)', 'Antenna B above ground (m)', 'Antena B sobre el suelo (m)'), 0, 300, .5],
  ['freq_mhz', tr('Frequência (MHz)', 'Frequency (MHz)', 'Frecuencia (MHz)'), 28, 1300, .001],
  ['tx_power_w', tr('Potência TX (W)', 'TX power (W)', 'Potencia TX (W)'), .1, 1500, .1],
  ['gain_a_dbi', tr('Ganho antena A (dBi)', 'Antenna A gain (dBi)', 'Ganancia antena A (dBi)'), -10, 30, .5],
  ['gain_b_dbi', tr('Ganho antena B (dBi)', 'Antenna B gain (dBi)', 'Ganancia antena B (dBi)'), -10, 30, .5],
  ['cable_a_db', tr('Perda de cabo A (dB)', 'Cable loss A (dB)', 'Pérdida de cable A (dB)'), 0, 30, .1],
  ['cable_b_db', tr('Perda de cabo B (dB)', 'Cable loss B (dB)', 'Pérdida de cable B (dB)'), 0, 30, .1],
  ['sensitivity_dbm', tr('Sensibilidade p/ decodificar (dBm)', 'Sensitivity to decode (dBm)', 'Sensibilidad para decodificar (dBm)'), -140, -80, 1]];
async function openLink(opts = {}) {
  await loadDefaults();
  if (!startTool('link', {a: null, b: null, stationA: null, stationB: null, result: null, markers: {}, line: null, worst: null, fromCoverage: opts.fromCoverage || null,
    params: {height_a: 10, height_b: 10, freq_mhz: defaults.freq_mhz, tx_power_w: defaults.tx_power_w, gain_a_dbi: 3, gain_b_dbi: 3,
      cable_a_db: 1, cable_b_db: 1, sensitivity_dbm: defaults.sensitivity_dbm, ...(opts.params || {})}})) return;
  renderLink();
  if (opts.a) setEnd('a', opts.a, opts.stationA || null, false);
  if (opts.b) setEnd('b', opts.b, opts.stationB || null, false);
  if (opts.a && opts.b) { mapRef().fitBounds(L.latLngBounds([opts.a, opts.b]).pad(.25)); schedule(runLink, 0); }
}
function renderLink() {
  const t = tool;
  const end = (k, label) => '<div class="planning-field"><label for="planCoord' + k + '">' + esc(tr('Ponto', 'Point', 'Punto')) + ' ' + label + '</label><div class="planning-row">' +
    '<input id="planCoord' + k + '" placeholder="lat, lon" value="' + (t[k] ? fmtCoord(...t[k]) : '') + '">' +
    '<input id="planStation' + k + '" list="planningStations" placeholder="' + esc(tr('ou indicativo', 'or callsign', 'o indicativo')) + '" value="' + esc(t['station' + label] || '') + '" autocomplete="off"></div></div>';
  $('#planningBody').innerHTML = (t.fromCoverage ? '<div class="planning-actions"><button type="button" class="btn secondary" id="planBackCoverage">← ' + esc(tr('Voltar à cobertura', 'Back to coverage', 'Volver a la cobertura')) + '</button></div>' : '') +
    '<p id="planHint" class="planning-hint"></p>' + end('a', 'A') + end('b', 'B') +
    (defaults.own ? '<div class="planning-actions"><button type="button" class="btn secondary" data-own="a">' + esc(tr('A = minha estação', 'A = my station', 'A = mi estación')) + '</button><button type="button" class="btn secondary" data-own="b">' + esc(tr('B = minha estação', 'B = my station', 'B = mi estación')) + '</button></div>' : '') +
    '<details class="planning-params"' + (t.result ? '' : ' open') + '><summary>' + esc(tr('Antenas e rádio', 'Antennas and radio', 'Antenas y radio')) + '</summary><div class="planning-grid">' +
    LINK_FIELDS().map(([k, label, min, max, step]) => '<label>' + esc(label) + '<input type="number" data-param="' + k + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + t.params[k] + '"></label>').join('') +
    '</div><p class="planning-small">' + esc(tr('APRS no Brasil: 145,570 MHz, FM 1200 bps. −113 dBm ≈ 0,5 µV, nível típico para decodificar pacotes.',
      'APRS in Brazil: 145.570 MHz, FM 1200 bps. −113 dBm ≈ 0.5 µV, a typical level to decode packets.',
      'APRS en Brasil: 145,570 MHz, FM 1200 bps. −113 dBm ≈ 0,5 µV, nivel típico para decodificar paquetes.')) + '</p></details>' +
    '<div class="planning-actions"><button type="button" class="btn primary" id="planRun">' + esc(tr('Analisar', 'Analyze', 'Analizar')) + '</button>' +
    '<button type="button" class="btn secondary" id="planPdf" disabled>' + esc(tr('Exportar PDF', 'Export PDF', 'Exportar PDF')) + '</button>' +
    '<button type="button" class="btn secondary" id="planCopy" disabled>' + esc(tr('Copiar coordenadas', 'Copy coordinates', 'Copiar coordenadas')) + '</button>' +
    '<button type="button" class="btn secondary" id="planClear">' + esc(tr('Limpar', 'Clear', 'Limpiar')) + '</button></div><div id="planResult" aria-live="polite"></div>';
  ['a', 'b'].forEach(k => {
    $('#planCoord' + k).onchange = e => { const p = parseCoord(e.target.value); if (!p) return notify(tr('Coordenadas no formato: -15.79, -47.88', 'Coordinates as: -15.79, -47.88', 'Coordenadas en formato: -15.79, -47.88'), true); setEnd(k, p, null); };
    $('#planStation' + k).onchange = e => {
      const call = e.target.value.toUpperCase().trim(); if (!call) return;
      const p = stationPos(call);
      if (!p) return notify(tr('Estação sem posição conhecida: ', 'Station without known position: ', 'Estación sin posición conocida: ') + call, true);
      setEnd(k, p, call);
    };
  });
  $('#planningBody').querySelectorAll('[data-own]').forEach(b => b.onclick = () => setEnd(b.dataset.own, [defaults.own.lat, defaults.own.lon], defaults.own.callsign || null));
  $('#planningBody').querySelectorAll('[data-param]').forEach(el => el.onchange = () => { tool.params[el.dataset.param] = Number(el.value); if (tool.a && tool.b) schedule(runLink); });
  $('#planRun').onclick = () => schedule(runLink, 0);
  if ($('#planBackCoverage')) $('#planBackCoverage').onclick = () => openCoverage({restore: tool.fromCoverage});
  $('#planClear').onclick = () => { layer.clearLayers(); Object.assign(tool, {a: null, b: null, stationA: null, stationB: null, result: null, markers: {}, line: null, worst: null}); renderLink(); };
  $('#planCopy').onclick = () => copyText('A: ' + fmtCoord(...tool.a) + ' | B: ' + fmtCoord(...tool.b));
  $('#planPdf').onclick = e => savePdf({kind: 'link', ...linkPayload()}, 'PT2VHF_APRS_Enlace_' + new Date().toISOString().slice(0, 10) + '.pdf', e.target);
  hintLink(); if (t.result) showLink(t.result);
}
function hintLink() {
  if (tool?.kind !== 'link' || !$('#planHint')) return;
  $('#planHint').textContent = !tool.a ? tr('Clique no mapa para marcar o ponto A (ou digite coordenadas/indicativo).', 'Click the map to place point A (or type coordinates/callsign).', 'Haz clic en el mapa para marcar el punto A (o escribe coordenadas/indicativo).')
    : !tool.b ? tr('Agora clique no mapa para marcar o ponto B.', 'Now click the map to place point B.', 'Ahora haz clic en el mapa para marcar el punto B.')
    : tr('Arraste A ou B no mapa para ajustar; a análise é refeita ao soltar.', 'Drag A or B on the map to adjust; the analysis reruns when you drop it.', 'Arrastra A o B en el mapa para ajustar; el análisis se rehace al soltar.');
}
function setEnd(k, p, call = null, run = true) {
  const t = tool; if (t?.kind !== 'link') return;
  t[k] = p; t['station' + k.toUpperCase()] = call;
  if (t.markers[k]) t.markers[k].setLatLng(p);
  else {
    const m = L.marker(p, {icon: icon(k.toUpperCase(), 'end'), draggable: true, title: 'Ponto ' + k.toUpperCase()}).addTo(layer);
    m.on('drag', () => { const ll = m.getLatLng(); t[k] = [ll.lat, ll.lng]; drawLine(); });
    m.on('dragend', () => { const ll = m.getLatLng(); setEnd(k, [ll.lat, ll.lng], null); });
    t.markers[k] = m;
  }
  if ($('#planCoord' + k)) { $('#planCoord' + k).value = fmtCoord(...p); $('#planStation' + k).value = call || ''; }
  drawLine(); hintLink();
  if (run && t.a && t.b) schedule(runLink);
}
function drawLine(color) {
  const t = tool; if (!t.a || !t.b) return;
  if (!t.line) t.line = L.polyline([t.a, t.b], {color: '#9fb2bf', weight: 4, opacity: .9}).addTo(layer);
  t.line.setLatLngs([t.a, t.b]); if (color) t.line.setStyle({color});
}
function linkPayload() { const t = tool; return {a: t.a, b: t.b, station_a: t.stationA, station_b: t.stationB, params: t.params}; }
function schedule(fn, delay = 350) { clearTimeout(runTimer); runTimer = setTimeout(fn, delay); }
async function runLink() {
  const t = tool; if (t?.kind !== 'link' || !t.a || !t.b) return;
  const seq = ++runSeq, box = $('#planResult');
  box.innerHTML = '<p class="planning-small">' + esc(tr('Consultando elevações do terreno e calculando…', 'Querying terrain elevations and calculating…', 'Consultando elevaciones del terreno y calculando…')) + '</p>';
  try {
    const r = (await api('/api/planning/link', linkPayload())).data;
    if (seq !== runSeq || tool !== t) return;
    t.result = r; showLink(r);
  } catch (e) { if (seq === runSeq) { box.innerHTML = '<p class="planning-bad">' + esc(tr('Análise indisponível: ', 'Analysis unavailable: ', 'Análisis no disponible: ') + e.message) + '</p>'; $('#planPdf').disabled = true; } }
}
function showLink(r) {
  const t = tool;
  $('#planResult').innerHTML = resultHtml(r); $('#planPdf').disabled = false; $('#planCopy').disabled = false;
  if (!t.shown) { t.shown = true; const d = $('#planningBody .planning-params'); if (d) d.open = false; }
  drawLine(VERDICT_COLOR[r.verdict]);
  t.line?.bindTooltip(VERDICT_LABEL()[r.verdict] + ' · ' + fmtKm(r.distance_m) + ' · ' + fmtNum(r.budget.rx_dbm, ' dBm') + ' (' + r.budget.s_meter + ')', {sticky: true});
  if (t.worst) { layer.removeLayer(t.worst); t.worst = null; }
  if (r.worst && r.worst.ratio < .6) {
    t.worst = L.circleMarker([r.worst.lat, r.worst.lon], {radius: 8, color: '#fff', weight: 2, fillColor: '#e5484d', fillOpacity: 1}).addTo(layer)
      .bindTooltip(tr('Pior obstrução: ', 'Worst obstruction: ', 'Peor obstrucción: ') + fmtKm(r.worst.distance_m) + ' · ' + fmtNum(r.worst.ground_m, ' m', 0));
  }
}
// --- melhor ponto -----------------------------------------------------------------
async function openSurvey(saved = null) {
  await loadDefaults();
  if (!startTool('survey', {vertices: [], closed: false, ref: null, refStation: null, count: 10, result: null, links: {}, name: '', pickRef: false})) return;
  mapRef().doubleClickZoom.disable();
  if (saved) {
    Object.assign(tool, {vertices: saved.polygon.map(p => [p[0], p[1]]), ref: saved.reference, count: saved.count || 10, name: saved.name});
    finishPolygon(false); mapRef().fitBounds(L.latLngBounds(tool.vertices).pad(.15));
  }
  renderSurvey(); if (saved) schedule(runSurvey, 0);
}
function area(v) {
  if (v.length < 3) return {area: 0, perimeter: 0};
  const lat0 = v.reduce((s, p) => s + p[0], 0) / v.length, kx = Math.cos(lat0 * Math.PI / 180) * 111320, ky = 110574;
  const xy = v.map(p => [p[1] * kx, p[0] * ky]); let a = 0, per = 0;
  xy.forEach((p, i) => { const q = xy[(i + 1) % xy.length]; a += p[0] * q[1] - q[0] * p[1]; });
  v.forEach((p, i) => { per += mapRef().distance(p, v[(i + 1) % v.length]); });
  return {area: Math.abs(a) / 2e6, perimeter: per / 1000};
}
function renderSurvey() {
  const t = tool, m = area(t.vertices), saved = defaults.saved || [];
  $('#planningBody').innerHTML = '<p id="planHint" class="planning-hint"></p>' +
    (!t.closed ? '<div class="planning-actions"><button type="button" class="btn secondary" id="svUndo" ' + (t.vertices.length ? '' : 'disabled') + ' title="Ctrl+Z">' + esc(tr('Desfazer vértice', 'Undo vertex', 'Deshacer vértice')) + '</button>' +
      '<button type="button" class="btn primary" id="svFinish" ' + (t.vertices.length >= 3 ? '' : 'disabled') + '>' + esc(tr('Concluir', 'Finish', 'Terminar')) + '</button>' +
      '<button type="button" class="btn secondary" id="svCancel">' + esc(tr('Cancelar', 'Cancel', 'Cancelar')) + '</button></div>' :
      '<p class="planning-small"><b>' + esc(tr('Área', 'Area', 'Área')) + ':</b> ' + fmtNum(m.area, ' km²', 3) + ' · <b>' + esc(tr('Perímetro', 'Perimeter', 'Perímetro')) + ':</b> ' + fmtNum(m.perimeter, ' km', 2) + ' · ' + t.vertices.length + ' ' + esc(tr('vértices', 'vertices', 'vértices')) + '</p>' +
      '<div class="planning-grid"><label>' + esc(tr('Referência', 'Reference', 'Referencia')) + '<select id="svRef"><option value="">' + esc(tr('Centro do polígono', 'Polygon center', 'Centro del polígono')) + '</option>' +
      (defaults.own ? '<option value="own"' + (t.refStation === '__own' ? ' selected' : '') + '>' + esc(tr('Minha estação', 'My station', 'Mi estación')) + '</option>' : '') +
      '<option value="pick"' + (t.ref && !t.refStation ? ' selected' : '') + '>' + esc(t.ref && !t.refStation ? tr('Ponto escolhido', 'Chosen point', 'Punto elegido') + ' (' + fmtCoord(...t.ref) + ')' : tr('Escolher no mapa…', 'Pick on the map…', 'Elegir en el mapa…')) + '</option>' +
      (t.refStation && t.refStation !== '__own' ? '<option value="st" selected>' + esc(t.refStation) + '</option>' : '') + '</select></label>' +
      '<label>' + esc(tr('ou indicativo', 'or callsign', 'o indicativo')) + '<input id="svRefStation" list="planningStations" autocomplete="off"></label>' +
      '<label>' + esc(tr('Quantidade de pontos', 'Number of points', 'Cantidad de puntos')) + '<input id="svCount" type="number" min="1" max="50" value="' + t.count + '"></label></div>' +
      '<div class="planning-actions"><button type="button" class="btn primary" id="svRun">' + esc(tr('Buscar pontos', 'Find points', 'Buscar puntos')) + '</button>' +
      '<button type="button" class="btn secondary" id="svCsv" disabled>CSV</button><button type="button" class="btn secondary" id="svPdf" disabled>' + esc(tr('Exportar PDF', 'Export PDF', 'Exportar PDF')) + '</button>' +
      '<button type="button" class="btn secondary" id="svRedraw">' + esc(tr('Novo polígono', 'New polygon', 'Nuevo polígono')) + '</button></div>') +
    '<details class="planning-params"><summary>' + esc(tr('Surveys salvos', 'Saved surveys', 'Surveys guardados')) + ' (' + saved.length + ')</summary>' +
    (t.closed ? '<div class="planning-row"><input id="svName" maxlength="60" placeholder="' + esc(tr('Nome do survey', 'Survey name', 'Nombre del survey')) + '" value="' + esc(t.name || '') + '"><button type="button" class="btn secondary" id="svSave">' + esc(tr('Salvar', 'Save', 'Guardar')) + '</button></div>' : '') +
    (saved.length ? '<ul class="planning-saved">' + saved.map(s => '<li><button type="button" class="planning-link" data-open="' + s.id + '">' + esc(s.name) + '</button> <small>' + s.polygon.length + ' ' + esc(tr('vértices', 'vertices', 'vértices')) + '</small> <button type="button" class="planning-link" data-del="' + s.id + '" aria-label="' + esc(tr('Excluir', 'Delete', 'Eliminar')) + ' ' + esc(s.name) + '">✕</button></li>').join('') + '</ul>'
      : '<p class="planning-small">' + esc(tr('Nenhum survey salvo.', 'No saved surveys.', 'Ningún survey guardado.')) + '</p>') +
    '</details><div id="svResult" aria-live="polite"></div>';
  const on = (id, fn) => { if ($('#' + id)) $('#' + id).onclick = fn; };
  on('svUndo', undoVertex); on('svFinish', () => finishPolygon()); on('svCancel', closeTool); on('svRun', () => schedule(runSurvey, 0));
  on('svRedraw', () => { layer.clearLayers(); Object.assign(tool, {vertices: [], closed: false, result: null, links: {}, guide: null, shape: null, vmarkers: null, pmarkers: null, refMarker: null}); mapRef().doubleClickZoom.disable(); renderSurvey(); });
  on('svCsv', exportCsv);
  on('svPdf', e => savePdf(surveyPayload(), 'PT2VHF_APRS_Survey_' + new Date().toISOString().slice(0, 10) + '.pdf', e.target));
  on('svSave', saveSurvey);
  if ($('#svCount')) $('#svCount').onchange = e => { const n = Number(e.target.value); if (!(n >= 1 && n <= 50)) return notify(tr('Quantidade: 1 a 50', 'Number: 1 to 50', 'Cantidad: 1 a 50'), true); tool.count = n; schedule(runSurvey); };
  if ($('#svRef')) $('#svRef').onchange = e => {
    const v = e.target.value;
    if (v === 'pick') { tool.pickRef = true; hintSurvey(); return; }
    if (v === 'own') { setRef([defaults.own.lat, defaults.own.lon], '__own'); return; }
    if (!v) { tool.ref = null; tool.refStation = null; drawRef(); schedule(runSurvey); }
  };
  if ($('#svRefStation')) $('#svRefStation').onchange = e => {
    const call = e.target.value.toUpperCase().trim(), p = stationPos(call);
    if (!p) return notify(tr('Estação sem posição conhecida: ', 'Station without known position: ', 'Estación sin posición conocida: ') + call, true);
    setRef(p, call);
  };
  $('#planningBody').querySelectorAll('[data-open]').forEach(b => b.onclick = () => { const s = saved.find(x => String(x.id) === b.dataset.open); if (s) openSurvey(s); });
  $('#planningBody').querySelectorAll('[data-del]').forEach(b => b.onclick = async () => {
    try { const r = await api('/api/planning/delete', {id: Number(b.dataset.del)}); defaults.saved = r.saved; renderSurvey(); } catch (e) { notify(e.message, true); }
  });
  hintSurvey(); if (t.result) showSurvey(t.result);
}
function hintSurvey() {
  if (tool?.kind !== 'survey' || !$('#planHint')) return;
  $('#planHint').textContent = tool.pickRef ? tr('Clique no mapa para escolher o ponto de referência.', 'Click the map to choose the reference point.', 'Haz clic en el mapa para elegir el punto de referencia.')
    : !tool.closed ? (tool.vertices.length < 3
      ? tr('Clique no mapa para criar os vértices da área', 'Click the map to create the area vertices', 'Haz clic en el mapa para crear los vértices del área') + ' (' + tool.vertices.length + '/3).'
      : tr('Continue clicando ou feche a área: clique no primeiro vértice, dê duplo clique ou use Concluir.', 'Keep clicking or close the area: click the first vertex, double-click or use Finish.', 'Sigue haciendo clic o cierra el área: haz clic en el primer vértice, doble clic o usa Terminar.'))
    : tr('Arraste os vértices para ajustar; arraste o ponto do meio de um lado para criar um vértice; botão direito num vértice remove.', 'Drag vertices to adjust; drag a side midpoint to add a vertex; right-click a vertex to remove it.', 'Arrastra los vértices para ajustar; arrastra el punto medio de un lado para crear un vértice; clic derecho en un vértice lo quita.');
}
function surveyClick(p) {
  const t = tool, map = mapRef();
  if (t.pickRef) { setRef(p, null); return; }
  if (t.closed) return;
  if (t.vertices.length >= 3 && map.latLngToContainerPoint(p).distanceTo(map.latLngToContainerPoint(t.vertices[0])) < 12) { finishPolygon(); return; }
  if (t.vertices.length >= 100) return notify(tr('Máximo de 100 vértices', 'Maximum of 100 vertices', 'Máximo de 100 vértices'), true);
  t.vertices.push(p); drawShape();
  if ($('#svUndo')) { $('#svUndo').disabled = false; $('#svFinish').disabled = t.vertices.length < 3; }
  hintSurvey();
}
function undoVertex() { const t = tool; if (t?.kind !== 'survey' || t.closed || !t.vertices.length) return; t.vertices.pop(); drawShape(); renderSurvey(); }
function finishPolygon(run = true) {
  const t = tool; if (t.vertices.length < 3) return notify(tr('Marque pelo menos 3 vértices', 'Place at least 3 vertices', 'Marca al menos 3 vértices'), true);
  t.closed = true; mapRef().doubleClickZoom.enable(); if (t.guide) { layer.removeLayer(t.guide); t.guide = null; }
  drawShape(); drawRef();
  if (run) { renderSurvey(); schedule(runSurvey, 0); }
}
function drawShape() {
  const t = tool;
  if (t.shape) layer.removeLayer(t.shape);
  (t.vmarkers || []).forEach(m => layer.removeLayer(m)); t.vmarkers = [];
  t.shape = t.closed ? L.polygon(t.vertices, {color: '#f3cf48', weight: 2, fillOpacity: .08, interactive: false}).addTo(layer)
    : L.polyline(t.vertices, {color: '#f3cf48', weight: 2, interactive: false}).addTo(layer);
  t.vertices.forEach((p, i) => {
    const m = L.marker(p, {icon: L.divIcon({className: 'planning-vertex' + (i === 0 && !t.closed ? ' first' : ''), iconSize: [14, 14], iconAnchor: [7, 7]}), draggable: t.closed, keyboard: false}).addTo(layer);
    if (!t.closed && i === 0) m.on('click', e => { L.DomEvent.stop(e); if (t.vertices.length >= 3) finishPolygon(); });
    if (t.closed) {
      m.on('drag', () => { const ll = m.getLatLng(); t.vertices[i] = [ll.lat, ll.lng]; t.shape.setLatLngs(t.vertices); });
      m.on('dragend', () => { drawShape(); renderSurvey(); schedule(runSurvey); });
      m.on('contextmenu', e => { L.DomEvent.stop(e); if (t.vertices.length <= 3) return notify(tr('A área precisa de pelo menos 3 vértices', 'The area needs at least 3 vertices', 'El área necesita al menos 3 vértices'), true); t.vertices.splice(i, 1); drawShape(); renderSurvey(); schedule(runSurvey); });
    }
    t.vmarkers.push(m);
  });
  if (t.closed) t.vertices.forEach((p, i) => {
    const q = t.vertices[(i + 1) % t.vertices.length], mid = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
    const m = L.marker(mid, {icon: L.divIcon({className: 'planning-vertex mid', iconSize: [10, 10], iconAnchor: [5, 5]}), draggable: true, keyboard: false}).addTo(layer);
    m.on('dragend', () => { const ll = m.getLatLng(); t.vertices.splice(i + 1, 0, [ll.lat, ll.lng]); drawShape(); renderSurvey(); schedule(runSurvey); });
    t.vmarkers.push(m);
  });
}
function setRef(p, station) { const t = tool; t.ref = p; t.refStation = station; t.pickRef = false; drawRef(); renderSurvey(); schedule(runSurvey); }
function drawRef() {
  const t = tool; if (t.refMarker) { layer.removeLayer(t.refMarker); t.refMarker = null; }
  const p = t.ref || (t.result ? [t.result.reference.lat, t.result.reference.lon] : null); if (!p || !t.closed) return;
  t.refMarker = L.marker(p, {icon: L.divIcon({className: 'planning-ref', iconSize: [18, 18], iconAnchor: [9, 9]}), keyboard: false}).addTo(layer);
}
async function runSurvey() {
  const t = tool; if (t?.kind !== 'survey' || !t.closed) return;
  const seq = ++runSeq, box = $('#svResult');
  box.innerHTML = '<p class="planning-small">' + esc(tr('Consultando elevações dentro da área… áreas grandes podem levar alguns segundos.', 'Querying elevations inside the area… large areas may take a few seconds.', 'Consultando elevaciones dentro del área… las áreas grandes pueden tardar unos segundos.')) + '</p>';
  try {
    const r = (await api('/api/planning/best', {polygon: t.vertices, reference: t.ref, count: t.count})).data;
    if (seq !== runSeq || tool !== t) return;
    t.result = r; t.links = {}; showSurvey(r); drawRef();
  } catch (e) { if (seq === runSeq) box.innerHTML = '<p class="planning-bad">' + esc(tr('Busca indisponível: ', 'Search unavailable: ', 'Búsqueda no disponible: ') + e.message) + '</p>'; }
}
function showSurvey(r) {
  const t = tool;
  (t.pmarkers || []).forEach(m => layer.removeLayer(m)); t.pmarkers = [];
  r.points.forEach(p => {
    const m = L.marker([p.lat, p.lon], {icon: icon(String(p.rank), 'point' + (p.edge ? ' edge' : '')), zIndexOffset: 1000}).addTo(layer);
    m.bindTooltip('Nº ' + p.rank + ' · ' + fmtNum(p.elevation_m, ' m', 0));
    m.on('click', e => { L.DomEvent.stop(e); highlight(p.rank, true); });
    t.pmarkers.push(m);
  });
  const ref = r.reference;
  $('#svResult').innerHTML = (r.warning ? '<p class="planning-small planning-warn">' + esc(r.warning) + '</p>' : '') + (r.note ? '<p class="planning-small">' + esc(r.note) + '</p>' : '') +
    '<p class="planning-small">' + esc(tr('Do mais alto para o mais baixo.', 'From highest to lowest.', 'Del más alto al más bajo.')) + ' ' + esc(tr('Referência', 'Reference', 'Referencia')) + ': ' + fmtNum(ref.elevation_m, ' m', 0) + ' · ' +
    esc(tr('altitudes na área', 'elevations in the area', 'altitudes en el área')) + ': ' + fmtNum(r.elevation_range_m[0], ' m', 0) + ' – ' + fmtNum(r.elevation_range_m[1], ' m', 0) + '</p>' +
    (r.points.length ? '<div class="planning-scroll"><table class="planning-table planning-survey"><thead><tr><th>Nº</th><th>' + esc(tr('Altitude', 'Elevation', 'Altitud')) + '</th><th>' + esc(tr('Desnível', 'Height diff.', 'Desnivel')) + '</th><th>' + esc(tr('Distância', 'Distance', 'Distancia')) + '</th><th>' + esc(tr('Direção', 'Direction', 'Dirección')) + '</th><th>' + esc(tr('Coordenadas', 'Coordinates', 'Coordenadas')) + '</th><th></th></tr></thead><tbody>' +
      r.points.map(p => '<tr data-rank="' + p.rank + '" tabindex="0"><td><b>' + p.rank + '</b></td><td>' + fmtNum(p.elevation_m, ' m', 0) + (p.edge ? ' ↗' : '') + '</td><td>' + (p.delta_m > 0 ? '+' : '') + fmtNum(p.delta_m, ' m', 0) + '</td><td>' + fmtKm(p.distance_m) + '</td><td>' + esc(p.direction) + ' ' + p.bearing_deg + '°</td>' +
        '<td><button type="button" class="planning-link" data-copy="' + p.rank + '">' + fmtCoord(p.lat, p.lon) + '</button></td><td><button type="button" class="btn secondary" data-link="' + p.rank + '">' + esc(tr('Enlace…', 'Link…', 'Enlace…')) + '</button></td></tr>' +
        '<tr class="planning-linkrow" data-linkrow="' + p.rank + '" hidden><td colspan="7"></td></tr>').join('') + '</tbody></table></div>' +
      '<p class="planning-small">' + esc(tr('↗ = borda da área: o terreno continua subindo fora do polígono. Elevações do modelo de terreno (~30–40 m), sem prédios e árvores.',
        '↗ = area edge: terrain keeps rising outside the polygon. Terrain model elevations (~30–40 m), without buildings and trees.',
        '↗ = borde del área: el terreno sigue subiendo fuera del polígono. Elevaciones del modelo de terreno (~30–40 m), sin edificios ni árboles.')) + '</p>' +
      '<details class="planning-params"><summary>' + esc(tr('Avaliar pela cobertura', 'Evaluate by coverage', 'Evaluar por cobertura')) + '</summary>' +
      '<p class="planning-small">' + esc(tr('O ponto mais alto nem sempre é o que cobre mais. Calcula a cobertura dos 5 primeiros e conta a área e as estações conhecidas alcançadas.',
        'The highest point is not always the one that covers most. Computes the coverage of the top 5 and counts the area and known stations reached.',
        'El punto más alto no siempre es el que más cubre. Calcula la cobertura de los 5 primeros y cuenta el área y las estaciones conocidas alcanzadas.')) + '</p>' +
      '<div class="planning-row"><label class="planning-small">' + esc(tr('Raio (km)', 'Radius (km)', 'Radio (km)')) + ' <input id="svCovRadius" type="number" min="1" max="30" value="15" style="width:70px"></label>' +
      '<button type="button" class="btn primary" id="svCovRun">' + esc(tr('Avaliar 5 primeiros', 'Evaluate top 5', 'Evaluar 5 primeros')) + '</button></div><div id="svCoverage" aria-live="polite"></div></details>'
      : '<p class="planning-small">' + esc(tr('Nenhum ponto encontrado.', 'No points found.', 'Ningún punto encontrado.')) + '</p>');
  $('#svCsv').disabled = !r.points.length; $('#svPdf').disabled = !r.points.length;
  const box = $('#svResult');
  box.querySelectorAll('tr[data-rank]').forEach(row => {
    const go = () => { const p = r.points.find(x => x.rank === Number(row.dataset.rank)); mapRef().setView([p.lat, p.lon], Math.max(mapRef().getZoom(), 14)); highlight(p.rank, false); };
    row.onclick = e => { if (!e.target.closest('button')) go(); }; row.onkeydown = e => { if (e.key === 'Enter') go(); };
  });
  box.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => copyText(b.textContent));
  box.querySelectorAll('[data-link]').forEach(b => b.onclick = () => pointLink(Number(b.dataset.link)));
  if ($('#svCovRun')) $('#svCovRun').onclick = e => surveyByCoverage(e.target);
}
function highlight(rank, scroll) {
  document.querySelectorAll('#svResult tr[data-rank]').forEach(r => r.classList.toggle('active', Number(r.dataset.rank) === rank));
  tool?.pmarkers?.forEach((m, i) => m.getElement()?.classList.toggle('active', i === rank - 1));
  if (scroll) document.querySelector('#svResult tr[data-rank="' + rank + '"]')?.scrollIntoView({block: 'nearest'});
}
function pointLink(rank) {
  const t = tool, row = document.querySelector('[data-linkrow="' + rank + '"]'), cell = row.firstElementChild, prev = t.links[rank];
  if (!row.hidden && !prev) { row.hidden = true; return; }
  row.hidden = false;
  cell.innerHTML = '<div class="planning-row"><label>' + esc(tr('Até', 'To', 'Hasta')) + ' <input data-target list="planningStations" placeholder="' + esc(tr('referência ou indicativo', 'reference or callsign', 'referencia o indicativo')) + '" value="' + esc(prev?.station_b || '') + '" autocomplete="off"></label>' +
    '<label>' + esc(tr('Antena no ponto (m)', 'Antenna at the point (m)', 'Antena en el punto (m)')) + ' <input type="number" data-ha min="0" max="300" value="' + (prev?.params.height_a ?? 10) + '" style="width:70px"></label>' +
    '<label>' + esc(tr('Antena no destino (m)', 'Antenna at the target (m)', 'Antena en el destino (m)')) + ' <input type="number" data-hb min="0" max="300" value="' + (prev?.params.height_b ?? 10) + '" style="width:70px"></label>' +
    '<button type="button" class="btn primary" data-run>' + esc(tr('Analisar', 'Analyze', 'Analizar')) + '</button><button type="button" class="btn secondary" data-full>' + esc(tr('Abrir no mapa', 'Open on map', 'Abrir en el mapa')) + '</button></div>' +
    '<div data-out>' + (prev?.result ? linkSummary(prev.result) : '') + '</div>';
  const payload = () => {
    const p = t.result.points.find(x => x.rank === rank), call = cell.querySelector('[data-target]').value.toUpperCase().trim();
    const pos = call ? stationPos(call) : null;
    if (call && !pos) throw new Error(tr('Estação sem posição conhecida: ', 'Station without known position: ', 'Estación sin posición conocida: ') + call);
    return {rank, target: pos ? call : tr('referência', 'reference', 'referencia'), a: [p.lat, p.lon], b: pos || [t.result.reference.lat, t.result.reference.lon],
      station_a: null, station_b: pos ? call : null,
      params: {height_a: Number(cell.querySelector('[data-ha]').value), height_b: Number(cell.querySelector('[data-hb]').value),
        freq_mhz: defaults.freq_mhz, tx_power_w: defaults.tx_power_w, sensitivity_dbm: defaults.sensitivity_dbm}};
  };
  cell.querySelector('[data-run]').onclick = async () => {
    const out = cell.querySelector('[data-out]');
    try { const item = payload(); out.innerHTML = '<p class="planning-small">…</p>'; item.result = (await api('/api/planning/link', item)).data; t.links[rank] = item; out.innerHTML = linkSummary(item.result); }
    catch (e) { out.innerHTML = '<p class="planning-bad">' + esc(e.message) + '</p>'; }
  };
  cell.querySelector('[data-full]').onclick = () => { try { const item = payload(); openLink({a: item.a, b: item.b, stationB: item.station_b, params: item.params}); } catch (e) { notify(e.message, true); } };
}
function linkSummary(r) {
  return '<p>' + badge(r) + ' ' + fmtKm(r.distance_m) + ' · ' + fmtNum(r.budget.rx_dbm, ' dBm') + ' (' + esc(r.budget.s_meter) + ') · ' + esc(tr('margem', 'margin', 'margen')) + ' ' + fmtNum(r.budget.margin_db, ' dB') + '</p>' +
    profileSvg(r, {width: 440, height: 170}) + '<p class="planning-small">' + esc(tr('Incluído no PDF do survey.', 'Included in the survey PDF.', 'Incluido en el PDF del survey.')) + '</p>';
}
function exportCsv() {
  const r = tool.result, q = v => '"' + String(v).replaceAll('"', '""') + '"';
  const lines = [['Nº', 'Altitude (m)', 'Desnível (m)', 'Distância (m)', 'Direção', 'Azimute (°)', 'Latitude', 'Longitude', 'Observação'].map(q).join(';')];
  r.points.forEach(p => lines.push([p.rank, p.elevation_m, p.delta_m, p.distance_m, p.direction, p.bearing_deg, p.lat, p.lon, p.edge ? 'Borda da área' : 'Topo'].map(q).join(';')));
  saveText('PT2VHF_APRS_Survey_' + new Date().toISOString().slice(0, 10) + '.csv', '﻿' + lines.join('\r\n'));
}
function surveyPayload() {
  const t = tool;
  return {kind: 'survey', name: $('#svName')?.value || t.name || '', polygon: t.vertices, reference: t.ref, count: t.count,
    links: Object.values(t.links).map(l => ({rank: l.rank, target: l.target, a: l.a, b: l.b, station_b: l.station_b, params: l.params}))};
}
async function saveSurvey() {
  const t = tool, name = $('#svName').value.trim();
  if (!name) return notify(tr('Dê um nome ao survey', 'Name the survey', 'Ponle un nombre al survey'), true);
  try { const r = await api('/api/planning/save', {name, polygon: t.vertices, reference: t.ref, count: t.count}); t.name = name; defaults.saved = r.saved; renderSurvey(); notify(tr('Survey salvo: ', 'Survey saved: ', 'Survey guardado: ') + name); }
  catch (e) { notify(e.message, true); }
}
// --- análise de cobertura (v1.15.0, mesmo modelo do PT2VHF Mesh Analyzer) --------------
const COVERAGE_SCALES = {
  plasma: ['Plasma', [[13, 8, 135], [126, 3, 168], [204, 71, 120], [248, 149, 64], [240, 249, 33]]],
  viridis: ['Viridis', [[68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37]]],
  turbo: [() => tr('Arco-íris', 'Rainbow', 'Arcoíris'), [[48, 18, 59], [70, 134, 251], [26, 228, 182], [250, 186, 57], [180, 4, 38]]],
  signal: [() => tr('Vermelho → verde', 'Red → green', 'Rojo → verde'), [[192, 57, 43], [230, 126, 34], [241, 196, 15], [130, 200, 80], [39, 174, 96]]]};
const scaleName = k => { const n = COVERAGE_SCALES[k][0]; return typeof n === 'function' ? n() : n; };
const COVERAGE_CLIMATES = () => [['equatorial', tr('Equatorial', 'Equatorial', 'Ecuatorial')],
  ['continental_subtropical', tr('Continental subtropical', 'Continental subtropical', 'Continental subtropical')],
  ['maritime_subtropical', tr('Marítimo subtropical', 'Maritime subtropical', 'Marítimo subtropical')],
  ['desert', tr('Desértico', 'Desert', 'Desértico')], ['continental_temperate', tr('Continental temperado', 'Continental temperate', 'Continental templado')],
  ['maritime_temperate_land', tr('Marítimo temperado (terra)', 'Maritime temperate (land)', 'Marítimo templado (tierra)')],
  ['maritime_temperate_sea', tr('Marítimo temperado (mar)', 'Maritime temperate (sea)', 'Marítimo templado (mar)')]];
const COVERAGE_FIELDS = () => ({
  tx: [['tx_power_w', tr('Potência (W)', 'Power (W)', 'Potencia (W)'), .1, 1500, .1], ['freq_mhz', tr('Frequência (MHz)', 'Frequency (MHz)', 'Frecuencia (MHz)'), 28, 1300, .001],
    ['tx_height_m', tr('Antena acima do solo (m)', 'Antenna above ground (m)', 'Antena sobre el suelo (m)'), .5, 300, .5], ['tx_gain_dbi', tr('Ganho da antena (dBi)', 'Antenna gain (dBi)', 'Ganancia de la antena (dBi)'), -10, 30, .5]],
  rx: [['rx_sensitivity_dbm', tr('Sensibilidade (dBm)', 'Sensitivity (dBm)', 'Sensibilidad (dBm)'), -140, -80, 1], ['rx_height_m', tr('Antena acima do solo (m)', 'Antenna above ground (m)', 'Antena sobre el suelo (m)'), .5, 100, .5],
    ['rx_gain_dbi', tr('Ganho da antena (dBi)', 'Antenna gain (dBi)', 'Ganancia de la antena (dBi)'), -10, 30, .5], ['rx_cable_db', tr('Perda no cabo (dB)', 'Cable loss (dB)', 'Pérdida en el cable (dB)'), 0, 30, .5]],
  env: [['clutter_m', tr('Altura de obstáculos (m)', 'Clutter height (m)', 'Altura de obstáculos (m)'), 0, 60, .5], ['refractivity_n', tr('Refratividade (N)', 'Refractivity (N)', 'Refractividad (N)'), 250, 400, 1]],
  sim: [['location_pct', tr('% de locais', '% of locations', '% de lugares'), 50, 99.9, 1], ['time_pct', tr('% do tempo', '% of time', '% del tiempo'), 50, 99.9, 1]]});
function coverageColor(scale, f) {
  const stops = (COVERAGE_SCALES[scale] || COVERAGE_SCALES.plasma)[1], x = Math.max(0, Math.min(1, f)) * (stops.length - 1);
  const i = Math.min(stops.length - 2, Math.floor(x)), u = x - i, a = stops[i], b = stops[i + 1];
  return [0, 1, 2].map(k => Math.round(a[k] + (b[k] - a[k]) * u));
}
const coverageGradient = scale => 'linear-gradient(90deg,' + [0, .25, .5, .75, 1].map(f => 'rgb(' + coverageColor(scale, f).join(',') + ')').join(',') + ')';
const num = (v, d = 1) => fmtNum(v, '', d);
function uvFromDbm(dbm) { return Math.sqrt(50 * Math.pow(10, (dbm - 30) / 10)) * 1e6; }
// S-meter em VHF (S9 = −93 dBm, 6 dB por unidade; IARU R.1), igual ao planning.py.
function sUnits(dbm) {
  if (dbm >= -93) return dbm > -92.5 ? 'S9+' + Math.round(dbm + 93) + ' dB' : 'S9';
  return 'S' + Math.max(0, Math.min(9, Math.round(9 + (dbm + 93) / 6)));
}
async function openCoverage(opts = {}) {
  await loadDefaults();
  const saved = opts.restore;
  if (!startTool('coverage', {tx: null, station: null, pickTx: true, result: null, overlay: null, marker: null, marks: null, running: false, searchKm: 5,
    params: {tx_power_w: 50, freq_mhz: defaults.freq_mhz || 145.57, tx_height_m: 10, tx_gain_dbi: 3, rx_sensitivity_dbm: defaults.sensitivity_dbm ?? -113,
      rx_height_m: 2, rx_gain_dbi: 3, rx_cable_db: 1, climate: 'continental_subtropical', clutter_m: 1, refractivity_n: 301,
      location_pct: 95, time_pct: 95, max_km: 50, hires: false},
    display: {style: 'heat', min: -125, max: -70, scale: 'plasma', transparency: 50}})) return;
  if (saved) Object.assign(tool, {params: {...saved.params}, display: {...saved.display}, searchKm: saved.searchKm});
  renderCoverage();
  if (saved) {
    setCoverageTx(saved.tx, saved.station);
    if (saved.result) { tool.result = saved.result; drawCoverage(); showCoverage(saved.result); }
  } else if (opts.station) {
    const p = stationPos(opts.station); if (p) setCoverageTx(p, opts.station);
  }
}
function renderCoverage() {
  const t = tool, p = t.params, v = t.display, F = COVERAGE_FIELDS();
  const field = ([k, label, min, max, step]) => '<label>' + esc(label) + '<input type="number" data-cov="' + k + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + esc(String(p[k])) + '"></label>';
  const grid = fields => '<div class="planning-grid">' + fields.map(field).join('') + '</div>';
  const section = (title, help, inner, open) => '<details class="planning-params coverage-section"' + (open ? ' open' : '') + '><summary>' + esc(title) + '</summary>' +
    (help ? '<p class="planning-small">' + esc(help) + '</p>' : '') + inner + '</details>';
  const sens = p.rx_sensitivity_dbm;
  $('#planningBody').innerHTML = '<p id="planHint" class="planning-hint"></p>' +
    section(tr('Transmissor', 'Transmitter', 'Transmisor'), tr('A estação cuja cobertura é simulada.', 'The station whose coverage is simulated.', 'La estación cuya cobertura se simula.'),
      '<div class="planning-field"><label for="covCoord">' + esc(tr('Latitude, longitude', 'Latitude, longitude', 'Latitud, longitud')) + '</label><div class="planning-row">' +
      '<input id="covCoord" placeholder="-15.79, -47.88" value="' + (t.tx ? fmtCoord(...t.tx) : '') + '">' +
      '<input id="covStation" list="planningStations" placeholder="' + esc(tr('ou indicativo', 'or callsign', 'o indicativo')) + '" value="' + esc(t.station || '') + '" autocomplete="off"></div></div>' +
      grid(F.tx) +
      '<div class="planning-actions"><button type="button" class="btn ' + (t.pickTx ? 'primary' : 'secondary') + '" id="covPick">' + esc(tr('Marcar no mapa', 'Place on map', 'Marcar en el mapa')) + '</button>' +
      (defaults.own ? '<button type="button" class="btn secondary" id="covOwn">' + esc(tr('Minha estação', 'My station', 'Mi estación')) + '</button>' : '') +
      '<button type="button" class="btn secondary" id="covCenter"' + (t.tx ? '' : ' disabled') + '>' + esc(tr('Centralizar', 'Center', 'Centrar')) + '</button></div>' +
      '<div class="planning-row"><label class="planning-small">' + esc(tr('Buscar ponto mais alto num raio de (km)', 'Search the highest point within (km)', 'Buscar el punto más alto en un radio de (km)')) +
      ' <input type="number" id="covSearchKm" min="0.05" max="50" step="0.1" value="' + t.searchKm + '" style="width:70px"></label>' +
      '<button type="button" class="btn secondary" id="covHighest"' + (t.tx ? '' : ' disabled') + '>' + esc(tr('Ir para o ponto mais alto', 'Go to the highest point', 'Ir al punto más alto')) + '</button></div>' +
      '<p class="planning-small">' + esc(tr('Dica: arraste o pino para ajustar, ou digite coordenadas/indicativo.', 'Tip: drag the pin to adjust, or type coordinates/callsign.', 'Consejo: arrastra el pin para ajustar, o escribe coordenadas/indicativo.')) + '</p>', true) +
    section(tr('Receptor', 'Receiver', 'Receptor'), tr('As estações que devem ouvir este transmissor. APRS 1200 bps: −113 dBm ≈ 0,5 µV (S6) decodifica pacotes.', 'The stations that should hear this transmitter. APRS 1200 bps: −113 dBm ≈ 0.5 µV (S6) decodes packets.', 'Las estaciones que deben oír este transmisor. APRS 1200 bps: −113 dBm ≈ 0,5 µV (S2) decodifica paquetes.'),
      grid(F.rx) + '<p class="planning-small" id="covSens">' + esc(tr('Sensibilidade', 'Sensitivity', 'Sensibilidad')) + ': ' + num(uvFromDbm(sens), 2) + ' µV · ' + esc(sUnits(sens)) + '</p>', false) +
    section(tr('Ambiente', 'Environment', 'Ambiente'), tr('Premissas de terreno e atmosfera; os valores padrão servem para a maioria dos casos.', 'Terrain and atmosphere assumptions; defaults suit most cases.', 'Premisas de terreno y atmósfera; los valores por defecto sirven para la mayoría de los casos.'),
      '<div class="planning-grid"><label>' + esc(tr('Clima de rádio', 'Radio climate', 'Clima de radio')) + '<select id="covClimate">' + COVERAGE_CLIMATES().map(([k, l]) => '<option value="' + k + '"' + (k === p.climate ? ' selected' : '') + '>' + esc(l) + '</option>').join('') + '</select></label></div>' + grid(F.env), false) +
    section(tr('Simulação', 'Simulation', 'Simulación'), tr('Confiabilidade estatística do resultado.', 'Statistical reliability of the result.', 'Confiabilidad estadística del resultado.'),
      grid(F.sim) + '<label class="planning-small"><input type="checkbox" id="covHires"' + (p.hires ? ' checked' : '') + '> ' +
      esc(tr('Relevo em alta resolução (~38 m): mais detalhe, mais lento, raio até 40 km', 'High-resolution terrain (~38 m): more detail, slower, radius up to 40 km', 'Relieve en alta resolución (~38 m): más detalle, más lento, radio hasta 40 km')) + '</label>', false) +
    section(tr('Exibição', 'Display', 'Visualización'), tr('As mudanças valem na hora para a cobertura já calculada.', 'Changes apply immediately to the computed coverage.', 'Los cambios se aplican de inmediato a la cobertura calculada.'),
      '<div class="planning-actions coverage-style" role="radiogroup"><button type="button" class="btn ' + (v.style === 'heat' ? 'primary' : 'secondary') + '" data-cov-style="heat" role="radio" aria-checked="' + (v.style === 'heat') + '">' + esc(tr('Mapa de calor', 'Heat map', 'Mapa de calor')) + '</button>' +
      '<button type="button" class="btn ' + (v.style === 'contours' ? 'primary' : 'secondary') + '" data-cov-style="contours" role="radio" aria-checked="' + (v.style === 'contours') + '">' + esc(tr('Contornos', 'Contours', 'Contornos')) + '</button></div>' +
      '<div class="planning-grid"><label>' + esc(tr('Mínimo (dBm)', 'Minimum (dBm)', 'Mínimo (dBm)')) + '<input type="number" data-cov-display="min" min="-160" max="-20" step="1" value="' + v.min + '"></label>' +
      '<label>' + esc(tr('Máximo (dBm)', 'Maximum (dBm)', 'Máximo (dBm)')) + '<input type="number" data-cov-display="max" min="-150" max="0" step="1" value="' + v.max + '"></label>' +
      '<label>' + esc(tr('Escala de cores', 'Color scale', 'Escala de colores')) + '<select data-cov-display="scale">' + Object.keys(COVERAGE_SCALES).map(k => '<option value="' + k + '"' + (k === v.scale ? ' selected' : '') + '>' + esc(scaleName(k)) + '</option>').join('') + '</select></label>' +
      '<label>' + esc(tr('Transparência (%)', 'Transparency (%)', 'Transparencia (%)')) + '<input type="number" data-cov-display="transparency" min="0" max="90" step="5" value="' + v.transparency + '"></label></div>' +
      '<div class="coverage-bar" id="covBar" style="background:' + coverageGradient(v.scale) + '"></div><div class="coverage-bar-labels"><span id="covBarMin">' + v.min + ' dBm</span><span id="covBarMax">' + v.max + ' dBm</span></div>', true) +
    '<div class="coverage-radius"><label for="covRadius"><b>' + esc(tr('Raio da cobertura (km)', 'Coverage radius (km)', 'Radio de la cobertura (km)')) + '</b></label><input type="number" id="covRadius" min="1" max="100" step="1" value="' + p.max_km + '">' +
    '<span class="planning-small">' + esc(tr('até 100 km (40 km em alta resolução); raios maiores demoram mais', 'up to 100 km (40 km in high resolution); larger radii take longer', 'hasta 100 km (40 km en alta resolución); radios mayores tardan más')) + '</span></div>' +
    '<div class="planning-actions"><button type="button" class="btn primary" id="covRun"' + (t.tx ? '' : ' disabled') + '>' + esc(tr('Calcular cobertura', 'Compute coverage', 'Calcular cobertura')) + '</button>' +
    '<button type="button" class="btn secondary" id="covPdf"' + (t.result ? '' : ' disabled') + '>' + esc(tr('Baixar PDF', 'Download PDF', 'Descargar PDF')) + '</button>' +
    '<button type="button" class="btn secondary" id="covClear">' + esc(tr('Limpar', 'Clear', 'Limpiar')) + '</button></div><div id="covResult" aria-live="polite"></div>';
  const body = $('#planningBody');
  $('#covCoord').onchange = e => { const c = parseCoord(e.target.value); if (!c) return notify(tr('Coordenadas no formato: -15.79, -47.88', 'Coordinates as: -15.79, -47.88', 'Coordenadas en formato: -15.79, -47.88'), true); setCoverageTx(c, null); };
  $('#covStation').onchange = e => {
    const call = e.target.value.toUpperCase().trim(); if (!call) return;
    const c = stationPos(call);
    if (!c) return notify(tr('Estação sem posição conhecida: ', 'Station without known position: ', 'Estación sin posición conocida: ') + call, true);
    setCoverageTx(c, call); mapRef().setView(c, Math.max(mapRef().getZoom(), 11));
  };
  if ($('#covOwn')) $('#covOwn').onclick = () => { setCoverageTx([defaults.own.lat, defaults.own.lon], defaults.own.callsign || null); mapRef().setView(tool.tx, Math.max(mapRef().getZoom(), 11)); };
  body.querySelectorAll('[data-cov]').forEach(el => el.onchange = () => {
    const n = Number(el.value); if (!Number.isFinite(n)) return;
    p[el.dataset.cov] = n;
    if (el.dataset.cov === 'rx_sensitivity_dbm') $('#covSens').textContent = tr('Sensibilidade', 'Sensitivity', 'Sensibilidad') + ': ' + num(uvFromDbm(n), 2) + ' µV · ' + sUnits(n);
  });
  $('#covClimate').onchange = e => { p.climate = e.target.value; };
  $('#covHires').onchange = e => { p.hires = e.target.checked; if (p.hires && p.max_km > 40) { p.max_km = 40; $('#covRadius').value = 40; notify(tr('Alta resolução: raio limitado a 40 km.', 'High resolution: radius limited to 40 km.', 'Alta resolución: radio limitado a 40 km.')); } };
  $('#covRadius').onchange = e => {
    const n = Number(e.target.value), max = p.hires ? 40 : 100;
    if (!Number.isFinite(n) || n < 1 || n > max) { notify(tr('Raio da cobertura: 1 a ', 'Coverage radius: 1 to ', 'Radio de la cobertura: 1 a ') + max + ' km.', true); e.target.value = p.max_km; return; }
    p.max_km = n;
  };
  $('#covPick').onclick = () => { tool.pickTx = true; $('#covPick').className = 'btn primary'; hintCoverage(); };
  $('#covCenter').onclick = () => { if (tool.tx) mapRef().setView(tool.tx, Math.max(mapRef().getZoom(), 12)); };
  $('#covSearchKm').onchange = e => {
    const n = Number(e.target.value);
    if (!Number.isFinite(n) || n < .05 || n > 50) { notify(tr('Buscar ponto mais alto: raio de 0,05 a 50 km.', 'Highest point search: radius 0.05 to 50 km.', 'Buscar punto más alto: radio de 0,05 a 50 km.'), true); e.target.value = tool.searchKm; return; }
    tool.searchKm = n;
  };
  $('#covHighest').onclick = coverageHighest;
  body.querySelectorAll('[data-cov-style]').forEach(b => b.onclick = () => {
    v.style = b.dataset.covStyle;
    body.querySelectorAll('[data-cov-style]').forEach(x => { const on = x.dataset.covStyle === v.style; x.className = 'btn ' + (on ? 'primary' : 'secondary'); x.setAttribute('aria-checked', String(on)); });
    drawCoverage();
  });
  body.querySelectorAll('[data-cov-display]').forEach(el => el.onchange = () => {
    const k = el.dataset.covDisplay; v[k] = k === 'scale' ? el.value : Number(el.value);
    if (v.min >= v.max) return notify(tr('O mínimo deve ser menor que o máximo.', 'The minimum must be lower than the maximum.', 'El mínimo debe ser menor que el máximo.'), true);
    $('#covBar').style.background = coverageGradient(v.scale); $('#covBarMin').textContent = v.min + ' dBm'; $('#covBarMax').textContent = v.max + ' dBm';
    drawCoverage();
  });
  $('#covRun').onclick = runCoverage;
  $('#covPdf').onclick = e => { if (tool?.result) savePdf(coveragePayload(true), 'PT2VHF_APRS_Cobertura_' + new Date().toISOString().slice(0, 10) + '.pdf', e.target); };
  $('#covClear').onclick = () => { clearCoverage(); tool.result = null; $('#covResult').innerHTML = ''; $('#covPdf').disabled = true; };
  hintCoverage(); if (t.result) showCoverage(t.result);
}
function coveragePayload(pdf = false) {
  // Os mesmos parâmetros no cálculo e no PDF: o servidor reaproveita a cobertura já calculada.
  const t = tool, params = {...t.params, station: t.station || '', name: t.station || tr('Transmissor', 'Transmitter', 'Transmisor')};
  return pdf ? {kind: 'coverage', center: t.tx, params, display: t.display, name: t.station || ''} : {center: t.tx, params};
}
function hintCoverage() {
  if (tool?.kind !== 'coverage' || !$('#planHint')) return;
  $('#planHint').textContent = tool.running ? tr('Calculando a cobertura… áreas novas baixam o relevo e podem levar alguns segundos.', 'Computing coverage… new areas download terrain and may take a few seconds.', 'Calculando la cobertura… las áreas nuevas descargan el relieve y pueden tardar unos segundos.')
    : tool.pickTx || !tool.tx ? tr('Clique no mapa para posicionar o transmissor (ou escolha uma estação conhecida).', 'Click the map to place the transmitter (or choose a known station).', 'Haz clic en el mapa para ubicar el transmisor (o elige una estación conocida).')
    : tr('Ajuste os parâmetros e clique em Calcular cobertura.', 'Adjust the parameters and click Compute coverage.', 'Ajusta los parámetros y haz clic en Calcular cobertura.');
}
function setCoverageTx(c, call = null) {
  const t = tool; if (t?.kind !== 'coverage') return;
  t.tx = c; t.station = call; t.pickTx = false;
  if (!t.marker) {
    t.marker = L.marker(c, {draggable: true, zIndexOffset: 1000, icon: L.divIcon({className: 'coverage-pin', html: '<span>📡</span>', iconSize: [34, 34], iconAnchor: [17, 32]})}).addTo(layer);
    t.marker.on('dragend', () => { const ll = t.marker.getLatLng(); setCoverageTx([ll.lat, ll.lng], null); });
  } else t.marker.setLatLng(c);
  t.marker.bindTooltip(esc(call || tr('Transmissor', 'Transmitter', 'Transmisor')), {direction: 'top', offset: [0, -30]});
  if ($('#covCoord')) { $('#covCoord').value = fmtCoord(...c); $('#covStation').value = call || ''; }
  if ($('#covPick')) $('#covPick').className = 'btn secondary';
  ['#covRun', '#covCenter', '#covHighest'].forEach(id => { if ($(id)) $(id).disabled = false; });
  hintCoverage();
}
async function coverageHighest() {
  const t = tool; if (!t?.tx) return;
  const btn = $('#covHighest'); btn.disabled = true;
  try {
    const r = (await api('/api/planning/highest', {center: t.tx, radius_km: t.searchKm})).data;
    setCoverageTx([r.lat, r.lon], null); mapRef().panTo(t.tx);
    notify(tr('Ponto mais alto em ', 'Highest point within ', 'Punto más alto en ') + num(r.searched_km) + ' km: ' + Math.round(r.ground_m) + ' m.');
  } catch (e) { notify(tr('Ponto mais alto: ', 'Highest point: ', 'Punto más alto: ') + e.message, true); }
  finally { btn.disabled = false; }
}
async function runCoverage() {
  const t = tool; if (!t?.tx || t.running) return;
  t.running = true; $('#covRun').disabled = true; hintCoverage();
  $('#covResult').innerHTML = '<p class="planning-small">' + esc(tr('Calculando…', 'Computing…', 'Calculando…')) + '</p>';
  try {
    const r = (await api('/api/planning/coverage', coveragePayload())).data;
    if (tool !== t) return;
    r.bytes = Uint8Array.from(atob(r.grid), ch => ch.charCodeAt(0));
    t.result = r; drawCoverage(); showCoverage(r);
    mapRef().fitBounds(L.latLngBounds(r.bounds).pad(.02));
    const sec = document.querySelectorAll('#planningBody .coverage-section'); sec.forEach((s, i) => { s.open = i === 4; });
  } catch (e) { $('#covResult').innerHTML = '<p class="planning-bad">' + esc(e.message) + '</p>'; }
  finally { t.running = false; if ($('#covRun')) $('#covRun').disabled = false; hintCoverage(); }
}
function clearCoverage() {
  const t = tool;
  if (t?.overlay) { layer.removeLayer(t.overlay); t.overlay = null; }
  if (t?.marks) { layer.removeLayer(t.marks); t.marks = null; }
  $('#coverageLegend')?.remove();
}
function drawCoverage() {
  const t = tool, r = t?.result; if (!r || !r.bytes) return;
  const v = t.display, n = r.size, canvas = document.createElement('canvas'); canvas.width = n; canvas.height = n;
  const ctx = canvas.getContext('2d'), img = ctx.createImageData(n, n), px = img.data, alpha = Math.round(255 * (1 - v.transparency / 100));
  const span = v.max - v.min, band = 10, contours = v.style === 'contours';
  const level = b => { if (!b) return null; const dbm = b - 200; return dbm < v.min ? null : dbm; };
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const i = y * n + x, dbm = level(r.bytes[i]); if (dbm == null) continue;
    let f = (dbm - v.min) / span, a = alpha;
    if (contours) {
      const k = Math.floor((dbm - v.min) / band); f = Math.min(1, (k * band + band / 2) / span);
      const right = x + 1 < n ? level(r.bytes[i + 1]) : null, down = y + 1 < n ? level(r.bytes[i + n]) : null;
      if (right == null || Math.floor((right - v.min) / band) !== k || down == null || Math.floor((down - v.min) / band) !== k) a = Math.min(255, alpha + 110);
    }
    const c = coverageColor(v.scale, f), o = i * 4; px[o] = c[0]; px[o + 1] = c[1]; px[o + 2] = c[2]; px[o + 3] = a;
  }
  ctx.putImageData(img, 0, 0);
  if (t.overlay) layer.removeLayer(t.overlay);
  t.overlay = L.imageOverlay(canvas.toDataURL('image/png'), r.bounds, {interactive: false, className: 'coverage-overlay'}).addTo(layer);
  let legend = $('#coverageLegend');
  if (!legend) { legend = document.createElement('div'); legend.id = 'coverageLegend'; ($('#map')?.parentElement || document.body).appendChild(legend); }
  legend.innerHTML = '<div class="coverage-legend-head"><b>' + esc(tr('SINAL', 'SIGNAL', 'SEÑAL')) + '</b><span>' + esc(contours ? tr('Contornos (10 dB)', 'Contours (10 dB)', 'Contornos (10 dB)') : tr('Mapa de calor', 'Heat map', 'Mapa de calor')) + '</span></div>' +
    '<div class="coverage-bar" style="background:' + coverageGradient(v.scale) + '"></div><div class="coverage-bar-labels"><span>' + v.min + ' dBm</span><span>' + v.max + ' dBm</span></div>';
}
function coverageAt(r, lat, lon) {
  const [[s, w], [nn, e]] = r.bounds; if (lat < s || lat > nn || lon < w || lon > e) return null;
  const x = Math.floor((lon - w) / (e - w) * r.size), y = Math.floor((nn - lat) / (nn - s) * r.size);
  const b = r.bytes[Math.min(r.size - 1, y) * r.size + Math.min(r.size - 1, x)]; return b ? b - 200 : null;
}
function distanceKm(a, b) {
  const rad = Math.PI / 180, dl = (b[0] - a[0]) * rad, dg = (b[1] - a[1]) * rad;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * rad) * Math.cos(b[0] * rad) * Math.sin(dg / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
// Estações com posição: com cobertura, sem cobertura (dentro do raio) e fora do raio calculado.
function classifyStations(r) {
  const p = r.params, c = [r.center.lat, r.center.lon], out = {covered: [], uncovered: [], outside: []}, me = String(tool.station || '').toUpperCase();
  for (const s of stations) {
    const call = String(s.callsign || '').toUpperCase(); if (!call || call === me) continue;
    const pos = [Number(s.latitude), Number(s.longitude)], km = distanceKm(c, pos), item = {call, pos, km, dbm: null};
    if (km > p.max_km) { out.outside.push(item); continue; }
    item.dbm = coverageAt(r, pos[0], pos[1]);
    (item.dbm != null && item.dbm >= p.rx_sensitivity_dbm ? out.covered : out.uncovered).push(item);
  }
  out.covered.sort((a, b) => b.dbm - a.dbm); out.uncovered.sort((a, b) => (b.dbm ?? -999) - (a.dbm ?? -999)); out.outside.sort((a, b) => a.km - b.km);
  return out;
}
function coverageLinkTo(item) {
  const t = tool, p = t.params;
  const back = {tx: t.tx, station: t.station, params: {...p}, display: {...t.display}, searchKm: t.searchKm, result: t.result};
  openLink({a: t.tx, b: item.pos, stationA: t.station, stationB: item.call, fromCoverage: back,
    params: {height_a: p.tx_height_m, height_b: p.rx_height_m, freq_mhz: p.freq_mhz, tx_power_w: p.tx_power_w,
      gain_a_dbi: p.tx_gain_dbi, gain_b_dbi: p.rx_gain_dbi, cable_a_db: 1, cable_b_db: p.rx_cable_db, sensitivity_dbm: p.rx_sensitivity_dbm}});
}
function drawStationMarks(groups, observed, cells) {
  const t = tool; if (t.marks) layer.removeLayer(t.marks);
  t.marks = L.layerGroup().addTo(layer);
  if (t.showCells) for (const c of cells?.items || []) {
    L.circleMarker([c.lat, c.lon], {radius: 4, weight: 1, color: '#fff', fillOpacity: .85, fillColor: c.agrees ? '#3ba6ff' : '#f39c12', interactive: true})
      .bindTooltip(tr('Atividade RF real', 'Real RF activity', 'Actividad RF real') + ': ' + c.count + ' · ' + tr('previsto', 'predicted', 'previsto') + ': ' +
        (c.predicted_dbm != null ? c.predicted_dbm + ' dBm' : tr('sem sinal', 'no signal', 'sin señal'))).addTo(t.marks);
  }
  for (const item of groups.uncovered) {
    L.circleMarker(item.pos, {radius: 13, color: '#ff4d4f', weight: 3, fill: false, className: 'coverage-miss'})
      .bindTooltip(esc(item.call) + ': ' + (item.dbm != null ? item.dbm + ' dBm' : tr('sem sinal', 'no signal', 'sin señal')) + ' · ' + tr('clique para analisar o enlace', 'click to analyze the link', 'clic para analizar el enlace'))
      .on('click', () => coverageLinkTo(item)).addTo(t.marks);
  }
  for (const o of observed?.items || []) {
    L.marker([o.lat, o.lon], {icon: L.divIcon({className: 'coverage-observed' + (o.agrees ? '' : ' disagree'), iconSize: [14, 14], iconAnchor: [7, 7]}), keyboard: false})
      .bindTooltip(esc(o.callsign) + ' ' + tr('ouviu por RF', 'heard over RF', 'escuchó por RF') + ' (' + o.packets + ' ' + tr('pacotes', 'packets', 'paquetes') + ') · ' +
        tr('previsto', 'predicted', 'previsto') + ': ' + (o.predicted_dbm != null ? o.predicted_dbm + ' dBm' : tr('sem sinal', 'no signal', 'sin señal'))).addTo(t.marks);
  }
}
function showCoverage(r) {
  const p = r.params, g = classifyStations(r), o = r.observed;
  const line = (x, extra) => '<li><button type="button" class="planning-link" data-cov-link="' + esc(x.call) + '">' + esc(x.call) + '</button>: ' + extra + '</li>';
  const list = (title, items, fmt, open, note = '') => items.length ? '<details' + (open ? ' open' : '') + '><summary>' + esc(title) + ' (' + items.length + ')</summary><ul class="planning-small">' +
    items.slice(0, 60).map(x => line(x, fmt(x))).join('') + '</ul>' + note + '</details>' : '';
  $('#covResult').innerHTML = '<h4>' + esc(tr('Resultado', 'Result', 'Resultado')) + '</h4><ul class="planning-small">' +
    '<li>' + esc(tr('Área com sinal acima de ', 'Area with signal above ', 'Área con señal por encima de ')) + p.rx_sensitivity_dbm + ' dBm (' + num(r.sensitivity_uv ?? uvFromDbm(p.rx_sensitivity_dbm), 2) + ' µV · ' + esc(r.sensitivity_s || sUnits(p.rx_sensitivity_dbm)) + '): <b>' + num(r.covered_km2) + ' km²</b></li>' +
    '<li>' + esc(tr('Ponto mais distante com sinal: ', 'Farthest point with signal: ', 'Punto más lejano con señal: ')) + '<b>' + num(r.farthest_km) + ' km</b> (' + esc(tr('raio', 'radius', 'radio')) + ' ' + num(p.max_km) + ' km)</li>' +
    '<li>' + esc(tr('Terreno no transmissor: ', 'Ground at the transmitter: ', 'Terreno en el transmisor: ')) + Math.round(r.center.ground_m) + ' m · ' + esc(tr('antena a ', 'antenna at ', 'antena a ')) + num(p.tx_height_m) + ' m · ' + num(p.tx_power_w) + ' W</li>' +
    '<li>' + esc(tr('Margem de confiabilidade: ', 'Reliability margin: ', 'Margen de confiabilidad: ')) + num(r.fade_margin_db) + ' dB · ' + esc(tr('relevo de ~', 'terrain ~', 'relieve de ~')) + Math.round(r.terrain_m) + ' m/pixel</li></ul>' +
    (o ? (o.total ? '<p class="planning-small coverage-observed-summary"><b>' + esc(tr('Previsto × real', 'Predicted × real', 'Previsto × real')) + ':</b> ' + o.agree + ' ' + esc(tr('de', 'of', 'de')) + ' ' + o.total + ' ' +
      esc(tr('estações que ouviram ', 'stations that heard ', 'estaciones que escucharon ')) + esc(o.station) + ' ' + esc(tr('por RF estão dentro da cobertura prevista', 'over RF are inside the predicted coverage', 'por RF están dentro de la cobertura prevista')) + ' (' + o.accuracy_pct + '%). ' +
      esc(tr('Quadrados azuis no mapa; laranja = ouviu, mas o modelo não previa.', 'Blue squares on the map; orange = heard, but not predicted.', 'Cuadrados azules en el mapa; naranja = escuchó, pero el modelo no lo preveía.')) + '</p>'
      : '<p class="planning-small">' + esc(tr('Ainda não há estações que ouviram ', 'No stations have heard ', 'Aún no hay estaciones que escucharon ')) + esc(o.station) + esc(tr(' diretamente por RF para comparar com a previsão.', ' directly over RF yet to compare with the prediction.', ' directamente por RF para comparar con la previsión.')) + '</p>')
      : '<p class="planning-small">' + esc(tr('Escolha uma estação conhecida como transmissor para comparar a previsão com as recepções reais por RF.', 'Pick a known station as transmitter to compare the prediction with real RF receptions.', 'Elige una estación conocida como transmisor para comparar la previsión con las recepciones reales por RF.')) + '</p>') +
    (r.observed_cells?.total ? '<p class="planning-small"><label><input type="checkbox" id="covCells"' + (tool.showCells ? ' checked' : '') + '> <b>' +
      esc(tr('Atividade RF real na área', 'Real RF activity in the area', 'Actividad RF real en el área')) + ':</b> ' + r.observed_cells.agree + ' ' + esc(tr('de', 'of', 'de')) + ' ' + r.observed_cells.total + ' ' +
      esc(tr('células do mapa de calor de Cobertura RF (~1 km, recepção direta) estão dentro da cobertura prevista', 'RF coverage heat-map cells (~1 km, direct reception) are inside the predicted coverage', 'celdas del mapa de calor de Cobertura RF (~1 km, recepción directa) están dentro de la cobertura prevista')) +
      ' (' + r.observed_cells.accuracy_pct + '%). ' + esc(tr('Mostrar no mapa.', 'Show on the map.', 'Mostrar en el mapa.')) + '</label></p>' : '') +
    (g.covered.length ? list(tr('Estações dentro da cobertura', 'Stations inside the coverage', 'Estaciones dentro de la cobertura'), g.covered, x => x.dbm + ' dBm · ' + num(uvFromDbm(x.dbm), 2) + ' µV · ' + sUnits(x.dbm), true)
      : '<p class="planning-small">' + esc(tr('Nenhuma estação conhecida com posição dentro da área coberta.', 'No known station with position inside the covered area.', 'Ninguna estación conocida con posición dentro del área cubierta.')) + '</p>') +
    list(tr('Estações sem cobertura', 'Stations without coverage', 'Estaciones sin cobertura'), g.uncovered,
      x => (x.dbm != null ? x.dbm + ' dBm · ' + tr('faltam ', 'missing ', 'faltan ') + num(p.rx_sensitivity_dbm - x.dbm) + ' dB' : tr('sem sinal', 'no signal', 'sin señal')) + ' · ' + num(x.km) + ' km', true,
      '<p class="planning-small">' + esc(tr('Contorno vermelho no mapa. Clique numa estação para abrir a análise de enlace.', 'Red outline on the map. Click a station to open the link analysis.', 'Contorno rojo en el mapa. Haz clic en una estación para abrir el análisis de enlace.')) + '</p>') +
    list(tr('Fora do raio calculado', 'Outside the computed radius', 'Fuera del radio calculado'), g.outside, x => num(x.km) + ' km', false) +
    '<p class="planning-small">' + esc(r.notes) + '</p>';
  const all = [...g.covered, ...g.uncovered, ...g.outside];
  $('#covResult').querySelectorAll('[data-cov-link]').forEach(b => b.onclick = () => { const it = all.find(x => x.call === b.dataset.covLink); if (it) coverageLinkTo(it); });
  const cells = r.observed_cells;
  if ($('#covCells')) $('#covCells').onchange = e => { tool.showCells = e.target.checked; drawStationMarks(g, o, cells); };
  drawStationMarks(g, o, cells);
  if ($('#covPdf')) $('#covPdf').disabled = false;
}
// --- melhor ponto avaliado pela cobertura ---------------------------------------------
async function surveyByCoverage(button) {
  const t = tool; if (t?.kind !== 'survey' || !t.result?.points?.length) return;
  const box = $('#svCoverage'), radius = Number($('#svCovRadius')?.value || 15);
  if (!(radius >= 1 && radius <= 30)) return notify(tr('Raio da avaliação: 1 a 30 km', 'Evaluation radius: 1 to 30 km', 'Radio de la evaluación: 1 a 30 km'), true);
  button.disabled = true;
  box.innerHTML = '<p class="planning-small">' + esc(tr('Calculando a cobertura dos 5 primeiros pontos…', 'Computing the coverage of the top 5 points…', 'Calculando la cobertura de los 5 primeros puntos…')) + '</p>';
  try {
    const r = (await api('/api/planning/best-coverage', {radius_km: radius, points: t.result.points.slice(0, 5).map(p => ({rank: p.rank, lat: p.lat, lon: p.lon})),
      params: {tx_power_w: 50, freq_mhz: defaults.freq_mhz, tx_height_m: 10, rx_sensitivity_dbm: defaults.sensitivity_dbm}})).data;
    if (tool !== t) return;
    box.innerHTML = '<table class="planning-table"><thead><tr><th>Nº</th><th>' + esc(tr('Área coberta', 'Covered area', 'Área cubierta')) + '</th><th>' + esc(tr('Estações alcançadas', 'Stations reached', 'Estaciones alcanzadas')) + '</th></tr></thead><tbody>' +
      r.items.map(x => '<tr' + (x.rank === r.best ? ' class="active"' : '') + '><td><b>' + x.rank + '</b>' + (x.rank === r.best ? ' ★' : '') + '</td><td>' + num(x.covered_km2) + ' km²</td><td title="' + esc(x.stations_names.join(', ')) + '">' + x.stations + '</td></tr>').join('') +
      '</tbody></table><p class="planning-small">' + esc(tr('★ = melhor ponto pela cobertura (mais estações, depois maior área), 50 W e antena a 10 m, raio de ', '★ = best point by coverage (most stations, then largest area), 50 W and antenna at 10 m, radius ', '★ = mejor punto por cobertura (más estaciones, luego mayor área), 50 W y antena a 10 m, radio de ')) + r.radius_km + ' km.</p>';
    highlight(r.best, true);
  } catch (e) { box.innerHTML = '<p class="planning-bad">' + esc(e.message) + '</p>'; }
  finally { button.disabled = false; }
}
// --- menu Ferramentas -------------------------------------------------------------
function showMap() {
  const tab = $('.tab[data-tab="map"]');
  if (tab && !tab.classList.contains('active')) tab.click();
  setTimeout(() => mapRef()?.invalidateSize?.(), 80);
}
function toggleToolsMenu(open) {
  const menu = $('#toolsMenu'), btn = $('#toolsMenuButton'); if (!menu || !btn) return;
  const show = open ?? menu.classList.contains('hidden');
  if (show) { const r = btn.getBoundingClientRect(); menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 300)) + 'px'; menu.style.top = (r.bottom + 2) + 'px'; }
  menu.classList.toggle('hidden', !show); btn.setAttribute('aria-expanded', String(show)); btn.classList.toggle('open', show);
}
function toolPdf() {
  const button = tool?.kind === 'coverage' ? $('#covPdf') : tool?.kind === 'link' ? $('#planPdf') : tool?.kind === 'survey' ? $('#svPdf') : null;
  if (!button || button.disabled) return notify(tr('Abra a análise de cobertura, de enlace ou o melhor ponto e calcule um resultado para gerar o relatório em PDF.', 'Open the coverage, link or best-point tool and compute a result to generate the PDF report.', 'Abre la cobertura, el enlace o el mejor punto y calcula un resultado para generar el informe PDF.'), true);
  button.click();
}
async function toolDiagnostics(button) {
  button.disabled = true;
  try {
    const res = await fetch('/api/diagnostics/log', {cache: 'no-store'}); if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text(), name = 'PT2VHF_APRS_Client_diagnostico_' + new Date().toISOString().slice(0, 10) + '.log';
    const nativeSave = window.pywebview?.api?.save_text_file;
    if (nativeSave) { const r = await nativeSave(name, text); if (r?.saved) notify(tr('Diagnóstico salvo: ', 'Diagnostics saved: ', 'Diagnóstico guardado: ') + r.path); else if (!r?.cancelled) throw new Error(r?.error || 'log'); }
    else { const url = URL.createObjectURL(new Blob([text], {type: 'text/plain;charset=utf-8'})), a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 5000);
      notify(tr('Diagnóstico baixado. Envie o arquivo junto com a descrição do problema.', 'Diagnostics downloaded. Send the file with the problem description.', 'Diagnóstico descargado. Envía el archivo con la descripción del problema.')); }
  } catch (e) { notify(tr('Diagnóstico: ', 'Diagnostics: ', 'Diagnóstico: ') + e.message, true); }
  finally { button.disabled = false; }
}
function translateToolsMenu() {
  const set = (sel, pt, en, es) => { const el = $(sel); if (el) el.textContent = tr(pt, en, es); };
  set('#toolsMenuButton', 'Ferramentas ▾', 'Tools ▾', 'Herramientas ▾');
  set('[data-tools-i18n="rf"]', 'Planejamento de RF', 'RF planning', 'Planificación de RF');
  set('[data-tools-i18n="terrain"]', 'Relevo', 'Terrain', 'Relieve');
  set('[data-tools-i18n="reports"]', 'Relatórios e suporte', 'Reports and support', 'Informes y soporte');
  set('#toolCoverage span', 'Análise de cobertura', 'Coverage analysis', 'Análisis de cobertura');
  set('#toolLink span', 'Analisar enlace entre 2 pontos', 'Analyze link between 2 points', 'Analizar enlace entre 2 puntos');
  set('#toolSurvey span', 'Melhor ponto para instalar estação', 'Best spot to install a station', 'Mejor punto para instalar una estación');
  set('#toolPdf span', 'Relatório (PDF)', 'Report (PDF)', 'Informe (PDF)');
  set('#toolDiagnostics span', 'Diagnóstico para suporte', 'Support diagnostics', 'Diagnóstico para soporte');
}
function mount() {
  if ($('#planningPanel')) return;
  const stage = $('#map')?.parentElement || document.body;
  const panel = document.createElement('aside');
  panel.id = 'planningPanel'; panel.hidden = true; panel.setAttribute('aria-label', tr('Ferramenta de planejamento', 'Planning tool', 'Herramienta de planificación'));
  panel.innerHTML = '<div class="planning-head"><b id="planningTitle"></b><button type="button" class="btn secondary" id="planningClose" title="Esc" aria-label="' + esc(tr('Fechar ferramenta', 'Close tool', 'Cerrar herramienta')) + '">✕</button></div><div id="planningBody"></div>';
  stage.appendChild(panel);
  $('#planningClose').onclick = closeTool;
  // v1.15.0: as ferramentas saíram do menu Itens do mapa para o menu Ferramentas do topo.
  const menu = $('#toolsMenu'), btn = $('#toolsMenuButton');
  if (!menu || !btn) return;
  translateToolsMenu();
  btn.addEventListener('click', e => { e.stopPropagation(); toggleToolsMenu(); });
  document.addEventListener('click', e => { if (!menu.classList.contains('hidden') && !e.target.closest('#toolsMenu,#toolsMenuButton')) toggleToolsMenu(false); });
  window.addEventListener('resize', () => toggleToolsMenu(false));
  $('#toolCoverage').onclick = () => openCoverage();
  $('#toolLink').onclick = () => openLink();
  $('#toolSurvey').onclick = () => openSurvey();
  $('#toolPdf').onclick = () => { toggleToolsMenu(false); toolPdf(); };
  $('#toolDiagnostics').onclick = e => { toggleToolsMenu(false); toolDiagnostics(e.currentTarget); };
  $('#elevationToggle')?.addEventListener('change', e => { if (e.target.checked) showMap(); });
  new MutationObserver(translateToolsMenu).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
}
document.addEventListener('keydown', e => {
  if (!tool || e.target.closest?.('input,select,textarea')) return;
  if (e.key === 'Escape') { if (tool.pickRef) { tool.pickRef = false; hintSurvey(); return; } if (tool.pickTx && tool.tx) { tool.pickTx = false; renderCoverage(); return; } e.preventDefault(); closeTool(); }
  else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && tool.kind === 'survey' && !tool.closed) { e.preventDefault(); undoVertex(); }
});
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
window.pt2vhfPlanning = {openLink, openSurvey, openCoverage, close: closeTool, state: () => tool,
  payload: () => (tool?.kind === 'link' ? linkPayload() : tool?.kind === 'coverage' ? coveragePayload(true) : surveyPayload())};
})();
