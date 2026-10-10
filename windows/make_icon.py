from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.compact_icon import render_compact_icon

SOURCE = ROOT / "pt2vhf_aprs" / "static" / "img" / "aprs_taskbar_icon.png"
OUTPUT = ROOT / "windows" / "app_icon.ico"

if SOURCE.exists():
    canvas = Image.open(SOURCE).convert("RGBA").resize((1024, 1024), Image.Resampling.LANCZOS)
else:
    canvas = render_compact_icon(1024)

canvas.save(
    OUTPUT,
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(OUTPUT)
