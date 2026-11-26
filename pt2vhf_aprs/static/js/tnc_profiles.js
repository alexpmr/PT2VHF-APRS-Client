/* v2.0.7: perfis de TNC. Cada perfil guarda a configuração TNC / RF inteira com um nome;
 * "Carregar perfil" grava a configuração dele como a atual (um TNC ativo por vez). */
(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const api = () => window.PT2VHF_TNC || {};
  const tr = text => (api().tr ? api().tr(text) : text);

  async function requestJson(url, options = {}) {
    const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) throw new Error(tr(data.error || `HTTP ${response.status}`));
    return data;
  }

  function setMessage(text, isError = false) {
    const out = $('#tncProfileStatus');
    if (!out) return;
    out.textContent = text;
    out.classList.toggle('error', !!isError);
  }

  function render(profiles = [], selected = '') {
    const select = $('#tncProfileSelect');
    if (!select) return;
    select.innerHTML = '';
    if (!profiles.length) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = tr('Nenhum perfil salvo');
      select.appendChild(opt);
    }
    for (const profile of profiles) {
      const opt = document.createElement('option');
      opt.value = profile.name;
      opt.textContent = profile.summary ? `${profile.name} — ${profile.summary}` : profile.name;
      opt.setAttribute('translate', 'no');
      select.appendChild(opt);
    }
    if (selected) select.value = selected;
    $('#tncProfileLoad').disabled = !profiles.length;
    $('#tncProfileDelete').disabled = !profiles.length;
  }

  async function refresh(selected = '') {
    try {
      const data = await requestJson('/api/tnc/profiles');
      render(data.profiles || [], selected);
    } catch (error) { setMessage(error.message, true); }
  }

  async function saveProfile() {
    const name = String($('#tncProfileName')?.value || $('#tncProfileSelect')?.value || '').trim();
    if (!name) { setMessage(tr('Informe um nome para o perfil.'), true); $('#tncProfileName')?.focus(); return; }
    try {
      const config = api().collectConfig ? api().collectConfig() : null;
      const data = await requestJson('/api/tnc/profiles', { method: 'POST', body: JSON.stringify({ name, config }) });
      render(data.profiles || [], data.profile?.name || name);
      if ($('#tncProfileName')) $('#tncProfileName').value = '';
      setMessage(`${tr('Perfil salvo:')} ${data.profile?.name || name}`);
    } catch (error) { setMessage(error.message, true); }
  }

  async function loadProfile() {
    const name = $('#tncProfileSelect')?.value;
    if (!name) return;
    try {
      const data = await requestJson('/api/tnc/profiles/load', { method: 'POST', body: JSON.stringify({ name }) });
      api().applyConfig?.(data.config || {});
      api().setStatus?.(data.status || {});
      void api().refreshData?.();
      setMessage(`${tr('Perfil carregado:')} ${data.name}`);
    } catch (error) { setMessage(error.message, true); }
  }

  async function deleteProfile() {
    const name = $('#tncProfileSelect')?.value;
    if (!name) return;
    try {
      const data = await requestJson('/api/tnc/profiles/delete', { method: 'POST', body: JSON.stringify({ name }) });
      render(data.profiles || []);
      setMessage(`${tr('Perfil excluído:')} ${name}`);
    } catch (error) { setMessage(error.message, true); }
  }

  function init() {
    if (!$('#tncProfilesCard')) return;
    $('#tncProfileSave')?.addEventListener('click', saveProfile);
    $('#tncProfileLoad')?.addEventListener('click', loadProfile);
    $('#tncProfileDelete')?.addEventListener('click', deleteProfile);
    $('#tncProfileName')?.addEventListener('keydown', event => {
      if (event.key === 'Enter') { event.preventDefault(); void saveProfile(); }
    });
    document.addEventListener('pt2vhf-language-changed', () => refresh($('#tncProfileSelect')?.value || ''));
    void refresh();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
