"""Flag likely wrong-language prose and lost negation for linguistic review."""
import json
from pathlib import Path
import re
from lingua import Language, LanguageDetectorBuilder

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.test-runtime'
work = json.loads((WORK / 'i18n-catalog-work.json').read_text(encoding='utf-8'))
catalogs = json.loads((WORK / 'i18n-built-catalog.json').read_text(encoding='utf-8'))
languages = {'pt-BR': Language.PORTUGUESE, 'en': Language.ENGLISH, 'es': Language.SPANISH, 'fr': Language.FRENCH, 'de-DE': Language.GERMAN, 'it-IT': Language.ITALIAN}
detector = LanguageDetectorBuilder.from_languages(*languages.values()).build()
technical = re.compile(r'https?://\S+|www\.\S+|<[^>]+>|\{[^}]+\}|\b(?:PT2VHF|APRS(?:-IS)?|AX\.25|TNC|KISS|RF|RX|TX|AIS|SSID|TCP|UDP|USB|Windows|Linux|macOS|SQLite|GPS|ACK|REJ|DTR|RTS|PTT)\b')
negative = {
 'en':r'unsaved|unidentified|unsupported|unauthorized|offline|not|no|without|never|cannot|unavailable|invalid|fail|disconnect|incomplete|unknown|unverified|unread|disabled|independent|wireless|omit|N/A',
 'es':r'no|sin|nunca|ning[uú]n|inv[aá]l|desconect|fall|incomplet|desconoci|desactiv|independ|inal[aá]mbric|omitir|N/A',
 'fr':r'introuvable|pas|ne|aucun|sans|jamais|impossible|inval|d[eé]connect|[eé]chou|incomplet|inconnu|indisponible|non|d[eé]sactiv|ind[eé]pend|omet|N/A',
 'de-DE':r'ungespeichert|unverifiziert|nein|unbefugt|nicht|kein|ohne|niemals|ung[uü]lt|getrennt|fehl|unbekannt|unvollst[aä]ndig|ungeles|unbest[aä]tigt|deaktiviert|unabh[aä]ngig|drahtlos|auslass|N/A',
 'it-IT':r'\bno\b|non|nessun|senza|mai|impossibile|inval|disconness|errore|incomplet|sconosci|disabilit|indipendent|wireless|omet|N/A'
}
findings = []
english_sources = []
for source in work['keys']:
    for locale, expected in languages.items():
        text = catalogs.get(locale, {}).get(source, source if locale == 'pt-BR' else '')
        clean = technical.sub(' ', re.sub(r'CyclOSM|HOT|OSM\.DE|ÖPNVKarte|OpenTopoMap|Esri World Imagery|OpenStreetMap|RainViewer|DEM|Terrarium', ' ', text))
        words = re.findall(r'[A-Za-zÀ-ÿ]{2,}', clean)
        if len(words) >= 5:
            scores = detector.compute_language_confidence_values(clean)
            best = scores[0]
            actual = next(score.value for score in scores if score.language == expected)
            if best.language != expected and best.value >= .8 and actual < .15:
                findings.append({'kind':'wrong-language-prose','locale':locale,'source':source,'text':text,'detected':best.language.name,'confidence':round(best.value,3),'expectedConfidence':round(actual,3),'modules':work['sources'][source]})
                if locale == 'pt-BR' and best.language == Language.ENGLISH:
                    english_sources.append(source)
        if locale != 'pt-BR' and re.search(r'\b(?:não|nenhuma?|nunca|sem)\b', source, re.I) and text and not re.search(negative[locale], text, re.I):
            findings.append({'kind':'check-negation','locale':locale,'source':source,'text':text,'modules':work['sources'][source]})
(WORK / 'i18n-language-review.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
(WORK / 'i18n-english-sources.json').write_text(json.dumps(english_sources,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'languageFindings':sum(row['kind']=='wrong-language-prose' for row in findings),'negationReview':sum(row['kind']=='check-negation' for row in findings),'englishSourcesInPortuguese':len(english_sources)},indent=2))
