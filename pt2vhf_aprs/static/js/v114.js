(()=>{
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function req(url,opts={}){const res=await fetch(url,{headers:{'Content-Type':'application/json',...(opts.headers||{})},...opts});let body={};try{body=await res.json();}catch(_){}if(!res.ok)throw new Error(body.error||('HTTP '+res.status));return body;}
function idsFrom(key){try{return new Set(JSON.parse(localStorage.getItem(key)||'[]').map(Number).filter(Number.isFinite));}catch(_){return new Set();}}
function eligibleNorads(){const s=idsFrom('pt2vhf_v112_satellite_selected'),f=idsFrom('pt2vhf_v112_satellite_favorites');for(const x of f)s.add(x);return [...s];}
let selectedStation='',catalog=[],lastStationCalls=new Set(),poll=null;

function initSelectionPanel(){
 const p=$('#satelliteSelectionPanel');if(!p)return;
 p.open=localStorage.getItem('pt2vhf_v114_sat_selection_open')==='1';
 p.addEventListener('toggle',()=>localStorage.setItem('pt2vhf_v114_sat_selection_open',p.open?'1':'0'));
}
function fmtAgo(v){if(!v)return '—';const t=Date.parse(v);if(!Number.isFinite(t))return v;const s=Math.max(0,Math.floor((Date.now()-t)/1000));if(s<60)return s+' s';if(s<3600)return Math.floor(s/60)+' min';return Math.floor(s/3600)+' h';}
function satNames(row){return (row.satellites||[]).map(x=>x.callsign||x.name).filter(Boolean).join(', ')||'—';}
async function loadStations(){
 const ids=eligibleNorads(),hours=$('#satelliteStationsHours')?.value||'6',rf=$('#satelliteStationsRfOnly')?.checked?'1':'0',msg=$('#satelliteStationsMessagesOnly')?.checked?'1':'0';
 const host=$('#satelliteStationsList');if(!host)return;
 try{
  const data=await req('/api/v114/satellites/stations?norads='+encodeURIComponent(ids.join(','))+'&hours='+hours+'&rf_only='+rf+'&messages_only='+msg);
  const rows=data.items||[];
  const nowCalls=new Set(rows.map(x=>String(x.callsign||'')));
  let fresh=0;for(const c of nowCalls)if(lastStationCalls.size&&!lastStationCalls.has(c))fresh++;
  lastStationCalls=nowCalls;
  const badge=$('#satelliteNewStationsBadge');if(badge){badge.textContent=fresh+' novas';badge.classList.toggle('hidden',fresh===0);}
  host.innerHTML=rows.length?rows.map(r=>'<button type="button" class="satellite-station-row'+(r.context_match?' context':'')+'" data-call="'+esc(r.callsign)+'"><span><strong>'+esc(r.callsign)+'</strong><small>'+esc(r.name||'')+'</small></span><span>'+esc(r.medium||'')+' · '+Number(r.packet_count||0)+' pkt</span><span>'+esc(satNames(r))+'</span><span>'+esc(fmtAgo(r.last_heard))+'</span></button>').join(''):'<span class="hint">Nenhuma estação no filtro atual.</span>';
  $$('.satellite-station-row',host).forEach(btn=>btn.addEventListener('click',()=>selectStation(btn.dataset.call,rows.find(x=>String(x.callsign)===btn.dataset.call))));
 }catch(e){host.innerHTML='<span class="hint">'+esc(e.message)+'</span>';}
}
async function selectStation(call,row){
 selectedStation=String(call||'').toUpperCase();const to=$('#satelliteMessageTo');if(to)to.value=selectedStation;
 const d=$('#satelliteStationDetail');if(d){d.classList.remove('hidden');d.innerHTML='<strong>'+esc(selectedStation)+'</strong><span>Última recepção: '+esc(fmtAgo(row?.last_heard))+'</span><span>Meio: '+esc(row?.medium||'—')+'</span><span>Satélite: '+esc(satNames(row||{}))+'</span><span>Distância: '+esc(row?.distance_km??'—')+' km</span>';}
 await loadConversation();
}
async function loadConversation(){
 const host=$('#satelliteConversation');if(!host)return;
 const call=String($('#satelliteMessageTo')?.value||selectedStation).toUpperCase().trim();
 if(!call){host.innerHTML='<span class="hint">Selecione uma estação.</span>';return;}
 try{
  const rows=await req('/api/messages?mine=1');
  const conv=(rows||[]).filter(m=>String(m.from_call||'').toUpperCase()===call||String(m.to_call||'').toUpperCase()===call).slice(0,40).reverse();
  host.innerHTML=conv.length?conv.map(m=>'<div class="satellite-msg '+(m.direction==='out'?'out':'in')+'"><small>'+esc(m.direction==='out'?'TX':'RX')+' · '+esc(m.status||'')+'</small><span>'+esc(m.message||'')+'</span></div>').join(''):'<span class="hint">Sem mensagens recentes.</span>';
  host.scrollTop=host.scrollHeight;
 }catch(e){host.innerHTML='<span class="hint">'+esc(e.message)+'</span>';}
}
async function sendMessage(){
 const to=String($('#satelliteMessageTo')?.value||'').toUpperCase().trim(),text=String($('#satelliteMessageText')?.value||'').trim(),route=$('#satelliteMessageRoute')?.value||'auto',path=String($('#satelliteMessagePath')?.value||'').trim(),st=$('#satelliteMessageStatus');
 if(!to||!text){if(st)st.textContent='Informe destinatário e mensagem.';return;}
 try{if(st)st.textContent='Enviando…';await req('/api/messages/send',{method:'POST',body:JSON.stringify({type:'message',to,message:text,route,path})});$('#satelliteMessageText').value='';if(st)st.textContent='Mensagem enfileirada.';selectedStation=to;await loadConversation();}
 catch(e){if(st)st.textContent=e.message;}
}
async function loadPassContext(){
 const host=$('#satellitePassContext');if(!host)return;const ids=eligibleNorads();if(!ids.length){host.textContent='Nenhum satélite selecionado/favorito.';return;}
 try{const d=await req('/api/v114/satellites/next-pass?norads='+encodeURIComponent(ids.join(',')));const p=d.pass;if(!p){host.textContent='Sem passagem APRS calculada.';return;}host.textContent=(p.name||p.callsign||'Satélite')+' · '+(p.phase==='active'?'EM PASSAGEM':'próximo AOS')+' · '+new Date(p.aos).toLocaleTimeString()+' · '+(p.max_elevation_deg??'—')+'° · '+((Number(p.downlink_hz)||Number(p.uplink_hz))?(Number(p.downlink_hz||p.uplink_hz)/1e6).toFixed(3)+' MHz':'freq. n/d');}catch(e){host.textContent=e.message;}
}
function populateBeaconSatellites(){
 const sel=$('#satelliteBeaconSatellite');if(!sel)return;const ids=new Set(eligibleNorads());const rows=catalog.filter(x=>ids.has(Number(x.norad_id)));sel.innerHTML=rows.map(x=>'<option value="'+Number(x.norad_id)+'">'+esc(x.name||('NORAD '+x.norad_id))+'</option>').join('');if(rows.length)loadBeaconProfile();
}
function beaconPayload(){return {path:$('#satelliteBeaconPath')?.value||'',comment:$('#satelliteBeaconComment')?.value||'SAT',interval_seconds:Number($('#satelliteBeaconInterval')?.value||60),min_elevation_deg:Number($('#satelliteBeaconMinElevation')?.value||5),coverage_only:!!$('#satelliteBeaconCoverageOnly')?.checked,stop_at_los:!!$('#satelliteBeaconStopLos')?.checked,enabled:!!$('#satelliteBeaconEnabled')?.checked,tx_consent:!!$('#satelliteBeaconConsent')?.checked};}
async function loadBeaconProfile(){
 const id=Number($('#satelliteBeaconSatellite')?.value||0);if(!id)return;
 try{const d=await req('/api/v114/satellites/'+id+'/beacon'),p=d.profile||{};$('#satelliteBeaconPath').value=p.path||'';$('#satelliteBeaconComment').value=p.comment||'SAT';$('#satelliteBeaconInterval').value=String(p.interval_seconds||60);$('#satelliteBeaconMinElevation').value=String(p.min_elevation_deg??5);$('#satelliteBeaconCoverageOnly').checked=!!p.coverage_only;$('#satelliteBeaconStopLos').checked=!!p.stop_at_los;$('#satelliteBeaconEnabled').checked=!!p.enabled;$('#satelliteBeaconConsent').checked=!!p.tx_consent;renderBeaconPreview(d);}catch(e){$('#satelliteBeaconPreview').textContent=e.message;}
}
function renderBeaconPreview(d){const h=$('#satelliteBeaconPreview');if(!h)return;h.innerHTML='<code>'+esc(d.raw||'')+'</code><span>'+Number(d.frame_size_bytes||0)+' bytes</span>'+(d.warning?'<strong>'+esc(d.warning)+'</strong>':'');}
async function previewBeacon(){const id=Number($('#satelliteBeaconSatellite')?.value||0);if(!id)return;try{renderBeaconPreview(await req('/api/v114/satellites/'+id+'/beacon/preview',{method:'POST',body:JSON.stringify(beaconPayload())}));}catch(e){$('#satelliteBeaconPreview').textContent=e.message;}}
async function saveBeacon(){const id=Number($('#satelliteBeaconSatellite')?.value||0);if(!id)return;try{const d=await req('/api/v114/satellites/'+id+'/beacon',{method:'POST',body:JSON.stringify(beaconPayload())});renderBeaconPreview(d);}catch(e){alert(e.message);}}
async function sendBeacon(){const id=Number($('#satelliteBeaconSatellite')?.value||0);if(!id)return;try{await saveBeacon();await req('/api/v114/satellites/'+id+'/beacon/send',{method:'POST',body:'{}'});await updateBeaconCount();}catch(e){alert(e.message);}}
async function updateBeaconCount(){try{const rows=await req('/api/v114/satellites/beacon/history?limit=500');const n=(rows||[]).filter(x=>x.status==='queued').length;const h=$('#satelliteBeaconTxCount');if(h)h.textContent=n+' enviados';}catch(_){}}
function bind(){
 initSelectionPanel();
 $('#satelliteStationsRefresh')?.addEventListener('click',loadStations);
 ['satelliteStationsHours','satelliteStationsRfOnly','satelliteStationsMessagesOnly'].forEach(id=>$('#'+id)?.addEventListener('change',loadStations));
 $('#satelliteMessageSend')?.addEventListener('click',sendMessage);
 $('#satelliteMessageTo')?.addEventListener('change',loadConversation);
 $('#satelliteMessageText')?.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();void sendMessage();}});
 $('#satelliteMessageRoute')?.addEventListener('change',()=>document.querySelector('.satellite-message-path')?.classList.toggle('hidden',$('#satelliteMessageRoute').value!=='rf_custom'));
 $('#satelliteBeaconSatellite')?.addEventListener('change',loadBeaconProfile);
 ['satelliteBeaconPath','satelliteBeaconComment','satelliteBeaconInterval','satelliteBeaconMinElevation','satelliteBeaconCoverageOnly','satelliteBeaconStopLos','satelliteBeaconEnabled','satelliteBeaconConsent'].forEach(id=>$('#'+id)?.addEventListener('change',previewBeacon));
 $('#satelliteBeaconSave')?.addEventListener('click',saveBeacon);$('#satelliteBeaconSendNow')?.addEventListener('click',sendBeacon);
 window.addEventListener('pt2vhf:satellite-catalog-loaded',e=>{catalog=e.detail?.catalog||[];populateBeaconSatellites();void loadStations();void loadPassContext();});
 window.addEventListener('pt2vhf:satellite-selection-changed',()=>{populateBeaconSatellites();void loadStations();void loadPassContext();});
 window.addEventListener('pt2vhf:satellite-favorites-changed',()=>{populateBeaconSatellites();void loadStations();void loadPassContext();});
 document.addEventListener('click',e=>{if(e.target.closest?.('[data-tab="satellites"]'))setTimeout(()=>{void loadStations();void loadConversation();void loadPassContext();void updateBeaconCount();},80);});
 poll=setInterval(()=>{if(document.querySelector('.tab.active[data-tab="satellites"]')){void loadStations();if(selectedStation)void loadConversation();void loadPassContext();}},15000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind);else bind();
window.addEventListener('beforeunload',()=>{if(poll)clearInterval(poll);});
})();