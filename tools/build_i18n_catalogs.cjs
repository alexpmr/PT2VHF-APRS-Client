// Uso único (v2.0.7): junta os 13 arquivos de tradução antigos (por versão) num catálogo por idioma.
// Mantido no repositório para referência; os catálogos em static/js/i18n/ passam a ser editados direto.
const fs = require('fs'), vm = require('vm'), path = require('path');
const js = path.join(__dirname, '..', 'pt2vhf_aprs', 'static', 'js');
const old = ['extra', 'de', 'it', 'ja', 'pl', 'nl', 'zh', 'v1425', 'v1426', 'v1430', 'live', 'v205', 'th']
  .map(n => path.join(js, `i18n_${n}.js`));
const ctx = { window: {} }; vm.createContext(ctx);
for (const f of old) vm.runInContext(fs.readFileSync(f, 'utf8'), ctx, { filename: f });
const NAMES = { en: 'inglês', es: 'espanhol', fr: 'francês', 'de-DE': 'alemão', 'it-IT': 'italiano', 'ja-JP': 'japonês',
  'pl-PL': 'polonês', 'nl-NL': 'neerlandês', 'zh-CN': 'chinês simplificado', 'th-TH': 'tailandês' };
fs.mkdirSync(path.join(js, 'i18n'), { recursive: true });
for (const [locale, catalog] of Object.entries(ctx.window.PT2VHF_I18N)) {
  const body = JSON.stringify(catalog, null, 1);
  const out = `/* Catálogo de tradução: ${NAMES[locale] || locale} (${locale}). Chave = texto em português da interface.\n` +
    ` * Um arquivo por idioma (desde a v2.0.7); para traduzir um texto novo, acrescente a chave aqui e nos\n` +
    ` * outros idiomas. O corpo é JSON puro (tools/i18n_audit.py lê direto). */\n` +
    `(window.PT2VHF_I18N = window.PT2VHF_I18N || {})['${locale}'] = ${body};\n`;
  fs.writeFileSync(path.join(js, 'i18n', `${locale}.js`), out);
  console.log(locale, Object.keys(catalog).length);
}
