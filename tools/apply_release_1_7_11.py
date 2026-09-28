from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.7.11":
    raise SystemExit(f"v1.7.11 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.7.11"'],
    "pt2vhf_aprs/static/css/app.css": [
        ".map-items-menu {",
        "position: fixed;",
        "z-index: 5000;",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "const positionMapItemsMenu = () => {",
        "const closeMapItemsMenu = () => {",
        "menu.classList.remove('hidden')",
        "requestAnimationFrame(positionMapItemsMenu)",
        "window.addEventListener('scroll', positionMapItemsMenu, true)",
    ],
    "tests/test_core.py": ["test_v1711_map_items_menu_not_clipped_and_opens"],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.7.11 validation failed: {needle!r} missing from {rel}")

print("v1.7.11 portable validation OK")
