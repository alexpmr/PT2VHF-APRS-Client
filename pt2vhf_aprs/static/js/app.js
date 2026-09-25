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
    topologyHours: 0,
    mapLegendElement: null,
    trafficReplayLayers: new Set(),
    timelineReplayActive: false,
    trafficEvents: [],
    trafficIndex: 0,
    trafficPlaying: false,
    trafficOverview: null,
    trafficHasMore: false,
    trafficChunkLastId: 0,
    trafficMode: 'history',
    trafficSpeed: 1,
    trafficTimer: null,
    lastTrafficPacketId: 0,
    trafficPollBusy: false,
    lastActivitySoundAt: 0,
    activityAudioContext: null,
    lastRxCount: 0,
    lastTxCount: 0,
    trafficIndicatorTimer: null,
    replayBounds: null,
    replayWindowStart: null,
    replayWindowEnd: null,
    replaySeeking: false,
    favoriteCallsigns: new Set(),
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
    unreadMessagesOnly: false,
    hideTelemetryMessages: true,
    groupMessages: false,
    selectedConversation: '',
    ownCallsign: '',
    messageAlertBaselineReady: false,
    lastAlertedMessageId: 0,
    currentAlertMessage: null,
    soundOnPersonalMessage: true,
    soundOnStationActivity: true,
    highlightStationActivity: true,
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
    versionCheckInProgress: false,
    messageSending: false,
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
    if (state.versionCheckInProgress) return;
    const el = $('#versionStatus');
    const textEl = $('#versionStatusText');
    if (!el || !textEl) return;
    if (!force && state.configLoaded && !state.currentConfig?.check_updates_on_start) {
      el.classList.remove('checking', 'latest', 'update', 'error', 'ahead');
      textEl.textContent = ui('Verificação manual', 'Manual check');
      el.title = ui('Clique para verificar atualizações.', 'Click to check for updates.');
      return;
    }

    state.versionCheckInProgress = true;
    el.classList.remove('latest', 'update', 'error', 'ahead');
    el.classList.add('checking');
    textEl.textContent = ui('Verificando versão…', 'Checking version…');

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const data = await api(`/api/update-status${force ? '?force=1' : ''}`, { signal: controller.signal });
      state.updateInfo = data;
      el.classList.remove('checking');

      const current = data.current_version ? `v${data.current_version}` : ui('versão atual', 'current version');
      const latest = data.latest_version ? `v${data.latest_version}` : '';

      if (data.status === 'update_available') {
        el.classList.add('update');
        textEl.textContent = ui(`Nova versão ${latest}`, `New version ${latest}`);
        el.title = ui(`Instalada ${current}. Clique para ver a Release e baixar manualmente.`, `Installed ${current}. Click to open the Release and download manually.`);
      } else if (data.status === 'latest') {
        el.classList.add('latest');
        textEl.textContent = ui('Última versão', 'Latest version');
        el.title = ui(`${current} é a versão mais recente publicada.`, `${current} is the latest published version.`);
      } else if (data.status === 'ahead') {
        el.classList.add('ahead');
        textEl.textContent = `Build ${current}`;
        el.title = latest ? `Build > ${latest}` : ui('Build de desenvolvimento.', 'Development build.');
      } else {
        throw new Error(data.error || ui('Falha temporária na verificação.', 'Temporary update check failure.'));
      }
      updateUpdateSettingsUi();
    } catch (err) {
      console.warn('Falha ao verificar nova versão:', err);
      el.classList.remove('checking');
      el.classList.add('error');
      const current = state.updateInfo?.current_version ? `v${state.updateInfo.current_version}` : '';
      textEl.textContent = current
        ? ui(`${current} · verificação indisponível`, `${current} · check unavailable`)
        : ui('Falha temporária na verificação', 'Temporary check failure');
      el.title = ui(
        'Não foi possível verificar agora; nova tentativa será feita automaticamente.',
        'Could not check now; another attempt will be made automatically.'
      );
      const status = $('#updateSettingsStatus');
      if (status) status.textContent = ui(
        'Não foi possível verificar agora; nova tentativa será feita automaticamente.',
        'Could not check now; another attempt will be made automatically.'
      );
    } finally {
      clearTimeout(timeout);
      state.versionCheckInProgress = false;
    }
  }

  function showUpdateModal() {
    const data = state.updateInfo;
    if (!data || data.status !== 'update_available') return;
    $('#updateModalTitle').textContent = ui(`Nova versão v${data.latest_version} disponível`, `New version v${data.latest_version} available`);
    $('#updateModalSummary').textContent = ui(
      `Instalada v${data.current_version}. O download e a instalação são manuais.`,
      `Installed v${data.current_version}. Download and installation are manual.`
    );
    $('#updateReleaseNotes').textContent = String(data.release_notes || ui('Sem notas de versão.', 'No release notes.'));
    $('#updateModal').classList.remove('hidden');
  }

  async function refreshPendingUpdateStatus() {
    const status = $('#updateSettingsStatus');
    if (!status) return;
    if (state.updateInfo?.status === 'update_available') {
      status.textContent = ui(
        `Nova versão v${state.updateInfo.latest_version} disponível. Instalação manual.`,
        `New version v${state.updateInfo.latest_version} available. Manual installation.`
      );
    } else if (state.updateInfo?.status === 'latest') {
      status.textContent = ui('Você está usando a última versão.', 'You are using the latest version.');
    } else if (!state.versionCheckInProgress) {
      status.textContent = ui('Aguardando próxima verificação.', 'Waiting for the next check.');
    }
  }

  function updateUpdateSettingsUi() {
    const btn = $('#openLatestReleaseButton');
    if (btn) btn.classList.toggle('hidden', state.updateInfo?.status !== 'update_available' || !state.updateInfo?.release_url);
    refreshPendingUpdateStatus();
  }

  function openLatestRelease() {
    const url = state.updateInfo?.release_url;
    if (!url) return;
    const nativeApi = window.pywebview?.api;
    if (nativeApi?.open_external) nativeApi.open_external(url);
    else window.open(url, '_blank', 'noopener');
  }

  $('#versionStatus')?.addEventListener('click', e => {
    e.preventDefault();
    if (state.updateInfo?.status === 'update_available') showUpdateModal();
    else refreshVersionStatus(true);
  });
  $('#updateModalClose')?.addEventListener('click', () => $('#updateModal')?.classList.add('hidden'));
  $('#checkUpdatesNowButton')?.addEventListener('click', async () => {
    await refreshVersionStatus(true);
    if (state.updateInfo?.status === 'update_available') showUpdateModal();
    else if (state.updateInfo?.status === 'latest') toast(ui('Verificação concluída: última versão.', 'Check complete: latest version.'), 'ok');
  });
  $('#updateOpenRelease')?.addEventListener('click', openLatestRelease);
  $('#openLatestReleaseButton')?.addEventListener('click', openLatestRelease);

  async function showWhatsNewAfterUpdate() {
    try {
      const info = await api('/api/current-version-info');
      const version = String(info.version || '').trim();
      if (!version) return;
      const key = 'pt2vhf_last_seen_version';
      const previous = String(localStorage.getItem(key) || '').trim();

      // Primeira instalação: apenas registra a versão. Em instalações já
      // configuradas, ausência da chave indica atualização a partir de uma
      // versão anterior que ainda não possuía este recurso.
      if (!previous && !info.existing_install) {
        localStorage.setItem(key, version);
        return;
      }
      if (previous === version) return;

      const list = $('#whatsNewList');
      const title = $('#whatsNewTitle');
      const summary = $('#whatsNewSummary');
      if (!list || !title || !summary) return;

      title.textContent = ui(
        `PT2VHF APRS Client atualizado para v${version}`,
        `PT2VHF APRS Client updated to v${version}`
      );
      summary.textContent = previous
        ? ui(`Atualização concluída: v${previous} → v${version}. Principais novidades:`, `Update complete: v${previous} → v${version}. What's new:`)
        : ui(`Atualização concluída para v${version}. Principais novidades:`, `Updated to v${version}. What's new:`);
      list.innerHTML = (info.items || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
      $('#whatsNewModal')?.classList.remove('hidden');
      $('#whatsNewModal')?.setAttribute('data-version', version);
    } catch (err) {
      console.warn('Não foi possível carregar as novidades da versão:', err);
    }
  }

  $('#whatsNewClose')?.addEventListener('click', () => {
    const modal = $('#whatsNewModal');
    const version = String(modal?.getAttribute('data-version') || '').trim();
    if (version) localStorage.setItem('pt2vhf_last_seen_version', version);
    modal?.classList.add('hidden');
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
      loadMessages({ scrollToNewest: true });
    }
    if (tab === 'stations') loadStations({ scrollToNewest: true });
    if (tab === 'log') loadLog(true);
    if (tab === 'analysis') refreshTopologyAnalysis();
    if (tab === 'config') loadConfig();
  }

  function tabSetup() {
    $$('.tab').forEach(btn => btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      if (tab === state.activeTab) return;
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
      updateMapLegend();
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
    addMapLegendControl(state.map);
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

  function topologyPeriodValue(value) {
    const parsed = Number(value);
    return [0, 1, 6, 24, 168].includes(parsed) ? parsed : 0;
  }

  function topologyPeriodLabel(hours = state.topologyHours) {
    if (Number(hours) === 0) return ui('Completo', 'Complete');
    if (Number(hours) === 168) return ui('7 dias', '7 days');
    return `${Number(hours)} h`;
  }

  function addTopologyControl(map) {
    const savedEnabled = localStorage.getItem('pt2vhf_topology_enabled');
    const savedHoursRaw = localStorage.getItem('pt2vhf_topology_hours');
    state.topologyEnabled = savedEnabled === '1';
    state.topologyHours = savedHoursRaw === null ? 0 : topologyPeriodValue(savedHoursRaw);

    const TopologyControl = L.Control.extend({
      options: { position: 'topright' },
      onAdd() {
        const wrapper = L.DomUtil.create('div', 'leaflet-control topology-control');
        wrapper.innerHTML = `
          <label><input id="topologyToggle" type="checkbox" ${state.topologyEnabled ? 'checked' : ''}> ${ui('Topologia observada', 'Observed topology')}</label>
          <select id="topologyHours" title="${ui('Período da topologia', 'Topology period')}">
            <option value="0">${ui('Completo', 'Complete')}</option>
            <option value="1">1 h</option>
            <option value="6">6 h</option>
            <option value="24">24 h</option>
            <option value="168">${ui('7 dias', '7 days')}</option>
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
            updateMapLegend();
          });
          select.addEventListener('change', async () => {
            state.topologyHours = topologyPeriodValue(select.value);
            localStorage.setItem('pt2vhf_topology_hours', String(state.topologyHours));
            if ($('#analysisPeriod')) $('#analysisPeriod').value = String(state.topologyHours);
            if (state.topologyEnabled) await loadTopology();
            if (state.activeTab === 'analysis') await refreshTopologyAnalysis();
          });
        }, 0);
        return wrapper;
      }
    });
    new TopologyControl().addTo(map);
  }

  function addMapLegendControl(map) {
    const LegendControl = L.Control.extend({
      options: { position: 'bottomleft' },
      onAdd() {
        const wrapper = L.DomUtil.create('div', 'leaflet-control map-line-legend');
        wrapper.innerHTML = `
          <button type="button" class="map-legend-toggle" aria-expanded="true">${ui('Legenda', 'Legend')} ▾</button>
          <div class="map-legend-body">
            <div class="map-legend-item" data-legend="track"><span class="legend-line"></span><span>${ui('Tracklog', 'Tracklog')}</span></div>
            <div class="map-legend-item" data-legend="rf"><span class="legend-line"></span><span>${ui('Enlace RF', 'RF link')}</span></div>
            <div class="map-legend-item" data-legend="igate"><span class="legend-line"></span><span>${ui('Via IGate/APRS-IS', 'Via IGate/APRS-IS')}</span></div>
            <div class="map-legend-item" data-legend="replay"><span class="legend-line"></span><span>${ui('Animação temporal', 'Timeline replay')}</span></div>
            <div class="map-legend-item" data-legend="packet"><span class="legend-packet"></span><span>${ui('Pacote em movimento', 'Moving packet')}</span></div>
          </div>`;
        L.DomEvent.disableClickPropagation(wrapper);
        L.DomEvent.disableScrollPropagation(wrapper);
        wrapper.querySelector('.map-legend-toggle')?.addEventListener('click', event => {
          const body = wrapper.querySelector('.map-legend-body');
          const expanded = !body.classList.toggle('hidden');
          event.currentTarget.setAttribute('aria-expanded', expanded ? 'true' : 'false');
          event.currentTarget.textContent = expanded ? `${ui('Legenda', 'Legend')} ▾` : `${ui('Legenda', 'Legend')} ▸`;
        });
        state.mapLegendElement = wrapper;
        setTimeout(updateMapLegend, 0);
        return wrapper;
      }
    });
    new LegendControl().addTo(map);
  }

  function updateMapLegend() {
    const root = state.mapLegendElement;
    if (!root) return;
    const track = root.querySelector('[data-legend="track"] .legend-line');
    const rf = root.querySelector('[data-legend="rf"] .legend-line');
    const igate = root.querySelector('[data-legend="igate"] .legend-line');
    const replay = root.querySelector('[data-legend="replay"] .legend-line');
    if (track) {
      track.style.borderTopColor = state.mapConfig.track_color;
      track.style.borderTopWidth = `${Math.max(2, state.mapConfig.track_width)}px`;
    }
    if (rf) {
      rf.style.borderTopColor = state.mapConfig.topology_rf_color;
      rf.style.borderTopWidth = `${Math.max(2, state.mapConfig.topology_width)}px`;
    }
    if (igate) {
      igate.style.borderTopColor = state.mapConfig.topology_igate_color;
      igate.style.borderTopWidth = `${Math.max(2, state.mapConfig.topology_width)}px`;
      igate.style.borderTopStyle = 'dashed';
    }
    if (replay) {
      replay.style.borderTopColor = '#ffd54a';
      replay.style.borderTopWidth = `${Math.max(2, state.mapConfig.topology_width + 1)}px`;
      replay.style.borderTopStyle = 'dashed';
    }
    root.querySelector('[data-legend="rf"]')?.classList.toggle('legend-muted', !state.topologyEnabled);
    root.querySelector('[data-legend="igate"]')?.classList.toggle('legend-muted', !state.topologyEnabled);
    const packetAnimating = state.trafficPlaying || state.trafficReplayLayers.size > 0;
    root.querySelector('[data-legend="replay"]')?.classList.toggle('legend-muted', !state.timelineReplayActive);
    root.querySelector('[data-legend="packet"]')?.classList.toggle('legend-muted', !packetAnimating);
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
        ${favoriteStarHtml(s.callsign, false)}
        <button type="button" class="btn secondary station-log-button" data-callsign="${escapeHtml(s.callsign)}">Ver logs</button>
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

  function stationIsVisible(callsign) {
    const call = normalizedCall(callsign);
    if (!call || !state.map) return false;
    const marker = state.markers.get(call);
    const point = marker?.getLatLng?.();
    if (!point || !Number.isFinite(Number(point.lat)) || !Number.isFinite(Number(point.lng))) return false;
    return state.map.getBounds().contains(point);
  }

  function playStationActivitySound(callsign) {
    if (!state.soundOnStationActivity || !stationIsVisible(callsign)) return;
    const now = Date.now();
    if (now - state.lastActivitySoundAt < 700) return;
    state.lastActivitySoundAt = now;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      if (!state.activityAudioContext) state.activityAudioContext = new AudioContextClass();
      const ctx = state.activityAudioContext;
      if (ctx.state === 'suspended') ctx.resume().catch(() => {});
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.0001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.08, ctx.currentTime + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.16);
      oscillator.connect(gain).connect(ctx.destination);
      oscillator.start();
      oscillator.stop(ctx.currentTime + 0.18);
    } catch (_) {}
  }

  function pulseStation(callsign, options = {}) {
    const call = normalizedCall(callsign);
    if (!call || !state.highlightStationActivity || !stationIsVisible(call)) return;
    const marker = state.markers.get(call);
    const el = marker?.getElement?.();
    if (!el) return;
    el.classList.remove('station-transmitting');
    void el.offsetWidth;
    el.classList.add('station-transmitting');
    setTimeout(() => el.classList.remove('station-transmitting'), Number(options.duration || 1800));
  }

  function stationActivity(callsign) {
    const call = normalizedCall(callsign);
    if (!call || !state.map) return;

    const notifyVisibleStation = () => {
      if (!stationIsVisible(call)) return;
      pulseStation(call);
      playStationActivitySound(call);
    };

    if (state.markers.has(call)) {
      notifyVisibleStation();
      return;
    }

    // Uma estação recém-recebida pode ainda não ter marcador no refresh de 5 s.
    // Atualiza o mapa primeiro e só então sinaliza se ela realmente estiver visível.
    loadMapData().then(notifyVisibleStation).catch(() => {});
  }

  function trafficSegmentVisible(segment) {
    if (!state.map) return false;
    const from = L.latLng(Number(segment.source_lat), Number(segment.source_lon));
    const to = L.latLng(Number(segment.target_lat), Number(segment.target_lon));
    if (![from.lat, from.lng, to.lat, to.lng].every(Number.isFinite)) return false;
    const bounds = state.map.getBounds();
    if (bounds.contains(from) || bounds.contains(to)) return true;
    return bounds.intersects(L.latLngBounds(from, to));
  }


  function clearTrafficReplayLayers() {
    for (const layer of state.trafficReplayLayers) {
      try { state.map?.removeLayer(layer); } catch (_) {}
    }
    state.trafficReplayLayers.clear();
    updateMapLegend();
  }

  function trafficEventDetails(event) {
    return `<div class="traffic-packet-popup">
      <strong>${escapeHtml(event.source || ui('Origem desconhecida', 'Unknown source'))}</strong><br>
      ${escapeHtml(fmtDate(event.timestamp))}<br>
      <span>${escapeHtml(event.packet_format || '')}</span>
      ${event.incomplete ? `<div class="traffic-incomplete">${escapeHtml(ui('Caminho incompleto: há nós sem posição conhecida.', 'Incomplete path: some nodes have no known position.'))}</div>` : ''}
      <pre>${escapeHtml(event.raw || '')}</pre>
    </div>`;
  }

  function animateTrafficSegment(segment, event, durationMs) {
    if (!state.map) return Promise.resolve();
    const from = [Number(segment.source_lat), Number(segment.source_lon)];
    const to = [Number(segment.target_lat), Number(segment.target_lon)];
    if (![...from, ...to].every(Number.isFinite)) return Promise.resolve();
    if (!trafficSegmentVisible(segment)) return Promise.resolve();

    const particle = L.circleMarker(from, {
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
    });
  }

  function trafficTimestampMs(value) {
    const ms = new Date(value || '').getTime();
    return Number.isFinite(ms) ? ms : null;
  }

  function drawTrafficDensity() {
    const canvas = $('#trafficDensityCanvas');
    const bins = state.trafficOverview?.bins || [];
    if (!canvas || !bins.length) return;
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(1, Math.round(rect.width || 800));
    const height = Math.max(1, Math.round(rect.height || 42));
    if (canvas.width !== width) canvas.width = width;
    if (canvas.height !== height) canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);
    const max = Math.max(1, ...bins.map(v => Number(v || 0)));
    const barWidth = width / bins.length;
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#3ba6ff';
    bins.forEach((value, index) => {
      const h = Math.max(1, Math.round((Number(value || 0) / max) * (height - 3)));
      ctx.globalAlpha = .25 + .65 * (Number(value || 0) / max);
      ctx.fillRect(index * barWidth, height - h, Math.max(1, barWidth), h);
    });
    ctx.globalAlpha = 1;
  }

  function trafficTimelineTimestamp(value) {
    const first = trafficTimestampMs(state.trafficOverview?.first_timestamp);
    const last = trafficTimestampMs(state.trafficOverview?.last_timestamp);
    if (first === null || last === null) return null;
    const ratio = Math.max(0, Math.min(1, Number(value || 0) / 1000));
    return new Date(first + (last - first) * ratio).toISOString();
  }

  function syncTrafficTimeline(timestamp) {
    const slider = $('#trafficTimeline');
    const first = trafficTimestampMs(state.trafficOverview?.first_timestamp);
    const last = trafficTimestampMs(state.trafficOverview?.last_timestamp);
    const current = trafficTimestampMs(timestamp);
    if (!slider || first === null || last === null || current === null) return;
    const ratio = last > first ? (current - first) / (last - first) : 0;
    slider.value = String(Math.round(Math.max(0, Math.min(1, ratio)) * 1000));
    if ($('#trafficTimelineCursor')) $('#trafficTimelineCursor').textContent = fmtDate(timestamp) || '—';
  }

  function isoToDatetimeLocal(value) {
    const d = new Date(value || '');
    if (Number.isNaN(d.getTime())) return '';
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function datetimeLocalToIso(value) {
    const d = new Date(String(value || ''));
    return Number.isNaN(d.getTime()) ? '' : d.toISOString();
  }

  async function loadTrafficOverview() {
    const hours = topologyPeriodValue(state.topologyHours);
    const params = new URLSearchParams({ bins: '140' });
    if (state.replayWindowStart) params.set('start', state.replayWindowStart);
    if (state.replayWindowEnd) params.set('end', state.replayWindowEnd);
    if (!state.replayWindowStart && !state.replayWindowEnd) params.set('hours', String(hours));
    const data = await api(`/api/traffic/overview?${params.toString()}`);
    state.trafficOverview = data;
    const startInput = $('#trafficRangeStart');
    const endInput = $('#trafficRangeEnd');
    if (startInput) startInput.value = state.replayWindowStart ? isoToDatetimeLocal(state.replayWindowStart) : '';
    if (endInput) endInput.value = state.replayWindowEnd ? isoToDatetimeLocal(state.replayWindowEnd) : '';
    if ($('#trafficTimelineStart')) $('#trafficTimelineStart').textContent = fmtDate(data.first_timestamp) || '—';
    if ($('#trafficTimelineEnd')) $('#trafficTimelineEnd').textContent = fmtDate(data.last_timestamp) || '—';
    const slider = $('#trafficTimeline');
    if (slider) {
      slider.min = '0';
      slider.max = '1000';
      slider.step = '1';
      if (!state.replaySeeking) slider.value = '0';
      slider.disabled = !data.first_timestamp || !data.last_timestamp;
    }
    if ($('#trafficTimelineCursor')) $('#trafficTimelineCursor').textContent = fmtDate(data.first_timestamp) || '—';
    requestAnimationFrame(drawTrafficDensity);
    return data;
  }

  async function animateTrafficEvent(event) {
    if (!event) return;
    stationActivity(event.source);
    const speed = Math.max(.25, Number(state.trafficSpeed || 1));
    const duration = Math.max(90, 1150 / speed);
    state.timelineReplayActive = state.trafficMode === 'history';
    updateMapLegend();
    // Todos os segmentos observados do mesmo pacote começam juntos para mostrar a propagação multi-link simultânea.
    await Promise.all((event.segments || []).map(segment => animateTrafficSegment(segment, event, duration)));
    if ($('#trafficCurrentTime')) $('#trafficCurrentTime').textContent = fmtDate(event.timestamp) || '—';
    syncTrafficTimeline(event.timestamp);
  }

  function updateTrafficAnimationUi() {
    const total = state.trafficEvents.length;
    const played = Math.min(state.trafficIndex, total);
    const pending = Math.max(0, total - played);
    if ($('#trafficPlayedCount')) $('#trafficPlayedCount').textContent = played.toLocaleString(currentLocale());
    if ($('#trafficPendingCount')) $('#trafficPendingCount').textContent = pending.toLocaleString(currentLocale());
    if ($('#trafficCurrentSpeed')) $('#trafficCurrentSpeed').textContent = `${String(state.trafficSpeed).replace('.', ',')}×`;
    if ($('#trafficAnimationStatus')) {
      $('#trafficAnimationStatus').textContent = state.trafficPlaying
        ? (state.trafficMode === 'live' ? ui('Ao vivo', 'Live') : ui('Reproduzindo', 'Playing'))
        : ui('Pausado', 'Paused');
    }
    if ($('#trafficPlayPauseButton')) $('#trafficPlayPauseButton').textContent = state.trafficPlaying ? '⏸ Pause' : '▶ Play';
    $('#trafficLiveButton')?.classList.toggle('active-filter', state.trafficMode === 'live');
    updateMapLegend();
  }

  async function loadTrafficHistory(resetIndex = true, startTimestamp = '') {
    if (resetIndex || !state.trafficOverview) await loadTrafficOverview();
    const first = startTimestamp || state.trafficOverview?.first_timestamp || '';
    const hours = topologyPeriodValue(state.topologyHours);
    const params = new URLSearchParams({ limit: '5000' });
    if (first) params.set('start', first);
    else if (hours) params.set('hours', String(hours));
    if (state.replayWindowEnd) params.set('end', state.replayWindowEnd);
    const data = await api(`/api/traffic/events?${params.toString()}`);
    state.trafficEvents = (data.events || []).filter(event => event.source || (event.segments || []).length);
    state.trafficHasMore = !!data.has_more;
    state.trafficChunkLastId = Number(data.last_id || 0);
    if (resetIndex) state.trafficIndex = 0;
    if (first) syncTrafficTimeline(first);
    updateTrafficAnimationUi();
  }

  async function appendNextTrafficChunk() {
    if (!state.trafficHasMore || !state.trafficChunkLastId) return false;
    const params = new URLSearchParams({ after_id: String(state.trafficChunkLastId), limit: '5000' });
    if (state.replayWindowEnd) params.set('end', state.replayWindowEnd);
    const data = await api(`/api/traffic/events?${params.toString()}`);
    const next = (data.events || []).filter(event => event.source || (event.segments || []).length);
    if (!next.length) {
      state.trafficHasMore = false;
      return false;
    }
    state.trafficEvents.push(...next);
    state.trafficHasMore = !!data.has_more;
    state.trafficChunkLastId = Number(data.last_id || state.trafficChunkLastId);
    updateTrafficAnimationUi();
    return true;
  }

  async function seekTrafficTimeline(value) {
    const target = trafficTimelineTimestamp(value);
    if (!target) return;
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.replaySeeking = true;
    clearTrafficReplayLayers();
    if ($('#trafficTimelineCursor')) $('#trafficTimelineCursor').textContent = fmtDate(target);
    try {
      await loadTrafficHistory(true, target);
      if (state.trafficEvents[0]) {
        await animateTrafficEvent(state.trafficEvents[0]);
      }
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      state.replaySeeking = false;
      updateTrafficAnimationUi();
    }
  }

  function stopTrafficTimer() {
    if (state.trafficTimer) {
      clearTimeout(state.trafficTimer);
      state.trafficTimer = null;
    }
  }

  async function playNextTrafficEvent() {
    stopTrafficTimer();
    if (!state.trafficPlaying || state.trafficMode !== 'history') return;
    if (!state.trafficEvents.length) {
      try {
        await loadTrafficHistory(true);
      } catch (err) {
        toast(err.message, 'error');
        state.trafficPlaying = false;
        updateTrafficAnimationUi();
        return;
      }
    }
    if (state.trafficIndex >= state.trafficEvents.length) {
      try {
        if (await appendNextTrafficChunk()) return playNextTrafficEvent();
      } catch (err) {
        console.warn(err);
      }
      state.trafficPlaying = false;
      state.timelineReplayActive = false;
      updateTrafficAnimationUi();
      return;
    }
    const event = state.trafficEvents[state.trafficIndex++];
    updateTrafficAnimationUi();
    await animateTrafficEvent(event);
    if (!state.trafficPlaying) return;
    state.trafficTimer = setTimeout(playNextTrafficEvent, Math.max(25, 500 / Math.max(.25, Number(state.trafficSpeed || 1))));
  }

  async function pollTrafficEvents() {
    if (state.trafficPollBusy) return;
    state.trafficPollBusy = true;
    try {
      if (!state.lastTrafficPacketId) {
        const baseline = await api('/api/traffic/events?bootstrap=1');
        state.lastTrafficPacketId = Number(baseline.last_id || 0);
        return;
      }
      const data = await api(`/api/traffic/events?after_id=${encodeURIComponent(state.lastTrafficPacketId)}&limit=500`);
      const events = data.events || [];
      state.lastTrafficPacketId = Math.max(state.lastTrafficPacketId, Number(data.last_id || 0));
      for (const event of events) {
        if (state.trafficPlaying && state.trafficMode === 'live') {
          animateTrafficEvent(event);
        } else {
          stationActivity(event.source);
        }
      }
    } catch (err) {
      console.warn(err);
    } finally {
      state.trafficPollBusy = false;
    }
  }

  function flashTrafficIndicator(direction) {
    const root = $('#trafficActivityIndicator');
    if (!root) return;
    const cls = direction === 'tx' ? 'tx-active' : 'rx-active';
    root.classList.add(cls);
    clearTimeout(state.trafficIndicatorTimer);
    state.trafficIndicatorTimer = setTimeout(() => {
      root.classList.remove('rx-active', 'tx-active');
    }, 360);
  }

  function updateTrafficActivityIndicator(status) {
    const rx = Number(status.packets_received || 0);
    const tx = Number(status.packets_sent || 0);

    if (rx >= state.lastRxCount && rx > state.lastRxCount) flashTrafficIndicator('rx');
    if (tx >= state.lastTxCount && tx > state.lastTxCount) flashTrafficIndicator('tx');

    state.lastRxCount = rx;
    state.lastTxCount = tx;

    const root = $('#trafficActivityIndicator');
    if (root) {
      const rxText = status.last_packet_at ? fmtDate(status.last_packet_at) : '—';
      const txText = status.last_tx_at ? fmtDate(status.last_tx_at) : '—';
      root.title = ui(
        `RX: ${rx.toLocaleString(currentLocale())} · último ${rxText}\nTX: ${tx.toLocaleString(currentLocale())} · último ${txText}`,
        `RX: ${rx.toLocaleString(currentLocale())} · last ${rxText}\nTX: ${tx.toLocaleString(currentLocale())} · last ${txText}`
      );
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
      updateTrafficActivityIndicator(s);
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

  function isUnreadPersonalMessage(message) {
    if (!message || message.direction !== 'in' || message.message_type !== 'message' || message.read_at) return false;
    const own = normalizedCall(state.ownCallsign);
    return !own || normalizedCall(message.to_call) === own;
  }

  function visibleMessages() {
    let rows = state.hideTelemetryMessages
      ? state.messages.filter(message => !isTelemetryMessage(message))
      : [...state.messages];
    if (state.unreadMessagesOnly) rows = rows.filter(isUnreadPersonalMessage);
    return rows;
  }

  function normalizedCall(value) {
    return String(value || '').trim().toUpperCase();
  }

  function isFavorite(callsign) {
    return state.favoriteCallsigns.has(normalizedCall(callsign));
  }

  function favoriteStarHtml(callsign, compact = true) {
    const call = normalizedCall(callsign);
    if (!call) return '';
    const favorite = isFavorite(call);
    return `<button type="button" class="favorite-star${favorite ? ' is-favorite' : ''}${compact ? ' compact-star' : ''}" data-favorite-callsign="${escapeHtml(call)}" aria-pressed="${favorite ? 'true' : 'false'}" title="${escapeHtml(favorite ? ui('Remover dos favoritos', 'Remove from favorites') : ui('Adicionar aos favoritos', 'Add to favorites'))}">${favorite ? '★' : '☆'}</button>`;
  }

  function callsignButtonHtml(callsign, otherCall = '') {
    const call = normalizedCall(callsign);
    if (!call) return '';
    return `${favoriteStarHtml(call)}<button type="button" class="callsign-link message-callsign-link" data-callsign="${escapeHtml(call)}" data-other-call="${escapeHtml(normalizedCall(otherCall))}">${escapeHtml(call)}</button>`;
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
      if (isUnreadPersonalMessage(message)) item.unread += 1;
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
      .filter(item => !state.unreadMessagesOnly || item.unread > 0)
      .sort((a, b) => {
        const favoriteDelta = Number(isFavorite(b.contact)) - Number(isFavorite(a.contact));
        if (favoriteDelta) return favoriteDelta;
        return a.contact.localeCompare(b.contact, currentLocale(), { numeric:true, sensitivity:'base' }) * factor;
      });
  }

  function renderGroupedMessages() {
    const conversations = conversationItems();
    const list = $('#conversationList');
    const empty = $('#conversationThreadEmpty');
    const content = $('#conversationThreadContent');
    const recipientButton = $('#conversationRecipientButton');
    const thread = $('#conversationMessages');

    if (!conversations.length) {
      list.innerHTML = `<div class="conversation-list-empty">${state.unreadMessagesOnly ? ui('Nenhuma mensagem não lida.', 'No unread messages.') : ui('Nenhuma conversa individual para os filtros atuais.', 'No individual conversations for the current filters.')}</div>`;
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
      return `<div class="conversation-item${selected}" data-conversation-contact="${escapeHtml(item.contact)}" role="button" tabindex="0">
        <span class="conversation-item-top">
          <strong>${favoriteStarHtml(item.contact)}${escapeHtml(item.contact)}</strong>
          <span>${escapeHtml(fmtDate(item.last?.timestamp))}</span>
        </span>
        <span class="conversation-item-bottom">
          <span>${escapeHtml(item.last?.message || '')}</span>
          ${item.unread ? `<span class="conversation-unread">${item.unread}</span>` : ''}
        </span>
      </div>`;
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
    if (!rows.length) {
      $('#messagesTable tbody').innerHTML = `<tr class="message-empty"><td colspan="6">${state.unreadMessagesOnly ? escapeHtml(ui('Nenhuma mensagem não lida.', 'No unread messages.')) : escapeHtml(ui('Nenhuma mensagem para os filtros atuais.', 'No messages for the current filters.'))}</td></tr>`;
      updateSortIndicators('messagesTable', spec);
      return;
    }
    $('#messagesTable tbody').innerHTML = rows.map(m => `
      <tr data-message-id="${Number(m.id || 0)}" class="${m.status === 'ACK' ? 'message-row-ack ' : m.status === 'REJ' ? 'message-row-rej ' : ''}${isUnreadPersonalMessage(m) ? 'message-row-unread' : ''}">
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

  $('#conversationList')?.addEventListener('click', async event => {
    if (event.target.closest('.favorite-star')) return;
    const item = event.target.closest('[data-conversation-contact]');
    if (!item) return;
    state.selectedConversation = normalizedCall(item.dataset.conversationContact);
    if (state.selectedConversation) {
      $('#messageType').value = 'message';
      updateMessageComposerMode();
      $('#messageTo').value = state.selectedConversation;
      try {
        await api('/api/messages/conversation/read', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({ contact: state.selectedConversation })
        });
        const now = new Date().toISOString();
        state.messages = state.messages.map(m => (
          isUnreadPersonalMessage(m) && resolveMessageContact(m) === state.selectedConversation
            ? { ...m, read_at: now }
            : m
        ));
      } catch (_) {}
    }
    renderMessages();
    updateUnread();
    const thread = $('#conversationMessages');
    if (thread) thread.scrollTop = thread.scrollHeight;
  });
  $('#conversationList')?.addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.closest('[data-conversation-contact]') && !event.target.closest('.favorite-star')) {
      event.preventDefault();
      event.target.closest('[data-conversation-contact]').click();
    }
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

  $('#messagesTable tbody')?.addEventListener('click', async event => {
    if (event.target.closest('.favorite-star')) return;
    const retry = event.target.closest('.message-retry-button');
    if (retry) {
      event.preventDefault();
      event.stopPropagation();
      retryMessagePart(Number(retry.dataset.retryRowId || 0));
      return;
    }
    const button = event.target.closest('.message-callsign-link');
    if (button) {
      event.preventDefault();
      event.stopPropagation();
      selectMessageRecipient(button.dataset.callsign || '', button.dataset.otherCall || '');
      return;
    }
    const row = event.target.closest('tr[data-message-id]');
    if (!row) return;
    const id = Number(row.dataset.messageId || 0);
    const message = state.messages.find(m => Number(m.id || 0) === id);
    if (!isUnreadPersonalMessage(message)) return;
    try {
      await api(`/api/messages/${id}/read`, { method:'POST' });
      message.read_at = new Date().toISOString();
      renderMessages();
      updateUnread();
    } catch (_) {}
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

  function updateUnreadMessagesButton() {
    const btn = $('#unreadMessagesButton');
    if (!btn) return;
    btn.classList.toggle('active-filter', state.unreadMessagesOnly);
    btn.setAttribute('aria-pressed', state.unreadMessagesOnly ? 'true' : 'false');
    btn.textContent = state.unreadMessagesOnly ? ui('✓ Não lidas', '✓ Unread') : ui('Não lidas', 'Unread');
  }

  $('#unreadMessagesButton')?.addEventListener('click', () => {
    state.unreadMessagesOnly = !state.unreadMessagesOnly;
    updateUnreadMessagesButton();
    renderMessages();
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
      $('#destinationList').innerHTML = list.map(call => `<option value="${escapeHtml(call)}" label="${isFavorite(call) ? '★ ' + escapeHtml(ui('Favorita', 'Favorite')) : ''}"></option>`).join('');
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

  document.addEventListener('click', async e => {
    const button = e.target.closest('.station-log-button');
    if (!button) return;
    e.preventDefault();
    e.stopPropagation();
    const callsign = normalizedCall(button.dataset.callsign || '');
    if (!callsign) return;
    activateTab('log');
    const filter = $('#logFilter');
    if (filter) {
      filter.value = callsign;
      filter.classList.add('log-filter-focus');
      setTimeout(() => filter.classList.remove('log-filter-focus'), 2200);
      filter.focus();
    }
    await loadLog(true);
  });

  function estimateMessageParts(text) {
    let remaining = String(text || '').replace(/\s+/g, ' ').trim();
    if (!remaining) return 0;
    const limit = 63;
    let parts = 0;
    while (remaining) {
      if (remaining.length <= limit) {
        parts++;
        break;
      }
      const windowText = remaining.slice(0, limit + 1);
      let cut = windowText.lastIndexOf(' ', limit);
      if (cut <= 0) cut = limit;
      parts++;
      remaining = remaining.slice(cut).trimStart();
    }
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
    if (state.messageSending) {
      toast(ui('A mensagem já está sendo colocada na fila.', 'The message is already being queued.'), 'error');
      return;
    }
    const type = $('#messageType').value;
    const to = $('#messageTo').value.trim().toUpperCase();
    const message = $('#messageText').value.trim();
    const bulletinId = $('#bulletinId').value;
    const group = $('#bulletinGroup').value.trim().toUpperCase();

    if (!message) return toast('Informe a mensagem.', 'error');
    if (type === 'message' && !to) return toast('Informe o indicativo de destino.', 'error');
    if (type === 'group_bulletin' && !group) return toast('Informe o grupo do boletim.', 'error');

    const payload = { type, to, message, bulletin_id: bulletinId, group };
    const button = $('#sendMessageButton');
    state.messageSending = true;
    if (button) {
      button.disabled = true;
      button.textContent = ui('Enviando…', 'Sending…');
    }

    try {
      const result = await api('/api/messages/send', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)
      });
      $('#messageText').value = '';
      updateMessageCharCounter();
      if (result.type === 'message') {
        const count = Number(result.part_count || 1);
        if (result.duplicate) {
          toast(ui('Esta mesma mensagem já estava na fila; o envio duplicado foi bloqueado.', 'This message was already queued; duplicate sending was blocked.'), 'ok');
        } else {
          toast(count > 1
            ? ui(`Mensagem colocada na fila em ${count} partes APRS.`, `Message queued in ${count} APRS parts.`)
            : ui('Mensagem colocada na fila de transmissão.', 'Message queued for transmission.'), 'ok');
        }
      } else {
        toast('Boletim enviado ao APRS-IS sem solicitação de ACK.', 'ok');
      }
      await loadMessages();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      state.messageSending = false;
      updateMessageComposerMode();
      if (button) button.disabled = false;
    }
  }

  $('#messageType').addEventListener('change', updateMessageComposerMode);
  $('#bulletinGroup').addEventListener('input', e => { e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 5); });
  $('#sendMessageButton')?.addEventListener('click', event => { event.preventDefault(); void sendMessage(); });
  $('#messageText').addEventListener('input', updateMessageCharCounter);
  $('#messageText').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
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
      const unreadCount = incoming.filter(m => !m.read_at).length;
      const badge = $('#messageBadge');
      if (badge) {
        badge.textContent = unreadCount;
        badge.classList.toggle('hidden', unreadCount <= 0);
      }
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
  $('#incomingMessageCompactReply')?.addEventListener('click', async () => {
    const message = state.currentAlertMessage;
    if (!message) return;
    const sender = message.from_call || '';
    if (message.id) {
      try { await api(`/api/messages/${Number(message.id)}/read`, { method:'POST' }); } catch (_) {}
    }
    closeCompactIncomingMessageAlert();
    await loadMessages({ scrollToNewest:false });
    selectMessageRecipient(sender);
  });

  async function readIncomingMessage(message) {
    if (!message) return;
    const sender = normalizedCall(message.from_call || '');
    const messageId = Number(message.id || 0);
    closeIncomingMessageAlert();
    closeCompactIncomingMessageAlert();
    if (state.unreadMessagesOnly) {
      state.unreadMessagesOnly = false;
      updateUnreadMessagesButton();
    }
    if (messageId) {
      try { await api(`/api/messages/${messageId}/read`, { method:'POST' }); } catch (_) {}
    }
    activateTab('messages');
    await loadMessages({ scrollToNewest:false });
    if (state.groupMessages && sender) {
      state.selectedConversation = sender;
      $('#messageType').value = 'message';
      updateMessageComposerMode();
      $('#messageTo').value = sender;
      renderGroupedMessages();
      requestAnimationFrame(() => {
        const selected = document.querySelector('[data-conversation-contact="' + CSS.escape(sender) + '"]');
        selected?.scrollIntoView({ block:'nearest' });
        const thread = $('#conversationMessages');
        if (thread) thread.scrollTop = thread.scrollHeight;
      });
    } else {
      renderMessages();
      requestAnimationFrame(() => {
        const rows = $('#messagesTable tbody tr');
        const visible = visibleMessages();
        const spec = state.sort.messages;
        const ordered = sortedData(visible, spec);
        const index = ordered.findIndex(row => Number(row.id || 0) === messageId);
        const row = index >= 0 ? rows[index] : null;
        row?.scrollIntoView({ block:'center' });
        row?.classList.add('message-focus-row');
        setTimeout(() => row?.classList.remove('message-focus-row'), 2200);
      });
    }
    updateUnread();
  }

  $('#incomingMessageRead')?.addEventListener('click', () => readIncomingMessage(state.currentAlertMessage));
  $('#incomingMessageClose')?.addEventListener('click', closeIncomingMessageAlert);
  $('#incomingMessageModal')?.addEventListener('click', e => {
    if (e.target.id === 'incomingMessageModal') closeIncomingMessageAlert();
  });
  $('#incomingMessageReply')?.addEventListener('click', async () => {
    const message = state.currentAlertMessage;
    if (!message) return;
    if (message.id) {
      try { await api(`/api/messages/${Number(message.id)}/read`, { method:'POST' }); } catch (_) {}
    }
    closeIncomingMessageAlert();
    await loadMessages({ scrollToNewest:false });
    openMessageComposer(message.from_call || '');
  });

  function updateUnread() {
    const unread = state.messages.filter(isUnreadPersonalMessage).length;
    const badge = $('#messageBadge');
    if (!badge) return;
    badge.textContent = unread;
    badge.classList.toggle('hidden', unread <= 0);
  }

  function markMessagesSeen() {
    updateUnread();
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

  async function loadFavorites() {
    try {
      const calls = await api('/api/favorites');
      state.favoriteCallsigns = new Set((calls || []).map(normalizedCall).filter(Boolean));
      if (state.stations.length) renderStations();
      if (state.messages.length) renderMessages();
      await loadMapData();
    } catch (err) { console.warn(err); }
  }

  async function toggleFavorite(callsign) {
    const call = normalizedCall(callsign);
    if (!call) return;
    const favorite = !isFavorite(call);
    try {
      await api(`/api/favorites/${encodeURIComponent(call)}`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ favorite })
      });
      if (favorite) state.favoriteCallsigns.add(call);
      else state.favoriteCallsigns.delete(call);
      $$('[data-favorite-callsign]').filter(el => normalizedCall(el.dataset.favoriteCallsign) === call).forEach(el => {
        el.classList.toggle('is-favorite', favorite);
        el.textContent = favorite ? '★' : '☆';
        el.setAttribute('aria-pressed', favorite ? 'true' : 'false');
      });
      state.stations = state.stations.map(s => normalizedCall(s.callsign) === call ? { ...s, favorite: favorite ? 1 : 0 } : s);
      renderStations();
      renderMessages();
      await loadMapData();
    } catch (err) { toast(err.message, 'error'); }
  }

  document.addEventListener('click', event => {
    const star = event.target.closest('.favorite-star');
    if (!star) return;
    event.preventDefault();
    event.stopPropagation();
    toggleFavorite(star.dataset.favoriteCallsign || '');
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
    const favoriteRows = state.stations.filter(s => isFavorite(s.callsign) || Number(s.favorite || 0) === 1);
    const otherRows = state.stations.filter(s => !(isFavorite(s.callsign) || Number(s.favorite || 0) === 1));
    const rows = [...sortedData(favoriteRows, spec), ...sortedData(otherRows, spec)];
    $('#stationsTable tbody').innerHTML = rows.map(s => `
      <tr class="station-row${isFavorite(s.callsign) ? ' station-favorite' : ''}" data-callsign="${escapeHtml(s.callsign)}" tabindex="0" title="${escapeHtml(ui('Abrir esta estação no mapa', 'Open this station on the map'))}">
        <td>${favoriteStarHtml(s.callsign)}${aprsSymbolHtml(s.symbol_table || '/', s.symbol || '>', 24)} ${escapeHtml(s.callsign)}</td>
        <td class="station-last-heard">${escapeHtml(fmtDate(s.last_heard))}</td>
        <td>${fmtNum(s.distance_km, 1, ' km')}</td>
        <td>${fmtNum(s.speed, 1, ' km/h')}</td>
        <td>${fmtNum(s.course, 0, '°')}</td>
        <td>${fmtNum(s.altitude, 1, ' m')}</td>
        <td>${escapeHtml(s.info || '')}</td>
      </tr>`).join('');

    $$('#stationsTable tbody .station-row').forEach(row => {
      const open = () => focusStationOnMap(row.dataset.callsign);
      row.addEventListener('click', event => {
        if (event.target.closest('.favorite-star')) return;
        open();
      });
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
    const status = $('#configSaveStatus');
    if (status) {
      status.textContent = state.configDirty
        ? ui('Há alterações não salvas.', 'There are unsaved changes.')
        : ui('Configuração sem alterações pendentes.', 'No pending configuration changes.');
      status.classList.toggle('unsaved', state.configDirty);
    }
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
      state.soundOnStationActivity = !!cfg.sound_on_station_activity;
      state.highlightStationActivity = !!cfg.highlight_station_activity;
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
      const configStatus = $('#configSaveStatus');
      if (configStatus && !configStatus.classList.contains('saved')) {
        configStatus.textContent = ui('Configuração sem alterações pendentes.', 'No pending configuration changes.');
        configStatus.classList.remove('unsaved');
      }
      updateUpdateSettingsUi();
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
    data.sound_on_station_activity = !!form.elements.sound_on_station_activity?.checked;
    data.highlight_station_activity = !!form.elements.highlight_station_activity?.checked;
    data.check_updates_on_start = !!form.elements.check_updates_on_start?.checked;
    data.auto_download_updates = false;
    data.install_updates_on_exit = false;

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
          : ui('Configuração salva.', 'Configuration saved.'),
        'ok'
      );
      applyMapPreferences(result.config || data);
      applyAppearancePreferences(result.config || data);
      await loadConfig();
      await loadStations();
      state.configDirty = false;
      const saveStatus = $('#configSaveStatus');
      if (saveStatus) {
        saveStatus.textContent = ui('Configuração salva com sucesso.', 'Configuration saved successfully.');
        saveStatus.classList.remove('unsaved');
        saveStatus.classList.add('saved');
        setTimeout(() => saveStatus.classList.remove('saved'), 2600);
      }
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

  function previewTrackStyleFromForm() {
    const form = $('#configForm');
    if (!form) return;
    state.mapConfig.track_color = form.elements.namedItem('track_color')?.value || '#3ba6ff';
    state.mapConfig.track_width = Number(form.elements.namedItem('track_width')?.value || 2);
    for (const line of state.trackLines.values()) {
      line.setStyle({ color: state.mapConfig.track_color, weight: state.mapConfig.track_width, opacity: .78 });
    }
    syncMapPreferenceControls();
    updateMapLegend();
  }

  $('#configForm')?.elements.namedItem('track_color')?.addEventListener('input', e => {
    const colorText = $('#trackColorText');
    if (colorText) colorText.value = e.target.value;
    previewTrackStyleFromForm();
  });

  $('#trackColorText')?.addEventListener('input', e => {
    let value = e.target.value.trim();
    if (!value.startsWith('#')) value = '#' + value;
    if (/^#[0-9a-fA-F]{6}$/.test(value)) {
      const colorInput = $('#configForm')?.elements.namedItem('track_color');
      if (colorInput) colorInput.value = value;
      previewTrackStyleFromForm();
    }
  });

  $('#trackWidth')?.addEventListener('input', previewTrackStyleFromForm);

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
    else {
      for (const line of state.topologyLines.values()) {
        const kind = line.options?.dashArray ? 'igate' : 'rf';
        line.setStyle({
          color: kind === 'igate' ? state.mapConfig.topology_igate_color : state.mapConfig.topology_rf_color,
          weight: state.mapConfig.topology_width
        });
      }
    }
    updateMapLegend();
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
    markConfigDirty();
    toast(ui('Visual da topologia restaurado ao padrão. Clique em Salvar configuração para persistir.', 'Topology appearance restored to defaults. Click Save to persist.'), 'ok');
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
      markConfigDirty();
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
    markConfigDirty();
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
    'Secundária \\':'Secondary \\',
    'Página única de configuração':'Single settings page',
    'As opções estão organizadas por seções. Role a página para acessar Estação APRS, APRS-IS, Mapa e Topologia, Mensagens/Aparência, Aplicativo, Atualizações e Backup/Dados.':'Settings are organized into sections. Scroll to access APRS Station, APRS-IS, Map and Topology, Messages/Appearance, Application, Updates and Backup/Data.',
    'Somente estações brasileiras (padrão)':'Brazilian stations only (default)',
    'Raio (km)':'Radius (km)',
    'Centro radial — Latitude':'Radial center — Latitude',
    'Centro radial — Longitude':'Radial center — Longitude',
    'Sem centro informado, usa a posição configurada da estação.':'If no center is provided, the configured station position is used.',
    'Área geográfica opcional':'Optional geographic area',
    'Norte':'North',
    'Oeste':'West',
    'Sul':'South',
    'Leste':'East',
    'Copiar filtro':'Copy filter',
    'Restaurar filtro Brasil':'Restore Brazil filter',
    'Retry de mensagem após (segundos)':'Retry message after (seconds)',
    'Máximo de retries por parte':'Maximum retries per part',
    'Análise da topologia observada':'Observed topology analysis',
    'Rankings de digipeaters/IGates e enlaces que deixaram de aparecer no período.':'Digipeater/IGate rankings and links no longer seen in the period.',
    'Atualizar análise':'Refresh analysis',
    'Animar período':'Animate period',
    'Atualizações':'Updates',
    'Verificar atualizações automaticamente':'Check for updates automatically',
    'Baixar atualização automaticamente':'Download updates automatically',
    'Instalar atualização automaticamente ao fechar':'Install updates automatically on exit',
    'Nenhuma atualização pendente.':'No pending update.',
    'Verificar atualização agora':'Check for updates now',
    'Baixar atualização':'Download update',
    'Restaurar versão anterior':'Restore previous version',
    'Restaurar configuração padrão':'Restore default settings',
    'Restaura preferências e dados da estação; mensagens, estações, logs e tracklogs não são apagados.':'Restores preferences and station settings; messages, stations, logs and tracklogs are not deleted.',
    'Alterações não salvas':'Unsaved changes',
    'Salvar alterações da Configuração?':'Save Settings changes?',
    'Há alterações que ainda não foram salvas.':'There are changes that have not been saved yet.',
    'Salvar e sair':'Save and leave',
    'Descartar alterações':'Discard changes',
    'Cancelar':'Cancel',
    'Atualização do aplicativo':'Application update',
    'Nova versão disponível':'New version available',
    'Baixar agora':'Download now',
    'Ver Release':'View Release',
    'Depois':'Later',
    'Alternar tema':'Toggle theme',
    'A configuração oferece sugestões regionais e continua aceitando servidor manual.':'Settings provide regional suggestions and still accept a custom server.',
    'O padrão de novas instalações recebe indicativos brasileiros. O campo continua totalmente editável para filtros APRS-IS manuais.':'New installations default to Brazilian callsigns. The field remains fully editable for manual APRS-IS filters.',
    'Conectar ao iniciar vem habilitado em novas instalações e pode ser desligado nesta seção.':'Connect at startup is enabled on new installations and can be disabled in this section.',
    'Quando houver atualização, clique no aviso para abrir o painel integrado, consultar as novidades e baixar o pacote compatível.':'When an update is available, click the notice to open the integrated panel, review changes and download the compatible package.',
    'É possível verificar automaticamente, baixar automaticamente e, nas plataformas compatíveis, instalar ao fechar. O Windows Portable mantém backup para rollback.':'Updates can be checked and downloaded automatically and, on supported platforms, installed on exit. Windows Portable keeps a rollback backup.',
    'O botão Restaurar configuração padrão redefine preferências e dados de configuração, sem apagar mensagens, estações, logs ou tracklogs.':'Restore default settings resets preferences and configuration data without deleting messages, stations, logs or tracklogs.',
    'Análise':'Analysis',
    'Análise da rede':'Network analysis',
    'Indicadores da topologia observada no APRS-IS, com comparação histórica e replay no mapa.':'Observed APRS-IS topology indicators with historical comparison and map replay.',
    'Período':'Period',
    '1 hora':'1 hour',
    '6 horas':'6 hours',
    '24 horas':'24 hours',
    '7 dias':'7 days',
    'Enlaces ativos':'Active links',
    'Pacotes observados':'Observed packets',
    'Eventos do período':'Period events',
    'Mostrar log':'Show log',
    'Completo':'Complete',
    'Animação do tráfego APRS':'APRS traffic animation',
    'Simula os pacotes percorrendo os enlaces observados entre estação, digipeaters e IGates.':'Simulates packets moving through observed links between stations, digipeaters and IGates.',
    'Modo':'Mode',
    'Histórico':'History',
    'Ao vivo':'Live',
    'Velocidade':'Speed',
    'Início':'Start',
    'reproduzidos':'played',
    'pendentes':'pending',
    'Horário:':'Time:',
    'Velocidade:':'Speed:',
    'Pausado':'Paused',
    'Não lidas':'Unread',
    'Tocar sinal sonoro quando uma estação transmitir':'Play a sound when a station transmits',
    'Destacar em vermelho a estação que acabou de transmitir':'Highlight in red the station that just transmitted',
    'Favorita':'Favorite',
    'Adicionar aos favoritos':'Add to favorites',
    'Remover dos favoritos':'Remove from favorites',
    'Legenda':'Legend',
    'Tracklog':'Tracklog',
    'Enlace RF':'RF link',
    'Via IGate/APRS-IS':'Via IGate/APRS-IS',
    'Animação temporal':'Timeline replay',
    'Pacote em movimento':'Moving packet',
    'Nenhuma mensagem não lida.':'No unread messages.',
    'Caminho incompleto: há nós sem posição conhecida.':'Incomplete path: some nodes have no known position.'
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
      if (state.activeTab === 'config' && state.configLoaded && !state.configLoading) markConfigDirty();
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

  async function refreshTopologyAnalysis() {
    const box = $('#topologyStatsContent');
    if (!box) return;
    const periodSelect = $('#analysisPeriod');
    if (periodSelect) periodSelect.value = String(topologyPeriodValue(state.topologyHours));
    box.textContent = ui('Carregando análise…', 'Loading analysis…');
    try {
      const data = await api(`/api/topology/stats?hours=${encodeURIComponent(topologyPeriodValue(state.topologyHours))}`);
      const list = (items, formatter) => items.length
        ? '<ol>' + items.map(formatter).join('') + '</ol>'
        : '<span class="hint">' + ui('Sem dados.', 'No data.') + '</span>';
      box.innerHTML =
        '<div class="topology-stat-group"><h4>' + ui('Digipeaters mais utilizados', 'Most used digipeaters') + '</h4>' +
        list(data.digipeaters || [], x => `<li><strong>${escapeHtml(x.callsign)}</strong> — ${Number(x.packets||0).toLocaleString(currentLocale())}</li>`) + '</div>' +
        '<div class="topology-stat-group"><h4>' + ui('IGates mais ativos', 'Most active IGates') + '</h4>' +
        list(data.igates || [], x => `<li><strong>${escapeHtml(x.callsign)}</strong> — ${Number(x.packets||0).toLocaleString(currentLocale())}</li>`) + '</div>' +
        '<div class="topology-stat-group"><h4>' + ui('Enlaces que deixaram de aparecer', 'Links no longer seen') + '</h4>' +
        list(data.recently_disappeared || [], x => `<li>${escapeHtml(x.source)} → ${escapeHtml(x.target)} · ${escapeHtml(fmtDate(x.last_seen))}</li>`) + '</div>' +
        '<div class="topology-stat-group"><h4>' + ui(data.complete ? 'Histórico completo' : 'Comparação com período anterior', data.complete ? 'Complete history' : 'Comparison with previous period') + '</h4>' +
        '<div class="hint">' +
        (data.complete
          ? ui(
              `${Number(data.comparison?.current_events || 0).toLocaleString(currentLocale())} eventos armazenados no histórico disponível.`,
              `${Number(data.comparison?.current_events || 0).toLocaleString(currentLocale())} events stored in the available history.`
            )
          : ui(
              `${Number(data.comparison?.current_events || 0).toLocaleString(currentLocale())} eventos agora · ${Number(data.comparison?.previous_events || 0).toLocaleString(currentLocale())} no período anterior · Δ ${Number(data.comparison?.delta || 0).toLocaleString(currentLocale())}`,
              `${Number(data.comparison?.current_events || 0).toLocaleString(currentLocale())} events now · ${Number(data.comparison?.previous_events || 0).toLocaleString(currentLocale())} previous · Δ ${Number(data.comparison?.delta || 0).toLocaleString(currentLocale())}`
            )) + '</div></div>';

      if ($('#analysisMetricPeriod')) $('#analysisMetricPeriod').textContent = topologyPeriodLabel();
      if ($('#analysisMetricEdges')) $('#analysisMetricEdges').textContent = Number(data.edges || 0).toLocaleString(currentLocale());
      if ($('#analysisMetricPackets')) $('#analysisMetricPackets').textContent = Number(data.packets || 0).toLocaleString(currentLocale());
      if ($('#analysisMetricEvents')) $('#analysisMetricEvents').textContent = Number(data.comparison?.current_events || 0).toLocaleString(currentLocale());
    } catch (err) {
      box.textContent = err.message;
    }
  }

  $('#refreshTopologyStatsButton')?.addEventListener('click', refreshTopologyAnalysis);
  $('#analysisPeriod')?.addEventListener('change', async event => {
    state.topologyHours = topologyPeriodValue(event.target.value);
    state.replayWindowStart = null;
    state.replayWindowEnd = null;
    localStorage.setItem('pt2vhf_topology_hours', String(state.topologyHours));
    const mapPeriod = $('#topologyHours');
    if (mapPeriod) mapPeriod.value = String(state.topologyHours);
    if (state.topologyEnabled) await loadTopology();
    stopTrafficTimer();
    state.trafficPlaying = false;
    if (state.trafficMode === 'history') {
      try { await loadTrafficHistory(true); } catch (_) {}
    }
    updateTrafficAnimationUi();
    await refreshTopologyAnalysis();
  });

  $('#trafficApplyRangeButton')?.addEventListener('click', async () => {
    const start = datetimeLocalToIso($('#trafficRangeStart')?.value);
    const end = datetimeLocalToIso($('#trafficRangeEnd')?.value);
    if (!start || !end) {
      toast(ui('Informe início e fim do intervalo.', 'Enter both interval start and end.'), 'error');
      return;
    }
    if (new Date(start).getTime() >= new Date(end).getTime()) {
      toast(ui('O início precisa ser anterior ao fim.', 'The start must be before the end.'), 'error');
      return;
    }
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.trafficMode = 'history';
    state.replayWindowStart = start;
    state.replayWindowEnd = end;
    if ($('#trafficMode')) $('#trafficMode').value = 'history';
    clearTrafficReplayLayers();
    try {
      await loadTrafficHistory(true, start);
      toast(ui('Intervalo aplicado ao Replay da Rede.', 'Replay interval applied.'), 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  $('#trafficClearRangeButton')?.addEventListener('click', async () => {
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.replayWindowStart = null;
    state.replayWindowEnd = null;
    clearTrafficReplayLayers();
    try {
      await loadTrafficHistory(true);
      toast(ui('Replay sincronizado com o período da Análise.', 'Replay synced with the Analysis period.'), 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  $('#trafficMode')?.addEventListener('change', async event => {
    state.trafficMode = event.target.value === 'live' ? 'live' : 'history';
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.timelineReplayActive = false;
    clearTrafficReplayLayers();
    if (state.trafficMode === 'history') {
      try { await loadTrafficHistory(true); } catch (err) { toast(err.message, 'error'); }
    } else {
      state.trafficEvents = [];
      state.trafficIndex = 0;
      const overview = state.trafficOverview || await loadTrafficOverview().catch(() => null);
      if (overview?.last_timestamp) syncTrafficTimeline(overview.last_timestamp);
    }
    updateTrafficAnimationUi();
  });

  $('#trafficSpeed')?.addEventListener('change', event => {
    state.trafficSpeed = Math.max(.25, Number(event.target.value || 1));
    updateTrafficAnimationUi();
  });

  $('#trafficTimeline')?.addEventListener('input', event => {
    state.replaySeeking = true;
    const target = trafficTimelineTimestamp(event.target.value);
    if (target && $('#trafficTimelineCursor')) $('#trafficTimelineCursor').textContent = fmtDate(target);
  });
  $('#trafficTimeline')?.addEventListener('change', async event => {
    if (state.trafficMode !== 'history') {
      state.trafficMode = 'history';
      if ($('#trafficMode')) $('#trafficMode').value = 'history';
    }
    await seekTrafficTimeline(event.target.value);
  });

  $('#trafficPlayPauseButton')?.addEventListener('click', async () => {
    state.trafficPlaying = !state.trafficPlaying;
    state.timelineReplayActive = state.trafficPlaying && state.trafficMode === 'history';
    updateTrafficAnimationUi();
    if (!state.trafficPlaying) {
      stopTrafficTimer();
      return;
    }
    activateTab('map');
    if (state.trafficMode === 'history') await playNextTrafficEvent();
  });

  $('#trafficLiveButton')?.addEventListener('click', async () => {
    stopTrafficTimer();
    clearTrafficReplayLayers();
    state.trafficMode = 'live';
    state.trafficPlaying = true;
    state.timelineReplayActive = false;
    state.trafficEvents = [];
    state.trafficIndex = 0;
    if ($('#trafficMode')) $('#trafficMode').value = 'live';
    try {
      const overview = await loadTrafficOverview();
      if (overview?.last_timestamp) syncTrafficTimeline(overview.last_timestamp);
      const baseline = await api('/api/traffic/events?bootstrap=1');
      state.lastTrafficPacketId = Number(baseline.last_id || state.lastTrafficPacketId || 0);
    } catch (_) {}
    updateTrafficAnimationUi();
  });

  $('#trafficResetButton')?.addEventListener('click', async () => {
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.timelineReplayActive = false;
    state.trafficIndex = 0;
    clearTrafficReplayLayers();
    if (state.trafficMode === 'history') {
      try { await loadTrafficHistory(true); } catch (err) { toast(err.message, 'error'); }
    }
    if ($('#trafficCurrentTime')) $('#trafficCurrentTime').textContent = '—';
    updateTrafficAnimationUi();
  });

  $('#trafficBackButton')?.addEventListener('click', async () => {
    if (state.trafficMode !== 'history') {
      toast(ui('Voltar está disponível no modo Histórico.', 'Back is available in History mode.'), 'error');
      return;
    }
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.timelineReplayActive = true;
    if (!state.trafficEvents.length) await loadTrafficHistory(true);
    state.trafficIndex = Math.max(0, state.trafficIndex - 1);
    const index = Math.max(0, state.trafficIndex - 1);
    const event = state.trafficEvents[index];
    activateTab('map');
    clearTrafficReplayLayers();
    if (event) await animateTrafficEvent(event);
    updateTrafficAnimationUi();
  });

  $('#trafficForwardButton')?.addEventListener('click', async () => {
    if (state.trafficMode !== 'history') {
      toast(ui('Avançar está disponível no modo Histórico.', 'Forward is available in History mode.'), 'error');
      return;
    }
    stopTrafficTimer();
    state.trafficPlaying = false;
    state.timelineReplayActive = true;
    if (!state.trafficEvents.length) await loadTrafficHistory(true);
    if (state.trafficIndex >= state.trafficEvents.length && state.trafficHasMore) {
      try { await appendNextTrafficChunk(); } catch (_) {}
    }
    const event = state.trafficEvents[state.trafficIndex];
    if (event) {
      state.trafficIndex += 1;
      activateTab('map');
      clearTrafficReplayLayers();
      await animateTrafficEvent(event);
    }
    updateTrafficAnimationUi();
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
    document.addEventListener('pointerdown', () => {
      try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass && !state.activityAudioContext) state.activityAudioContext = new AudioContextClass();
        state.activityAudioContext?.resume?.().catch(() => {});
      } catch (_) {}
    }, { once:true });
    const startup = await Promise.allSettled([initMap(), loadStations(), loadLog(false), loadConfig(), refreshStatus()]);
    const failed = startup.filter(item => item.status === 'rejected');
    if (failed.length) console.warn('Falhas parciais na inicialização:', failed);
    updateMyMessagesButton();
    updateUnreadMessagesButton();
    updateTrafficAnimationUi();
    await Promise.allSettled([loadFavorites(), loadMessages(), checkIncomingPersonalMessages(), pollTrafficEvents()]);
    if (state.currentConfig?.check_updates_on_start) await refreshVersionStatus(false);
    else updateUpdateSettingsUi();
    updateUpdateSettingsUi();
    await showWhatsNewAfterUpdate();
    loadTrafficOverview().catch(err => console.warn('Replay overview:', err));

    // Não bloqueia a inicialização da interface aguardando permissão/localização.
    setTimeout(() => { initializeAutomaticLocation().catch(err => console.warn(err)); }, 1200);

    setInterval(refreshStatus, 2000);
    setInterval(loadMapData, 5000);
    setInterval(pollTrafficEvents, 2000);
    setInterval(loadMessages, 3000);
    setInterval(checkIncomingPersonalMessages, 3000);
    setInterval(() => { if (state.currentConfig?.check_updates_on_start) refreshVersionStatus(false); }, 5 * 60 * 1000);
    setInterval(() => { if (state.activeTab === 'stations') loadStations(); }, 5000);
    setInterval(() => { if (state.activeTab === 'log') loadLog(false); }, 1000);
  }

  boot();
})();
