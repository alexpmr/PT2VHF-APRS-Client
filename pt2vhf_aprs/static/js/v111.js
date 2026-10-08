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
    if($('#v111NotifyOpen'))return;
    const config=$('#tab-config');
    if(!config)return;
    const wrap=document.createElement('div');wrap.className='v111-notify-wrap v111-notify-config';
    wrap.innerHTML='<button id="v111NotifyOpen" class="btn secondary" type="button">'+tr('Centro de notificações','Notification center','Centro de notificaciones','Centre de notifications')+' <span id="v111NotifyCount"></span></button><div id="v111NotifyPanel" class="v111-notify-panel hidden"><div class="v111-notify-head"><strong>'+tr('Notificações','Notifications','Notificaciones','Notifications')+'</strong><button id="v111MarkRead" class="btn secondary">'+tr('Marcar todas como lidas','Mark all read','Marcar todas leídas','Tout marquer lu')+'</button></div><div id="v111NotifyList"></div></div>';
    const anchor=$('#v190ConfigCard')||config.querySelector('.config-card')||config;
    anchor.appendChild(wrap);
    $('#v111NotifyOpen').onclick=async()=>{$('#v111NotifyPanel').classList.toggle('hidden');await renderNotifications();};
    $('#v111MarkRead').onclick=async()=>{await req('/api/v111/notifications/read',{method:'POST',body:'{}'});await renderNotifications();updateBell();};
    document.addEventListener('click',e=>{if(!wrap.contains(e.target))$('#v111NotifyPanel').classList.add('hidden');});
    updateBell();setInterval(updateBell,15000);
  }
  async function updateBell(){try{const rows=await req('/api/v111/notifications?unread=1&limit=200');const n=rows.length;const el=$('#v111NotifyCount');if(el)el.textContent=n?'('+String(n)+')':'';}catch(_){}}
  async function renderNotifications(){const host=$('#v111NotifyList');if(!host)return;try{const rows=await req('/api/v111/notifications?limit=100');host.innerHTML=rows.length?rows.map(n=>'<article class="v111-note '+esc(n.severity)+(n.read_at?' read':'')+'"><time>'+esc(n.timestamp)+'</time><strong>'+esc(n.title)+'</strong><p>'+esc(n.detail||'')+'</p></article>').join(''):'<p>—</p>';}catch(e){host.textContent=e.message;}}

  function healthLabel(state){
    return {
      disconnected:tr('Desconectado','Disconnected','Desconectado','Déconnecté'),
      transport_open_waiting:tr('Porta aberta, sem dados','Transport open, no data','Puerto abierto, sin datos','Transport ouvert, sans données'),
      bytes_without_kiss:tr('Bytes chegando, sem KISS','Bytes arriving, no KISS','Bytes llegando, sin KISS','Octets reçus, sans KISS'),
      terminal_bytes_active:tr('Terminal/PKT ativo','Terminal/PKT active','Terminal/PKT activo','Terminal/PKT actif'),
      terminal_prompt_detected:tr('Prompt de TNC detectado','TNC prompt detected','Prompt TNC detectado','Invite TNC détectée'),
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
    const reference=tab.querySelector(':scope > .tnc-card, :scope > .tnc-status-grid')||tab.firstElementChild;
    tab.insertBefore(host,reference?.nextSibling||null);
    if(host.parentElement!==tab)tab.appendChild(host);
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
    card.innerHTML='<h3>'+tr('Saúde e retenção do banco','Database health and retention','Salud y retención de la base','Santé et rétention de la base')+'</h3>'+
      '<p>'+tr('Retenções menores mantêm o banco mais leve; períodos maiores preservam mais histórico. Cada categoria é independente.','Shorter retention keeps the database lighter; longer periods preserve more history. Each category is independent.','Retenciones menores mantienen la base más liviana; períodos mayores conservan más historial. Cada categoría es independiente.','Une rétention plus courte allège la base; une durée plus longue conserve davantage d’historique. Chaque catégorie est indépendante.')+'</p>'+
      '<div id="v111DbMetrics" class="v111-counter-grid"></div><div class="v111-retention-grid"></div><div class="v111-actions"><button id="v111RetentionSave" class="btn secondary">'+tr('Salvar política','Save policy','Guardar política','Enregistrer politique')+'</button><button id="v111RetentionApply" class="btn secondary">'+tr('Aplicar limpeza agora','Apply cleanup now','Aplicar limpieza ahora','Appliquer nettoyage')+'</button><button id="v111DbOptimize" class="btn secondary">'+tr('Otimizar banco','Optimize database','Optimizar base','Optimiser base')+'</button></div>';
    config.appendChild(card);
    const defs=[
      ['packets_days',tr('Pacotes brutos','Raw packets','Paquetes brutos','Paquets bruts')],
      ['tracks_days','Tracklogs'],
      ['aprs_log_days','APRS log'],
      ['topology_events_days',tr('Enlaces / Topologia','Links / Topology','Enlaces / Topología','Liens / Topologie')],
      ['tnc_frames_days','TNC frames'],
      ['tnc_decisions_days','TNC decisions'],
      ['notifications_days',tr('Notificações','Notifications','Notificaciones','Notifications')],
      ['messages_days',tr('Mensagens','Messages','Mensajes','Messages')]
    ];
    const presetOptions=(value)=>{
      const v=Number(value||0);
      const presets=[
        [0,tr('Não apagar','Do not delete','No borrar','Ne pas supprimer')],
        [1,tr('1 dia','1 day','1 día','1 jour')],
        [7,tr('1 semana','1 week','1 semana','1 semaine')],
        [30,tr('1 mês','1 month','1 mes','1 mois')]
      ];
      if(!presets.some(([n])=>n===v))presets.push([v,tr('Atual: ','Current: ','Actual: ','Actuel : ')+v+' '+tr('dias','days','días','jours')]);
      return presets.map(([n,label])=>'<option value="'+n+'"'+(n===v?' selected':'')+'>'+esc(label)+'</option>').join('');
    };
    const load=async()=>{
      const [h,saved]=await Promise.all([req('/api/v111/db/health'),req('/api/v111/db/retention')]);
      $('#v111DbMetrics').innerHTML=[
        [tr('Tamanho','Size','Tamaño','Taille'),Math.round(h.size_bytes/1024/1024*10)/10+' MB'],
        ['SQLite',h.integrity],[tr('Fragmentação','Fragmentation','Fragmentación','Fragmentation'),h.fragmentation_percent+'%'],
        ['WAL',Math.round(h.wal_bytes/1024/1024*10)/10+' MB']
      ].map(([k,v])=>'<div><span>'+esc(k)+'</span><strong>'+esc(v)+'</strong></div>').join('');
      $('.v111-retention-grid',card).innerHTML=defs.map(([k,l])=>'<label class="field"><span>'+esc(l)+'</span><select data-ret="'+k+'">'+presetOptions(saved[k])+'</select></label>').join('');
    };
    const payload=()=>{const p={};$$('[data-ret]',card).forEach(i=>p[i.dataset.ret]=Number(i.value||0));return p;};
    $('#v111RetentionSave').onclick=async()=>{await req('/api/v111/db/retention',{method:'POST',body:JSON.stringify(payload())});toast(tr('Política de retenção salva.','Retention policy saved.','Política de retención guardada.','Politique de rétention enregistrée.'));};
    $('#v111RetentionApply').onclick=async()=>{
      if(!confirm(tr('Aplicar agora a política de retenção?','Apply retention policy now?','¿Aplicar política ahora?','Appliquer la politique maintenant ?')))return;
      await req('/api/v111/db/retention',{method:'POST',body:JSON.stringify(payload())});
      const r=await req('/api/v111/db/retention/apply',{method:'POST',body:'{}'});
      const reclaimed=Math.max(0,Number(r.reclaimable_bytes||0))/1024/1024;
      toast(tr('Limpeza concluída: ','Cleanup completed: ','Limpieza concluida: ','Nettoyage terminé : ')+Number(r.deleted_total||0)+' '+tr('registros removidos; ','records removed; ','registros eliminados; ','enregistrements supprimés ; ')+reclaimed.toFixed(1)+' MB '+tr('recuperáveis ao otimizar.','reclaimable after optimization.','recuperables al optimizar.','récupérables après optimisation.'));
      load();
    };
    $('#v111DbOptimize').onclick=async()=>{if(!confirm(tr('Otimizar o SQLite agora?','Optimize SQLite now?','¿Optimizar SQLite ahora?','Optimiser SQLite maintenant ?')))return;await req('/api/v111/db/optimize',{method:'POST',body:'{}'});toast(tr('Banco otimizado.','Database optimized.','Base optimizada.','Base optimisée.'));load();};
    load();
  }

  function installAutoReply(){
    const config=$('#tab-config');if(!config||$('#v148AutoReply'))return;
    const card=document.createElement('div');card.id='v148AutoReply';card.className='config-card full-card config-section';
    card.innerHTML='<h3>'+tr('Resposta automática','Automatic reply','Respuesta automática','Réponse automatique')+'</h3>'+
      '<p>'+tr('Responde apenas a mensagens APRS diretas destinadas à sua estação. ACK/REJ, queries, boletins e grupos não disparam esta função.','Replies only to direct APRS messages addressed to your station. ACK/REJ, queries, bulletins and groups do not trigger it.','Responde solo a mensajes APRS directos destinados a su estación. ACK/REJ, consultas, boletines y grupos no activan esta función.','Répond uniquement aux messages APRS directs adressés à votre station. ACK/REJ, requêtes, bulletins et groupes ne la déclenchent pas.')+'</p>'+
      '<label class="check-field"><input id="v148AutoReplyEnabled" type="checkbox"><span>'+tr('Ativar resposta automática','Enable automatic reply','Activar respuesta automática','Activer la réponse automatique')+'</span></label>'+
      '<label class="field"><span>'+tr('Texto da resposta','Reply text','Texto de respuesta','Texte de réponse')+'</span><textarea id="v148AutoReplyText" rows="3" maxlength="240"></textarea></label>'+
      '<label class="field"><span>'+tr('Intervalo mínimo para o mesmo remetente','Minimum interval for the same sender','Intervalo mínimo para el mismo remitente','Intervalle minimum pour le même expéditeur')+'</span><select id="v148AutoReplyCooldown"><option value="30">30 s</option><option value="60">1 min</option><option value="300">5 min</option><option value="900">15 min</option><option value="3600">1 h</option></select></label>'+
      '<div class="v111-actions"><button id="v148AutoReplySave" class="btn secondary">'+tr('Salvar resposta automática','Save automatic reply','Guardar respuesta automática','Enregistrer la réponse automatique')+'</button></div>';
    config.appendChild(card);
    const load=async()=>{try{const cfg=await req('/api/config');$('#v148AutoReplyEnabled').checked=!!cfg.auto_reply_enabled;$('#v148AutoReplyText').value=cfg.auto_reply_text||'';const sel=$('#v148AutoReplyCooldown');const value=String(cfg.auto_reply_cooldown_seconds||300);if(!Array.from(sel.options).some(o=>o.value===value)){const o=document.createElement('option');o.value=value;o.textContent=value+' s';sel.appendChild(o);}sel.value=value;}catch(e){toast(e.message);}};
    $('#v148AutoReplySave').onclick=async()=>{
      const payload={auto_reply_enabled:$('#v148AutoReplyEnabled').checked,auto_reply_text:$('#v148AutoReplyText').value,auto_reply_cooldown_seconds:Number($('#v148AutoReplyCooldown').value||300)};
      const saved=await req('/api/config',{method:'POST',body:JSON.stringify(payload)});
      if(saved && saved.ok===false)throw new Error(saved.error||'Erro');
      toast(tr('Resposta automática salva.','Automatic reply saved.','Respuesta automática guardada.','Réponse automatique enregistrée.'));
      load();
    };
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

  function boot(){installNotificationCenter();installTncOperations();installDatabaseHealth();installAutoReply();watchStation();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();