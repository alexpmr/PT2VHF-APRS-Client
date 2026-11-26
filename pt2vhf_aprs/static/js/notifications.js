/* v2.0.7: mensagem recebida com o programa minimizado ou em segundo plano.
 * Mostra o número de não lidas no título da janela (barra de tarefas) e pede ao programa um aviso
 * do sistema (balão da bandeja no Windows, notify-send no Linux, Central de Notificações no macOS).
 * No navegador de outro computador da rede usa a Notification API do próprio navegador. */
(() => {
  'use strict';
  const t = (pt, vars) => (window.pt2vhfT ? window.pt2vhfT(pt, vars) : pt);
  const baseTitle = document.title;
  const isLocal = ['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname);
  let unread = 0;

  function enabled() {
    const input = document.querySelector('#configForm [name="desktop_notifications"]');
    return input ? input.checked : true;
  }

  function inBackground() {
    return document.hidden || !document.hasFocus();
  }

  function updateTitle() {
    document.title = unread > 0 ? `(${unread}) ${baseTitle}` : baseTitle;
  }

  async function notify(title, body) {
    if (isLocal) {
      try {
        await fetch('/api/notify', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, body }) });
      } catch (_) { /* aviso na tela continua */ }
      return;
    }
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') {
      try { await Notification.requestPermission(); } catch (_) { return; }
    }
    if (Notification.permission === 'granted') {
      try { new Notification(title, { body, tag: 'pt2vhf-message' }); } catch (_) { /* sem suporte */ }
    }
  }

  document.addEventListener('pt2vhf-unread-count', event => {
    unread = Math.max(0, Number(event.detail?.count) || 0);
    updateTitle();
  });

  document.addEventListener('pt2vhf-personal-messages', event => {
    const messages = event.detail?.messages || [];
    if (!messages.length || !enabled() || !inBackground()) return;
    const last = messages[messages.length - 1];
    const title = messages.length > 1
      ? t('{n} mensagens novas', { n: messages.length })
      : t('Mensagem de {indicativo}', { indicativo: last.from_call || '?' });
    void notify(title, String(last.message || ''));
  });

  window.addEventListener('focus', updateTitle);
})();
