/* v2.0.7: cópia automática do banco (Configuração → Backup). */
(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const t = (pt, vars) => (window.pt2vhfT ? window.pt2vhfT(pt, vars) : pt);
  let busy = false;

  async function requestJson(url, options = {}) {
    const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) throw new Error(t(data.error || `HTTP ${response.status}`));
    return data;
  }

  function fmtBytes(bytes) {
    const n = Number(bytes) || 0;
    if (n >= 1024 * 1024 * 1024) return `${(n / 1024 / 1024 / 1024).toFixed(1)} GB`;
    if (n >= 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
    return `${Math.max(1, Math.round(n / 1024))} KB`;
  }

  function fmtDate(iso) {
    try {
      const lang = window.pt2vhfLanguage ? window.pt2vhfLanguage() : 'en';
      return new Date(iso).toLocaleString(lang === 'th-TH' ? 'th-TH-u-ca-gregory' : lang, { dateStyle: 'short', timeStyle: 'short' });
    } catch (_) { return iso; }
  }

  function setStatus(text, isError = false) {
    const out = $('#dbBackupStatus');
    if (!out) return;
    out.textContent = text;
    out.classList.toggle('field-status-error', !!isError);
  }

  function render(data = {}) {
    const body = $('#dbBackupList');
    if (!body) return;
    const backups = data.backups || [];
    body.innerHTML = '';
    if (!backups.length) {
      body.innerHTML = `<tr><td colspan="3" class="hint">${t('Nenhuma cópia ainda.')}</td></tr>`;
    }
    for (const item of backups) {
      const row = document.createElement('tr');
      const label = fmtDate(item.created_at) + (item.manual ? ` · ${t('manual')}` : '');
      row.innerHTML = `<td></td><td translate="no"></td><td><button type="button" class="btn secondary small"></button></td>`;
      row.cells[0].textContent = label;
      row.cells[1].textContent = fmtBytes(item.bytes);
      const button = row.querySelector('button');
      button.textContent = t('Restaurar');
      button.addEventListener('click', () => restore(item));
      body.appendChild(row);
    }
    const folder = $('#dbBackupFolder');
    if (folder) folder.textContent = data.folder || '';
    const pending = data.pending_restore;
    $('#dbRestorePending')?.classList.toggle('hidden', !pending);
    if (pending) {
      const match = backups.find(item => item.name === pending.name);
      $('#dbRestorePendingText').textContent = t('A cópia de {data} será restaurada na próxima vez que o programa abrir. Feche e abra o programa para concluir.', { data: match ? fmtDate(match.created_at) : pending.name });
    }
    const last = data.last_restore;
    if (last && !pending) {
      setStatus(last.ok ? t('Banco restaurado da cópia escolhida. O banco anterior foi guardado na pasta before_restore.') : `${t('Não foi possível restaurar a cópia:')} ${last.error || ''}`, !last.ok);
    }
  }

  async function refresh() {
    try { render(await requestJson('/api/db/backups')); } catch (error) { setStatus(error.message, true); }
  }

  async function backupNow() {
    if (busy) return;
    busy = true;
    setStatus(t('Copiando o banco…'));
    try {
      const data = await requestJson('/api/db/backups', { method: 'POST', body: '{}' });
      setStatus(t('Cópia criada ({tamanho}).', { tamanho: fmtBytes(data.bytes) }));
      await refresh();
    } catch (error) {
      setStatus(`${t('Não foi possível copiar o banco:')} ${error.message}`, true);
    } finally { busy = false; }
  }

  async function restore(item) {
    const question = t('Restaurar a cópia de {data}? Estações, mensagens e tracklogs recebidos depois dela serão substituídos. O banco atual fica guardado na pasta before_restore.', { data: fmtDate(item.created_at) });
    if (!window.confirm(question)) return;
    try {
      await requestJson('/api/db/backups/restore', { method: 'POST', body: JSON.stringify({ name: item.name }) });
      await refresh();
    } catch (error) { setStatus(error.message, true); }
  }

  function init() {
    if (!$('#dbBackupCard')) return;
    $('#dbBackupNowButton')?.addEventListener('click', backupNow);
    $('#dbRestoreCancelButton')?.addEventListener('click', async () => {
      try { await requestJson('/api/db/backups/cancel-restore', { method: 'POST', body: '{}' }); } catch (_) { /* nada pendente */ }
      setStatus(t('Restauração cancelada.'));
      await refresh();
    });
    $('#dbRestoreQuitButton')?.addEventListener('click', async () => {
      try { await requestJson('/api/app/quit', { method: 'POST', body: '{}' }); } catch (error) { setStatus(error.message, true); }
    });
    document.addEventListener('pt2vhf-language-changed', refresh);
    document.addEventListener('click', event => {
      if (event.target.closest?.('[data-config-subtab="backup"]')) void refresh();
    });
    void refresh();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
