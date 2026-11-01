"""Assemble a reviewable keyed catalog, rejecting broken interpolation drafts."""
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".test-runtime"
work = json.loads((WORK / "i18n-catalog-work.json").read_text(encoding="utf-8"))
draft_path = WORK / "i18n-local-drafts.json"
drafts = json.loads(draft_path.read_text(encoding="utf-8")) if draft_path.exists() else {}
catalogs = work["catalogs"]
for language, entries in json.loads((ROOT / "tools/i18n_translations.json").read_text(encoding="utf-8")).items():
    catalogs.setdefault(language, {}).update(entries)
findings = []
slots = re.compile(r"\{(?:v\d+|versao|link)\}")
TECH = set('APRS IS AX RF RX TX AIS TNC KISS AGWPE SSID DTR RTS PTT GPS TCP UDP USB HTTP HTTPS ACK REJ CQ BLN CPU RAM HEX PKT API DEM SNR RSSI MMSI IMO ETA CTCSS CSS HTML JSON CSV PDF GPX KML KMZ TXT SQLite OpenStreetMap RainViewer PT2VHF'.split())
UNITS = set('px baud bps mb gb mhz khz hz dbm db km m s ms min w v Âµv lat lon pixel'.split())
def invariant(key):
    if re.fullmatch(r'(?:https?://|www\.)\S+', key):
        return True
    words = ''.join(ch if ch.isalpha() else ' ' for ch in slots.sub('', key)).split()
    return bool(words) and all(word in TECH or word.lower() in UNITS for word in words)
for locale in ("en", "es", "fr", "de-DE", "it-IT"):
    catalog = catalogs.setdefault(locale, {})
    for key in work["keys"]:
        if invariant(key):
            catalog[key] = key
            continue
        if key in catalog:
            if Counter(slots.findall(key)) != Counter(slots.findall(catalog[key])):
                findings.append({'locale': locale, 'source': key, 'draft': catalog[key], 'issues': ['existing interpolation placeholders differ'], 'modules': work['sources'][key]})
            continue
        draft = drafts.get(locale, {}).get(key)
        if not draft:
            findings.append({"locale": locale, "source": key, "issues": ["missing translation"], "modules": work["sources"][key]})
            continue
        issues = list(draft["issues"])
        if Counter(slots.findall(key)) != Counter(slots.findall(draft["text"])):
            issues.append("interpolation placeholders differ")
        if issues:
            findings.append({"locale": locale, "source": key, "draft": draft["text"], "issues": issues, "modules": work["sources"][key]})
            continue
        catalog[key] = draft["text"]

result = {locale: dict(sorted(catalogs[locale].items())) for locale in ("pt-BR", "en", "es", "fr", "de-DE", "it-IT")}
for source, portuguese in list(result['pt-BR'].items()):
    if portuguese == source or portuguese in work['sources']:
        continue
    for locale in ('en','es','fr','de-DE','it-IT'):
        if source in result[locale]:
            result[locale].setdefault(portuguese, result[locale][source])
# Register unambiguous English UI wording as aliases. This also lets newly
# inserted text rendered in English switch back to Portuguese correctly.
english_sources = {}
for source, value in result['en'].items():
    if source != value:
        english_sources.setdefault(value, set()).add(source)
for english, originals in english_sources.items():
    if len(originals) != 1 or english in work['sources']:
        continue
    source = next(iter(originals))
    result['pt-BR'].setdefault(english, result['pt-BR'].get(source, source))
    for locale in ('es','fr','de-DE','it-IT'):
        if source in result[locale]:
            result[locale].setdefault(english, result[locale][source])
script = "/* Keyed UI catalogs. Generated for review from public source literals; no runtime translation service. */\n(() => {\n  'use strict';\n  const catalog = " + json.dumps(result, ensure_ascii=False, indent=2) + ";\n  window.PT2VHF_I18N ||= {};\n  for (const [locale, entries] of Object.entries(catalog)) Object.assign(window.PT2VHF_I18N[locale] ||= {}, entries);\n})();\n"
(WORK / 'i18n-built-catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT / "pt2vhf_aprs/static/js/i18n_catalog.js").write_text(script, encoding="utf-8")
report = {"sourceKeys": len(work["keys"]), "catalogKeys": {locale: len(entries) for locale, entries in result.items()}, "reviewFindings": findings}
(WORK / "i18n-catalog-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"sourceKeys": report["sourceKeys"], "catalogKeys": report["catalogKeys"], "reviewFindings": len(findings)}, indent=2))
