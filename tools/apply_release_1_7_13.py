from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.13":
    raise SystemExit(f"v1.7.13 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.13"'],
    "pt2vhf_aprs/static/js/app.js": [
        "const objectHasSymbol = !!String(object.symbol || '').trim();",
        "aprsSymbolHtml(object.symbol_table || '/', object.symbol, 24)",
        "options.duration || 1000",
        "Versão atualizada",
        "Versão ${data.latest_version} disponível",
        "30 * 60 * 1000",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        "animation: stationTxPulse 1s ease-out;",
        "animation: stationTxRing 1s ease-out forwards;",
        ".aprs-object-marker-wrap.station-transmitting .aprs-object-marker",
    ],
    "tests/test_core.py": ["test_v1713_object_symbols_activity_and_version_status"],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.13 validation failed: {needle!r} missing from {rel}")

js = (ROOT / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
if ".setContent('APRS-IS')" in js:
    raise SystemExit("v1.7.13 validation failed: APRS-IS tooltip still present")
if '<div class="aprs-object-marker">◆</div>' in js:
    raise SystemExit("v1.7.13 validation failed: fixed orange object diamond still present")

print("v1.7.13 portable validation OK")
