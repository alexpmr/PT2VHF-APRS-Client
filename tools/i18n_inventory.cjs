// Consolidated catalogs, independent of the legacy vector-count audit.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const js = path.join(root, 'pt2vhf_aprs/static/js');
const context = vm.createContext({ window: {}, console });
const files = ['i18n_extra.js', 'i18n_de.js', 'i18n_it.js', 'i18n_ja.js', 'i18n_pl.js', 'i18n_nl.js', 'i18n_zh.js', 'i18n_v1425.js', 'i18n_v1426.js', 'i18n_v1430.js', 'i18n_live.js'];
for (const file of files) vm.runInContext(fs.readFileSync(path.join(js, file), 'utf8'), context, { filename: file });
const app = fs.readFileSync(path.join(js, 'app.js'), 'utf8');
vm.runInContext(app.slice(app.indexOf('  const EN_TEXT ='), app.indexOf('  const LANGUAGE_META =')) + '\nwindow.english = Object.fromEntries(EN_TEXT);', context);
const catalogs = context.window.PT2VHF_I18N;
catalogs.en = { ...context.window.english, ...catalogs.en };
const sources = new Map();
function add(key, file) {
  key = key.trim();
  if (!/[a-zA-ZÀ-ÿ]{3}/.test(key) || /[{}<>]/.test(key)) return;
  if (!sources.has(key)) sources.set(key, new Set());
  sources.get(key).add(file);
}
for (const file of fs.readdirSync(js).filter(name => name.endsWith('.js') && !name.startsWith('i18n_'))) {
  const text = fs.readFileSync(path.join(js, file), 'utf8');
  for (const match of text.matchAll(/\bui\s*\(\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g)) {
    add(vm.runInNewContext(match[1]), file);
  }
}
for (const file of fs.readdirSync(path.join(root, 'pt2vhf_aprs/templates')).filter(name => name.endsWith('.html'))) {
  const text = fs.readFileSync(path.join(root, 'pt2vhf_aprs/templates', file), 'utf8');
  for (const match of text.matchAll(/>\s*([^<>{}\n]+)\s*</g)) add(match[1], file);
  for (const match of text.matchAll(/(?:placeholder|title|aria-label)="([^"{}]+)"/g)) add(match[1], file);
}
const baselinePath = path.join(root, 'tools/i18n_inventory_baseline.json');
const findings = {};
const report = { note: 'Literal candidate inventory only; missing entries can include technical terms and module-local dictionaries. This does not prove full UI localization.', modules: files, candidates: sources.size, locales: {} };
for (const locale of ['pt-BR', 'en', 'es', 'fr', 'de-DE', 'it-IT']) {
  const catalog = catalogs[locale] || {};
  const missing = locale === 'pt-BR' ? [] : [...sources.keys()].filter(key => !catalog[key]).sort();
  findings[locale] = missing;
  report.locales[locale] = { catalogKeys: Object.keys(catalog).length, missingCount: missing.length, missing: missing.map(key => ({ key, modules: [...sources.get(key)] })), sourceIdentical: Object.entries(catalog).filter(([key, value]) => key === value).map(([key]) => key) };
}
if (process.argv.includes('--write-baseline')) fs.writeFileSync(baselinePath, JSON.stringify(findings, null, 2) + '\n');
const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
report.newMissing = Object.fromEntries(Object.entries(findings).map(([locale, keys]) => [locale, keys.filter(key => !(baseline[locale] || []).includes(key))]));
const out = process.argv.indexOf('--output');
if (out >= 0) fs.writeFileSync(path.resolve(process.argv[out + 1]), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ candidates: report.candidates, locales: Object.fromEntries(Object.entries(report.locales).map(([locale, value]) => [locale, { catalogKeys: value.catalogKeys, missingCount: value.missingCount }])), newMissing: report.newMissing }, null, 2));
if (Object.values(report.newMissing).some(keys => keys.length)) process.exitCode = 1;
