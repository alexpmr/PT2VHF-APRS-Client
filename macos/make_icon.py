from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.compact_icon import render_compact_icon

# Logo oficial permanece em pt2vhf_aprs/static/img/app_logo.png.
SOURCE = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"
OUTPUT = ROOT / "macos" / "app_icon.icns"

canvas = render_compact_icon(1024)
canvas.save(OUTPUT, format="ICNS")
print(OUTPUT)
