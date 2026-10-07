(()=>{
  'use strict';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const tr=(pt,en,es,fr)=>{
    const lang=document.documentElement.lang||'pt-BR';
    if(lang.startsWith('en'))return en;if(lang.startsWith('es'))return es;if(lang.startsWith('fr'))return fr;return pt;
  };
  async function req(url,opts={}){
    const res=await fetch(url,{headers:{'Content-Type':'application/json',...(opts.headers||{})},...opts});
    let body={}; try{body=await res.json();}catch(_){}
    if(!res.ok) throw new Error(body.error||('HTTP '+res.status));
    return body;
  }
  const fmtDate=v=>{
    if(!v)return '—'; const d=new Date(v); if(Number.isNaN(d.getTime()))return String(v);
    return d.toLocaleString(undefined,{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
  };
  const fmtFreq=hz=>{const n=Number(hz);return Number.isFinite(n)&&n>0?(n/1e6).toFixed(3)+' MHz':'—'};
  const fmtDuration=sec=>{const n=Math.max(0,Number(sec)||0);const m=Math.floor(n/60),s=Math.round(n%60);return m+'m '+String(s).padStart(2,'0')+'s';};
  const prefs=()=>{
    try{return JSON.parse(localStorage.getItem('pt2vhf_v112_satellite_prefs')||'{}')||{};}catch(_){return {};}
  };
  const savePrefs=extra=>localStorage.setItem('pt2vhf_v112_satellite_prefs',JSON.stringify({...prefs(),...extra}));
  const favoriteSet=()=>{
    try{return new Set(JSON.parse(localStorage.getItem('pt2vhf_v112_satellite_favorites')||'[]').map(Number));}catch(_){return new Set([25544]);}
  };
  const saveFavorites=set=>localStorage.setItem('pt2vhf_v112_satellite_favorites',JSON.stringify([...set]));
  const selectedSet=()=>{
    try{
      const raw=localStorage.getItem('pt2vhf_v112_satellite_selected');
      if(raw===null)return new Set([25544]);
      const a=JSON.parse(raw);
      return new Set((Array.isArray(a)?a:[]).map(Number).filter(Number.isFinite));
    }catch(_){return new Set([25544]);}
  };
  const saveSelected=set=>localStorage.setItem('pt2vhf_v112_satellite_selected',JSON.stringify([...set]));

  const state={
    initialized:false,map:null,stationMarker:null,catalog:[],status:[],passes:[],
    selected:selectedSet(),favorites:favoriteSet(),activeNorad:25544,
    layers:new Map(),mainLayers:new Map(),mainMap:null,refreshTimer:null,alertTimer:null,
    observer:null,trackBusy:new Set(),lastCatalogMeta:null,
    trackQueue:[],trackQueued:new Set(),trackPromises:new Map(),trackRequestGen:new Map(),trackActive:0,trackGeneration:new Map(),
  };

  function layerPrefs(){
    const p=prefs();
    return {
      footprint:p.footprint!==false,future:p.future!==false,past:p.past!==false,
      labels:p.labels!==false,follow:!!p.follow,favoritesOnly:!!p.favoritesOnly,
      catalogScope:['aprs','packet','all'].includes(String(p.catalogScope||''))?String(p.catalogScope):'aprs',
      horizon:Number(p.horizon||90),alerts:p.alerts!==false,alertLead:Number(p.alertLead||10),
      alertMin:Number(p.alertMin??10),passHours:Number(p.passHours||24),passMin:Number(p.passMin||0),
    };
  }
  function applyPrefControls(){
    const p=layerPrefs();
    const map={
      '#satelliteShowFootprint':p.footprint,'#satelliteShowFuture':p.future,'#satelliteShowPast':p.past,
      '#satelliteShowLabels':p.labels,'#satelliteFollowSelected':p.follow,'#satelliteFavoritesOnly':p.favoritesOnly,
      '#satelliteAlertsEnabled':p.alerts,
    };
    for(const [sel,val] of Object.entries(map)){const el=$(sel);if(el)el.checked=!!val;}
    if($('#satelliteCatalogScope'))$('#satelliteCatalogScope').value=String(p.catalogScope);
    if($('#satelliteTrackHorizon'))$('#satelliteTrackHorizon').value=String(p.horizon);
    if($('#satelliteAlertLead'))$('#satelliteAlertLead').value=String(p.alertLead);
    if($('#satelliteAlertMinElevation'))$('#satelliteAlertMinElevation').value=String(p.alertMin);
    if($('#satellitePassHours'))$('#satellitePassHours').value=String(p.passHours);
    if($('#satellitePassMinElevation'))$('#satellitePassMinElevation').value=String(p.passMin);
  }

  function waitLeaflet(){
    return new Promise(resolve=>{
      if(window.L){resolve(true);return;}
      let n=0;const id=setInterval(()=>{if(window.L){clearInterval(id);resolve(true);}else if(++n>80){clearInterval(id);resolve(false);}},100);
    });
  }
  function splitTrack(points){
    const out=[];let cur=[];let last=null;
    for(const p of points||[]){
      const lat=Number(p.latitude),lon=Number(p.longitude);
      if(!Number.isFinite(lat)||!Number.isFinite(lon))continue;
      if(last!==null&&Math.abs(lon-last)>180){if(cur.length>1)out.push(cur);cur=[];}
      cur.push([lat,lon]);last=lon;
    }
    if(cur.length>1)out.push(cur);return out;
  }
  function satelliteIcon(meta){
    const isIss=Number(meta?.norad_id)===25544;
    return L.divIcon({className:'',html:'<div class="satellite-orbit-marker '+(isIss?'iss':'')+'">🛰</div>',iconSize:[28,28],iconAnchor:[14,14]});
  }
  function stationIcon(){
    return L.divIcon({className:'',html:'<div class="satellite-station-marker"></div>',iconSize:[18,18],iconAnchor:[9,9]});
  }
  function clearLayerSet(map,container){
    for(const entry of container.values())for(const layer of entry){try{map.removeLayer(layer);}catch(_){}}
    container.clear();
  }

  async function initDedicatedMap(){
    if(state.map)return;
    if(!await waitLeaflet())return;
    state.map=L.map('satelliteMap',{preferCanvas:true,worldCopyJump:true,zoomSnap:.25}).setView([-15.8,-47.9],3);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(state.map);
  }
  function setObserverMarker(){
    if(!state.map||!state.observer)return;
    const p=[Number(state.observer.latitude),Number(state.observer.longitude)];
    if(!p.every(Number.isFinite))return;
    if(state.stationMarker)state.stationMarker.setLatLng(p);
    else state.stationMarker=L.marker(p,{icon:stationIcon(),title:tr('Minha estação','My station','Mi estación','Ma station')}).addTo(state.map);
  }

  function satelliteMeta(norad){return state.catalog.find(x=>Number(x.norad_id)===Number(norad))||{};}
  function statusFor(norad){return state.status.find(x=>Number(x.norad_id)===Number(norad))||{};}
  function freqSummary(meta){
    const up=fmtFreq(meta.uplink_hz),down=fmtFreq(meta.downlink_hz);
    return up===down?down:(tr('↑','↑','↑','↑')+up+' / '+tr('↓','↓','↓','↓')+down);
  }
  function visibleCatalogRows(){
    const p=layerPrefs();
    const query=String($('#satelliteQuickSearch')?.value||'').trim().toUpperCase().replace(/\s+/g,' ');
    return state.catalog.filter(meta=>{
      const id=Number(meta.norad_id);
      if(p.favoritesOnly&&!state.favorites.has(id))return false;
      if(!query)return true;
      const hay=[meta.name,meta.callsign,meta.designation,meta.norad_id].map(v=>String(v??'').toUpperCase().replace(/\s+/g,' ')).join(' ');
      return hay.includes(query);
    });
  }

  function updateSelectionSummary(){
    const host=$('#satelliteSelectionSummaryText');if(!host)return;
    const selected=state.selected.size;
    const favorites=state.favorites.size;
    const visible=visibleCatalogRows().length;
    host.textContent=selected+' selecionados · '+favorites+' favoritos · '+visible+' visíveis';
  }

  function renderCatalog(){
    const host=$('#satelliteCatalogList');if(!host)return;
    const p=layerPrefs();
    const rows=visibleCatalogRows();
    host.innerHTML=rows.length?rows.map(meta=>{
      const id=Number(meta.norad_id),active=state.selected.has(id),fav=state.favorites.has(id);
      const operational=String(meta.operational_state||'monitor');
      return '<div class="satellite-catalog-row '+(active?'active':'')+'" data-norad="'+id+'">'+
        '<input class="satellite-select" type="checkbox" '+(active?'checked':'')+' aria-label="'+esc(tr('Mostrar satélite','Show satellite','Mostrar satélite','Afficher satellite'))+'">'+
        '<button type="button" class="satellite-open"><span class="satellite-name">'+esc(meta.name||('NORAD '+id))+'</span><small>NORAD '+id+' · '+esc(meta.operation_type||meta.protocol||meta.mode||'digital')+' · '+esc(freqSummary(meta))+'</small>'+(active&&!meta.tle_available?'<small class="satellite-render-warning">'+esc(tr('TLE indisponível','TLE unavailable','TLE no disponible','TLE indisponible'))+'</small>':'')+'</button>'+
        '<select class="satellite-operational" title="'+esc(tr('Estado operacional','Operational state','Estado operativo','État opérationnel'))+'"><option value="monitor" '+(operational==='monitor'?'selected':'')+'>'+esc(tr('Monitorar','Monitor','Monitorear','Surveiller'))+'</option><option value="ignore" '+(operational==='ignore'?'selected':'')+'>'+esc(tr('Ignorar','Ignore','Ignorar','Ignorer'))+'</option><option value="inactive" '+(operational==='inactive'?'selected':'')+'>'+esc(tr('Fora do ar','Inactive','Fuera de servicio','Hors service'))+'</option></select>'+
        '<button type="button" class="satellite-favorite" title="'+esc(tr('Favorito','Favorite','Favorito','Favori'))+'">'+(fav?'★':'☆')+'</button></div>';
    }).join(''):'<span class="hint">'+esc(tr('Nenhum satélite para o filtro atual.','No satellites for the current filter.','No hay satélites para el filtro actual.','Aucun satellite pour ce filtre.'))+'</span>';

    $$('.satellite-catalog-row',host).forEach(row=>{
      const id=Number(row.dataset.norad);
      $('.satellite-select',row)?.addEventListener('change',ev=>{
        if(ev.target.checked){
          state.selected.add(id);saveSelected(state.selected);markSelectionGeneration(id);
          renderCatalog();updateSelectionSummary();showSatelliteImmediately(id,false);
        }else{
          state.selected.delete(id);saveSelected(state.selected);markSelectionGeneration(id);
          removeSatelliteLayers(id);
          renderCatalog();updateSelectionSummary();
        }
        window.dispatchEvent(new CustomEvent('pt2vhf:satellite-selection-changed'));
      });
      $('.satellite-open',row)?.addEventListener('click',()=>{state.activeNorad=id;state.selected.add(id);saveSelected(state.selected);markSelectionGeneration(id);renderCatalog();updateSelectionSummary();safeRenderDetail(id);showSatelliteImmediately(id,true);window.dispatchEvent(new CustomEvent('pt2vhf:satellite-selection-changed'));});
      $('.satellite-operational',row)?.addEventListener('change',async ev=>{
        ev.stopPropagation();
        try{
          const saved=await req('/api/v113/satellites/'+encodeURIComponent(id)+'/operation',{method:'POST',body:JSON.stringify({state:ev.target.value})});
          const meta=satelliteMeta(id);meta.operational_state=saved.state;meta.operational=saved.state==='monitor';
          await loadPasses();safeRenderDetail(id);window.dispatchEvent(new CustomEvent('pt2vhf:satellite-selection-changed'));
        }catch(e){console.warn(e);}
      });
      $('.satellite-favorite',row)?.addEventListener('click',()=>{
        state.favorites.has(id)?state.favorites.delete(id):state.favorites.add(id);saveFavorites(state.favorites);renderCatalog();updateSelectionSummary();renderPasses();window.dispatchEvent(new CustomEvent('pt2vhf:satellite-favorites-changed'));
      });
    });
  }

  function renderDetail(norad){
    const host=$('#satelliteDetail');if(!host)return;
    const m=satelliteMeta(norad),p=statusFor(norad);
    const epoch=m.tle_epoch||p.tle_epoch;
    const age=epoch?Math.floor((Date.now()-new Date(epoch).getTime())/86400000):null;
    const dopUp=Number(p.doppler_uplink_hz),dopDown=Number(p.doppler_downlink_hz);
    host.innerHTML='<h3>'+esc(m.name||('NORAD '+norad))+'</h3><div class="satellite-detail-grid">'+
      '<strong>NORAD</strong><span>'+esc(norad)+'</span>'+
      '<strong>'+esc(tr('Indicativo','Callsign','Indicativo','Indicatif'))+'</strong><span>'+esc(m.callsign||'—')+'</span>'+
      '<strong>'+esc(tr('Posição','Position','Posición','Position'))+'</strong><span>'+(Number.isFinite(Number(p.latitude))?Number(p.latitude).toFixed(3)+', '+Number(p.longitude).toFixed(3):'—')+'</span>'+
      '<strong>'+esc(tr('Altitude','Altitude','Altitud','Altitude'))+'</strong><span>'+(p.altitude_km??'—')+' km</span>'+
      '<strong>'+esc(tr('Velocidade orbital','Orbital speed','Velocidad orbital','Vitesse orbitale'))+'</strong><span>'+(p.speed_km_s??'—')+' km/s</span>'+
      '<strong>'+esc(tr('Azimute / elevação','Azimuth / elevation','Azimut / elevación','Azimut / élévation'))+'</strong><span>'+(p.azimuth_deg??'—')+'° / '+(p.elevation_deg??'—')+'°</span>'+
      '<strong>'+esc(tr('Distância','Range','Distancia','Distance'))+'</strong><span>'+(p.range_km??'—')+' km</span>'+
      '<strong>Footprint</strong><span>'+(p.footprint_radius_km??'—')+' km</span>'+
      '<strong>'+esc(tr('Uplink','Uplink','Uplink','Uplink'))+'</strong><span>'+esc(fmtFreq(m.uplink_hz))+(Number.isFinite(dopUp)?' · Doppler '+(dopUp>=0?'+':'')+dopUp+' Hz':'')+'</span>'+
      '<strong>'+esc(tr('Downlink','Downlink','Downlink','Downlink'))+'</strong><span>'+esc(fmtFreq(m.downlink_hz))+(Number.isFinite(dopDown)?' · Doppler '+(dopDown>=0?'+':'')+dopDown+' Hz':'')+'</span>'+
      '<strong>'+esc(tr('Tipo de operação','Operation type','Tipo de operación','Type d’opération'))+'</strong><span>'+esc(m.operation_type||'—')+(m.aprs_confirmed?' · APRS confirmado':'')+'</span>'+
      '<strong>'+esc(tr('Estado operacional','Operational state','Estado operativo','État opérationnel'))+'</strong><span>'+esc(m.operational_state||'monitor')+'</span>'+
      '<strong>'+esc(tr('Modo','Mode','Modo','Mode'))+'</strong><span>'+esc(m.mode||m.protocol||'—')+'</span>'+
      '<strong>TLE</strong><span class="'+(age!==null&&age>7?'satellite-tle-stale':'')+'">'+esc(epoch?fmtDate(epoch)+' · '+age+' d':'—')+'</span>'+
      '<strong>'+esc(tr('Fonte TLE','TLE source','Fuente TLE','Source TLE'))+'</strong><span>'+esc(m.tle_source||state.lastCatalogMeta?.tle_source||'—')+'</span>'+
      '<strong>'+esc(tr('Fonte do catálogo','Catalog source','Fuente del catálogo','Source du catalogue'))+'</strong><span>'+esc(m.source||state.lastCatalogMeta?.catalog_source||'—')+'</span>'+
      '</div>'+
      '<div class="satellite-service-controls"><strong>'+esc(tr('Serviços monitorados','Monitored services','Servicios monitorizados','Services surveillés'))+'</strong>'+
      ['aprs','sstv','telemetry','voice','packet'].map(key=>'<label><input type="checkbox" data-satellite-service="'+key+'" '+((m.service_states?.[key]??true)?'checked':'')+'><span>'+esc({aprs:'APRS',sstv:'SSTV',telemetry:'Telemetria',voice:'Voz/FM',packet:'Packet/AX.25'}[key])+'</span></label>').join('')+
      '</div>';
    host.querySelectorAll('[data-satellite-service]').forEach(input=>input.addEventListener('change',async()=>{
      const services={...(m.service_states||{})};services[input.dataset.satelliteService]=input.checked;
      try{const saved=await req('/api/v113/satellites/'+encodeURIComponent(norad)+'/operation',{method:'POST',body:JSON.stringify({state:m.operational_state||'monitor',services})});m.service_states=saved.services;await loadPasses();window.dispatchEvent(new CustomEvent('pt2vhf:satellite-selection-changed'));}catch(e){console.warn(e);}
    }));
  }

  function safeRenderDetail(norad){
    try{renderDetail(norad);return true;}
    catch(e){
      console.error('[SAT] detail render error',e);
      const host=$('#satelliteDetail');
      if(host)host.innerHTML='<div class="satellite-render-error">'+esc(tr('Erro ao renderizar detalhes do satélite','Satellite detail rendering error','Error al mostrar detalles del satélite','Erreur d’affichage des détails du satellite'))+': '+esc(e?.message||e)+'</div>';
      return false;
    }
  }

  function renderLiveStrip(norad){
    const host=$('#satelliteLiveStrip');if(!host)return;
    const m=satelliteMeta(norad),p=statusFor(norad);
    const pass=state.passes.find(x=>Number(x.norad_id)===Number(norad)&&new Date(x.los).getTime()>Date.now());
    host.innerHTML='<span><strong>'+esc(m.name||('NORAD '+norad))+'</strong></span>'+
      '<span>'+esc(tr('Elevação','Elevation','Elevación','Élévation'))+': <strong>'+(p.elevation_deg??'—')+'°</strong></span>'+
      '<span>'+esc(tr('Azimute','Azimuth','Azimut','Azimut'))+': <strong>'+(p.azimuth_deg??'—')+'°</strong></span>'+
      '<span>AOS: <strong>'+esc(pass?fmtDate(pass.aos):'—')+'</strong></span>'+
      '<span>TCA: <strong>'+esc(pass?fmtDate(pass.tca):'—')+'</strong></span>'+
      '<span>LOS: <strong>'+esc(pass?fmtDate(pass.los):'—')+'</strong></span>'+
      '<span>'+esc(tr('Frequência','Frequency','Frecuencia','Fréquence'))+': <strong>'+esc(freqSummary(m))+'</strong></span>';
  }

  function renderOneOnMap(map,container,meta,pos,trackData,isMain=false){
    const id=Number(meta.norad_id); const old=container.get(id)||[]; for(const l of old){try{map.removeLayer(l);}catch(_){}}
    const layers=[]; if(!Number.isFinite(Number(pos.latitude))||!Number.isFinite(Number(pos.longitude))){container.set(id,layers);return;}
    const p=layerPrefs(),latlng=[Number(pos.latitude),Number(pos.longitude)];
    const marker=L.marker(latlng,{icon:satelliteIcon(meta),title:meta.name||('NORAD '+id)}).addTo(map);
    if(p.labels)marker.bindTooltip(meta.name||('NORAD '+id),{permanent:false,direction:'top'});
    marker.on('click',()=>{state.activeNorad=id;safeRenderDetail(id);renderLiveStrip(id);if(!isMain)void drawSatelliteTrack(id,true);});
    layers.push(marker);

    if(p.footprint&&Number(pos.footprint_radius_km)>0){
      const circle=L.circle(latlng,{radius:Number(pos.footprint_radius_km)*1000,weight:1,opacity:.55,fillOpacity:.08,interactive:false}).addTo(map);layers.push(circle);
    }
    if(trackData?.points?.length){
      const now=Date.now(),past=[],future=[];
      for(const point of trackData.points){(new Date(point.time).getTime()<=now?past:future).push(point);}
      if(p.past)for(const seg of splitTrack(past)){layers.push(L.polyline(seg,{weight:2,opacity:.45,dashArray:'4 6',interactive:false}).addTo(map));}
      if(p.future)for(const seg of splitTrack(future)){layers.push(L.polyline(seg,{weight:2,opacity:.82,interactive:false}).addTo(map));}
    }
    container.set(id,layers);
    if(!isMain&&p.follow&&id===state.activeNorad)map.panTo(latlng,{animate:true});
  }

  function hasPosition(pos){
    return Number.isFinite(Number(pos?.latitude))&&Number.isFinite(Number(pos?.longitude));
  }
  function markSelectionGeneration(norad){
    const id=Number(norad);state.trackGeneration.set(id,(state.trackGeneration.get(id)||0)+1);return state.trackGeneration.get(id);
  }
  function removeSatelliteLayers(norad){
    const id=Number(norad);
    for(const [map,container] of [[state.map,state.layers],[state.mainMap,state.mainLayers]]){
      if(!map||!container.has(id))continue;
      for(const layer of container.get(id)||[]){try{map.removeLayer(layer);}catch(_){}}
      container.delete(id);
    }
    state.trackQueue=state.trackQueue.filter(x=>x.id!==id);state.trackQueued.delete(id);
  }
  function setSatelliteRenderStatus(norad,text,error=false){
    const host=$('#satelliteLiveStrip');if(!host||Number(norad)!==Number(state.activeNorad))return;
    host.innerHTML='<span class="'+(error?'satellite-render-error':'hint')+'">'+esc(text)+'</span>';
  }
  function renderCachedPosition(norad,center=false){
    const id=Number(norad),meta=satelliteMeta(id),pos=statusFor(id);
    if(!state.map||!state.selected.has(id)||!meta.norad_id||!hasPosition(pos))return false;
    renderOneOnMap(state.map,state.layers,meta,pos,null,false);
    if(center)state.map.setView([Number(pos.latitude),Number(pos.longitude)],Math.max(state.map.getZoom(),4));
    if(id===state.activeNorad){safeRenderDetail(id);renderLiveStrip(id);}
    return true;
  }
  async function fetchAndRenderTrack(norad,center=false,generation=null){
    const id=Number(norad),meta=satelliteMeta(id);if(!state.map||!meta.norad_id)return;
    const started=performance.now(),gen=generation??state.trackGeneration.get(id)??0;
    if(state.trackPromises.has(id)){
      const existing=state.trackPromises.get(id),existingGen=state.trackRequestGen.get(id);
      if(existingGen===gen)return existing;
      try{await existing;}catch(_){}
      if(!state.selected.has(id)||gen!==(state.trackGeneration.get(id)??0))return;
    }
    const task=(async()=>{
      try{
        const p=layerPrefs();
        const data=await req('/api/v112/satellites/'+encodeURIComponent(id)+'/track?past=30&future='+encodeURIComponent(p.horizon)+'&step=60');
        if(!state.selected.has(id)||gen!==(state.trackGeneration.get(id)??0))return;
        const current=data.current||statusFor(id);
        if(!hasPosition(current))throw new Error(tr('Posição orbital indisponível','Orbital position unavailable','Posición orbital no disponible','Position orbitale indisponible'));
        renderOneOnMap(state.map,state.layers,meta,current,data,false);
        if(center)state.map.setView([Number(current.latitude),Number(current.longitude)],Math.max(state.map.getZoom(),4));
        if(id===state.activeNorad){safeRenderDetail(id);renderLiveStrip(id);}
        console.debug('[SAT] selection→track',id,Math.round(performance.now()-started)+'ms');
      }catch(e){
        if(state.selected.has(id)&&gen===(state.trackGeneration.get(id)??0)){
          const fallback=renderCachedPosition(id,center);
          if(!fallback)setSatelliteRenderStatus(id,(meta.tle_available===false?tr('TLE indisponível','TLE unavailable','TLE no disponible','TLE indisponible'):tr('Erro ao calcular órbita','Orbital calculation error','Error al calcular órbita','Erreur de calcul orbital'))+': '+e.message,true);
        }
      }finally{
        if(state.trackPromises.get(id)===task){state.trackPromises.delete(id);state.trackRequestGen.delete(id);}
        state.trackBusy.delete(id);
      }
    })();
    state.trackPromises.set(id,task);state.trackRequestGen.set(id,gen);state.trackBusy.add(id);return task;
  }
  function pumpTrackQueue(){
    while(state.trackActive<4&&state.trackQueue.length){
      const job=state.trackQueue.shift();state.trackQueued.delete(job.id);
      if(!state.selected.has(job.id))continue;
      state.trackActive++;
      void fetchAndRenderTrack(job.id,job.center,job.generation).finally(()=>{state.trackActive--;pumpTrackQueue();});
    }
  }
  function enqueueTrack(norad,center=false){
    const id=Number(norad),generation=state.trackGeneration.get(id)??0;
    if(!state.selected.has(id)||state.trackQueued.has(id))return;
    if(state.trackPromises.has(id)&&state.trackRequestGen.get(id)===generation)return;
    state.trackQueued.add(id);state.trackQueue.push({id,center,generation});pumpTrackQueue();
  }
  function showSatelliteImmediately(norad,center=false){
    const id=Number(norad);if(!state.selected.has(id))return;
    const rendered=renderCachedPosition(id,center);
    if(!rendered)setSatelliteRenderStatus(id,tr('Carregando posição…','Loading position…','Cargando posición…','Chargement position…'));
    enqueueTrack(id,center);
  }
  async function drawSatelliteTrack(norad,center=false){showSatelliteImmediately(norad,center);}
  async function refreshOrbitalMaps(){
    if(state.map){
      const keep=new Set(state.selected);
      for(const id of [...state.layers.keys()])if(!keep.has(id))removeSatelliteLayers(id);
      for(const id of keep)showSatelliteImmediately(id,false);
    }
    void refreshMainMap();
  }

  async function refreshMainMap(){
    const map=window.pt2vhfMainMap||window.map;if(!map)return;
    state.mainMap=map;
    const enabled=localStorage.getItem('pt2vhf_map_item_satellites')!=='0';
    if(!enabled){clearLayerSet(map,state.mainLayers);return;}
    const p=layerPrefs(); const keep=new Set(state.selected);
    for(const id of [...state.mainLayers.keys()])if(!keep.has(id)){for(const l of state.mainLayers.get(id)||[]){try{map.removeLayer(l);}catch(_){}}state.mainLayers.delete(id);}
    for(const id of keep){
      const meta=satelliteMeta(id),pos=statusFor(id);if(!hasPosition(pos))continue;
      try{
        const data=await req('/api/v112/satellites/'+encodeURIComponent(id)+'/track?past=0&future='+Math.min(90,p.horizon)+'&step=90');
        renderOneOnMap(map,state.mainLayers,meta,data.current||pos,data,true);
      }catch(_){renderOneOnMap(map,state.mainLayers,meta,pos,null,true);}
    }
  }

  function renderPasses(){
    const body=$('#satellitePassTable tbody');if(!body)return;
    const p=layerPrefs();
    const rows=state.passes.filter(x=>{
      const id=Number(x.norad_id);
      return (!p.favoritesOnly||state.favorites.has(id));
    });
    body.innerHTML=rows.length?rows.map(x=>'<tr data-norad="'+esc(x.norad_id)+'">'+
      '<td><strong>'+esc(x.name||('NORAD '+x.norad_id))+'</strong><br><small>'+esc(x.callsign||'')+'</small></td>'+
      '<td>'+esc(fmtDate(x.aos))+'</td><td>'+esc(fmtDate(x.tca))+'</td><td>'+esc(fmtDate(x.los))+'</td>'+
      '<td>'+esc(x.max_elevation_deg)+'°</td><td>'+esc(x.aos_azimuth_deg)+'° / '+esc(x.tca_azimuth_deg)+'° / '+esc(x.los_azimuth_deg)+'°</td>'+
      '<td>'+esc(fmtDuration(x.duration_seconds))+'</td><td>'+esc(freqSummary(x))+'<br><small>'+esc(x.mode||x.protocol||'')+'</small></td></tr>').join(''):
      '<tr><td colspan="8" class="hint">'+esc(tr('Nenhuma passagem no filtro atual.','No passes in the current filter.','No hay pases en el filtro actual.','Aucun passage avec ce filtre.'))+'</td></tr>';
    $$('tr[data-norad]',body).forEach(row=>row.addEventListener('click',()=>{
      const id=Number(row.dataset.norad);state.activeNorad=id;state.selected.add(id);saveSelected(state.selected);markSelectionGeneration(id);renderCatalog();safeRenderDetail(id);renderLiveStrip(id);showSatelliteImmediately(id,true);
    }));
  }

  async function loadPasses(){
    const p=layerPrefs();
    try{
      const data=await req('/api/v112/satellites/passes?hours='+encodeURIComponent(p.passHours)+'&min_elevation='+encodeURIComponent(p.passMin)+'&scope='+encodeURIComponent(p.catalogScope));
      state.passes=data.items||[];state.observer=data.observer||state.observer;setObserverMarker();renderPasses();checkPassAlerts();
    }catch(e){const body=$('#satellitePassTable tbody');if(body)body.innerHTML='<tr><td colspan="8" class="hint">'+esc(e.message)+'</td></tr>';}
  }

  async function loadStatus(){
    try{
      const data=await req('/api/v112/satellites/status?scope='+encodeURIComponent(layerPrefs().catalogScope));
      state.status=data.items||[];state.observer=data.observer||state.observer;setObserverMarker();
      if(state.activeNorad)safeRenderDetail(state.activeNorad);
      await refreshOrbitalMaps();
    }catch(e){console.warn(e);}
  }

  function catalogStatusText(meta){
    if(!meta.updated_at)return tr('Dados orbitais ainda não baixados.','Orbital data not downloaded yet.','Datos orbitales aún no descargados.','Données orbitales pas encore téléchargées.');
    const errors=(meta.errors||[]).filter(Boolean);
    return tr('Atualizado','Updated','Actualizado','Mis à jour')+' '+fmtDate(meta.updated_at)+(errors.length?' · '+errors.join(' | '):'');
  }
  async function loadCatalog(autoUpdate=true){
    const host=$('#satelliteDataStatus');
    try{
      let data=await req('/api/v112/satellites/catalog?scope='+encodeURIComponent(layerPrefs().catalogScope));
      if(autoUpdate&&(!data.updated_at||!(data.catalog||[]).some(x=>x.tle_available))){
        if(host)host.textContent=tr('Baixando TLE e catálogo…','Downloading TLE and catalog…','Descargando TLE y catálogo…','Téléchargement TLE et catalogue…');
        await req('/api/v112/satellites/update?scope='+encodeURIComponent(layerPrefs().catalogScope),{method:'POST',body:'{}'});
        data=await req('/api/v112/satellites/catalog?scope='+encodeURIComponent(layerPrefs().catalogScope));
      }
      state.catalog=data.catalog||[];state.lastCatalogMeta=data;
      if(!state.catalog.some(x=>Number(x.norad_id)===state.activeNorad))state.activeNorad=Number(state.catalog[0]?.norad_id||25544);
      if(host){host.textContent=catalogStatusText(data);host.classList.toggle('error',!!(data.errors||[]).length);}
      renderCatalog();updateSelectionSummary();window.dispatchEvent(new CustomEvent('pt2vhf:satellite-catalog-loaded',{detail:{catalog:state.catalog}}));await refreshOrbitalMaps();await loadStatus();await loadPasses();
    }catch(e){if(host){host.textContent=e.message;host.classList.add('error');}}
  }

  async function manualUpdate(){
    const b=$('#satelliteRefreshButton');if(b){b.disabled=true;b.textContent=tr('Atualizando…','Updating…','Actualizando…','Mise à jour…');}
    try{await req('/api/v112/satellites/update',{method:'POST',body:'{}'});await loadCatalog(false);}
    catch(e){const h=$('#satelliteDataStatus');if(h){h.textContent=e.message;h.classList.add('error');}}
    finally{if(b){b.disabled=false;b.textContent='Atualizar TLE / catálogo';}}
  }

  function notifiedSet(){
    try{return new Set(JSON.parse(localStorage.getItem('pt2vhf_v112_pass_notified')||'[]'));}catch(_){return new Set();}
  }
  function saveNotified(set){
    const arr=[...set].slice(-200);localStorage.setItem('pt2vhf_v112_pass_notified',JSON.stringify(arr));
  }
  async function pushNotification(pass){
    try{await req('/api/v111/notifications',{method:'POST',body:JSON.stringify({
      category:'satellite',title:(pass.name||('NORAD '+pass.norad_id))+' · '+tr('passagem próxima','upcoming pass','próximo pase','passage proche'),
      detail:'AOS '+fmtDate(pass.aos)+' · '+pass.max_elevation_deg+'° · '+freqSummary(pass),severity:'info',entity:String(pass.norad_id)
    })});}catch(_){}
  }
  function showPassAlert(pass){
    let overlay=$('#v112SatelliteAlert');
    if(!overlay){
      overlay=document.createElement('div');overlay.id='v112SatelliteAlert';overlay.className='satellite-alert-overlay hidden';document.body.appendChild(overlay);
    }
    overlay.innerHTML='<div class="satellite-alert-card"><small>'+esc(tr('Alerta de passagem APRS/packet','APRS/packet pass alert','Alerta de pase APRS/packet','Alerte de passage APRS/packet'))+'</small>'+
      '<h3>'+esc(pass.name||('NORAD '+pass.norad_id))+'</h3><div class="satellite-detail-grid">'+
      '<strong>AOS</strong><span>'+esc(fmtDate(pass.aos))+'</span><strong>TCA</strong><span>'+esc(fmtDate(pass.tca))+'</span><strong>LOS</strong><span>'+esc(fmtDate(pass.los))+'</span>'+
      '<strong>'+esc(tr('Elevação máxima','Maximum elevation','Elevación máxima','Élévation maximale'))+'</strong><span>'+esc(pass.max_elevation_deg)+'°</span>'+
      '<strong>'+esc(tr('Uplink','Uplink','Uplink','Uplink'))+'</strong><span>'+esc(fmtFreq(pass.uplink_hz))+'</span>'+
      '<strong>'+esc(tr('Downlink','Downlink','Downlink','Downlink'))+'</strong><span>'+esc(fmtFreq(pass.downlink_hz))+'</span>'+
      '<strong>'+esc(tr('Modo','Mode','Modo','Mode'))+'</strong><span>'+esc(pass.mode||pass.protocol||'—')+'</span></div>'+
      '<div class="satellite-alert-actions"><button class="btn secondary" data-action="favorite">'+esc(tr('Favoritar','Favorite','Favorito','Favori'))+'</button><button class="btn primary" data-action="open">'+esc(tr('Abrir Satélites','Open Satellites','Abrir Satélites','Ouvrir Satellites'))+'</button><button class="btn secondary" data-action="close">'+esc(tr('Fechar','Close','Cerrar','Fermer'))+'</button></div></div>';
    overlay.classList.remove('hidden');
    $('[data-action="close"]',overlay).onclick=()=>overlay.classList.add('hidden');
    $('[data-action="open"]',overlay).onclick=()=>{overlay.classList.add('hidden');document.querySelector('[data-tab="satellites"]')?.click();state.activeNorad=Number(pass.norad_id);void drawSatelliteTrack(state.activeNorad,true);};
    $('[data-action="favorite"]',overlay).onclick=()=>{state.favorites.add(Number(pass.norad_id));saveFavorites(state.favorites);renderCatalog();};
  }
  function checkPassAlerts(){
    const p=layerPrefs();if(!p.alerts)return;
    const now=Date.now(),lead=p.alertLead*60000,seen=notifiedSet();
    for(const pass of state.passes){
      const aos=new Date(pass.aos).getTime(),key=String(pass.norad_id)+'|'+String(pass.aos);
      if(!Number.isFinite(aos)||seen.has(key)||Number(pass.max_elevation_deg)<p.alertMin)continue;
      if(aos>=now&&aos-now<=lead){
        seen.add(key);showPassAlert(pass);void pushNotification(pass);
      }
    }
    saveNotified(seen);
  }

  function bindPrefs(){
    const bindings=[
      ['#satelliteShowFootprint','footprint','checked'],['#satelliteShowFuture','future','checked'],['#satelliteShowPast','past','checked'],
      ['#satelliteShowLabels','labels','checked'],['#satelliteFollowSelected','follow','checked'],['#satelliteFavoritesOnly','favoritesOnly','checked'],
      ['#satelliteAlertsEnabled','alerts','checked'],['#satelliteCatalogScope','catalogScope','value'],['#satelliteTrackHorizon','horizon','value'],['#satelliteAlertLead','alertLead','value'],
      ['#satelliteAlertMinElevation','alertMin','value'],['#satellitePassHours','passHours','value'],['#satellitePassMinElevation','passMin','value'],
    ];
    for(const [sel,key,prop] of bindings){
      const el=$(sel);if(!el)continue;
      el.addEventListener('change',()=>{
        const raw=el[prop];const value=prop==='checked'?!!raw:(['horizon','alertLead','alertMin','passHours','passMin'].includes(key)?Number(raw):raw);
        savePrefs({[key]:value});
        if(key==='favoritesOnly')renderCatalog();
        if(key==='catalogScope')void loadCatalog(false);
        if(['passHours','passMin'].includes(key))void loadPasses();
        if(['footprint','future','past','labels','horizon'].includes(key))void refreshOrbitalMaps();
      });
    }
    $('#satellitePassRefresh')?.addEventListener('click',loadPasses);
    $('#satelliteRefreshButton')?.addEventListener('click',manualUpdate);
    $('#satelliteSelectAll')?.addEventListener('click',()=>{
      const rows=visibleCatalogRows();
      for(const meta of rows){const id=Number(meta.norad_id);state.selected.add(id);markSelectionGeneration(id);}
      saveSelected(state.selected);renderCatalog();updateSelectionSummary();
      for(const meta of rows)showSatelliteImmediately(Number(meta.norad_id),false);
      window.dispatchEvent(new CustomEvent('pt2vhf:satellite-selection-changed'));
    });
    $('#satelliteClearAll')?.addEventListener('click',()=>{
      for(const meta of visibleCatalogRows()){const id=Number(meta.norad_id);state.selected.delete(id);markSelectionGeneration(id);removeSatelliteLayers(id);}
      saveSelected(state.selected);renderCatalog();updateSelectionSummary();window.dispatchEvent(new CustomEvent('pt2vhf:satellite-selection-changed'));
    });
    $('#satelliteResetDefaults')?.addEventListener('click',()=>{
      for(const id of [...state.selected]){state.selected.delete(id);markSelectionGeneration(id);removeSatelliteLayers(id);}
      state.selected.add(25544);markSelectionGeneration(25544);saveSelected(state.selected);
      state.activeNorad=25544;renderCatalog();updateSelectionSummary();showSatelliteImmediately(25544,true);
      window.dispatchEvent(new CustomEvent('pt2vhf:satellite-selection-changed'));
    });
    $('#satelliteQuickSearch')?.addEventListener('input',()=>{renderCatalog();updateSelectionSummary();});
    $('#satelliteQuickSearchClear')?.addEventListener('click',()=>{const q=$('#satelliteQuickSearch');if(q){q.value='';q.focus();}renderCatalog();updateSelectionSummary();});
  }

  function installLayoutReset(){
    const config=$('#tab-config');if(!config||$('#v112ResetFloatingLayout'))return;
    const btn=document.createElement('button');btn.id='v112ResetFloatingLayout';btn.type='button';btn.className='btn secondary';btn.textContent=tr('Restaurar layout das janelas','Reset window layout','Restaurar diseño de ventanas','Réinitialiser les fenêtres');
    btn.addEventListener('click',()=>{for(const id of ['tab-messages','tab-stations','tab-log'])document.getElementById(id)?._pt2vhfResetFloatGeometry?.();});
    const card=$('#v190ConfigCard')||config.querySelector('.config-card');card?.appendChild(btn);
  }

  async function init(){
    if(state.initialized)return;state.initialized=true;applyPrefControls();bindPrefs();installLayoutReset();
    await initDedicatedMap();
    const workspace=document.querySelector('.satellite-workspace');
    if(workspace && typeof ResizeObserver!=='undefined' && !window.__pt2vhfSatResizeObserver){
      window.__pt2vhfSatResizeObserver=new ResizeObserver(()=>requestAnimationFrame(()=>state.map?.invalidateSize({animate:false})));
      window.__pt2vhfSatResizeObserver.observe(workspace);
    }
    for(const id of state.selected)showSatelliteImmediately(id,false);await loadCatalog(true);
    state.refreshTimer=setInterval(()=>{if(document.querySelector('.tab.active[data-tab="satellites"]'))void loadStatus();else if(localStorage.getItem('pt2vhf_map_item_satellites')!=='0')void loadStatus();},30000);
    state.alertTimer=setInterval(()=>{if(state.passes.length)checkPassAlerts();else void loadPasses();},60000);
  }

  document.addEventListener('click',e=>{
    if(e.target.closest?.('.tab[data-tab="satellites"]'))setTimeout(()=>{void init();setTimeout(()=>state.map?.invalidateSize({animate:false}),80);},0);
  });
  window.addEventListener('pt2vhf:main-map-ready',()=>{state.mainMap=window.pt2vhfMainMap||window.map;void refreshMainMap();});
  window.addEventListener('pt2vhf:satellite-visibility',()=>void refreshMainMap());
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{
    installLayoutReset();
    if(document.querySelector('.tab.active[data-tab="satellites"]'))void init();
  });else{installLayoutReset();if(document.querySelector('.tab.active[data-tab="satellites"]'))void init();}
})();
