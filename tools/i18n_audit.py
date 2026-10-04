from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_FILES = list((ROOT / "pt2vhf_aprs" / "static" / "js").glob("*.js"))
HTML_FILES = list((ROOT / "pt2vhf_aprs" / "templates").glob("*.html"))

TR_CALL = re.compile(r"\btr\(([^\n;]{1,800})\)")
VISIBLE_HTML = re.compile(r">\s*([^<>{}\n][^<>{}\n]{2,120})\s*<")
IGNORE_HTML = re.compile(r"^(?:[\s\d.,:+\-×/%°–—→←↑↓|]+|KISS|AX\.25|APRS(?:-IS)?|RF|AIS|CSV|GeoJSON|KML|TNC/?RF|AGWPE)$", re.I)


def _split_args(raw: str) -> list[str]:
    try:
        node = ast.parse(f"f({raw})", mode="eval")
        call = node.body
        if isinstance(call, ast.Call):
            return [ast.get_source_segment(f"f({raw})", arg) or "" for arg in call.args]
    except Exception:
        return []
    return []


def audit() -> dict:
    malformed = []
    tr_count = 0
    for path in JS_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in TR_CALL.finditer(text):
            args = _split_args(match.group(1))
            tr_count += 1
            if len(args) < 4:
                malformed.append({"file": str(path.relative_to(ROOT)), "snippet": match.group(0)[:180], "args": len(args)})

    hardcoded = []
    for path in HTML_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in VISIBLE_HTML.finditer(text):
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            if not value or "{{" in value or "{%" in value or IGNORE_HTML.match(value):
                continue
            if re.search(r"[A-Za-zÀ-ÿ]{3,}", value):
                hardcoded.append({"file": str(path.relative_to(ROOT)), "text": value[:160]})

    coverage = 100.0 if tr_count and not malformed else (0.0 if not tr_count else round((tr_count - len(malformed)) * 100 / tr_count, 2))
    return {
        "tr_calls": tr_count,
        "malformed_tr_calls": malformed,
        "technical_coverage_percent": coverage,
        "hardcoded_visible_candidates": hardcoded,
        "hardcoded_candidate_count": len(hardcoded),
    }


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    strict = "--strict" in sys.argv
    if strict and result["malformed_tr_calls"]:
        raise SystemExit(1)
