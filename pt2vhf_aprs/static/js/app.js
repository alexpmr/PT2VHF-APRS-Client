(() => {
  'use strict';

  const state = {
    activeTab: 'map',
    map: null,
    baseLayer: null,
    mapLoadBusy: false,
    mapLoadLastAt: 0,
    mapLoadQueued: false,
    mapPeriodHours: Number(localStorage.getItem('pt2vhf_map_period_hours') || 0),
    stationsEnabled: localStorage.getItem('pt2vhf_map_item_stations') !== '0',
    objectsEnabled: localStorage.getItem('pt2vhf_map_item_objects') !== '0',
    tracklogEnabled: localStorage.getItem('pt2vhf_map_item_tracklogs') !== '0',
    rfLinksEnabled: localStorage.getItem('pt2vhf_map_item_rf') !== '0',
    igateLinksEnabled: localStorage.getItem('pt2vhf_map_item_igate') !== '0',
    packetsEnabled: localStorage.getItem('pt2vhf_map_item_packets') !== '0',
    mapKnownCallsigns: new Set(),
    mapVisibleCallsigns: new Set(),
    systemMetricsBusy: false,
    mapConfig: {
      map_type: 'osm',
      track_color: '#3ba6ff',
      track_width: 2,
      topology_rf_color: '#ffff00',
      topology_igate_color: '#ffff00',
      topology_width: 1,
      map_brightness: 100
    },
    markers: new Map(),
    objectMarkers: new Map(),
    trackLines: new Map(),
    topologyLines: new Map(),
    topologyEnabled: false,
    topologyHours: 0,
    topologyLoadBusy: false,
    mapLegendElement: null,
    mapLegendCollapsed: localStorage.getItem('pt2vhf_map_legend_collapsed') === '1',
    trafficReplayLayers: new Set(),
    queryTraceLayers: new Set(),
    queryPollers: new Map(),
    queryLastByStation: new Map(),
    timelineReplayActive: false,
    trafficEvents: [],
    trafficIndex: 0,
    trafficPlaying: false,
    trafficAnimationEnabled: true,
    trafficOverview: null,
    trafficHasMore: false,
    trafficChunkLastId: 0,
    trafficMode: 'history',
    trafficSpeed: [0.5, 1, 2, 5].includes(Number(localStorage.getItem('pt2vhf_traffic_speed'))) ? Number(localStorage.getItem('pt2vhf_traffic_speed')) : 1,
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
    conversationSortKey: localStorage.getItem('pt2vhf_conversation_sort_key') === 'date' ? 'date' : 'sender',
    configDirty: false,
    configLoading: false,
    configBaseline: '',
    pendingTab: '',
    updateInfo: null,
    updateDownloading: false,
    versionCheckInProgress: false,
    messageSending: false,
    mapHistoryOpen: localStorage.getItem('pt2vhf_map_history_open') === '1',
  };

  const BRAZIL_PREFIXES = ['PP','PQ','PR','PS','PT','PU','PV','PW','PX','PY','ZV','ZW','ZX','ZY','ZZ'];
  const BRAZIL_FILTER = 'p/' + BRAZIL_PREFIXES.join('/');

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => [...document.querySelectorAll(sel)];

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  }

  const EXTRA_I18N = window.PT2VHF_I18N || {};

  function normalizeLanguage(value) {
    return ['pt-BR', 'en', 'es', 'fr'].includes(String(value || '')) ? String(value) : 'pt-BR';
  }

  function translatedText(pt, en) {
    if (state.language === 'en') return en || pt;
    if (state.language === 'es' || state.language === 'fr') {
      return EXTRA_I18N[state.language]?.[pt] || en || EN_TEXT?.get?.(pt) || pt;
    }
    return pt;
  }

  function ui(pt, en) {
    return translatedText(pt, en);
  }

  function currentLocale() {
    return ({'pt-BR':'pt-BR', en:'en-US', es:'es-ES', fr:'fr-FR'})[state.language] || 'pt-BR';
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
    const requestOptions = { ...options };
    let timeoutId = null;
    let controller = null;
    if (!requestOptions.signal) {
      controller = new AbortController();
      requestOptions.signal = controller.signal;
      timeoutId = setTimeout(() => controller.abort(), 10000);
    }
    try {
      const response = await fetch(url, requestOptions);
      let data = null;
      const ct = response.headers.get('content-type') || '';
      if (ct.includes('application/json')) data = await response.json();
      if (!response.ok) throw new Error(data?.error || `Erro HTTP ${response.status}`);
      return data;
    } catch (err) {
      if (err?.name === 'AbortError') {
        throw new Error(ui(
          `O backend local não respondeu em 10 segundos (${url}).`,
          `The local backend did not respond within 10 seconds (${url}).`
        ));
      }
      throw err;
    } finally {
      if (timeoutId) clearTimeout(timeoutId);
    }
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
        el.title = ui(`Instalada ${current}. Clique para baixar e instalar ${latest}.`, `Installed ${current}. Click to download and install ${latest}.`);
      } else if (data.status === 'latest') {
        el.classList.add('latest');
        textEl.textContent = ui('Última versão', 'Latest version');
        el.title = ui(`${current} é a versão mais recente publicada.`, `${current} is the latest published version.`);
      } else if (data.status === 'ahead') {
        el.classList.add('ahead');
        textEl.textContent = ui(`Versão ${current}`, `Build ${current}`);
        el.title = latest ? ui(`Versão > ${latest}`, `Build > ${latest}`) : ui('Versão de desenvolvimento.', 'Development build.');
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

  function setUpdateProgress(message = '', type = '') {
    const progress = $('#updateDownloadProgress');
    if (!progress) return;
    const text = String(message || '').trim();
    progress.textContent = text;
    progress.classList.remove('hidden', 'working', 'success', 'error');
    if (!text) {
      progress.classList.add('hidden');
      return;
    }
    if (type) progress.classList.add(type);
  }

  function showUpdateModal() {
    const data = state.updateInfo;
    if (!data || data.status !== 'update_available') return;
    $('#updateModalTitle').textContent = ui(`Nova versão v${data.latest_version} disponível`, `New version v${data.latest_version} available`);
    const ready = !!data.asset_ready && !!data.install_supported;
    $('#updateModalSummary').textContent = ready
      ? ui(
          `Instalada v${data.current_version}. O pacote ${data.asset_name} será baixado, validado e instalado automaticamente.`,
          `Installed v${data.current_version}. Package ${data.asset_name} will be downloaded, verified and installed automatically.`
        )
      : ui(
          data.error || 'A instalação automática não está disponível nesta execução. Use a página da Release.',
          data.error || 'Automatic installation is not available in this build. Use the Release page.'
        );
    $('#updateReleaseNotes').textContent = String(data.release_notes || ui('Sem notas de versão.', 'No release notes.'));
    const installButton = $('#updateInstallNow');
    if (installButton) installButton.disabled = !ready || state.updateDownloading;
    const closeButton = $('#updateModalClose');
    const releaseButton = $('#updateOpenRelease');
    if (closeButton) closeButton.disabled = !!state.updateDownloading;
    if (releaseButton) releaseButton.disabled = !!state.updateDownloading;
    if (!state.updateDownloading) {
      setUpdateProgress();
      const bar = $('#updateProgressBar');
      if (bar) {
        bar.classList.add('hidden');
        bar.removeAttribute('value');
      }
    }
    $('#updateModal').classList.remove('hidden');
  }

  async function refreshPendingUpdateStatus() {
    const status = $('#updateSettingsStatus');
    if (!status) return;
    if (state.updateInfo?.status === 'update_available') {
      const ready = !!state.updateInfo.asset_ready && !!state.updateInfo.install_supported;
      status.textContent = ready
        ? ui(
            `Nova versão v${state.updateInfo.latest_version} disponível para instalação automática.`,
            `New version v${state.updateInfo.latest_version} is ready for automatic installation.`
          )
        : ui(
            state.updateInfo.error || `Nova versão v${state.updateInfo.latest_version} disponível; pacote automático indisponível.`,
            state.updateInfo.error || `New version v${state.updateInfo.latest_version} is available; automatic package unavailable.`
          );
    } else if (state.updateInfo?.status === 'latest') {
      status.textContent = ui('Você está usando a última versão.', 'You are using the latest version.');
    } else if (!state.versionCheckInProgress) {
      status.textContent = ui('Aguardando próxima verificação.', 'Waiting for the next check.');
    }
  }

  function updateUpdateSettingsUi() {
    const btn = $('#openLatestReleaseButton');
    if (btn) {
      const ready = state.updateInfo?.status === 'update_available' && state.updateInfo?.asset_ready && state.updateInfo?.install_supported;
      btn.classList.toggle('hidden', !ready);
      btn.disabled = !!state.updateDownloading;
    }
    refreshPendingUpdateStatus();
  }

  function openLatestRelease() {
    const url = state.updateInfo?.release_url;
    if (!url) return;
    const nativeApi = window.pywebview?.api;
    if (nativeApi?.open_external) nativeApi.open_external(url);
    else window.open(url, '_blank', 'noopener');
  }

  function openKmlExportModal() {
    const modal = $('#kmlExportModal');
    const period = $('#kmlExportPeriod');
    if (period) period.value = String(topologyPeriodValue(state.mapPeriodHours));
    if ($('#kmlExportStatus')) $('#kmlExportStatus').textContent = '';
    modal?.classList.remove('hidden');
  }

  async function saveKmlContent(filename, content) {
    const nativeSave = window.pywebview?.api?.save_text_file;
    if (nativeSave) {
      const result = await nativeSave(filename, content);
      if (result?.cancelled) return { cancelled: true };
      if (!result?.saved) {
        throw new Error(result?.error || ui('Não foi possível salvar o arquivo KML.', 'Could not save the KML file.'));
      }
      return { saved: true, path: String(result.path || filename), native: true };
    }

    if (typeof window.showSaveFilePicker === 'function') {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{
            description: 'KML',
            accept: { 'application/vnd.google-earth.kml+xml': ['.kml'] },
          }],
          excludeAcceptAllOption: false,
        });
        const writable = await handle.createWritable();
        await writable.write(new Blob([content], { type: 'application/vnd.google-earth.kml+xml;charset=utf-8' }));
        await writable.close();
        return { saved: true, path: handle.name || filename, native: false };
      } catch (err) {
        if (err?.name === 'AbortError') return { cancelled: true };
        throw err;
      }
    }

    const proceed = window.confirm(ui(
      'Este navegador não permite escolher a pasta diretamente. Se continuar, o arquivo será enviado ao gerenciador de downloads do navegador. Deseja continuar?',
      'This browser cannot choose the folder directly. If you continue, the file will be sent to the browser download manager. Continue?'
    ));
    if (!proceed) return { cancelled: true };

    const blob = new Blob([content], { type: 'application/vnd.google-earth.kml+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
    return { saved: true, path: ui('pasta de downloads do navegador', 'browser downloads folder'), browserFallback: true };
  }

  async function exportKml() {
    const selected = {
      stations: !!$('#kmlStations')?.checked,
      positions: !!$('#kmlPositions')?.checked,
      tracklogs: !!$('#kmlTracklogs')?.checked,
      topology: !!$('#kmlTopology')?.checked,
    };
    if (!Object.values(selected).some(Boolean)) {
      const message = ui('Selecione pelo menos uma camada para exportar.', 'Select at least one layer to export.');
      if ($('#kmlExportStatus')) $('#kmlExportStatus').textContent = message;
      toast(message, 'error');
      return;
    }

    const button = $('#kmlExportConfirm');
    const cancel = $('#kmlExportCancel');
    const status = $('#kmlExportStatus');
    if (button) button.disabled = true;
    if (cancel) cancel.disabled = true;
    if (status) status.textContent = ui('Gerando arquivo KML…', 'Generating KML file…');

    const params = new URLSearchParams({
      stations: selected.stations ? '1' : '0',
      positions: selected.positions ? '1' : '0',
      tracklogs: selected.tracklogs ? '1' : '0',
      topology: selected.topology ? '1' : '0',
      hours: String(topologyPeriodValue($('#kmlExportPeriod')?.value || 0)),
    });

    try {
      const response = await fetch(`/api/export/kml?${params.toString()}`);
      if (!response.ok) {
        let message = `Erro HTTP ${response.status}`;
        try {
          const data = await response.json();
          if (data?.error) message = data.error;
        } catch (_) {}
        throw new Error(message);
      }

      const disposition = String(response.headers.get('content-disposition') || '');
      const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
      const filename = filenameMatch?.[1] || `PT2VHF_APRS_Client_${new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15)}.kml`;
      const content = await response.text();

      if (status) status.textContent = ui('Escolha onde deseja salvar o arquivo…', 'Choose where to save the file…');
      const result = await saveKmlContent(filename, content);
      if (result?.cancelled) {
        if (status) status.textContent = ui('Exportação cancelada.', 'Export cancelled.');
        return;
      }

      const savedMessage = result?.path
        ? ui(`KML salvo em: ${result.path}`, `KML saved to: ${result.path}`)
        : ui('KML salvo com sucesso.', 'KML saved successfully.');
      if (status) status.textContent = savedMessage;
      toast(savedMessage, 'ok');
      setTimeout(() => $('#kmlExportModal')?.classList.add('hidden'), 900);
    } catch (err) {
      const message = String(err?.message || err);
      if (status) status.textContent = message;
      toast(message, 'error');
    } finally {
      if (button) button.disabled = false;
      if (cancel) cancel.disabled = false;
    }
  }

  $('#kmlExportButton')?.addEventListener('click', openKmlExportModal);
  $('#kmlExportCancel')?.addEventListener('click', () => $('#kmlExportModal')?.classList.add('hidden'));
  $('#kmlExportConfirm')?.addEventListener('click', () => void exportKml());

  async function installLatestUpdate() {
    let data = state.updateInfo;
    if (!data || data.status !== 'update_available') {
      await refreshVersionStatus(true);
      data = state.updateInfo;
      if (!data || data.status !== 'update_available') {
        toast(ui('Nenhuma atualização disponível no momento.', 'No update is currently available.'), 'error');
        return;
      }
    }
    if (state.updateDownloading) {
      showUpdateModal();
      return;
    }
    if (!data.asset_ready || !data.install_supported) {
      showUpdateModal();
      const message = ui(
        data.error || 'A instalação automática não está disponível para este pacote.',
        data.error || 'Automatic installation is not available for this package.'
      );
      setUpdateProgress(message, 'error');
      toast(message, 'error');
      return;
    }

    const progressBar = $('#updateProgressBar');
    const installButton = $('#updateInstallNow');
    const settingsInstallButton = $('#openLatestReleaseButton');
    const closeButton = $('#updateModalClose');
    const releaseButton = $('#updateOpenRelease');

    // Feedback visual antes mesmo da chamada HTTP: o clique nunca pode parecer inerte.
    state.updateDownloading = true;
    if (installButton) {
      installButton.disabled = true;
      installButton.textContent = ui('Preparando…', 'Preparing…');
    }
    if (settingsInstallButton) {
      settingsInstallButton.disabled = true;
      settingsInstallButton.textContent = ui('Preparando atualização…', 'Preparing update…');
    }
    updateUpdateSettingsUi();
    if (closeButton) closeButton.disabled = true;
    if (releaseButton) releaseButton.disabled = true;
    if (progressBar) {
      progressBar.classList.remove('hidden');
      progressBar.removeAttribute('value');
    }
    setUpdateProgress(ui(
      `Preparando o download de ${data.asset_name}…`,
      `Preparing download of ${data.asset_name}…`
    ), 'working');
    $('#updateModal')?.classList.remove('hidden');
    // Dá ao navegador uma oportunidade de pintar o estado "Preparando" antes do request longo.
    await new Promise(resolve => setTimeout(resolve, 0));
    setUpdateProgress(ui(
      `Baixando, validando e preparando ${data.asset_name}… Não feche a aplicação.`,
      `Downloading, validating and preparing ${data.asset_name}… Do not close the application.`
    ), 'working');
    console.info('PT2VHF updater: instalação solicitada', data.asset_name, data.latest_version);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 180000);
    try {
      const result = await api('/api/update/install', { method:'POST', signal:controller.signal });
      if (progressBar) progressBar.value = 100;
      setUpdateProgress(String(result.message || ui(
        'Atualização pronta. O instalador auxiliar foi confirmado e a aplicação será reiniciada…',
        'Update ready. The updater helper was confirmed and the application will restart…'
      )), 'success');
      toast(ui(
        `v${result.version} validada. O instalador foi iniciado e a aplicação será reiniciada.`,
        `v${result.version} verified. The installer was started and the application will restart.`
      ), 'ok');
    } catch (err) {
      console.error('PT2VHF updater: falha ao baixar/instalar', err);
      const detail = String(err?.message || err || ui('Falha desconhecida na atualização.', 'Unknown update failure.'));
      const message = ui(
        `Não foi possível concluir a atualização automática.\n\nDetalhes: ${detail}`,
        `Automatic update could not be completed.\n\nDetails: ${detail}`
      );
      setUpdateProgress(message, 'error');
      toast(detail, 'error');
      state.updateDownloading = false;
      if (progressBar) {
        progressBar.classList.add('hidden');
        progressBar.removeAttribute('value');
      }
      if (installButton) {
        installButton.disabled = false;
        installButton.textContent = ui('Baixar e instalar', 'Download and install');
      }
      if (settingsInstallButton) {
        settingsInstallButton.disabled = false;
        settingsInstallButton.textContent = ui('Baixar e instalar nova versão', 'Download and install new version');
      }
      if (closeButton) closeButton.disabled = false;
      if (releaseButton) releaseButton.disabled = false;
      updateUpdateSettingsUi();
    } finally {
      clearTimeout(timeout);
    }
  }

  $('#versionStatus')?.addEventListener('click', e => {
    e.preventDefault();
    if (state.updateInfo?.status === 'update_available') showUpdateModal();
    else refreshVersionStatus(true);
  });
  $('#updateModalClose')?.addEventListener('click', () => {
    if (state.updateDownloading) {
      toast(ui('A atualização está em andamento. Aguarde a conclusão.', 'The update is in progress. Please wait for it to finish.'), 'error');
      return;
    }
    $('#updateModal')?.classList.add('hidden');
  });
  $('#checkUpdatesNowButton')?.addEventListener('click', async () => {
    await refreshVersionStatus(true);
    if (state.updateInfo?.status === 'update_available') showUpdateModal();
    else if (state.updateInfo?.status === 'latest') toast(ui('Verificação concluída: última versão.', 'Check complete: latest version.'), 'ok');
  });
  $('#updateInstallNow')?.addEventListener('click', () => void installLatestUpdate());
  $('#updateOpenRelease')?.addEventListener('click', openLatestRelease);
  $('#openLatestReleaseButton')?.addEventListener('click', () => void installLatestUpdate());

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

  function currentAppVersion() {
    return String($('.app-version')?.textContent || '').trim().replace(/^v/i, '') || '1.7.1';
  }

  function aboutCopy() {
    const version = currentAppVersion();
    const copies = {
      'pt-BR': {
        title: 'Sobre',
        subtitle: 'Sobre o projeto, o autor e como contribuir com sugestões.',
        author: 'Criado por Alex, PT2VHF, radioamador e idealizador do PT2VHF APRS Client.',
        project: 'O PT2VHF APRS Client é um cliente APRS moderno e multiplataforma para mapa, mensagens, estatísticas e análise da rede.',
        contactTitle: 'Contato / Sugestões / Dúvidas / Melhorias',
        contact: 'Sugestões, dúvidas, relatos de problemas e ideias de melhoria são bem-vindos.',
        promoteTitle: 'Divulgue o projeto na rede APRS',
        promote: 'Você pode enviar manualmente um Announcement APRS para divulgar o cliente. A mensagem poderá ser revisada antes do envio.',
        promoteButton: 'Divulgar PT2VHF APRS Client na rede APRS',
        eyebrow: 'Divulgação APRS',
        modalTitle: 'Enviar anúncio do PT2VHF APRS Client',
        modalDescription: 'Revise a mensagem abaixo. O anúncio será transmitido uma única vez usando o seu indicativo corrente como remetente.',
        messageLabel: 'Mensagem do Announcement',
        send: 'Confirmar e enviar',
        cancel: 'Cancelar',
        confirm: 'Enviar este Announcement APRS agora? O remetente será o seu indicativo corrente.',
        sent: 'Announcement do PT2VHF APRS Client enviado.',
        download: `PT2VHF APRS Client v${version} - Download: tiny.cc/aprs`,
      },
      en: {
        title: 'About',
        subtitle: 'About the project, its author and how to contribute suggestions.',
        author: 'Created by Alex, PT2VHF, amateur radio operator and creator of PT2VHF APRS Client.',
        project: 'PT2VHF APRS Client is a modern cross-platform APRS client for maps, messaging, statistics and network analysis.',
        contactTitle: 'Contact / Suggestions / Questions / Improvements',
        contact: 'Suggestions, questions, bug reports and improvement ideas are welcome.',
        promoteTitle: 'Promote the project on the APRS network',
        promote: 'You can manually send an APRS Announcement to promote the client. The message can be reviewed before sending.',
        promoteButton: 'Promote PT2VHF APRS Client on APRS',
        eyebrow: 'APRS promotion',
        modalTitle: 'Send PT2VHF APRS Client announcement',
        modalDescription: 'Review the message below. The announcement will be sent once using your current callsign as sender.',
        messageLabel: 'Announcement message',
        send: 'Confirm and send',
        cancel: 'Cancel',
        confirm: 'Send this APRS Announcement now? Your current callsign will be used as sender.',
        sent: 'PT2VHF APRS Client Announcement sent.',
        download: `PT2VHF APRS Client v${version} - Download: tiny.cc/aprs`,
      },
      es: {
        title: 'Acerca de',
        subtitle: 'Sobre el proyecto, su autor y cómo aportar sugerencias.',
        author: 'Creado por Alex, PT2VHF, radioaficionado e impulsor de PT2VHF APRS Client.',
        project: 'PT2VHF APRS Client es un cliente APRS moderno y multiplataforma para mapas, mensajes, estadísticas y análisis de la red.',
        contactTitle: 'Contacto / Sugerencias / Dudas / Mejoras',
        contact: 'Son bienvenidas las sugerencias, dudas, informes de problemas e ideas de mejora.',
        promoteTitle: 'Divulgar el proyecto en la red APRS',
        promote: 'Puede enviar manualmente un Announcement APRS para divulgar el cliente. El mensaje puede revisarse antes del envío.',
        promoteButton: 'Divulgar PT2VHF APRS Client en APRS',
        eyebrow: 'Divulgación APRS',
        modalTitle: 'Enviar anuncio de PT2VHF APRS Client',
        modalDescription: 'Revise el mensaje. El anuncio se transmitirá una sola vez usando su indicativo actual como remitente.',
        messageLabel: 'Mensaje del Announcement',
        send: 'Confirmar y enviar',
        cancel: 'Cancelar',
        confirm: '¿Enviar este Announcement APRS ahora? Se usará su indicativo actual como remitente.',
        sent: 'Announcement de PT2VHF APRS Client enviado.',
        download: `PT2VHF APRS Client v${version} - Descarga: tiny.cc/aprs`,
      },
      fr: {
        title: 'À propos',
        subtitle: 'À propos du projet, de son auteur et des suggestions.',
        author: 'Créé par Alex, PT2VHF, radioamateur et créateur de PT2VHF APRS Client.',
        project: 'PT2VHF APRS Client est un client APRS moderne et multiplateforme pour la carte, les messages, les statistiques et l’analyse du réseau.',
        contactTitle: 'Contact / Suggestions / Questions / Améliorations',
        contact: 'Les suggestions, questions, signalements de problèmes et idées d’amélioration sont les bienvenus.',
        promoteTitle: 'Promouvoir le projet sur le réseau APRS',
        promote: 'Vous pouvez envoyer manuellement une annonce APRS pour promouvoir le client. Le message peut être vérifié avant l’envoi.',
        promoteButton: 'Promouvoir PT2VHF APRS Client sur APRS',
        eyebrow: 'Promotion APRS',
        modalTitle: 'Envoyer une annonce PT2VHF APRS Client',
        modalDescription: 'Vérifiez le message. L’annonce sera transmise une seule fois avec votre indicatif actuel comme expéditeur.',
        messageLabel: 'Message de l’annonce',
        send: 'Confirmer et envoyer',
        cancel: 'Annuler',
        confirm: 'Envoyer cette annonce APRS maintenant ? Votre indicatif actuel sera utilisé comme expéditeur.',
        sent: 'Annonce PT2VHF APRS Client envoyée.',
        download: `PT2VHF APRS Client v${version} - Téléchargement: tiny.cc/aprs`,
      },
    };
    return copies[state.language] || copies['pt-BR'];
  }

  function promotionPacketPreview(text = '') {
    const source = normalizedCall(state.ownCallsign) || 'NOCALL';
    return `${source}>APZVHF,TCPIP*::BLNA     :${String(text || '').slice(0, 67)}`;
  }

  function updatePromotionPreview() {
    const input = $('#promotionMessageText');
    if (!input) return;
    const text = String(input.value || '').slice(0, 67);
    $('#promotionCharCount').textContent = `${text.length} / 67`;
    $('#promotionPacketPreview').textContent = promotionPacketPreview(text);
  }

  function renderAbout() {
    const copy = aboutCopy();
    if ($('#aboutTitle')) $('#aboutTitle').textContent = copy.title;
    if ($('#aboutSubtitle')) $('#aboutSubtitle').textContent = copy.subtitle;
    if ($('#aboutAuthorText')) $('#aboutAuthorText').textContent = copy.author;
    if ($('#aboutProjectText')) $('#aboutProjectText').textContent = copy.project;
    if ($('#aboutContactTitle')) $('#aboutContactTitle').textContent = copy.contactTitle;
    if ($('#aboutContactText')) $('#aboutContactText').textContent = copy.contact;
    if ($('#aboutPromoteTitle')) $('#aboutPromoteTitle').textContent = copy.promoteTitle;
    if ($('#aboutPromoteText')) $('#aboutPromoteText').textContent = copy.promote;
    if ($('#aboutPromoteButton')) $('#aboutPromoteButton').textContent = copy.promoteButton;
    if (!$('#promotionModal')?.classList.contains('hidden')) {
      $('#promotionEyebrow').textContent = copy.eyebrow;
      $('#promotionModalTitle').textContent = copy.modalTitle;
      $('#promotionModalDescription').textContent = copy.modalDescription;
      $('#promotionMessageLabel').textContent = copy.messageLabel;
      $('#promotionSendButton').textContent = copy.send;
      $('#promotionCancelButton').textContent = copy.cancel;
      const input = $('#promotionMessageText');
      if (input && !input.dataset.userEdited) input.value = copy.download;
      updatePromotionPreview();
    }
  }

  function openPromotionModal() {
    const copy = aboutCopy();
    $('#promotionEyebrow').textContent = copy.eyebrow;
    $('#promotionModalTitle').textContent = copy.modalTitle;
    $('#promotionModalDescription').textContent = copy.modalDescription;
    $('#promotionMessageLabel').textContent = copy.messageLabel;
    $('#promotionSendButton').textContent = copy.send;
    $('#promotionCancelButton').textContent = copy.cancel;
    const input = $('#promotionMessageText');
    if (input) {
      input.dataset.userEdited = '';
      input.value = copy.download.slice(0, 67);
    }
    updatePromotionPreview();
    $('#promotionModal')?.classList.remove('hidden');
  }

  $('#aboutPromoteButton')?.addEventListener('click', openPromotionModal);
  $('#promotionCancelButton')?.addEventListener('click', () => $('#promotionModal')?.classList.add('hidden'));
  $('#promotionMessageText')?.addEventListener('input', event => {
    event.target.dataset.userEdited = '1';
    updatePromotionPreview();
  });
  $('#promotionSendButton')?.addEventListener('click', async () => {
    const copy = aboutCopy();
    const message = String($('#promotionMessageText')?.value || '').trim().slice(0, 67);
    if (!message) {
      toast(ui('Informe o texto do anúncio.', 'Enter the announcement text.'), 'error');
      return;
    }
    if (!window.confirm(copy.confirm)) return;
    const button = $('#promotionSendButton');
    if (button) button.disabled = true;
    try {
      await api('/api/messages/send', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ type:'announcement', bulletin_id:'A', message })
      });
      $('#promotionModal')?.classList.add('hidden');
      toast(copy.sent, 'ok');
      void loadMessages({ scrollToNewest:true });
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      if (button) button.disabled = false;
    }
  });

  function syncMapContextBar() {
    const visible = state.activeTab === 'map';
    $('#mapContextBar')?.classList.toggle('hidden', !visible);
    document.body.classList.toggle('map-context-visible', visible);
    const panel = $('.map-traffic-panel');
    const button = $('#mapHistoryToggle');
    if (panel) panel.classList.toggle('hidden', !visible || !state.mapHistoryOpen);
    if (button) {
      button.classList.toggle('active-filter', state.mapHistoryOpen);
      button.setAttribute('aria-expanded', state.mapHistoryOpen ? 'true' : 'false');
      button.textContent = ui('Histórico', 'History');
    }
  }

  function activateTab(tab) {
    state.activeTab = tab;
    $$('.tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    $$('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${tab}`));
    syncMapContextBar();
    if (tab === 'map') {
      setTimeout(() => state.map?.invalidateSize(), 30);
      void loadMapData();
      void pollTrafficEvents();
    }
    if (tab === 'messages') {
      $('.tab[data-tab="messages"]')?.classList.remove('has-unread');
      loadMessages({ scrollToNewest: true });
    }
    if (tab === 'stations') loadStations({ scrollToNewest: true });
    if (tab === 'log') loadLog(true);
    if (tab === 'analysis') refreshTopologyAnalysis();
    if (tab === 'config') loadConfig();
    if (tab === 'about') renderAbout();
  }

  $('#mapHistoryToggle')?.addEventListener('click', () => {
    state.mapHistoryOpen = !state.mapHistoryOpen;
    localStorage.setItem('pt2vhf_map_history_open', state.mapHistoryOpen ? '1' : '0');
    syncMapContextBar();
    setTimeout(() => state.map?.invalidateSize(), 30);
  });

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
    const statisticsSize = Math.min(20, Math.max(11, Number(cfg.statistics_font_size || 13)));
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
    root.style.setProperty('--statistics-font-size', `${statisticsSize}px`);
  }

  function applyMapPreferences(cfg = {}) {
    state.mapConfig = {
      map_type: localStorage.getItem('pt2vhf_map_type_quick') || cfg.map_type || state.mapConfig.map_type || 'osm',
      track_color: cfg.track_color || state.mapConfig.track_color || '#3ba6ff',
      track_width: Number(cfg.track_width || state.mapConfig.track_width || 2),
      topology_rf_color: cfg.topology_rf_color || state.mapConfig.topology_rf_color || '#ffff00',
      topology_igate_color: cfg.topology_igate_color || state.mapConfig.topology_igate_color || '#ffff00',
      topology_width: Number(cfg.topology_width || state.mapConfig.topology_width || 1),
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

      const quickType = $('#mapTypeQuick');
      if (quickType) quickType.value = state.mapConfig.map_type;
      state.topologyEnabled = !!(state.rfLinksEnabled || state.igateLinksEnabled);
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

    const visualPane = state.map.createPane('pt2vhfVisualPane');
    visualPane.style.zIndex = '450';
    visualPane.style.pointerEvents = 'none';

    const markerPane = state.map.createPane('pt2vhfMarkerPane');
    markerPane.style.zIndex = '650';
    markerPane.style.pointerEvents = 'auto';

    applyMapPreferences(cfg);
    addBrowserLocationControl(state.map);
    addMapControls();
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
    return [0, 1, 6, 12, 24, 168].includes(parsed) ? parsed : 0;
  }

  function topologyPeriodLabel(hours = state.topologyHours) {
    if (Number(hours) === 0) return ui('Completo', 'Complete');
    if (Number(hours) === 168) return ui('7 dias', '7 days');
    return `${Number(hours)} h`;
  }

  function addMapControls() {
    state.mapPeriodHours = topologyPeriodValue(state.mapPeriodHours);
    state.topologyHours = state.mapPeriodHours;
    state.topologyEnabled = !!(state.rfLinksEnabled || state.igateLinksEnabled);

    const period = $('#mapPeriodHours');
    if (period) period.value = String(state.mapPeriodHours);

    const itemBindings = [
      ['#mapItemStations', 'stationsEnabled', 'pt2vhf_map_item_stations'],
      ['#mapItemObjects', 'objectsEnabled', 'pt2vhf_map_item_objects'],
      ['#mapItemTracklogs', 'tracklogEnabled', 'pt2vhf_map_item_tracklogs'],
      ['#mapItemRfLinks', 'rfLinksEnabled', 'pt2vhf_map_item_rf'],
      ['#mapItemIgateLinks', 'igateLinksEnabled', 'pt2vhf_map_item_igate'],
      ['#mapItemPackets', 'packetsEnabled', 'pt2vhf_map_item_packets'],
    ];

    for (const [selector, key, storageKey] of itemBindings) {
      const input = $(selector);
      if (!input) continue;
      input.checked = !!state[key];
      if (input.dataset.bound === '1') continue;
      input.dataset.bound = '1';
      input.addEventListener('change', async () => {
        state[key] = input.checked;
        localStorage.setItem(storageKey, state[key] ? '1' : '0');
        state.topologyEnabled = !!(state.rfLinksEnabled || state.igateLinksEnabled);
        if (!state.packetsEnabled) clearTrafficReplayLayers();
        await loadMapData();
        if (state.topologyEnabled) await loadTopology();
        else clearTopologyLines();
        updateMapLegend();
      });
    }

    if (period && period.dataset.bound !== '1') {
      period.dataset.bound = '1';
      period.addEventListener('change', async () => {
        state.mapPeriodHours = topologyPeriodValue(period.value);
        state.topologyHours = state.mapPeriodHours;
        state.replayWindowStart = null;
        state.replayWindowEnd = null;
        localStorage.setItem('pt2vhf_map_period_hours', String(state.mapPeriodHours));
        if ($('#analysisPeriod')) $('#analysisPeriod').value = String(state.mapPeriodHours);
        await loadMapData();
        if (state.topologyEnabled) await loadTopology();
        stopTrafficTimer();
        state.trafficPlaying = false;
        state.trafficOverview = null;
        if (state.trafficMode === 'history') {
          try { await loadTrafficHistory(true); } catch (_) {}
        }
        updateTrafficAnimationUi();
      });
    }

    const button = $('#mapItemsButton');
    const menu = $('#mapItemsMenu');
    if (button && menu && button.dataset.bound !== '1') {
      button.dataset.bound = '1';

      const positionMapItemsMenu = () => {
        if (menu.classList.contains('hidden')) return;
        const rect = button.getBoundingClientRect();
        const margin = 6;
        const width = Math.max(225, menu.offsetWidth || 225);
        const maxLeft = Math.max(margin, window.innerWidth - width - margin);
        const left = Math.min(Math.max(margin, rect.left), maxLeft);
        menu.style.left = `${Math.round(left)}px`;
        menu.style.top = `${Math.round(rect.bottom + 5)}px`;
      };

      const closeMapItemsMenu = () => {
        menu.classList.add('hidden');
        button.setAttribute('aria-expanded', 'false');
      };

      button.addEventListener('click', event => {
        event.preventDefault();
        event.stopPropagation();
        const willOpen = menu.classList.contains('hidden');
        if (willOpen) {
          menu.classList.remove('hidden');
          button.setAttribute('aria-expanded', 'true');
          requestAnimationFrame(positionMapItemsMenu);
        } else {
          closeMapItemsMenu();
        }
      });

      menu.addEventListener('click', event => event.stopPropagation());
      document.addEventListener('click', closeMapItemsMenu);
      window.addEventListener('resize', positionMapItemsMenu);
      window.addEventListener('scroll', positionMapItemsMenu, true);
    }

    const mapType = $('#mapTypeQuick');
    if (mapType) {
      mapType.value = state.mapConfig.map_type;
      if (mapType.dataset.bound !== '1') {
        mapType.dataset.bound = '1';
        mapType.addEventListener('change', () => {
          const value = ['osm', 'topo', 'satellite'].includes(mapType.value) ? mapType.value : 'osm';
          state.mapConfig.map_type = value;
          localStorage.setItem('pt2vhf_map_type_quick', value);
          const provider = MAP_PROVIDERS[value] || MAP_PROVIDERS.osm;
          if (state.baseLayer) state.map.removeLayer(state.baseLayer);
          state.baseLayer = L.tileLayer(provider.url, provider.options).addTo(state.map);
          state.baseLayer.bringToBack();
        });
      }
    }
  }

  function syncMapLegendCollapsed() {
    const root = state.mapLegendElement;
    if (!root) return;
    const body = root.querySelector('.map-legend-body');
    const button = root.querySelector('.map-legend-toggle');
    const collapsed = !!state.mapLegendCollapsed;
    body?.classList.toggle('hidden', collapsed);
    if (button) {
      button.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      button.textContent = collapsed ? `${ui('Legenda', 'Legend')} ▸` : `${ui('Legenda', 'Legend')} ▾`;
      button.title = collapsed ? ui('Expandir legenda', 'Expand legend') : ui('Minimizar legenda', 'Minimize legend');
    }
  }

  function addMapLegendControl(map) {
    const LegendControl = L.Control.extend({
      options: { position: 'bottomleft' },
      onAdd() {
        const wrapper = L.DomUtil.create('div', 'leaflet-control map-line-legend');
        wrapper.innerHTML = `
          <button type="button" class="map-legend-toggle"></button>
          <div class="map-legend-body">
            <div class="map-legend-item" data-legend="track"><span class="legend-line"></span><span>${ui('Tracklog', 'Tracklog')}</span></div>
            <div class="map-legend-item" data-legend="rf"><span class="legend-line"></span><span>${ui('Enlace RF', 'RF link')}</span></div>
            <div class="map-legend-item" data-legend="igate"><span class="legend-line"></span><span>${ui('Via IGate/APRS-IS', 'Via IGate/APRS-IS')}</span></div>
            <div class="map-legend-item" data-legend="replay"><span class="legend-line"></span><span>${ui('Animação temporal', 'Timeline replay')}</span></div>
            <div class="map-legend-item" data-legend="packet"><span class="legend-packet"></span><span>${ui('Pacote em movimento', 'Moving packet')}</span></div>
          </div>`;
        L.DomEvent.disableClickPropagation(wrapper);
        L.DomEvent.disableScrollPropagation(wrapper);
        wrapper.querySelector('.map-legend-toggle')?.addEventListener('click', () => {
          state.mapLegendCollapsed = !state.mapLegendCollapsed;
          try { localStorage.setItem('pt2vhf_map_legend_collapsed', state.mapLegendCollapsed ? '1' : '0'); } catch (_) {}
          syncMapLegendCollapsed();
        });
        state.mapLegendElement = wrapper;
        syncMapLegendCollapsed();
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
    root.querySelector('[data-legend="track"]')?.classList.toggle('legend-muted', !state.tracklogEnabled);
    root.querySelector('[data-legend="rf"]')?.classList.toggle('legend-muted', !state.rfLinksEnabled);
    root.querySelector('[data-legend="igate"]')?.classList.toggle('legend-muted', !state.igateLinksEnabled);
    const packetAnimating = state.trafficPlaying || state.trafficReplayLayers.size > 0;
    root.querySelector('[data-legend="replay"]')?.classList.toggle('legend-muted', !state.timelineReplayActive);
    root.querySelector('[data-legend="packet"]')?.classList.toggle('legend-muted', !state.packetsEnabled || !packetAnimating);
  }

  function clearTopologyLines() {
    for (const line of state.topologyLines.values()) state.map?.removeLayer(line);
    state.topologyLines.clear();
  }

  async function loadTopology() {
    if (!state.map || !state.topologyEnabled || state.activeTab !== 'map') return;
    if (state.topologyLoadBusy) return;
    state.topologyLoadBusy = true;
    try {
      const edges = await api(`/api/topology?hours=${encodeURIComponent(state.mapPeriodHours)}`);
      const active = new Set();

      for (const edge of edges) {
        if (edge.kind === 'igate' && !state.igateLinksEnabled) continue;
        if (edge.kind !== 'igate' && !state.rfLinksEnabled) continue;
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
          dashArray: edge.kind === 'igate' ? '7 5' : null,
          interactive: false,
          pane: 'pt2vhfVisualPane'
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
    } finally {
      state.topologyLoadBusy = false;
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
            pane: 'pt2vhfMarkerPane',
            zIndexOffset: 1800
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
              fillOpacity: .08,
              interactive: false,
              pane: 'pt2vhfVisualPane'
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

  function formatRelativeLastHeard(value) {
    const ms = stationLastHeardMs({ last_heard: value });
    if (!Number.isFinite(ms)) return '';

    const totalMinutes = Math.max(0, Math.floor((Date.now() - ms) / 60000));
    const language = normalizeLanguage(state.language);

    if (totalMinutes < 1) {
      if (language === 'en') return 'less than 1 min ago';
      if (language === 'es') return 'hace menos de 1 min';
      if (language === 'fr') return 'il y a moins de 1 min';
      return 'há menos de 1 min';
    }

    if (totalMinutes < 60) {
      if (language === 'en') return `${totalMinutes} min ago`;
      if (language === 'es') return `hace ${totalMinutes} min`;
      if (language === 'fr') return `il y a ${totalMinutes} min`;
      return `há ${totalMinutes} min`;
    }

    if (totalMinutes < 1440) {
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;
      if (language === 'en') return minutes ? `${hours} h and ${minutes} min ago` : `${hours} h ago`;
      if (language === 'es') return minutes ? `hace ${hours} h y ${minutes} min` : `hace ${hours} h`;
      if (language === 'fr') return minutes ? `il y a ${hours} h et ${minutes} min` : `il y a ${hours} h`;
      return minutes ? `há ${hours} h e ${minutes} min` : `há ${hours} h`;
    }

    const days = Math.floor(totalMinutes / 1440);
    if (language === 'en') return `${days} day${days === 1 ? '' : 's'} ago`;
    if (language === 'es') return `hace ${days} día${days === 1 ? '' : 's'}`;
    if (language === 'fr') return `il y a ${days} jour${days === 1 ? '' : 's'}`;
    return `há ${days} dia${days === 1 ? '' : 's'}`;
  }

  function refreshStationPopupRelativeTimes() {
    document.querySelectorAll('.station-last-heard-relative').forEach(element => {
      const relative = formatRelativeLastHeard(element.dataset.lastHeard || '');
      element.textContent = relative ? ` — ${relative}` : '';
    });
  }

  function popupHtml(s) {
    let path = '';
    try { path = JSON.parse(s.path || '[]').join(','); } catch (_) { path = s.path || ''; }
    const lastHeardDate = fmtDate(s.last_heard);
    const lastHeardRelative = formatRelativeLastHeard(s.last_heard);
    const lastHeardMarkup = `${escapeHtml(lastHeardDate)}<span class="station-last-heard-relative" data-last-heard="${escapeHtml(String(s.last_heard ?? ''))}">${lastHeardRelative ? ` — ${escapeHtml(lastHeardRelative)}` : ''}</span>`;
    return `<div class="station-popup">
      <h3>${aprsSymbolHtml(s.symbol_table || '/', s.symbol || '>', 24)} ${escapeHtml(s.name || s.callsign)}</h3>
      <div class="popup-grid">
        <strong>Indicativo</strong><span>${escapeHtml(s.callsign)}</span>
        <strong>${ui('Última recepção', 'Last heard')}</strong><span>${lastHeardMarkup}</span>
        <strong>Posição</strong><span>${fmtNum(s.latitude, 6)}, ${fmtNum(s.longitude, 6)}</span>
        <strong>Velocidade</strong><span>${fmtNum(s.speed, 1, ' km/h')}</span>
        <strong>Curso</strong><span>${fmtNum(s.course, 0, '°')}</span>
        <strong>Altitude</strong><span>${fmtNum(s.altitude, 1, ' m')}</span>
        <strong>Informação</strong><span>${escapeHtml(s.info || '')}</span>
        <strong>Via</strong><span>${escapeHtml(path)}</span>
      </div>
      <div class="station-query-actions">
        <div class="station-query-title">Diagnóstico / Queries APRS</div>
        <div class="station-query-buttons">
          <button type="button" class="btn secondary station-query-button" data-query-type="APRSP" data-callsign="${escapeHtml(s.callsign)}">Posição</button>
          <button type="button" class="btn secondary station-query-button" data-query-type="APRSS" data-callsign="${escapeHtml(s.callsign)}">Status</button>
          <button type="button" class="btn secondary station-query-button" data-query-type="APRSD" data-callsign="${escapeHtml(s.callsign)}">Ouvidos</button>
          <button type="button" class="btn secondary station-query-button" data-query-type="PINGACK" data-callsign="${escapeHtml(s.callsign)}">Ping/ACK</button>
          <button type="button" class="btn secondary station-query-button" data-query-type="APRST" data-callsign="${escapeHtml(s.callsign)}">Trace</button>
        </div>
        <div class="station-query-result" data-query-result="${escapeHtml(s.callsign)}">${queryResultMarkup(state.queryLastByStation.get(normalizedCall(s.callsign)) || null)}</div>
        <button type="button" class="btn secondary station-query-history-button" data-callsign="${escapeHtml(s.callsign)}">Ver histórico de queries</button>
        <div class="station-query-history hidden" data-query-history="${escapeHtml(s.callsign)}"></div>
      </div>
      <div class="station-popup-actions">
        ${favoriteStarHtml(s.callsign, false)}
        <button type="button" class="btn secondary station-log-button" data-callsign="${escapeHtml(s.callsign)}">Ver logs</button>
        <button type="button" class="btn primary station-message-button" data-callsign="${escapeHtml(s.callsign)}">Enviar mensagem</button>
      </div>
    </div>`;
  }

  function stationLastHeardMs(station) {
    const raw = station?.last_heard;
    if (raw === null || raw === undefined || raw === '') return null;
    if (typeof raw === 'number' && Number.isFinite(raw)) return raw < 100000000000 ? raw * 1000 : raw;
    const text = String(raw).trim();
    if (/^\d+(?:\.\d+)?$/.test(text)) {
      const n = Number(text);
      return Number.isFinite(n) ? (n < 100000000000 ? n * 1000 : n) : null;
    }
    const normalized = /^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}/.test(text) ? text.replace(' ', 'T') : text;
    const ms = Date.parse(normalized);
    return Number.isFinite(ms) ? ms : null;
  }

  function timestampWithinHours(value, hours) {
    const period = topologyPeriodValue(hours);
    if (period === 0) return true;
    const ms = stationLastHeardMs({ last_heard: value });
    if (!Number.isFinite(ms)) return false;
    return Math.max(0, Date.now() - ms) <= period * 60 * 60 * 1000;
  }

  function stationMatchesMapPeriod(station) {
    return !!state.stationsEnabled && timestampWithinHours(station?.last_heard, state.mapPeriodHours);
  }

  function objectMatchesMapPeriod(object) {
    return !!state.objectsEnabled && timestampWithinHours(object?.last_heard, state.mapPeriodHours);
  }

  function trackMatchesMapPeriod(track) {
    return !!state.tracklogEnabled && timestampWithinHours(track?.timestamp, state.mapPeriodHours);
  }

  function mapDistanceKm(a, b) {
    const lat1 = Number(a?.latitude), lon1 = Number(a?.longitude);
    const lat2 = Number(b?.latitude), lon2 = Number(b?.longitude);
    if (![lat1, lon1, lat2, lon2].every(Number.isFinite)) return 0;
    const r = 6371.0088;
    const rad = value => value * Math.PI / 180;
    const p1 = rad(lat1), p2 = rad(lat2);
    const dp = rad(lat2 - lat1), dl = rad(lon2 - lon1);
    const h = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    return r * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(Math.max(0, 1 - h)));
  }

  function splitTrackSegments(rows) {
    const segments = [];
    let current = [];
    let previous = null;
    for (const row of rows) {
      const lat = Number(row.latitude), lon = Number(row.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
      let split = false;
      if (previous) {
        const distance = mapDistanceKm(previous, row);
        const prevMs = stationLastHeardMs({ last_heard: previous.timestamp });
        const nowMs = stationLastHeardMs({ last_heard: row.timestamp });
        const elapsedHours = Number.isFinite(prevMs) && Number.isFinite(nowMs)
          ? Math.max((nowMs - prevMs) / 3600000, 1 / 3600)
          : 0;
        const impliedSpeed = elapsedHours > 0 ? distance / elapsedHours : 0;
        // Never draw a giant connecting line across a relocation or a corrupt position.
        split = distance >= 250 || (distance >= 75 && elapsedHours > 0 && impliedSpeed > 1200);
      }
      if (split) {
        if (current.length >= 2) segments.push(current);
        current = [];
      }
      current.push([lat, lon]);
      previous = row;
    }
    if (current.length >= 2) segments.push(current);
    return segments;
  }

  async function loadMapData() {
    if (!state.map || state.activeTab !== 'map') return;
    if (state.mapLoadBusy) return;
    state.mapLoadBusy = true;
    try {
      const data = await api('/api/map-data');
      const allStations = Array.isArray(data.stations) ? data.stations : [];
      const visibleStations = allStations.filter(stationMatchesMapPeriod);
      state.mapKnownCallsigns = new Set(allStations.map(station => normalizedCall(station.callsign)).filter(Boolean));
      state.mapVisibleCallsigns = new Set(visibleStations.map(station => normalizedCall(station.callsign)).filter(Boolean));

      const activeStations = new Set(visibleStations.map(station => station.callsign));
      for (const [call, marker] of state.markers) {
        if (!activeStations.has(call)) {
          state.map.removeLayer(marker);
          state.markers.delete(call);
        }
      }

      for (const station of visibleStations) {
        const latlng = [Number(station.latitude), Number(station.longitude)];
        if (!Number.isFinite(latlng[0]) || !Number.isFinite(latlng[1])) continue;
        let marker = state.markers.get(station.callsign);
        if (!marker) {
          marker = L.marker(latlng, {
            icon: markerIcon(station),
            title: station.callsign,
            interactive: true,
            pane: 'pt2vhfMarkerPane',
            zIndexOffset: 1200
          }).addTo(state.map);
          state.markers.set(station.callsign, marker);
        } else {
          marker.setLatLng(latlng).setIcon(markerIcon(station));
        }
        marker.setZIndexOffset(1200);
        marker.bindPopup(popupHtml(station), { maxWidth: 520 });
        if (marker._pt2vhfQueryPopupHandler) marker.off('popupopen', marker._pt2vhfQueryPopupHandler);
        marker._pt2vhfQueryPopupHandler = () => { void loadStationQueryHistory(station.callsign, false); };
        marker.on('popupopen', marker._pt2vhfQueryPopupHandler);
      }

      const visibleObjects = (Array.isArray(data.objects) ? data.objects : []).filter(objectMatchesMapPeriod);
      const activeObjects = new Set(visibleObjects.map(object => String(object.name || '')));
      for (const [name, marker] of state.objectMarkers) {
        if (!activeObjects.has(name)) {
          state.map.removeLayer(marker);
          state.objectMarkers.delete(name);
        }
      }
      for (const object of visibleObjects) {
        const latlng = [Number(object.latitude), Number(object.longitude)];
        if (![...latlng].every(Number.isFinite)) continue;
        const name = String(object.name || '').trim();
        if (!name) continue;
        let marker = state.objectMarkers.get(name);
        const icon = L.divIcon({
          className: 'aprs-object-marker-wrap',
          html: `<div class="aprs-object-marker">◆</div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });
        if (!marker) {
          marker = L.marker(latlng, {
            icon,
            title: name,
            interactive: true,
            pane: 'pt2vhfMarkerPane',
            zIndexOffset: 1400
          }).addTo(state.map);
          state.objectMarkers.set(name, marker);
        } else {
          marker.setLatLng(latlng).setIcon(icon);
        }
        marker.setZIndexOffset(1400);
        marker.bindPopup(`<div class="station-popup"><h3>${escapeHtml(name)}</h3>
          <div class="popup-grid"><strong>Tipo</strong><span>Objeto APRS</span>
          <strong>Origem</strong><span>${escapeHtml(object.source_callsign || '')}</span>
          <strong>Última recepção</strong><span>${escapeHtml(fmtDate(object.last_heard))}</span>
          <strong>Informação</strong><span>${escapeHtml(object.info || '')}</span></div></div>`);
      }

      const grouped = new Map();
      if (state.tracklogEnabled) {
        for (const track of (Array.isArray(data.tracks) ? data.tracks : [])) {
          if (!trackMatchesMapPeriod(track)) continue;
          if (!grouped.has(track.callsign)) grouped.set(track.callsign, []);
          grouped.get(track.callsign).push(track);
        }
      }

      const drawable = new Map();
      for (const [call, rows] of grouped) {
        const segments = splitTrackSegments(rows);
        if (segments.length) drawable.set(call, segments);
      }

      for (const [call, line] of state.trackLines) {
        if (!drawable.has(call)) {
          state.map.removeLayer(line);
          state.trackLines.delete(call);
        }
      }

      for (const [call, segments] of drawable) {
        let line = state.trackLines.get(call);
        if (!line) {
          line = L.polyline(segments, {
            color: state.mapConfig.track_color,
            weight: state.mapConfig.track_width,
            opacity: .78,
            interactive: false,
            pane: 'pt2vhfVisualPane'
          }).addTo(state.map);
          state.trackLines.set(call, line);
        } else {
          line.setLatLngs(segments);
          line.setStyle({
            color: state.mapConfig.track_color,
            weight: state.mapConfig.track_width,
            opacity: .78
          });
        }
      }
      updateMapLegend();
      if (state.topologyEnabled) await loadTopology();
    } catch (err) {
      console.warn(err);
    } finally {
      state.mapLoadBusy = false;
      state.mapLoadLastAt = Date.now();
      if (state.mapLoadQueued) {
        state.mapLoadQueued = false;
        setTimeout(() => { void loadMapData(); }, 0);
      }
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
    if (!call || !state.map || state.activeTab !== 'map') return;

    // Nunca dispara refresh completo do mapa a partir de um evento individual.
    // Estações sem posição/marcador aguardam o refresh periódico normal.
    if (!state.markers.has(call) || !stationIsVisible(call)) return;

    pulseStation(call);
    playStationActivitySound(call);
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
    if (!state.map || !state.packetsEnabled) return Promise.resolve();

    const from = [Number(segment.source_lat), Number(segment.source_lon)];
    if (!from.every(Number.isFinite)) return Promise.resolve();

    const isInternet = segment.kind === 'igate';
    const segmentColor = isInternet ? state.mapConfig.topology_igate_color : '#ffd54a';

    if (segment.internet_handoff) {
      if (!state.igateLinksEnabled && !state.packetsEnabled) return Promise.resolve();
      const halo = L.circleMarker(from, {
        radius: 7,
        color: segmentColor,
        weight: 2,
        dashArray: '5 4',
        fillOpacity: .08,
        opacity: .95,
        interactive: false,
        pane: 'pt2vhfVisualPane'
      }).addTo(state.map);
      state.trafficReplayLayers.add(halo);
      const label = L.tooltip({ permanent: false, direction: 'top', opacity: .9 })
        .setLatLng(from)
        .setContent('APRS-IS')
        .addTo(state.map);
      state.trafficReplayLayers.add(label);
      const start = performance.now();
      return new Promise(resolve => {
        const tick = now => {
          const t = Math.min(1, (now - start) / Math.max(120, durationMs));
          halo.setRadius(7 + 22 * t);
          halo.setStyle({ opacity: 1 - .7 * t, fillOpacity: .12 * (1 - t) });
          if (t < 1) requestAnimationFrame(tick);
          else {
            setTimeout(() => {
              try { state.map?.removeLayer(halo); } catch (_) {}
              try { state.map?.removeLayer(label); } catch (_) {}
              state.trafficReplayLayers.delete(halo);
              state.trafficReplayLayers.delete(label);
            }, 350);
            resolve();
          }
        };
        requestAnimationFrame(tick);
      });
    }

    const to = [Number(segment.target_lat), Number(segment.target_lon)];
    if (!to.every(Number.isFinite)) return Promise.resolve();
    if (!trafficSegmentVisible(segment)) return Promise.resolve();

    let trail = null;
    const showLink = isInternet ? state.igateLinksEnabled : state.rfLinksEnabled;
    if (showLink) {
      trail = L.polyline([from, to], {
        color: segmentColor,
        weight: Math.max(2, Number(state.mapConfig.topology_width || 1) + 1),
        opacity: .72,
        dashArray: isInternet ? '8 6' : null,
        interactive: false,
        pane: 'pt2vhfVisualPane'
      }).addTo(state.map);
      state.trafficReplayLayers.add(trail);
    }

    const particle = L.circleMarker(from, {
      radius: 6,
      color: '#ffffff',
      weight: 1,
      fillColor: segmentColor,
      fillOpacity: .95,
      opacity: .95,
      interactive: false,
      pane: 'pt2vhfVisualPane'
    }).addTo(state.map);
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
          stationActivity(segment.target);
          setTimeout(() => {
            try { state.map?.removeLayer(particle); } catch (_) {}
            if (trail) {
              try { state.map?.removeLayer(trail); } catch (_) {}
              state.trafficReplayLayers.delete(trail);
            }
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
    const hours = topologyPeriodValue(state.mapPeriodHours);
    const params = new URLSearchParams({ bins: '140' });
    params.set('hours', String(hours));
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
    if (!event || !state.packetsEnabled) return;
    stationActivity(event.source);
    const speed = Math.max(.25, Number(state.trafficSpeed || 1));
    const duration = Math.max(90, 900 / speed);
    state.timelineReplayActive = state.trafficMode === 'history';
    updateMapLegend();

    // Reproduz o path observado hop a hop, na ordem real do cabeçalho APRS.
    // Assim, uma resposta/ACK que retorne pelos mesmos digipeaters percorre
    // visualmente o caminho inverso, em vez de aparecer como um enlace direto.
    for (const segment of (event.segments || [])) {
      await animateTrafficSegment(segment, event, duration);
    }

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


  function setTrafficSpeed(value, source = '') {
    const parsed = Number(value || 1);
    state.trafficSpeed = [0.5, 1, 2, 5].includes(parsed) ? parsed : 1;
    localStorage.setItem('pt2vhf_traffic_speed', String(state.trafficSpeed));

    const replaySelect = $('#trafficSpeed');
    const topologySelect = $('#topologySpeed');
    if (replaySelect && source !== 'replay') replaySelect.value = String(state.trafficSpeed);
    if (topologySelect && source !== 'topology') topologySelect.value = String(state.trafficSpeed);

    updateTrafficAnimationUi();
  }

  async function loadTrafficHistory(resetIndex = true, startTimestamp = '') {
    if (resetIndex || !state.trafficOverview) await loadTrafficOverview();
    const first = startTimestamp || state.trafficOverview?.first_timestamp || '';
    const hours = topologyPeriodValue(state.mapPeriodHours);
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
    if (state.trafficPollBusy || state.activeTab !== 'map') return;
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

      if (state.trafficPlaying && state.trafficMode === 'live') {
        for (const event of events.slice(-20)) {
          void animateTrafficEvent(event);
        }
      } else {
        const sources = [...new Set(events.map(event => normalizedCall(event.source)).filter(Boolean))].slice(-50);
        for (const source of sources) stationActivity(source);
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

  function resourceLevel(value) {
    const n = Number(value || 0);
    if (n >= 85) return 'critical';
    if (n >= 65) return 'warn';
    return 'normal';
  }

  async function refreshSystemMetrics() {
    if (state.systemMetricsBusy) return;
    state.systemMetricsBusy = true;
    try {
      const m = await api('/api/system-metrics');
      const cpu = Math.max(0, Number(m.cpu_percent || 0));
      const memMb = Math.max(0, Number(m.memory_mb || 0));
      const memPct = Math.max(0, Number(m.memory_percent || 0));
      const root = $('#systemResourceMeter');
      const cpuValue = $('#headerCpuUsage');
      const memValue = $('#headerMemoryUsage');
      const cpuBar = $('#headerCpuBar');
      const memBar = $('#headerMemoryBar');
      const cpuMetric = $('#cpuResourceMetric');
      const memMetric = $('#memoryResourceMetric');
      if (cpuValue) cpuValue.textContent = `${cpu.toFixed(cpu >= 10 ? 0 : 1)}%`;
      if (memValue) memValue.textContent = `${memMb.toFixed(0)} MB`;
      if (cpuBar) cpuBar.style.width = `${Math.min(100, cpu)}%`;
      if (memBar) memBar.style.width = `${Math.min(100, memPct)}%`;
      if (cpuMetric) cpuMetric.dataset.level = resourceLevel(cpu);
      if (memMetric) memMetric.dataset.level = resourceLevel(memPct);
      if (root) {
        const uptime = Number(m.uptime_seconds || 0);
        const h = Math.floor(uptime / 3600);
        const min = Math.floor((uptime % 3600) / 60);
        const sec = Math.floor(uptime % 60);
        root.title = [
          `CPU total do app: ${cpu.toFixed(1)}%`,
          `RAM: ${memMb.toFixed(1)} MB (${memPct.toFixed(1)}%)`,
          `Processos: ${Number(m.process_count || 0)}`,
          `Threads: ${Number(m.thread_count || 0)}`,
          `Requests HTTP ativos: ${Number(m.active_requests || 0)}`,
          `Fila TX: ${Number(m.tx_queue || 0)}`,
          `Uptime: ${String(h).padStart(2,'0')}:${String(min).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
        ].join('\n');
      }
    } catch (_) {
    } finally {
      state.systemMetricsBusy = false;
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
    if (state.groupMessages) {
      state.selectedConversation = destination;
      renderGroupedMessages();
    }
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
        if (state.conversationSortKey === 'date') {
          const timeDelta = String(a.last?.timestamp || '').localeCompare(String(b.last?.timestamp || '')) * factor;
          if (timeDelta) return timeDelta;
        } else {
          const senderDelta = a.contact.localeCompare(b.contact, currentLocale(), { numeric:true, sensitivity:'base' }) * factor;
          if (senderDelta) return senderDelta;
        }
        const favoriteDelta = Number(isFavorite(b.contact)) - Number(isFavorite(a.contact));
        if (favoriteDelta) return favoriteDelta;
        return a.contact.localeCompare(b.contact, currentLocale(), { numeric:true, sensitivity:'base' });
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

    const composerDestination = normalizedCall($('#messageTo')?.value);
    const own = normalizedCall(state.ownCallsign);
    const destinationConversation = composerDestination && (!own || composerDestination !== own)
      ? conversations.find(item => item.contact === composerDestination)
      : null;

    if (composerDestination && (!own || composerDestination !== own)) {
      state.selectedConversation = destinationConversation ? composerDestination : '';
    } else if (!state.selectedConversation || !conversations.some(item => item.contact === state.selectedConversation)) {
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

    const selected = conversations.find(item => item.contact === state.selectedConversation);
    if (!selected) {
      const destination = normalizedCall($('#messageTo')?.value);
      empty.textContent = destination
        ? ui(`Novo destinatário: ${destination}. Ainda não há conversa registrada com este indicativo.`, `New recipient: ${destination}. There is no recorded conversation with this callsign yet.`)
        : ui('Selecione uma conversa ou informe um destinatário.', 'Select a conversation or enter a recipient.');
      empty.classList.remove('hidden');
      content.classList.add('hidden');
      return;
    }

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
        ? ui(`Telemetria oculta (${hiddenCount} registro(s) nesta lista).`, `Telemetry hidden (${hiddenCount} record(s) in this list).`)
        : ui('Telemetria visível.', 'Telemetry visible.'),
      'ok'
    );
  });

  function updateGroupMessagesButton() {
    const btn = $('#groupMessagesButton');
    if (!btn) return;
    btn.classList.toggle('active-filter', state.groupMessages);
    btn.setAttribute('aria-pressed', state.groupMessages ? 'true' : 'false');
    btn.textContent = state.groupMessages
      ? ui('✓ Agrupado por remetente', '✓ Grouped by sender')
      : ui('Agrupar por remetente', 'Group by sender');
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

  $('#messageTo')?.addEventListener('input', () => {
    if (!state.groupMessages) return;
    const destination = normalizedCall($('#messageTo')?.value);
    const conversations = conversationItems();
    if (destination && conversations.some(item => item.contact === destination)) {
      state.selectedConversation = destination;
    } else if (destination) {
      state.selectedConversation = '';
    }
    renderGroupedMessages();
  });

  $('#messageTo')?.addEventListener('change', () => {
    if (!state.groupMessages) return;
    renderGroupedMessages();
  });

  $('#conversationSortKey')?.addEventListener('change', event => {
    state.conversationSortKey = event.target.value === 'date' ? 'date' : 'sender';
    localStorage.setItem('pt2vhf_conversation_sort_key', state.conversationSortKey);
    renderGroupedMessages();
  });
  if ($('#conversationSortKey')) $('#conversationSortKey').value = state.conversationSortKey;

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
    btn.textContent = state.myMessagesOnly
      ? ui('✓ Minhas mensagens', '✓ My messages')
      : ui('Minhas mensagens', 'My messages');
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
    if (!window.confirm(ui(
      'Apagar TODAS as mensagens e boletins armazenados neste computador? Somente o histórico local de mensagens será removido. Esta ação não pode ser desfeita.',
      'Delete ALL messages and bulletins stored on this computer? Only the local message history will be removed. This cannot be undone.'
    ))) return;
    try {
      const result = await api('/api/messages/clear', { method: 'POST' });
      state.messages = [];
      state.selectedConversation = '';
      renderMessages();
      updateUnread();
      localStorage.removeItem('pt2vhf_last_seen_msg');
      state.messageAlertBaselineReady = false;
      state.lastAlertedMessageId = 0;
      $('#messageBadge')?.classList.add('hidden');
      $('.tab[data-tab="messages"]')?.classList.remove('has-unread');
      toast(ui(
        `Histórico de mensagens apagado (${Number(result.deleted || 0)} registro(s)).`,
        `Message history deleted (${Number(result.deleted || 0)} record(s)).`
      ), 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  $('#clearMessagesMaintenanceButton')?.addEventListener('click', () => {
    $('#clearMessagesButton')?.click();
  });

  $('#messageTo').addEventListener('input', debounce(async (ev) => {
    try {
      const list = await api(`/api/callsigns?prefix=${encodeURIComponent(ev.target.value)}`);
      $('#destinationList').innerHTML = list.map(call => `<option value="${escapeHtml(call)}" label="${isFavorite(call) ? '★ ' + escapeHtml(ui('Favorita', 'Favorite')) : ''}"></option>`).join('');
    } catch (_) {}
  }, 180));

  function queryTypeLabel(type) {
    const labels = {
      APRSP: ui('Posição', 'Position'),
      APRSS: ui('Status', 'Status'),
      APRSD: ui('Ouvidos', 'Direct heard'),
      APRSH: ui('Heard', 'Heard'),
      APRSO: ui('Objetos', 'Objects'),
      APRST: ui('Trace', 'Trace'),
      PING: ui('Trace/PING?', 'Trace/PING?'),
      PINGACK: ui('Ping/ACK', 'Ping/ACK')
    };
    return labels[String(type || '').toUpperCase()] || String(type || ui('Query', 'Query'));
  }

  function queryResultMarkup(query) {
    if (!query) {
      return '<div class="station-query-result-title"><span>' +
        escapeHtml(ui('Resultado da última query', 'Latest query result')) +
        '</span></div><div class="hint">' +
        escapeHtml(ui('Nenhuma query executada recentemente para esta estação.', 'No recent query has been run for this station.')) +
        '</div>';
    }

    const status = String(query.status || '');
    const rtt = Number(query.rtt_ms);
    const rttText = Number.isFinite(rtt) ? Math.round(rtt).toLocaleString(currentLocale()) + ' ms' : '';
    const response = String(query.response_text || '').trim();
    const trace = Array.isArray(query.trace_path_list)
      ? query.trace_path_list
      : (() => {
          try { return JSON.parse(query.trace_path || '[]'); } catch (_) { return []; }
        })();
    const traceNodes = Array.isArray(query.trace_nodes) ? query.trace_nodes : [];
    const located = traceNodes.filter(node => node?.known).length;
    const statusClass = status === 'Respondida' ? 'query-status-ok'
      : (status === 'Aguardando resposta' || status === 'Enviando' ? '' : 'query-status-error');
    const sentAt = query.sent_at ? fmtDate(query.sent_at) : '';
    const traceText = trace.length ? trace.join(' → ') : '';
    const traceSummary = trace.length
      ? '<div class="station-query-response"><strong>' +
        escapeHtml(ui('Caminho:', 'Path:')) + '</strong> ' + escapeHtml(traceText) +
        (traceNodes.length ? '<br><span class="hint">' +
          escapeHtml(ui(
            located + '/' + traceNodes.length + ' hops com posição conhecida.',
            located + '/' + traceNodes.length + ' hops with known position.'
          )) + '</span>' : '') + '</div>'
      : '';

    return '<div class="station-query-result-title"><span>' +
      escapeHtml(ui('Resultado da última query', 'Latest query result')) +
      '</span><span class="' + statusClass + '">' + escapeHtml(status || ui('Sem estado', 'No status')) + '</span></div>' +
      '<div class="station-query-result-grid">' +
      '<strong>' + escapeHtml(ui('Query', 'Query')) + '</strong><span>' + escapeHtml(queryTypeLabel(query.query_type)) + '</span>' +
      (sentAt ? '<strong>' + escapeHtml(ui('Enviada', 'Sent')) + '</strong><span>' + escapeHtml(sentAt) + '</span>' : '') +
      (rttText ? '<strong>RTT</strong><span>' + escapeHtml(rttText) + '</span>' : '') +
      '</div>' +
      (response ? '<div class="station-query-response">' + escapeHtml(response) + '</div>' : '') +
      traceSummary;
  }

  function queryResultElement(callsign) {
    const call = normalizedCall(callsign);
    return [...document.querySelectorAll('.station-query-result')].find(
      el => normalizedCall(el.dataset.queryResult || '') === call
    ) || null;
  }

  function queryHistoryElement(callsign) {
    const call = normalizedCall(callsign);
    return [...document.querySelectorAll('.station-query-history')].find(
      el => normalizedCall(el.dataset.queryHistory || '') === call
    ) || null;
  }

  function setStationQueryResult(callsign, query) {
    const call = normalizedCall(callsign);
    if (!call) return;
    if (query) state.queryLastByStation.set(call, query);
    const el = queryResultElement(call);
    if (el) el.innerHTML = queryResultMarkup(query || state.queryLastByStation.get(call) || null);
  }

  function renderStationQueryHistory(callsign, rows) {
    const el = queryHistoryElement(callsign);
    if (!el) return;
    const items = Array.isArray(rows) ? rows : [];
    if (!items.length) {
      el.innerHTML = '<div class="hint">' + escapeHtml(ui('Nenhuma query registrada para esta estação.', 'No queries recorded for this station.')) + '</div>';
      return;
    }
    el.innerHTML = items.map(item => {
      const rtt = Number(item.rtt_ms);
      const rttText = Number.isFinite(rtt) ? ' · ' + Math.round(rtt).toLocaleString(currentLocale()) + ' ms' : '';
      return '<div class="station-query-history-item"><strong>' +
        escapeHtml(queryTypeLabel(item.query_type)) + '</strong> · ' +
        escapeHtml(String(item.status || '')) + rttText +
        '<br><span>' + escapeHtml(fmtDate(item.sent_at)) + '</span></div>';
    }).join('');
  }

  async function loadStationQueryHistory(callsign, showHistory = false) {
    const call = normalizedCall(callsign);
    if (!call) return [];
    try {
      const rows = await api('/api/queries?station=' + encodeURIComponent(call) + '&limit=12');
      let latest = Array.isArray(rows) && rows.length ? rows[0] : null;
      if (latest && ['APRST','PING'].includes(String(latest.query_type || '').toUpperCase())) {
        try { latest = await api('/api/queries/' + Number(latest.id)); } catch (_) {}
      }
      if (latest) setStationQueryResult(call, latest);
      else setStationQueryResult(call, null);
      if (showHistory) renderStationQueryHistory(call, rows);
      return rows || [];
    } catch (err) {
      if (showHistory) {
        const el = queryHistoryElement(call);
        if (el) el.innerHTML = '<div class="query-status-error">' + escapeHtml(err.message) + '</div>';
      }
      return [];
    }
  }

  function drawQueryTrace(query) {
    if (!state.map) return;
    clearQueryTrace();
    const nodes = Array.isArray(query?.trace_nodes) ? query.trace_nodes : [];
    const known = nodes.filter(n => n.known && Number.isFinite(Number(n.latitude)) && Number.isFinite(Number(n.longitude)));
    if (!known.length) return;

    for (const node of known) {
      const point = [Number(node.latitude), Number(node.longitude)];
      const marker = L.marker(point, {
        icon: L.divIcon({
          className: 'query-trace-node',
          html: '<span>' + escapeHtml(node.callsign) + '</span>',
          iconSize: [62, 27],
          iconAnchor: [31, 13]
        }),
        interactive: true,
        pane: 'pt2vhfMarkerPane',
        zIndexOffset: 1600,
        title: node.callsign
      }).addTo(state.map);
      marker.bindTooltip(node.callsign, { direction: 'top' });
      state.queryTraceLayers.add(marker);
    }

    for (let i = 0; i + 1 < nodes.length; i++) {
      const a = nodes[i], b = nodes[i + 1];
      if (!a?.known || !b?.known) continue;
      const points = [
        [Number(a.latitude), Number(a.longitude)],
        [Number(b.latitude), Number(b.longitude)]
      ];
      if (!points.flat().every(Number.isFinite)) continue;
      const line = L.polyline(points, {
        color: '#ffb347',
        weight: 4,
        opacity: .92,
        dashArray: '8 6',
        interactive: false,
        pane: 'pt2vhfVisualPane'
      }).addTo(state.map);
      state.queryTraceLayers.add(line);
    }

    const bounds = L.latLngBounds(known.map(n => [Number(n.latitude), Number(n.longitude)]));
    if (bounds.isValid()) state.map.fitBounds(bounds.pad(.18), { maxZoom: 13 });
  }

  async function pollQueryResult(queryId, callsign) {
    const key = Number(queryId);
    if (!key) return;
    const previous = state.queryPollers.get(key);
    if (previous) clearTimeout(previous);

    try {
      const query = await api('/api/queries/' + key);
      const waiting = query?.status === 'Aguardando resposta';
      setStationQueryResult(callsign, query);
      if (query?.status === 'Respondida' && ['APRST','PING'].includes(String(query.query_type || ''))) {
        drawQueryTrace(query);
      }
      if (waiting) {
        const timer = setTimeout(() => void pollQueryResult(key, callsign), 1000);
        state.queryPollers.set(key, timer);
      } else {
        state.queryPollers.delete(key);
      }
    } catch (err) {
      state.queryPollers.delete(key);
      setStationQueryResult(callsign, {
        query_type: state.queryLastByStation.get(normalizedCall(callsign))?.query_type || 'QUERY',
        status: ui('Falha ao consultar resultado', 'Failed to check result'),
        response_text: err.message,
        sent_at: new Date().toISOString()
      });
    }
  }

  async function sendStationQuery(button) {
    const callsign = normalizedCall(button?.dataset?.callsign || '');
    const queryType = String(button?.dataset?.queryType || '').toUpperCase();
    if (!callsign || !queryType) return;
    button.disabled = true;
    setStationQueryResult(callsign, {
      query_type: queryType,
      status: ui('Enviando', 'Sending'),
      sent_at: new Date().toISOString()
    });
    try {
      const result = await api('/api/queries/send', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ to: callsign, query_type: queryType })
      });
      setStationQueryResult(callsign, {
        ...result,
        status: result.status || 'Aguardando resposta',
        sent_at: new Date().toISOString()
      });
      toast(ui('Query ' + queryType + ' enviada para ' + callsign + '.', 'Query ' + queryType + ' sent to ' + callsign + '.'), 'ok');
      void pollQueryResult(result.id, callsign);
    } catch (err) {
      setStationQueryResult(callsign, {
        query_type: queryType,
        status: ui('Falhou', 'Failed'),
        response_text: err.message,
        sent_at: new Date().toISOString()
      });
      toast(err.message, 'error');
    } finally {
      button.disabled = false;
    }
  }

  document.addEventListener('click', e => {
    const button = e.target.closest('.station-query-button');
    if (!button) return;
    e.preventDefault();
    e.stopPropagation();
    void sendStationQuery(button);
  });

  document.addEventListener('click', async e => {
    const button = e.target.closest('.station-query-history-button');
    if (!button) return;
    e.preventDefault();
    e.stopPropagation();
    const callsign = normalizedCall(button.dataset.callsign || '');
    const history = queryHistoryElement(callsign);
    if (!history) return;
    const opening = history.classList.contains('hidden');
    history.classList.toggle('hidden', !opening);
    button.textContent = opening ? ui('Ocultar histórico', 'Hide history') : ui('Ver histórico de queries', 'View query history');
    if (opening) await loadStationQueryHistory(callsign, true);
  });

  function openMessageComposer(destination = '') {
    $('.tab[data-tab="messages"]')?.click();
    selectMessageRecipient(destination);
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
    const isAnnouncement = type === 'announcement';

    $('#messageDestinationField').classList.toggle('hidden', !isMessage);
    $('#bulletinIdField').classList.toggle('hidden', isMessage || isAnnouncement);
    $('#bulletinGroupField').classList.toggle('hidden', !isGroup);

    const messageInput = $('#messageText');
    if (isMessage) messageInput.removeAttribute('maxlength');
    else messageInput.maxLength = 67;
    messageInput.placeholder = isMessage
      ? ui('Digite a mensagem APRS; textos longos serão enviados em partes', 'Type the APRS message; long texts will be sent in parts')
      : isAnnouncement
        ? ui('Digite o texto do anúncio APRS', 'Type the APRS announcement text')
        : ui('Digite o texto do boletim APRS', 'Type the APRS bulletin text');
    $('#sendMessageButton').textContent = isMessage
      ? ui('Enviar', 'Send')
      : isAnnouncement
        ? ui('Enviar anúncio', 'Send announcement')
        : ui('Enviar boletim', 'Send bulletin');
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
    const bulletinId = type === 'announcement' ? 'A' : $('#bulletinId').value;
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
        toast(
          result.type === 'announcement'
            ? ui('Anúncio enviado ao APRS-IS sem solicitação de ACK.', 'Announcement sent to APRS-IS without ACK request.')
            : ui('Boletim enviado ao APRS-IS sem solicitação de ACK.', 'Bulletin sent to APRS-IS without ACK request.'),
          'ok'
        );
      }
      void loadMessages({ scrollToNewest:true });
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
      const messagesTab = $('.tab[data-tab="messages"]');
      messagesTab?.classList.toggle('has-unread', unreadCount > 0 && state.activeTab !== 'messages');
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
    if (badge) {
      badge.textContent = unread;
      badge.classList.toggle('hidden', unread <= 0);
    }
    $('.tab[data-tab="messages"]')?.classList.toggle('has-unread', unread > 0 && state.activeTab !== 'messages');
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
    const call = normalizedCall(callsign);
    let station = state.stations.find(s => normalizedCall(s.callsign) === call);
    if (!station) {
      try {
        await loadStations();
        station = state.stations.find(s => normalizedCall(s.callsign) === call);
      } catch (_) {}
    }
    if (!station) {
      toast(ui(`${call || callsign} ainda não foi encontrada na lista local de estações.`, `${call || callsign} was not found in the local station list.`), 'error');
      return;
    }

    const lat = Number(station.latitude);
    const lon = Number(station.longitude);
    const positionRejected = station.position_valid === false || !!String(station.position_issue || '');
    if (
      positionRejected
      || !Number.isFinite(lat)
      || !Number.isFinite(lon)
      || (Math.abs(lat) < 1e-9 && Math.abs(lon) < 1e-9)
    ) {
      const reason = station.position_issue_label ? ` (${station.position_issue_label})` : '';
      toast(ui(
        `${station.callsign} não possui uma posição válida para exibir no mapa${reason}.`,
        `${station.callsign} does not have a valid position to display on the map${reason}.`
      ), 'error');
      return;
    }

    const mapTab = $('.tab[data-tab="map"]');
    if (mapTab) mapTab.click();

    await new Promise(resolve => setTimeout(resolve, 70));
    state.map?.invalidateSize();
    const zoom = Math.max(state.map?.getZoom() || 4, 13);
    state.map?.setView([lat, lon], zoom, { animate: true });

    let marker = state.markers.get(station.callsign);
    if (!marker) {
      await loadMapData();
      marker = state.markers.get(station.callsign);
    }
    marker?.openPopup();
    if (marker) pulseStation(station.callsign);
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
    const firstConfigLoad = !state.configLoaded;
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
      state.trafficAnimationEnabled = cfg.traffic_animation_enabled !== 0 && cfg.traffic_animation_enabled !== false;
      if (firstConfigLoad) {
        state.trafficMode = 'live';
        state.trafficPlaying = state.trafficAnimationEnabled;
        state.timelineReplayActive = false;
        if ($('#trafficMode')) $('#trafficMode').value = 'live';
      } else if (!state.trafficAnimationEnabled && state.trafficMode === 'live') {
        state.trafficPlaying = false;
      }
      updateTrafficAnimationUi();
      state.messagePopupSeconds = Math.min(60, Math.max(1, Number(cfg.message_popup_seconds || 5)));
      state.language = normalizeLanguage(cfg.language);
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
    data.traffic_animation_enabled = !!form.elements.traffic_animation_enabled?.checked;
    data.respond_to_queries = !!form.elements.respond_to_queries?.checked;
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
    if (topologyRfColor && topologyRfColorText) topologyRfColorText.value = topologyRfColor.value || '#ffff00';
    if (topologyIgateColor && topologyIgateColorText) topologyIgateColorText.value = topologyIgateColor.value || '#ffff00';
    if (topologyWidth && topologyWidthValue) topologyWidthValue.textContent = `${topologyWidth.value || 1} px`;
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
    state.mapConfig.topology_rf_color = form.elements.namedItem('topology_rf_color')?.value || '#ffff00';
    state.mapConfig.topology_igate_color = form.elements.namedItem('topology_igate_color')?.value || '#ffff00';
    state.mapConfig.topology_width = Number(form.elements.namedItem('topology_width')?.value || 1);
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
    form.elements.namedItem('topology_rf_color').value = '#ffff00';
    form.elements.namedItem('topology_igate_color').value = '#ffff00';
    form.elements.namedItem('topology_width').value = '1';
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
      ['statistics_font_size', '#statisticsFontSizeValue', v => `${v || 13} px`],
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
      logs_line_height: form.elements.namedItem('logs_line_height')?.value || 1.30,
      statistics_font_size: form.elements.namedItem('statistics_font_size')?.value || 13
    });
    state.language = normalizeLanguage(form.elements.namedItem('language')?.value);
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
    'logs_font_family','logs_font_size','logs_font_weight','logs_line_height',
    'statistics_font_size'
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
  $('#resetStatisticsTypography')?.addEventListener('click', () => resetTypography('statistics', {font_size:13}));

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
    'Apagar todas':'Delete all',
    'Limpar':'Clear',
    'Exportar KML':'Export KML',
    'Exportar dados em KML':'Export data to KML',
    'Estações':'Stations',
    'Posições':'Positions',
    'Tracklogs':'Tracklogs',
    'Topologia / enlaces':'Topology / links',
    'Gerar KML':'Generate KML',
    'Cancelar':'Cancel',
    'Remetente':'Sender',
    'Data':'Date',
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
    'Padrão: topologia amarela (#ffff00), 1 px.':'Default: yellow topology (#ffff00), 1 px.',
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
    'Estatísticas da topologia observada':'Observed topology statistics',
    'Ranking de estações ativas, digipeaters/IGates e enlaces que deixaram de aparecer no período.':'Active-station and digipeater/IGate rankings plus links no longer seen in the period.',
    'Atualizar estatísticas':'Refresh statistics',
    'Clique em Atualizar estatísticas.':'Click Refresh statistics.',
    'Usar período das Estatísticas':'Use Statistics period',
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
    '🇧🇷 Português - padrão':'🇧🇷 Portuguese - default',
    'Trocar idioma':'Change language',
    '🏴 English':'🏴 English',
    'Estatísticas':'Statistics',
    'Estatísticas da rede':'Network statistics',
    'Clientes / versões APRS':'APRS clients / versions',
    'Software / dispositivos APRS':'APRS software / devices',
    'Distribuição pelo identificador TOCALL do último pacote de cada estação. Quando o software/versão não puder ser determinado com segurança, ele fica como Não identificado.':'Distribution based on the TOCALL identifier in each station\'s latest packet. When software/version cannot be determined reliably, it remains Unidentified.',
    'Indicadores e estatísticas da topologia observada no APRS-IS, com comparação histórica e replay no mapa.':'Observed APRS-IS topology indicators and statistics with historical comparison and map replay.',
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
    'Atividade':'Activity',
    'Tudo':'All',
    'menos de 2 h':'under 2 h',
    '2 a 24 h':'2 to 24 h',
    'mais de 24 h':'over 24 h',
    'Filtrar estações no mapa pela última interação':'Filter map stations by last interaction',
    'Todas as estações':'All stations',
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
    'Minimizar legenda':'Minimize legend',
    'Expandir legenda':'Expand legend',
    'Tracklog':'Tracklog',
    'Enlace RF':'RF link',
    'Via IGate/APRS-IS':'Via IGate/APRS-IS',
    'Animação temporal':'Timeline replay',
    'Pacote em movimento':'Moving packet',
    'Nenhuma mensagem não lida.':'No unread messages.',
    'Caminho incompleto: há nós sem posição conhecida.':'Incomplete path: some nodes have no known position.'
  }).forEach(([key, value]) => EN_TEXT.set(key, value));

  Object.entries({
    'Sobre':'About',
    'Histórico':'History',
    'Tracklog':'Tracklog',
    'Período das estações':'Station period',
    'Período do tracklog':'Tracklog period',
    'Período da topologia':'Topology period',
    'Anúncio geral':'General announcement',
    'Enviar anúncio':'Send announcement',
    'Digite o texto do anúncio APRS':'Type the APRS announcement text',
    'Replay da Rede':'Network Replay',
    'Volte no tempo e acompanhe os pacotes pelos enlaces observados.':'Go back in time and follow packets across observed links.',
    'Parado':'Stopped',
    'Até':'To',
    'Aplicar intervalo':'Apply range',
    'Usar período das Estatísticas':'Use Statistics period',
    'Modo':'Mode',
    'Ao vivo':'Live',
    'Histórico':'History',
    'reproduzidos':'played',
    'pendentes':'pending',
    'Horário:':'Time:',
    'Velocidade:':'Speed:',
    'Selecione uma conversa para abrir o histórico.':'Select a conversation to open its history.',
    'Enter = enviar · Shift+Enter = nova linha':'Enter = send · Shift+Enter = new line',
    'Tráfego bruto TNC2 recebido e transmitido. O passcode da autenticação é mascarado.':'Raw TNC2 traffic received and transmitted. The authentication passcode is masked.',
    'Dir.':'Dir.',
    'Tráfego APRS-IS':'APRS-IS traffic',
    'Indicadores e estatísticas da topologia observada no APRS-IS, com comparação histórica e replay no mapa.':'Indicators and statistics for observed APRS-IS topology, with historical comparison and map replay.',
    'Clique em Atualizar estatísticas.':'Click Refresh statistics.',
    'Campos marcados como Obrigatório precisam ser preenchidos antes de conectar ao APRS-IS.':'Fields marked Required must be completed before connecting to APRS-IS.',
    'Obrigatório. O passcode APRS-IS será calculado automaticamente.':'Required. The APRS-IS passcode will be calculated automatically.',
    'Formato das coordenadas':'Coordinate format',
    'Informe a altitude real da estação sempre que possível.':'Enter the station’s real altitude whenever possible.',
    'Somente estações brasileiras (padrão)':'Brazilian stations only (default)',
    'Centro radial — Latitude':'Radial center — Latitude',
    'Centro radial — Longitude':'Radial center — Longitude',
    'Área geográfica opcional':'Optional geographic area',
    'Norte':'North',
    'Oeste':'West',
    'Sul':'South',
    'Leste':'East',
    'Retry de mensagem após (segundos)':'Retry message after (seconds)',
    'Máximo de retries por parte':'Maximum retries per part',
    'Tocar sinal sonoro quando uma estação transmitir':'Play a sound when a station transmits',
    'Destacar em vermelho a estação que acabou de transmitir':'Highlight the station that just transmitted in red',
    'Logs':'Logs',
    'Negrito':'Bold',
    'Espaçamento entre linhas':'Line spacing',
    'Aguardando verificação.':'Waiting for check.',
    'Baixar e instalar nova versão':'Download and install new version',
    'Restaurar configuração padrão':'Restore default configuration',
    'Salvar configuração':'Save configuration',
    'Alterações ainda não salvas serão indicadas ao sair desta aba.':'Unsaved changes will be indicated when leaving this tab.',
    'Atualização do aplicativo':'Application update',
    'Nova versão disponível':'New version available',
    'Baixar e instalar':'Download and install',
    'Ver Release':'View Release',
    'Depois':'Later',
    'Animação do tráfego APRS':'APRS traffic animation',
    'Pacote em movimento':'Moving packet',
    'Animação temporal':'Timeline replay',
    'Estações mais ativas':'Most active stations',
    'Digipeaters mais utilizados':'Most used digipeaters',
    'IGates mais ativos':'Most active IGates',
    'Enlaces que deixaram de aparecer':'Links no longer seen',
    'Atualizar estatísticas':'Refresh statistics',
    'Período':'Period',
    'Software / dispositivo':'Software / device',
    'Não identificado':'Unidentified',
    'Restaurar padrão':'Restore default',
    'Tamanho da fonte':'Font size',
    'Ver histórico de queries':'View query history',
    'Ocultar histórico':'Hide history',
    'Resultado da última query':'Latest query result',
    'Nenhuma query registrada para esta estação.':'No query is recorded for this station.',
    'Nenhuma query executada recentemente para esta estação.':'No query has been run recently for this station.'
  }).forEach(([key, value]) => EN_TEXT.set(key, value));

  const LANGUAGE_META = {
    'pt-BR': { label: 'Português', flag: '/static/img/flag_br.svg', alt: 'Brasil', htmlLang: 'pt-BR' },
    en: { label: 'English', flag: '/static/img/flag_england.svg', alt: 'England', htmlLang: 'en' },
    es: { label: 'Español', flag: '/static/img/flag_spain.svg', alt: 'España', htmlLang: 'es' },
    fr: { label: 'Français', flag: '/static/img/flag_france.svg', alt: 'France', htmlLang: 'fr' },
  };

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
    return translatedText(value, map[value] || value);
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
      const translated = state.language === 'en'
        ? EN_TEXT.get(trimmed)
        : (EXTRA_I18N[state.language]?.[trimmed] || EN_TEXT.get(trimmed));
      const chosen = state.language === 'pt-BR' ? trimmed : (translated || trimmed);
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
        const translated = state.language === 'en'
          ? EN_TEXT.get(original)
          : (EXTRA_I18N[state.language]?.[original] || EN_TEXT.get(original));
        el.setAttribute(attr, state.language === 'pt-BR' ? original : (translated || original));
      }
    }
  }

  function syncLanguageFlag() {
    const flag = $('#languageFlag');
    if (!flag) return;
    const meta = LANGUAGE_META[state.language] || LANGUAGE_META['pt-BR'];
    flag.src = meta.flag;
    flag.alt = meta.alt;
  }

  function syncQuickLanguageButtons() {
    const meta = LANGUAGE_META[state.language] || LANGUAGE_META['pt-BR'];
    const currentFlag = $('#languageQuickCurrentFlag');
    const currentLabel = $('#languageQuickCurrentLabel');
    if (currentFlag) {
      currentFlag.src = meta.flag;
      currentFlag.alt = meta.alt;
    }
    if (currentLabel) currentLabel.textContent = meta.label;
    $$('.language-quick-option').forEach(button => {
      const active = button.dataset.language === state.language;
      button.classList.toggle('active', active);
      button.setAttribute('aria-checked', active ? 'true' : 'false');
    });
    const configLanguage = $('#configForm')?.elements.namedItem('language');
    if (configLanguage && configLanguage.value !== state.language) configLanguage.value = state.language;
  }

  function setLanguageMenuOpen(open) {
    const menu = $('#languageQuickMenu');
    const current = $('#languageQuickCurrent');
    if (!menu || !current) return;
    menu.classList.toggle('hidden', !open);
    current.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function applyLanguage(language) {
    state.language = normalizeLanguage(language);
    document.documentElement.lang = (LANGUAGE_META[state.language] || LANGUAGE_META['pt-BR']).htmlLang;
    translateDom(document.body);
    syncQuickLanguageButtons();
    syncLanguageFlag();
    syncMapLegendCollapsed();
    syncMapContextBar();
    refreshStationPopupRelativeTimes();
    renderAbout();
    updateMessageComposerMode();
    updateUpdateSettingsUi();
    refreshStatus();
    if (state.messages.length) renderMessages();
    if (state.stations.length) renderStations();
    if (state.activeTab === 'analysis') void refreshTopologyAnalysis();
    if (!$('#updateModal')?.classList.contains('hidden')) showUpdateModal();
  }

  async function setQuickLanguage(language) {
    const next = normalizeLanguage(language);
    applyLanguage(next);
    setLanguageMenuOpen(false);
    try {
      const result = await api('/api/config', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ language: next })
      });
      state.currentConfig = result.config || { ...(state.currentConfig || {}), language: next };
      const input = $('#configForm')?.elements.namedItem('language');
      if (input) input.value = next;
      if (state.configLoaded) {
        state.configBaseline = configFormSnapshot();
        state.configDirty = false;
        const status = $('#configSaveStatus');
        if (status) {
          status.textContent = ui('Configuração sem alterações pendentes.', 'No pending configuration changes.');
          status.classList.remove('unsaved');
        }
      }
    } catch (err) {
      toast(err.message, 'error');
    }
  }

  $('#languageQuickCurrent')?.addEventListener('click', e => {
    e.preventDefault();
    e.stopPropagation();
    const open = $('#languageQuickCurrent')?.getAttribute('aria-expanded') === 'true';
    setLanguageMenuOpen(!open);
  });

  document.addEventListener('click', e => {
    const option = e.target.closest('.language-quick-option');
    if (option) {
      e.preventDefault();
      e.stopPropagation();
      void setQuickLanguage(option.dataset.language || 'pt-BR');
      return;
    }
    if (!e.target.closest('#languageQuickSwitch')) setLanguageMenuOpen(false);
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') setLanguageMenuOpen(false);
  });

  const languageObserver = new MutationObserver(records => {
    if (state.language === 'pt-BR') return;
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
      { key: 'callsign', label: ui('Indicativo', 'Callsign'), input: form?.elements.namedItem('callsign') },
      { key: 'latitude', label: ui('Latitude', 'Latitude'), input: form?.elements.namedItem('latitude') },
      { key: 'longitude', label: ui('Longitude', 'Longitude'), input: form?.elements.namedItem('longitude') },
      { key: 'altitude', label: ui('Altitude', 'Altitude'), input: form?.elements.namedItem('altitude') },
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
    const names = missing.map(item => item.label);
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

  function renderClientVersionStats(stats) {
    const box = $('#clientVersionStatsContent');
    if (!box) return;
    const data = stats || {};
    const items = Array.isArray(data.items) ? data.items : [];
    const identified = Number(data.identified_stations || 0);
    const unidentified = Number(data.unidentified_stations || 0);
    const total = Number(data.total_stations || 0);
    const topLimit = Math.max(1, Number(data.top_limit || 20));
    const topItems = items.slice(0, topLimit);
    const own = data.own_client || null;
    const ownInTop = !!own && topItems.some(item => item.identifier === own.identifier);
    const visibleItems = [...topItems];
    if (own && !ownInTop && Number(own.stations || 0) > 0) visibleItems.push({ ...own, force_own_row: true });

    if (!items.length) {
      box.innerHTML = '<span class="hint">' +
        escapeHtml(ui(
          total ? 'Nenhum software/dispositivo pôde ser identificado com segurança neste período.' : 'Sem estações no período selecionado.',
          total ? 'No software/device could be identified reliably in this period.' : 'No stations in the selected period.'
        )) + '</span>' +
        (unidentified ? '<div class="client-version-unidentified">' +
          escapeHtml(ui('Não identificado: ', 'Unidentified: ')) +
          unidentified.toLocaleString(currentLocale()) + '</div>' : '');
      return;
    }

    const rowHtml = item => {
      const rank = item.rank ? String(item.rank) + 'º' : '—';
      const name = item.friendly_name || item.identifier || ui('Não identificado', 'Unidentified');
      const ownClass = item.is_own_client || item.force_own_row ? ' class="client-version-own-row"' : '';
      return '<tr' + ownClass + '><td><strong>' + escapeHtml(rank) + '</strong></td><td>' +
        '<span class="client-version-name">' + escapeHtml(name) + '</span></td><td>' +
        Number(item.stations || 0).toLocaleString(currentLocale()) + '</td><td>' +
        Number(item.percent || 0).toLocaleString(currentLocale(), {maximumFractionDigits:1}) + '%</td></tr>';
    };

    box.innerHTML =
      '<table class="client-version-table"><thead><tr><th>#</th><th>' +
      escapeHtml(ui('Software / dispositivo', 'Software / device')) +
      '</th><th>' + escapeHtml(ui('Estações', 'Stations')) +
      '</th><th>%</th></tr></thead><tbody>' +
      visibleItems.map(rowHtml).join('') +
      '</tbody></table>' +
      (own && !ownInTop && Number(own.stations || 0) <= 0
        ? '<div class="client-version-unidentified">' +
          escapeHtml(ui('PT2VHF APRS Client ainda não foi observado neste período.', 'PT2VHF APRS Client has not been observed in this period yet.')) +
          '</div>' : '') +
      '<div class="client-version-unidentified">' +
      escapeHtml(ui(
        'Identificadas: ' + identified.toLocaleString(currentLocale()) +
          ' · Não identificado: ' + unidentified.toLocaleString(currentLocale()) +
          ' · Total: ' + total.toLocaleString(currentLocale()),
        'Identified: ' + identified.toLocaleString(currentLocale()) +
          ' · Unidentified: ' + unidentified.toLocaleString(currentLocale()) +
          ' · Total: ' + total.toLocaleString(currentLocale())
      )) +
      '<br><span>' + escapeHtml(ui(
        'Identificação: APRS Device Identification (aprsorg/aprs-deviceid).',
        'Identification: APRS Device Identification (aprsorg/aprs-deviceid).'
      )) + '</span></div>';
  }


  async function refreshTopologyAnalysis() {
    const box = $('#topologyStatsContent');
    if (!box) return;
    const periodSelect = $('#analysisPeriod');
    if (periodSelect) periodSelect.value = String(topologyPeriodValue(state.mapPeriodHours));
    box.textContent = ui('Carregando estatísticas…', 'Loading statistics…');
    try {
      const data = await api(`/api/topology/stats?hours=${encodeURIComponent(topologyPeriodValue(state.mapPeriodHours))}`);
      const list = (items, formatter) => items.length
        ? '<ol>' + items.map(formatter).join('') + '</ol>'
        : '<span class="hint">' + ui('Sem dados.', 'No data.') + '</span>';
      const mapCall = (callsign) => `<button type="button" class="stats-map-link" data-map-callsign="${escapeHtml(callsign)}">${escapeHtml(callsign)}</button>`;
      const evidence = value => value
        ? `<span class="stats-evidence">${escapeHtml(ui('evidência', 'evidence'))}: ${escapeHtml(value)}</span>`
        : '';

      box.innerHTML =
        '<div class="topology-stat-group"><h4>' + ui('Estações mais ativas', 'Most active stations') + '</h4>' +
        '<div class="hint">' + ui('Tráfego útil por estação; telemetria, iGates e digipeaters não entram neste ranking.', 'Useful traffic by station; telemetry, iGates and digipeaters are excluded from this ranking.') + '</div>' +
        list(data.active_stations || [], x => `<li><button type="button" class="callsign-link callsign-quick-message" data-quick-message-callsign="${escapeHtml(x.callsign)}">${escapeHtml(x.callsign)}</button> — ${Number(x.packets||0).toLocaleString(currentLocale())} · ${Number(x.percent||0).toLocaleString(currentLocale(), {maximumFractionDigits:1})}%</li>`) + '</div>' +

        '<div class="topology-stat-group"><h4>' + ui('Estações que mais interagiram', 'Most interactive stations') + '</h4>' +
        '<div class="hint">' + ui('Somente conversas APRS manuais entre estações. Beacons, telemetria, ACK/REJ, queries, respostas automáticas, boletins e retries não entram no ranking.', 'Only manual APRS conversations between stations. Beacons, telemetry, ACK/REJ, queries, automatic replies, bulletins and retries are excluded.') + '</div>' +
        list(data.manual_conversations || [], x => `<li>${mapCall(x.callsign)} — ${Number(x.interactions||0).toLocaleString(currentLocale())} ${escapeHtml(ui('interações', 'interactions'))} · ${Number(x.peers||0).toLocaleString(currentLocale())} ${escapeHtml(ui('contatos', 'peers'))} · ${Number(x.percent||0).toLocaleString(currentLocale(), {maximumFractionDigits:1})}%</li>`) + '</div>' +

        '<div class="topology-stat-group"><h4>' + ui('Digipeaters mais utilizados', 'Most used digipeaters') + '</h4>' +
        list(data.digipeaters || [], x => `<li>${mapCall(x.callsign)} — ${Number(x.packets||0).toLocaleString(currentLocale())}</li>`) + '</div>' +

        '<div class="topology-stat-group"><h4>' + ui('IGates mais ativos', 'Most active IGates') + '</h4>' +
        list(data.igates || [], x => `<li>${mapCall(x.callsign)} — ${Number(x.packets||0).toLocaleString(currentLocale())}</li>`) + '</div>' +

        '<div class="topology-stat-group"><h4>' + ui('Estações com problemas', 'Stations with problems') + '</h4>' +
        '<div class="hint">' + ui('Anomalias observadas; um evento isolado não implica necessariamente defeito da estação.', 'Observed anomalies; a single event does not necessarily mean the station is faulty.') + '</div>' +
        list(data.problem_stations || [], x => `<li>${mapCall(x.callsign)} — ${escapeHtml(x.problem || x.issue_type || '')} · ${Number(x.occurrences||0).toLocaleString(currentLocale())} · ${escapeHtml(x.recurrence || '')} <button type="button" class="callsign-link station-log-button" data-callsign="${escapeHtml(x.callsign)}">${escapeHtml(ui('Logs', 'Logs'))}</button></li>`) + '</div>' +

        '<div class="topology-stat-group"><h4>' + ui('Possíveis melhorias', 'Possible improvements') + '</h4>' +
        '<div class="hint">' + ui('Sugestões inferidas do tráfego observado; não substituem estudo de propagação RF.', 'Suggestions inferred from observed traffic; they do not replace an RF propagation study.') + '</div>' +
        list(data.improvement_suggestions || [], x => `<li>${x.callsign ? mapCall(x.callsign) + ' — ' : ''}<strong>${escapeHtml(x.title || '')}</strong>: ${escapeHtml(x.detail || '')} ${evidence(x.evidence)}</li>`) + '</div>' +

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
      renderClientVersionStats(data.client_versions);
    } catch (err) {
      box.textContent = err.message;
    }
  }

  document.addEventListener('click', event => {
    const link = event.target.closest('[data-quick-message-callsign]');
    if (!link) return;
    event.preventDefault();
    openMessageComposer(link.dataset.quickMessageCallsign || '');
  });

  document.addEventListener('click', event => {
    const link = event.target.closest('[data-map-callsign]');
    if (!link) return;
    event.preventDefault();
    event.stopPropagation();
    void focusStationOnMap(link.dataset.mapCallsign || '');
  });

  $('#refreshTopologyStatsButton')?.addEventListener('click', refreshTopologyAnalysis);
  $('#analysisPeriod')?.addEventListener('change', async event => {
    state.topologyHours = topologyPeriodValue(event.target.value);
    state.replayWindowStart = null;
    state.replayWindowEnd = null;
    localStorage.setItem('pt2vhf_topology_hours', String(state.topologyHours));
    // O período das Estatísticas é independente do período único do Mapa.
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
      toast(ui('Replay sincronizado com o período das Estatísticas.', 'Replay synced with the Statistics period.'), 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  setTrafficSpeed(state.trafficSpeed);
  if ($('#mapTypeQuick')) $('#mapTypeQuick').value = state.mapConfig.map_type;

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
    setTrafficSpeed(event.target.value, 'replay');
  });

  $('#topologySpeed')?.addEventListener('change', event => {
    setTrafficSpeed(event.target.value, 'topology');
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

    const schedulePolling = (task, intervalMs) => {
      const run = async () => {
        try {
          await task();
        } catch (err) {
          console.warn('Polling:', err);
        } finally {
          setTimeout(run, intervalMs);
        }
      };
      setTimeout(run, intervalMs);
    };

    // Cada rotina agenda a próxima execução apenas depois que a anterior termina.
    // Isso impede acúmulo de requests quando SQLite/backend ficam momentaneamente lentos.
    schedulePolling(refreshStatus, 3000);
    schedulePolling(refreshSystemMetrics, 2000);
    schedulePolling(async () => {
      if (state.activeTab === 'map') await loadMapData();
    }, 10000);
    schedulePolling(async () => {
      if (state.activeTab === 'map') await pollTrafficEvents();
    }, 3000);
    schedulePolling(async () => {
      if (state.activeTab === 'messages') await loadMessages();
    }, 5000);
    schedulePolling(checkIncomingPersonalMessages, 5000);
    schedulePolling(async () => {
      if (state.currentConfig?.check_updates_on_start) await refreshVersionStatus(false);
    }, 30 * 60 * 1000);
    schedulePolling(async () => {
      if (state.activeTab === 'stations') await loadStations();
    }, 10000);
    schedulePolling(refreshStationPopupRelativeTimes, 30000);
    schedulePolling(async () => {
      if (state.activeTab === 'log') await loadLog(false);
    }, 3000);
  }

  boot();
})();
