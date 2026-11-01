"""Collect public UI literals and existing inline translations for review."""
from html.parser import HTMLParser
import ast
import json
from pathlib import Path
import re
from i18n_audit import _iter_tr_calls, _split_js_args

ROOT = Path(__file__).resolve().parents[1]
rows = []
literal = re.compile(r"^(['\"])(?:\\.|(?!\1).)*\1$", re.S)
for path in sorted((ROOT / "pt2vhf_aprs/static/js").glob("*.js")):
    if path.name.startswith("i18n_"):
        continue
    source = path.read_text(encoding="utf-8")
    source = re.sub(r"\b(?:ui|t)\s*\(", "tr(", source)
    for snippet, raw in _iter_tr_calls(source):
        args = _split_js_args(raw)
        if not args or not literal.fullmatch(args[0]):
            continue
        rows.append({"module": path.name, "args": [arg if literal.fullmatch(arg) else None for arg in args[:4]]})


class UIParser(HTMLParser):
    def __init__(self, module, owned_slots=None):
        super().__init__()
        self.module = module
        self.stack = []
        self.owned_slots = owned_slots or {}

    def add_text(self, value):
        owned = {key: info for key, info in self.owned_slots.items() if '{' + key + '}' in value}
        rows.append({"module": self.module, "text": value, "ownedSlots": owned})

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in {"input", "img", "br", "hr", "meta", "link", "source"}:
            self.stack.append(tag)
        for key in ("title", "placeholder", "aria-label"):
            value = attrs.get(key, "").strip()
            if value and "{{" not in value:
                self.add_text(value)

    def handle_endtag(self, tag):
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - self.stack[::-1].index(tag) - 1]

    def handle_data(self, data):
        value = data.strip()
        if value and not {"script", "style", "code"}.intersection(self.stack) and not any(token in value for token in ("{{", "{%")):
            self.add_text(value)


for path in sorted((ROOT / "pt2vhf_aprs/templates").glob("*.html")):
    UIParser(path.name).feed(path.read_text(encoding="utf-8"))
js_ast = ROOT / ".test-runtime/i18n-js-ast.json"
if js_ast.exists():
    for row in json.loads(js_ast.read_text(encoding="utf-8")):
        if "html" in row:
            UIParser(row["module"], row.get("ownedSlots")).feed(row["html"])
        else:
            rows.append(row)


def python_text(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        result, index = "", 0
        for value in node.values:
            if isinstance(value, ast.Constant):
                result += str(value.value)
            else:
                result += "{v" + str(index) + "}"
                index += 1
        return result
    return None


for path in sorted((ROOT / "pt2vhf_aprs").glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        values = []
        if isinstance(node, ast.Dict):
            values = [value for key, value in zip(node.keys, node.values) if isinstance(key, ast.Constant) and key.value in {"error", "message", "warning", "reason", "detail", "title", "classification_source", "description", "hint", "status_text", "friendly_name", "label"}]
        elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and node.exc.args:
            values = node.exc.args[:1]
        elif isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in {'message','reason','detail','description','hint','title','summary','warning','error','recommendation','status_text','label'} for target in node.targets):
            values = [node.value]
        elif isinstance(node, ast.Assign) and any(isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) and target.slice.value in {'classification_source', 'message', 'error', 'reason', 'description', 'hint', 'status_text'} for target in node.targets):
            values = [node.value]
        elif isinstance(node, ast.Return):
            candidates = node.value.elts if isinstance(node.value, ast.Tuple) else [node.value]
            values = [value for value in candidates if (text := python_text(value)) and (' ' in text or re.search('[ãõçáéíóú]', text)) and not text.startswith(('@echo ', '?APRS'))]
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'_error', 'ReleaseLookupError'}:
            values = node.args[1:] if node.func.id == 'ReleaseLookupError' else node.args
        for value in values:
            text = python_text(value)
            if text and len(text) < 2000 and re.search(r"[A-Za-zÀ-ÿ]{2}", re.sub(r"\{v\d+\}", "", text)):
                rows.append({"module": path.name, "kind": "server-ui-message", "text": text})
out = ROOT / ".test-runtime/i18n-source-literals.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Collected {len(rows)} UI literal occurrences in {out}")
