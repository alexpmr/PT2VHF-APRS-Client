// Run with node tests/i18n_dom.browser.cjs (requires playwright + Chromium).
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.I18N_BROWSER_CHANNEL ? { channel: process.env.I18N_BROWSER_CHANNEL } : {}) });
  try {
    const page = await browser.newPage();
    await page.setContent('<main><span id="status">Nome</span><input id="entry" placeholder="Nome" title="Nome" aria-label="Nome"><section id="dynamic"></section><span translate="no" id="received">Nome</span><span class="notranslate">Nome</span></main>');
    for (const file of ['i18n/es.js', 'i18n/fr.js', 'i18n/de-DE.js', 'i18n/it-IT.js', 'i18n/ja-JP.js', 'i18n/pl-PL.js', 'i18n/nl-NL.js', 'i18n/zh-CN.js', 'i18n/en.js', 'i18n/th-TH.js', 'i18n_dom.js']) {
      await page.addScriptTag({ path: path.join(root, 'pt2vhf_aprs/static/js', file) });
    }
    await page.evaluate(() => {
      window.testLanguage = 'pt-BR';
      window.testTranslator = pt2vhfCreateDomTranslator(key => testLanguage === 'pt-BR' ? key : testLanguage === 'en' ? ({ Nome: 'Name', Ativo: 'Active' })[key] : PT2VHF_I18N[testLanguage]?.[key]);
      testTranslator.observe(document.body);
      document.querySelector('#entry').value = 'PT2VHF-15';
    });
    for (const lang of ['pt-BR', 'en', 'es', 'fr', 'de-DE', 'it-IT', 'pt-BR']) {
      await page.evaluate(lang => { window.testLanguage = lang; testTranslator.translate(document.body); }, lang);
      const expected = await page.evaluate(lang => lang === 'pt-BR' ? 'Nome' : lang === 'en' ? 'Name' : PT2VHF_I18N[lang].Nome, lang);
      assert.ok(expected);
      assert.equal(await page.locator('#entry').getAttribute('placeholder'), expected);
      assert.equal(await page.locator('#entry').getAttribute('title'), expected);
      assert.equal(await page.locator('#entry').getAttribute('aria-label'), expected);
      assert.equal(await page.locator('#entry').inputValue(), 'PT2VHF-15');
      assert.equal(await page.locator('#received').textContent(), 'Nome');
      assert.equal(await page.locator('.notranslate').textContent(), 'Nome');
      // A bare text node added later, a changed text node and a root attribute.
      await page.evaluate(() => {
        document.querySelector('#dynamic').replaceChildren(document.createTextNode('Nome'));
        document.querySelector('#status').firstChild.nodeValue = 'Ativo';
        document.querySelector('#entry').setAttribute('title', 'Ativo');
      });
      await page.waitForFunction(() => document.querySelector('#dynamic').textContent === (testLanguage === 'pt-BR' ? 'Nome' : testLanguage === 'en' ? 'Name' : PT2VHF_I18N[testLanguage].Nome));
      const active = await page.evaluate(() => testLanguage === 'pt-BR' ? 'Ativo' : testLanguage === 'en' ? 'Active' : PT2VHF_I18N[testLanguage].Ativo);
      assert.equal(await page.locator('#status').textContent(), active);
      assert.equal(await page.locator('#entry').getAttribute('title'), active);
      await page.evaluate(() => { document.querySelector('#entry').setAttribute('title', 'Nome'); });
      await page.waitForFunction(() => document.querySelector('#entry').title === (testLanguage === 'pt-BR' ? 'Nome' : testLanguage === 'en' ? 'Name' : PT2VHF_I18N[testLanguage].Nome));
    }
    await page.evaluate(() => { document.querySelector('#status').firstChild.nodeValue = 'PT2VHF-15>APRS:Nome'; });
    await page.waitForTimeout(50);
    assert.equal(await page.locator('#status').textContent(), 'PT2VHF-15>APRS:Nome');
    assert.equal(await page.evaluate(() => Object.keys(PT2VHF_I18N).length), 10);
    console.log('PASS: six locales, switching back, live text/attributes, added text, preserved input/received data, eight extra catalogs');
  } finally { await browser.close(); }
})().catch(err => { console.error(err); process.exitCode = 1; });
