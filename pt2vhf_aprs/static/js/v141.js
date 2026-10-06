(()=>{
'use strict';
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const key=id=>'pt2vhf_v141_sat_panel_'+id;
function restorePanels(){
  $$('[data-sat-collapsible]').forEach(panel=>{
    const id=panel.dataset.satCollapsible;
    const saved=localStorage.getItem(key(id));
    panel.open=saved==='1';
    panel.addEventListener('toggle',()=>{
      localStorage.setItem(key(id),panel.open?'1':'0');
      if(panel.open&&document.querySelector('.tab.active[data-tab="satellites"]')){
        setTimeout(()=>window.dispatchEvent(new Event('resize')),60);
      }
    });
  });
}
function boot(){
  restorePanels();
  document.addEventListener('click',e=>{
    if(e.target.closest?.('.tab[data-tab="satellites"]')){
      setTimeout(()=>window.dispatchEvent(new Event('resize')),120);
    }
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();