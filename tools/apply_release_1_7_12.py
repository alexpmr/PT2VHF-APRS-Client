from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.12":
    raise SystemExit(f"v1.7.12 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.12"'],
    "pt2vhf_aprs/static/js/app.js": [
        "createPane('pt2vhfVisualPane')",
        "createPane('pt2vhfMarkerPane')",
        "visualPane.style.pointerEvents = 'none'",
        "markerPane.style.pointerEvents = 'auto'",
        "pane: 'pt2vhfMarkerPane'",
        "pane: 'pt2vhfVisualPane'",
        "zIndexOffset: 1200",
        "zIndexOffset: 1400",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".leaflet-pane.pt2vhf-visual-pane { pointer-events: none !important; }",
        ".leaflet-pane.pt2vhf-marker-pane { pointer-events: auto !important; }",
        ".aprs-marker-wrap { background: transparent; border: 0; pointer-events: auto !important; cursor: pointer; }",
        ".aprs-object-marker-wrap { background: transparent; border: 0; pointer-events: auto !important; cursor: pointer; }",
    ],
    "tests/test_core.py": ["test_v1712_clickable_markers_use_dedicated_pane"],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.12 validation failed: {needle!r} missing from {rel}")

print("v1.7.12 portable validation OK")
