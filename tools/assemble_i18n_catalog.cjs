const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const js = path.join(root, 'pt2vhf_aprs/static/js');
const context = vm.createContext({ window: {}, console });
for (const file of ['i18n_extra.js', 'i18n_de.js', 'i18n_it.js', 'i18n_ja.js', 'i18n_pl.js', 'i18n_nl.js', 'i18n_zh.js', 'i18n_v1425.js', 'i18n_v1426.js', 'i18n_v1430.js', 'i18n_live.js']) vm.runInContext(fs.readFileSync(path.join(js, file), 'utf8'), context);
const app = fs.readFileSync(path.join(js, 'app.js'), 'utf8');
vm.runInContext(app.slice(app.indexOf('  const EN_TEXT ='), app.indexOf('  const LANGUAGE_META =')) + '\nwindow.english = Object.fromEntries(EN_TEXT);', context);
const catalogs = context.window.PT2VHF_I18N;
catalogs.en = { ...context.window.english, ...catalogs.en };
const sources = new Map();
const conflicts = [];
function add(key, module) {
  if (typeof key !== 'string' || !/[A-Za-zÀ-ÿ]{2}/.test(key.replace(/\{v\d+\}/g, ''))) return;
  if (!sources.has(key)) sources.set(key, new Set());
  sources.get(key).add(module);
}
for (const row of JSON.parse(fs.readFileSync(path.join(root, '.test-runtime/i18n-source-literals.json'), 'utf8'))) {
  if (row.text) {
    add(row.text, row.module);
    for (const [locale, value] of Object.entries(row.translations || {})) { (catalogs[locale] ||= {})[row.text] ||= value; }
    continue;
  }
  const args = row.values || row.args.map(value => value == null ? null : vm.runInNewContext(value));
  const key = args[0];
  add(key, row.module);
  for (const [i, locale] of [[1, 'en'], [2, 'es'], [3, 'fr']]) {
    if (!args[i]) continue;
    catalogs[locale] ||= {};
    if (catalogs[locale][key] && catalogs[locale][key] !== args[i]) conflicts.push({ key, locale, catalog: catalogs[locale][key], inline: args[i], module: row.module });
    else catalogs[locale][key] = args[i];
  }
}
// TNC has its own complete EN/ES/FR dictionaries; make those available globally.
const tnc = fs.readFileSync(path.join(js, 'tnc.js'), 'utf8');
const tncStart = tnc.indexOf('  const TNC_I18N =');
const tncEnd = tnc.indexOf('  function tncLanguage', tncStart);
vm.runInContext(tnc.slice(tncStart, tncEnd) + '\nwindow.tncCatalog = TNC_I18N;', context);
for (const [locale, entries] of Object.entries(context.window.tncCatalog)) {
  catalogs[locale] = { ...entries, ...(catalogs[locale] || {}) };
  Object.keys(entries).forEach(key => add(key, 'tnc.js'));
}
for (const entries of Object.values(catalogs)) Object.keys(entries).forEach(key => add(key, 'legacy-catalogs'));
const reviewed = JSON.parse(fs.readFileSync(path.join(root, 'tools/i18n_reviewed_overrides.json'), 'utf8'));
catalogs['pt-BR'] = reviewed['pt-BR'] || {};
for (const [key, values] of Object.entries(reviewed.entries)) {
  if (values.length !== reviewed.locales.length) throw new Error('Invalid reviewed locale vector for ' + key);
  reviewed.locales.forEach((locale, i) => { (catalogs[locale] ||= {})[key] = values[i]; });
  add(key, 'reviewed-overrides');
}
const technical = /^(?:[\d\s\p{P}\p{S}]+|APRS(?:-IS)?|AX\.25|RF|AIS|TNC(?:\s*\/\s*RF)?|KISS|AGWPE|TCP|UDP|USB|GPS|DTR|RTS|PTT|CSV|PDF|GeoJSON|KML|SSID|ACK|REJ|CQ|Wi-Fi|Bluetooth|OpenStreetMap|Leaflet|RainViewer|PT2VHF(?: APRS Client)?|English|Português \(Brasil\)|Español|Français|Deutsch|Italiano|日本語|Polski|Nederlands|简体中文|Latitude|Longitude|Altitude|km\/h|baud|dBm|W|MHz|UTC|HTTP|HTTPS)$/u;
const keys = [...sources.keys()].filter(key => !technical.test(key)).sort();
const todo = {};
for (const locale of ['en', 'es', 'fr', 'de-DE', 'it-IT']) todo[locale] = keys.filter(key => !catalogs[locale]?.[key]);
const result = { catalogs, sources: Object.fromEntries([...sources].map(([key, modules]) => [key, [...modules]])), keys, todo, conflicts };
fs.writeFileSync(path.join(root, '.test-runtime/i18n-catalog-work.json'), JSON.stringify(result, null, 2));
console.log(JSON.stringify({ keys: keys.length, conflicts: conflicts.length, missing: Object.fromEntries(Object.entries(todo).map(([locale, keys]) => [locale, keys.length])) }, null, 2));
