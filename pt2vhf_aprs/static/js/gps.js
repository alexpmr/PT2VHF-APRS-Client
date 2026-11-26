/* v2.0.7: GPS e SmartBeaconing (Configuração → Estação). Mostra a situação do GPS ao vivo. */
(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const t = (pt, vars) => (window.pt2vhfT ? window.pt2vhfT(pt, vars) : pt);
  let timer = null;

  function sourceChanged() {
    const gpsd = $('#gpsSource')?.value === 'gpsd';
    document.querySelectorAll('#gpsConfigCard .gps-serial-field').forEach(el => el.classList.toggle('hidden', gpsd));
    document.querySelectorAll('#gpsConfigCard .gps-gpsd-field').forEach(el => el.classList.toggle('hidden', !gpsd));
  }

  function render(data = {}) {
    const out = $('#gpsStatusLine');
    if (!out) return;
    const fix = data.fix || {};
    let text;
    let tone = '';
    switch (data.state) {
      case 'off': text = t('GPS desligado.'); break;
      case 'connecting': text = t('Conectando ao GPS…'); break;
      case 'error': text = `${t('Erro no GPS:')} ${t(data.error || '')}`; tone = 'error'; break;
      case 'no_fix': text = t('GPS conectado, aguardando posição (céu aberto ajuda).'); tone = 'warn'; break;
      case 'fix':
        if (fix.fresh) {
          const parts = [`${Number(fix.latitude).toFixed(5)}, ${Number(fix.longitude).toFixed(5)}`];
          if (fix.speed_kmh != null) parts.push(`${Math.round(fix.speed_kmh)} km/h`);
          if (fix.course != null) parts.push(`${Math.round(fix.course)}°`);
          if (fix.altitude_m != null) parts.push(`${Math.round(fix.altitude_m)} m`);
          if (fix.satellites != null) parts.push(t('{n} satélites', { n: fix.satellites }));
          text = `${t('Posição do GPS:')} ${parts.join(' · ')}`;
          tone = 'ok';
        } else {
          text = t('GPS conectado, aguardando posição (céu aberto ajuda).');
          tone = 'warn';
        }
        break;
      default: text = '';
    }
    out.textContent = text;
    out.dataset.tone = tone;
  }

  async function poll() {
    try {
      const response = await fetch('/api/gps/status');
      if (response.ok) render(await response.json());
    } catch (_) { /* servidor reiniciando */ }
  }

  async function loadPorts() {
    try {
      const response = await fetch('/api/tnc/ports?quick=1');
      const data = await response.json();
      const list = $('#gpsSerialPorts');
      if (!list) return;
      list.innerHTML = '';
      for (const port of data.ports || []) {
        const opt = document.createElement('option');
        opt.value = port.device;
        opt.label = port.description ? `${port.device} — ${port.description}` : port.device;
        list.appendChild(opt);
      }
    } catch (_) { /* sem lista, digita a porta */ }
  }

  function visible() {
    const card = $('#gpsConfigCard');
    return !!card && card.offsetParent !== null && !document.hidden;
  }

  function init() {
    if (!$('#gpsConfigCard')) return;
    $('#gpsSource')?.addEventListener('change', sourceChanged);
    $('#gpsSerialPort')?.addEventListener('focus', loadPorts, { once: true });
    // A Configuração preenche o formulário depois de carregar; reaplica a visibilidade.
    document.addEventListener('pt2vhf-config-loaded', sourceChanged);
    setTimeout(sourceChanged, 1500);
    sourceChanged();
    timer = setInterval(() => { if (visible()) void poll(); }, 3000);
    void poll();
    window.addEventListener('beforeunload', () => clearInterval(timer));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
