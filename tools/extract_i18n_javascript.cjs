// Parse UI expressions without executing application code.
const fs = require('node:fs');
const path = require('node:path');
let acorn;
try { acorn = require('acorn'); } catch { acorn = require('../.test-runtime/js-parser/acorn.cjs'); }
const root = path.resolve(__dirname, '..');
const rows = [];
function hasText(node) {
  return node?.type === 'Literal' && typeof node.value === 'string' || node?.type === 'TemplateLiteral' || node?.type === 'BinaryExpression' && node.operator === '+' && (hasText(node.left) || hasText(node.right));
}
for (const file of fs.readdirSync(path.join(root, 'pt2vhf_aprs/static/js')).filter(file => file.endsWith('.js') && !file.startsWith('i18n_'))) {
  const source = fs.readFileSync(path.join(root, 'pt2vhf_aprs/static/js', file), 'utf8');
  const tree = acorn.parse(source, { ecmaVersion: 'latest', sourceType: 'script' });
  function expression(node, slots = new Map(), allowNew = true) {
    function slot(value) {
      const code = source.slice(value.start, value.end).replace(/\s+/g, '');
      if (!slots.has(code)) {
        if (!allowNew) throw new Error('Different interpolation expression');
        slots.set(code, 'v' + slots.size);
      }
      if (value.type === 'ConditionalExpression') {
        const choices = [value.consequent, value.alternate].filter(item => item.type === 'Literal' && typeof item.value === 'string').map(item => item.value);
        if (choices.some(text => /[A-Za-zÀ-ÿ]{3}/.test(text))) {
          slots.owned ||= {};
          slots.owned[slots.get(code)] = { choices, expression: source.slice(value.start, value.end) };
        }
      }
      return '{' + slots.get(code) + '}';
    }
    if (node.type === 'Literal' && typeof node.value === 'string') return node.value;
    if (node.type === 'BinaryExpression' && node.operator === '+' && hasText(node)) return expression(node.left, slots, allowNew) + expression(node.right, slots, allowNew);
    if (node.type === 'TemplateLiteral') return node.quasis.map((part, index) => part.value.cooked + (node.expressions[index] ? slot(node.expressions[index]) : '')).join('');
    return slot(node);
  }
  function add(node, kind, html = false) {
    if (node?.type === 'ConditionalExpression') { add(node.consequent, kind, html); add(node.alternate, kind, html); return; }
    if (!hasText(node)) return;
    const slots = new Map();
    const value = expression(node, slots);
    if (/[A-Za-zÀ-ÿ]{2}/.test(value.replace(/\{v\d+\}/g, ''))) rows.push({ module: file, kind, ownedSlots: slots.owned || {}, ...(html ? { html: value } : { text: value }) });
  }
  function walk(node) {
    if (!node || typeof node !== 'object') return;
    if (node.type === 'ArrayExpression' && node.elements.length >= 3 && node.elements.length <= 5 && node.elements[0]?.type === 'Literal' && (typeof node.elements[0].value === 'number' || typeof node.elements[0].value === 'string' && /^[a-z][a-z0-9_]*$/.test(node.elements[0].value)) && node.elements[1]?.type === 'Literal' && typeof node.elements[1].value === 'string' && /[A-ZÀ-Ý\sÀ-ÿ]/.test(node.elements[1].value) && node.elements[2]?.type === 'Literal' && typeof node.elements[2].value === 'string') {
      rows.push({ module: file, kind: 'label-vector', values: node.elements.slice(1).map(item => item?.type === 'Literal' && typeof item.value === 'string' ? item.value : null) });
    }
    if (node.type === 'Property' && node.value?.type === 'ObjectExpression') {
      const locale = node.key.name || node.key.value;
      if (['en', 'es', 'fr', 'de-DE', 'it-IT', 'ja-JP', 'pl-PL', 'nl-NL', 'zh-CN'].includes(locale)) {
        for (const entry of node.value.properties) {
          if (entry.key?.type === 'Literal' && typeof entry.key.value === 'string' && entry.value?.type === 'Literal' && typeof entry.value.value === 'string') rows.push({ module: file, kind: 'inline-dictionary', text: entry.key.value, translations: { [locale]: entry.value.value } });
        }
      }
    }
    if (node.type === 'CallExpression' && node.callee.type === 'Identifier' && ['ui', 'tr', 't'].includes(node.callee.name) && hasText(node.arguments[0])) {
      const slots = new Map();
      const values = [expression(node.arguments[0], slots)];
      for (const argument of node.arguments.slice(1, 4)) {
        try { values.push(hasText(argument) ? expression(argument, slots, false) : null); } catch { values.push(null); }
      }
      rows.push({ module: file, kind: 'translation-call', values, ownedSlots: slots.owned || {} });
    }
    if (node.type === 'CallExpression' && node.callee.type === 'Identifier' && ['toast', 'alert', 'confirm', 'prompt'].includes(node.callee.name)) add(node.arguments[0], node.callee.name);
    if (node.type === 'AssignmentExpression' && node.left.type === 'MemberExpression') {
      const property = node.left.computed ? node.left.property.value : node.left.property.name;
      if (['textContent', 'innerText', 'title', 'placeholder'].includes(property)) add(node.right, property);
      if (property === 'innerHTML') add(node.right, property, true);
    }
    if (node.type === 'CallExpression' && node.callee.type === 'MemberExpression' && node.callee.property.name === 'setAttribute' && ['title', 'placeholder', 'aria-label'].includes(node.arguments[0]?.value)) add(node.arguments[1], node.arguments[0].value);
    if (['TemplateLiteral', 'Literal'].includes(node.type) && hasText(node)) {
      const slots = new Map();
      const value = expression(node, slots);
      if (/<[a-zA-Z][^>]*>/.test(value)) rows.push({ module: file, kind: 'html-fragment', html: value, ownedSlots: slots.owned || {} });
    }
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) value.forEach(walk);
      else if (value && typeof value === 'object') walk(value);
    }
  }
  walk(tree);
}
fs.writeFileSync(path.join(root, '.test-runtime/i18n-js-ast.json'), JSON.stringify(rows, null, 2));
console.log(`Parsed ${rows.length} UI expressions, attributes and HTML fragments`);
