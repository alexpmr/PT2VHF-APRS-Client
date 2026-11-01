// Source-derived coverage and interpolation checks, without a debt baseline.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const context = vm.createContext({ window: {}, document: { documentElement: { lang: 'pt-BR' } } });
for (const file of ['i18n_catalog.js', 'i18n_runtime.js']) {
  vm.runInContext(fs.readFileSync(path.join(root, 'pt2vhf_aprs/static/js', file), 'utf8'), context);
}
const { lookup } = context.window.pt2vhfI18n;
const work = JSON.parse(fs.readFileSync(path.join(root, '.test-runtime/i18n-catalog-work.json'), 'utf8'));
const failures = [];
const expressions = JSON.parse(fs.readFileSync(path.join(root, '.test-runtime/i18n-source-literals.json'), 'utf8'));
for (const expression of expressions) {
  for (const info of Object.values(expression.ownedSlots || {})) {
    const untranslated = info.choices.filter(text => /[a-zÀ-ÿ]{3}/i.test(text) && !/^(?:Internet\/APRS-IS|true|false)$/.test(text) && !text.includes('<'));
    if (untranslated.length) failures.push({ module: expression.module, issue: 'owned UI words hidden in interpolation', choices: untranslated, expression: info.expression });
  }
}
for (const language of ['en', 'es', 'fr', 'de-DE', 'it-IT']) {
  for (const source of work.keys) {
    const translated = lookup(source, language);
    if (!translated) { failures.push({ language, source, issue: 'missing' }); continue; }
    const tokens = text => (text.match(/\{v\d+\}/g) || []).sort().join('|');
    if (tokens(source) !== tokens(translated)) failures.push({ language, source, translated, issue: 'interpolation changed' });
    if (/\{v\d+\}/.test(source)) {
      const values = source.replace(/\{v(\d+)\}/g, (_, i) => `PT2VHF-${i}`);
      const expected = translated.replace(/\{v(\d+)\}/g, (_, i) => `PT2VHF-${i}`);
      const actual = lookup(values, language) ?? values;
      if (actual !== expected) failures.push({ language, source, issue: 'live template did not match', expected, actual });
    }
  }
}
fs.writeFileSync(path.join(root, '.test-runtime/i18n-strict-report.json'), JSON.stringify(failures, null, 2));
assert.equal(failures.length, 0, JSON.stringify(failures.slice(0, 12), null, 2));
assert.equal(lookup('Tabela secundária', 'en'), 'Alternate table');
assert.match(lookup('RF inferido (não confirmado diretamente)', 'de-DE'), /nicht direkt bestätigt/);
console.log(`PASS: ${work.keys.length} source keys across five target locales, placeholders and live templates`);
