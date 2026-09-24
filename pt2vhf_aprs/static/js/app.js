(() => {
  'use strict';

  const state = {
    activeTab: 'map',
    map: null,
    baseLayer: null,
    mapConfig: {
      map_type: 'osm',
      track_color: '#3ba6ff',
      track_width: 2,
      topology_rf_color: '#35a7ff',
      topology_igate_color: '#b06cff',
      topology_width: 2,
      map_brightness: 100
    },
    markers: new Map(),
    trackLines: new Map(),
    topologyLines: new Map(),
    topologyEnabled: false,
    topologyHours: 24,
    userLocationMarker: null,
    userLocationAccuracy: null,
    messages: [],
    stations: [],
    logs: [],
    sort: {
      messages: { key: 'timestamp', dir: 'asc', type: 'text' },
      stations: { key: 'last_heard', dir: 'desc', type: 'text' },
      logs: { key: 'timestamp', dir: 'desc', type: 'text' }
    },
    connected: false,
    symbolTable: '/',
    configLoaded: false,
    myMessagesOnly: false,
    hideTelemetryMessages: true,
    groupMessages: false,
    selectedConversation: '',
    ownCallsign: '',
    messageAlertBaselineReady: false,
    lastAlertedMessageId: 0,
    currentAlertMessage: null,
    soundOnPersonalMessage: true,
    messagePopupSeconds: 5,
    language: 'pt-BR',
    configSection: 'aprs',
    currentConfig: null,
    autoLocationInProgress: false,
    lastConnectionErrorShown: '',
    conversationSort: localStorage.getItem('pt2vhf_conversation_sort') === 'desc' ? 'desc' : 'asc',
    configDirty: false,
    configLoading: false,
    configBaseline: '',
    pendingTab: '',
    updateInfo: null,
    updateDownloading: false,
  };

  const BRAZIL_PREFIXES = ['PP','PQ','PR','PS','PT','PU','PV','PW','PX','PY','ZV','ZW','ZX','ZY','ZZ'];
  const BRAZIL_FILTER = 'p/' + BRAZIL_PREFIXES.join('/');

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  }

  function ui(pt, en) {
    return state.language === 'en' ? en : pt;
  }

  function currentLocale() {
    return state.language === 'en' ? 'en-US' : 'pt-BR';
  }

  function fmtDate(value) {
    if (!value) return '';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleString(currentLocale(), { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit', second:'2-digit' });
  }

  function fmtNum(value, digits = 1, suffix = '') {
    if (value === null || value === undefined || value === '') return '';
    const n = Number(value);
    return Number.isFinite(n) ? `${n.toLocaleString(currentLocale(), {maximumFractionDigits: digits})}${suffix}` : '';
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
    if (!force && state.configLoaded && !state.currentConfig?.check_updates_on_start) {
      el.classList.remove('checking', 'latest', 'update', 'error', 'ahead');
      textEl.textContent = ui('Verificação manual', 'Manual check');
      el.title = ui('Clique para verificar atualizações.', 'Click to check for updates.');
      return;
    }

    el.classList.remove('latest', 'update', 'error', 'ahead');
    el.classList.add('checking');
    textEl.textContent = ui('Verificando versão…', 'Checking version…');

    try {
      const data = await api(`/api/update-status${force ? '?force=1' : ''}`);
      state.updateInfo = data;
      el.classList.remove('checking');

      const current = data.current_version ? `v${data.current_version}` : ui('versão atual', 'current version');
      const latest = data.latest_version ? `v${data.latest_version}` : '';

      if (data.status === 'update_available') {
        el.classList.add('update');
        textEl.textContent = ui(`Nova versão ${latest}`, `New version ${latest}`);
        el.title = ui(`Instalada ${current}. Clique para atualizar.`, `Installed ${current}. Click to update.`);
        if (state.currentConfig?.auto_download_updates && !data.downloaded && !state.updateDownloading) {
          downloadAvailableUpdate(true);
        }
      } else if (data.status === 'latest') {
        el.classList.add('latest');
        textEl.textContent = ui('Última versão', 'Latest version');
        el.title = ui(`${current} é a versão mais recente publicada.`, `${current} is the latest published version.`);
      } else if (data.status === 'ahead') {
        el.classList.add('ahead');
        textEl.textContent = `Build ${current}`;
        el.title = latest ? `Build > ${latest}` : ui('Build de desenvolvimento.', 'Development build.');
      } else {
        el.classList.add('error');
        textEl.textContent = ui('Versão não verificada', 'Version not verified');
        el.title = ui('Não foi possível consultar a release mais recente no GitHub.', 'Could not check the latest GitHub release.');
      }
      updateUpdateSettingsUi();
    } catch (_) {
      el.classList.remove('checking');
      el.classList.add('error');
      textEl.textContent = ui('Versão não verificada', 'Version not verified');
      el.title = ui('Não foi possível consultar a release mais recente no GitHub.', 'Could not check the latest GitHub release.');
    }
  }

  function showUpdateModal() {
    const data = state.updateInfo;
    if (!data || data.status !== 'update_available') return;
    $('#updateModalTitle').textContent = ui(`Nova versão v${data.latest_version} disponível`, `New version v${data.latest_version} available`);
    $('#updateModalSummary').textContent = data.asset_name
      ? ui(`Pacote compatível: ${data.asset_name}`, `Compatible package: ${data.asset_name}`)
      : ui('Não há pacote automático compatível para esta plataforma.', 'No automatic package is available for this platform.');
    $('#updateReleaseNotes').textContent = String(data.release_notes || ui('Sem notas de versão.', 'No release notes.'));
    $('#updateDownloadNow').classList.toggle('hidden', !data.asset_url || !!data.downloaded);
    $('#updateDownloadProgress').textContent = data.downloaded
      ? ui('Atualização já baixada. Ela será aplicada ao fechar se essa opção estiver habilitada.', 'Update already downloaded. It will be applied on exit if enabled.')
      : '';
    $('#updateModal').classList.remove('hidden');
  }

  async function downloadAvailableUpdate(silent = false) {
    if (state.updateDownloading) return;
    if (!state.updateInfo?.asset_url) {
      if (!silent) toast(ui('Não há pacote automático compatível.', 'No compatible automatic package.'), 'error');
      return;
    }
    state.updateDownloading = true;
    const progress = $('#updateDownloadProgress');
    if (progress) progress.textContent = ui('Baixando e verificando SHA-256…', 'Downloading and verifying SHA-256…');
    try {
      const result = await api('/api/update/download', { method: 'POST' });
      if (progress) progress.textContent = ui(`Atualização baixada: ${result.update.asset_name}`, `Update downloaded: ${result.update.asset_name}`);
      if (!silent) {
        toast(ui('Atualização baixada e verificada.', 'Update downloaded and verified.'), 'ok');
        if (state.updateInfo?.install_supported && !state.currentConfig?.install_updates_on_exit) {
          const enable = window.confirm(ui(
            'Deseja instalar automaticamente esta atualização quando fechar o aplicativo?',
            'Install this update automatically when the application closes?'
          ));
          if (enable) {
            const payload = { ...(state.currentConfig || {}), install_updates_on_exit: true };
            const saved = await api('/api/config', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) });
            state.currentConfig = saved.config || payload;
            const checkbox = $('#configForm')?.elements.namedItem('install_updates_on_exit');
            if (checkbox) checkbox.checked = true;
          }
        }
      }
      await refreshVersionStatus(true);
      await refreshPendingUpdateStatus();
    } catch (err) {
      if (progress) progress.textContent = err.message;
      if (!silent) toast(err.message, 'error');
    } finally {
      state.updateDownloading = false;
    }
  }

  async function refreshPendingUpdateStatus() {
    try {
      const data = await api('/api/update/pending');
      const status = $('#updateSettingsStatus');
      if (status) {
        status.textContent = data.pending
          ? ui(`Baixada v${data.pending.version}: ${data.pending.asset_name}`, `Downloaded v${data.pending.version}: ${data.pending.asset_name}`)
          : ui('Nenhuma atualização pendente.', 'No pending update.');
      }
      $('#rollbackUpdateButton')?.classList.toggle('hidden', !data.rollback);
      $('#downloadUpdateButton')?.classList.toggle('hidden', !(state.updateInfo?.status === 'update_available' && !data.pending));
    } catch (_) {}
  }

  function updateUpdateSettingsUi() {
    const btn = $('#downloadUpdateButton');
    if (btn) btn.classList.toggle('hidden', !(state.updateInfo?.status === 'update_available' && state.updateInfo?.asset_url && !state.updateInfo?.downloaded));
  }

  $('#versionStatus')?.addEventListener('click', e => {
    e.preventDefault();
    if (state.updateInfo?.status === 'update_available') showUpdateModal();
    else refreshVersionStatus(true);
  });
  $('#updateModalClose')?.addEventListener('click', () => $('#updateModal')?.classList.add('hidden'));
  $('#updateDownloadNow')?.addEventListener('click', () => downloadAvailableUpdate(false));
  $('#downloadUpdateButton')?.addEventListener('click', () => downloadAvailableUpdate(false));
  $('#checkUpdatesNowButton')?.addEventListener('click', async () => {
    await refreshVersionStatus(true);
    if (state.updateInfo?.status === 'update_available') showUpdateModal();
    else toast(ui('Verificação concluída.', 'Update check completed.'), 'ok');
  });
  $('#updateOpenRelease')?.addEventListener('click', () => {
    const url = state.updateInfo?.release_url;
    if (!url) return;
    const nativeApi = window.pywebview?.api;
    if (nativeApi?.open_external) nativeApi.open_external(url);
    else window.open(url, '_blank', 'noopener');
  });
  $('#rollbackUpdateButton')?.addEventListener('click', async () => {
    if (!window.confirm(ui('Preparar rollback para a versão anterior ao fechar o aplicativo?', 'Prepare rollback to the previous version when the app closes?'))) return;
    try {
      const result = await api('/api/update/rollback', { method:'POST' });
      toast(result.message || ui('Rollback preparado.', 'Rollback prepared.'), 'ok');
    } catch (err) { toast(err.message, 'error'); }
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

  document.addEventListener('click', e => {
    const shortcut = e.target.closest('[data-help-tab]');
    if (!shortcut) return;
    const target = shortcut.dataset.helpTab;
    const tab = $('.tab[data-tab="' + target + '"]');
    if (tab) tab.click();
  });

  function setupExternalLinksForEmbeddedWindow() {
    document.addEventListener('click', event => {
      const link = event.target.closest('a[href]');
      if (!link) return;

      const href = link.getAttribute('href') || '';
      if (!href || href.startsWith('#') || href.startsWith('/') || href.startsWith('./') || href.startsWith('../')) return;

      let target;
      try {
        target = new URL(href, window.location.href);
      } catch (_) {
        return;
      }

      const isExternal = ['http:', 'https:', 'mailto:'].includes(target.protocol)
        && (target.protocol === 'mailto:' || target.origin !== window.location.origin);
      if (!isExternal) return;

      const nativeApi = window.pywebview?.api;
      if (nativeApi?.open_external) {
        event.preventDefault();
        nativeApi.open_external(target.href);
      }
    });
  }

  function activateTab(tab) {
    state.activeTab = tab;
    $$('.tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    $$('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${tab}`));
    if (tab === 'map') setTimeout(() => state.map?.invalidateSize(), 30);
    if (tab === 'messages') {
      markMessagesSeen();
      loadMessages({ scrollToNewest: true });
    }
    if (tab === 'stations') loadStations({ scrollToNewest: true });
    if (tab === 'log') loadLog(true);
    if (tab === 'config') loadConfig();
  }

  function tabSetup() {
    $$('.tab').forEach(btn => btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      if (state.activeTab === 'config' && tab !== 'config' && state.configDirty) {
        state.pendingTab = tab;
        $('#unsavedConfigModal')?.classList.remove('hidden');
        return;
      }
      activateTab(tab);
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
    const theme = cfg.app_theme === 'light' ? 'light' : 'dark';
    root.dataset.theme = theme;
    const messagesFamily = FONT_FAMILIES[cfg.messages_font_family] || FONT_FAMILIES.system;
    const stationsFamily = FONT_FAMILIES[cfg.stations_font_family] || FONT_FAMILIES.system;
    const logsFamily = FONT_FAMILIES[cfg.logs_font_family] || FONT_FAMILIES.consolas;
    const messagesSize = Math.min(20, Math.max(10, Number(cfg.messages_font_size || 12)));
    const stationsSize = Math.min(20, Math.max(10, Number(cfg.stations_font_size || 12)));
    const logsSize = Math.min(20, Math.max(10, Number(cfg.logs_font_size || 12)));
    const messagesLine = Math.min(2, Math.max(1, Number(cfg.messages_line_height || 1.35)));
    const stationsLine = Math.min(2, Math.max(1, Number(cfg.stations_line_height || 1.25)));
    const logsLine = Math.min(2, Math.max(1, Number(cfg.logs_line_height || 1.30)));

    root.style.setProperty('--messages-font-family', messagesFamily);
    root.style.setProperty('--messages-font-size', `${messagesSize}px`);
    root.style.setProperty('--messages-font-weight', cfg.messages_font_weight === 'bold' ? '700' : '400');
    root.style.setProperty('--messages-line-height', String(messagesLine));
    root.style.setProperty('--stations-font-family', stationsFamily);
    root.style.setProperty('--stations-font-size', `${stationsSize}px`);
    root.style.setProperty('--stations-font-weight', cfg.stations_font_weight === 'bold' ? '700' : '400');
    root.style.setProperty('--stations-line-height', String(stationsLine));
    root.style.setProperty('--logs-font-family', logsFamily);
    root.style.setProperty('--logs-font-size', `${logsSize}px`);
    root.style.setProperty('--logs-font-weight', cfg.logs_font_weight === 'bold' ? '700' : '400');
    root.style.setProperty('--logs-line-height', String(logsLine));
  }

  function applyMapPreferences(cfg = {}) {
    state.mapConfig = {
      map_type: cfg.map_type || state.mapConfig.map_type || 'osm',
      track_color: cfg.track_color || state.mapConfig.track_color || '#3ba6ff',
      track_width: Number(cfg.track_width || state.mapConfig.track_width || 2),
      topology_rf_color: cfg.topology_rf_color || state.mapConfig.topology_rf_color || '#35a7ff',
      topology_igate_color: cfg.topology_igate_color || state.mapConfig.topology_igate_color || '#b06cff',
      topology_width: Number(cfg.topology_width || state.mapConfig.topology_width || 2),
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

      if (state.topologyEnabled) loadTopology();
    }
  }

  async function waitForLeaflet(timeoutMs = 10000) {
    const started = Date.now();
    while (typeof L === 'undefined' && Date.now() - started < timeoutMs) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return typeof L !== 'undefined';
  }

  async function initMap() {
    if (!(await waitForLeaflet())) {
      $('#map').innerHTML = '<div style="padding:30px">O mapa não pôde ser carregado, mas as demais abas continuam disponíveis. Verifique o acesso ao CDN do Leaflet.</div>';
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
    addTopologyControl(state.map);
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

  function addTopologyControl(map) {
    const savedEnabled = localStorage.getItem('pt2vhf_topology_enabled');
    const savedHours = Number(localStorage.getItem('pt2vhf_topology_hours') || 24);
    state.topologyEnabled = savedEnabled === '1';
    state.topologyHours = [1, 6, 24, 168].includes(savedHours) ? savedHours : 24;

    const TopologyControl = L.Control.extend({
      options: { position: 'topright' },
      onAdd() {
        const wrapper = L.DomUtil.create('div', 'leaflet-control topology-control');
        wrapper.innerHTML = `
          <label><input id="topologyToggle" type="checkbox" ${state.topologyEnabled ? 'checked' : ''}> Topologia observada</label>
          <select id="topologyHours" title="Período da topologia">
            <option value="1">1 h</option>
            <option value="6">6 h</option>
            <option value="24">24 h</option>
            <option value="168">7 dias</option>
          </select>`;
        L.DomEvent.disableClickPropagation(wrapper);
        L.DomEvent.disableScrollPropagation(wrapper);

        setTimeout(() => {
          const toggle = wrapper.querySelector('#topologyToggle');
          const select = wrapper.querySelector('#topologyHours');
          select.value = String(state.topologyHours);
          toggle.addEventListener('change', async () => {
            state.topologyEnabled = toggle.checked;
            localStorage.setItem('pt2vhf_topology_enabled', state.topologyEnabled ? '1' : '0');
            if (state.topologyEnabled) await loadTopology();
            else clearTopologyLines();
          });
          select.addEventListener('change', async () => {
            state.topologyHours = Number(select.value) || 24;
            localStorage.setItem('pt2vhf_topology_hours', String(state.topologyHours));
            if (state.topologyEnabled) await loadTopology();
          });
        }, 0);
        return wrapper;
      }
    });
    new TopologyControl().addTo(map);
  }

  function clearTopologyLines() {
    for (const line of state.topologyLines.values()) state.map?.removeLayer(line);
    state.topologyLines.clear();
  }

  async function loadTopology() {
    if (!state.map || !state.topologyEnabled) return;
    try {
      const edges = await api(`/api/topology?hours=${encodeURIComponent(state.topologyHours)}`);
      const active = new Set();

      for (const edge of edges) {
        const key = `${edge.source}>${edge.target}:${edge.kind}`;
        active.add(key);
        const points = [
          [Number(edge.source_lat), Number(edge.source_lon)],
          [Number(edge.target_lat), Number(edge.target_lon)]
        ];
        if (!points.flat().every(Number.isFinite)) continue;

        let line = state.topologyLines.get(key);
        const style = {
          color: edge.kind === 'igate' ? state.mapConfig.topology_igate_color : state.mapConfig.topology_rf_color,
          weight: state.mapConfig.topology_width,
          opacity: .72,
          dashArray: edge.kind === 'igate' ? '7 5' : null
        };
        if (!line) {
          line = L.polyline(points, style).addTo(state.map);
          state.topologyLines.set(key, line);
        } else {
          line.setLatLngs(points).setStyle(style);
        }

        line.bindPopup(`
          <div class="topology-popup">
            <h3>Topologia observada</h3>
            <div><strong>${escapeHtml(edge.source)} → ${escapeHtml(edge.target)}</strong></div>
            <div>Tipo: ${edge.kind === 'igate' ? 'Entrada no IGate' : 'Enlace RF observado'}</div>
            <div>Pacotes observados: ${Number(edge.packet_count || 0).toLocaleString('pt-BR')}</div>
            <div>Primeiro: ${escapeHtml(fmtDate(edge.first_seen))}</div>
            <div>Último: ${escapeHtml(fmtDate(edge.last_seen))}</div>
          </div>`);
      }

      for (const [key, line] of state.topologyLines) {
        if (!active.has(key)) {
          state.map.removeLayer(line);
          state.topologyLines.delete(key);
        }
      }
    } catch (err) {
      console.warn(err);
    }
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
      const activeStations = new Set(data.stations.map(s => s.callsign));
      for (const [call, marker] of state.markers) {
        if (!activeStations.has(call)) {
          state.map.removeLayer(marker);
          state.markers.delete(call);
        }
      }

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
      for (const [call, line] of state.trackLines) {
        if (!grouped.has(call)) {
          state.map.removeLayer(line);
          state.trackLines.delete(call);
        }
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
      if (state.topologyEnabled) await loadTopology();
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
      el.querySelector('span:last-child').textContent = translateConnectionState(s.state || (s.connected ? 'Conectado' : 'Desconectado'));
      el.title = s.last_error || s.server_message || '';
      $('#connectButton').textContent = s.connected || s.wanted ? ui('Desconectar', 'Disconnect') : ui('Conectar', 'Connect');
      if (!s.connected && !s.wanted && s.last_error && s.last_error !== state.lastConnectionErrorShown) {
        state.lastConnectionErrorShown = s.last_error;
        toast(ui('Falha na conexão APRS-IS: ', 'APRS-IS connection failed: ') + s.last_error, 'error');
      }
      if (s.connected) state.lastConnectionErrorShown = '';
      const stationCount = Number(s.stations || 0);
      const messageCount = Number(s.messages || 0);
      const packetCount = Number(s.packets_received || 0);
      if ($('#headerStationCount')) $('#headerStationCount').textContent = stationCount.toLocaleString('pt-BR');
      if ($('#headerPacketCount')) $('#headerPacketCount').textContent = packetCount.toLocaleString('pt-BR');
      if ($('#stationTotalCount')) $('#stationTotalCount').textContent = stationCount.toLocaleString('pt-BR');
      if ($('#messageTotalCount')) $('#messageTotalCount').textContent = messageCount.toLocaleString('pt-BR');
    } catch (_) {}
  }

  $('#connectButton').addEventListener('click', async () => {
    try {
      if (state.connected || $('#connectButton').textContent === ui('Desconectar', 'Disconnect')) {
        await api('/api/disconnect', { method: 'POST' });
      } else {
        const missing = missingRequiredStationFields();
        if (missing.length) {
          showRequiredFieldsModal(missing);
          return;
        }
        if (!validateCallsignField()) {
          const invalidCall = requiredStationDefinitions().find(item => item.key === 'callsign');
          showRequiredFieldsModal(invalidCall ? [invalidCall] : []);
          $('#callsignInput')?.reportValidity();
          return;
        }
        await api('/api/connect', { method: 'POST' });
      }
      await refreshStatus();
    } catch (err) {
      if (/Preencha os campos obrigatórios/i.test(String(err.message || ''))) {
        showRequiredFieldsModal(missingRequiredStationFields());
      } else {
        toast(err.message, 'error');
      }
    }
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
      return String(av).localeCompare(String(bv), currentLocale(), { numeric: true, sensitivity: 'base' }) * factor;
    });
  }

  function updateSortIndicators(tableId, spec) {
    const table = document.getElementById(tableId);
    table.querySelectorAll('th[data-key]').forEach(th => {
      th.querySelector('.sort-indicator').textContent = th.dataset.key === spec.key ? (spec.dir === 'asc' ? '▲' : '▼') : '';
    });
  }

  async function loadMessages(options = {}) {
    try {
      const viewport = $('.messages-table-wrap');
      const previousScrollTop = viewport?.scrollTop || 0;
      const distanceFromBottom = viewport
        ? Math.max(0, viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight)
        : 0;
      const atNewest = distanceFromBottom <= 18;

      const thread = $('#conversationMessages');
      const previousThreadScrollTop = thread?.scrollTop || 0;
      const threadDistanceFromBottom = thread
        ? Math.max(0, thread.scrollHeight - thread.scrollTop - thread.clientHeight)
        : 0;
      const threadAtNewest = threadDistanceFromBottom <= 18;

      const filter = $('#messageFilter').value.trim();
      const mine = state.myMessagesOnly ? '&mine=1' : '';
      state.messages = await api(`/api/messages?from=${encodeURIComponent(filter)}${mine}`);
      renderMessages();
      updateUnread();

      if (!state.groupMessages && viewport && state.sort.messages.key === 'timestamp' && state.sort.messages.dir === 'asc') {
        if (options.scrollToNewest || atNewest) viewport.scrollTop = viewport.scrollHeight;
        else viewport.scrollTop = previousScrollTop;
      }

      if (state.groupMessages && thread) {
        if (options.scrollToNewest || threadAtNewest) thread.scrollTop = thread.scrollHeight;
        else thread.scrollTop = previousThreadScrollTop;
      }
    } catch (err) { console.warn(err); }
  }

  function messageTypeLabel(type) {
    if (type === 'bulletin') return '<span class="message-type-badge bulletin">Boletim</span>';
    if (type === 'group_bulletin') return '<span class="message-type-badge group-bulletin">Grupo</span>';
    return '<span class="message-type-badge message">Mensagem</span>';
  }

  function messageStatusLabel(status) {
    if (status === 'ACK') return 'Lido';
    if (status === 'REJ') return 'Rejeitada';
    return status || '';
  }

  function messageGroupSummary(message) {
    const groupId = String(message?.message_group_id || '');
    const total = Number(message?.part_count || 0);
    if (!groupId || total <= 1) return '';
    const latestByPart = new Map();
    for (const row of state.messages) {
      if (String(row.message_group_id || '') !== groupId || row.direction !== 'out') continue;
      const part = Number(row.part_index || 0);
      if (!part) continue;
      const current = latestByPart.get(part);
      if (!current || Number(row.id || 0) > Number(current.id || 0)) latestByPart.set(part, row);
    }
    const rows = [...latestByPart.values()];
    const ack = rows.filter(row => row.status === 'ACK').length;
    const rej = rows.filter(row => row.status === 'REJ').length;
    if (ack >= total) return ui('Todas confirmadas', 'All confirmed');
    if (rej) return ui(`${ack}/${total} confirmadas · ${rej} rejeitada(s)`, `${ack}/${total} confirmed · ${rej} rejected`);
    return ui(`${ack}/${total} confirmadas`, `${ack}/${total} confirmed`);
  }

  function retryButtonHtml(message) {
    if (message?.direction !== 'out' || message?.message_type !== 'message') return '';
    if (['ACK', 'Substituída por retry'].includes(String(message.status || ''))) return '';
    const max = Number(state.currentConfig?.message_retry_attempts || 0);
    const used = Number(message.retry_count || 0);
    if (max <= 0 || used >= max) return '';
    return `<button type="button" class="btn secondary message-retry-button" data-retry-row-id="${Number(message.id)}" title="${escapeHtml(ui('Reenviar esta parte', 'Retry this part'))}">↻ ${escapeHtml(ui('Retry', 'Retry'))}</button>`;
  }
  function isTelemetryMessage(message) {
    const text = String(message?.message || '').trim().toUpperCase();
    if (!text) return false;
    return /^(?:PARM|UNIT|EQNS|BITS)\./.test(text)
      || /^T#\d{3}(?:,|$)/.test(text);
  }

  function visibleMessages() {
    return state.hideTelemetryMessages
      ? state.messages.filter(message => !isTelemetryMessage(message))
      : state.messages;
  }

  function normalizedCall(value) {
    return String(value || '').trim().toUpperCase();
  }

  function callsignButtonHtml(callsign, otherCall = '') {
    const call = normalizedCall(callsign);
    if (!call) return '';
    return `<button type="button" class="callsign-link message-callsign-link" data-callsign="${escapeHtml(call)}" data-other-call="${escapeHtml(normalizedCall(otherCall))}">${escapeHtml(call)}</button>`;
  }

  function resolveMessageContact(message) {
    if (!message || message.message_type !== 'message') return '';
    const from = normalizedCall(message.from_call);
    const to = normalizedCall(message.to_call);
    const own = normalizedCall(state.ownCallsign);

    if (own) {
      if (from === own && to && to !== own) return to;
      if (to === own && from && from !== own) return from;
    }
    return message.direction === 'out' ? (to || from) : (from || to);
  }

  function selectMessageRecipient(callsign, fallbackCall = '') {
    const own = normalizedCall(state.ownCallsign);
    let destination = normalizedCall(callsign);
    const fallback = normalizedCall(fallbackCall);

    if (destination && own && destination === own && fallback && fallback !== own) {
      destination = fallback;
    }
    if (!destination || (own && destination === own)) {
      toast('Não foi possível determinar outro indicativo para responder.', 'error');
      return;
    }

    $('#messageType').value = 'message';
    updateMessageComposerMode();
    $('#messageTo').value = destination;
    $('#messageText').focus();
  }

  function conversationItems() {
    const seen = Number(localStorage.getItem('pt2vhf_last_seen_msg') || 0);
    const conversations = new Map();

    for (const message of visibleMessages()) {
      if (message.message_type !== 'message') continue;
      const contact = resolveMessageContact(message);
      if (!contact) continue;
      if (!conversations.has(contact)) {
        conversations.set(contact, { contact, messages: [], unread: 0, last: null });
      }
      const item = conversations.get(contact);
      item.messages.push(message);
      if (!item.last || Number(message.id || 0) > Number(item.last.id || 0)) item.last = message;
      if (message.direction === 'in' && Number(message.id || 0) > seen) item.unread += 1;
    }

    const factor = state.conversationSort === 'asc' ? 1 : -1;
    return [...conversations.values()]
      .map(item => ({
        ...item,
        messages: item.messages.sort((a, b) => {
          const time = String(a.timestamp || '').localeCompare(String(b.timestamp || ''));
          return time || (Number(a.id || 0) - Number(b.id || 0));
        })
      }))
      .sort((a, b) => a.contact.localeCompare(b.contact, currentLocale(), { numeric:true, sensitivity:'base' }) * factor);
  }

  function renderGroupedMessages() {
    const conversations = conversationItems();
    const list = $('#conversationList');
    const empty = $('#conversationThreadEmpty');
    const content = $('#conversationThreadContent');
    const recipientButton = $('#conversationRecipientButton');
    const thread = $('#conversationMessages');

    if (!conversations.length) {
      list.innerHTML = '<div class="conversation-list-empty">Nenhuma conversa individual para os filtros atuais.</div>';
      state.selectedConversation = '';
      empty.classList.remove('hidden');
      content.classList.add('hidden');
      return;
    }

    if (!state.selectedConversation || !conversations.some(item => item.contact === state.selectedConversation)) {
      state.selectedConversation = conversations[0].contact;
    }

    list.innerHTML = conversations.map(item => {
      const selected = item.contact === state.selectedConversation ? ' selected' : '';
      return `<button type="button" class="conversation-item${selected}" data-conversation-contact="${escapeHtml(item.contact)}">
        <span class="conversation-item-top">
          <strong>${escapeHtml(item.contact)}</strong>
          <span>${escapeHtml(fmtDate(item.last?.timestamp))}</span>
        </span>
        <span class="conversation-item-bottom">
          <span>${escapeHtml(item.last?.message || '')}</span>
          ${item.unread ? `<span class="conversation-unread">${item.unread}</span>` : ''}
        </span>
      </button>`;
    }).join('');

    const selected = conversations.find(item => item.contact === state.selectedConversation) || conversations[0];
    empty.classList.add('hidden');
    content.classList.remove('hidden');
    recipientButton.textContent = selected.contact;
    recipientButton.dataset.callsign = selected.contact;
    thread.innerHTML = selected.messages.map(message => {
      const direction = message.direction === 'out' ? 'out' : 'in';
      const status = messageStatusLabel(message.status);
      return `<div class="chat-bubble-row ${direction}">
        <div class="chat-bubble">
          <div class="chat-bubble-text">${escapeHtml(message.message || '')}</div>
          <div class="chat-bubble-meta">
            <span>${escapeHtml(fmtDate(message.timestamp))}</span>
            ${status ? `<span class="${message.status === 'ACK' ? 'status-ack' : message.status === 'REJ' ? 'status-rej' : ''}">${escapeHtml(status)}</span>` : ''}
            ${messageGroupSummary(message) ? `<span class="message-group-status">${escapeHtml(messageGroupSummary(message))}</span>` : ''}
            ${retryButtonHtml(message)}
          </div>
        </div>
      </div>`;
    }).join('');
  }

  function renderMessages() {
    const tableWrap = $('.messages-table-wrap');
    const groupedView = $('#groupedMessagesView');
    tableWrap?.classList.toggle('hidden', state.groupMessages);
    groupedView?.classList.toggle('hidden', !state.groupMessages);

    if (state.groupMessages) {
      renderGroupedMessages();
      return;
    }

    const spec = state.sort.messages;
    const rows = sortedData(visibleMessages(), spec);
    $('#messagesTable tbody').innerHTML = rows.map(m => `
      <tr class="${m.status === 'ACK' ? 'message-row-ack' : m.status === 'REJ' ? 'message-row-rej' : ''}">
        <td class="${m.direction === 'in' ? 'direction-in' : 'direction-out'}">${callsignButtonHtml(m.from_call, m.to_call)}</td>
        <td>${callsignButtonHtml(m.to_call, m.from_call)}</td>
        <td>${messageTypeLabel(m.message_type)}</td>
        <td>${escapeHtml(m.message)}</td>
        <td>${escapeHtml(fmtDate(m.timestamp))}</td>
        <td class="${m.status === 'ACK' ? 'status-ack' : m.status === 'REJ' ? 'status-rej' : ''}">
          ${escapeHtml(messageStatusLabel(m.status))}
          ${messageGroupSummary(m) ? `<span class="message-group-status">${escapeHtml(messageGroupSummary(m))}</span>` : ''}
          ${retryButtonHtml(m)}
        </td>
      </tr>`).join('');
    updateSortIndicators('messagesTable', spec);
  }

  const loadMessagesDebounced = debounce(loadMessages, 250);
  $('#messageFilter').addEventListener('input', loadMessagesDebounced);

  const telemetryPreference = localStorage.getItem('pt2vhf_hide_telemetry');
  state.hideTelemetryMessages = telemetryPreference === null ? true : telemetryPreference !== '0';
  state.groupMessages = localStorage.getItem('pt2vhf_group_messages') === '1';
  const telemetryToggle = $('#hideTelemetryMessages');
  if (telemetryToggle) telemetryToggle.checked = state.hideTelemetryMessages;
  telemetryToggle?.addEventListener('change', () => {
    state.hideTelemetryMessages = telemetryToggle.checked;
    localStorage.setItem('pt2vhf_hide_telemetry', state.hideTelemetryMessages ? '1' : '0');
    renderMessages();
    updateUnread();
    const hiddenCount = state.messages.filter(isTelemetryMessage).length;
    toast(
      state.hideTelemetryMessages
        ? `Telemetria oculta (${hiddenCount} registro(s) nesta lista).`
        : 'Telemetria visível.',
      'ok'
    );
  });

  function updateGroupMessagesButton() {
    const btn = $('#groupMessagesButton');
    if (!btn) return;
    btn.classList.toggle('active-filter', state.groupMessages);
    btn.setAttribute('aria-pressed', state.groupMessages ? 'true' : 'false');
    btn.textContent = state.groupMessages ? '✓ Agrupado por remetente' : 'Agrupar por remetente';
  }

  $('#groupMessagesButton')?.addEventListener('click', () => {
    state.groupMessages = !state.groupMessages;
    localStorage.setItem('pt2vhf_group_messages', state.groupMessages ? '1' : '0');
    updateGroupMessagesButton();
    renderMessages();
    const viewport = state.groupMessages ? $('#conversationMessages') : $('.messages-table-wrap');
    if (viewport) viewport.scrollTop = viewport.scrollHeight;
  });

  $('#conversationList')?.addEventListener('click', event => {
    const item = event.target.closest('[data-conversation-contact]');
    if (!item) return;
    state.selectedConversation = normalizedCall(item.dataset.conversationContact);
    if (state.selectedConversation) {
      $('#messageType').value = 'message';
      updateMessageComposerMode();
      $('#messageTo').value = state.selectedConversation;
    }
    renderGroupedMessages();
    const thread = $('#conversationMessages');
    if (thread) thread.scrollTop = thread.scrollHeight;
  });

  $('#conversationSortButton')?.addEventListener('click', () => {
    state.conversationSort = state.conversationSort === 'asc' ? 'desc' : 'asc';
    localStorage.setItem('pt2vhf_conversation_sort', state.conversationSort);
    const indicator = $('#conversationSortIndicator');
    if (indicator) indicator.textContent = state.conversationSort === 'asc' ? '▲' : '▼';
    renderGroupedMessages();
  });
  if ($('#conversationSortIndicator')) $('#conversationSortIndicator').textContent = state.conversationSort === 'asc' ? '▲' : '▼';

  $('#conversationRecipientButton')?.addEventListener('click', event => {
    selectMessageRecipient(event.currentTarget.dataset.callsign || '');
  });

  $('#messagesTable tbody')?.addEventListener('click', event => {
    const retry = event.target.closest('.message-retry-button');
    if (retry) {
      event.preventDefault();
      event.stopPropagation();
      retryMessagePart(Number(retry.dataset.retryRowId || 0));
      return;
    }
    const button = event.target.closest('.message-callsign-link');
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    selectMessageRecipient(button.dataset.callsign || '', button.dataset.otherCall || '');
  });

  $('#conversationMessages')?.addEventListener('click', event => {
    const retry = event.target.closest('.message-retry-button');
    if (!retry) return;
    event.preventDefault();
    retryMessagePart(Number(retry.dataset.retryRowId || 0));
  });

  async function retryMessagePart(rowId) {
    if (!rowId) return;
    try {
      await api(`/api/messages/${rowId}/retry`, { method:'POST' });
      toast(ui('Parte reenviada com novo ID APRS.', 'Part retried with a new APRS ID.'), 'ok');
      await loadMessages({ scrollToNewest:true });
    } catch (err) { toast(err.message, 'error'); }
  }

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
    updateGroupMessagesButton();
    await loadMessages({ scrollToNewest: true });
  });

  $('#clearMessagesButton')?.addEventListener('click', async () => {
    if (!window.confirm('Apagar TODO o histórico de mensagens e boletins armazenado neste computador? Esta ação não pode ser desfeita.')) return;
    try {
      const result = await api('/api/messages/clear', { method: 'POST' });
      state.messages = [];
      renderMessages();
      localStorage.removeItem('pt2vhf_last_seen_msg');
      state.messageAlertBaselineReady = false;
      state.lastAlertedMessageId = 0;
      $('#messageBadge')?.classList.add('hidden');
      toast(`Histórico de mensagens limpo (${Number(result.deleted || 0)} registro(s)).`, 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
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
    $('#messageTo').value = normalizedCall(destination);
    $('#messageText').focus();
  }

  document.addEventListener('click', e => {
    const button = e.target.closest('.station-message-button');
    if (!button) return;
    e.preventDefault();
    e.stopPropagation();
    openMessageComposer(button.dataset.callsign || '');
  });

  function estimateMessageParts(text) {
    const clean = String(text || '').replace(/\s+/g, ' ').trim();
    if (!clean) return 0;
    if (clean.length <= 63) return 1;
    const limit = 55;
    let parts = 0;
    let current = '';
    for (let word of clean.split(' ')) {
      if (word.length > limit) {
        if (current) { parts++; current = ''; }
        parts += Math.floor(word.length / limit);
        word = word.slice(Math.floor(word.length / limit) * limit);
        if (word) current = word;
        continue;
      }
      const candidate = current ? `${current} ${word}` : word;
      if (candidate.length <= limit) current = candidate;
      else { parts++; current = word; }
    }
    if (current) parts++;
    return Math.max(1, parts);
  }

  function updateMessageCharCounter() {
    const input = $('#messageText');
    const counter = $('#messageCharCounter');
    if (!input || !counter) return;
    const type = $('#messageType')?.value || 'message';
    if (type === 'message') {
      const parts = estimateMessageParts(input.value);
      counter.textContent = `${input.value.length} caracteres${parts > 1 ? ` · ${parts} partes APRS` : ''}`;
      counter.classList.remove('near-limit');
    } else {
      counter.textContent = `${input.value.length} / 67`;
      counter.classList.toggle('near-limit', input.value.length >= 59);
    }
  }

  function updateMessageComposerMode() {
    const type = $('#messageType').value;
    const isMessage = type === 'message';
    const isGroup = type === 'group_bulletin';

    $('#messageDestinationField').classList.toggle('hidden', !isMessage);
    $('#bulletinIdField').classList.toggle('hidden', isMessage);
    $('#bulletinGroupField').classList.toggle('hidden', !isGroup);

    const messageInput = $('#messageText');
    if (isMessage) messageInput.removeAttribute('maxlength');
    else messageInput.maxLength = 67;
    messageInput.placeholder = isMessage ? 'Digite a mensagem APRS; textos longos serão enviados em partes' : 'Digite o texto do boletim APRS';
    $('#sendMessageButton').textContent = isMessage ? 'Enviar' : 'Enviar boletim';
    updateMessageCharCounter();
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
      updateMessageCharCounter();
      if (result.type === 'message') {
        const count = Number(result.part_count || 1);
        toast(count > 1 ? `Mensagem enviada em ${count} partes APRS.` : 'Mensagem enviada ao APRS-IS.', 'ok');
      } else {
        toast('Boletim enviado ao APRS-IS sem solicitação de ACK.', 'ok');
      }
      await loadMessages();
    } catch (err) { toast(err.message, 'error'); }
  }

  $('#messageType').addEventListener('change', updateMessageComposerMode);
  $('#bulletinGroup').addEventListener('input', e => { e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 5); });
  $('#sendMessageButton').addEventListener('click', sendMessage);
  $('#messageText').addEventListener('input', updateMessageCharCounter);
  $('#messageText').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  updateMessageComposerMode();
  updateMessageCharCounter();

  let compactMessageAlertTimer = null;

  function closeIncomingMessageAlert() {
    $('#incomingMessageModal')?.classList.add('hidden');
    state.currentAlertMessage = null;
  }

  function closeCompactIncomingMessageAlert() {
    clearTimeout(compactMessageAlertTimer);
    compactMessageAlertTimer = null;
    $('#incomingMessageCompact')?.classList.add('hidden');
    state.currentAlertMessage = null;
  }

  function showIncomingMessageAlert(message) {
    state.currentAlertMessage = message;

    if (state.activeTab === 'messages') {
      $('#incomingMessageCompactFrom').textContent = message.from_call || '';
      $('#incomingMessageCompactTime').textContent = fmtDate(message.timestamp);
      $('#incomingMessageCompactText').textContent = message.message || '';
      $('#incomingMessageCompact')?.classList.remove('hidden');
      clearTimeout(compactMessageAlertTimer);
      compactMessageAlertTimer = setTimeout(
        closeCompactIncomingMessageAlert,
        Math.max(1, Number(state.messagePopupSeconds || 5)) * 1000
      );
      return;
    }

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

      const modalVisible = !$('#incomingMessageModal')?.classList.contains('hidden');
      const compactVisible = !$('#incomingMessageCompact')?.classList.contains('hidden');
      if (modalVisible || compactVisible) return;
      const next = incoming.find(m => Number(m.id) > state.lastAlertedMessageId);
      if (next) {
        state.lastAlertedMessageId = Number(next.id) || state.lastAlertedMessageId;
        showIncomingMessageAlert(next);
      }
    } catch (err) {
      console.warn(err);
    }
  }

  $('#incomingMessageCompactClose')?.addEventListener('click', closeCompactIncomingMessageAlert);
  $('#incomingMessageCompactReply')?.addEventListener('click', () => {
    const message = state.currentAlertMessage;
    if (!message) return;
    const sender = message.from_call || '';
    closeCompactIncomingMessageAlert();
    selectMessageRecipient(sender);
  });

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
    const incoming = visibleMessages().filter(m => m.direction === 'in');
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
      const viewport = $('#logViewport');
      const previousScrollTop = viewport?.scrollTop || 0;
      const wasNearTop = previousScrollTop <= 12;
      const filter = $('#logFilter')?.value.trim() || '';
      const direction = $('#logDirection')?.value || 'ALL';
      const limit = $('#logLimit')?.value || '1000';
      state.logs = await api(`/api/log?filter=${encodeURIComponent(filter)}&direction=${encodeURIComponent(direction)}&limit=${encodeURIComponent(limit)}`);
      renderLog(forceScroll, previousScrollTop, wasNearTop);
    } catch (err) {
      console.warn(err);
    }
  }

  function renderLog(forceScroll = false, previousScrollTop = 0, wasNearTop = true) {
    const tbody = $('#logTable tbody');
    const viewport = $('#logViewport');
    if (!tbody || !viewport) return;

    const auto = $('#logAutoScroll')?.checked ?? true;

    if (!state.logs.length) {
      tbody.innerHTML = '<tr class="log-empty"><td colspan="3">Nenhum tráfego APRS-IS registrado para este filtro.</td></tr>';
      return;
    }

    const rows = sortedData(state.logs, state.sort.logs);
    tbody.innerHTML = rows.map(row => {
      const direction = row.direction === 'TX' ? 'TX' : 'RX';
      return `<tr class="log-${direction.toLowerCase()}">
        <td>${escapeHtml(fmtDate(row.timestamp))}</td>
        <td class="log-direction">${direction}</td>
        <td class="log-raw">${escapeHtml(row.raw || '')}</td>
      </tr>`;
    }).join('');
    const indicator = $('#logTimeHeader .sort-indicator');
    if (indicator) indicator.textContent = state.sort.logs.dir === 'asc' ? '▲' : '▼';

    if (auto && (forceScroll || wasNearTop)) {
      viewport.scrollTop = 0;
    } else {
      viewport.scrollTop = previousScrollTop;
    }
  }

  $('#logTimeHeader')?.addEventListener('click', () => {
    state.sort.logs.dir = state.sort.logs.dir === 'asc' ? 'desc' : 'asc';
    renderLog(false, $('#logViewport')?.scrollTop || 0, false);
  });

  const loadLogDebounced = debounce(() => loadLog(true), 220);
  $('#logFilter')?.addEventListener('input', loadLogDebounced);
  $('#logDirection')?.addEventListener('change', () => loadLog(true));
  $('#logLimit')?.addEventListener('change', () => loadLog(true));
  $('#logAutoScroll')?.addEventListener('change', () => {
    if ($('#logAutoScroll').checked) {
      const viewport = $('#logViewport');
      viewport.scrollTop = 0;
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

  async function loadStations(options = {}) {
    try {
      const viewport = $('.stations-table-wrap');
      const previousScrollTop = viewport?.scrollTop || 0;
      const atNewest = previousScrollTop <= 12;
      const filter = $('#stationFilter').value.trim();
      state.stations = await api(`/api/stations?filter=${encodeURIComponent(filter)}`);
      renderStations();

      if (viewport && state.sort.stations.key === 'last_heard' && state.sort.stations.dir === 'desc') {
        if (options.scrollToNewest || atNewest) viewport.scrollTop = 0;
        else viewport.scrollTop = previousScrollTop;
      }
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

    $$('#stationsTable tbody .station-row').forEach(row => {
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

  async function clearAllStations() {
    if (!window.confirm('Apagar TODAS as estações e todos os tracklogs armazenados neste computador? Novas estações voltarão a aparecer quando forem recebidas.')) return;
    try {
      const result = await api('/api/stations/clear', { method: 'POST' });
      state.stations = [];
      renderStations();

      for (const marker of state.markers.values()) state.map?.removeLayer(marker);
      for (const line of state.trackLines.values()) state.map?.removeLayer(line);
      state.markers.clear();
      state.trackLines.clear();

      clearTopologyLines();
      await loadMapData();
      await refreshStatus();

      const deletedStations = Number(result.deleted?.stations || 0);
      const deletedTracks = Number(result.deleted?.tracks || 0);
      toast(`Estações limpas (${deletedStations} estação(ões), ${deletedTracks} ponto(s) de tracklog).`, 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
  }

  async function clearMapTracklogs() {
    if (!window.confirm('Apagar TODOS os tracklogs armazenados neste computador? As estações permanecerão no mapa. Esta ação não pode ser desfeita.')) return;
    try {
      const result = await api('/api/tracks/clear', { method: 'POST' });
      for (const line of state.trackLines.values()) state.map?.removeLayer(line);
      state.trackLines.clear();
      await loadMapData();
      await refreshStatus();
      toast(`Tracklogs apagados (${Number(result.deleted || 0)} ponto(s)).`, 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
  }

  $('#clearStationsButton')?.addEventListener('click', clearAllStations);
  $('#clearTracklogsButton')?.addEventListener('click', clearMapTracklogs);

  $('#stationFilter').addEventListener('input', debounce(() => loadStations({ scrollToNewest: true }), 250));

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

  function validateCallsignField() {
    const input = $('#callsignInput');
    const status = $('#callsignValidationStatus');
    if (!input) return false;
    const value = String(input.value || '').trim().toUpperCase();
    const valid = /^[A-Z0-9]{1,6}$/.test(value);
    input.setCustomValidity(!value ? '' : (valid ? '' : ui(
      'Use de 1 a 6 letras ou números, sem SSID.',
      'Use 1 to 6 letters or numbers, without SSID.'
    )));
    if (status) {
      status.textContent = !value
        ? ui('Obrigatório. O passcode APRS-IS será calculado automaticamente.', 'Required. The APRS-IS passcode will be calculated automatically.')
        : valid
          ? ui('Indicativo válido. Passcode atualizado automaticamente.', 'Valid callsign. Passcode updated automatically.')
          : ui('Indicativo inválido. Use de 1 a 6 letras ou números, sem SSID.', 'Invalid callsign. Use 1 to 6 letters or numbers, without SSID.');
      status.classList.toggle('field-status-error', !!value && !valid);
    }
    return valid;
  }

  $('#callsignInput')?.addEventListener('input', () => {
    updateCalculatedPasscode(true);
    validateCallsignField();
    refreshRequiredFieldHighlights();
  });
  $('#callsignInput')?.addEventListener('change', () => {
    updateCalculatedPasscode(true);
    validateCallsignField();
    refreshRequiredFieldHighlights();
  });

  function configFormSnapshot() {
    const form = $('#configForm');
    if (!form) return '';
    const data = {};
    for (const el of [...form.elements]) {
      if (!el.name || el.type === 'file' || el.type === 'submit' || el.type === 'button') continue;
      data[el.name] = el.type === 'checkbox' ? !!el.checked : String(el.value ?? '');
    }
    return JSON.stringify(Object.keys(data).sort().reduce((acc, key) => { acc[key] = data[key]; return acc; }, {}));
  }

  function markConfigDirty() {
    if (!state.configLoaded || state.configLoading) return;
    state.configDirty = configFormSnapshot() !== state.configBaseline;
  }

  async function loadConfig() {
    state.configLoading = true;
    try {
      const cfg = await api('/api/config');
      state.currentConfig = cfg;
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
      state.messagePopupSeconds = Math.min(60, Math.max(1, Number(cfg.message_popup_seconds || 5)));
      state.language = cfg.language === 'en' ? 'en' : 'pt-BR';
      if (!String(cfg.passcode || '').trim()) updateCalculatedPasscode(true);
      validateCallsignField();
      updateAltitudeSourceStatus(cfg.altitude_source, cfg.altitude);
      applyMapPreferences(cfg);
      applyAppearancePreferences(cfg);
      syncMapPreferenceControls();
      syncAppearanceControls();
      syncDmsFromDecimal();
      applyCoordinateMode(localStorage.getItem('pt2vhf_coordinate_mode') || 'decimal');
      applyLanguage(state.language);
      state.configLoaded = true;
      state.configBaseline = configFormSnapshot();
      state.configDirty = false;
      await refreshPendingUpdateStatus();
    } catch (err) { toast(err.message, 'error'); }
    finally { state.configLoading = false; }
  }

  async function saveConfigForm() {
    const form = $('#configForm');
    syncDecimalFromDmsIfNeeded();
    const data = Object.fromEntries(new FormData(form).entries());
    data.connect_on_start = !!form.elements.connect_on_start?.checked;
    data.open_browser_on_start = !!form.elements.open_browser_on_start?.checked;
    data.sound_on_personal_message = !!form.elements.sound_on_personal_message?.checked;
    data.check_updates_on_start = !!form.elements.check_updates_on_start?.checked;
    data.auto_download_updates = !!form.elements.auto_download_updates?.checked;
    data.install_updates_on_exit = !!form.elements.install_updates_on_exit?.checked;

    const filterValidation = validateAprsFilterSyntax(data.aprs_filter || '');
    if (!filterValidation.valid) {
      toast(ui(
        `Filtro APRS-IS inválido: ${filterValidation.invalid.join(', ')}`,
        `Invalid APRS-IS filter: ${filterValidation.invalid.join(', ')}`
      ), 'error');
      $('#aprsFilterInput')?.focus();
      return false;
    }

    if (!String(data.aprs_filter || '').trim()) {
      const proceed = window.confirm(ui(
        'O filtro APRS-IS está vazio. Dependendo do servidor e da porta utilizados, o cliente poderá receber um volume muito maior de tráfego, inclusive todo o fluxo disponibilizado nessa conexão.\n\nDeseja continuar sem filtro?',
        'The APRS-IS filter is empty. Depending on the server and port in use, the client may receive a much larger traffic stream, including all traffic made available on that connection.\n\nDo you want to continue without a filter?'
      ));
      if (!proceed) {
        showConfigSection('aprs');
        $('#aprsFilterInput')?.focus();
        return false;
      }
    }

    try {
      const result = await api('/api/config', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data)
      });
      toast(
        result.reconnected
          ? ui('Configuração salva. APRS-IS reconectando com os novos parâmetros.', 'Configuration saved. APRS-IS is reconnecting with the new parameters.')
          : ui('Configuração salva no banco local.', 'Configuration saved to the local database.'),
        'ok'
      );
      applyMapPreferences(result.config || data);
      applyAppearancePreferences(result.config || data);
      await loadConfig();
      await loadStations();
      state.configDirty = false;
      return true;
    } catch (err) {
      toast(err.message, 'error');
      return false;
    }
  }

  $('#configForm').addEventListener('submit', async e => {
    e.preventDefault();
    await saveConfigForm();
  });
  $('#configForm').addEventListener('input', markConfigDirty);
  $('#configForm').addEventListener('change', markConfigDirty);

  $('#unsavedSaveButton')?.addEventListener('click', async () => {
    const target = state.pendingTab;
    if (await saveConfigForm()) {
      $('#unsavedConfigModal')?.classList.add('hidden');
      state.pendingTab = '';
      if (target) activateTab(target);
    }
  });
  $('#unsavedDiscardButton')?.addEventListener('click', async () => {
    const target = state.pendingTab;
    await loadConfig();
    $('#unsavedConfigModal')?.classList.add('hidden');
    state.pendingTab = '';
    if (target) activateTab(target);
  });
  $('#unsavedCancelButton')?.addEventListener('click', () => {
    $('#unsavedConfigModal')?.classList.add('hidden');
    state.pendingTab = '';
  });

  $('#sendBeaconButton')?.addEventListener('click', async () => {
    const altitude = Number($('#altitudeInput')?.value);
    const source = String($('#altitudeSourceInput')?.value || '');
    if (altitude === 0 && source === 'fallback_zero') {
      toast(ui(
        'A altitude ainda está em 0 m porque não foi obtida automaticamente. O beacon será enviado, mas recomendamos informar a altitude real.',
        'Altitude is still 0 m because it was not obtained automatically. The beacon will be sent, but entering the real altitude is recommended.'
      ), 'error');
    }
    try {
      await api('/api/beacon', { method:'POST' });
      toast(ui('Beacon enviado ao APRS-IS.', 'Beacon sent to APRS-IS.'), 'ok');
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
    const topologyRfColor = form.elements.namedItem('topology_rf_color');
    const topologyRfColorText = $('#topologyRfColorText');
    const topologyIgateColor = form.elements.namedItem('topology_igate_color');
    const topologyIgateColorText = $('#topologyIgateColorText');
    const topologyWidth = form.elements.namedItem('topology_width');
    const topologyWidthValue = $('#topologyWidthValue');

    if (colorInput && colorText) colorText.value = colorInput.value || '#3ba6ff';
    if (widthInput && widthValue) widthValue.textContent = `${widthInput.value || 2} px`;
    if (brightnessInput && brightnessValue) brightnessValue.textContent = `${brightnessInput.value || 100}%`;
    if (topologyRfColor && topologyRfColorText) topologyRfColorText.value = topologyRfColor.value || '#35a7ff';
    if (topologyIgateColor && topologyIgateColorText) topologyIgateColorText.value = topologyIgateColor.value || '#b06cff';
    if (topologyWidth && topologyWidthValue) topologyWidthValue.textContent = `${topologyWidth.value || 2} px`;
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

  function previewTopologyStyleFromForm() {
    const form = $('#configForm');
    if (!form) return;
    state.mapConfig.topology_rf_color = form.elements.namedItem('topology_rf_color')?.value || '#35a7ff';
    state.mapConfig.topology_igate_color = form.elements.namedItem('topology_igate_color')?.value || '#b06cff';
    state.mapConfig.topology_width = Number(form.elements.namedItem('topology_width')?.value || 2);
    syncMapPreferenceControls();
    if (state.topologyEnabled) loadTopology();
  }

  function bindTopologyColor(name, textSelector) {
    const colorInput = $('#configForm')?.elements.namedItem(name);
    const textInput = $(textSelector);
    colorInput?.addEventListener('input', () => {
      if (textInput) textInput.value = colorInput.value;
      previewTopologyStyleFromForm();
    });
    textInput?.addEventListener('input', () => {
      let value = textInput.value.trim();
      if (!value.startsWith('#')) value = '#' + value;
      if (/^#[0-9a-fA-F]{6}$/.test(value) && colorInput) {
        colorInput.value = value;
        previewTopologyStyleFromForm();
      }
    });
  }

  bindTopologyColor('topology_rf_color', '#topologyRfColorText');
  bindTopologyColor('topology_igate_color', '#topologyIgateColorText');
  $('#topologyWidth')?.addEventListener('input', previewTopologyStyleFromForm);

  $('#resetTopologyStyleButton')?.addEventListener('click', () => {
    const form = $('#configForm');
    if (!form) return;
    form.elements.namedItem('topology_rf_color').value = '#35a7ff';
    form.elements.namedItem('topology_igate_color').value = '#b06cff';
    form.elements.namedItem('topology_width').value = '2';
    previewTopologyStyleFromForm();
    toast('Visual da topologia restaurado ao padrão. Clique em Salvar configuração para persistir.', 'ok');
  });

  function syncAppearanceControls() {
    const form = $('#configForm');
    if (!form) return;
    const pairs = [
      ['messages_font_size', '#messagesFontSizeValue', v => `${v || 12} px`],
      ['stations_font_size', '#stationsFontSizeValue', v => `${v || 12} px`],
      ['logs_font_size', '#logsFontSizeValue', v => `${v || 12} px`],
      ['messages_line_height', '#messagesLineHeightValue', v => `${Number(v || 1.35).toLocaleString(currentLocale(), {minimumFractionDigits:2, maximumFractionDigits:2})}×`],
      ['stations_line_height', '#stationsLineHeightValue', v => `${Number(v || 1.25).toLocaleString(currentLocale(), {minimumFractionDigits:2, maximumFractionDigits:2})}×`],
      ['logs_line_height', '#logsLineHeightValue', v => `${Number(v || 1.30).toLocaleString(currentLocale(), {minimumFractionDigits:2, maximumFractionDigits:2})}×`],
    ];
    for (const [name, selector, formatter] of pairs) {
      const input = form.elements.namedItem(name);
      const output = $(selector);
      if (input && output) output.textContent = formatter(input.value);
    }
  }

  function previewAppearanceFromForm() {
    const form = $('#configForm');
    if (!form) return;
    applyAppearancePreferences({
      app_theme: form.elements.namedItem('app_theme')?.value || 'dark',
      messages_font_family: form.elements.namedItem('messages_font_family')?.value || 'system',
      messages_font_size: form.elements.namedItem('messages_font_size')?.value || 12,
      messages_font_weight: form.elements.namedItem('messages_font_weight')?.value || 'normal',
      messages_line_height: form.elements.namedItem('messages_line_height')?.value || 1.35,
      stations_font_family: form.elements.namedItem('stations_font_family')?.value || 'system',
      stations_font_size: form.elements.namedItem('stations_font_size')?.value || 12,
      stations_font_weight: form.elements.namedItem('stations_font_weight')?.value || 'normal',
      stations_line_height: form.elements.namedItem('stations_line_height')?.value || 1.25,
      logs_font_family: form.elements.namedItem('logs_font_family')?.value || 'consolas',
      logs_font_size: form.elements.namedItem('logs_font_size')?.value || 12,
      logs_font_weight: form.elements.namedItem('logs_font_weight')?.value || 'normal',
      logs_line_height: form.elements.namedItem('logs_line_height')?.value || 1.30
    });
    state.language = form.elements.namedItem('language')?.value === 'en' ? 'en' : 'pt-BR';
    applyLanguage(state.language);
    syncAppearanceControls();
  }


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

  for (const name of [
    'app_theme','language',
    'messages_font_family','messages_font_size','messages_font_weight','messages_line_height',
    'stations_font_family','stations_font_size','stations_font_weight','stations_line_height',
    'logs_font_family','logs_font_size','logs_font_weight','logs_line_height'
  ]) {
    const el = $('#configForm')?.elements.namedItem(name);
    el?.addEventListener('input', previewAppearanceFromForm);
    el?.addEventListener('change', previewAppearanceFromForm);
  }

  function resetTypography(prefix, defaults) {
    const form = $('#configForm');
    if (!form) return;
    for (const [suffix, value] of Object.entries(defaults)) {
      const el = form.elements.namedItem(`${prefix}_${suffix}`);
      if (el) el.value = String(value);
    }
    previewAppearanceFromForm();
    toast(ui('Formatação restaurada ao padrão. Clique em Salvar para persistir.', 'Formatting restored to defaults. Click Save to persist.'), 'ok');
  }
  $('#resetMessagesTypography')?.addEventListener('click', () => resetTypography('messages', {font_family:'system',font_size:12,font_weight:'normal',line_height:1.35}));
  $('#resetStationsTypography')?.addEventListener('click', () => resetTypography('stations', {font_family:'system',font_size:12,font_weight:'normal',line_height:1.25}));
  $('#resetLogsTypography')?.addEventListener('click', () => resetTypography('logs', {font_family:'consolas',font_size:12,font_weight:'normal',line_height:1.30}));

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


  const EN_TEXT = new Map(Object.entries({
    'MAPA':'MAP',
    'Mensagens':'Messages',
    'Estações':'Stations',
    'Configuração':'Settings',
    'Ajuda':'Help',
    'Estações recebidas:':'Stations received:',
    'Pacotes APRS-IS:':'APRS-IS packets:',
    'Conectar':'Connect',
    'Desconectar':'Disconnect',
    'Desconectado':'Disconnected',
    'Verificando versão…':'Checking version…',
    'Mensagens APRS':'APRS Messages',
    'Ocultar telemetria':'Hide telemetry',
    'Agrupar por remetente':'Group by sender',
    'Minhas mensagens':'My messages',
    'Limpar mensagens':'Clear messages',
    'Filtro por origem':'Source filter',
    'De':'From',
    'Para':'To',
    'Tipo':'Type',
    'Mensagem':'Message',
    'Hora':'Time',
    'Status':'Status',
    'Conversas':'Conversations',
    'Conversa com':'Conversation with',
    'Tipo':'Type',
    'Destino':'Destination',
    'Boletim geral':'General bulletin',
    'Boletim de grupo':'Group bulletin',
    'Linha':'Line',
    'Grupo':'Group',
    'Enviar':'Send',
    'Últimos dados conhecidos de cada estação recebida.':'Latest known data for each received station.',
    'Limpar tracklogs':'Clear tracklogs',
    'Limpar estações':'Clear stations',
    'Filtro':'Filter',
    'Indicativo':'Callsign',
    'Última recepção':'Last heard',
    'Distância':'Distance',
    'Velocidade':'Speed',
    'Curso':'Course',
    'Altitude':'Altitude',
    'Informação':'Information',
    'Log APRS-IS':'APRS-IS Log',
    'Pesquisar no Log':'Search log',
    'Direção':'Direction',
    'Linhas':'Lines',
    'Todos':'All',
    'Acompanhar mais recentes no topo':'Keep newest at top',
    'Limpar log':'Clear log',
    'Os dados ficam persistidos no SQLite local. Para transmitir ao APRS-IS, a conexão precisa estar verificada.':'Data is stored in the local SQLite database. To transmit to APRS-IS, the connection must be verified.',
    'APRS / Estação':'APRS / Station',
    'Aplicativo':'Application',
    'Estação':'Station',
    'Obrigatório':'Required',
    'Passcode APRS-IS':'APRS-IS passcode',
    'SSID':'SSID',
    'Comentário':'Comment',
    'Formato das coordenadas':'Coordinate format',
    'Decimal':'Decimal',
    'Graus / minutos / segundos':'Degrees / minutes / seconds',
    'Usar minha localização atual':'Use my current location',
    'Latitude':'Latitude',
    'Longitude':'Longitude',
    'Graus':'Degrees',
    'Min':'Min',
    'Seg':'Sec',
    'Altitude (m)':'Altitude (m)',
    'E-mail':'Email',
    'Ícone APRS':'APRS icon',
    'Escolher ícone':'Choose icon',
    'Servidor':'Server',
    'Porta':'Port',
    'Filtro APRS-IS':'APRS-IS filter',
    'Beacon (minutos)':'Beacon (minutes)',
    'Conectar ao iniciar':'Connect at startup',
    'Editor gráfico de filtro':'Graphical filter editor',
    'Abrir editor':'Open editor',
    'Fechar editor':'Close editor',
    'Raio a partir da posição da estação (km)':'Radius from station position (km)',
    'Prefixos de indicativo':'Callsign prefixes',
    'Indicativos exatos':'Exact callsigns',
    'Tipos de pacote':'Packet types',
    'Posição':'Position',
    'Meteorologia':'Weather',
    'Telemetria':'Telemetry',
    'Objetos':'Objects',
    'Itens':'Items',
    'Gerar filtro':'Generate filter',
    'Restaurar r/2000':'Restore r/2000',
    'Salvar configuração APRS':'Save APRS settings',
    'Enviar beacon agora':'Send beacon now',
    'Mapa':'Map',
    'Tipo de mapa':'Map type',
    'Cor dos tracklogs':'Tracklog color',
    'Espessura dos tracklogs':'Tracklog width',
    'Brilho do mapa':'Map brightness',
    'Cor da topologia RF':'RF topology color',
    'Cor da topologia via IGate':'IGate topology color',
    'Espessura da topologia':'Topology width',
    'Restaurar topologia padrão':'Restore topology defaults',
    'Aparência e aplicativo':'Appearance and application',
    'Tema da aplicação':'Application theme',
    'Escuro - padrão':'Dark - default',
    'Claro':'Light',
    'Idioma / Language':'Language / Idioma',
    'Português - padrão':'Portuguese - default',
    'English':'English',
    'Abrir também no navegador ao iniciar':'Also open in browser at startup',
    'Fonte':'Font',
    'Tamanho':'Size',
    'Tocar sinal sonoro ao receber mensagem para minha estação':'Play a sound when a message for my station arrives',
    'Duração do aviso na aba Mensagens':'Alert duration in Messages tab',
    'Salvar configurações do aplicativo':'Save application settings',
    'Backup da configuração':'Configuration backup',
    'Salvar em arquivo':'Save to file',
    'Recuperar de arquivo':'Restore from file',
    'Primeiros passos':'Getting started',
    'Configure sua estação antes de conectar ao APRS-IS':'Configure your station before connecting to APRS-IS',
    'Abrir Configuração':'Open Settings',
    'Dúvidas, dificuldades ou sugestões?':'Questions, problems or suggestions?',
    'Fale comigo':'Contact me',
    'Nova mensagem APRS':'New APRS message',
    'Mensagem para esta estação':'Message for this station',
    'Responder':'Reply',
    'Fechar aviso':'Close alert',
    'OK':'OK',
    'Topologia observada':'Observed topology'
  }));


  Object.entries({
    'Grupo de configurações':'Settings group',
    'Campos marcados como':'Fields marked as',
    'precisam ser preenchidos antes de conectar ao APRS-IS.':'must be filled in before connecting to APRS-IS.',
    'calculado automaticamente':'calculated automatically',
    'Calculado automaticamente pelo indicativo-base; o SSID não altera o código.':'Calculated automatically from the base callsign; SSID does not change the code.',
    'Os valores em graus/minutos/segundos são convertidos automaticamente para decimal antes de salvar.':'Degrees/minutes/seconds values are automatically converted to decimal before saving.',
    'opcional':'optional',
    'usa sua latitude/longitude configuradas como centro e recebe estações em um raio de 2.000 km. O campo continua totalmente editável para filtros manuais.':'uses your configured latitude/longitude as the center and receives stations within a 2,000 km radius. The field remains fully editable for manual filters.',
    'Monte os componentes abaixo e gere a string APRS-IS automaticamente.':'Choose the components below and generate the APRS-IS filter string automatically.',
    'Gera':'Generates',
    'Se o filtro for deixado vazio, o programa pedirá confirmação antes de salvar. Dependendo do servidor/porta, isso pode resultar em um fluxo de tráfego muito amplo.':'If the filter is left empty, the program will ask for confirmation before saving. Depending on the server/port, this can result in a very broad traffic stream.',
    'Satélite — Esri World Imagery':'Satellite - Esri World Imagery',
    'Cor dos enlaces RF':'RF link color',
    'Cor dos enlaces IGate':'IGate link color',
    'Padrão: RF #35a7ff, IGate #b06cff, 2 px.':'Default: RF #35a7ff, IGate #b06cff, 2 px.',
    'OpenStreetMap e OpenTopoMap usam cartografia colaborativa. A opção Satélite usa Esri World Imagery. Cores e espessura da topologia são aplicadas imediatamente e persistidas ao salvar.':'OpenStreetMap and OpenTopoMap use collaborative cartography. Satellite mode uses Esri World Imagery. Topology colors and width are applied immediately and persisted when saving.',
    'A alteração é aplicada imediatamente e fica salva após clicar em Salvar.':'The change is applied immediately and persisted after clicking Save.',
    'O idioma é aplicado imediatamente à interface.':'The language is applied immediately to the interface.',
    'Sistema':'System',
    'Tempo, em segundos, antes do pequeno aviso fechar automaticamente. Ele também pode ser fechado manualmente.':'Time in seconds before the compact alert closes automatically. It can also be closed manually.',
    'Tema, idioma, fontes e tamanhos são aplicados à interface e persistidos no banco local.':'Theme, language, fonts and sizes are applied to the interface and stored in the local database.',
    'O arquivo exportado contém o passcode APRS-IS em texto legível. Guarde-o em local seguro.':'The exported file contains the APRS-IS passcode in readable text. Keep it in a secure location.',
    'Guia rápido para configurar, usar e diagnosticar o PT2VHF APRS Client.':'Quick guide to configure, use and troubleshoot PT2VHF APRS Client.',
    'Na aba':'In the',
    'informe seu indicativo, SSID, posição e parâmetros APRS-IS. O passcode é calculado automaticamente a partir do indicativo-base.':'tab, enter your callsign, SSID, position and APRS-IS parameters. The passcode is calculated automatically from the base callsign.',
    '1. Estação':'1. Station',
    '2. APRS-IS':'2. APRS-IS',
    '3. Mapa':'3. Map',
    '4. Mensagens e boletins':'4. Messages and bulletins',
    '5. Estações':'5. Stations',
    '6. Log APRS-IS':'6. APRS-IS Log',
    '7. Atualizações':'7. Updates',
    '8. Banco e backup':'8. Database and backup',
    'Diagnóstico rápido':'Quick troubleshooting',
    'Indicativo:':'Callsign:',
    'informe o seu indicativo radioamador. O SSID identifica a finalidade da estação, por exemplo':'enter your amateur-radio callsign. The SSID identifies the station purpose, for example',
    'para móvel.':'for mobile.',
    'Passcode APRS-IS:':'APRS-IS passcode:',
    'é calculado automaticamente e aparece ao lado do indicativo. O SSID não muda esse código.':'is calculated automatically and appears next to the callsign. The SSID does not change this code.',
    'Latitude/Longitude:':'Latitude/Longitude:',
    'podem ser informadas em decimal ou graus/minutos/segundos. O botão':'can be entered in decimal or degrees/minutes/seconds. The button',
    'solicita a posição ao navegador/SO e preenche os campos quando autorizado. A altitude também é obrigatória para conectar.':'requests the location from the browser/OS and fills the fields when authorized. Altitude is also required to connect.',
    'Ícone APRS:':'APRS icon:',
    'escolha o símbolo adequado à sua estação ou veículo.':'choose the appropriate symbol for your station or vehicle.',
    'O servidor padrão é':'The default server is',
    'porta':'port',
    'Filtro de recepção:':'Receive filter:',
    'como configuração inicial, use':'for initial configuration, use',
    'O editor gráfico pode montar filtros radiais, por prefixo, indicativos exatos e tipos de pacote, mantendo o campo manual sempre disponível.':'The graphical editor can build radial, prefix, exact-callsign and packet-type filters while keeping the manual field always available.',
    'Se o filtro ficar vazio, o programa pede confirmação antes de salvar e explica o impacto potencial no volume de tráfego.':'If the filter is empty, the program asks for confirmation before saving and explains the potential impact on traffic volume.',
    'Se o Log mostrar':'If the Log shows',
    'revise o campo de filtro APRS-IS. Um texto livre como':'review the APRS-IS filter field. Free text such as',
    'não é um filtro APRS-IS válido.':'is not a valid APRS-IS filter.',
    'Marque':'Enable',
    'se quiser que o cliente tente conectar automaticamente.':'if you want the client to connect automatically.',
    'mantém a janela integrada e abre uma segunda visualização no navegador padrão. A opção vem desligada por padrão.':'keeps the integrated window and opens a second view in the default browser. This option is off by default.',
    'Escolha entre':'Choose between',
    'e':'and',
    'Satélite':'Satellite',
    'É possível ajustar':'You can adjust',
    'brilho do mapa':'map brightness',
    'cor':'color',
    'espessura dos tracklogs':'tracklog width',
    'além das':'as well as',
    'cores e espessura da topologia observada':'observed topology colors and width',
    'Clique em uma estação para abrir os detalhes. O botão':'Click a station to open its details. The button',
    'Enviar mensagem':'Send message',
    'leva diretamente à tela de mensagens com o destino preenchido.':'opens the message screen with the destination filled in.',
    'A posição e o zoom do mapa ficam salvos localmente.':'Map position and zoom are stored locally.',
    'Mensagem:':'Message:',
    'comunicação APRS direcionada a um indicativo, com suporte a ACK/REJ.':'APRS communication addressed to a callsign, with ACK/REJ support.',
    'Boletim geral:':'General bulletin:',
    'usa':'uses',
    'a':'to',
    'e não solicita ACK.':'and does not request an ACK.',
    'Boletim de grupo:':'Group bulletin:',
    'permite informar um grupo de até cinco caracteres.':'allows a group of up to five characters.',
    'O botão':'The',
    'mostra apenas mensagens individuais de ou para o seu':'button shows only individual messages from or to your',
    'As mensagens seguem fluxo de chat, com as mais novas embaixo. A opção':'Messages follow a chat flow, with the newest at the bottom. The',
    'organiza o histórico em conversas por contato.':'option organizes history into conversations by contact.',
    'Clique em qualquer indicativo nas colunas':'Click any callsign in the',
    'ou':'or',
    'para selecioná-lo como destinatário e responder. Se clicar no próprio indicativo, o programa tenta selecionar o outro participante.':'columns to select it as the recipient and reply. If you click your own callsign, the program tries to select the other participant.',
    'O compositor aceita mensagens longas. Use':'The composer accepts long messages. Use',
    'para enviar e':'to send and',
    'para nova linha. Mensagens maiores são divididas automaticamente em partes APRS numeradas, cada uma com confirmação própria.':'for a new line. Longer messages are automatically split into numbered APRS parts, each with its own confirmation.',
    'apaga todo o histórico local de mensagens e boletins após confirmação.':'deletes the entire local message and bulletin history after confirmation.',
    'Quando chega uma nova mensagem para sua estação e a aba Mensagens já está aberta, o programa usa um aviso pequeno e não bloqueante, que fecha automaticamente pelo tempo definido em Configuração. Fora da aba Mensagens, permanece o aviso completo com opção de responder.':'When a new message for your station arrives while the Messages tab is open, the program shows a small non-blocking alert that closes automatically after the configured time. Outside the Messages tab, the full alert remains available with a Reply option.',
    'A lista mostra indicativo, última recepção, distância, velocidade, curso, altitude e informações conhecidas.':'The list shows callsign, last heard, distance, speed, course, altitude and known information.',
    'Clique em uma linha para abrir o':'Click a row to open the',
    'centralizar a estação e mostrar o popup correspondente.':'center the station and show its popup.',
    'Os títulos das colunas podem ser clicados para alterar a ordenação.':'Column headers can be clicked to change sorting.',
    'apaga todas as estações e tracklogs locais; novas estações voltarão a aparecer quando forem recebidas.':'deletes all local stations and tracklogs; new stations will appear again when received.',
    'Fonte e tamanho da tabela podem ser ajustados em':'Table font and size can be adjusted under',
    'Aparência':'Appearance',
    'Use o Log para diagnosticar conexão, autenticação, filtro e tráfego recebido/transmitido.':'Use the Log to diagnose connection, authentication, filtering and received/transmitted traffic.',
    'indica dados recebidos e':'indicates received data and',
    'indica dados enviados.':'indicates transmitted data.',
    'confirma autenticação APRS-IS. Linhas iniciadas por':'confirms APRS-IS authentication. Lines starting with',
    'são mensagens de controle do servidor, não estações APRS.':'are server control messages, not APRS stations.',
    'O passcode é mascarado no Log.':'The passcode is masked in the Log.',
    'O cabeçalho informa se você está usando a':'The header indicates whether you are using the',
    'última versão':'latest version',
    'ou se existe uma':'or whether a',
    'nova versão':'new version',
    'publicada.':'is available.',
    'Quando houver atualização, clique no aviso para abrir a Release no GitHub.':'When an update is available, click the notice to open the GitHub Release.',
    'O instalador encerra automaticamente a versão anterior antes de substituir os arquivos.':'The installer automatically closes the previous version before replacing files.',
    'O banco SQLite fica em:':'The SQLite database is stored at:',
    'O instalador e o Portable EXE usam esse mesmo banco local.':'The installer and Portable EXE use the same local database.',
    'Em':'Under',
    'você pode salvar ou recuperar as preferências em JSON.':'you can save or restore preferences as JSON.',
    'O JSON exportado contém o passcode APRS-IS em texto legível. Guarde-o em local seguro.':'The exported JSON contains the APRS-IS passcode in readable text. Keep it in a secure location.',
    'Conecta, mas não aparecem estações':'Connects, but no stations appear',
    'Confira o filtro APRS-IS e procure erros de filtro no Log.':'Check the APRS-IS filter and look for filter errors in the Log.',
    'Não transmite':'Does not transmit',
    'Confira se a conexão está como verificada e se indicativo/passcode estão corretos.':'Check that the connection is verified and that callsign/passcode are correct.',
    'Mapa não carrega':'Map does not load',
    'Confira a conexão com a Internet; os tiles dos mapas são carregados de provedores externos.':'Check the Internet connection; map tiles are loaded from external providers.',
    'Distâncias incorretas':'Incorrect distances',
    'Confira latitude e longitude da sua estação em Configuração.':'Check your station latitude and longitude in Settings.',
    'Sem aviso sonoro':'No sound alert',
    'Confira a opção de som em Configuração → Aparência e o volume do Windows.':'Check the sound option under Settings > Appearance and the system volume.',
    'Se precisar de ajuda para configurar o programa, encontrou algum problema ou tem uma sugestão de melhoria, entre em contato.':'If you need help configuring the program, found a problem or have an improvement suggestion, get in touch.',
    'Escolher ícone APRS':'Choose APRS icon',
    'Tabela primária (/) e secundária (\\).':'Primary (/) and secondary (\\) table.',
    'Primária /':'Primary /',
    'Secundária \\':'Secondary \\'
  }).forEach(([key, value]) => EN_TEXT.set(key, value));

  function translateConnectionState(value) {
    const map = {
      'Desconectado':'Disconnected',
      'Desconectando...':'Disconnecting...',
      'Conectado; autenticando...':'Connected; authenticating...',
      'Conectado e verificado':'Connected and verified',
      'Conectado sem verificação':'Connected without verification',
      'Conexão perdida':'Connection lost',
      'Configuração incompleta':'Incomplete configuration',
      'Reconectando com a nova configuração...':'Reconnecting with new settings...'
    };
    return state.language === 'en' ? (map[value] || value) : value;
  }

  function translateDom(root = document.body) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const parent = node.parentElement;
      if (!parent || ['SCRIPT','STYLE','CODE'].includes(parent.tagName)) continue;
      if (node._pt2vhfOriginalText === undefined) node._pt2vhfOriginalText = node.nodeValue;
      const original = node._pt2vhfOriginalText;
      const trimmed = original.trim();
      if (!trimmed) continue;
      const translated = EN_TEXT.get(trimmed);
      const chosen = state.language === 'en' && translated ? translated : trimmed;
      const lead = original.match(/^\s*/)?.[0] || '';
      const trail = original.match(/\s*$/)?.[0] || '';
      node.nodeValue = lead + chosen + trail;
    }

    const attrs = ['placeholder', 'title', 'aria-label'];
    for (const el of root.querySelectorAll?.('*') || []) {
      for (const attr of attrs) {
        if (!el.hasAttribute(attr)) continue;
        const key = 'i18n' + attr.replace(/[^a-z0-9]/gi,'_');
        if (!(key in el.dataset)) el.dataset[key] = el.getAttribute(attr) || '';
        const original = el.dataset[key];
        const translated = EN_TEXT.get(original);
        el.setAttribute(attr, state.language === 'en' && translated ? translated : original);
      }
    }
  }

  function applyLanguage(language) {
    state.language = language === 'en' ? 'en' : 'pt-BR';
    document.documentElement.lang = state.language === 'en' ? 'en' : 'pt-BR';
    translateDom(document.body);
    refreshStatus();
    if (state.messages.length) renderMessages();
    if (state.stations.length) renderStations();
  }

  const languageObserver = new MutationObserver(records => {
    if (state.language !== 'en') return;
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE) translateDom(node);
      }
    }
  });
  languageObserver.observe(document.body, { childList: true, subtree: true });

  function showConfigSection(_section) {
    state.configSection = 'all';
    $$('.config-section').forEach(el => el.classList.remove('hidden'));
  }
  showConfigSection('all');

  function requiredStationDefinitions() {
    syncDecimalFromDmsIfNeeded();
    const form = $('#configForm');
    return [
      { key: 'callsign', labelPt: 'Indicativo', labelEn: 'Callsign', input: form?.elements.namedItem('callsign') },
      { key: 'latitude', labelPt: 'Latitude', labelEn: 'Latitude', input: form?.elements.namedItem('latitude') },
      { key: 'longitude', labelPt: 'Longitude', labelEn: 'Longitude', input: form?.elements.namedItem('longitude') },
      { key: 'altitude', labelPt: 'Altitude', labelEn: 'Altitude', input: form?.elements.namedItem('altitude') },
    ];
  }

  function missingRequiredStationFields() {
    return requiredStationDefinitions().filter(item => !String(item.input?.value ?? '').trim());
  }

  function clearRequiredFieldHighlights() {
    $$('.required-field-missing').forEach(el => el.classList.remove('required-field-missing'));
  }

  function highlightMissingRequiredFields(missing) {
    clearRequiredFieldHighlights();
    for (const item of missing) {
      if (item.key === 'latitude' || item.key === 'longitude') {
        $('#coordinateDecimalFields')?.classList.add('required-field-missing');
        $('#coordinateDmsFields')?.classList.add('required-field-missing');
      } else {
        item.input?.closest('.field')?.classList.add('required-field-missing');
      }
    }
  }

  function refreshRequiredFieldHighlights() {
    const modalOpen = !$('#requiredFieldsModal')?.classList.contains('hidden');
    const highlighted = $$('.required-field-missing').length > 0;
    if (!modalOpen && !highlighted) return;
    const missing = missingRequiredStationFields();
    highlightMissingRequiredFields(missing);
    if (!missing.length) $('#requiredFieldsModal')?.classList.add('hidden');
  }

  function showRequiredFieldsModal(missing = missingRequiredStationFields()) {
    if (!missing.length) return false;
    highlightMissingRequiredFields(missing);
    const names = missing.map(item => state.language === 'en' ? item.labelEn : item.labelPt);
    const message = $('#requiredFieldsMessage');
    const list = $('#requiredFieldsList');
    if (message) message.textContent = ui(
      'Antes de conectar ao APRS-IS, complete os campos obrigatórios abaixo.',
      'Before connecting to APRS-IS, complete the required fields below.'
    );
    if (list) list.innerHTML = names.map(name => `<span>${escapeHtml(name)}</span>`).join('');
    $('#requiredFieldsModal')?.classList.remove('hidden');
    return true;
  }

  function guideToRequiredStationFields(missing = missingRequiredStationFields()) {
    $('#requiredFieldsModal')?.classList.add('hidden');
    $('.tab[data-tab="config"]')?.click();
    setTimeout(() => {
      showConfigSection('aprs');
      highlightMissingRequiredFields(missing);
      const first = missing[0];
      let focusTarget = first?.input;
      if (first?.key === 'latitude') {
        focusTarget = $('#coordinateInputMode')?.value === 'dms' ? $('#latDeg') : $('#latitudeDecimal');
      } else if (first?.key === 'longitude') {
        focusTarget = $('#coordinateInputMode')?.value === 'dms' ? $('#lonDeg') : $('#longitudeDecimal');
      }
      focusTarget?.focus();
      focusTarget?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      toast(ui(
        'Complete os campos realçados para conectar.',
        'Complete the highlighted fields to connect.'
      ), 'error');
    }, 100);
  }

  $('#requiredFieldsGoConfig')?.addEventListener('click', () => guideToRequiredStationFields());
  $('#requiredFieldsClose')?.addEventListener('click', () => $('#requiredFieldsModal')?.classList.add('hidden'));


  function decimalToDms(value, lat) {
    const number = Number(value);
    if (!Number.isFinite(number)) return null;
    const abs = Math.abs(number);
    const deg = Math.floor(abs);
    const minFloat = (abs - deg) * 60;
    const min = Math.floor(minFloat);
    const sec = (minFloat - min) * 60;
    return { deg, min, sec, hem: lat ? (number < 0 ? 'S' : 'N') : (number < 0 ? 'W' : 'E') };
  }

  function dmsToDecimal(deg, min, sec, hem) {
    const d = Number(deg), m = Number(min), s = Number(sec);
    if (![d,m,s].every(Number.isFinite) || d < 0 || m < 0 || m >= 60 || s < 0 || s >= 60) return null;
    let value = d + m / 60 + s / 3600;
    if (hem === 'S' || hem === 'W') value *= -1;
    return value;
  }

  function syncDmsFromDecimal() {
    const lat = decimalToDms($('#latitudeDecimal')?.value, true);
    const lon = decimalToDms($('#longitudeDecimal')?.value, false);
    if (lat) {
      $('#latDeg').value = lat.deg; $('#latMin').value = lat.min; $('#latSec').value = lat.sec.toFixed(4); $('#latHem').value = lat.hem;
    }
    if (lon) {
      $('#lonDeg').value = lon.deg; $('#lonMin').value = lon.min; $('#lonSec').value = lon.sec.toFixed(4); $('#lonHem').value = lon.hem;
    }
  }

  function syncDecimalFromDmsIfNeeded() {
    if ($('#coordinateInputMode')?.value !== 'dms') return true;
    const lat = dmsToDecimal($('#latDeg')?.value, $('#latMin')?.value, $('#latSec')?.value, $('#latHem')?.value);
    const lon = dmsToDecimal($('#lonDeg')?.value, $('#lonMin')?.value, $('#lonSec')?.value, $('#lonHem')?.value);
    if (lat !== null) $('#latitudeDecimal').value = lat.toFixed(6);
    if (lon !== null) $('#longitudeDecimal').value = lon.toFixed(6);
    return lat !== null && lon !== null;
  }

  function applyCoordinateMode(mode) {
    const selected = mode === 'dms' ? 'dms' : 'decimal';
    if ($('#coordinateInputMode')) $('#coordinateInputMode').value = selected;
    $('#coordinateDecimalFields')?.classList.toggle('hidden', selected !== 'decimal');
    $('#coordinateDmsFields')?.classList.toggle('hidden', selected !== 'dms');
    localStorage.setItem('pt2vhf_coordinate_mode', selected);
    if (selected === 'dms') syncDmsFromDecimal();
  }

  $('#coordinateInputMode')?.addEventListener('change', e => applyCoordinateMode(e.target.value));
  for (const id of ['latDeg','latMin','latSec','latHem','lonDeg','lonMin','lonSec','lonHem']) {
    $('#' + id)?.addEventListener('input', () => {
      syncDecimalFromDmsIfNeeded();
      refreshRequiredFieldHighlights();
    });
    $('#' + id)?.addEventListener('change', () => {
      syncDecimalFromDmsIfNeeded();
      refreshRequiredFieldHighlights();
    });
  }
  $('#latitudeDecimal')?.addEventListener('change', syncDmsFromDecimal);
  $('#longitudeDecimal')?.addEventListener('change', syncDmsFromDecimal);

  function updateAltitudeSourceStatus(source, altitude) {
    const status = $('#altitudeSourceStatus');
    const field = $('#altitudeField');
    const value = Number(altitude);
    const fallback = source === 'fallback_zero' && value === 0;
    field?.classList.toggle('altitude-fallback-zero', fallback);
    if (!status) return;
    if (fallback) {
      status.textContent = ui(
        'Altitude não disponível automaticamente. Foi usado 0 m para não impedir a conexão. Recomendamos informar a altitude real da estação.',
        'Altitude was not available automatically. 0 m was used so the connection is not blocked. We recommend entering the station\'s actual altitude.'
      );
    } else if (source === 'geolocation' && Number.isFinite(value)) {
      status.textContent = ui('Altitude fornecida pela localização do sistema. Revise se necessário.', 'Altitude provided by system location. Review if needed.');
    } else {
      status.textContent = ui('Informe a altitude real da estação sempre que possível.', 'Enter the station\'s actual altitude whenever possible.');
    }
  }

  $('#altitudeInput')?.addEventListener('input', () => {
    const source = $('#altitudeSourceInput');
    if (source) source.value = 'manual';
    updateAltitudeSourceStatus('manual', $('#altitudeInput')?.value);
    refreshRequiredFieldHighlights();
  });
  $('#latitudeDecimal')?.addEventListener('input', refreshRequiredFieldHighlights);
  $('#longitudeDecimal')?.addEventListener('input', refreshRequiredFieldHighlights);

  function applyUserLocation(position, { fillStation = true, centerMap = true } = {}) {
    const lat = Number(position.coords.latitude);
    const lon = Number(position.coords.longitude);
    const altRaw = position.coords.altitude;
    const alt = altRaw === null || altRaw === undefined ? NaN : Number(altRaw);
    const accuracy = Number(position.coords.accuracy);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) throw new Error(ui('Localização inválida.', 'Invalid location.'));

    if (centerMap && state.map) {
      const point = [lat, lon];
      state.map.setView(point, Math.max(Number(state.map.getZoom() || 0), 13), { animate: true });
      if (state.userLocationMarker) state.userLocationMarker.setLatLng(point);
      else {
        state.userLocationMarker = L.marker(point, {
          icon: L.divIcon({
            className: '',
            html: '<div class="user-location-dot"></div>',
            iconSize: [18, 18],
            iconAnchor: [9, 9]
          }),
          title: ui('Minha localização', 'My location'),
          zIndexOffset: 1000
        }).addTo(state.map).bindPopup(ui('Minha localização', 'My location'));
      }
      if (Number.isFinite(accuracy) && accuracy > 0) {
        if (state.userLocationAccuracy) state.userLocationAccuracy.setLatLng(point).setRadius(accuracy);
        else state.userLocationAccuracy = L.circle(point, {
          radius: accuracy, weight: 1, opacity: .75, fillOpacity: .08
        }).addTo(state.map);
      }
    }

    let altitudeSource = String($('#altitudeSourceInput')?.value || state.currentConfig?.altitude_source || 'manual');
    let altitudeValue = String($('#altitudeInput')?.value || '').trim();

    if (fillStation) {
      $('#latitudeDecimal').value = lat.toFixed(6);
      $('#longitudeDecimal').value = lon.toFixed(6);

      const existingAltitudeIsManual = altitudeValue !== '' && altitudeSource === 'manual';
      if (!existingAltitudeIsManual) {
        if (Number.isFinite(alt)) {
          altitudeValue = alt.toFixed(1);
          altitudeSource = 'geolocation';
        } else {
          altitudeValue = '0';
          altitudeSource = 'fallback_zero';
        }
        $('#altitudeInput').value = altitudeValue;
        if ($('#altitudeSourceInput')) $('#altitudeSourceInput').value = altitudeSource;
      }
      syncDmsFromDecimal();
      updateAltitudeSourceStatus(altitudeSource, altitudeValue);
      refreshRequiredFieldHighlights();
    }

    const status = $('#currentLocationStatus');
    if (status) {
      const accuracyText = Number.isFinite(accuracy)
        ? ui(`Precisão aproximada: ${Math.round(accuracy)} m.`, `Approximate accuracy: ${Math.round(accuracy)} m.`)
        : ui('Posição obtida.', 'Location obtained.');
      status.textContent = accuracyText + (altitudeSource === 'fallback_zero'
        ? ' ' + ui('Altitude indisponível; usado 0 m. Recomendamos corrigir.', 'Altitude unavailable; 0 m was used. We recommend correcting it.')
        : '');
    }

    return { lat, lon, altitude: Number(altitudeValue), altitudeSource, accuracy };
  }

  function geolocationErrorText(error) {
    const pt = {1:'Permissão de localização negada.',2:'Não foi possível determinar a localização.',3:'A localização demorou demais para responder.'};
    const en = {1:'Location permission was denied.',2:'Unable to determine location.',3:'Location request timed out.'};
    return (state.language === 'en' ? en : pt)[error?.code] || ui('Falha ao obter a localização.', 'Unable to obtain location.');
  }

  function requestUserLocation(options = {}) {
    const {
      fillStation = true,
      centerMap = true,
      persist = false,
      confirmOverwrite = false,
      button = null,
      automatic = false,
    } = options;

    if (!navigator.geolocation) {
      const message = ui('Localização não disponível neste ambiente. Preencha as coordenadas manualmente.', 'Location is unavailable in this environment. Enter coordinates manually.');
      if ($('#currentLocationStatus')) $('#currentLocationStatus').textContent = message;
      if (!automatic) toast(message, 'error');
      return Promise.resolve(null);
    }

    if (confirmOverwrite) {
      syncDecimalFromDmsIfNeeded();
      const currentLat = String($('#latitudeDecimal')?.value || '').trim();
      const currentLon = String($('#longitudeDecimal')?.value || '').trim();
      if ((currentLat || currentLon) && !window.confirm(ui(
        'Já existem coordenadas preenchidas. Deseja substituí-las pela sua localização atual?',
        'Coordinates are already filled in. Replace them with your current location?'
      ))) return Promise.resolve(null);
    }

    if (button) {
      button.disabled = true;
      button.textContent = ui('Localizando…', 'Locating…');
    }
    if ($('#currentLocationStatus')) $('#currentLocationStatus').textContent = ui('Solicitando localização…', 'Requesting location…');

    return new Promise(resolve => {
      navigator.geolocation.getCurrentPosition(async position => {
        try {
          const result = applyUserLocation(position, { fillStation, centerMap });
          if (persist && fillStation) {
            const payload = {
              ...(state.currentConfig || {}),
              latitude: result.lat,
              longitude: result.lon,
              altitude: Number.isFinite(result.altitude) ? result.altitude : 0,
              altitude_source: result.altitudeSource,
            };
            const saved = await api('/api/config', {
              method: 'POST',
              headers: {'Content-Type':'application/json'},
              body: JSON.stringify(payload)
            });
            state.currentConfig = saved.config || payload;
          }
          if (!automatic) toast(ui('Localização atual aplicada.', 'Current location applied.'), 'ok');
          resolve(result);
        } catch (err) {
          if (!automatic) toast(err.message, 'error');
          resolve(null);
        } finally {
          if (button) {
            button.disabled = false;
            button.textContent = ui('Usar minha localização atual', 'Use my current location');
          }
        }
      }, error => {
        const message = geolocationErrorText(error);
        if ($('#currentLocationStatus')) $('#currentLocationStatus').textContent = message + ' ' + ui('Preencha as coordenadas manualmente.', 'Enter the coordinates manually.');
        if (!automatic) toast(message, 'error');
        if (button) {
          button.disabled = false;
          button.textContent = ui('Usar minha localização atual', 'Use my current location');
        }
        resolve(null);
      }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 });
    });
  }

  $('#useCurrentLocationButton')?.addEventListener('click', () => {
    requestUserLocation({
      fillStation: true,
      centerMap: true,
      persist: false,
      confirmOverwrite: true,
      button: $('#useCurrentLocationButton'),
      automatic: false,
    });
  });

  async function initializeAutomaticLocation() {
    if (state.autoLocationInProgress) return;
    if (localStorage.getItem('pt2vhf_initial_location_attempted') === '1') return;
    state.autoLocationInProgress = true;
    localStorage.setItem('pt2vhf_initial_location_attempted', '1');
    try {
      const missingCoordinates = !String($('#latitudeDecimal')?.value || '').trim()
        || !String($('#longitudeDecimal')?.value || '').trim();
      await requestUserLocation({
        fillStation: missingCoordinates,
        centerMap: true,
        persist: missingCoordinates,
        confirmOverwrite: false,
        automatic: true,
      });
    } finally {
      state.autoLocationInProgress = false;
    }
  }


  function splitFilterValues(value) {
    return String(value || '').toUpperCase().split(/[\s,;\/]+/).map(v => v.trim()).filter(Boolean);
  }

  function validateAprsFilterSyntax(value) {
    const terms = String(value || '').trim().split(/\s+/).filter(Boolean);
    const invalid = [];
    const unsupported = [];
    for (const term of terms) {
      const lower = term.toLowerCase();
      let ok = true;
      if (lower.startsWith('r/')) ok = /^r\/(?:\d+(?:\.\d+)?|-?\d+(?:\.\d+)?\/-?\d+(?:\.\d+)?\/\d+(?:\.\d+)?)$/i.test(term);
      else if (lower.startsWith('p/')) ok = /^p\/[a-z0-9]+(?:\/[a-z0-9]+)*$/i.test(term);
      else if (lower.startsWith('b/')) ok = /^b\/[a-z0-9-]+(?:\/[a-z0-9-]+)*$/i.test(term);
      else if (lower.startsWith('t/')) ok = /^t\/[a-z]+$/i.test(term);
      else if (lower.startsWith('a/')) ok = /^a\/-?\d+(?:\.\d+)?\/-?\d+(?:\.\d+)?\/-?\d+(?:\.\d+)?\/-?\d+(?:\.\d+)?$/i.test(term);
      else unsupported.push(term);
      if (!ok) invalid.push(term);
    }
    return { valid: invalid.length === 0, invalid, unsupported };
  }

  function parseFilterIntoBuilder() {
    const value = String($('#aprsFilterInput')?.value || '').trim();
    const terms = value.split(/\s+/).filter(Boolean);
    if ($('#filterBrazilOnly')) $('#filterBrazilOnly').checked = false;
    $('#filterRadiusKm').value = '';
    $('#filterRadiusLat').value = '';
    $('#filterRadiusLon').value = '';
    $('#filterPrefixes').value = '';
    $('#filterBuddies').value = '';
    for (const id of ['filterAreaNorth','filterAreaWest','filterAreaSouth','filterAreaEast']) if ($('#' + id)) $('#' + id).value = '';
    $$('.filter-type').forEach(input => { input.checked = false; });
    const unsupported = [];
    for (const term of terms) {
      const [kind, ...values] = term.split('/');
      const lower = String(kind || '').toLowerCase();
      if (lower === 'p' && values.length) {
        const normalized = values.map(v => v.toUpperCase());
        const isBrazil = BRAZIL_PREFIXES.every(p => normalized.includes(p)) && normalized.every(p => BRAZIL_PREFIXES.includes(p));
        if ($('#filterBrazilOnly')) $('#filterBrazilOnly').checked = isBrazil;
        if (!isBrazil) $('#filterPrefixes').value = normalized.join(', ');
      } else if (lower === 'b' && values.length) {
        $('#filterBuddies').value = values.join(', ').toUpperCase();
      } else if (lower === 'r' && values.length === 1) {
        $('#filterRadiusKm').value = values[0];
      } else if (lower === 'r' && values.length >= 3) {
        $('#filterRadiusLat').value = values[0];
        $('#filterRadiusLon').value = values[1];
        $('#filterRadiusKm').value = values[2];
      } else if (lower === 't' && values.length) {
        for (const ch of values.join('')) {
          const input = document.querySelector(`.filter-type[value="${CSS.escape(ch)}"]`);
          if (input) input.checked = true;
        }
      } else if (lower === 'a' && values.length >= 4) {
        $('#filterAreaNorth').value = values[0];
        $('#filterAreaWest').value = values[1];
        $('#filterAreaSouth').value = values[2];
        $('#filterAreaEast').value = values[3];
      } else if (term) {
        unsupported.push(term);
      }
    }
    const validation = validateAprsFilterSyntax(value);
    const status = $('#filterBuilderParseStatus');
    if (status) {
      if (!validation.valid) status.textContent = ui(`Filtro com componente inválido: ${validation.invalid.join(', ')}`, `Filter has invalid component: ${validation.invalid.join(', ')}`);
      else if (unsupported.length || validation.unsupported.length) status.textContent = ui('A string contém componentes ainda não representados no editor. Eles serão preservados enquanto você não gerar uma nova string.', 'The string contains components not yet represented in the editor. They are preserved until you generate a new string.');
      else status.textContent = ui('Filtro interpretado pelo editor gráfico.', 'Filter interpreted by the graphical editor.');
    }
  }

  $('#toggleFilterBuilderButton')?.addEventListener('click', () => {
    const panel = $('#filterBuilderPanel');
    const hidden = panel.classList.toggle('hidden');
    $('#toggleFilterBuilderButton').textContent = hidden ? ui('Abrir editor', 'Open editor') : ui('Fechar editor', 'Close editor');
    if (!hidden) parseFilterIntoBuilder();
  });

  $('#aprsFilterInput')?.addEventListener('change', parseFilterIntoBuilder);

  $('#generateFilterButton')?.addEventListener('click', () => {
    syncDecimalFromDmsIfNeeded();
    const parts = [];
    const radiusText = String($('#filterRadiusKm')?.value || '').trim();
    const radius = radiusText ? Number(radiusText) : NaN;
    if (Number.isFinite(radius) && radius > 0) {
      const customLatText = String($('#filterRadiusLat')?.value || '').trim();
      const customLonText = String($('#filterRadiusLon')?.value || '').trim();
      if (!!customLatText !== !!customLonText) {
        toast(ui('Informe latitude e longitude do centro radial, ou deixe ambas vazias.', 'Enter both radial center latitude and longitude, or leave both blank.'), 'error');
        return;
      }
      const lat = customLatText ? Number(customLatText) : Number($('#latitudeDecimal')?.value);
      const lon = customLonText ? Number(customLonText) : Number($('#longitudeDecimal')?.value);
      if (Number.isFinite(lat) && Number.isFinite(lon)) {
        parts.push(`r/${lat.toFixed(6)}/${lon.toFixed(6)}/${Math.round(radius)}`);
      } else {
        toast(ui('Informe Latitude e Longitude para gerar o filtro radial.', 'Enter Latitude and Longitude to generate the radial filter.'), 'error');
        return;
      }
    }

    const brazilOnly = !!$('#filterBrazilOnly')?.checked;
    const prefixes = splitFilterValues($('#filterPrefixes')?.value);
    if (brazilOnly) parts.push(BRAZIL_FILTER);
    else if (prefixes.length) parts.push('p/' + prefixes.join('/'));

    const buddies = splitFilterValues($('#filterBuddies')?.value);
    if (buddies.length) parts.push('b/' + buddies.join('/'));

    const areaTexts = ['filterAreaNorth','filterAreaWest','filterAreaSouth','filterAreaEast'].map(id => String($('#' + id)?.value || '').trim());
    const anyArea = areaTexts.some(Boolean);
    if (anyArea) {
      if (!areaTexts.every(Boolean)) {
        toast(ui('Preencha os quatro limites da área geográfica.', 'Fill all four geographic area limits.'), 'error');
        return;
      }
      const areaValues = areaTexts.map(Number);
      if (!areaValues.every(Number.isFinite)) {
        toast(ui('Os limites da área geográfica são inválidos.', 'Geographic area limits are invalid.'), 'error');
        return;
      }
      parts.push(`a/${areaValues.join('/')}`);
    }

    const types = $$('.filter-type:checked').map(input => input.value).join('');
    if (types) parts.push('t/' + types);
    $('#aprsFilterInput').value = parts.join(' ');
    parseFilterIntoBuilder();
    markConfigDirty();
    toast(ui('Filtro APRS-IS gerado. Revise a string antes de salvar.', 'APRS-IS filter generated. Review the string before saving.'), 'ok');
  });

  $('#copyFilterButton')?.addEventListener('click', async () => {
    const value = String($('#aprsFilterInput')?.value || '');
    try {
      await navigator.clipboard.writeText(value);
      toast(ui('Filtro copiado.', 'Filter copied.'), 'ok');
    } catch (_) {
      window.prompt(ui('Copie o filtro:', 'Copy the filter:'), value);
    }
  });

  $('#restoreDefaultFilterButton')?.addEventListener('click', () => {
    $('#aprsFilterInput').value = BRAZIL_FILTER;
    if ($('#filterBrazilOnly')) $('#filterBrazilOnly').checked = true;
    $('#filterRadiusKm').value = '';
    $('#filterRadiusLat').value = '';
    $('#filterRadiusLon').value = '';
    $('#filterPrefixes').value = '';
    $('#filterBuddies').value = '';
    for (const id of ['filterAreaNorth','filterAreaWest','filterAreaSouth','filterAreaEast']) if ($('#' + id)) $('#' + id).value = '';
    $$('.filter-type').forEach(input => { input.checked = false; });
    parseFilterIntoBuilder();
    markConfigDirty();
    toast(ui('Filtro padrão para estações brasileiras restaurado.', 'Default Brazil-only filter restored.'), 'ok');
  });
  $('#themeQuickToggle')?.addEventListener('click', async () => {
    const current = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
    const next = current === 'light' ? 'dark' : 'light';
    const formTheme = $('#configForm')?.elements.namedItem('app_theme');
    if (formTheme) formTheme.value = next;
    applyAppearancePreferences({ ...(state.currentConfig || {}), app_theme: next });
    if (state.activeTab === 'config') {
      markConfigDirty();
      return;
    }
    try {
      const payload = { ...(state.currentConfig || {}), app_theme: next };
      const saved = await api('/api/config', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) });
      state.currentConfig = saved.config || payload;
    } catch (err) { toast(err.message, 'error'); }
  });

  $('#refreshTopologyStatsButton')?.addEventListener('click', async () => {
    const box = $('#topologyStatsContent');
    if (!box) return;
    box.textContent = ui('Carregando análise…', 'Loading analysis…');
    try {
      const data = await api(`/api/topology/stats?hours=${encodeURIComponent(state.topologyHours || 24)}`);
      const list = (items, formatter) => items.length ? '<ol>' + items.map(formatter).join('') + '</ol>' : '<span class="hint">' + ui('Sem dados.', 'No data.') + '</span>';
      box.innerHTML =
        '<div class="topology-stat-group"><h4>' + ui('Digipeaters mais utilizados', 'Most used digipeaters') + '</h4>' +
        list(data.digipeaters || [], x => `<li><strong>${escapeHtml(x.callsign)}</strong> — ${Number(x.packets||0).toLocaleString(currentLocale())}</li>`) + '</div>' +
        '<div class="topology-stat-group"><h4>' + ui('IGates mais ativos', 'Most active IGates') + '</h4>' +
        list(data.igates || [], x => `<li><strong>${escapeHtml(x.callsign)}</strong> — ${Number(x.packets||0).toLocaleString(currentLocale())}</li>`) + '</div>' +
        '<div class="topology-stat-group"><h4>' + ui('Enlaces que deixaram de aparecer', 'Links no longer seen') + '</h4>' +
        list(data.recently_disappeared || [], x => `<li>${escapeHtml(x.source)} → ${escapeHtml(x.target)} · ${escapeHtml(fmtDate(x.last_seen))}</li>`) + '</div>' +
        '<div class="topology-stat-group"><h4>' + ui('Comparação com período anterior', 'Comparison with previous period') + '</h4>' +
        '<div class="hint">' +
        ui(
          `${Number(data.comparison?.current_events || 0).toLocaleString(currentLocale())} eventos agora · ${Number(data.comparison?.previous_events || 0).toLocaleString(currentLocale())} no período anterior · Δ ${Number(data.comparison?.delta || 0).toLocaleString(currentLocale())}`,
          `${Number(data.comparison?.current_events || 0).toLocaleString(currentLocale())} events now · ${Number(data.comparison?.previous_events || 0).toLocaleString(currentLocale())} previous · Δ ${Number(data.comparison?.delta || 0).toLocaleString(currentLocale())}`
        ) + '</div></div>';
    } catch (err) { box.textContent = err.message; }
  });

  $('#animateTopologyButton')?.addEventListener('click', async () => {
    if (state.configDirty) {
      toast(ui('Salve ou descarte as alterações da Configuração antes de abrir a animação.', 'Save or discard Settings changes before opening the animation.'), 'error');
      return;
    }
    if (!state.map) return;
    try {
      const events = await api(`/api/topology/timeline?hours=${encodeURIComponent(state.topologyHours || 24)}&limit=2500`);
      if (!events.length) {
        toast(ui('Não há eventos de topologia com posição para animar.', 'There are no positioned topology events to animate.'), 'error');
        return;
      }
      activateTab('map');
      clearTopologyLines();
      state.topologyEnabled = true;
      localStorage.setItem('pt2vhf_topology_enabled', '1');
      const step = Math.max(1, Math.ceil(events.length / 180));
      let index = 0;
      const timer = setInterval(() => {
        const slice = events.slice(index, index + step);
        for (const edge of slice) {
          const points = [
            [Number(edge.source_lat), Number(edge.source_lon)],
            [Number(edge.target_lat), Number(edge.target_lon)]
          ];
          if (!points.flat().every(Number.isFinite)) continue;
          const key = `timeline:${index}:${edge.source}>${edge.target}`;
          const line = L.polyline(points, {
            color: edge.kind === 'igate' ? state.mapConfig.topology_igate_color : state.mapConfig.topology_rf_color,
            weight: state.mapConfig.topology_width,
            opacity: .64,
            dashArray: edge.kind === 'igate' ? '7 5' : null
          }).addTo(state.map);
          line.bindPopup(`${escapeHtml(edge.source)} → ${escapeHtml(edge.target)}<br>${escapeHtml(fmtDate(edge.timestamp))}`);
          state.topologyLines.set(key, line);
        }
        index += step;
        if (index >= events.length) {
          clearInterval(timer);
          setTimeout(() => loadTopology(), 700);
        }
      }, 80);
    } catch (err) { toast(err.message, 'error'); }
  });

  $('#resetConfigButton')?.addEventListener('click', async () => {
    if (!window.confirm(ui('Restaurar TODA a configuração para os padrões atuais? Mensagens, estações, logs e tracklogs serão preservados.', 'Restore ALL settings to current defaults? Messages, stations, logs and tracklogs will be preserved.'))) return;
    try {
      await api('/api/config/reset', { method:'POST' });
      localStorage.removeItem('pt2vhf_coordinate_mode');
      await loadConfig();
      toast(ui('Configuração padrão restaurada.', 'Default configuration restored.'), 'ok');
    } catch (err) { toast(err.message, 'error'); }
  });

  setupSortableTable('messagesTable', 'messages', renderMessages);
  setupSortableTable('stationsTable', 'stations', renderStations);
  setupExternalLinksForEmbeddedWindow();
  tabSetup();

  async function boot() {
    const startup = await Promise.allSettled([initMap(), loadStations(), loadLog(false), loadConfig(), refreshStatus()]);
    const failed = startup.filter(item => item.status === 'rejected');
    if (failed.length) console.warn('Falhas parciais na inicialização:', failed);
    updateMyMessagesButton();
    await Promise.allSettled([loadMessages(), checkIncomingPersonalMessages()]);
    if (state.currentConfig?.check_updates_on_start) await refreshVersionStatus(false);
    else updateUpdateSettingsUi();
    await refreshPendingUpdateStatus();

    // Não bloqueia a inicialização da interface aguardando permissão/localização.
    setTimeout(() => { initializeAutomaticLocation().catch(err => console.warn(err)); }, 1200);

    setInterval(refreshStatus, 2000);
    setInterval(loadMapData, 5000);
    setInterval(loadMessages, 3000);
    setInterval(checkIncomingPersonalMessages, 3000);
    setInterval(() => { if (state.currentConfig?.check_updates_on_start) refreshVersionStatus(false); }, 30 * 60 * 1000);
    setInterval(() => { if (state.activeTab === 'stations') loadStations(); }, 5000);
    setInterval(() => { if (state.activeTab === 'log') loadLog(false); }, 1000);
  }

  boot();
})();
