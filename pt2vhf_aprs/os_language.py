"""v2.0.5: idioma padrão = idioma do sistema operacional.

Enquanto o usuário não escolhe um idioma (Configuração ou seletor de bandeiras), o
aplicativo segue o idioma do SO. Idioma do SO que o app não tem vira inglês.
"""
from __future__ import annotations

import locale
import os
import subprocess
import sys
from functools import lru_cache

SUPPORTED = ("pt-BR", "en", "es", "fr", "de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN", "th-TH")
FALLBACK = "en"

_BY_PREFIX = {
    "pt": "pt-BR", "en": "en", "es": "es", "fr": "fr", "de": "de-DE", "it": "it-IT",
    "ja": "ja-JP", "pl": "pl-PL", "nl": "nl-NL", "zh": "zh-CN", "th": "th-TH",
}


def map_language(tag: str | None) -> str | None:
    """Converte 'pt_BR.UTF-8', 'de-AT', 'zh-Hans-CN', 'Portuguese_Brazil' etc. num idioma do app."""
    raw = str(tag or "").strip()
    if not raw or raw.upper() in {"C", "POSIX"} or raw.upper().startswith("C."):
        return None
    raw = raw.split(".")[0].split("@")[0].replace("_", "-")
    prefix = raw.split("-")[0].lower()
    if prefix in _BY_PREFIX:
        return _BY_PREFIX[prefix]
    # Nomes longos do Windows (locale.getlocale() devolve "Portuguese_Brazil").
    names = {"portuguese": "pt-BR", "english": "en", "spanish": "es", "french": "fr", "german": "de-DE",
             "italian": "it-IT", "japanese": "ja-JP", "polish": "pl-PL", "dutch": "nl-NL", "chinese": "zh-CN", "thai": "th-TH"}
    return names.get(prefix)


def _windows_ui_language() -> str | None:
    try:
        import ctypes
        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale.get(lcid)
    except Exception:
        return None


def _macos_language() -> str | None:
    try:
        out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True,
                             text=True, timeout=3).stdout
        for part in out.replace("(", " ").replace(")", " ").replace(",", " ").split():
            tag = part.strip().strip('"')
            if tag:
                return tag
    except Exception:
        return None
    return None


def _candidates() -> list[str]:
    found: list[str] = []
    override = os.environ.get("PT2VHF_LANGUAGE")
    if override:
        found.append(override)
    if sys.platform == "win32":
        found.append(_windows_ui_language() or "")
    elif sys.platform == "darwin":
        found.append(_macos_language() or "")
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var) or ""
        found.extend(value.split(":"))
    try:
        found.append(locale.getlocale()[0] or "")
    except Exception:
        pass
    return [item for item in found if item]


@lru_cache(maxsize=1)
def system_language() -> str:
    for tag in _candidates():
        mapped = map_language(tag)
        if mapped:
            return mapped
    return FALLBACK
