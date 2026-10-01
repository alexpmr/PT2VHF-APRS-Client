(() => {
  'use strict';

  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  let lastConfig = null;
  let initialized = false;
  let pollTimer = null;

  async function requestJson(url, options = {}) {
    const response = await fetch(url, {
      cache: 'no-store',
      headers: {'Content-Type':'application/json', ...(options.headers || {})},
      ...options,
    });
    let payload = {};
    try { payload = await response.json(); } catch (_) {}
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    return payload;
  }

  function showError(error = '') {
    const box = $('#tncError');
    if (!box) return;
    box.textContent = String(error || '');
    box.classList.toggle('hidden', !error);
  }

  function statusClass(connected, paused) {
    if (paused) return 'status disconnected';
    return connected ? 'status connected' : 'status disconnected';
  }

  function humanTime(value) {
    if (!value) return '—';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return d.toLocaleString();
  }

  function roleLabel(role) {
    return ({
      monitor:'Monitor', station:'Estação local', digi:'Digipeater',
      igate_rx:'iGate RX-only', igate_bidir:'iGate bidirecional', digi_igate:'Digi + iGate'
    })[role] || role || '—';
  }

  function optimizerLabel(mode) {
    return ({off:'Desligado', observe:'Observação', automatic:'Automático'})[mode] || mode || '—';
  }

  function setStatus(payload = {}) {
    const status = payload.status || payload;
    const header = $('#tncHeaderStatus');
    if (header) {
      header.className = `${statusClass(!!status.connected, !!status.tx_paused)} tnc-header-status`;
      const text = header.querySelector('span:last-child');
      if (text) text.textContent = status.connected ? (status.tx_paused ? 'TNC · TX parado' : 'TNC conectado') : 'TNC offline';
      header.title = [status.state, status.endpoint, status.last_error].filter(Boolean).join(' · ');
    }
    const pairs = [
      ['#tncMetricState', status.state || 'Desconectado'],
      ['#tncMetricEndpoint', status.endpoint || '—'],
      ['#tncMetricRx', Number(status.frames_rx || 0).toLocaleString()],
      ['#tncMetricTx', Number(status.frames_tx || 0).toLocaleString()],
      ['#tncMetricDuplicates', Number(status.duplicates_suppressed || 0).toLocaleString()],
      ['#tncMetricQueue', Number(status.tx_queue || 0).toLocaleString()],
      ['#tncMetricLastRx', status.last_rx_at ? `Último: ${humanTime(status.last_rx_at)}` : '—'],
      ['#tncMetricLastTx', status.last_tx_at ? `Último: ${humanTime(status.last_tx_at)}` : '—'],
      ['#tncMetricTxState', status.tx_paused ? 'TX PARADO' : (lastConfig?.auto_tx_enabled ? 'TX automático habilitado' : 'TX automático desligado')],
      ['#tncMetricOptimizer', optimizerLabel(status.optimizer_mode || lastConfig?.optimizer_mode)],
      ['#tncMetricRole', roleLabel(status.role || lastConfig?.role)],
    ];
    for (const [selector, value] of pairs) {
      const el = $(selector);
      if (el) el.textContent = value;
    }
    $('#tncConnect')?.toggleAttribute('disabled', !!status.connected);
    $('#tncDisconnect')?.toggleAttribute('disabled', !status.connected);
    $('#tncEmergencyStop')?.toggleAttribute('disabled', !!status.tx_paused);
    $('#tncResumeTx')?.toggleAttribute('disabled', !status.tx_paused);
  }

  function field(id) { return document.getElementById(id); }
  function checked(id) { return !!field(id)?.checked; }
  function val(id, fallback = '') { return field(id)?.value ?? fallback; }

  function collectConfig() {
    return {
      transport: val('tncTransport', 'tcp'),
      serial_port: val('tncSerialPort'),
      serial_baud: Number(val('tncSerialBaud', 9600)),
      tcp_host: String(val('tncTcpHost', '127.0.0.1')).trim(),
      tcp_port: Number(val('tncTcpPort', 8001)),
      auto_connect: checked('tncAutoConnect'),
      role: val('tncRole', 'monitor'),
      auto_tx_enabled: checked('tncAutoTxEnabled'),
      tx_confirmed: checked('tncTxConfirmed'),
      digi_enabled: checked('tncDigiEnabled'),
      digi_profile: val('tncDigiProfile', 'fill'),
      digi_aliases: String(val('tncDigiAliases')).trim(),
      digi_max_hops: Number(val('tncDigiMaxHops', 3)),
      duplicate_window_seconds: Number(val('tncDuplicateWindow', 30)),
      source_rate_limit_per_minute: Number(val('tncSourceRate', 30)),
      igate_rx_enabled: checked('tncIgateRx'),
      igate_tx_enabled: checked('tncIgateTx'),
      igate_heard_window_minutes: Number(val('tncIgateHeardWindow', 30)),
      igate_rf_path: String(val('tncIgateRfPath')).trim(),
      optimizer_mode: val('tncOptimizerMode', 'observe'),
      retention_days: Number(val('tncRetentionDays', 14)),
    };
  }

  function applyConfig(cfg = {}) {
    lastConfig = cfg;
    const values = {
      tncTransport: cfg.transport || 'tcp',
      tncSerialBaud: cfg.serial_baud ?? 9600,
      tncTcpHost: cfg.tcp_host || '127.0.0.1',
      tncTcpPort: cfg.tcp_port ?? 8001,
      tncRole: cfg.role || 'monitor',
      tncDigiProfile: cfg.digi_profile || 'fill',
      tncDigiAliases: cfg.digi_aliases || '',
      tncDigiMaxHops: cfg.digi_max_hops ?? 3,
      tncDuplicateWindow: cfg.duplicate_window_seconds ?? 30,
      tncSourceRate: cfg.source_rate_limit_per_minute ?? 30,
      tncIgateHeardWindow: cfg.igate_heard_window_minutes ?? 30,
      tncIgateRfPath: cfg.igate_rf_path || '',
      tncOptimizerMode: cfg.optimizer_mode || 'observe',
      tncRetentionDays: cfg.retention_days ?? 14,
    };
    for (const [id, value] of Object.entries(values)) if (field(id)) field(id).value = String(value);
    const booleans = {
      tncAutoConnect: cfg.auto_connect,
      tncAutoTxEnabled: cfg.auto_tx_enabled,
      tncTxConfirmed: cfg.tx_confirmed,
      tncDigiEnabled: cfg.digi_enabled,
      tncIgateRx: cfg.igate_rx_enabled,
      tncIgateTx: cfg.igate_tx_enabled,
    };
    for (const [id, value] of Object.entries(booleans)) if (field(id)) field(id).checked = !!value;
    if (field('tncSerialPort') && cfg.serial_port) field('tncSerialPort').dataset.selected = cfg.serial_port;
    syncTransportFields();
  }

  function syncTransportFields() {
    const serialMode = val('tncTransport', 'tcp') === 'serial';
    $$('.tnc-serial-field').forEach(el => el.classList.toggle('hidden', !serialMode));
    $$('.tnc-tcp-field').forEach(el => el.classList.toggle('hidden', serialMode));
  }

  function applyRolePreset() {
    const role = val('tncRole', 'monitor');
    if (role === 'monitor' || role === 'station') {
      field('tncDigiEnabled').checked = false;
      field('tncIgateRx').checked = false;
      field('tncIgateTx').checked = false;
    } else if (role === 'digi') {
      field('tncDigiEnabled').checked = true;
      field('tncIgateRx').checked = false;
      field('tncIgateTx').checked = false;
    } else if (role === 'igate_rx') {
      field('tncDigiEnabled').checked = false;
      field('tncIgateRx').checked = true;
      field('tncIgateTx').checked = false;
    } else if (role === 'igate_bidir') {
      field('tncDigiEnabled').checked = false;
      field('tncIgateRx').checked = true;
      field('tncIgateTx').checked = true;
    } else if (role === 'digi_igate') {
      field('tncDigiEnabled').checked = true;
      field('tncIgateRx').checked = true;
      field('tncIgateTx').checked = true;
    }
  }

  async function loadPorts() {
    const select = field('tncSerialPort');
    if (!select) return;
    const wanted = select.value || select.dataset.selected || lastConfig?.serial_port || '';
    try {
      const data = await requestJson('/api/tnc/ports');
      select.innerHTML = '<option value="">Selecione…</option>';
      for (const port of data.ports || []) {
        const opt = document.createElement('option');
        opt.value = port.device;
        opt.textContent = port.description && port.description !== port.device
          ? `${port.device} — ${port.description}` : port.device;
        select.appendChild(opt);
      }
      if (wanted && !Array.from(select.options).some(o => o.value === wanted)) {
        const opt = document.createElement('option');
        opt.value = wanted; opt.textContent = wanted + ' — não detectada agora';
        select.appendChild(opt);
      }
      select.value = wanted;
    } catch (error) {
      showError('Não foi possível listar as portas seriais: ' + error.message);
    }
  }

  async function saveConfig({quiet = false} = {}) {
    const payload = collectConfig();
    const data = await requestJson('/api/tnc/config', {method:'POST', body:JSON.stringify(payload)});
    applyConfig(data.config || payload);
    setStatus(data.status || {});
    if (!quiet) {
      const out = $('#tncSaveStatus');
      if (out) {
        out.textContent = 'Configuração TNC / RF salva.';
        setTimeout(() => { if (out.textContent.includes('salva')) out.textContent = ''; }, 3500);
      }
    }
    showError('');
    return data;
  }

  function renderFrames(rows = []) {
    const body = $('#tncFramesBody'); if (!body) return;
    if (!rows.length) { body.innerHTML = '<tr><td colspan="7">Sem frames.</td></tr>'; return; }
    body.innerHTML = rows.map(row => `<tr>
      <td>${esc(humanTime(row.timestamp))}</td><td><span class="tnc-badge ${row.direction==='TX'?'warn':'good'}">${esc(row.direction)}</span></td>
      <td>${esc(row.source)}</td><td>${esc(row.destination)}</td><td>${esc(row.packet_type)}</td>
      <td>${esc((row.path || []).join(', '))}</td><td title="${esc(row.reason)}"><code>${esc(row.raw_tnc2)}</code></td>
    </tr>`).join('');
  }

  function renderDecisions(rows = []) {
    const body = $('#tncDecisionsBody'); if (!body) return;
    if (!rows.length) { body.innerHTML = '<tr><td colspan="6">Sem decisões.</td></tr>'; return; }
    body.innerHTML = rows.map(row => {
      const cls = row.decision === 'sent' || row.decision === 'queued' ? 'good' : (row.decision === 'blocked' || row.decision === 'error' ? 'bad' : 'warn');
      return `<tr><td>${esc(humanTime(row.timestamp))}</td><td>${esc(row.action)}</td><td><span class="tnc-badge ${cls}">${esc(row.decision)}</span></td>
      <td>${esc(row.source)}</td><td>${esc(row.destination)}</td><td>${esc(row.reason)}</td></tr>`;
    }).join('');
  }

  function renderHeard(rows = []) {
    const body = $('#tncHeardBody'); if (!body) return;
    if (!rows.length) { body.innerHTML = '<tr><td colspan="6">Nenhuma estação ouvida pelo TNC.</td></tr>'; return; }
    body.innerHTML = rows.map(row => `<tr><td><strong>${esc(row.callsign)}</strong></td><td>${esc(humanTime(row.last_heard))}</td>
      <td><span class="tnc-badge ${row.direct?'good':'warn'}">${row.direct?'Sim':'Via digi'}</span></td><td>${Number(row.heard_count||0).toLocaleString()}</td>
      <td>${esc(row.last_packet_type)}</td><td>${esc((row.path || []).map(p => typeof p === 'string' ? p : (p.value || '') + (p.repeated ? '*' : '')).join(', '))}</td></tr>`).join('');
  }

  function renderOptimizer(report = {}) {
    const stats = report.statistics || {};
    const body = $('#tncEdgesBody');
    if (body) {
      const edges = stats.top_edges || [];
      body.innerHTML = edges.length ? edges.map(row => `<tr><td>${esc(row.source)}</td><td>${esc(row.destination)}</td>
        <td><span class="tnc-badge ${row.medium==='RF'?'good':'warn'}">${esc(row.medium)}</span></td>
        <td>${Number(row.interactions||0).toLocaleString()}</td><td>${Number(row.ack_count||0).toLocaleString()}</td><td>${esc(humanTime(row.last_seen))}</td></tr>`).join('')
        : '<tr><td colspan="6">Aguardando interações.</td></tr>';
    }
    const rec = $('#tncRecommendations');
    if (rec) {
      const rows = report.recommendations || [];
      rec.innerHTML = rows.map(item => `<div class="tnc-recommendation"><strong>${esc(item.title)}</strong><span>${esc(item.detail)}</span></div>`).join('') || '<span class="hint">Aguardando dados.</span>';
    }
    const opt = $('#tncMetricOptimizer'); if (opt) opt.textContent = optimizerLabel(report.mode);
  }

  async function refreshStatus() {
    try {
      const data = await requestJson('/api/tnc/status');
      if (!lastConfig) applyConfig(data.config || {});
      setStatus(data.status || {});
    } catch (error) {
      const header = $('#tncHeaderStatus');
      if (header) {
        header.className = 'status disconnected tnc-header-status';
        const text = header.querySelector('span:last-child');
        if (text) text.textContent = 'TNC erro';
        header.title = error.message;
      }
    }
  }

  async function refreshData() {
    try {
      const [frames, decisions, heard, optimizer] = await Promise.all([
        requestJson('/api/tnc/frames?limit=200'),
        requestJson('/api/tnc/decisions?limit=200'),
        requestJson('/api/tnc/heard?limit=150'),
        requestJson('/api/tnc/optimizer'),
      ]);
      renderFrames(frames);
      renderDecisions(decisions);
      renderHeard(heard);
      renderOptimizer(optimizer);
      showError('');
    } catch (error) {
      showError(error.message);
    }
  }

  async function initialLoad() {
    try {
      const data = await requestJson('/api/tnc/status');
      applyConfig(data.config || {});
      setStatus(data.status || {});
      await loadPorts();
      await refreshData();
    } catch (error) { showError(error.message); }
  }

  function bind() {
    if (initialized) return;
    initialized = true;
    field('tncTransport')?.addEventListener('change', syncTransportFields);
    field('tncRole')?.addEventListener('change', applyRolePreset);
    $('#tncRefreshPorts')?.addEventListener('click', loadPorts);
    $('#tncRefreshData')?.addEventListener('click', refreshData);
    $('#tncSave')?.addEventListener('click', async () => {
      try { await saveConfig(); await refreshData(); } catch (error) { showError(error.message); }
    });
    $('#tncConnect')?.addEventListener('click', async () => {
      try {
        await saveConfig({quiet:true});
        const data = await requestJson('/api/tnc/connect', {method:'POST', body:'{}'});
        setStatus(data.status || {});
        setTimeout(refreshStatus, 500);
      } catch (error) { showError(error.message); }
    });
    $('#tncDisconnect')?.addEventListener('click', async () => {
      try { const data = await requestJson('/api/tnc/disconnect', {method:'POST', body:'{}'}); setStatus(data.status || {}); }
      catch (error) { showError(error.message); }
    });
    $('#tncEmergencyStop')?.addEventListener('click', async () => {
      try {
        const data = await requestJson('/api/tnc/tx/stop', {method:'POST', body:'{}'});
        setStatus(data.status || {}); await refreshData();
      } catch (error) { showError(error.message); }
    });
    $('#tncResumeTx')?.addEventListener('click', async () => {
      if (!confirm('Liberar novamente a transmissão automática em RF com a configuração atual?')) return;
      try {
        const data = await requestJson('/api/tnc/tx/resume', {method:'POST', body:'{}'});
        setStatus(data.status || {}); await refreshData();
      } catch (error) { showError(error.message); }
    });
    document.addEventListener('click', event => {
      const tab = event.target.closest?.('.tab[data-tab="tnc"]');
      if (tab) setTimeout(refreshData, 80);
    });
  }

  bind();
  initialLoad();
  pollTimer = setInterval(() => {
    refreshStatus();
    if ($('.tab.active[data-tab="tnc"]')) refreshData();
  }, 3000);
  window.addEventListener('beforeunload', () => { if (pollTimer) clearInterval(pollTimer); });
})();
