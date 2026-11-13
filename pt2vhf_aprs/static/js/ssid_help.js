// Sugestões de SSID (recomendações WB4APR, "APRS SSID Recommendations", 6 fev 2012).
// Aparece ao abrir Configuração → Estação (uma vez por sessão, até o usuário marcar
// "Não mostrar novamente") e pelo botão ao lado do campo SSID. Clicar numa linha preenche o SSID.
(() => {
'use strict';

const $ = (s, r = document) => r.querySelector(s);
const lang = () => String(document.documentElement.lang || localStorage.getItem('pt2vhf_language') || 'pt-BR').toLowerCase();
const tr = (pt, en, es) => {
  const l = lang();
  return l.startsWith('pt') ? pt : l.startsWith('es') ? (es || en) : en;
};
const HIDE_KEY = 'pt2vhf_ssid_help_hidden';
let shownThisSession = false;

// [ssid, português, inglês, espanhol]
const SSIDS = [
  [0, 'Estação principal, normalmente fixa e capaz de trocar mensagens', 'Your primary station, usually fixed and message capable', 'Estación principal, normalmente fija y con mensajería'],
  [1, 'Estação adicional genérica: digipeater, móvel, meteorológica etc.', 'Generic additional station: digi, mobile, wx, etc.', 'Estación adicional genérica: digi, móvil, meteo, etc.'],
  [2, 'Estação adicional genérica: digipeater, móvel, meteorológica etc.', 'Generic additional station: digi, mobile, wx, etc.', 'Estación adicional genérica: digi, móvil, meteo, etc.'],
  [3, 'Estação adicional genérica: digipeater, móvel, meteorológica etc.', 'Generic additional station: digi, mobile, wx, etc.', 'Estación adicional genérica: digi, móvil, meteo, etc.'],
  [4, 'Estação adicional genérica: digipeater, móvel, meteorológica etc.', 'Generic additional station: digi, mobile, wx, etc.', 'Estación adicional genérica: digi, móvil, meteo, etc.'],
  [5, 'Outras redes (D-Star, iPhone, Android, BlackBerry etc.)', 'Other networks (D-Star, iPhones, Androids, BlackBerrys, etc.)', 'Otras redes (D-Star, iPhone, Android, BlackBerry, etc.)'],
  [6, 'Atividade especial: operação via satélite, acampamento, 6 metros etc.', 'Special activity: satellite ops, camping, 6 meters, etc.', 'Actividad especial: satélite, campamento, 6 metros, etc.'],
  [7, 'Rádios portáteis (HT) ou outros equipamentos carregados pela pessoa', 'Walkie-talkies, HTs or other human portable', 'Portátiles (HT) u otros equipos que lleva la persona'],
  [8, 'Barcos, veleiros, motorhomes ou segundo móvel principal', 'Boats, sailboats, RVs or second main mobile', 'Barcos, veleros, autocaravanas o segundo móvil principal'],
  [9, 'Móvel principal (normalmente capaz de trocar mensagens)', 'Primary mobile (usually message capable)', 'Móvil principal (normalmente con mensajería)'],
  [10, 'Internet, iGates, EchoLink, Winlink, AVRS, APRN etc.', 'Internet, iGates, EchoLink, Winlink, AVRS, APRN, etc.', 'Internet, iGates, EchoLink, Winlink, AVRS, APRN, etc.'],
  [11, 'Balões, aeronaves, espaçonaves etc.', 'Balloons, aircraft, spacecraft, etc.', 'Globos, aeronaves, naves espaciales, etc.'],
  [12, 'APRStt, DTMF, RFID, dispositivos, rastreadores só de transmissão* etc.', 'APRStt, DTMF, RFID, devices, one-way trackers*, etc.', 'APRStt, DTMF, RFID, dispositivos, rastreadores solo TX*, etc.'],
  [13, 'Estações meteorológicas', 'Weather stations', 'Estaciones meteorológicas'],
  [14, 'Caminhoneiros ou motoristas em tempo integral', 'Truckers or generally full time drivers', 'Camioneros o conductores a tiempo completo'],
  [15, 'Estação adicional genérica: digipeater, móvel, meteorológica etc.', 'Generic additional station: digi, mobile, wx, etc.', 'Estación adicional genérica: digi, móvil, meteo, etc.'],
];

function esc(s) { return String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c])); }
function ssidInput() { return $('#configForm [name="ssid"]'); }
function hidden() { try { return localStorage.getItem(HIDE_KEY) === '1'; } catch (e) { return false; } }

function render() {
  const modal = $('#ssidHelpModal');
  const current = Number(ssidInput()?.value || 0);
  const rows = SSIDS.map(([n, pt, en, es]) =>
    '<button type="button" class="ssid-help-row' + (n === current ? ' current' : '') + '" data-ssid="' + n + '">'
    + '<span class="ssid-help-num">-' + n + '</span><span>' + esc(tr(pt, en, es)) + '</span></button>').join('');
  modal.innerHTML = '<div class="modal-card ssid-help-card">'
    + '<div class="modal-header"><div><h3 id="ssidHelpTitle">' + esc(tr('Sugestões de SSID', 'SSID suggestions', 'Sugerencias de SSID')) + '</h3>'
    + '<p>' + esc(tr('Recomendações de WB4APR (criador do APRS) para indicar o tipo de estação só pelo indicativo. Clique numa linha para usar o SSID.',
      'WB4APR (APRS author) recommendations to hint the station type from the callsign alone. Click a row to use that SSID.',
      'Recomendaciones de WB4APR (autor de APRS) para indicar el tipo de estación solo por el indicativo. Haga clic en una fila para usar ese SSID.')) + '</p></div>'
    + '<button type="button" class="icon-button" data-ssid-help-close aria-label="' + esc(tr('Fechar', 'Close', 'Cerrar')) + '">×</button></div>'
    + '<div class="ssid-help-body">'
    + '<div class="ssid-help-list">' + rows + '</div>'
    + '<div class="ssid-help-notes">'
    + '<p>' + esc(tr('O SSID 0 normalmente não aparece: PY2ABC é o mesmo que PY2ABC-0.',
      'SSID 0 is usually not displayed: PY2ABC is the same as PY2ABC-0.',
      'El SSID 0 normalmente no se muestra: PY2ABC es lo mismo que PY2ABC-0.')) + '</p>'
    + '<p>' + esc(tr('* Rastreadores que só transmitem devem preferir o -12, porque o -9 costuma indicar um radioamador com comunicação completa, que pode ser chamado por mensagem APRS ou por voz.',
      '* One-way trackers should prefer -12, because -9 usually means a ham in full two-way contact, reachable by APRS message or voice.',
      '* Los rastreadores que solo transmiten deben preferir -12, porque -9 suele indicar un radioaficionado con comunicación completa, localizable por mensaje APRS o voz.')) + '</p>'
    + '<p>' + esc(tr('Os SSIDs -1 a -4 e -15 são genéricos para quem tem várias estações do mesmo tipo (até 6 digipeaters, rastreadores, estações meteorológicas ou veículos). Use o -6 em atividades especiais (satélite, ISS, 6 m, expedições) para que o histórico e as estatísticas fiquem separados da operação normal.',
      'SSIDs -1 to -4 and -15 are generic, for anyone with several stations of the same kind (up to 6 digis, trackers, weather stations or vehicles). Use -6 for special activities (satellite, ISS, 6 m, outings) so tracks and statistics stay separate from normal operation.',
      'Los SSID -1 a -4 y -15 son genéricos, para quien tiene varias estaciones del mismo tipo (hasta 6 digis, rastreadores, meteo o vehículos). Use -6 en actividades especiales (satélite, ISS, 6 m, salidas) para separar el historial y las estadísticas de la operación normal.')) + '</p>'
    + '<p>' + esc(tr('Objetos e estações geradas pela internet podem usar outros sufixos, como -63 (PSK63), -tt (APRStt/DTMF), -ID (RFID) e -A a -Z (D-Star). São só sugestões, não uma regra.',
      'Objects and internet-generated stations can use other suffixes, such as -63 (PSK63), -tt (APRStt/DTMF), -ID (RFID) and -A to -Z (D-Star). These are guidelines, not a rule.',
      'Los objetos y las estaciones generadas por internet pueden usar otros sufijos, como -63 (PSK63), -tt (APRStt/DTMF), -ID (RFID) y -A a -Z (D-Star). Son sugerencias, no una regla.')) + '</p>'
    + '</div></div>'
    + '<div class="ssid-help-footer">'
    + '<label class="ssid-help-dontshow"><input type="checkbox" data-ssid-help-hide' + (hidden() ? ' checked' : '') + '> '
    + esc(tr('Não mostrar automaticamente', 'Do not show automatically', 'No mostrar automáticamente')) + '</label>'
    + '<button type="button" class="btn secondary" data-ssid-help-close>' + esc(tr('Fechar', 'Close', 'Cerrar')) + '</button>'
    + '</div></div>';
}

function ensureModal() {
  let modal = $('#ssidHelpModal');
  if (modal) return modal;
  modal = document.createElement('div');
  modal.id = 'ssidHelpModal';
  modal.className = 'modal hidden';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-labelledby', 'ssidHelpTitle');
  document.body.appendChild(modal);
  modal.addEventListener('click', e => {
    if (e.target === modal || e.target.closest('[data-ssid-help-close]')) { close(); return; }
    const row = e.target.closest('[data-ssid]');
    if (row) {
      const input = ssidInput();
      if (input) {
        input.value = row.dataset.ssid;
        input.dispatchEvent(new Event('input', {bubbles: true}));
        input.dispatchEvent(new Event('change', {bubbles: true}));
      }
      close();
      input?.focus();
    }
  });
  modal.addEventListener('change', e => {
    if (!e.target.matches('[data-ssid-help-hide]')) return;
    try { localStorage.setItem(HIDE_KEY, e.target.checked ? '1' : '0'); } catch (err) {}
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !modal.classList.contains('hidden')) close(); });
  return modal;
}

function open() {
  const modal = ensureModal();
  render();
  modal.classList.remove('hidden');
  shownThisSession = true;
  modal.querySelector('.ssid-help-row.current')?.focus();
}
function close() { $('#ssidHelpModal')?.classList.add('hidden'); }

// Abre sozinho só quando a sub-aba Estação está visível. Se outro aviso estiver aberto
// (ex.: "Feito por radioamadores" ou novidades da versão), espera ele ser fechado.
let autoTimer = null;
function otherDialogOpen() {
  return [...document.querySelectorAll('[role="dialog"][aria-modal="true"]')]
    .some(el => el.id !== 'ssidHelpModal' && !el.classList.contains('hidden') && el.getClientRects().length);
}
function maybeAutoOpen(delay = 150, tries = 90) {
  if (shownThisSession || hidden()) return;
  clearTimeout(autoTimer);
  autoTimer = setTimeout(() => {
    if (shownThisSession || hidden()) return;
    if (!$('#tab-config')?.classList.contains('active')) return;
    if (window.pt2vhfConfigTabs?.current?.() !== 'station') return;
    if (otherDialogOpen()) { if (tries > 0) maybeAutoOpen(1000, tries - 1); return; }
    open();
  }, delay);
}

function addButton() {
  const input = ssidInput();
  if (!input || $('#ssidHelpButton')) return;
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.id = 'ssidHelpButton';
  btn.className = 'ssid-help-button';
  const label = () => {
    btn.textContent = tr('Sugestões de SSID', 'SSID suggestions', 'Sugerencias de SSID');
  };
  label();
  new MutationObserver(label).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
  btn.addEventListener('click', open);
  input.closest('label')?.appendChild(btn);
}

function mount() {
  addButton();
  document.addEventListener('click', e => {
    if (e.target.closest('.tab[data-tab="config"], #configSubtabs [data-config-subtab="station"]')) maybeAutoOpen();
  });
  // Primeira abertura sem indicativo: o app já começa na Configuração; espera os avisos iniciais.
  maybeAutoOpen(2500);
}
window.pt2vhfSsidHelp = {open, close};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
