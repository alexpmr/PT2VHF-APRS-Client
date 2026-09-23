(() => {
  'use strict';

  const state = {
    activeTab: 'map',
    map: null,
    baseLayer: null,
    mapConfig: { map_type: 'osm', track_color: '#3ba6ff', track_width: 2 },
    markers: new Map(),
    trackLines: new Map(),
    userLocationMarker: null,
    userLocationAccuracy: null,
    messages: [],
    stations: [],
    logs: [],
    sort: {
      messages: { key: 'timestamp', dir: 'desc', type: 'text' },
      stations: { key: 'last_heard', dir: 'desc', type: 'text' }
    },
    connected: false,
    symbolTable: '/',
    configLoaded: false,
    myMessagesOnly: false,
    ownCallsign: '',
    messageAlertBaselineReady: false,
    lastAlertedMessageId: 0,
    currentAlertMessage: null,
    soundOnPersonalMessage: true,
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

  async function refreshVersionStatus(force = false) {
    const el = $('#versionStatus');
    const textEl = $('#versionStatusText');
    if (!el || !textEl) return;

    el.classList.remove('latest', 'update', 'error', 'ahead');
    el.classList.add('checking');
    textEl.textContent = 'Verificando versão…';
    el.removeAttribute('href');

    try {
      const data = await api(`/api/update-status${force ? '?force=1' : ''}`);
      el.classList.remove('checking');

      const current = data.current_version ? `v${data.current_version}` : 'versão atual';
      const latest = data.latest_version ? `v${data.latest_version}` : '';

      if (data.status === 'update_available') {
        el.classList.add('update');
        textEl.textContent = `Nova versão ${latest}`;
        el.title = `Instalada ${current}. Clique para abrir a nova release.`;
        if (data.release_url) el.href = data.release_url;
      } else if (data.status === 'latest') {
        el.classList.add('latest');
        textEl.textContent = 'Última versão';
        el.title = `${current} é a versão mais recente publicada.`;
      } else if (data.status === 'ahead') {
        el.classList.add('ahead');
        textEl.textContent = `Build ${current}`;
        el.title = latest ? `Este build é mais novo que a release publicada ${latest}.` : 'Build de desenvolvimento.';
      } else {
        el.classList.add('error');
        textEl.textContent = 'Versão não verificada';
        el.title = 'Não foi possível consultar a release mais recente no GitHub.';
      }
    } catch (_) {
      el.classList.remove('checking');
      el.classList.add('error');
      textEl.textContent = 'Versão não verificada';
      el.title = 'Não foi possível consultar a release mais recente no GitHub.';
    }
  }

  $('#versionStatus')?.addEventListener('click', e => {
    const el = e.currentTarget;
    if (!el.getAttribute('href')) {
      e.preventDefault();
      refreshVersionStatus(true);
    }
  });

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
      if (tab === 'log') {
        loadLog(true);
      }
      if (tab === 'config') loadConfig();
    }));
  }

  const MAP_PROVIDERS = {
    osm: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      options: { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }
    },
    topo: {
      url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
      options: { maxZoom: 17, attribution: 'Map data &copy; OpenStreetMap contributors | Map style &copy; OpenTopoMap (CC-BY-SA)' }
    },
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      options: { maxZoom: 19, attribution: 'Tiles &copy; Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community' }
    }
  };

  const FONT_FAMILIES = {
    system: 'Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
    segoe: '"Segoe UI", Arial, sans-serif',
    arial: 'Arial, sans-serif',
    verdana: 'Verdana, sans-serif',
    tahoma: 'Tahoma, sans-serif',
    consolas: 'Consolas, "Courier New", monospace'
  };

  function applyAppearancePreferences(cfg = {}) {
    const root = document.documentElement;
    const messagesFamily = FONT_FAMILIES[cfg.messages_font_family] || FONT_FAMILIES.system;
    const stationsFamily = FONT_FAMILIES[cfg.stations_font_family] || FONT_FAMILIES.system;
    const messagesSize = Math.min(20, Math.max(10, Number(cfg.messages_font_size || 12)));
    const stationsSize = Math.min(20, Math.max(10, Number(cfg.stations_font_size || 12)));

    root.style.setProperty('--messages-font-family', messagesFamily);
    root.style.setProperty('--messages-font-size', `${messagesSize}px`);
    root.style.setProperty('--stations-font-family', stationsFamily);
    root.style.setProperty('--stations-font-size', `${stationsSize}px`);
  }

  function applyMapPreferences(cfg = {}) {
    state.mapConfig = {
      map_type: cfg.map_type || state.mapConfig.map_type || 'osm',
      track_color: cfg.track_color || state.mapConfig.track_color || '#3ba6ff',
      track_width: Number(cfg.track_width || state.mapConfig.track_width || 2),
      map_brightness: Number(cfg.map_brightness || state.mapConfig.map_brightness || 100)
    };

    if (state.map) {
      const provider = MAP_PROVIDERS[state.mapConfig.map_type] || MAP_PROVIDERS.osm;
      if (state.baseLayer) state.map.removeLayer(state.baseLayer);
      state.baseLayer = L.tileLayer(provider.url, provider.options).addTo(state.map);
      state.baseLayer.bringToBack();

      const tilePane = state.map.getPane('tilePane');
      if (tilePane) tilePane.style.filter = `brightness(${state.mapConfig.map_brightness}%)`;

      for (const line of state.trackLines.values()) {
        line.setStyle({
          color: state.mapConfig.track_color,
          weight: state.mapConfig.track_width,
          opacity: .78
        });
      }
    }
  }

  async function initMap() {
    if (typeof L === 'undefined') {
      $('#map').innerHTML = '<div style="padding:30px">Não foi possível carregar o Leaflet.</div>';
      return;
    }
    let saved = { latitude: -14.2350, longitude: -51.9253, zoom: 4 };
    let cfg = {};
    try {
      [saved, cfg] = await Promise.all([api('/api/map-state'), api('/api/config')]);
    } catch (_) {}
    state.map = L.map('map', { preferCanvas: true }).setView([saved.latitude, saved.longitude], saved.zoom);
    applyMapPreferences(cfg);
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
      <div class="station-popup-actions">
        <button type="button" class="btn primary station-message-button" data-callsign="${escapeHtml(s.callsign)}">Enviar mensagem</button>
      </div>
    </div>`;
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
          line = L.polyline(points, {
            color: state.mapConfig.track_color,
            weight: state.mapConfig.track_width,
            opacity: .78
          }).addTo(state.map);
          state.trackLines.set(call, line);
        } else {
          line.setLatLngs(points);
          line.setStyle({
            color: state.mapConfig.track_color,
            weight: state.mapConfig.track_width,
            opacity: .78
          });
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
      const packetCount = $('#packetCount');
      const activeFilter = $('#activeFilter');
      if (packetCount) packetCount.textContent = Number(s.packets_received || 0).toLocaleString('pt-BR');
      if (activeFilter) {
        activeFilter.textContent = s.active_filter || 'sem filtro';
        activeFilter.classList.toggle('warning-text', !s.active_filter);
      }
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
      const mine = state.myMessagesOnly ? '&mine=1' : '';
      state.messages = await api(`/api/messages?from=${encodeURIComponent(filter)}${mine}`);
      renderMessages();
      updateUnread();
    } catch (err) { console.warn(err); }
  }

  function messageTypeLabel(type) {
    if (type === 'bulletin') return '<span class="message-type-badge bulletin">Boletim</span>';
    if (type === 'group_bulletin') return '<span class="message-type-badge group-bulletin">Grupo</span>';
    return '<span class="message-type-badge message">Mensagem</span>';
  }

  function renderMessages() {
    const spec = state.sort.messages;
    const rows = sortedData(state.messages, spec);
    $('#messagesTable tbody').innerHTML = rows.map(m => `
      <tr>
        <td class="${m.direction === 'in' ? 'direction-in' : 'direction-out'}">${escapeHtml(m.from_call)}</td>
        <td>${escapeHtml(m.to_call)}</td>
        <td>${messageTypeLabel(m.message_type)}</td>
        <td>${escapeHtml(m.message)}</td>
        <td>${escapeHtml(fmtDate(m.timestamp))}</td>
        <td class="${m.status === 'ACK' ? 'status-ack' : m.status === 'REJ' ? 'status-rej' : ''}">${escapeHtml(m.status || '')}</td>
      </tr>`).join('');
    updateSortIndicators('messagesTable', spec);
  }

  const loadMessagesDebounced = debounce(loadMessages, 250);
  $('#messageFilter').addEventListener('input', loadMessagesDebounced);

  function updateMyMessagesButton() {
    const btn = $('#myMessagesButton');
    const filter = $('#messageFilter');
    if (!btn) return;
    btn.classList.toggle('active-filter', state.myMessagesOnly);
    btn.setAttribute('aria-pressed', state.myMessagesOnly ? 'true' : 'false');
    btn.textContent = state.myMessagesOnly ? '✓ Minhas mensagens' : 'Minhas mensagens';
    if (filter) {
      filter.disabled = state.myMessagesOnly;
      if (state.myMessagesOnly) filter.value = '';
    }
  }

  $('#myMessagesButton')?.addEventListener('click', async () => {
    state.myMessagesOnly = !state.myMessagesOnly;
    updateMyMessagesButton();
    await loadMessages();
  });

  $('#messageTo').addEventListener('input', debounce(async (ev) => {
    try {
      const list = await api(`/api/callsigns?prefix=${encodeURIComponent(ev.target.value)}`);
      $('#destinationList').innerHTML = list.map(c => `<option value="${escapeHtml(c)}"></option>`).join('');
    } catch (_) {}
  }, 180));

  function openMessageComposer(destination = '') {
    $('.tab[data-tab="messages"]')?.click();
    $('#messageType').value = 'message';
    updateMessageComposerMode();
    $('#messageTo').value = String(destination || '').toUpperCase().trim();
    $('#messageText').focus();
  }

  document.addEventListener('click', e => {
    const button = e.target.closest('.station-message-button');
    if (!button) return;
    e.preventDefault();
    e.stopPropagation();
    openMessageComposer(button.dataset.callsign || '');
  });

  function updateMessageComposerMode() {
    const type = $('#messageType').value;
    const isMessage = type === 'message';
    const isGroup = type === 'group_bulletin';

    $('#messageDestinationField').classList.toggle('hidden', !isMessage);
    $('#bulletinIdField').classList.toggle('hidden', isMessage);
    $('#bulletinGroupField').classList.toggle('hidden', !isGroup);

    const messageInput = $('#messageText');
    messageInput.maxLength = isMessage ? 63 : 67;
    messageInput.placeholder = isMessage ? 'Digite a mensagem APRS' : 'Digite o texto do boletim APRS';
    $('#sendMessageButton').textContent = isMessage ? 'Enviar' : 'Enviar boletim';
  }

  async function sendMessage() {
    const type = $('#messageType').value;
    const to = $('#messageTo').value.trim().toUpperCase();
    const message = $('#messageText').value.trim();
    const bulletinId = $('#bulletinId').value;
    const group = $('#bulletinGroup').value.trim().toUpperCase();

    if (!message) return toast('Informe a mensagem.', 'error');
    if (type === 'message' && !to) return toast('Informe o indicativo de destino.', 'error');
    if (type === 'group_bulletin' && !group) return toast('Informe o grupo do boletim.', 'error');

    const payload = { type, to, message, bulletin_id: bulletinId, group };

    try {
      const result = await api('/api/messages/send', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)
      });
      $('#messageText').value = '';
      toast(result.type === 'message' ? 'Mensagem enviada ao APRS-IS.' : 'Boletim enviado ao APRS-IS sem solicitação de ACK.', 'ok');
      await loadMessages();
    } catch (err) { toast(err.message, 'error'); }
  }

  $('#messageType').addEventListener('change', updateMessageComposerMode);
  $('#bulletinGroup').addEventListener('input', e => { e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 5); });
  $('#sendMessageButton').addEventListener('click', sendMessage);
  $('#messageText').addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
  updateMessageComposerMode();

  function closeIncomingMessageAlert() {
    $('#incomingMessageModal')?.classList.add('hidden');
    state.currentAlertMessage = null;
  }

  function showIncomingMessageAlert(message) {
    state.currentAlertMessage = message;
    $('#incomingMessageFrom').textContent = message.from_call || '';
    $('#incomingMessageTime').textContent = fmtDate(message.timestamp);
    $('#incomingMessageText').textContent = message.message || '';
    $('#incomingMessageModal')?.classList.remove('hidden');
  }

  async function checkIncomingPersonalMessages() {
    try {
      if (!state.ownCallsign) return;
      const messages = await api('/api/messages?mine=1');
      const incoming = messages
        .filter(m => m.direction === 'in' && m.message_type === 'message' && String(m.to_call || '').toUpperCase() === state.ownCallsign)
        .sort((a, b) => Number(a.id) - Number(b.id));

      const latest = incoming.reduce((max, m) => Math.max(max, Number(m.id) || 0), 0);
      if (!state.messageAlertBaselineReady) {
        state.lastAlertedMessageId = latest;
        state.messageAlertBaselineReady = true;
        return;
      }

      if (!$('#incomingMessageModal')?.classList.contains('hidden')) return;
      const next = incoming.find(m => Number(m.id) > state.lastAlertedMessageId);
      if (next) {
        state.lastAlertedMessageId = Number(next.id) || state.lastAlertedMessageId;
        showIncomingMessageAlert(next);
      }
    } catch (err) {
      console.warn(err);
    }
  }

  $('#incomingMessageClose')?.addEventListener('click', closeIncomingMessageAlert);
  $('#incomingMessageModal')?.addEventListener('click', e => {
    if (e.target.id === 'incomingMessageModal') closeIncomingMessageAlert();
  });
  $('#incomingMessageReply')?.addEventListener('click', () => {
    const message = state.currentAlertMessage;
    if (!message) return;
    closeIncomingMessageAlert();
    openMessageComposer(message.from_call || '');
  });

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

  async function loadLog(forceScroll = false) {
    try {
      const filter = $('#logFilter')?.value.trim() || '';
      const direction = $('#logDirection')?.value || 'ALL';
      const limit = $('#logLimit')?.value || '1000';
      state.logs = await api(`/api/log?filter=${encodeURIComponent(filter)}&direction=${encodeURIComponent(direction)}&limit=${encodeURIComponent(limit)}`);
      renderLog(forceScroll);
    } catch (err) {
      console.warn(err);
    }
  }

  function renderLog(forceScroll = false) {
    const tbody = $('#logTable tbody');
    const viewport = $('#logViewport');
    if (!tbody || !viewport) return;

    const auto = $('#logAutoScroll')?.checked ?? true;
    const wasNearBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight < 60;

    if (!state.logs.length) {
      tbody.innerHTML = '<tr class="log-empty"><td colspan="3">Nenhum tráfego APRS-IS registrado para este filtro.</td></tr>';
      return;
    }

    tbody.innerHTML = state.logs.map(row => {
      const direction = row.direction === 'TX' ? 'TX' : 'RX';
      return `<tr class="log-${direction.toLowerCase()}">
        <td>${escapeHtml(fmtDate(row.timestamp))}</td>
        <td class="log-direction">${direction}</td>
        <td class="log-raw">${escapeHtml(row.raw || '')}</td>
      </tr>`;
    }).join('');

    if (auto && (forceScroll || wasNearBottom)) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }

  const loadLogDebounced = debounce(() => loadLog(true), 220);
  $('#logFilter')?.addEventListener('input', loadLogDebounced);
  $('#logDirection')?.addEventListener('change', () => loadLog(true));
  $('#logLimit')?.addEventListener('change', () => loadLog(true));
  $('#logAutoScroll')?.addEventListener('change', () => {
    if ($('#logAutoScroll').checked) {
      const viewport = $('#logViewport');
      viewport.scrollTop = viewport.scrollHeight;
    }
  });

  $('#clearLogButton')?.addEventListener('click', async () => {
    if (!window.confirm('Limpar todo o histórico do Log APRS-IS?')) return;
    try {
      await api('/api/log/clear', { method: 'POST' });
      state.logs = [];
      renderLog(true);
      toast('Log APRS-IS limpo.', 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
  });

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
      <tr class="station-row" data-callsign="${escapeHtml(s.callsign)}" tabindex="0" title="Abrir esta estação no mapa">
        <td>${aprsSymbolHtml(s.symbol_table || '/', s.symbol || '>', 24)} ${escapeHtml(s.callsign)}</td>
        <td class="station-last-heard">${escapeHtml(fmtDate(s.last_heard))}</td>
        <td>${fmtNum(s.distance_km, 1, ' km')}</td>
        <td>${fmtNum(s.speed, 1, ' km/h')}</td>
        <td>${fmtNum(s.course, 0, '°')}</td>
        <td>${fmtNum(s.altitude, 1, ' m')}</td>
        <td>${escapeHtml(s.info || '')}</td>
      </tr>`).join('');

    $('#stationsTable tbody .station-row').forEach(row => {
      const open = () => focusStationOnMap(row.dataset.callsign);
      row.addEventListener('click', open);
      row.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          open();
        }
      });
    });

    updateSortIndicators('stationsTable', spec);
  }

  async function focusStationOnMap(callsign) {
    const station = state.stations.find(s => s.callsign === callsign);
    if (!station) return;

    const lat = Number(station.latitude);
    const lon = Number(station.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      toast(`${callsign} ainda não informou uma posição válida.`, 'error');
      return;
    }

    const mapTab = $('.tab[data-tab="map"]');
    if (mapTab) mapTab.click();

    await new Promise(resolve => setTimeout(resolve, 70));
    state.map?.invalidateSize();
    const zoom = Math.max(state.map?.getZoom() || 4, 13);
    state.map?.setView([lat, lon], zoom, { animate: true });

    let marker = state.markers.get(callsign);
    if (!marker) {
      await loadMapData();
      marker = state.markers.get(callsign);
    }
    marker?.openPopup();
  }

  $('#stationFilter').addEventListener('input', debounce(loadStations, 250));

  function calculateAprsPasscode(callsign) {
    const base = String(callsign || '').trim().toUpperCase().split('-')[0];
    if (!/^[A-Z0-9]{1,6}$/.test(base)) return '';

    let hash = 0x73e2;
    for (let i = 0; i < base.length; i += 2) {
      hash ^= base.charCodeAt(i) << 8;
      if (i + 1 < base.length) hash ^= base.charCodeAt(i + 1);
    }
    return String(hash & 0x7fff);
  }

  function updateCalculatedPasscode(force = false) {
    const form = $('#configForm');
    if (!form) return;
    const callsign = form.elements.namedItem('callsign');
    const passcode = form.elements.namedItem('passcode');
    if (!callsign || !passcode) return;

    const calculated = calculateAprsPasscode(callsign.value);
    if (calculated && (force || document.activeElement === callsign || !passcode.value.trim())) {
      passcode.value = calculated;
    }
  }

  $('#callsignInput')?.addEventListener('input', () => updateCalculatedPasscode(true));
  $('#callsignInput')?.addEventListener('change', () => updateCalculatedPasscode(true));

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
      const baseCall = String(cfg.callsign || '').toUpperCase().trim();
      const ssid = Number(cfg.ssid || 0);
      state.ownCallsign = baseCall ? (ssid ? `${baseCall}-${ssid}` : baseCall) : '';
      state.soundOnPersonalMessage = !!cfg.sound_on_personal_message;
      if (!String(cfg.passcode || '').trim()) updateCalculatedPasscode(true);
      applyMapPreferences(cfg);
      applyAppearancePreferences(cfg);
      syncMapPreferenceControls();
      syncAppearanceControls();
      state.configLoaded = true;
    } catch (err) { toast(err.message, 'error'); }
  }

  $('#configForm').addEventListener('submit', async e => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = Object.fromEntries(new FormData(form).entries());
    data.connect_on_start = form.elements.connect_on_start.checked;
    data.sound_on_personal_message = form.elements.sound_on_personal_message.checked;
    try {
      const result = await api('/api/config', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data)
      });
      toast(result.reconnected ? 'Configuração salva. APRS-IS reconectando com os novos parâmetros.' : 'Configuração salva no banco local.', 'ok');
      applyMapPreferences(result.config || data);
      applyAppearancePreferences(result.config || data);
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

  function syncMapPreferenceControls() {
    const form = $('#configForm');
    if (!form) return;

    const colorInput = form.elements.namedItem('track_color');
    const colorText = $('#trackColorText');
    const widthInput = form.elements.namedItem('track_width');
    const widthValue = $('#trackWidthValue');
    const brightnessInput = form.elements.namedItem('map_brightness');
    const brightnessValue = $('#mapBrightnessValue');

    if (colorInput && colorText) colorText.value = colorInput.value || '#3ba6ff';
    if (widthInput && widthValue) widthValue.textContent = `${widthInput.value || 2} px`;
    if (brightnessInput && brightnessValue) brightnessValue.textContent = `${brightnessInput.value || 100}%`;
  }

  $('#configForm')?.elements.namedItem('track_color')?.addEventListener('input', e => {
    const colorText = $('#trackColorText');
    if (colorText) colorText.value = e.target.value;
  });

  $('#trackColorText')?.addEventListener('input', e => {
    let value = e.target.value.trim();
    if (!value.startsWith('#')) value = '#' + value;
    if (/^#[0-9a-fA-F]{6}$/.test(value)) {
      const colorInput = $('#configForm')?.elements.namedItem('track_color');
      if (colorInput) colorInput.value = value;
    }
  });

  $('#trackWidth')?.addEventListener('input', e => {
    const out = $('#trackWidthValue');
    if (out) out.textContent = `${e.target.value} px`;
  });

  $('#mapBrightness')?.addEventListener('input', e => {
    const out = $('#mapBrightnessValue');
    if (out) out.textContent = `${e.target.value}%`;
    const tilePane = state.map?.getPane('tilePane');
    if (tilePane) tilePane.style.filter = `brightness(${e.target.value}%)`;
  });

  function syncAppearanceControls() {
    const form = $('#configForm');
    if (!form) return;
    const msgSize = form.elements.namedItem('messages_font_size');
    const stnSize = form.elements.namedItem('stations_font_size');
    const msgOut = $('#messagesFontSizeValue');
    const stnOut = $('#stationsFontSizeValue');
    if (msgSize && msgOut) msgOut.textContent = `${msgSize.value || 12} px`;
    if (stnSize && stnOut) stnOut.textContent = `${stnSize.value || 12} px`;
  }

  function previewAppearanceFromForm() {
    const form = $('#configForm');
    if (!form) return;
    applyAppearancePreferences({
      messages_font_family: form.elements.namedItem('messages_font_family')?.value || 'system',
      messages_font_size: form.elements.namedItem('messages_font_size')?.value || 12,
      stations_font_family: form.elements.namedItem('stations_font_family')?.value || 'system',
      stations_font_size: form.elements.namedItem('stations_font_size')?.value || 12
    });
    syncAppearanceControls();
  }

  for (const name of ['messages_font_family', 'messages_font_size', 'stations_font_family', 'stations_font_size']) {
    $('#configForm')?.elements.namedItem(name)?.addEventListener('input', previewAppearanceFromForm);
    $('#configForm')?.elements.namedItem(name)?.addEventListener('change', previewAppearanceFromForm);
  }

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
    await Promise.all([initMap(), loadStations(), loadLog(false), loadConfig(), refreshStatus()]);
    updateMyMessagesButton();
    await loadMessages();
    await checkIncomingPersonalMessages();
    await refreshVersionStatus();
    setInterval(refreshStatus, 2000);
    setInterval(loadMapData, 5000);
    setInterval(loadMessages, 3000);
    setInterval(checkIncomingPersonalMessages, 3000);
    setInterval(refreshVersionStatus, 30 * 60 * 1000);
    setInterval(() => { if (state.activeTab === 'stations') loadStations(); }, 5000);
    setInterval(() => { if (state.activeTab === 'log') loadLog(false); }, 1000);
  }

  boot();
})();
