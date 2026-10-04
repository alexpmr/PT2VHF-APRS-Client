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


def audit() -> dict:
    malformed = []
    tr_count = 0
    for path in JS_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        for snippet, raw_args in _iter_tr_calls(text):
            args = _split_js_args(raw_args)
            tr_count += 1
            if len(args) < 4:
                malformed.append({"file": str(path.relative_to(ROOT)), "snippet": snippet[:180], "args": len(args)})

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
    missing_es = sorted(fr_keys - es_keys)
    missing_fr = sorted(es_keys - fr_keys)
    dict_total = len(es_keys | fr_keys)
    dict_coverage = 100.0 if not (missing_es or missing_fr) else round((dict_total * 2 - len(missing_es) - len(missing_fr)) * 100.0 / max(1, dict_total * 2), 2)
    coverage = 100.0 if tr_count and not malformed else (0.0 if not tr_count else round((tr_count - len(malformed)) * 100 / tr_count, 2))
    return {
        "tr_calls": tr_count,
        "malformed_tr_calls": malformed,
        "technical_coverage_percent": coverage,
        "dictionary_coverage_percent": dict_coverage,
        "missing_es_keys": missing_es,
        "missing_fr_keys": missing_fr,
        "hardcoded_visible_candidates": hardcoded,
        "hardcoded_candidate_count": len(hardcoded),
    }


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    strict = "--strict" in sys.argv
    if strict and (result["malformed_tr_calls"] or result["missing_es_keys"] or result["missing_fr_keys"]):
        raise SystemExit(1)
