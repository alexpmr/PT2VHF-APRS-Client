(() => {
  'use strict';
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const lang = () => (document.documentElement.lang || localStorage.getItem('pt2vhf_language') || 'pt-BR').toLowerCase();
  const tr = (pt,en,es,fr) => lang().startsWith('en')?en:lang().startsWith('es')?es:lang().startsWith('fr')?fr:pt;
  const json = async (url, opts={}) => {
    const r = await fetch(url, {cache:'no-store', headers:{'Content-Type':'application/json', ...(opts.headers||{})}, ...opts});
    const d = await r.json();
    if (!r.ok) throw new Error(d?.error || r.statusText);
    return d;
  };
  const notify = msg => {
    const toast = $('#toast');
    if (toast) { toast.textContent = msg; toast.classList.remove('hidden'); setTimeout(()=>toast.classList.add('hidden'), 5000); }
  };

  function floatPanel(panelId, label) {
    const panel = document.getElementById(panelId);
    if (!panel || panel.dataset.v190FloatReady) return;
    panel.dataset.v190FloatReady = '1';
    const header = $('.panel-header', panel) || panel.firstElementChild;
    if (!header) return;
    const actions = document.createElement('div');
    actions.className = 'v190-float-actions';
    actions.innerHTML = '<button type="button" class="btn secondary v190-detach">↗ '+tr('Destacar','Detach','Desacoplar','Détacher')+'</button>';
    header.appendChild(actions);

    let placeholder = null;
    let dragging = false, dx = 0, dy = 0;
    const key = 'pt2vhf_v190_float_'+panelId;
    const state = () => { try { return JSON.parse(localStorage.getItem(key)||'{}'); } catch(_) { return {}; } };
    const save = () => {
      if (!panel.classList.contains('v190-floating')) return;
      const r=panel.getBoundingClientRect();
      localStorage.setItem(key, JSON.stringify({left:r.left,top:r.top,width:r.width,height:r.height,minimized:panel.classList.contains('v190-minimized')}));
    };
    const detach = () => {
      if (panel.classList.contains('v190-floating')) return;
      placeholder = document.createComment('v190-'+panelId);
      panel.parentNode.insertBefore(placeholder, panel);
      panel.classList.remove('tab-panel','active');
      panel.classList.add('v190-floating');
      document.body.appendChild(panel);
      const s=state();
      panel.style.left=(s.left ?? Math.max(20,window.innerWidth*0.18))+'px';
      panel.style.top=(s.top ?? 120)+'px';
      panel.style.width=(s.width ?? Math.min(720,window.innerWidth*0.65))+'px';
      panel.style.height=(s.height ?? Math.min(620,window.innerHeight*0.7))+'px';
      if (s.minimized) panel.classList.add('v190-minimized');
      actions.innerHTML='<button type="button" class="btn secondary v190-minimize">—</button><button type="button" class="btn secondary v190-dock">↙ '+tr('Encaixar','Dock','Acoplar','Ancrer')+'</button>';
      document.querySelector('[data-tab="map"]')?.click();
      bindButtons();
      save();
    };
    const dock = () => {
      panel.classList.remove('v190-floating','v190-minimized');
      panel.removeAttribute('style');
      panel.classList.add('tab-panel');
      if (placeholder?.parentNode) placeholder.parentNode.replaceChild(panel, placeholder);
      placeholder = null;
      actions.innerHTML='<button type="button" class="btn secondary v190-detach">↗ '+tr('Destacar','Detach','Desacoplar','Détacher')+'</button>';
      bindButtons();
      document.querySelector('[data-tab="'+(panelId==='tab-messages'?'messages':'stations')+'"]')?.click();
    };
    const minimize = () => { panel.classList.toggle('v190-minimized'); save(); };
    const bindButtons = () => {
      $('.v190-detach',actions)?.addEventListener('click',detach);
      $('.v190-dock',actions)?.addEventListener('click',dock);
      $('.v190-minimize',actions)?.addEventListener('click',minimize);
    };
    bindButtons();
    header.classList.add('v190-drag-handle');
    header.addEventListener('pointerdown', ev => {
      if (!panel.classList.contains('v190-floating') || ev.target.closest('button,input,select,textarea,a,label')) return;
      dragging=true; const r=panel.getBoundingClientRect(); dx=ev.clientX-r.left; dy=ev.clientY-r.top;
      header.setPointerCapture?.(ev.pointerId);
    });
    header.addEventListener('pointermove', ev => {
      if (!dragging) return;
      const w=panel.offsetWidth,h=panel.offsetHeight;
      panel.style.left=Math.max(0,Math.min(window.innerWidth-w,ev.clientX-dx))+'px';
      panel.style.top=Math.max(0,Math.min(window.innerHeight-48,ev.clientY-dy))+'px';
    });
    header.addEventListener('pointerup',()=>{dragging=false;save();});
    panel.addEventListener('mouseup',save);
    new ResizeObserver(save).observe(panel);
  }

  function installGlobalSearch() {
    document.querySelector('.v1818-search')?.remove();
    const bar=$('.map-context-controls');
    if (!bar || $('#v190GlobalSearch')) return;
    const wrap=document.createElement('div');
    wrap.className='v190-search';
    wrap.innerHTML='<input id="v190GlobalSearch" type="search" autocomplete="off" placeholder="'+tr('Busca global…','Global search…','Búsqueda global…','Recherche globale…')+'"><div class="v190-search-results hidden"></div>';
    bar.prepend(wrap);
    const input=$('input',wrap), results=$('.v190-search-results',wrap);
    let seq=0;
    input.addEventListener('input',async()=>{
      const q=input.value.trim(), n=++seq;
      if(q.length<2){results.classList.add('hidden');results.innerHTML='';return;}
      try{
        const rows=await json('/api/v190/search?q='+encodeURIComponent(q)+'&limit=30');
        if(n!==seq)return;
        results.innerHTML=rows.map(r=>'<button type="button" data-kind="'+esc(r.entity_type)+'" data-key="'+esc(r.key)+'" data-lat="'+esc(r.latitude)+'" data-lon="'+esc(r.longitude)+'"><span><strong>'+esc(r.key)+'</strong><small>'+esc(r.friendly_name||r.name||r.info||r.comment||'')+'</small></span><em>'+esc(r.entity_type)+'</em></button>').join('');
        results.classList.toggle('hidden',!rows.length);
      }catch(e){results.innerHTML='<div class="v190-search-error">'+esc(e.message)+'</div>';results.classList.remove('hidden');}
    });
    results.addEventListener('click',ev=>{
      const b=ev.target.closest('button[data-key]'); if(!b)return;
      results.classList.add('hidden'); input.value=b.dataset.key;
      const lat=Number(b.dataset.lat),lon=Number(b.dataset.lon);
      document.querySelector('[data-tab="map"]')?.click();
      try{ if(Number.isFinite(lat)&&Number.isFinite(lon)&&window.map) window.map.setView([lat,lon],Math.max(window.map.getZoom(),12)); }catch(_){}
      if(b.dataset.kind==='station') openStationOrganizer(b.dataset.key);
    });
  }

  async function openStationOrganizer(callsign) {
    let modal=$('#v190StationOrganizer');
    if(!modal){
      modal=document.createElement('div'); modal.id='v190StationOrganizer'; modal.className='message-alert-overlay hidden';
      modal.innerHTML='<div class="message-alert-card v190-organizer"><div class="message-alert-content"><div class="message-alert-eyebrow">'+tr('Organização da estação','Station organization','Organización de estación','Organisation de station')+'</div><h3 id="v190OrgTitle"></h3><label class="field"><span>'+tr('Nome amigável','Friendly name','Nombre amigable','Nom convivial')+'</span><input id="v190Friendly"></label><label class="field"><span>'+tr('Grupo','Group','Grupo','Groupe')+'</span><select id="v190Group"></select></label><label class="field"><span>'+tr('Cor','Color','Color','Couleur')+'</span><input id="v190Color" type="color" value="#ffaa00"></label><label class="check-field"><input id="v190Favorite" type="checkbox"><span>'+tr('Favorita','Favorite','Favorita','Favorite')+'</span></label><label class="field"><span>'+tr('Nota','Note','Nota','Note')+'</span><textarea id="v190Note" rows="3"></textarea></label><div class="message-alert-actions"><button id="v190OrgSave" class="btn primary">'+tr('Salvar','Save','Guardar','Enregistrer')+'</button><button id="v190OrgClose" class="btn secondary">'+tr('Fechar','Close','Cerrar','Fermer')+'</button></div></div></div>';
      document.body.appendChild(modal);
      $('#v190OrgClose',modal).onclick=()=>modal.classList.add('hidden');
    }
    const [meta,groups]=await Promise.all([json('/api/v190/stations/'+encodeURIComponent(callsign)+'/meta'),json('/api/v190/groups')]);
    $('#v190OrgTitle',modal).textContent=callsign;
    $('#v190Friendly',modal).value=meta.friendly_name||'';
    $('#v190Note',modal).value=meta.note||'';
    $('#v190Favorite',modal).checked=!!meta.favorite;
    $('#v190Color',modal).value=/^#[0-9a-f]{6}$/i.test(meta.color||'')?meta.color:'#ffaa00';
    $('#v190Group',modal).innerHTML='<option value="">—</option>'+groups.map(g=>'<option value="'+g.id+'">'+esc(g.name)+'</option>').join('');
    $('#v190Group',modal).value=meta.group_id||'';
    $('#v190OrgSave',modal).onclick=async()=>{
      await json('/api/v190/stations/'+encodeURIComponent(callsign)+'/meta',{method:'POST',body:JSON.stringify({friendly_name:$('#v190Friendly',modal).value,group_id:$('#v190Group',modal).value,color:$('#v190Color',modal).value,note:$('#v190Note',modal).value})});
      await json('/api/favorites/'+encodeURIComponent(callsign),{method:'POST',body:JSON.stringify({favorite:$('#v190Favorite',modal).checked})});
      notify(tr('Organização salva.','Organization saved.','Organización guardada.','Organisation enregistrée.')); modal.classList.add('hidden');
    };
    modal.classList.remove('hidden');
  }

  function installGroupsBackupAlerts() {
    const config=$('#tab-config');
    if(!config || $('#v190ConfigCard')) return;
    const card=document.createElement('div'); card.id='v190ConfigCard'; card.className='config-card full-card config-section';
    card.innerHTML='<h3>'+tr('Backup completo, grupos e alertas','Full backup, groups and alerts','Backup completo, grupos y alertas','Sauvegarde complète, groupes et alertes')+'</h3>'+
      '<div class="v190-config-grid"><div><h4>'+tr('Backup completo','Full backup','Backup completo','Sauvegarde complète')+'</h4><p>'+tr('Inclui banco, mensagens, estações, favoritos, tracklogs, agendamentos, grupos e preferências.','Includes database, messages, stations, favorites, tracklogs, schedules, groups and preferences.','Incluye base, mensajes, estaciones, favoritos, tracklogs, programaciones, grupos y preferencias.','Inclut base, messages, stations, favoris, traces, planifications, groupes et préférences.')+'</p><a class="btn secondary" href="/api/v190/backup/full">'+tr('Criar backup completo','Create full backup','Crear backup completo','Créer sauvegarde complète')+'</a><input id="v190RestoreFile" type="file" accept=".zip"><button id="v190Restore" type="button" class="btn danger">'+tr('Restaurar backup','Restore backup','Restaurar backup','Restaurer sauvegarde')+'</button></div>'+
      '<div><h4>'+tr('Grupos de estações','Station groups','Grupos de estaciones','Groupes de stations')+'</h4><div id="v190Groups"></div><div class="v190-group-add"><input id="v190GroupName" placeholder="'+tr('Nome do grupo','Group name','Nombre del grupo','Nom du groupe')+'"><button id="v190GroupAdd" class="btn secondary">'+tr('Adicionar','Add','Agregar','Ajouter')+'</button></div></div>'+
      '<div><h4>'+tr('Alertas configuráveis','Configurable alerts','Alertas configurables','Alertes configurables')+'</h4><div id="v190Alerts" class="v190-alert-list"></div><button id="v190AlertsSave" class="btn secondary">'+tr('Salvar alertas','Save alerts','Guardar alertas','Enregistrer alertes')+'</button></div></div>';
    config.appendChild(card);
    const renderGroups=async()=>{const groups=await json('/api/v190/groups');$('#v190Groups',card).innerHTML=groups.length?groups.map(g=>'<span class="v190-group-chip"><span>'+esc(g.name)+' <small>'+g.members+'</small></span><button type="button" class="v190-group-sync" data-group-id="'+g.id+'" title="'+tr('Usar em mensagens agendadas','Use in scheduled messages','Usar en mensajes programados','Utiliser dans les messages planifiés')+'">→ MSG</button></span>').join(''):'—';};
    renderGroups();
    $('#v190Groups',card).addEventListener('click',async ev=>{const b=ev.target.closest('.v190-group-sync');if(!b)return;try{await json('/api/v190/groups/'+b.dataset.groupId+'/sync-recipient-group',{method:'POST',body:'{}'});notify(tr('Grupo sincronizado com as listas de destinatários das mensagens agendadas.','Group synced to scheduled-message recipient lists.','Grupo sincronizado con las listas de destinatarios programados.','Groupe synchronisé avec les listes de destinataires planifiées.'));}catch(e){notify(e.message);}});
    $('#v190GroupAdd',card).onclick=async()=>{const name=$('#v190GroupName',card).value.trim();if(!name)return;await json('/api/v190/groups',{method:'POST',body:JSON.stringify({name})});$('#v190GroupName',card).value='';renderGroups();};
    $('#v190Restore',card).onclick=async()=>{
      const file=$('#v190RestoreFile',card).files?.[0]; if(!file){notify(tr('Selecione um backup.','Select a backup.','Seleccione un backup.','Sélectionnez une sauvegarde.'));return;}
      if(!confirm(tr('Restaurar o backup e substituir os dados atuais? Um backup pré-restauração será criado.','Restore backup and replace current data? A pre-restore backup will be created.','¿Restaurar el backup y reemplazar los datos actuales? Se creará un backup previo.','Restaurer la sauvegarde et remplacer les données actuelles ? Une sauvegarde préalable sera créée.')))return;
      const fd=new FormData();fd.append('backup',file);
      const r=await fetch('/api/v190/backup/restore',{method:'POST',body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error||r.statusText);notify(tr('Backup restaurado. Reinicie o aplicativo.','Backup restored. Restart the application.','Backup restaurado. Reinicie la aplicación.','Sauvegarde restaurée. Redémarrez l’application.'));
    };
    const defs=[['station_appeared',tr('Estação apareceu','Station appeared','Estación apareció','Station apparue')],['station_disappeared',tr('Estação desapareceu','Station disappeared','Estación desapareció','Station disparue')],['favorite_appeared',tr('Favorito apareceu','Favorite appeared','Favorito apareció','Favori apparu')],['new_message',tr('Nova mensagem','New message','Nuevo mensaje','Nouveau message')],['tnc_down',tr('TNC caiu','TNC disconnected','TNC desconectado','TNC déconnecté')],['aprsis_down',tr('APRS-IS caiu','APRS-IS disconnected','APRS-IS desconectado','APRS-IS déconnecté')],['database_problem',tr('Problema no banco','Database problem','Problema de base','Problème de base')]];
    const saveAlertSettings=async(showNotice=false)=>{
      const payload={};
      $('[data-v190-alert]',card).forEach(i=>payload[i.dataset.v190Alert]=i.checked);
      payload.disappear_minutes=Number($('#v190DisappearMinutes',card)?.value||60);
      await json('/api/v190/alerts/settings',{method:'POST',body:JSON.stringify(payload)});
      window.__pt2vhfV190AlertSettings={...payload};
      if(showNotice) notify(tr('Alertas salvos.','Alerts saved.','Alertas guardadas.','Alertes enregistrées.'));
    };
    let alertSaveTimer=null;
    json('/api/v190/alerts/settings').then(settings=>{
      window.__pt2vhfV190AlertSettings={...settings};
      $('#v190Alerts',card).innerHTML=defs.map(([k,l])=>'<label class="check-field"><input type="checkbox" data-v190-alert="'+k+'" '+(settings[k]?'checked':'')+'><span>'+esc(l)+'</span></label>').join('')+'<label class="field"><span>'+tr('Considerar desaparecida após','Consider disappeared after','Considerar desaparecida después de','Considérer disparue après')+'</span><input id="v190DisappearMinutes" type="number" min="5" max="1440" value="'+esc(settings.disappear_minutes||60)+'"></label>';
      const autoSave=()=>{
        clearTimeout(alertSaveTimer);
        alertSaveTimer=setTimeout(()=>saveAlertSettings(false).catch(()=>{}),250);
      };
      $('[data-v190-alert]',card).forEach(i=>i.addEventListener('change',()=>{
        window.__pt2vhfV190AlertSettings={...(window.__pt2vhfV190AlertSettings||{}),[i.dataset.v190Alert]:i.checked};
        autoSave();
      }));
      $('#v190DisappearMinutes',card)?.addEventListener('change',autoSave);
    });
    $('#v190AlertsSave',card).onclick=()=>saveAlertSettings(true).catch(e=>notify(e.message));
  }

  function installHelpDiagnostics() {
    const help=$('#tab-help');
    if(!help || $('#v190HelpDiagnostics')) return;
    const card=document.createElement('article');
    card.id='v190HelpDiagnostics'; card.className='help-card help-wide';
    card.innerHTML='<h3>'+tr('Diagnóstico e suporte','Diagnostics and support','Diagnóstico y soporte','Diagnostic et support')+'</h3><p>'+tr('Resumo operacional do aplicativo, banco SQLite, plataforma, APRS-IS e TNC/RF.','Operational summary of the app, SQLite database, platform, APRS-IS and TNC/RF.','Resumen operativo de la aplicación, SQLite, plataforma, APRS-IS y TNC/RF.','Résumé opérationnel de l’application, SQLite, plateforme, APRS-IS et TNC/RF.')+'</p><div id="v190DiagSummary" class="v190-diag-summary">—</div><div class="v1818-export-actions"><button id="v190DiagRefresh" type="button" class="btn secondary">'+tr('Atualizar diagnóstico','Refresh diagnostics','Actualizar diagnóstico','Actualiser diagnostic')+'</button><a class="btn primary" href="/api/v1818/diagnostics.zip">'+tr('Gerar pacote de suporte','Generate support package','Generar paquete de soporte','Générer paquet de support')+'</a></div>';
    const grid=$('.help-grid',help) || help;
    grid.appendChild(card);
    const refresh=async()=>{
      const box=$('#v190DiagSummary',card); box.textContent=tr('Carregando…','Loading…','Cargando…','Chargement…');
      try{
        const d=await json('/api/v1818/diagnostics');
        const rows=[
          [tr('Versão','Version','Versión','Version'),d.version],
          [tr('Plataforma','Platform','Plataforma','Plateforme'),d.platform],
          [tr('Arquitetura','Architecture','Arquitectura','Architecture'),d.architecture],
          ['SQLite',d.database?.quick_check],
          [tr('Tamanho do banco','Database size','Tamaño de base','Taille de base'),d.database?.size_bytes],
          ['APRS-IS',d.aprs_is?.connected?tr('Conectado','Connected','Conectado','Connecté'):tr('Desconectado','Disconnected','Desconectado','Déconnecté')],
          ['TNC/RF',d.tnc?.connected?tr('Conectado','Connected','Conectado','Connecté'):tr('Desconectado','Disconnected','Desconectado','Déconnecté')],
          [tr('Porta local','Local port','Puerto local','Port local'),d.local_server?.port]
        ];
        box.innerHTML=rows.map(([k,v])=>'<div><span>'+esc(k)+'</span><strong>'+esc(v??'—')+'</strong></div>').join('');
      }catch(e){box.textContent=e.message;}
    };
    $('#v190DiagRefresh',card).onclick=refresh; refresh();
  }

  function installTimelineAndTncTest() {
    const host=$('#v1818AdvancedPanel') || $('#tab-analysis');
    if(host && !$('#v190Timeline')){
      const details=document.createElement('details');
      details.innerHTML='<summary>'+tr('Timeline unificada','Unified timeline','Timeline unificada','Chronologie unifiée')+'</summary><div class="v190-timeline-controls"><select id="v190TimelineHours"><option value="0">'+tr('Completo','All','Completo','Complet')+'</option><option value="1">1 h</option><option value="24" selected>24 h</option><option value="168">7 d</option></select><select id="v190TimelineKind"><option value="">'+tr('Todos os eventos','All events','Todos los eventos','Tous les événements')+'</option><option value="message">'+tr('Mensagens','Messages','Mensajes','Messages')+'</option><option value="position">'+tr('Posições','Positions','Posiciones','Positions')+'</option><option value="query">Queries</option><option value="rf">RF</option></select><button id="v190TimelineRefresh" class="btn secondary" type="button">'+tr('Atualizar','Refresh','Actualizar','Actualiser')+'</button></div><div id="v190Timeline" class="v190-timeline"></div>';
      host.appendChild(details);
      const load=async()=>{const hours=$('#v190TimelineHours').value,kind=$('#v190TimelineKind').value;const rows=await json('/api/v190/timeline?limit=500&hours='+encodeURIComponent(hours)+'&kind='+encodeURIComponent(kind));$('#v190Timeline').innerHTML=rows.map(e=>'<div><time>'+esc(e.time)+'</time><strong>'+esc(e.kind)+'</strong><span>'+esc(e.title)+'</span><small>'+esc(e.detail||'')+'</small></div>').join('');};
      details.addEventListener('toggle',()=>{if(details.open)load();});
      $('#v190TimelineRefresh',details).onclick=load;
      $('#v190TimelineHours',details).onchange=load;
      $('#v190TimelineKind',details).onchange=load;
    }
    const tnc=$('#tab-tnc .panel-header') || $('#tab-tnc');
    if(tnc && !$('#v190TestTnc')){
      const b=document.createElement('button');b.id='v190TestTnc';b.className='btn secondary';b.type='button';b.textContent=tr('Testar TNC','Test TNC','Probar TNC','Tester TNC');
      tnc.appendChild(b);b.onclick=async()=>{b.disabled=true;try{const r=await json('/api/v190/tnc/test',{method:'POST',body:'{}'});notify((r.ok?'✓ ':'✗ ')+(r.summary||r.error||''));}catch(e){notify('✗ '+e.message);}finally{b.disabled=false;}};
    }
  }

  function installPresentationMode() {
    const bar=$('.map-context-controls'); if(!bar || $('#v190Presentation')) return;
    const b=document.createElement('button');b.id='v190Presentation';b.className='btn secondary';b.type='button';b.textContent='⛶ '+tr('Apresentação','Presentation','Presentación','Présentation');bar.appendChild(b);
    const exit=document.createElement('button');exit.id='v190PresentationExit';exit.className='btn secondary hidden';exit.textContent='× '+tr('Sair','Exit','Salir','Quitter');document.body.appendChild(exit);
    const off=()=>{document.body.classList.remove('v190-presentation');exit.classList.add('hidden');if(document.fullscreenElement)document.exitFullscreen?.();};
    b.onclick=()=>{document.body.classList.add('v190-presentation');exit.classList.remove('hidden');document.documentElement.requestFullscreen?.().catch(()=>{});setTimeout(()=>window.map?.invalidateSize?.(),200);};
    exit.onclick=off;document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&document.body.classList.contains('v190-presentation'))off();});
  }

  async function alertPoll() {
    let last=localStorage.getItem('pt2vhf_v190_alert_since')||new Date().toISOString();
    let previous=null;
    let previousActive=null;
    let databaseProblemLatched=false;
    const seenMessageIds=new Set(JSON.parse(localStorage.getItem('pt2vhf_v190_seen_message_ids')||'[]').map(String));
    const tick=async()=>{
      try{
        const [serverSettings,state]=await Promise.all([
          json('/api/v190/alerts/settings'),
          json('/api/v190/alerts/state?since='+encodeURIComponent(last))
        ]);
        const settings={...serverSettings,...(window.__pt2vhfV190AlertSettings||{})};
        const activeRows=Array.isArray(state.active_stations)?state.active_stations:[];
        const activeMap=new Map(activeRows.map(st=>[String(st.callsign||'').toUpperCase(),st]).filter(([call])=>call));

        if(previousActive!==null){
          for(const [call,st] of activeMap){
            if(previousActive.has(call)) continue;
            if(st.favorite&&settings.favorite_appeared){
              notify(tr('Favorito apareceu: ','Favorite appeared: ','Favorito apareció: ','Favori apparu : ')+call);
            }else if(settings.station_appeared){
              notify(tr('Estação apareceu: ','Station appeared: ','Estación apareció: ','Station apparue : ')+call);
            }
          }
          if(settings.station_disappeared){
            for(const call of previousActive){
              if(activeMap.has(call)) continue;
              notify(tr('Estação desaparecida há mais de ','Station absent for more than ','Estación ausente por más de ','Station absente depuis plus de ')+(state.disappear_minutes||60)+' min: '+call);
            }
          }
        }
        previousActive=new Set(activeMap.keys());

        for(const m of state.messages_since||[]){
          const id=String(m.id??'');
          if(!id||seenMessageIds.has(id)) continue;
          seenMessageIds.add(id);
          if(settings.new_message) notify(tr('Nova mensagem de ','New message from ','Nuevo mensaje de ','Nouveau message de ')+m.from_call+': '+m.message);
        }
        while(seenMessageIds.size>500) seenMessageIds.delete(seenMessageIds.values().next().value);
        localStorage.setItem('pt2vhf_v190_seen_message_ids',JSON.stringify(Array.from(seenMessageIds)));

        if(previous){
          const tncWas=!!previous.tnc?.connected, tncNow=!!state.tnc?.connected;
          const aprsWas=!!previous.aprs_is?.connected, aprsNow=!!state.aprs_is?.connected;
          const tncWanted=state.tnc?.wanted!==false;
          const aprsWanted=state.aprs_is?.wanted!==false;
          if(tncWas&&!tncNow&&tncWanted&&settings.tnc_down) notify(tr('TNC desconectado.','TNC disconnected.','TNC desconectado.','TNC déconnecté.'));
          if(aprsWas&&!aprsNow&&aprsWanted&&settings.aprsis_down) notify(tr('APRS-IS desconectado.','APRS-IS disconnected.','APRS-IS desconectado.','APRS-IS déconnecté.'));
        }

        const dbBad=String(state.database_integrity||'').toLowerCase()!=='ok';
        if(dbBad&&!databaseProblemLatched&&settings.database_problem){
          notify(tr('Problema detectado no banco SQLite.','SQLite database problem detected.','Problema detectado en SQLite.','Problème détecté dans SQLite.'));
        }
        databaseProblemLatched=dbBad;

        previous=state;
        last=state.now;
        localStorage.setItem('pt2vhf_v190_alert_since',last);
      }catch(_){}
    };
    await tick();
    setInterval(tick,15000);
  }

  function boot(){
    floatPanel('tab-messages','Mensagens');
    floatPanel('tab-stations','Estações');
    installGlobalSearch();
    installGroupsBackupAlerts();
    installTimelineAndTncTest();
    installHelpDiagnostics();
    installPresentationMode();
    alertPoll();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();