from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_DIR = ROOT / "pt2vhf_aprs" / "static" / "js"
HTML_FILES = list((ROOT / "pt2vhf_aprs" / "templates").glob("*.html"))
RUNTIME_CATALOG = JS_DIR / "i18n_runtime.js"

EXTENDED_LANGUAGE_PACKS = {
    "de-DE": "i18n_de.js",
    "it-IT": "i18n_it.js",
    "ja-JP": "i18n_ja.js",
    "pl-PL": "i18n_pl.js",
    "nl-NL": "i18n_nl.js",
    "zh-CN": "i18n_zh.js",
}
SUPPORTED_LOCALES = ("en", "es", "fr", *EXTENDED_LANGUAGE_PACKS.keys())
CALL_BY_FILE = {
    "app.js": ("ui", 2),
    "tnc.js": ("tr", 1),
    "v110.js": ("tr", 4),
    "v111.js": ("tr", 4),
    "v142.js": ("tr", 4),
    "v1818.js": ("t", 4),
    "v190.js": ("tr", 4),
}

VISIBLE_HTML = re.compile(r">[\t ]*([^<>{}\n][^<>{}\n]{1,500})[\t ]*<")
VISIBLE_ATTR = re.compile(r'(?:placeholder|title|aria-label)="([^"{][^"]{1,500})"')
NATIVE_LANGUAGE_LABELS = {
    "Português", "English", "Español", "Français", "Deutsch",
    "Italiano", "日本語", "Polski", "Nederlands", "简体中文",
}
TECHNICAL_EXACT = re.compile(
    r"^(?:PT2VHF APRS Client|CPU|RAM|TNC|RF|APRS(?:-IS)?|AX\.25|KISS|"
    r"KISS TCP|KISS Serial|AGWPE TCP|OSM|OSM\.DE|CyclOSM|ÖPNVKarte|"
    r"ASCII|HEX|CSV|KML|GeoJSON|RX|TX|Dir\.|SSID|MMSI|QRZ\.com|"
    r"OpenStreetMap|ACK/REJ|CALL-SSID|PKT|VID:PID|USB Serial — CH9102)$",
    re.I,
)
CALLSIGN = re.compile(
    r"^(?:(?:PP|PQ|PR|PS|PT|PU|PV|PW|PX|PY|ZV|ZW|ZX|ZY|ZZ)"
    r"\d[A-Z0-9]{1,4}(?:-\d{1,2})?|BLN\d|COM\d+|WIDE\d-\d)$",
    re.I,
)


def _decode_js_literal(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\r", "\r")
        .replace("\\t", "\t")
        .replace("\\'", "'")
        .replace('\\"', '"')
        .replace("\\\\", "\\")
    )


def _iter_calls(text: str, function_name: str):
    index = 0
    call_re = re.compile(rf"\b{re.escape(function_name)}\s*\(")
    while True:
        match = call_re.search(text, index)
        if not match:
            return
        start = match.start()
        pos = match.end()
        depth = 1
        quote = ""
        escaped = False
        template_expr_depth = 0
        while pos < len(text) and depth:
            ch = text[pos]
            if quote:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif quote == "`" and ch == "$" and pos + 1 < len(text) and text[pos + 1] == "{":
                    template_expr_depth += 1
                    pos += 1
                elif quote == "`" and template_expr_depth:
                    if ch == "{":
                        template_expr_depth += 1
                    elif ch == "}":
                        template_expr_depth -= 1
                elif ch == quote and not template_expr_depth:
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
        yield text[start:pos], text[match.end():pos - 1]
        index = pos


def _split_js_args(raw: str) -> list[str]:
    args, buf = [], []
    quote = ""
    escaped = False
    depth = 0
    template_depth = 0
    i = 0
    while i < len(raw):
        ch = raw[i]
        if quote:
            buf.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif quote == "`" and ch == "$" and i + 1 < len(raw) and raw[i + 1] == "{":
                template_depth += 1
                buf.append("{")
                i += 1
            elif quote == "`" and template_depth:
                if ch == "{":
                    template_depth += 1
                elif ch == "}":
                    template_depth -= 1
            elif ch == quote and not template_depth:
                quote = ""
            i += 1
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
        i += 1
    if buf or raw.strip():
        args.append("".join(buf).strip())
    return args


def _literal_source(arg: str) -> str | None:
    arg = arg.strip()
    if len(arg) < 2 or arg[0] not in ("'", '"', "`") or arg[-1] != arg[0]:
        return None
    body = arg[1:-1]
    if arg[0] == "`":
        counter = 0

        def repl(_match: re.Match) -> str:
            nonlocal counter
            token = f"__ARG{counter}__"
            counter += 1
            return token

        body = re.sub(r"\$\{[^{}]*\}", repl, body)
    return _decode_js_literal(body)


def _object_keys(block: str) -> set[str]:
    key_re = re.compile(r'^\s*["\']((?:[^"\'\\]|\\.)+)["\']\s*:', re.M)
    return {_decode_js_literal(value) for value in key_re.findall(block)}


def _base_dictionary_keys() -> tuple[set[str], set[str]]:
    text = (JS_DIR / "i18n_extra.js").read_text(encoding="utf-8", errors="replace")
    es_start = text.find("  es: {")
    fr_start = text.find("  fr: {", es_start + 1)
    if es_start < 0 or fr_start < 0:
        return set(), set()
    return _object_keys(text[es_start:fr_start]), _object_keys(text[fr_start:])


def _english_keys() -> set[str]:
    text = (JS_DIR / "app.js").read_text(encoding="utf-8", errors="replace")
    start = text.find("const EN_TEXT")
    end = text.find("const LANGUAGE_META", start + 1)
    if start < 0 or end < 0:
        return set()
    return _object_keys(text[start:end])


def _runtime_catalog() -> tuple[dict[str, dict[str, str]], list[str]]:
    errors: list[str] = []
    if not RUNTIME_CATALOG.exists():
        return {}, ["missing_runtime_catalog"]
    text = RUNTIME_CATALOG.read_text(encoding="utf-8", errors="replace")
    begin = "/* PT2VHF_I18N_RUNTIME_BEGIN */"
    end = "/* PT2VHF_I18N_RUNTIME_END */"
    i = text.find(begin)
    j = text.find(end, i + len(begin))
    if i < 0 or j < 0:
        return {}, ["runtime_catalog_markers_missing"]
    payload = text[i + len(begin):j].strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        return {}, [f"runtime_catalog_json_invalid:{exc}"]
    for locale in SUPPORTED_LOCALES:
        values = data.get(locale)
        if not isinstance(values, dict):
            errors.append(f"runtime_locale_missing:{locale}")
            continue
        blank = [key for key, value in values.items() if not str(value).strip()]
        if blank:
            errors.append(f"runtime_blank_values:{locale}:{len(blank)}")
    return data, errors


def _extended_pack_counts(expected_keys: int) -> tuple[dict[str, int], list[dict]]:
    counts: dict[str, int] = {}
    errors: list[dict] = []
    value_re = re.compile(r'^"((?:[^"\\]|\\.)*)",?\s*$', re.M)
    for locale, filename in EXTENDED_LANGUAGE_PACKS.items():
        path = JS_DIR / filename
        if not path.exists():
            counts[locale] = 0
            errors.append({"locale": locale, "file": filename, "error": "missing_file"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        start = text.find("const values = [")
        end = text.find("];", start + 1)
        values = value_re.findall(text[start:end] if start >= 0 and end > start else "")
        counts[locale] = len(values)
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


def _is_translatable_source(value: str) -> bool:
    value = value.strip()
    if not value or value in NATIVE_LANGUAGE_LABELS:
        return False
    if not re.search(r"[A-Za-zÀ-ÿ\u3040-\u30ff\u3400-\u9fff]{2,}", value):
        return False
    if TECHNICAL_EXACT.match(value) or CALLSIGN.match(value):
        return False
    if re.match(r"^#[0-9A-Fa-f]{3,8}$", value):
        return False
    if re.match(r"^--\s*(?:MB|GB|%)$", value, re.I):
        return False
    if re.match(r"^(?:1200|2400|4800|9600|19200|38400|57600|115200|230400)\s*(?:baud|bps)$", value, re.I):
        return False
    if re.match(r"^\d+(?:[.,]\d+)?\s*min$", value, re.I):
        return False
    if re.match(r"^[0-9.,x% °/+\-]+$", value):
        return False
    if re.match(r"^(?:https?:|%LOCALAPPDATA%|[A-Za-z]:\\\\)", value):
        return False
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        return False
    return True


def _required_source_keys() -> tuple[set[str], list[dict], int]:
    required: set[str] = set()
    malformed: list[dict] = []
    call_count = 0

    for filename, (function_name, min_args) in CALL_BY_FILE.items():
        path = JS_DIR / filename
        text = path.read_text(encoding="utf-8", errors="replace")
        for snippet, raw_args in _iter_calls(text, function_name):
            args = _split_js_args(raw_args)
            call_count += 1
            if len(args) < min_args:
                malformed.append({
                    "file": str(path.relative_to(ROOT)),
                    "snippet": snippet[:180],
                    "args": len(args),
                    "expected_min_args": min_args,
                })
                continue
            source = _literal_source(args[0])
            if source and _is_translatable_source(source):
                required.add(source)

    for path in HTML_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in VISIBLE_HTML.finditer(text):
            value = html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())
            if "{{" in value or "{%" in value:
                continue
            if _is_translatable_source(value):
                required.add(value)
        for match in VISIBLE_ATTR.finditer(text):
            value = html.unescape(match.group(1).strip())
            if _is_translatable_source(value):
                required.add(value)
    return required, malformed, call_count


def _fallback_violations() -> list[str]:
    text = (JS_DIR / "app.js").read_text(encoding="utf-8", errors="replace")
    forbidden = (
        "EXTRA_I18N[state.language]?.[pt] || en",
        "EXTRA_I18N[state.language]?.[pt] || EN_TEXT",
        "EXTRA_I18N[state.language]?.[trimmed] || EN_TEXT",
        "EXTRA_I18N[state.language]?.[original] || EN_TEXT",
    )
    return [marker for marker in forbidden if marker in text]


def audit() -> dict:
    es_keys, fr_keys = _base_dictionary_keys()
    base_union = es_keys | fr_keys
    missing_es = sorted(fr_keys - es_keys)
    missing_fr = sorted(es_keys - fr_keys)
    extended_counts, extended_errors = _extended_pack_counts(len(es_keys))
    runtime, runtime_errors = _runtime_catalog()
    required, malformed, call_count = _required_source_keys()
    en_keys = _english_keys()

    missing_by_locale: dict[str, list[str]] = {}
    coverage_by_locale: dict[str, float] = {}
    for locale in SUPPORTED_LOCALES:
        if locale == "en":
            catalog = en_keys | set(runtime.get(locale, {}))
        else:
            catalog = base_union | set(runtime.get(locale, {}))
        missing = sorted(required - catalog)
        missing_by_locale[locale] = missing
        coverage_by_locale[locale] = round(
            (len(required) - len(missing)) * 100.0 / max(1, len(required)), 2
        )

    fallback_violations = _fallback_violations()
    return {
        "translation_calls": call_count,
        "malformed_translation_calls": malformed,
        "required_source_key_count": len(required),
        "base_es_key_count": len(es_keys),
        "base_fr_key_count": len(fr_keys),
        "english_key_count": len(en_keys),
        "missing_es_keys": missing_es,
        "missing_fr_keys": missing_fr,
        "extended_language_pack_counts": extended_counts,
        "extended_language_pack_errors": extended_errors,
        "runtime_catalog_counts": {locale: len(runtime.get(locale, {})) for locale in SUPPORTED_LOCALES},
        "runtime_catalog_errors": runtime_errors,
        "coverage_percent_by_locale": coverage_by_locale,
        "missing_catalog_keys_by_locale": missing_by_locale,
        "english_fallback_violations": fallback_violations,
    }


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    strict = "--strict" in sys.argv
    if strict and (
        result["malformed_translation_calls"]
        or result["missing_es_keys"]
        or result["missing_fr_keys"]
        or result["extended_language_pack_errors"]
        or result["runtime_catalog_errors"]
        or result["english_fallback_violations"]
        or any(result["missing_catalog_keys_by_locale"].values())
    ):
        raise SystemExit(1)
