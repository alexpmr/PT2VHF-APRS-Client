(() => {
  'use strict';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const lang=()=>String(document.documentElement.lang||localStorage.getItem('pt2vhf_language')||'pt-BR').toLowerCase();
  const tr=(pt,en,es,fr)=>lang().startsWith('en')?en:lang().startsWith('es')?es:lang().startsWith('fr')?fr:pt;
  const req=async(url,opts={})=>{
    const r=await fetch(url,{cache:'no-store',headers:{'Content-Type':'application/json',...(opts.headers||{})},...opts});
    const d=await r.json(); if(!r.ok) throw new Error(d?.error||r.statusText); return d;
  };
  const toast=msg=>{const t=$('#toast');if(t){t.textContent=msg;t.classList.remove('hidden');setTimeout(()=>t.classList.add('hidden'),4500);}};

  async function centerNotification(category,title,detail='',severity='info',entity=''){
    try{await req('/api/v111/notifications',{method:'POST',body:JSON.stringify({category,title,detail,severity,entity})});updateBell();}catch(_){}
  }
  window.pt2vhfNotificationCenterPush=centerNotification;

  function installNotificationCenter(){
    if($('#v111Bell'))return;
    const header=document.querySelector('header .header-actions')||document.querySelector('header');
    if(!header)return;
    const wrap=document.createElement('div');wrap.className='v111-notify-wrap';
    wrap.innerHTML='<button id="v111Bell" class="btn secondary" type="button" title="'+tr('Notificações','Notifications','Notificaciones','Notifications')+'">🔔 <span id="v111BellCount"></span></button><div id="v111NotifyPanel" class="v111-notify-panel hidden"><div class="v111-notify-head"><strong>'+tr('Notificações','Notifications','Notificaciones','Notifications')+'</strong><button id="v111MarkRead" class="btn secondary">'+tr('Marcar todas como lidas','Mark all read','Marcar todas leídas','Tout marquer lu')+'</button></div><div id="v111NotifyList"></div></div>';
    header.appendChild(wrap);
    $('#v111Bell').onclick=async()=>{$('#v111NotifyPanel').classList.toggle('hidden');await renderNotifications();};
    $('#v111MarkRead').onclick=async()=>{await req('/api/v111/notifications/read',{method:'POST',body:'{}'});await renderNotifications();updateBell();};
    document.addEventListener('click',e=>{if(!wrap.contains(e.target))$('#v111NotifyPanel').classList.add('hidden');});
    updateBell();setInterval(updateBell,15000);
  }
  async function updateBell(){try{const rows=await req('/api/v111/notifications?unread=1&limit=200');const n=rows.length;const el=$('#v111BellCount');if(el)el.textContent=n?String(n):'';}catch(_){}}
  async function renderNotifications(){const host=$('#v111NotifyList');if(!host)return;try{const rows=await req('/api/v111/notifications?limit=100');host.innerHTML=rows.length?rows.map(n=>'<article class="v111-note '+esc(n.severity)+(n.read_at?' read':'')+'"><time>'+esc(n.timestamp)+'</time><strong>'+esc(n.title)+'</strong><p>'+esc(n.detail||'')+'</p></article>').join(''):'<p>—</p>';}catch(e){host.textContent=e.message;}}

  function healthLabel(state){
    return {
      disconnected:tr('Desconectado','Disconnected','Desconectado','Déconnecté'),
      transport_open_waiting:tr('Porta aberta, sem dados','Transport open, no data','Puerto abierto, sin datos','Transport ouvert, sans données'),
      bytes_without_kiss:tr('Bytes chegando, sem KISS','Bytes arriving, no KISS','Bytes llegando, sin KISS','Octets reçus, sans KISS'),
      kiss_invalid_ax25:tr('KISS ativo, AX.25 inválido','KISS active, invalid AX.25','KISS activo, AX.25 inválido','KISS actif, AX.25 invalide'),
      kiss_active:tr('KISS detectado','KISS detected','KISS detectado','KISS détecté'),
      rx_active:tr('RX AX.25 operacional','AX.25 RX operational','RX AX.25 operativo','RX AX.25 opérationnel'),
      rx_tx_active:tr('RX/TX operacional','RX/TX operational','RX/TX operativo','RX/TX opérationnel')
    }[state]||state;
  }

  function installTncOperations(){
    const tab=$('#tab-tnc'); if(!tab||$('#v111TncOps'))return;
    const host=document.createElement('section');host.id='v111TncOps';host.className='tnc-card v111-tnc-ops';
    host.innerHTML='<div class="v111-section-head"><div><h3>'+tr('Saúde operacional do TNC','TNC operational health','Salud operativa del TNC','Santé opérationnelle du TNC')+'</h3><p id="v111TncHealthSummary">—</p></div><div><button id="v111TncCopy" class="btn secondary">'+tr('Copiar diagnóstico','Copy diagnostic','Copiar diagnóstico','Copier diagnostic')+'</button> <button id="v111TncSelfTest" class="btn primary">'+tr('Executar teste completo','Run full test','Ejecutar prueba completa','Exécuter test complet')+'</button></div></div><div id="v111TncCounters" class="v111-counter-grid"></div><details><summary>'+tr('Timeline de saúde','Health timeline','Timeline de salud','Chronologie de santé')+'</summary><div id="v111TncTimeline" class="v111-timeline"></div></details><pre id="v111TncSelfTestResult" class="hidden"></pre>';
    const first=tab.querySelector('.tnc-status-grid')?.parentElement||tab.firstElementChild;
    (first?.parentNode||tab).insertBefore(host,first?.nextSibling||null);
    let lastHealth=null;
    const refresh=async()=>{
      try{
        const h=await req('/api/v111/tnc/health');lastHealth=h;
        $('#v111TncHealthSummary').innerHTML='<strong>'+esc(healthLabel(h.health_state))+'</strong> — '+esc(h.health_summary||'');
        const rows=[
          ['Bytes RX',h.transport_bytes_rx],['KISS RX',h.kiss_frames_rx],['AX.25 RX',h.frames_rx],
          [tr('AX.25 inválidos','Invalid AX.25','AX.25 inválidos','AX.25 invalides'),h.invalid_frames_rx],
          ['Frames TX',h.frames_tx],['Bytes TX',h.transport_bytes_tx],
          [tr('Último RX','Last RX','Último RX','Dernier RX'),h.last_frame_rx||'—'],
          [tr('Último TX','Last TX','Último TX','Dernier TX'),h.last_frame_tx||'—']
        ];
        $('#v111TncCounters').innerHTML=rows.map(([k,v])=>'<div><span>'+esc(k)+'</span><strong>'+esc(v??0)+'</strong></div>').join('');
        const timeline=await req('/api/v111/tnc/timeline?limit=50');
        $('#v111TncTimeline').innerHTML=timeline.map(e=>'<div><time>'+esc(e.timestamp)+'</time><strong>'+esc(healthLabel(e.health_state))+'</strong><span>'+esc(e.detail||'')+'</span></div>').join('');
      }catch(e){$('#v111TncHealthSummary').textContent=e.message;}
    };
    $('#v111TncCopy').onclick=async()=>{if(!lastHealth)await refresh();const text=JSON.stringify(lastHealth,null,2);try{await navigator.clipboard.writeText(text);toast(tr('Diagnóstico copiado.','Diagnostic copied.','Diagnóstico copiado.','Diagnostic copié.'));}catch(_){prompt('TNC',text);}};
    $('#v111TncSelfTest').onclick=async()=>{const pre=$('#v111TncSelfTestResult');pre.classList.remove('hidden');pre.textContent=tr('Executando…','Running…','Ejecutando…','Exécution…');try{const r=await req('/api/v111/tnc/self-test',{method:'POST',body:'{}'});pre.textContent=JSON.stringify(r,null,2);await centerNotification('tnc',r.ok?tr('Autoteste TNC concluído','TNC self-test completed','Autoprueba TNC concluida','Autotest TNC terminé'):tr('Autoteste TNC com falha','TNC self-test failed','Autoprueba TNC falló','Échec autotest TNC'),JSON.stringify(r.checks),r.ok?'info':'warning');}catch(e){pre.textContent=e.message;}};
    refresh();setInterval(refresh,5000);
  }

  function installDatabaseHealth(){
    const config=$('#tab-config');if(!config||$('#v111DbHealth'))return;
    const card=document.createElement('div');card.id='v111DbHealth';card.className='config-card full-card config-section';
    card.innerHTML='<h3>'+tr('Saúde e retenção do banco','Database health and retention','Salud y retención de la base','Santé et rétention de la base')+'</h3><div id="v111DbMetrics" class="v111-counter-grid"></div><div class="v111-retention-grid"></div><div class="v111-actions"><button id="v111RetentionSave" class="btn secondary">'+tr('Salvar política','Save policy','Guardar política','Enregistrer politique')+'</button><button id="v111RetentionApply" class="btn secondary">'+tr('Aplicar limpeza agora','Apply cleanup now','Aplicar limpieza ahora','Appliquer nettoyage')+'</button><button id="v111DbOptimize" class="btn secondary">'+tr('Otimizar banco','Optimize database','Optimizar base','Optimiser base')+'</button></div>';
    config.appendChild(card);
    const defs=[
      ['packets_days',tr('Pacotes brutos','Raw packets','Paquetes brutos','Paquets bruts')],
      ['tracks_days','Tracklogs'],['aprs_log_days','APRS log'],['topology_events_days',tr('Topologia','Topology','Topología','Topologie')],
      ['tnc_frames_days','TNC frames'],['tnc_decisions_days','TNC decisions'],['notifications_days',tr('Notificações','Notifications','Notificaciones','Notifications')],['messages_days',tr('Mensagens','Messages','Mensajes','Messages')]
    ];
    const load=async()=>{
      const [h,s]=await Promise.all([req('/api/v111/db/health'),req('/api/v111/db/retention')]);
      $('#v111DbMetrics').innerHTML=[
        [tr('Tamanho','Size','Tamaño','Taille'),Math.round(h.size_bytes/1024/1024*10)/10+' MB'],
        ['SQLite',h.integrity],[tr('Fragmentação','Fragmentation','Fragmentación','Fragmentation'),h.fragmentation_percent+'%'],
        ['WAL',Math.round(h.wal_bytes/1024/1024*10)/10+' MB']
      ].map(([k,v])=>'<div><span>'+esc(k)+'</span><strong>'+esc(v)+'</strong></div>').join('');
      $('.v111-retention-grid',card).innerHTML=defs.map(([k,l])=>'<label class="field"><span>'+esc(l)+' — '+tr('dias (0 = manter)','days (0 = keep)','días (0 = mantener)','jours (0 = garder)')+'</span><input type="number" min="0" max="3650" data-ret="'+k+'" value="'+esc(s[k]??0)+'"></label>').join('');
    };
    const payload=()=>{const p={};$$('[data-ret]',card).forEach(i=>p[i.dataset.ret]=Number(i.value||0));return p;};
    $('#v111RetentionSave').onclick=async()=>{await req('/api/v111/db/retention',{method:'POST',body:JSON.stringify(payload())});toast(tr('Política salva.','Policy saved.','Política guardada.','Politique enregistrée.'));};
    $('#v111RetentionApply').onclick=async()=>{if(!confirm(tr('Aplicar agora a política de retenção?','Apply retention policy now?','¿Aplicar política ahora?','Appliquer la politique maintenant ?')))return;await req('/api/v111/db/retention',{method:'POST',body:JSON.stringify(payload())});const r=await req('/api/v111/db/retention/apply',{method:'POST',body:'{}'});toast(tr('Limpeza concluída.','Cleanup completed.','Limpieza concluida.','Nettoyage terminé.'));load();};
    $('#v111DbOptimize').onclick=async()=>{if(!confirm(tr('Otimizar o SQLite agora?','Optimize SQLite now?','¿Optimizar SQLite ahora?','Optimiser SQLite maintenant ?')))return;await req('/api/v111/db/optimize',{method:'POST',body:'{}'});toast(tr('Banco otimizado.','Database optimized.','Base optimizada.','Base optimisée.'));load();};
    load();
  }

  async function enrichStationOperational(){
    const panel=$('#v1818StationPanel');if(!panel||panel.classList.contains('hidden'))return;
    const call=String($('#v1818StationTitle',panel)?.textContent||'').trim().toUpperCase();if(!call)return;
    let host=$('#v111StationOps',panel);if(!host){host=document.createElement('section');host.id='v111StationOps';$('#v1818StationBody',panel)?.appendChild(host);}
    if(host.dataset.call===call)return;host.dataset.call=call;
    try{
      const p=await req('/api/v111/station/'+encodeURIComponent(call)+'/profile?hours=24');
      const s=p.summary||{};
      const heard=(p.heard_by||[]).map(x=>'<li><strong>'+esc(x.observer||'—')+'</strong> · '+esc(x.medium||'')+' · '+esc(x.observations||0)+' · '+esc(x.last_seen||'')+'</li>').join('');
      const paths=(p.paths||[]).map(x=>'<li><code>'+esc(x.path||'')+'</code> · '+esc(x.medium||'')+' · '+esc(x.packets||0)+'</li>').join('');
      host.innerHTML='<div class="v111-station-summary"><h4>'+tr('Perfil operacional','Operational profile','Perfil operativo','Profil opérationnel')+'</h4><div class="v111-counter-grid">'+
        [['Pacotes',s.packets||0],['RF',s.rf_packets||0],['APRS-IS',s.aprsis_packets||0],[tr('Mensagens','Messages','Mensajes','Messages'),p.messages||0]].map(([k,v])=>'<div><span>'+esc(k)+'</span><strong>'+esc(v)+'</strong></div>').join('')+
        '</div><h5>'+tr('Ouvido por','Heard by','Escuchado por','Entendu par')+'</h5><ul>'+(heard||'<li>—</li>')+'</ul><h5>'+tr('Caminhos observados','Observed paths','Rutas observadas','Chemins observés')+'</h5><ul>'+(paths||'<li>—</li>')+'</ul></div>';
    }catch(e){host.textContent=e.message;}
  }
  function watchStation(){const o=new MutationObserver(()=>enrichStationOperational());o.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});}

  function boot(){installNotificationCenter();installTncOperations();installDatabaseHealth();watchStation();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();