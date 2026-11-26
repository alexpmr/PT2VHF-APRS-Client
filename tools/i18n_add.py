"""Acrescenta textos aos catálogos static/js/i18n/<idioma>.js.

Uso: python tools/i18n_add.py novos.json
novos.json = {"texto em português": {"en": "...", "es": "...", "fr": "...", "de-DE": "...", "it-IT": "...",
              "ja-JP": "...", "pl-PL": "...", "nl-NL": "...", "zh-CN": "...", "th-TH": "..."}}
Recusa entrada sem os 10 idiomas, para nenhum texto novo ficar sem tradução.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "pt2vhf_aprs" / "static" / "js" / "i18n"
LOCALES = ("en", "es", "fr", "de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN", "th-TH")


def add(entries: dict) -> None:
    for pt, values in entries.items():
        missing = [loc for loc in LOCALES if not str(values.get(loc) or "").strip()]
        if missing:
            raise SystemExit(f"{pt!r}: faltam {missing}")
    for locale in LOCALES:
        path = CATALOG_DIR / f"{locale}.js"
        text = path.read_text(encoding="utf-8")
        cut = text.index("] = ") + 4
        catalog = json.loads(text[cut:].strip().rstrip(";"))
        for pt, values in entries.items():
            catalog[pt] = values[locale]
        path.write_text(text[:cut] + json.dumps(catalog, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    add(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print("ok")
