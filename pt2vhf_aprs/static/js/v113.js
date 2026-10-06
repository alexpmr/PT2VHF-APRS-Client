(()=>{
  'use strict';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  async function req(url,opts={}){
    const res=await fetch(url,{headers:{'Content-Type':'application/json',...(opts.headers||{})},...opts});
    let body={};try{body=await res.json();}catch(_){}
    if(!res.ok)throw new Error(body.error||('HTTP '+res.status));return body;
  }
  const storeKey='pt2vhf_v113_satellite_alarm';
  const alarmPrefs=()=>{try{return {...{enabled:true,lead:10,minElevation:10},...JSON.parse(localStorage.getItem(storeKey)||'{}')}}catch(_){return {enabled:true,lead:10,minElevation:10}}};
  const saveAlarm=p=>localStorage.setItem(storeKey,JSON.stringify({...alarmPrefs(),...p}));
  const notifiedKey='pt2vhf_v113_alarm_notified';
  const silencedKey='pt2vhf_v113_alarm_silenced';
  const setFrom=(key)=>{try{return new Set(JSON.parse(localStorage.getItem(key)||'[]'))}catch(_){return new Set()}};
  const saveSet=(key,set)=>localStorage.setItem(key,JSON.stringify([...set].slice(-300)));
  let nextPass=null,lastFetch=0,countdownTimer=null,refreshTimer=null,audioCtx=null;

  function formatHms(ms){
    const total=Math.max(0,Math.floor(ms/1000));
    const h=Math.floor(total/3600),m=Math.floor((total%3600)/60),s=total%60;
    return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
  }
  function passKey(p){return String(p?.norad_id||'')+'|'+String(p?.aos||'');}
  function ensureNameNode(){
    const c=$('#satelliteTabCountdown');if(!c)return null;
    let n=$('#satelliteTabNextName');if(!n){n=document.createElement('span');n.id='satelliteTabNextName';n.className='satellite-tab-next-name';c.insertAdjacentElement('afterend',n);}return n;
  }
  function countdownPhase(ms,active){
    if(active)return 'active';
    if(ms<=5*60000)return 'imminent';
    if(ms<=30*60000)return 'approaching';
    return 'normal';
  }
  function renderCountdown(){
    const el=$('#satelliteTabCountdown'),name=ensureNameNode(),label=$('#satelliteCountdownLabel');if(!el)return;
    if(!nextPass){
      el.textContent='--:--:--';el.dataset.phase='idle';el.title='Nenhuma passagem APRS prevista';
      if(name)name.textContent='Nenhuma passagem APRS prevista';
      if(label)label.textContent='Próxima passagem';
      return;
    }
    const now=Date.now(),aos=Date.parse(nextPass.aos||''),los=Date.parse(nextPass.los||'');
    const active=Number.isFinite(aos)&&Number.isFinite(los)&&aos<=now&&now<=los;
    const remaining=active?los-now:aos-now;
    if(!Number.isFinite(remaining)||remaining<0){void refreshNextPass(true);return;}
    el.textContent=formatHms(remaining);el.dataset.phase=countdownPhase(remaining,active);
    const callsign=String(nextPass.callsign||'').trim(),satName=String(nextPass.name||('NORAD '+nextPass.norad_id)).trim();
    const sat=callsign&&callsign.toUpperCase()!==satName.toUpperCase()?satName+' / '+callsign:(callsign||satName);
    el.title=(active?'Passagem APRS ativa — tempo até LOS: ':'Próxima passagem APRS — tempo até AOS: ')+sat;
    if(name)name.textContent=active?sat+' — EM PASSAGEM':sat;
    if(label)label.textContent=active?'LOS em':'Próxima passagem em';
    checkCoverageAlarm(remaining,active);
  }
  function countdownEligibleNorads(){
    const ids=new Set();
    try{for(const x of JSON.parse(localStorage.getItem('pt2vhf_v112_satellite_selected')||'[]'))ids.add(Number(x));}catch(_){}
    try{for(const x of JSON.parse(localStorage.getItem('pt2vhf_v112_satellite_favorites')||'[]'))ids.add(Number(x));}catch(_){}
    return [...ids].filter(Number.isFinite);
  }
  async function refreshNextPass(force=false){
    if(!force&&Date.now()-lastFetch<120000)return;
    lastFetch=Date.now();
    try{
      const p=alarmPrefs();
      const norads=countdownEligibleNorads();
      if(!norads.length){nextPass=null;renderCountdown();return;}
      const data=await req('/api/v114/satellites/next-pass?min_elevation='+encodeURIComponent(p.minElevation||0)+'&norads='+encodeURIComponent(norads.join(',')));
      nextPass=data.pass||null;renderCountdown();
    }catch(_){nextPass=null;renderCountdown();}
  }
  function beep(){
    try{
      audioCtx=audioCtx||new (window.AudioContext||window.webkitAudioContext)();
      const now=audioCtx.currentTime;
      [0,0.24,0.48].forEach((offset,i)=>{
        const o=audioCtx.createOscillator(),g=audioCtx.createGain();
        o.type='sine';o.frequency.value=i===1?1040:880;g.gain.setValueAtTime(.0001,now+offset);
        g.gain.exponentialRampToValueAtTime(.18,now+offset+.02);g.gain.exponentialRampToValueAtTime(.0001,now+offset+.17);
        o.connect(g);g.connect(audioCtx.destination);o.start(now+offset);o.stop(now+offset+.2);
      });
    }catch(_){}
  }
  function fmtDate(v){const d=new Date(v);return Number.isNaN(d.getTime())?'—':d.toLocaleString();}
  function fmtFreq(v){const n=Number(v);return Number.isFinite(n)&&n>0?(n/1e6).toFixed(3)+' MHz':'—';}
  function favorite(norad){
    try{const key='pt2vhf_v112_satellite_favorites';const set=new Set(JSON.parse(localStorage.getItem(key)||'[]').map(Number));set.add(Number(norad));localStorage.setItem(key,JSON.stringify([...set]));}catch(_){}
  }
  function showAlarm(p,remaining){
    let overlay=$('#v113SatelliteAlarm');if(!overlay){overlay=document.createElement('div');overlay.id='v113SatelliteAlarm';overlay.className='v113-alarm-overlay hidden';document.body.appendChild(overlay);}
    overlay.innerHTML='<div class="v113-alarm-card"><small>DESPERTADOR APRS — aproximação da cobertura</small><h3>'+esc(p.name||('NORAD '+p.norad_id))+'</h3>'+
      '<div class="v113-alarm-countdown">'+esc(formatHms(remaining))+'</div>'+
      '<div class="satellite-detail-grid"><strong>Indicativo</strong><span>'+esc(p.callsign||'—')+'</span><strong>AOS</strong><span>'+esc(fmtDate(p.aos))+'</span>'+
      '<strong>Elevação máxima</strong><span>'+esc(p.max_elevation_deg??'—')+'°</span><strong>Duração</strong><span>'+esc(Math.round(Number(p.duration_seconds||0)/60))+' min</span>'+
      '<strong>Uplink</strong><span>'+esc(fmtFreq(p.uplink_hz))+'</span><strong>Downlink</strong><span>'+esc(fmtFreq(p.downlink_hz))+'</span>'+
      '<strong>Modo APRS</strong><span>'+esc(p.mode||p.protocol||'APRS')+'</span></div>'+
      '<div class="v113-alarm-actions"><button class="btn secondary" data-a="fav">Favoritar</button><button class="btn secondary" data-a="silence">Silenciar esta passagem</button><button class="btn primary" data-a="open">Abrir / seguir satélite</button><button class="btn secondary" data-a="close">Fechar</button></div></div>';
    overlay.classList.remove('hidden');
    $('[data-a="close"]',overlay).onclick=()=>overlay.classList.add('hidden');
    $('[data-a="fav"]',overlay).onclick=()=>favorite(p.norad_id);
    $('[data-a="silence"]',overlay).onclick=()=>{const set=setFrom(silencedKey);set.add(passKey(p));saveSet(silencedKey,set);overlay.classList.add('hidden');};
    $('[data-a="open"]',overlay).onclick=()=>{overlay.classList.add('hidden');document.querySelector('[data-tab="satellites"]')?.click();setTimeout(()=>{const row=document.querySelector('.satellite-catalog-row[data-norad="'+CSS.escape(String(p.norad_id))+'"] .satellite-open');row?.click();const follow=$('#satelliteFollowSelected');if(follow&&!follow.checked){follow.checked=true;follow.dispatchEvent(new Event('change',{bubbles:true}));}},120);};
  }
  function checkCoverageAlarm(remaining,active){
    if(active||!nextPass)return;
    const pref=alarmPrefs();if(!pref.enabled)return;
    const lead=Math.max(1,Number(pref.lead||10))*60000,key=passKey(nextPass);
    if(remaining>lead||remaining<0)return;
    const notified=setFrom(notifiedKey),silenced=setFrom(silencedKey);
    if(notified.has(key)||silenced.has(key))return;
    notified.add(key);saveSet(notifiedKey,notified);beep();showAlarm(nextPass,remaining);
    req('/api/v111/notifications',{method:'POST',body:JSON.stringify({category:'satellite_alarm',severity:'info',entity:String(nextPass.norad_id||''),title:(nextPass.name||'Satélite APRS')+' se aproxima da cobertura',detail:'AOS '+fmtDate(nextPass.aos)+' · '+String(nextPass.max_elevation_deg||'—')+'° · '+fmtFreq(nextPass.downlink_hz)})}).catch(()=>{});
  }

  function bindAlarmControls(){
    const p=alarmPrefs(),enabled=$('#satelliteCoverageAlarmEnabled'),lead=$('#satelliteCoverageAlarmLead'),min=$('#satelliteAlertMinElevation');
    if(enabled)enabled.checked=!!p.enabled;if(lead)lead.value=String(p.lead||10);if(min&&Number.isFinite(Number(p.minElevation)))min.value=String(p.minElevation);
    enabled?.addEventListener('change',()=>saveAlarm({enabled:enabled.checked}));
    lead?.addEventListener('change',()=>saveAlarm({lead:Number(lead.value||10)}));
    min?.addEventListener('change',()=>{saveAlarm({minElevation:Number(min.value||0)});void refreshNextPass(true);});
  }

  async function loadSources(){
    const host=$('#satelliteSourcesList');if(!host)return;
    try{
      const data=await req('/api/v113/satellites/settings'),settings=data.settings||{},runtime=data.runtime||{};
      const en=$('#satelliteAutoUpdateEnabled'),time=$('#satelliteUpdateTime');
      if(en)en.checked=settings.auto_update_enabled!==false;
      if(time)time.value=String(settings.update_hour??0).padStart(2,'0')+':'+String(settings.update_minute??0).padStart(2,'0');
      host.innerHTML=(settings.sources||[]).map(src=>{
        const run=runtime[src.id]||{},cls=src.enabled===false?'off':(run.ok?'good':(run.error?'bad':''));
        const status=src.enabled===false?'Desativada':(run.ok?((run.count||0)+' TLE'):run.error||'Ainda não testada');
        return '<div class="satellite-source-row" data-source="'+esc(src.id)+'"><input class="source-enabled" type="checkbox" '+(src.enabled!==false?'checked':'')+'>'+
          '<div><strong>'+esc(src.label||src.id)+'</strong><small>'+esc(src.url||'')+'</small><small class="satellite-source-state '+cls+'">'+esc(status)+'</small></div>'+
          '<input class="source-priority" type="number" min="1" max="999" value="'+esc(src.priority||100)+'" title="Prioridade">'+
          '<button type="button" class="btn secondary source-test">Testar</button></div>';
      }).join('');
      $$('.source-test',host).forEach(btn=>btn.addEventListener('click',async()=>{
        const row=btn.closest('.satellite-source-row'),sid=row?.dataset.source;if(!sid)return;btn.disabled=true;
        try{const st=await req('/api/v113/satellites/source-test',{method:'POST',body:JSON.stringify({id:sid})});$('.satellite-source-state',row).textContent=(st.count||0)+' TLE · '+Math.round(st.elapsed_ms||0)+' ms';$('.satellite-source-state',row).className='satellite-source-state good';}
        catch(e){$('.satellite-source-state',row).textContent=e.message;$('.satellite-source-state',row).className='satellite-source-state bad';}
        finally{btn.disabled=false;}
      }));
    }catch(e){host.innerHTML='<span class="hint">'+esc(e.message)+'</span>';}
  }
  async function saveSources(){
    const rows=$$('.satellite-source-row'),time=String($('#satelliteUpdateTime')?.value||'00:00').split(':');
    const payload={auto_update_enabled:!!$('#satelliteAutoUpdateEnabled')?.checked,update_hour:Number(time[0]||0),update_minute:Number(time[1]||0),
      sources:rows.map(row=>({id:row.dataset.source,enabled:!!$('.source-enabled',row)?.checked,priority:Number($('.source-priority',row)?.value||100)}))};
    try{await req('/api/v113/satellites/settings',{method:'POST',body:JSON.stringify(payload)});await loadSources();}
    catch(e){alert(e.message);}
  }
  async function updateSources(){
    const b=$('#satelliteUpdateAllSources');if(b)b.disabled=true;
    try{await req('/api/v113/satellites/update',{method:'POST',body:'{}'});await loadSources();document.querySelector('#satelliteRefreshButton')?.click();void refreshNextPass(true);}
    catch(e){alert(e.message);}finally{if(b)b.disabled=false;}
  }
  function bindSources(){
    $('#satelliteSaveSources')?.addEventListener('click',saveSources);
    $('#satelliteUpdateAllSources')?.addEventListener('click',updateSources);
    void loadSources();
  }

  function boot(){
    bindAlarmControls();bindSources();void refreshNextPass(true);
    countdownTimer=setInterval(renderCountdown,1000);
    refreshTimer=setInterval(()=>void refreshNextPass(true),120000);
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)void refreshNextPass(true);});
    window.addEventListener('pt2vhf:satellite-selection-changed',()=>void refreshNextPass(true));
    window.addEventListener('pt2vhf:satellite-favorites-changed',()=>void refreshNextPass(true));
    window.addEventListener('pt2vhf:satellite-catalog-loaded',()=>void refreshNextPass(true));
    document.addEventListener('click',e=>{if(e.target.closest?.('[data-tab="satellites"]')){void refreshNextPass(true);void loadSources();}});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
