// v1.15.1: aba Configuração em sub-abas, no formato do PT2VHF Mesh Analyzer (uma seção por vez).
// Os cartões de outros módulos (v110, v111, v190, TNC) entram depois do carregamento; um
// MutationObserver os distribui nas sub-abas assim que aparecem.
(() => {
'use strict';

const $ = (s, r = document) => r.querySelector(s);
const lang = () => String(document.documentElement.lang || localStorage.getItem('pt2vhf_language') || 'pt-BR').toLowerCase();
const tr = (pt, en, es, fr) => {
  const consolidated = window.pt2vhfI18n.lookup(pt);
  if (consolidated !== undefined) return consolidated;
  const l = lang();
  const locale = l.startsWith('de') ? 'de-DE' : l.startsWith('it') ? 'it-IT' : l.startsWith('ja') ? 'ja-JP'
    : l.startsWith('pl') ? 'pl-PL' : l.startsWith('nl') ? 'nl-NL' : l.startsWith('zh') ? 'zh-CN' : '';
  const extended = locale ? window.PT2VHF_I18N?.[locale]?.[pt] : '';
  if (extended) return extended;
  return l.startsWith('pt') ? pt : l.startsWith('es') ? (es || en) : l.startsWith('fr') ? (fr || en) : en;
};
const STORAGE_KEY = 'pt2vhf_config_subtab';
const TABS = [
  ['station', () => tr('Estação', 'Station', 'Estación', 'Station')],
  ['aprsis', () => 'APRS-IS'],
  ['tnc', () => 'TNC / RF'],
  ['map', () => tr('Mapa', 'Map', 'Mapa', 'Carte')],
  ['app', () => tr('Aplicativo', 'Application', 'Aplicación', 'Application')],
  ['integrations', () => tr('Integrações', 'Integrations', 'Integraciones', 'Intégrations')],
  ['database', () => tr('Banco de dados', 'Database', 'Base de datos', 'Base de données')],
  ['backup', () => tr('Backup', 'Backup', 'Copia de seguridad', 'Sauvegarde')],
];
const FORM_TABS = new Set(['station', 'aprsis', 'map', 'app', 'database', 'backup']);
const BY_ID = {tncConfigBlock: 'tnc', v110ExternalConfig: 'integrations', v111DbHealth: 'database',
  retentionSettingsCard: 'database', v190ConfigCard: 'backup'};
let current = null;

function tabOf(el) {
  if (!(el instanceof HTMLElement)) return null;
  if (el.classList.contains('panel-header') || el.classList.contains('config-subtabs')
      || el.classList.contains('config-save-footer') || el.id === 'configForm' || el.tagName === 'SCRIPT') return null;
  return el.dataset.configTab || BY_ID[el.id] || 'app';
}
function cards() {
  const host = $('#tab-config'), form = $('#configForm');
  if (!host) return [];
  return [...host.children, ...(form ? [...form.children] : [])].filter(el => tabOf(el));
}
function apply() {
  for (const el of cards()) {
    const key = tabOf(el);
    if (!el.dataset.configTab) el.dataset.configTab = key;
    el.classList.toggle('config-subtab-hidden', key !== current);
  }
  const footer = $('#configForm .config-save-footer');
  if (footer) footer.classList.toggle('config-subtab-hidden', !FORM_TABS.has(current));
  const form = $('#configForm');
  if (form) form.classList.toggle('config-subtab-hidden', !FORM_TABS.has(current));
  const tnc = $('#tncConfigBlock');
  if (tnc) {
    tnc.classList.add('as-subtab');
    const open = current === 'tnc';
    if (tnc.open !== open) tnc.open = open;         // dispara o "toggle" que atualiza os dados do TNC
  }
  document.querySelectorAll('#configSubtabs [data-config-subtab]').forEach(btn => {
    const on = btn.dataset.configSubtab === current;
    btn.classList.toggle('active', on);
    btn.setAttribute('aria-selected', String(on));
    btn.tabIndex = on ? 0 : -1;
  });
}
function show(key, {remember = true} = {}) {
  if (!TABS.some(([k]) => k === key)) key = 'station';
  current = key;
  if (remember) { try { localStorage.setItem(STORAGE_KEY, key); } catch (e) {} }
  apply();
}
function label() {
  document.querySelectorAll('#configSubtabs [data-config-subtab]').forEach(btn => {
    const t = TABS.find(([k]) => k === btn.dataset.configSubtab); if (t) btn.textContent = t[1]();
  });
  $('#configSubtabs')?.setAttribute('aria-label', tr('Seções da configuração', 'Settings sections', 'Secciones de la configuración', 'Sections de la configuration'));
}
function mount() {
  const host = $('#tab-config');
  if (!host || $('#configSubtabs')) return;
  const bar = document.createElement('div');
  bar.id = 'configSubtabs'; bar.className = 'config-subtabs'; bar.setAttribute('role', 'tablist');
  bar.innerHTML = TABS.map(([k]) => '<button type="button" role="tab" class="config-subtab" data-config-subtab="' + k + '"></button>').join('');
  const header = host.querySelector(':scope > .panel-header');
  if (header) header.after(bar); else host.prepend(bar);
  label();
  bar.addEventListener('click', e => { const b = e.target.closest('[data-config-subtab]'); if (b) show(b.dataset.configSubtab); });
  bar.addEventListener('keydown', e => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const i = TABS.findIndex(([k]) => k === current), n = TABS.length;
    const next = TABS[(i + (e.key === 'ArrowRight' ? 1 : n - 1)) % n][0];
    show(next); bar.querySelector('[data-config-subtab="' + next + '"]')?.focus();
  });
  let saved = null;
  try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
  show(saved || 'station', {remember: false});
  // Cartões que outros módulos acrescentam depois entram na sub-aba certa.
  const observer = new MutationObserver(() => apply());
  observer.observe(host, {childList: true});
  if ($('#configForm')) observer.observe($('#configForm'), {childList: true});
  // Campo obrigatório numa sub-aba escondida: mostrar a sub-aba para o navegador poder apontar o erro.
  $('#configForm')?.addEventListener('invalid', e => {
    const card = cards().find(el => el.contains(e.target));
    if (card && card.dataset.configTab !== current) show(card.dataset.configTab);
  }, true);
  new MutationObserver(label).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
}
// Leva até um elemento da Configuração (ex.: campo obrigatório), abrindo a sub-aba dele.
function reveal(el) {
  const card = el && cards().find(c => c.contains(el));
  if (card) show(card.dataset.configTab || tabOf(card));
}
window.pt2vhfConfigTabs = {show, reveal, current: () => current};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
