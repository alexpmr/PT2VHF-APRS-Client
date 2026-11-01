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

EXTENDED_LANGUAGE_PACKS = {
    "de-DE": "i18n_de.js",
    "it-IT": "i18n_it.js",
    "ja-JP": "i18n_ja.js",
    "pl-PL": "i18n_pl.js",
    "nl-NL": "i18n_nl.js",
    "zh-CN": "i18n_zh.js",
}


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
    path = ROOT / "pt2vhf_aprs" / "static" / "js" / "i18n_extra.js"
    text = path.read_text(encoding="utf-8", errors="replace")
    es_start = text.find("  es: {")
    fr_start = text.find("  fr: {", es_start + 1)
    if es_start < 0 or fr_start < 0:
        return set(), set()
    es_block = text[es_start:fr_start]
    fr_block = text[fr_start:]
    key_re = re.compile(r'^\s*"((?:[^"\\]|\\.)+)"\s*:', re.M)
    return set(key_re.findall(es_block)), set(key_re.findall(fr_block))


def _extended_pack_counts(expected_keys: int) -> tuple[dict[str, int], list[dict]]:
    counts: dict[str, int] = {}
    errors: list[dict] = []
    value_re = re.compile(r'^"((?:[^"\\]|\\.)*)",?\s*$', re.M)
    for locale, filename in EXTENDED_LANGUAGE_PACKS.items():
        path = ROOT / "pt2vhf_aprs" / "static" / "js" / filename
        if not path.exists():
            counts[locale] = 0
            errors.append({"locale": locale, "file": filename, "error": "missing_file"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        start = text.find("const values = [")
        end = text.find("];", start + 1)
        values = value_re.findall(text[start:end] if start >= 0 and end > start else "")
        counts[locale] = len(values)
        empty = [index for index, value in enumerate(values) if not value.strip()]
        if empty:
            errors.append({
                "locale": locale,
                "file": filename,
                "error": "empty_translation",
                "indexes": empty[:20],
                "count": len(empty),
            })
        if len(values) != expected_keys:
            errors.append({
                "locale": locale,
                "file": filename,
                "error": "catalog_size_mismatch",
                "expected": expected_keys,
                "actual": len(values),
            })
        marker = f"window.PT2VHF_I18N['{locale}']"
        if marker not in text:
            errors.append({"locale": locale, "file": filename, "error": "locale_marker_missing"})
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
    path = ROOT / "pt2vhf_aprs" / "static" / "js" / "i18n_v1425.js"
    locales = ["es", "fr", "de-DE", "it-IT", "ja-JP", "pl-PL", "nl-NL", "zh-CN"]
    if not path.exists():
        return {locale: False for locale in locales}
    text = path.read_text(encoding="utf-8", errors="replace")
    return {locale: (f"'{locale}':" in text or f"{locale}:" in text) for locale in locales}


def _main_ui_literal_keys() -> set[str]:
    """Collect static source phrases from ui('pt', 'en') for coverage reporting.

    A literal missing from the base dictionary may still be supplied by
    versioned patch catalogs, so this is diagnostic (not a strict CI failure).
    """
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
            "Diagnostic only: extra i18n patch catalogs may supply some missing literals; "
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
