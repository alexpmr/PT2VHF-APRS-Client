from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.6.24":
    raise SystemExit(f"v1.6.24 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.6.24"'],
    "pt2vhf_aprs/templates/index.html": ['type="image/png"', "img/app_logo.png"],
    "windows/make_icon.py": ['SOURCE = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"'],
    "linux/build_linux.sh": ['src = Path("pt2vhf_aprs/static/img/app_logo.png")'],
    "macos/make_icon.py": [
        'SOURCE = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"',
        "ImageOps.contain",
    ],
    "windows_app.py": ['"app_logo.png"'],
    ".github/workflows/build-windows.yml": [
        "cp pt2vhf_aprs/static/img/app_logo.png dist-docs/manual_logo.png",
        "apply_release_1_6_24.py",
    ],
    "tools/generate_manual.py": ['"app_logo.png"'],
    "pt2vhf_aprs/version_notes.py": ['"1.6.24"', '"1.6.23"'],
    "README.md": ["# PT2VHF APRS Client - v1.6.24", "fonte visual única"],
    "tests/test_core.py": [
        "test_v1624_official_logo_is_single_branding_source",
        "test_v1624_version_notes_include_1623_and_1624",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.24 validation failed: {needle!r} missing from {rel}")

html = (ROOT / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
workflow = (ROOT / ".github" / "workflows" / "build-windows.yml").read_text(encoding="utf-8")
mac_icon = (ROOT / "macos" / "make_icon.py").read_text(encoding="utf-8")
for text, label in ((html, "HTML"), (workflow, "workflow"), (mac_icon, "macOS icon generator")):
    if "app_logo.svg" in text:
        raise SystemExit(f"v1.6.24 validation failed: legacy SVG branding remains in {label}")

logo = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"
data = logo.read_bytes()
if len(data) < 5000 or data[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("v1.6.24 validation failed: official PNG logo missing/invalid")
if data[12:16] != b"IHDR":
    raise SystemExit("v1.6.24 validation failed: PNG has no IHDR header")
width, height = struct.unpack(">II", data[16:24])
if width < 256 or height < 128:
    raise SystemExit(f"v1.6.24 validation failed: logo resolution too small: {width}x{height}")

print(f"v1.6.24 official-logo consolidation validation OK ({width}x{height})")
