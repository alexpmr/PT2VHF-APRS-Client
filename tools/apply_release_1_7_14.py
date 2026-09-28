from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.14":
    raise SystemExit(f"v1.7.14 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.14"'],
    "pt2vhf_aprs/static/js/app.js": [
        "const objectHasSymbol = !!String(object.symbol || '').trim();",
        "aprsSymbolHtml(object.symbol_table || '/', object.symbol, 24)",
        "Versão atualizada",
        "Versão ${data.latest_version} disponível",
        "30 * 60 * 1000",
        "createPane('pt2vhfVisualPane')",
        "createPane('pt2vhfMarkerPane')",
        "options.duration || 1000",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        "animation: stationTxPulse 1s ease-out;",
        "animation: stationTxRing 1s ease-out forwards;",
        ".aprs-object-marker-wrap.station-transmitting .aprs-object-marker",
        ".leaflet-pane.pt2vhf-visual-pane { pointer-events: none !important; }",
        ".leaflet-pane.pt2vhf-marker-pane { pointer-events: auto !important; }",
    ],
    "tests/test_core.py": [
        "test_v1713_object_symbols_activity_and_version_status",
        "test_v1712_clickable_markers_use_dedicated_pane",
    ],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.14 validation failed: {needle!r} missing from {rel}")

js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
if ".setContent('APRS-IS')" in js:
    raise SystemExit("v1.7.14 validation failed: APRS-IS tooltip still present")
if '<div class="aprs-object-marker">◆</div>' in js:
    raise SystemExit("v1.7.14 validation failed: fixed orange object diamond still present")

print("v1.7.14 full release validation OK")
