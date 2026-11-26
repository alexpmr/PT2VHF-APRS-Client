from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_FILES = list((ROOT / "pt2vhf_aprs" / "static" / "js").glob("*.js"))
HTML_FILES = list((ROOT / "pt2vhf_aprs" / "templates").glob("*.html"))

VISIBLE_HTML = re.compile(r">\s*([^<>{}\n][^<>{}\n]{2,120})\s*<")
IGNORE_HTML = re.compile(r"^(?:[\s\d.,:+\-×/%°–—→←↑↓|]+|KISS|AX\.25|APRS(?:-IS)?|RF|AIS|CSV|GeoJSON|KML|TNC/?RF|AGWPE)$", re.I)

CATALOG_DIR = ROOT / "pt2vhf_aprs" / "static" / "js" / "i18n"
# v2.0.7: um catálogo por idioma (static/js/i18n/<idioma>.js), no lugar dos 13 arquivos por versão.
EXTENDED_LANGUAGE_PACKS = {
    "de-DE": "de-DE.js",
    "it-IT": "it-IT.js",
    "ja-JP": "ja-JP.js",
    "pl-PL": "pl-PL.js",
    "nl-NL": "nl-NL.js",
    "zh-CN": "zh-CN.js",
    "th-TH": "th-TH.js",
}
# Lacuna herdada (26/11/2026): textos do catálogo espanhol ainda sem tradução nestes idiomas. O app usa o
# inglês nesses casos. O número só pode cair; subir quer dizer texto novo sem tradução.
KNOWN_MISSING_KEYS = {"ja-JP": 58, "pl-PL": 58, "nl-NL": 58, "zh-CN": 58}


def load_catalog(locale: str) -> dict[str, str]:
    """Lê static/js/i18n/<locale>.js (o corpo depois de "] = " é JSON puro)."""
    path = CATALOG_DIR / f"{locale}.js"
    text = path.read_text(encoding="utf-8")
    body = text[text.index("] = ") + 4:].strip().rstrip(";")
    data = json.loads(body)
    marker = f"window.PT2VHF_I18N = window.PT2VHF_I18N || {{}})['{locale}']"
    if marker not in text:
        raise ValueError(f"{path.name}: marcador do idioma ausente")
    return data


def _iter_tr_calls(text: str):
    index = 0
    while True:
        match = re.search(r"\btr\s*\(", text[index:])
        if not match:
            return
        start = index + match.start()
        pos = index + match.end()
        depth = 1
        quote = ""
        escaped = False
        while pos < len(text) and depth:
            ch = text[pos]
            if quote:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    quote = ""
            else:
                if ch in ("'", '"', "`"):
                    quote = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
            pos += 1
        if depth:
            yield text[start:], ""
            return
        yield text[start:pos], text[index + match.end():pos - 1]
        index = pos


def _split_js_args(raw: str) -> list[str]:
    args, buf = [], []
    quote = ""
    escaped = False
    depth = 0
    for ch in raw:
        if quote:
            buf.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            buf.append(ch)
        elif ch in "([{":
            depth += 1
            buf.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf or raw.strip():
        args.append("".join(buf).strip())
    return args


def _dictionary_keys() -> tuple[set[str], set[str]]:
    try:
        return set(load_catalog("es")), set(load_catalog("fr"))
    except (OSError, ValueError):
        return set(), set()


def _extended_pack_counts(expected_keys: int) -> tuple[dict[str, int], list[dict]]:
    counts: dict[str, int] = {}
    errors: list[dict] = []
    try:
        base = set(load_catalog("es"))
    except (OSError, ValueError):
        base = set()
    for locale, filename in EXTENDED_LANGUAGE_PACKS.items():
        try:
            catalog = load_catalog(locale)
        except FileNotFoundError:
            counts[locale] = 0
            errors.append({"locale": locale, "file": filename, "error": "missing_file"})
            continue
        except ValueError as exc:
            counts[locale] = 0
            errors.append({"locale": locale, "file": filename, "error": "invalid_catalog", "detail": str(exc)})
            continue
        counts[locale] = len(catalog)
        empty = [key for key, value in catalog.items() if not str(value).strip()]
        if empty:
            errors.append({"locale": locale, "file": filename, "error": "empty_translation",
                           "keys": empty[:20], "count": len(empty)})
        missing = sorted(base - set(catalog))
        if len(missing) > KNOWN_MISSING_KEYS.get(locale, 0):
            errors.append({"locale": locale, "file": filename, "error": "catalog_size_mismatch",
                           "expected": expected_keys, "actual": len(catalog), "missing": missing[:30]})
    return counts, errors


def _silent_english_fallbacks() -> list[dict]:
    """Detect the regression that caused non-English locales to display English."""
    findings: list[dict] = []
    patterns = [
        re.compile(r"EXTRA_I18N\[[^\]]+\]\?\.\[[^\]]+\]\s*\|\|\s*EN_TEXT"),
        re.compile(r"PT2VHF_I18N\?\.\[[^\]]+\]\?\.\[[^\]]+\]\s*\|\|\s*en\b"),
        re.compile(r"extended\s*\)\s*return\s+extended;\s*return\s+en\b", re.S),
    ]
    for path in JS_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            for match in pattern.finditer(text):
                findings.append({
                    "file": str(path.relative_to(ROOT)),
                    "snippet": match.group(0)[:180],
                })
    return findings


def _release_patch_locales() -> dict[str, bool]:
    locales = ["es", "fr", "de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN", "th-TH"]
    return {locale: (CATALOG_DIR / f"{locale}.js").exists() for locale in locales}


def _main_ui_literal_keys() -> set[str]:
    """Collect static source phrases from ui('pt', 'en') for coverage reporting (diagnostic only)."""
    source = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(
        encoding="utf-8", errors="replace"
    )
    pattern = re.compile(r"""\bui\s*\(\s*(['"])((?:\\.|(?!\1)[^\\])*)\1""")
    return {match.group(2) for match in pattern.finditer(source)}


def audit() -> dict:
    malformed = []
    tr_count = 0
    for path in JS_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        expected_args = 4 if path.name in {"v190.js", "v110.js", "v111.js", "v142.js"} else 1
        for snippet, raw_args in _iter_tr_calls(text):
            args = _split_js_args(raw_args)
            tr_count += 1
            if len(args) < expected_args:
                malformed.append({
                    "file": str(path.relative_to(ROOT)),
                    "snippet": snippet[:180],
                    "args": len(args),
                    "expected_min_args": expected_args,
                })

    hardcoded = []
    for path in HTML_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in VISIBLE_HTML.finditer(text):
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            if not value or "{{" in value or "{%" in value or IGNORE_HTML.match(value):
                continue
            if re.search(r"[A-Za-zÀ-ÿ]{3,}", value):
                hardcoded.append({"file": str(path.relative_to(ROOT)), "text": value[:160]})

    es_keys, fr_keys = _dictionary_keys()
    core_ui_keys = _main_ui_literal_keys()
    core_ui_missing_es = sorted(core_ui_keys - es_keys)
    core_ui_missing_fr = sorted(core_ui_keys - fr_keys)
    missing_es = sorted(fr_keys - es_keys)
    missing_fr = sorted(es_keys - fr_keys)
    dict_total = len(es_keys | fr_keys)
    extended_counts, extended_errors = _extended_pack_counts(len(es_keys))
    dict_coverage = 100.0 if not (missing_es or missing_fr) else round((dict_total * 2 - len(missing_es) - len(missing_fr)) * 100.0 / max(1, dict_total * 2), 2)
    coverage = 100.0 if tr_count and not malformed else (0.0 if not tr_count else round((tr_count - len(malformed)) * 100 / tr_count, 2))
    silent_english_fallbacks = _silent_english_fallbacks()
    release_patch_locales = _release_patch_locales()
    return {
        "tr_calls": tr_count,
        "malformed_tr_calls": malformed,
        "technical_coverage_percent": coverage,
        "dictionary_coverage_percent": dict_coverage,
        "main_ui_literal_count": len(core_ui_keys),
        "base_dictionary_missing_ui_count": {
            "es": len(core_ui_missing_es),
            "fr": len(core_ui_missing_fr),
        },
        "base_dictionary_missing_ui_examples": {
            "es": core_ui_missing_es[:50],
            "fr": core_ui_missing_fr[:50],
        },
        "note_on_core_ui_coverage": (
            "Diagnostic only: app.js has its own English table and some texts are technical; "
            "a browser audit is required to determine visible untranslated UI."
        ),
        "missing_es_keys": missing_es,
        "missing_fr_keys": missing_fr,
        "extended_language_pack_counts": extended_counts,
        "extended_language_pack_errors": extended_errors,
        "silent_english_fallbacks": silent_english_fallbacks,
        "release_patch_locales": release_patch_locales,
        "hardcoded_visible_candidates": hardcoded,
        "hardcoded_candidate_count": len(hardcoded),
    }


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    strict = "--strict" in sys.argv
    if strict and (
        result["malformed_tr_calls"]
        or result["missing_es_keys"]
        or result["missing_fr_keys"]
        or result["extended_language_pack_errors"]
        or result["silent_english_fallbacks"]
        or not all(result["release_patch_locales"].values())
    ):
        raise SystemExit(1)
