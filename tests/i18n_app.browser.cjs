const { chromium } = require('playwright');
const assert = require('node:assert/strict');
(async () => {
  const origin = process.env.I18N_APP_URL;
  assert.ok(origin?.startsWith('http://127.0.0.1:'), 'Use the isolated Python harness');
  const browser = await chromium.launch({ headless: true, ...(process.env.I18N_BROWSER_CHANNEL ? { channel: process.env.I18N_BROWSER_CHANNEL } : {}) });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
    async function dismissNotices() {
      for (const id of ['officialSiteNoticeClose', 'whatsNewClose']) {
        const button = page.locator('#' + id);
        if (await button.isVisible()) await button.click();
      }
    }
    await page.goto(origin);
    await page.waitForTimeout(1800);
    await dismissNotices();
    for (const [language, htmlLang, flag] of [
      ['en', 'en', 'flag_uk.svg'], ['es', 'es', 'flag_spain.svg'],
      ['fr', 'fr', 'flag_france.svg'], ['de-DE', 'de', 'flag_germany.svg'],
      ['it-IT', 'it', 'flag_italy.svg'], ['pt-BR', 'pt-BR', 'flag_br.svg']
    ]) {
      await page.locator('#languageQuickCurrent').click();
      const saved = page.waitForResponse(response => response.url().endsWith('/api/config') && response.request().method() === 'POST');
      await page.locator(`.language-quick-option[data-language="${language}"]`).click();
      assert.equal((await saved).status(), 200);
      assert.equal(await page.locator('html').getAttribute('lang'), htmlLang);
      assert.ok((await page.locator('#languageQuickCurrentFlag').getAttribute('src')).endsWith(flag));
      assert.equal(await page.locator(`.language-quick-option[data-language="${language}"]`).getAttribute('aria-checked'), 'true');
      for (const tab of ['messages', 'stations', 'log', 'analysis', 'automations', 'config', 'about', 'help', 'map']) {
        await dismissNotices();
        await page.locator(`.tab[data-tab="${tab}"]`).click();
        assert.ok(await page.locator(`#tab-${tab}`).isVisible(), `${language}: ${tab}`);
      }
      // Reload creates fresh DOM/state and exercises the saved server setting.
      await page.reload();
      await page.waitForFunction(lang => document.documentElement.lang === lang, htmlLang);
      await page.waitForTimeout(1800);
      await dismissNotices();
      assert.equal(await page.locator('#configForm [name="language"]').inputValue(), language);
      assert.equal(await page.locator('.language-quick-option').count(), 10);
    }
    assert.deepEqual(errors, []);
    console.log('PASS: real application, six languages, nine tabs, exact flags, active option and saved language after reload');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
