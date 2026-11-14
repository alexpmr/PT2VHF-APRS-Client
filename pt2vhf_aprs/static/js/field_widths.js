// v2.0.2: na Configuração, cada campo fica com a largura do conteúdo que ele aceita
// (indicativo com 6 letras não ocupa mais a coluna inteira). A largura sai dos próprios
// limites do campo: maxlength, min/max/step ou placeholder. Os cartões que
// outros módulos criam depois (TNC, integrações, retenção) são ajustados pelo observer.
(() => {
'use strict';

const SKIP_TYPES = new Set(['checkbox', 'radio', 'range', 'color', 'hidden', 'file', 'button', 'submit', 'reset', 'image']);
const MIN_CH = 8;
const MAX_CH = 60;
const FREE_TEXT_CH = 36;

const clamp = n => Math.max(MIN_CH, Math.min(MAX_CH, Math.ceil(n)));
const textLength = value => String(value ?? '').length;

function decimals(step) {
  const text = String(step || '');
  if (!text || text === 'any') return 0;
  const dot = text.indexOf('.');
  return dot < 0 ? 0 : text.length - dot - 1;
}

function numberWidth(input) {
  const min = input.getAttribute('min');
  const max = input.getAttribute('max');
  const places = decimals(input.getAttribute('step'));
  let digits = Math.max(textLength(min), textLength(max), textLength(input.placeholder) - 4, 3);
  if (min === null && max === null) digits = Math.max(digits, 6);
  // Dígitos + casas decimais + setas do campo numérico e respiro.
  return clamp(digits + (places ? places + 1 : 0) + 4);
}

function textWidth(input) {
  const limit = Number(input.getAttribute('maxlength'));
  if (Number.isFinite(limit) && limit > 0 && limit <= MAX_CH) {
    return clamp(Math.max(limit, Math.min(textLength(input.placeholder), limit)) + 3);
  }
  return clamp(Math.max(textLength(input.placeholder) + 3, FREE_TEXT_CH));
}

function widthFor(el) {
  if (el.tagName === 'SELECT') return 'auto';
  const type = String(el.type || 'text').toLowerCase();
  if (type === 'number') return numberWidth(el) + 'ch';
  return textWidth(el) + 'ch';
}

function shouldSize(el) {
  if (!(el instanceof HTMLElement) || el.dataset.width === 'full') return false;
  if (el.closest('.coordinate-dms-group, .range-field-row, .ssid-help-modal, .modal, [data-width="full"]')) return false;
  if (el.tagName === 'SELECT') return !el.multiple;
  if (el.tagName !== 'INPUT') return false;
  return !SKIP_TYPES.has(String(el.type || 'text').toLowerCase());
}

function sizeField(el) {
  if (!shouldSize(el)) return;
  const width = widthFor(el);
  if (el.dataset.fieldWidth === width) return;
  el.dataset.fieldWidth = width;
  el.style.width = width === 'auto' ? 'auto' : `min(100%, ${width})`;
  el.style.maxWidth = '100%';
  el.style.alignSelf = 'flex-start';
  el.style.justifySelf = 'start';
}

function sizeAll(root) {
  const host = root || document.getElementById('tab-config');
  if (!host) return;
  host.querySelectorAll('input, select').forEach(sizeField);
}

function start() {
  const host = document.getElementById('tab-config');
  if (!host) return;
  sizeAll(host);
  let pending = false;
  new MutationObserver(() => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; sizeAll(host); });
  }).observe(host, { childList: true, subtree: true });
}

window.pt2vhfFieldWidths = { widthFor, sizeAll };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
else start();
})();
