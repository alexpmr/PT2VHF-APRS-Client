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
    """Idioma da interface do Windows como tag BCP 47 ("es-419", "de-CH", "en-US").

    v2.0.7: antes só se consultava locale.windows_locale, que não conhece vários
    códigos (ex.: espanhol da América Latina 0x580A); o Windows então caía nas
    variáveis de ambiente e podia acabar em outro idioma. LCIDToLocaleName
    (Vista+, inclusive Win7) devolve o nome de qualquer LCID.
    """
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        lcid = int(kernel32.GetUserDefaultUILanguage())
    except Exception:
        return None
    try:
        buf = ctypes.create_unicode_buffer(85)
        if kernel32.LCIDToLocaleName(lcid, buf, len(buf), 0) and buf.value:
            return buf.value
    except Exception:
        pass
    return locale.windows_locale.get(lcid)


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


def _is_real_tag(tag: str) -> bool:
    raw = str(tag or "").strip().upper()
    return bool(raw) and raw not in {"C", "POSIX"} and not raw.startswith("C.")


@lru_cache(maxsize=1)
def system_language() -> str:
    """Idioma do app para o SO atual: o idioma do SO se suportado, senão inglês.

    v2.0.7: vale o PRIMEIRO idioma real encontrado (o da interface do SO). Se ele não
    é um dos suportados (russo, tcheco, sueco...), o app abre em inglês; antes a busca
    seguia para os candidatos seguintes (formato regional, variáveis de ambiente) e
    podia cair em outro idioma, como o português.
    """
    for tag in _candidates():
        if _is_real_tag(tag):
            return map_language(tag) or FALLBACK
    return FALLBACK
