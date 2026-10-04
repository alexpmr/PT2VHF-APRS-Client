(() => {
  'use strict';
  const t = (pt, en, es, fr) => {
    const lang = (document.documentElement.lang || localStorage.getItem('pt2vhf_language') || 'pt-BR').toLowerCase();
    if (lang.startsWith('en')) return en;
    if (lang.startsWith('es')) return es;
    if (lang.startsWith('fr')) return fr;
    return pt;
  };
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fetchJson = async (url) => {
    const r = await fetch(url, {cache:'no-store'});
    const data = await r.json();
    if (!r.ok) throw new Error(data?.error || r.statusText);
    return data;
  };

  function createSidePanel() {
    if (document.getElementById('v1818StationPanel')) return;
    const panel = document.createElement('aside');
    panel.id = 'v1818StationPanel';
    panel.className = 'v1818-side-panel hidden';
    panel.innerHTML = '<div class="v1818-panel-head"><strong id="v1818StationTitle"></strong><button id="v1818StationClose" class="icon-button" type="button">×</button></div><div id="v1818StationBody"></div>';
    document.body.appendChild(panel);
    panel.querySelector('#v1818StationClose').addEventListener('click', () => panel.classList.add('hidden'));
  }

  async function openStation(callsign) {
    const rows = await fetchJson('/api/v1818/stations/search?q=' + encodeURIComponent(callsign) + '&limit=20');
    const row = rows.find(x => String(x.callsign).toUpperCase() === String(callsign).toUpperCase()) || rows[0];
    if (!row) return;
    createSidePanel();
    const panel = document.getElementById('v1818StationPanel');
    document.getElementById('v1818StationTitle').textContent = row.callsign || callsign;
    const fields = [
      [t('Nome','Name','Nombre','Nom'), row.name],
      [t('Última recepção','Last heard','Última recepción','Dernière réception'), row.last_heard],
      [t('Posição','Position','Posición','Position'), (row.latitude != null && row.longitude != null) ? row.latitude + ', ' + row.longitude : '—'],
      [t('Altitude','Altitude','Altitud','Altitude'), row.altitude != null ? row.altitude + ' m' : '—'],
      [t('Velocidade','Speed','Velocidad','Vitesse'), row.speed != null ? row.speed : '—'],
      [t('Curso','Course','Rumbo','Cap'), row.course != null ? row.course + '°' : '—'],
      [t('Path','Path','Path','Path'), row.path || '—'],
      [t('Informações','Information','Información','Informations'), row.info || '—'],
    ];
    document.getElementById('v1818StationBody').innerHTML =
      '<div class="v1818-kv">' + fields.map(([k,v]) => '<div><span>'+esc(k)+'</span><strong>'+esc(v)+'</strong></div>').join('') + '</div>' +
      '<div class="v1818-actions"><button type="button" id="v1818Message" class="btn primary">'+t('Enviar mensagem','Send message','Enviar mensaje','Envoyer un message')+'</button><button type="button" id="v1818Log" class="btn secondary">'+t('Mostrar log','Show log','Mostrar log','Afficher le journal')+'</button></div>';
    panel.classList.remove('hidden');
    panel.querySelector('#v1818Message')?.addEventListener('click', () => {
      document.querySelector('[data-tab="messages"]')?.click();
      const input = document.getElementById('messageTo');
      if (input) { input.value = row.callsign; input.dispatchEvent(new Event('input', {bubbles:true})); }
    });
    panel.querySelector('#v1818Log')?.addEventListener('click', () => {
      document.querySelector('[data-tab="log"]')?.click();
      const input = document.getElementById('logFilter');
      if (input) { input.value = row.callsign; input.dispatchEvent(new Event('input', {bubbles:true})); }
    });
  }

  function installQuickSearch() {
    const bar = document.querySelector('.map-context-controls');
    if (!bar || document.getElementById('v1818QuickSearch')) return;
    const wrap = document.createElement('div');
    wrap.className = 'v1818-search';
    wrap.innerHTML = '<input id="v1818QuickSearch" type="search" autocomplete="off" placeholder="'+t('Localizar indicativo…','Find callsign…','Buscar indicativo…','Rechercher indicatif…')+'"><div id="v1818SearchResults" class="v1818-search-results hidden"></div>';
    bar.prepend(wrap);
    const input = wrap.querySelector('input');
    const results = wrap.querySelector('.v1818-search-results');
    let seq = 0;
    input.addEventListener('input', async () => {
      const q = input.value.trim();
      const current = ++seq;
      if (q.length < 2) { results.classList.add('hidden'); results.innerHTML=''; return; }
      try {
        const rows = await fetchJson('/api/v1818/stations/search?q='+encodeURIComponent(q)+'&limit=12');
        if (current !== seq) return;
        results.innerHTML = rows.map(row => '<button type="button" data-call="'+esc(row.callsign)+'"><strong>'+esc(row.callsign)+'</strong><span>'+esc(row.name || row.info || '')+'</span></button>').join('');
        results.classList.toggle('hidden', !rows.length);
      } catch (_) { results.classList.add('hidden'); }
    });
    results.addEventListener('click', ev => {
      const btn = ev.target.closest('button[data-call]');
      if (!btn) return;
      input.value = btn.dataset.call;
      results.classList.add('hidden');
      openStation(btn.dataset.call);
      try {
        if (window.map && window.stationMarkers && window.stationMarkers[btn.dataset.call]) {
          const marker = window.stationMarkers[btn.dataset.call];
          window.map.setView(marker.getLatLng(), Math.max(window.map.getZoom(), 12));
        }
      } catch (_) {}
    });
  }

  function installAdvancedPanel() {
    if (document.getElementById('v1818AdvancedPanel')) return;
    const statsSection = document.querySelector('#tab-analysis');
    const host = statsSection || document.querySelector('main');
    if (!host) return;
    const panel = document.createElement('section');
    panel.id = 'v1818AdvancedPanel';
    panel.className = 'panel-card v1818-advanced-panel';
    panel.innerHTML = '<div class="v1818-advanced-head"><div><h3>'+t('Saúde e comparação da rede','Network health and comparison','Salud y comparación de red','Santé et comparaison du réseau')+'</h3><p>'+t('Indicadores consolidados do período atual e anterior.','Consolidated indicators for current and previous periods.','Indicadores consolidados del período actual y anterior.','Indicateurs consolidés des périodes actuelle et précédente.')+'</p></div><label>'+t('Período','Period','Período','Période')+' <select id="v1818Hours"><option value="1">1 h</option><option value="6">6 h</option><option value="24" selected>24 h</option><option value="168">7 d</option></select></label></div><div id="v1818Metrics" class="v1818-metrics"></div><div class="v1818-export-actions"><a id="v1818Csv" class="btn secondary" href="#">CSV</a><a id="v1818Geojson" class="btn secondary" href="#">GeoJSON</a><a class="btn secondary" href="/api/v1818/diagnostics.zip">'+t('Pacote de diagnóstico','Diagnostic package','Paquete de diagnóstico','Paquet de diagnostic')+'</a></div><details><summary>'+t('Quem fala com quem','Who talks to whom','Quién habla con quién','Qui parle à qui')+'</summary><div id="v1818Graph" class="v1818-graph"></div></details>';
    host.appendChild(panel);
    const select = panel.querySelector('#v1818Hours');
    const refresh = async () => {
      const hours = Number(select.value || 24);
      panel.querySelector('#v1818Csv').href = '/api/v1818/export.csv?hours='+hours;
      panel.querySelector('#v1818Geojson').href = '/api/v1818/export.geojson?hours='+hours;
      try {
        const [q,c,g] = await Promise.all([
          fetchJson('/api/v1818/network-quality?hours='+hours),
          fetchJson('/api/v1818/period-compare?hours='+hours),
          fetchJson('/api/v1818/topology-graph?hours='+hours),
        ]);
        const metric = (label, value, extra='') => '<div><span>'+esc(label)+'</span><strong>'+esc(value ?? '—')+'</strong><small>'+esc(extra)+'</small></div>';
        const ch = c.changes || {};
        const fmtDelta = (key) => {
          const x=ch[key]; if (!x) return '';
          if (x.new) return t('novo','new','nuevo','nouveau');
          if (x.percent == null) return String(x.delta ?? '');
          return (x.percent>0?'+':'')+x.percent+'%';
        };
        panel.querySelector('#v1818Metrics').innerHTML =
          metric(t('Pacotes','Packets','Paquetes','Paquets'), q.packets, fmtDelta('packets')) +
          metric(t('Estações','Stations','Estaciones','Stations'), q.stations, fmtDelta('stations')) +
          metric('RF', q.rf_packets, fmtDelta('rf_packets')) +
          metric('APRS-IS', q.aprsis_packets, fmtDelta('aprsis_packets')) +
          metric(t('Duplicados','Duplicates','Duplicados','Doublons'), q.duplicates, q.duplicate_rate+'%') +
          metric(t('Mensagens com ACK','Messages with ACK','Mensajes con ACK','Messages avec ACK'), q.acked_messages, q.ack_rate+'%') +
          metric(t('RTT mediano','Median RTT','RTT mediano','RTT médian'), q.query_rtt_median_ms == null ? '—' : q.query_rtt_median_ms+' ms') +
          metric(t('Novas estações','New stations','Nuevas estaciones','Nouvelles stations'), q.new_stations, fmtDelta('new_stations'));
        const top = (g.edges || []).slice(0, 80);
        const graphHost = panel.querySelector('#v1818Graph');
        if (!top.length) {
          graphHost.innerHTML = '<p>—</p>';
        } else {
          const nodeIds = Array.from(new Set(top.flatMap(e => [e.source,e.target]))).slice(0, 50);
          const size = 760, cx = size/2, cy = size/2, radius = 285;
          const pos = new Map(nodeIds.map((id,i) => [id, {
            x: cx + Math.cos((Math.PI*2*i/nodeIds.length)-Math.PI/2)*radius,
            y: cy + Math.sin((Math.PI*2*i/nodeIds.length)-Math.PI/2)*radius
          }]));
          const maxInteractions = Math.max(...top.map(e => Number(e.interactions || 1)), 1);
          const lines = top.filter(e => pos.has(e.source) && pos.has(e.target)).map(e => {
            const a=pos.get(e.source), b=pos.get(e.target);
            const width = 0.8 + 4.2*(Number(e.interactions||1)/maxInteractions);
            const dash = String(e.kind||'').toLowerCase().includes('igate') ? '6 4' : '';
            return '<line x1="'+a.x+'" y1="'+a.y+'" x2="'+b.x+'" y2="'+b.y+'" stroke="currentColor" stroke-opacity=".34" stroke-width="'+width.toFixed(2)+'" stroke-dasharray="'+dash+'"><title>'+esc(e.source+' → '+e.target+' · '+e.kind+' · '+e.interactions)+'</title></line>';
          }).join('');
          const nodes = nodeIds.map(id => {
            const p=pos.get(id);
            const degree=(g.nodes||[]).find(n=>n.id===id)?.degree || 1;
            const r=Math.max(5,Math.min(13,5+Math.log10(1+degree)*3));
            return '<g class="v1818-node" data-call="'+esc(id)+'" tabindex="0"><circle cx="'+p.x+'" cy="'+p.y+'" r="'+r+'"></circle><text x="'+(p.x+10)+'" y="'+(p.y+4)+'">'+esc(id)+'</text><title>'+esc(id+' · '+degree+' '+t('interações','interactions','interacciones','interactions'))+'</title></g>';
          }).join('');
          graphHost.innerHTML = '<svg class="v1818-network-svg" viewBox="0 0 '+size+' '+size+'" role="img" aria-label="'+esc(t('Grafo de comunicação APRS','APRS communication graph','Grafo de comunicación APRS','Graphe de communication APRS'))+'">'+lines+nodes+'</svg>';
        }
      } catch (err) {
        panel.querySelector('#v1818Metrics').textContent = String(err.message || err);
      }
    };
    select.addEventListener('change', refresh);
    panel.querySelector('#v1818Graph').addEventListener('click', ev => {
      const btn = ev.target.closest('[data-call]');
      if (btn) openStation(btn.dataset.call);
    });
    refresh();
  }

  function installDelegatedStationPanel() {
    document.addEventListener('dblclick', ev => {
      const row = ev.target.closest('#stationsTable tbody tr');
      if (!row) return;
      const text = row.querySelector('td')?.textContent?.trim();
      if (text) openStation(text);
    });
  }

  function boot() {
    createSidePanel();
    installQuickSearch();
    installAdvancedPanel();
    installDelegatedStationPanel();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();