from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"
OUTPUT = ROOT / "windows" / "app_icon.ico"

img = Image.open(SOURCE).convert("RGBA")
img = img.resize((256, 256), Image.Resampling.LANCZOS)
img.save(
    OUTPUT,
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(OUTPUT)
