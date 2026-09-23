(() => {
  'use strict';

  const state = {
    activeTab: 'map',
    map: null,
    markers: new Map(),
    trackLines: new Map(),
    userLocationMarker: null,
    userLocationAccuracy: null,
    messages: [],
    stations: [],
    sort: {
      messages: { key: 'timestamp', dir: 'desc', type: 'text' },
      stations: { key: 'last_heard', dir: 'desc', type: 'text' }
    },
    connected: false,
    symbolTable: '/',
    configLoaded: false,
  };

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  }

  function fmtDate(value) {
    if (!value) return '';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit', second:'2-digit' });
  }

  function fmtNum(value, digits = 1, suffix = '') {
    if (value === null || value === undefined || value === '') return '';
    const n = Number(value);
    return Number.isFinite(n) ? `${n.toLocaleString('pt-BR', {maximumFractionDigits: digits})}${suffix}` : '';
  }

  async function api(url, options = {}) {
    const response = await fetch(url, options);
    let data = null;
    const ct = response.headers.get('content-type') || '';
    if (ct.includes('application/json')) data = await response.json();
    if (!response.ok) throw new Error(data?.error || `Erro HTTP ${response.status}`);
    return data;
  }

  let toastTimer = null;
  function toast(message, type = '') {
    const el = $('#toast');
    el.textContent = message;
    el.className = `toast ${type}`.trim();
    el.classList.remove('hidden');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.add('hidden'), 4200);
  }

  function debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  }

  const symbolRows = ['!"#$%&\'()*+,-./0', '123456789:;<=>?@', 'ABCDEFGHIJKLMNOP', 'QRSTUVWXYZ[\\]^_`', 'abcdefghijklmnop', 'qrstuvwxyz{|}~'];
  const spriteBase = 'https://raw.githubusercontent.com/OK-DMR/aprs-symbols/master/';

  function symbolAddress(symbol) {
    for (let row = 0; row < symbolRows.length; row++) {
      const col = symbolRows[row].indexOf(symbol);
      if (col >= 0) return { row, col };
    }
    return null;
  }

  function aprsSymbolHtml(table, symbol, size = 24) {
    const addr = symbolAddress(symbol || '>');
    if (!addr) return `<span class="aprs-fallback">${escapeHtml((table || '/') + (symbol || '?'))}</span>`;
    const isPrimary = table === '/';
    const baseTable = isPrimary ? 0 : 1;
    const overlay = (!isPrimary && table !== '\\') ? table : '';
    const scale = size / 24;
    const style = [
      `width:${size}px`, `height:${size}px`,
      `background-image:url('${spriteBase}aprs-symbols-24-${baseTable}.png')`,
      `background-size:${384 * scale}px ${144 * scale}px`,
      `background-position:${-addr.col * size}px ${-addr.row * size}px`
    ].join(';');
    return `<span class="aprs-symbol-stack" style="position:relative;display:inline-block;width:${size}px;height:${size}px">` +
      `<span class="aprs-symbol" style="${style}"></span>` +
      (overlay ? `<span style="position:absolute;inset:0;display:grid;place-items:center;font:bold ${Math.max(9, size*.42)}px sans-serif;color:#fff;text-shadow:0 1px 2px #000">${escapeHtml(overlay)}</span>` : '') +
      `</span>`;
  }

  function tabSetup() {
    $$('.tab').forEach(btn => btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      state.activeTab = tab;
      $$('.tab').forEach(b => b.classList.toggle('active', b === btn));
      $$('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${tab}`));
      if (tab === 'map') setTimeout(() => state.map?.invalidateSize(), 30);
      if (tab === 'messages') {
        markMessagesSeen();
        loadMessages();
      }
      if (tab === 'stations') loadStations();
      if (tab === 'config') loadConfig();
    }));
  }

  async function initMap() {
    if (typeof L === 'undefined') {
      $('#map').innerHTML = '<div style="padding:30px">Não foi possível carregar o Leaflet.</div>';
      return;
    }
    let saved = { latitude: -14.2350, longitude: -51.9253, zoom: 4 };
    try { saved = await api('/api/map-state'); } catch (_) {}
    state.map = L.map('map', { preferCanvas: true }).setView([saved.latitude, saved.longitude], saved.zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(state.map);
    addBrowserLocationControl(state.map);
    state.map.on('moveend', debounce(saveMapState, 400));
    await loadMapData();
  }

  function addBrowserLocationControl(map) {
    const LocationControl = L.Control.extend({
      options: { position: 'topleft' },
      onAdd() {
        const wrapper = L.DomUtil.create('div', 'leaflet-control leaflet-bar');
        const button = L.DomUtil.create('button', 'location-control', wrapper);
        button.type = 'button';
        button.title = 'Centralizar na minha localização';
        button.setAttribute('aria-label', 'Centralizar na minha localização');
        button.textContent = '◎';

        L.DomEvent.disableClickPropagation(wrapper);
        L.DomEvent.on(button, 'click', (event) => {
          L.DomEvent.stop(event);
          locateBrowser(button);
        });
        return wrapper;
      }
    });
    new LocationControl().addTo(map);
  }

  function locateBrowser(button) {
    if (!navigator.geolocation) {
      toast('Este navegador não oferece geolocalização.', 'error');
      return;
    }

    button.disabled = true;
    button.textContent = '…';

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const accuracy = Number(position.coords.accuracy) || 0;
        const point = [lat, lon];

        state.map.setView(point, Math.max(state.map.getZoom(), 15), { animate: true });

        if (state.userLocationMarker) state.userLocationMarker.setLatLng(point);
        else {
          state.userLocationMarker = L.marker(point, {
            icon: L.divIcon({
              className: '',
              html: '<div class="user-location-dot"></div>',
              iconSize: [18, 18],
              iconAnchor: [9, 9]
            }),
            title: 'Minha localização',
            zIndexOffset: 1000
          }).addTo(state.map).bindPopup('Minha localização');
        }

        if (accuracy > 0) {
          if (state.userLocationAccuracy) {
            state.userLocationAccuracy.setLatLng(point).setRadius(accuracy);
          } else {
            state.userLocationAccuracy = L.circle(point, {
              radius: accuracy,
              weight: 1,
              opacity: .75,
              fillOpacity: .08
            }).addTo(state.map);
          }
        }

        button.disabled = false;
        button.textContent = '◎';
        toast(accuracy > 0 ? `Localização obtida (precisão aproximada: ${Math.round(accuracy)} m).` : 'Localização obtida.', 'ok');
      },
      (error) => {
        const messages = {
          1: 'Permissão de localização negada pelo navegador.',
          2: 'Não foi possível determinar sua localização.',
          3: 'A localização demorou demais para responder.'
        };
        button.disabled = false;
        button.textContent = '◎';
        toast(messages[error.code] || 'Falha ao obter a localização do navegador.', 'error');
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  }

  async function saveMapState() {
    if (!state.map) return;
    const c = state.map.getCenter();
    try {
      await api('/api/map-state', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ latitude: c.lat, longitude: c.lng, zoom: state.map.getZoom() })
      });
    } catch (_) {}
  }

  function markerIcon(station) {
    return L.divIcon({
      className: 'aprs-marker-wrap',
      html: `<div class="aprs-marker">${aprsSymbolHtml(station.symbol_table || '/', station.symbol || '>', 24)}</div>`,
      iconSize: [34, 34], iconAnchor: [17, 17], popupAnchor: [0, -18]
    });
  }

  function popupHtml(s) {
    let path = '';
    try { path = JSON.parse(s.path || '[]').join(','); } catch (_) { path = s.path || ''; }
    return `<div class="station-popup">
      <h3>${aprsSymbolHtml(s.symbol_table || '/', s.symbol || '>', 24)} ${escapeHtml(s.name || s.callsign)}</h3>
      <div class="popup-grid">
        <strong>Indicativo</strong><span>${escapeHtml(s.callsign)}</span>
        <strong>Última recepção</strong><span>${escapeHtml(fmtDate(s.last_heard))}</span>
        <strong>Posição</strong><span>${fmtNum(s.latitude, 6)}, ${fmtNum(s.longitude, 6)}</span>
        <strong>Velocidade</strong><span>${fmtNum(s.speed, 1, ' km/h')}</span>
        <strong>Curso</strong><span>${fmtNum(s.course, 0, '°')}</span>
        <strong>Altitude</strong><span>${fmtNum(s.altitude, 1, ' m')}</span>
        <strong>Informação</strong><span>${escapeHtml(s.info || '')}</span>
        <strong>Via</strong><span>${escapeHtml(path)}</span>
      </div>
    </div>`;
  }

  function trackColor(callsign) {
    let h = 0;
    for (const ch of callsign) h = (h * 31 + ch.charCodeAt(0)) % 360;
    return `hsl(${h} 78% 56%)`;
  }

  async function loadMapData() {
    if (!state.map) return;
    try {
      const data = await api('/api/map-data');
      $('#mapStationCount').textContent = data.stations.length;
      $('#mapLastUpdate').textContent = new Date().toLocaleTimeString('pt-BR');

      for (const s of data.stations) {
        const latlng = [Number(s.latitude), Number(s.longitude)];
        if (!Number.isFinite(latlng[0]) || !Number.isFinite(latlng[1])) continue;
        let marker = state.markers.get(s.callsign);
        if (!marker) {
          marker = L.marker(latlng, { icon: markerIcon(s), title: s.callsign }).addTo(state.map);
          state.markers.set(s.callsign, marker);
        } else {
          marker.setLatLng(latlng).setIcon(markerIcon(s));
        }
        marker.bindPopup(popupHtml(s), { maxWidth: 420 });
      }

      const grouped = new Map();
      for (const t of data.tracks) {
        if (!grouped.has(t.callsign)) grouped.set(t.callsign, []);
        grouped.get(t.callsign).push([Number(t.latitude), Number(t.longitude)]);
      }
      for (const [call, points] of grouped) {
        if (points.length < 2) continue;
        let line = state.trackLines.get(call);
        if (!line) {
          line = L.polyline(points, { color: trackColor(call), weight: 2, opacity: .72 }).addTo(state.map);
          state.trackLines.set(call, line);
        } else {
          line.setLatLngs(points);
        }
      }
    } catch (err) {
      console.warn(err);
    }
  }

  async function refreshStatus() {
    try {
      const s = await api('/api/status');
      state.connected = !!s.connected;
      const el = $('#connectionStatus');
      el.classList.remove('connected', 'unverified', 'disconnected');
      if (s.connected && s.verified) el.classList.add('connected');
      else if (s.connected) el.classList.add('unverified');
      else el.classList.add('disconnected');
      el.querySelector('span:last-child').textContent = s.state || (s.connected ? 'Conectado' : 'Desconectado');
      el.title = s.last_error || s.server_message || '';
      $('#connectButton').textContent = s.connected || s.wanted ? 'Desconectar' : 'Conectar';
    } catch (_) {}
  }

  $('#connectButton').addEventListener('click', async () => {
    try {
      if (state.connected || $('#connectButton').textContent === 'Desconectar') {
        await api('/api/disconnect', { method: 'POST' });
      } else {
        await api('/api/connect', { method: 'POST' });
      }
      await refreshStatus();
    } catch (err) { toast(err.message, 'error'); }
  });

  function setupSortableTable(tableId, datasetName, renderFn) {
    const table = document.getElementById(tableId);
    table.querySelectorAll('th[data-key]').forEach(th => th.addEventListener('click', () => {
      const current = state.sort[datasetName];
      const key = th.dataset.key;
      const type = th.dataset.type || 'text';
      state.sort[datasetName] = {
        key,
        type,
        dir: current.key === key && current.dir === 'asc' ? 'desc' : 'asc'
      };
      renderFn();
    }));
  }

  function sortedData(items, spec) {
    const factor = spec.dir === 'asc' ? 1 : -1;
    return [...items].sort((a, b) => {
      let av = a[spec.key], bv = b[spec.key];
      const aEmpty = av === null || av === undefined || av === '';
      const bEmpty = bv === null || bv === undefined || bv === '';
      if (aEmpty && bEmpty) return 0;
      if (aEmpty) return 1;
      if (bEmpty) return -1;
      if (spec.type === 'number') return (Number(av) - Number(bv)) * factor;
      return String(av).localeCompare(String(bv), 'pt-BR', { numeric: true, sensitivity: 'base' }) * factor;
    });
  }

  function updateSortIndicators(tableId, spec) {
    const table = document.getElementById(tableId);
    table.querySelectorAll('th[data-key]').forEach(th => {
      th.querySelector('.sort-indicator').textContent = th.dataset.key === spec.key ? (spec.dir === 'asc' ? '▲' : '▼') : '';
    });
  }

  async function loadMessages() {
    try {
      const filter = $('#messageFilter').value.trim();
      state.messages = await api(`/api/messages?from=${encodeURIComponent(filter)}`);
      renderMessages();
      updateUnread();
    } catch (err) { console.warn(err); }
  }

  function renderMessages() {
    const spec = state.sort.messages;
    const rows = sortedData(state.messages, spec);
    $('#messagesTable tbody').innerHTML = rows.map(m => `
      <tr>
        <td class="${m.direction === 'in' ? 'direction-in' : 'direction-out'}">${escapeHtml(m.from_call)}</td>
        <td>${escapeHtml(m.to_call)}</td>
        <td>${escapeHtml(m.message)}</td>
        <td>${escapeHtml(fmtDate(m.timestamp))}</td>
        <td class="${m.status === 'ACK' ? 'status-ack' : m.status === 'REJ' ? 'status-rej' : ''}">${escapeHtml(m.status || '')}</td>
      </tr>`).join('');
    updateSortIndicators('messagesTable', spec);
  }

  const loadMessagesDebounced = debounce(loadMessages, 250);
  $('#messageFilter').addEventListener('input', loadMessagesDebounced);

  $('#messageTo').addEventListener('input', debounce(async (ev) => {
    try {
      const list = await api(`/api/callsigns?prefix=${encodeURIComponent(ev.target.value)}`);
      $('#destinationList').innerHTML = list.map(c => `<option value="${escapeHtml(c)}"></option>`).join('');
    } catch (_) {}
  }, 180));

  async function sendMessage() {
    const to = $('#messageTo').value.trim().toUpperCase();
    const message = $('#messageText').value.trim();
    if (!to || !message) return toast('Informe destino e mensagem.', 'error');
    try {
      await api('/api/messages/send', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({to, message})
      });
      $('#messageText').value = '';
      toast('Mensagem enviada ao APRS-IS.', 'ok');
      await loadMessages();
    } catch (err) { toast(err.message, 'error'); }
  }

  $('#sendMessageButton').addEventListener('click', sendMessage);
  $('#messageText').addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });

  function updateUnread() {
    const incoming = state.messages.filter(m => m.direction === 'in');
    const latest = incoming.reduce((max, m) => Math.max(max, Number(m.id) || 0), 0);
    const seen = Number(localStorage.getItem('pt2vhf_last_seen_msg') || 0);
    const unread = incoming.filter(m => Number(m.id) > seen).length;
    const badge = $('#messageBadge');
    badge.textContent = unread;
    badge.classList.toggle('hidden', unread <= 0 || state.activeTab === 'messages');
    if (state.activeTab === 'messages' && latest) {
      localStorage.setItem('pt2vhf_last_seen_msg', String(latest));
    }
  }

  function markMessagesSeen() {
    const latest = state.messages.filter(m => m.direction === 'in').reduce((max, m) => Math.max(max, Number(m.id) || 0), 0);
    if (latest) localStorage.setItem('pt2vhf_last_seen_msg', String(latest));
    $('#messageBadge').classList.add('hidden');
  }

  async function loadStations() {
    try {
      const filter = $('#stationFilter').value.trim();
      state.stations = await api(`/api/stations?filter=${encodeURIComponent(filter)}`);
      renderStations();
    } catch (err) { console.warn(err); }
  }

  function renderStations() {
    const spec = state.sort.stations;
    const rows = sortedData(state.stations, spec);
    $('#stationsTable tbody').innerHTML = rows.map(s => `
      <tr>
        <td>${aprsSymbolHtml(s.symbol_table || '/', s.symbol || '>', 24)} ${escapeHtml(s.name || s.callsign)}</td>
        <td>${escapeHtml(s.callsign)}</td>
        <td>${escapeHtml(fmtDate(s.last_heard))}</td>
        <td>${fmtNum(s.distance_km, 1, ' km')}</td>
        <td>${fmtNum(s.speed, 1, ' km/h')}</td>
        <td>${fmtNum(s.course, 0, '°')}</td>
        <td>${fmtNum(s.altitude, 1, ' m')}</td>
        <td>${escapeHtml(s.info || '')}</td>
      </tr>`).join('');
    updateSortIndicators('stationsTable', spec);
  }

  $('#stationFilter').addEventListener('input', debounce(loadStations, 250));

  async function loadConfig() {
    try {
      const cfg = await api('/api/config');
      const form = $('#configForm');
      for (const [key, value] of Object.entries(cfg)) {
        const input = form.elements.namedItem(key);
        if (!input) continue;
        if (input.type === 'checkbox') input.checked = !!value;
        else input.value = value ?? '';
      }
      updateSelectedSymbol();
      state.configLoaded = true;
    } catch (err) { toast(err.message, 'error'); }
  }

  $('#configForm').addEventListener('submit', async e => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    data.connect_on_start = form.elements.connect_on_start.checked;
    try {
      await api('/api/config', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data)
      });
      toast('Configuração salva no banco local.', 'ok');
      await loadConfig();
      await loadStations();
    } catch (err) { toast(err.message, 'error'); }
  });

  $('#configImportFile').addEventListener('change', async e => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      await api('/api/config/import', { method: 'POST', body: fd });
      toast('Configuração recuperada do arquivo.', 'ok');
      await loadConfig();
    } catch (err) { toast(err.message, 'error'); }
    e.target.value = '';
  });

  $('#sendBeaconButton').addEventListener('click', async () => {
    try {
      await api('/api/beacon', { method: 'POST' });
      toast('Beacon transmitido.', 'ok');
      await loadMapData();
    } catch (err) { toast(err.message, 'error'); }
  });

  function updateSelectedSymbol() {
    const form = $('#configForm');
    const table = form.elements.symbol_table.value || '/';
    const symbol = form.elements.symbol.value || '>';
    $('#selectedSymbolPreview').innerHTML = `${aprsSymbolHtml(table, symbol, 48)} <span><strong>${escapeHtml(table + symbol)}</strong><br><small>Tabela ${table === '/' ? 'primária' : 'secundária'}</small></span>`;
  }

  function renderSymbolGrid(table) {
    const symbols = symbolRows.join('');
    $('#symbolGrid').innerHTML = [...symbols].map(sym => `
      <button type="button" class="symbol-choice" data-symbol="${escapeHtml(sym)}">
        ${aprsSymbolHtml(table, sym, 24)}<span class="symbol-code">${escapeHtml(table + sym)}</span>
      </button>`).join('');
    $$('#symbolGrid .symbol-choice').forEach(btn => btn.addEventListener('click', () => {
      const form = $('#configForm');
      form.elements.symbol_table.value = table;
      form.elements.symbol.value = btn.dataset.symbol;
      updateSelectedSymbol();
      $('#symbolModal').classList.add('hidden');
    }));
  }

  $('#chooseSymbolButton').addEventListener('click', () => {
    const form = $('#configForm');
    state.symbolTable = form.elements.symbol_table.value === '\\' ? '\\' : '/';
    $$('.symbol-tab').forEach(b => b.classList.toggle('active', b.dataset.symbolTable === state.symbolTable));
    renderSymbolGrid(state.symbolTable);
    $('#symbolModal').classList.remove('hidden');
  });
  $('#closeSymbolModal').addEventListener('click', () => $('#symbolModal').classList.add('hidden'));
  $('#symbolModal').addEventListener('click', e => { if (e.target.id === 'symbolModal') e.currentTarget.classList.add('hidden'); });
  $$('.symbol-tab').forEach(btn => btn.addEventListener('click', () => {
    state.symbolTable = btn.dataset.symbolTable;
    $$('.symbol-tab').forEach(b => b.classList.toggle('active', b === btn));
    renderSymbolGrid(state.symbolTable);
  }));

  setupSortableTable('messagesTable', 'messages', renderMessages);
  setupSortableTable('stationsTable', 'stations', renderStations);
  tabSetup();

  async function boot() {
    await Promise.all([initMap(), loadMessages(), loadStations(), loadConfig(), refreshStatus()]);
    setInterval(refreshStatus, 2000);
    setInterval(loadMapData, 5000);
    setInterval(loadMessages, 3000);
    setInterval(() => { if (state.activeTab === 'stations') loadStations(); }, 5000);
  }

  boot();
})();
