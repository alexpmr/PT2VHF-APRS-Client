// Actual visible text/attribute audit; navigation alone is not localization QA.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
(async () => {
  const origin = process.env.I18N_APP_URL;
  assert.ok(origin?.startsWith('http://127.0.0.1:'));
  const browser = await chromium.launch({ headless: true, ...(process.env.I18N_BROWSER_CHANNEL ? { channel: process.env.I18N_BROWSER_CHANNEL } : {}) });
  const report = {};
  try {
    const page = await browser.newPage();
    const blockedMutations = [];
    await page.route('**/*', route => {
      const request = route.request();
      if (!request.url().startsWith(origin + '/')) return route.abort();
      const localOnly = ['/api/config', '/api/local-interface/presence', '/api/map-state', '/api/diagnostics/client-event', '/api/topology/rf-records/jobs', '/api/v111/notifications'];
      if (!['GET', 'HEAD'].includes(request.method()) && !localOnly.some(endpoint => request.url().endsWith(endpoint))) {
        blockedMutations.push(request.url());
        return route.abort();
      }
      return route.continue();
    });
    page.on('dialog', dialog => dialog.accept()); // Discard test edits, never send them.
    await page.goto(origin);
    await page.waitForTimeout(1700);
    async function dismiss() {
      for (const id of ['officialSiteNoticeClose', 'whatsNewClose']) if (await page.locator('#' + id).isVisible()) await page.locator('#' + id).click();
    }
    async function snapshot(language, view) {
      await page.waitForTimeout(100);
      report[language][view] = await page.evaluate(language => {
        const rows = [];
        function inspect(value, el, attribute, source) {
          const text = String(value || '').replace(/\s+/g, ' ').trim();
          if (!/[A-Za-zÀ-ÿ]{2}/.test(text) || el.closest('script,style,code,pre,textarea,[translate="no"],.notranslate,[data-i18n-skip],#languageQuickSwitch,[name="language"]')) return;
          if (!el.getClientRects().length || getComputedStyle(el).visibility === 'hidden') return;
          const expected = window.pt2vhfI18n.lookup(source ?? text, language);
          if (expected !== undefined && expected.replace(/\s+/g, ' ').trim() !== text) rows.push({ text, expected, attribute, element: el.id || el.closest('[id]')?.id || el.tagName });
          else if (expected === undefined && /\b(?:não|nenhuma?|configuração|estações|mensagens|agendamento|arquivo|ferramentas|recebidos|aguardando|conexão|usuário|salvar)\b/i.test(text)) rows.push({ text, expected: null, attribute, element: el.id || el.closest('[id]')?.id || el.tagName });
        }
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) if (walker.currentNode.parentElement) inspect(walker.currentNode.nodeValue, walker.currentNode.parentElement, 'text', window.pt2vhfTranslateDom.sourceText(walker.currentNode));
        for (const el of document.querySelectorAll('[title],[placeholder],[aria-label]')) for (const attr of ['title', 'placeholder', 'aria-label']) if (el.hasAttribute(attr)) inspect(el.getAttribute(attr), el, attr, window.pt2vhfTranslateDom.sourceAttribute(el, attr));
        return [...new Map(rows.map(row => [JSON.stringify(row), row])).values()];
      }, language);
    }
    for (const language of ['pt-BR', 'en', 'es', 'fr', 'de-DE', 'it-IT']) {
      report[language] = {};
      await dismiss();
      await page.locator('#languageQuickCurrent').click();
      const saved = page.waitForResponse(response => response.url().endsWith('/api/config') && response.request().method() === 'POST');
      await page.locator(`.language-quick-option[data-language="${language}"]`).click();
      assert.equal((await saved).status(), 200);
      for (const tab of ['map', 'messages', 'stations', 'log', 'analysis', 'automations', 'about', 'help', 'config']) {
        await dismiss();
        await page.locator(`.tab[data-tab="${tab}"]`).click();
        await snapshot(language, tab);
        if (tab === 'messages') {
          await page.locator('#messageViewButton').click();
          await snapshot(language, 'message-filters');
          await page.locator('#messageViewButton').click();
          await page.locator('#scheduledMessagesButton').click();
          await snapshot(language, 'scheduled-list');
          await page.locator('#newScheduledMessageButton').click();
          for (const target of ['station', 'list', 'bulletin', 'group']) {
            await page.locator('#scheduledTargetType').selectOption(target);
            await page.locator('#scheduledScheduleType').selectOption('weekly');
            if (await page.locator('#scheduledRoute').isVisible()) await page.locator('#scheduledRoute').selectOption('rf_custom');
            await snapshot(language, 'scheduled-editor/' + target);
          }
          await page.locator('#manageRecipientGroupsButton').click();
          await snapshot(language, 'recipient-editor');
          await page.locator('#closeScheduledMessagesButton').click();
        }
        if (tab === 'about') {
          await page.locator('#aboutPromoteButton').click();
          await snapshot(language, 'promotion-preview');
          await page.locator('#promotionCancelButton').click();
        }
        if (tab === 'config') {
          for (const subtab of ['station', 'aprsis', 'tnc', 'map', 'app', 'integrations', 'database', 'backup']) {
            await page.locator(`[data-config-subtab="${subtab}"]`).click();
            await snapshot(language, 'config/' + subtab);
          }
          await page.locator('[data-config-subtab="station"]').click();
          const preview = await page.locator('#selectedSymbolPreview small').textContent();
          assert.equal(preview, await page.evaluate(language => pt2vhfI18n.lookup('Tabela primária', language), language));
          await page.locator('#chooseSymbolButton').click();
          await snapshot(language, 'symbol-modal');
          await page.locator('#closeSymbolModal').click();
        }
      }
      await page.locator('.tab[data-tab="map"]').click();
      for (const tool of ['toolCoverage', 'toolLink', 'toolSurvey']) {
        await page.locator('#toolsMenuButton').click();
        await page.locator('#' + tool).click();
        await page.locator('#planningPanel').waitFor({ state: 'visible', timeout: 10000 });
        await snapshot(language, tool);
        await page.locator('#planningClose').click();
      }
    }
    assert.deepEqual(blockedMutations, [], 'Audit must never send, restore, connect, or save schedules');
  } finally {
    await browser.close();
    const output = path.resolve(__dirname, '../.test-runtime/i18n-visible-report.json');
    fs.writeFileSync(output, JSON.stringify(report, null, 2));
    const summary = Object.fromEntries(Object.entries(report).map(([locale, views]) => [locale, { views: Object.keys(views).length, residuals: Object.values(views).reduce((n, rows) => n + rows.length, 0) }]));
    console.log(JSON.stringify(summary, null, 2));
    console.log('Visible text/attribute report:', output);
  }
  if (Object.values(report).some(views => Object.values(views).some(rows => rows.length))) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
