"""Catálogos de tradução da v2.0.7 em diante: um arquivo por idioma em static/js/i18n/."""
import json
from pathlib import Path

CATALOG_DIR = Path(__file__).resolve().parent.parent / "pt2vhf_aprs" / "static" / "js" / "i18n"
LOCALES = ("es", "fr", "de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN", "en", "th-TH")


def catalog(locale: str) -> dict:
    text = (CATALOG_DIR / f"{locale}.js").read_text(encoding="utf-8")
    return json.loads(text[text.index("] = ") + 4:].strip().rstrip(";"))


def all_text() -> str:
    return "\n".join((CATALOG_DIR / f"{locale}.js").read_text(encoding="utf-8") for locale in LOCALES)
