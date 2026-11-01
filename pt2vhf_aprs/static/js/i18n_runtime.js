/* One lookup path for literal UI text and declared interpolation templates. */
(() => {
  'use strict';
  const catalogs = window.PT2VHF_I18N ||= {};
  const aliases = { pt: 'pt-BR', de: 'de-DE', it: 'it-IT', ja: 'ja-JP', pl: 'pl-PL', nl: 'nl-NL', zh: 'zh-CN' };
  const normalize = value => String(value ?? '').replace(/\s+/g, ' ').trim();
  const spacing = (source, value) => source.slice(0, source.length - source.trimStart().length) + value.trim() + source.slice(source.trimEnd().length);
  const locale = value => { const raw = String(value || document.documentElement.lang || 'pt-BR'); return aliases[raw] || raw; };
  const indexes = new Map();
  const sourceKeys = new Set(Object.values(catalogs).flatMap(catalog => Object.keys(catalog).map(normalize)));
  const escape = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  function pattern(template) {
    const slots = [];
    const parts = normalize(template).split(/((?:\{v\d+\})+)/);
    const expression = parts.map(part => {
      if (/^(?:\{v\d+\})+$/.test(part)) { slots.push(part); return '([\\s\\S]*?)'; }
      return escape(part).replace(/\s+/g, '\\s+');
    }).join('');
    if (!slots.length || normalize(template.replace(/\{v\d+\}/g, '')).length < 3) return null;
    return { regex: new RegExp('^' + expression + '$', 'i'), slots, prefix: parts[0].trim().toLowerCase(), suffix: parts[parts.length - 1].trim().toLowerCase() };
  }
  function index(language) {
    language = locale(language);
    if (indexes.has(language)) return indexes.get(language);
    const result = { literals: new Map(), folded: new Map(), reverse: new Map(), templates: [] };
    for (const [source, value] of Object.entries(catalogs[language] || {})) {
      if (typeof value !== 'string' || !value.trim()) continue;
      result.literals.set(normalize(source), value);
      const folded = result.folded.get(normalize(source).toLowerCase()) || new Set();
      folded.add(value);
      result.folded.set(normalize(source).toLowerCase(), folded);
      const reversed = result.reverse.get(normalize(value).toLowerCase()) || new Set();
      reversed.add(normalize(catalogs['pt-BR']?.[source] || source));
      result.reverse.set(normalize(value).toLowerCase(), reversed);
      const forward = pattern(source), backward = pattern(value);
      if (forward && backward && new Set(forward.slots).size === new Set(backward.slots).size && forward.slots.every(slot => backward.slots.includes(slot))) {
        result.templates.push({ source, canonicalSource: catalogs['pt-BR']?.[source] || source, value, forward, backward });
      }
    }
    result.templates.sort((a, b) => b.source.length - a.source.length);
    indexes.set(language, result);
    return result;
  }
  function interpolate(text, slots, match) {
    const values = new Map(slots.map((slot, i) => [slot, match[i + 1]]));
    return text.replace(/(?:\{v\d+\})+/g, slot => values.get(slot) ?? slot);
  }
  function lookup(source, language) {
    source = String(source ?? '');
    language = locale(language);
    const catalog = index(language);
    const exact = catalogs[language]?.[source];
    if (typeof exact === 'string') return spacing(source, exact);
    const normalized = normalize(source);
    const literal = catalog.literals.get(normalized);
    if (literal !== undefined) return spacing(source, literal);
    const folded = catalog.folded.get(normalized.toLowerCase());
    if (folded?.size === 1) return spacing(source, [...folded][0]);
    if (normalized.length <= 4000 && /\p{L}/u.test(normalized)) {
      for (const entry of catalog.templates) {
        if (entry.forward.prefix && !normalized.toLowerCase().startsWith(entry.forward.prefix) || entry.forward.suffix && !normalized.toLowerCase().endsWith(entry.forward.suffix)) continue;
        const match = entry.forward.regex.exec(source.trim());
        if (match) return spacing(source, interpolate(entry.value, entry.forward.slots, match));
      }
    }
    return language === 'pt-BR' ? source : undefined;
  }
  function canonicalize(text, language) {
    const normalized = normalize(text);
    if (sourceKeys.has(normalized)) return text;
    const catalog = index(language);
    const reversed = catalog.reverse.get(normalized.toLowerCase());
    if (reversed?.size === 1) return spacing(text, [...reversed][0]);
    if (normalized.length <= 4000 && /\p{L}/u.test(normalized)) {
      for (const entry of catalog.templates) {
        if (entry.backward.prefix && !normalized.toLowerCase().startsWith(entry.backward.prefix) || entry.backward.suffix && !normalized.toLowerCase().endsWith(entry.backward.suffix)) continue;
        const match = entry.backward.regex.exec(String(text).trim());
        if (match) return spacing(text, interpolate(entry.canonicalSource, entry.backward.slots, match));
      }
    }
    return text;
  }
  function translate(pt, en, es, fr) {
    const language = locale();
    const found = lookup(pt, language);
    if (found !== undefined) return found;
    return ({ en, es, fr })[language] || pt;
  }
  window.pt2vhfI18n = { lookup, translate, canonicalize, locale, normalize };
})();
