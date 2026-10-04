(() => {
  'use strict';
  const $ = (s,r=document)=>r.querySelector(s);
  const $$ = (s,r=document)=>Array.from(r.querySelectorAll(s));
  const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const lang=()=>String(document.documentElement.lang||localStorage.getItem('pt2vhf_language')||'pt-BR').toLowerCase();
  const tr=(pt,en,es,fr)=>lang().startsWith('en')?en:lang().startsWith('es')?es:lang().startsWith('fr')?fr:pt;
  const req=async(url,opts={})=>{
    const r=await fetch(url,{cache:'no-store',...opts});
    const ct=r.headers.get('content-type')||'';
    const d=ct.includes('json')?await r.json():await r.text();
    if(!r.ok) throw new Error(d?.error||d||r.statusText);
    return d;
  };
  const notify=msg=>{
    const toast=$('#toast');
    if(toast){toast.textContent=msg;toast.classList.remove('hidden');setTimeout(()=>toast.classList.add('hidden'),5000);}
  };

  function profileMarkup(p, rf=[]) {
    const title=tr('Dados externos','External data','Datos externos','Données externes');
    const rows=[];
    const add=(k,v)=>{if(v!==undefined&&v!==null&&String(v).trim()) rows.push('<div><span>'+esc(k)+'</span><strong>'+esc(v)+'</strong></div>');};
    add(tr('Nome','Name','Nombre','Nom'),p.name);
    add(tr('Cidade','City','Ciudad','Ville'),p.city);
    add(tr('Estado/Região','State/Region','Estado/Región','État/Région'),p.state);
    add(tr('País','Country','País','Pays'),p.country);
    add('Grid',p.grid);
    if(rf[0]){
      const m=rf[0];
      add('RSSI',m.rssi==null?'—':m.rssi+' dBm');
      add('SNR',m.snr==null?'—':m.snr+' dB');
      add('DCD',m.dcd==null?'—':(m.dcd?tr('Ativo','Active','Activo','Actif'):tr('Inativo','Inactive','Inactivo','Inactif')));
      add(tr('Frequência','Frequency','Frecuencia','Fréquence'),m.frequency_hz?Number(m.frequency_hz/1e6).toFixed(4)+' MHz':'—');
      add(tr('Fonte RF','RF source','Fuente RF','Source RF'),m.provider||'—');
    }
    const image=p.image_url?'<img class="v110-profile-photo" src="'+esc(p.image_url)+'" alt="'+esc(p.callsign||'')+'" referrerpolicy="no-referrer">':'<div class="v110-profile-placeholder">📡</div>';
    const status=p.status==='credentials_required'?tr('Configure as credenciais do QRZ.com em Configuração.','Configure QRZ.com credentials in Settings.','Configure las credenciales de QRZ.com en Configuración.','Configurez les identifiants QRZ.com dans Configuration.'):
      p.status==='disabled'?tr('Integração QRZ.com desativada.','QRZ.com integration disabled.','Integración QRZ.com desactivada.','Intégration QRZ.com désactivée.'):
      p.status==='not_found'?tr('Indicativo não encontrado no QRZ.com.','Callsign not found on QRZ.com.','Indicativo no encontrado en QRZ.com.','Indicatif introuvable sur QRZ.com.'):
      p.status==='error'?esc(p.error||''):'';
    return '<section class="v110-profile-card"><h4>'+title+'</h4><div class="v110-profile-main">'+image+'<div class="v110-profile-data">'+rows.join('')+'</div></div>'+
      (p.profile_url?'<a href="'+esc(p.profile_url)+'" target="_blank" rel="noopener">QRZ.com ↗</a>':'')+
      (p._cache?.fetched_at?'<small>'+tr('Atualizado','Updated','Actualizado','Mis à jour')+': '+esc(p._cache.fetched_at)+'</small>':'')+
      (status?'<small class="v110-profile-status">'+status+'</small>':'')+'</section>';
  }

  async function enrichOrganizer() {
    const modal=$('#v190StationOrganizer');
    if(!modal || modal.classList.contains('hidden')) return;
    const title=$('#v190OrgTitle',modal);
    const call=String(title?.textContent||'').trim().toUpperCase();
    if(!call) return;
    let host=$('#v110OrganizerProfile',modal);
    if(!host){
      host=document.createElement('div');host.id='v110OrganizerProfile';
      const actions=$('.message-alert-actions',modal);
      (actions?.parentNode||$('.message-alert-content',modal))?.insertBefore(host,actions||null);
    }
    host.innerHTML='<div class="v110-loading">'+tr('Consultando perfil…','Loading profile…','Consultando perfil…','Chargement du profil…')+'</div>';
    try{
      const [profile,rf]=await Promise.all([
        req('/api/v110/station-profile/'+encodeURIComponent(call)),
        req('/api/v110/rf-metadata/'+encodeURIComponent(call)+'?limit=1')
      ]);
      host.innerHTML=profileMarkup(profile,rf);
    }catch(e){host.textContent=e.message;}
  }

  function watchOrganizer(){
    const observer=new MutationObserver(()=>{if(!$('#v190StationOrganizer')?.classList.contains('hidden')) enrichOrganizer();});
    observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  }

  function watchSidePanel(){
    const observer=new MutationObserver(async()=>{
      const panel=$('#v1818StationPanel');
      if(!panel||panel.classList.contains('hidden'))return;
      const call=String($('#v1818StationTitle',panel)?.textContent||'').trim();
      if(!call)return;
      let host=$('#v110SideProfile',panel);
      if(!host){host=document.createElement('div');host.id='v110SideProfile';$('#v1818StationBody',panel)?.prepend(host);}
      if(host.dataset.call===call)return;host.dataset.call=call;
      try{
        const [profile,rf]=await Promise.all([req('/api/v110/station-profile/'+encodeURIComponent(call)),req('/api/v110/rf-metadata/'+encodeURIComponent(call)+'?limit=1')]);
        host.innerHTML=profileMarkup(profile,rf);
      }catch(e){host.textContent=e.message;}
    });
    observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  }

  function installExternalConfig(){
    const config=$('#tab-config');
    if(!config||$('#v110ExternalConfig'))return;
    const card=document.createElement('div');card.id='v110ExternalConfig';card.className='config-card full-card config-section';
    card.innerHTML='<h3>'+tr('Perfis externos e AIS','External profiles and AIS','Perfiles externos y AIS','Profils externes et AIS')+'</h3>'+
    '<div class="v110-config-grid">'+
      '<section><h4>QRZ.com</h4><label class="check-field"><input id="v110QrzEnabled" type="checkbox"><span>'+tr('Ativar enriquecimento de estações','Enable station enrichment','Activar enriquecimiento de estaciones','Activer l’enrichissement des stations')+'</span></label>'+
      '<label class="field"><span>'+tr('Usuário QRZ.com','QRZ.com username','Usuario QRZ.com','Utilisateur QRZ.com')+'</span><input id="v110QrzUser"></label>'+
      '<label class="field"><span>'+tr('Senha/API do QRZ.com','QRZ.com password/API','Contraseña/API de QRZ.com','Mot de passe/API QRZ.com')+'</span><input id="v110QrzPassword" type="password" autocomplete="new-password" placeholder="'+tr('Deixe vazio para manter','Leave blank to keep','Deje vacío para mantener','Laisser vide pour conserver')+'"></label>'+
      '<label class="field"><span>'+tr('Cache (horas)','Cache (hours)','Caché (horas)','Cache (heures)')+'</span><input id="v110QrzCache" type="number" min="1" max="8760"></label></section>'+
      '<section><h4>'+tr('Foto AIS','AIS photo','Foto AIS','Photo AIS')+'</h4><label class="check-field"><input id="v110AisEnabled" type="checkbox"><span>'+tr('Ativar provedor externo','Enable external provider','Activar proveedor externo','Activer fournisseur externe')+'</span></label>'+
      '<label class="field"><span>'+tr('URL do provedor','Provider URL','URL del proveedor','URL du fournisseur')+'</span><input id="v110AisUrl" placeholder="https://api.exemplo/{mmsi}?imo={imo}"></label>'+
      '<label class="field"><span>API key</span><input id="v110AisKey" type="password" autocomplete="new-password" placeholder="'+tr('Opcional / deixe vazio para manter','Optional / leave blank to keep','Opcional / deje vacío para mantener','Optionnel / laisser vide pour conserver')+'"></label>'+
      '<label class="field"><span>'+tr('Cache (horas)','Cache (hours)','Caché (horas)','Cache (heures)')+'</span><input id="v110AisCache" type="number" min="1" max="8760"></label></section>'+
    '</div><button id="v110ExternalSave" class="btn primary" type="button">'+tr('Salvar integrações','Save integrations','Guardar integraciones','Enregistrer les intégrations')+'</button>'+
    '<p class="muted">'+tr('As integrações usam APIs configuradas/oficiais e não fazem scraping de páginas.','Integrations use configured/official APIs and do not scrape web pages.','Las integraciones usan APIs configuradas/oficiales y no hacen scraping.','Les intégrations utilisent des API configurées/officielles et ne font pas de scraping.')+'</p>';
    config.appendChild(card);
    req('/api/v110/external/settings').then(s=>{
      $('#v110QrzEnabled').checked=!!s.qrz_enabled;$('#v110QrzUser').value=s.qrz_username||'';$('#v110QrzCache').value=s.qrz_cache_hours||168;
      $('#v110AisEnabled').checked=!!s.ais_enabled;$('#v110AisUrl').value=s.ais_url_template||'';$('#v110AisCache').value=s.ais_cache_hours||168;
      if(s.qrz_password_set)$('#v110QrzPassword').placeholder=tr('Credencial já configurada','Credential already configured','Credencial ya configurada','Identifiant déjà configuré');
      if(s.ais_api_key_set)$('#v110AisKey').placeholder='API key '+tr('já configurada','already configured','ya configurada','déjà configurée');
    });
    $('#v110ExternalSave').onclick=async()=>{
      const payload={qrz_enabled:$('#v110QrzEnabled').checked,qrz_username:$('#v110QrzUser').value,qrz_password:$('#v110QrzPassword').value,qrz_cache_hours:Number($('#v110QrzCache').value||168),ais_enabled:$('#v110AisEnabled').checked,ais_url_template:$('#v110AisUrl').value,ais_api_key:$('#v110AisKey').value,ais_cache_hours:Number($('#v110AisCache').value||168)};
      await req('/api/v110/external/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      $('#v110QrzPassword').value='';$('#v110AisKey').value='';notify(tr('Integrações salvas.','Integrations saved.','Integraciones guardadas.','Intégrations enregistrées.'));
    };
  }

  function installQualityTools(){
    const help=$('#tab-help');
    if(help&&!$('#v110QualityTools')){
      const card=document.createElement('article');card.id='v110QualityTools';card.className='help-card help-wide';
      card.innerHTML='<h3>'+tr('Validação e estabilidade','Validation and stability','Validación y estabilidad','Validation et stabilité')+'</h3>'+
      '<div class="v110-tools-grid"><section><h4>'+tr('Soak test','Soak test','Soak test','Soak test')+'</h4><label class="field"><span>'+tr('Duração','Duration','Duración','Durée')+'</span><select id="v110SoakHours"><option value="24">24 h</option><option value="72">72 h</option><option value="168">7 d</option><option value="0.05">'+tr('Teste rápido (~3 min)','Quick test (~3 min)','Prueba rápida (~3 min)','Test rapide (~3 min)')+'</option></select></label><button id="v110SoakStart" class="btn primary">'+tr('Iniciar','Start','Iniciar','Démarrer')+'</button> <button id="v110SoakStop" class="btn secondary">'+tr('Parar','Stop','Detener','Arrêter')+'</button><pre id="v110SoakStatus"></pre></section>'+
      '<section><h4>Kenwood TM-D700 PKT</h4><p>'+tr('Diagnóstico passivo: não transmite RF. A validação física exige o rádio real.','Passive diagnostic: does not transmit RF. Physical validation requires the real radio.','Diagnóstico pasivo: no transmite RF. La validación física requiere el radio real.','Diagnostic passif : aucune émission RF. La validation physique exige le poste réel.')+'</p><button id="v110TmProbe" class="btn secondary">'+tr('Executar diagnóstico TM-D700','Run TM-D700 diagnostic','Ejecutar diagnóstico TM-D700','Exécuter diagnostic TM-D700')+'</button><pre id="v110TmStatus"></pre></section></div>';
      ($('.help-grid',help)||help).appendChild(card);
      const refresh=async()=>{$('#v110SoakStatus').textContent=JSON.stringify(await req('/api/v110/soak/status'),null,2);};
      $('#v110SoakStart').onclick=async()=>{$('#v110SoakStatus').textContent=JSON.stringify(await req('/api/v110/soak/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({hours:Number($('#v110SoakHours').value),interval_seconds:300})}),null,2);};
      $('#v110SoakStop').onclick=async()=>{$('#v110SoakStatus').textContent=JSON.stringify(await req('/api/v110/soak/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}),null,2);};
      $('#v110TmProbe').onclick=async()=>{$('#v110TmStatus').textContent=tr('Executando…','Running…','Ejecutando…','Exécution…');try{$('#v110TmStatus').textContent=JSON.stringify(await req('/api/v110/tm-d700/probe',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}),null,2);}catch(e){$('#v110TmStatus').textContent=e.message;}};
      refresh();
    }
  }

  function enrichAisPopups(){
    const attach=()=>{
      if(!window.map||window.__v110AisBound)return;
      window.__v110AisBound=true;
      window.map.on('popupopen',async ev=>{
        const el=ev.popup?.getElement?.();if(!el||!el.querySelector('.object-friendly-popup'))return;
        const strongs=$$('strong',el);
        let mmsi='';
        for(const st of strongs){if(st.textContent.trim()==='MMSI'){mmsi=st.nextElementSibling?.textContent?.trim()||'';break;}}
        if(!/^\d{7,9}$/.test(mmsi))return;
        let host=$('.v110-ais-photo',el);if(!host){host=document.createElement('div');host.className='v110-ais-photo';$('.object-friendly-popup',el)?.insertBefore(host,$('.object-popup-technical',el));}
        try{
          const p=await req('/api/v110/ais-profile/'+encodeURIComponent(mmsi));
          if(p.image_url)host.innerHTML='<img src="'+esc(p.image_url)+'" alt="AIS '+esc(mmsi)+'" referrerpolicy="no-referrer"><small>'+tr('Foto externa associada por MMSI','External photo matched by MMSI','Foto externa asociada por MMSI','Photo externe associée par MMSI')+'</small>';
          else host.innerHTML='';
        }catch(_){host.innerHTML='';}
      });
    };
    const timer=setInterval(()=>{attach();if(window.__v110AisBound)clearInterval(timer);},1000);
  }

  function boot(){installExternalConfig();installQualityTools();watchOrganizer();watchSidePanel();enrichAisPopups();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();