/* Exact catalog matches only. Received/user content must use translate="no". */
(() => {
  'use strict';
  window.pt2vhfCreateDomTranslator = (lookup) => {
    const texts = new WeakMap();
    const attributes = new WeakMap();
    const ignored = el => !el || !!el.closest('script,style,code,textarea,[translate="no"],.notranslate,[data-i18n-skip]');
    function translateValue(current, previous) {
      // An external update replaces the source; never resurrect a stale status.
      const source = previous && current === previous.output ? previous.source : current;
      const key = source.trim();
      const value = lookup(key);
      const output = value == null ? source : source.slice(0, source.length - source.trimStart().length) + value + source.slice(source.trimEnd().length);
      return { source, output };
    }
    function translate(root) {
      if (!root) return;
      const nodes = [];
      if (root.nodeType === Node.TEXT_NODE) nodes.push(root);
      else {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) nodes.push(walker.currentNode);
      }
      for (const node of nodes) {
        if (ignored(node.parentElement)) continue;
        const entry = translateValue(node.nodeValue, texts.get(node));
        texts.set(node, entry);
        if (node.nodeValue !== entry.output) node.nodeValue = entry.output;
      }
      const elements = root.nodeType === Node.ELEMENT_NODE ? [root, ...root.querySelectorAll('*')] : [];
      for (const el of elements) {
        if (ignored(el)) continue;
        let entries = attributes.get(el);
        if (!entries) attributes.set(el, entries = new Map());
        for (const attr of ['placeholder', 'title', 'aria-label']) {
          if (!el.hasAttribute(attr)) { entries.delete(attr); continue; }
          const current = el.getAttribute(attr);
          const entry = translateValue(current, entries.get(attr));
          entries.set(attr, entry);
          if (current !== entry.output) el.setAttribute(attr, entry.output);
        }
      }
    }
    const observer = new MutationObserver(records => {
      const roots = new Set();
      for (const record of records) {
        if (record.type === 'childList') record.addedNodes.forEach(node => roots.add(node));
        else roots.add(record.target);
      }
      roots.forEach(translate);
    });
    return {
      translate,
      observe(root) { observer.observe(root, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['placeholder', 'title', 'aria-label'] }); },
      disconnect() { observer.disconnect(); }
    };
  };
})();
