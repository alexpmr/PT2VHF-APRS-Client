from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

def version_tuple(value: str) -> tuple[int, ...]:
    parts = []
    for piece in str(value or "").strip().lstrip("vV").split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            break
    return tuple(parts or [0])

if version_tuple(version) < (1, 6, 23):
    raise SystemExit(f"v1.6.23 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/static/js/app.js": [
        "mapLegendCollapsed: localStorage.getItem(",
        "function syncMapLegendCollapsed()",
    ],
    "pt2vhf_aprs/static/css/app.css": [
        ".map-legend-toggle",
    ],
    "windows/make_icon.py": [
        "app_logo.png",
    ],
    "linux/build_linux.sh": [
        "app_logo.png",
    ],
    "tools/generate_manual.py": [
        "app_logo.png",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.23 validation failed: {needle!r} missing from {rel}")

logo_png = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"
if not logo_png.exists() or logo_png.stat().st_size < 5000:
    raise SystemExit("v1.6.23 validation failed: application logo asset missing or invalid")

print("v1.6.23 branding/legend validation OK")
