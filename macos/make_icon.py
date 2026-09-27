from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"
OUTPUT = ROOT / "macos" / "app_icon.icns"

if not SOURCE.exists():
    raise SystemExit(f"Logo ausente: {SOURCE}")

img = Image.open(SOURCE).convert("RGBA")
img.load()
if img.width < 128 or img.height < 128:
    raise SystemExit(f"Logo com resolução insuficiente: {img.width}x{img.height}")

canvas = Image.new("RGBA", (1024, 1024), (255, 255, 255, 0))
fit = ImageOps.contain(img, (984, 984), method=Image.Resampling.LANCZOS)
canvas.alpha_composite(fit, ((1024 - fit.width) // 2, (1024 - fit.height) // 2))
canvas.save(OUTPUT, format="ICNS")
print(OUTPUT)
