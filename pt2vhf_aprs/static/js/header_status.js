/* v2.0.3 (relato PU2MUS): aviso "Auto-Resposta ligada" no cabeçalho.
 * O estado da verificação de versão ("Verificando versão…", "Atualizada") saiu do
 * cabeçalho; ali só aparece "Versão X disponível". O cabeçalho mostra, no lugar,
 * se a Auto-resposta está ligada, que é o que o operador precisa ver. */
(() => {
  'use strict';
  const badge = document.getElementById('autoReplyHeaderStatus');
  if (!badge) return;

  async function refresh() {
    try {
      const res = await fetch('/api/config', { cache: 'no-store' });
      if (!res.ok) return;
      const cfg = await res.json();
      badge.classList.toggle('hidden', !cfg.auto_reply_enabled);
    } catch (_) { /* servidor local reiniciando: tenta de novo no próximo ciclo */ }
  }

  badge.addEventListener('click', () => {
    document.querySelector('.tab[data-tab="automations"]')?.click();
  });
  window.addEventListener('pt2vhf:config-saved', refresh);
  refresh();
  setInterval(refresh, 30000);
})();
