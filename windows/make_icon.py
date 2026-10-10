from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "windows" / "aprs_taskbar_icon.png"
OUTPUT = ROOT / "windows" / "app_icon.ico"

source = Image.open(SOURCE).convert("RGBA")
canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
source.thumbnail((960, 960), Image.Resampling.LANCZOS)
offset = ((1024 - source.width) // 2, (1024 - source.height) // 2)
canvas.alpha_composite(source, offset)

canvas.save(
    OUTPUT,
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(OUTPUT)
