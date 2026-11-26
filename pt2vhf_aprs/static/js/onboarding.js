/* v2.0.7: assistente de primeiro uso. Aparece numa instalação nova (sem indicativo), depois do
 * aviso de abertura: indicativo/SSID → posição → servidor APRS-IS → salva e conecta. */
(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const t = (pt, vars) => (window.pt2vhfT ? window.pt2vhfT(pt, vars) : pt);
  const helpers = () => window.pt2vhfStationHelpers || {};
  let step = 1;

  async function requestJson(url, options = {}) {
    const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) throw new Error(t(data.error || `HTTP ${response.status}`));
    return data;
  }

  function serverForPosition(lat, lon) {
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return 'rotate.aprs2.net';
    if (lon <= -30) return lat < 12 ? 'soam.aprs2.net' : 'noam.aprs2.net';
    if (lon >= 110 && lat <= -10) return 'aunz.aprs2.net';
    if (lon >= 60) return 'asia.aprs2.net';
    return 'euro.aprs2.net';
  }

  function callsignValue() { return String($('#onboardingCallsign').value || '').trim().toUpperCase(); }

  function updateCallsign() {
    const call = callsignValue();
    const valid = helpers().isValidAmateurCallsign ? helpers().isValidAmateurCallsign(call) : call.length >= 3;
    $('#onboardingPasscode').textContent = valid && helpers().calculateAprsPasscode ? helpers().calculateAprsPasscode(call) : '—';
    $('#onboardingCallsignStatus').textContent = !call ? '' : valid
      ? t('Indicativo válido.')
      : t('Indicativo inválido. Use um indicativo de radioamador real, sem SSID (ex.: PY2ABC).');
    $('#onboardingCallsignStatus').classList.toggle('field-status-error', !!call && !valid);
    return valid;
  }

  function position() {
    const lat = parseFloat($('#onboardingLat').value);
    const lon = parseFloat($('#onboardingLon').value);
    const ok = Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180 && !(lat === 0 && lon === 0);
    return ok ? { lat, lon } : null;
  }

  function setPosition(lat, lon, source) {
    $('#onboardingLat').value = Number(lat).toFixed(6);
    $('#onboardingLon').value = Number(lon).toFixed(6);
    if (source !== 'grid' && helpers().maidenheadEncode) $('#onboardingGrid').value = helpers().maidenheadEncode(lat, lon, 6);
    $('#onboardingPositionStatus').textContent = '';
    $('#onboardingServer').value = serverForPosition(lat, lon);
  }

  function applyGrid() {
    const decoded = helpers().maidenheadDecode ? helpers().maidenheadDecode($('#onboardingGrid').value) : null;
    if (decoded) setPosition(decoded.lat, decoded.lon, 'grid');
    return !!decoded;
  }

  function showStep(next) {
    step = next;
    document.querySelectorAll('#onboardingForm [data-step]').forEach(el => el.classList.toggle('hidden', Number(el.dataset.step) !== step));
    document.querySelectorAll('#onboardingForm [data-step-dot]').forEach(el => el.classList.toggle('active', Number(el.dataset.stepDot) <= step));
    $('#onboardingBack').classList.toggle('hidden', step === 1);
    $('#onboardingNext').textContent = step === 3 ? t('Salvar e começar') : t('Avançar');
    const focus = { 1: '#onboardingCallsign', 2: '#onboardingGrid', 3: '#onboardingServer' }[step];
    setTimeout(() => $(focus)?.focus(), 50);
  }

  function close() { $('#onboardingModal').classList.add('hidden'); }

  async function finish() {
    const pos = position();
    const status = $('#onboardingSaveStatus');
    status.textContent = t('Salvando…');
    status.classList.remove('field-status-error');
    try {
      const call = callsignValue();
      await requestJson('/api/config', { method: 'POST', body: JSON.stringify({
        callsign: call,
        ssid: Number($('#onboardingSsid').value || 0),
        passcode: helpers().calculateAprsPasscode ? String(helpers().calculateAprsPasscode(call)) : '',
        latitude: pos.lat,
        longitude: pos.lon,
        server: $('#onboardingServer').value,
        port: 14580,
        onboarding_done: 1,
      }) });
      if ($('#onboardingConnect').checked) {
        try { await requestJson('/api/connect', { method: 'POST', body: '{}' }); } catch (_) { /* o cabeçalho mostra o estado */ }
      }
      await helpers().reloadConfig?.();
      close();
      document.dispatchEvent(new CustomEvent('pt2vhf-onboarding-done'));
    } catch (error) {
      status.textContent = error.message;
      status.classList.add('field-status-error');
    }
  }

  async function next(event) {
    event?.preventDefault?.();
    if (step === 1) {
      if (!updateCallsign()) { $('#onboardingCallsign').focus(); if (!callsignValue()) $('#onboardingCallsignStatus').textContent = t('Informe seu indicativo.'); return; }
      showStep(2);
    } else if (step === 2) {
      if (!position() && !applyGrid()) {
        $('#onboardingPositionStatus').textContent = t('Informe o Grid Locator, use a localização ou digite latitude e longitude.');
        $('#onboardingPositionStatus').classList.add('field-status-error');
        return;
      }
      showStep(3);
    } else {
      await finish();
    }
  }

  async function skip() {
    close();
    try { await requestJson('/api/config', { method: 'POST', body: JSON.stringify({ onboarding_done: 1 }) }); } catch (_) { /* volta a aparecer na próxima abertura */ }
  }

  function locate() {
    const out = $('#onboardingPositionStatus');
    if (!navigator.geolocation) { out.textContent = t('Localização não disponível neste computador.'); return; }
    out.textContent = t('Obtendo localização…');
    out.classList.remove('field-status-error');
    navigator.geolocation.getCurrentPosition(
      pos => setPosition(pos.coords.latitude, pos.coords.longitude, 'gps'),
      () => { out.textContent = t('Não foi possível obter a localização. Use o Grid Locator ou digite as coordenadas.'); out.classList.add('field-status-error'); },
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 },
    );
  }

  async function waitForOtherNotices() {
    // Um aviso por vez: espera o aviso de abertura e as novidades da versão fecharem.
    for (let i = 0; i < 120; i++) {
      const busy = ['#officialSiteNotice', '#whatsNewModal'].some(sel => $(sel) && !$(sel).classList.contains('hidden'));
      if (!busy && i >= 6) return;
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }

  async function maybeStart() {
    let cfg;
    try { cfg = await requestJson('/api/config'); } catch (_) { return; }
    if (Number(cfg.onboarding_done) || String(cfg.callsign || '').trim()) return;
    // O assistente já pede o SSID: as sugestões de SSID não abrem sozinhas nesta sessão (nem por cima dele).
    document.dispatchEvent(new CustomEvent('pt2vhf-onboarding-active'));
    await waitForOtherNotices();
    if (cfg.latitude != null && cfg.longitude != null && !(Number(cfg.latitude) === 0 && Number(cfg.longitude) === 0)) {
      setPosition(Number(cfg.latitude), Number(cfg.longitude), 'config');
    }
    $('#onboardingModal').classList.remove('hidden');
    showStep(1);
  }

  function init() {
    if (!$('#onboardingModal')) return;
    $('#onboardingForm').addEventListener('submit', next);
    $('#onboardingNext').addEventListener('click', next);
    $('#onboardingForm').addEventListener('keydown', event => {
      if (event.key === 'Enter' && event.target.id !== 'onboardingGrid' && event.target.tagName !== 'BUTTON') { event.preventDefault(); void next(); }
    });
    $('#onboardingBack').addEventListener('click', () => showStep(Math.max(1, step - 1)));
    $('#onboardingSkip').addEventListener('click', skip);
    $('#onboardingCallsign').addEventListener('input', () => {
      $('#onboardingCallsign').value = $('#onboardingCallsign').value.toUpperCase().replace(/[^A-Z0-9]/g, '');
      updateCallsign();
    });
    $('#onboardingGrid').addEventListener('change', applyGrid);
    $('#onboardingGrid').addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); applyGrid(); } });
    $('#onboardingLocate').addEventListener('click', locate);
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !$('#onboardingModal').classList.contains('hidden')) void skip();
    });
    void maybeStart();
  }

  window.pt2vhfOpenOnboarding = () => { $('#onboardingModal')?.classList.remove('hidden'); showStep(1); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
