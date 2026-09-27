from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "macos" / "app_icon.icns"


def font(size: int):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for name in candidates:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def fit(draw, text, max_width, start):
    size = start
    while size >= 26:
        f = font(size)
        box = draw.textbbox((0, 0), text, font=f, stroke_width=max(2, size // 20))
        if box[2] - box[0] <= max_width:
            return f
        size -= 2
    return font(26)


def centered(draw, text, y, max_width, start, stroke):
    f = fit(draw, text, max_width, start)
    box = draw.textbbox((0, 0), text, font=f, stroke_width=stroke)
    x = 512 - (box[2] - box[0]) // 2
    draw.text((x + stroke, y + stroke * 2), text, font=f, fill=(0, 18, 38, 190),
              stroke_width=stroke, stroke_fill=(0, 18, 38, 190))
    draw.text((x, y), text, font=f, fill=(232, 14, 25, 255),
              stroke_width=stroke, stroke_fill=(255, 255, 255, 255))


img = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
d = ImageDraw.Draw(img)
d.rounded_rectangle((60, 95, 964, 929), radius=220, fill=(248, 250, 252, 255))
d.ellipse((58, 178, 966, 846), fill=(3, 33, 75, 255))
d.ellipse((78, 198, 946, 826), fill=(247, 250, 252, 255))
d.ellipse((96, 216, 928, 808), fill=(8, 91, 170, 255))
grid = (215, 241, 255, 150)
for y in (330, 420, 512, 604, 694):
    d.line((110, y, 914, y), fill=grid, width=4)
for box in ((420,216,604,808),(315,216,709,808),(210,216,814,808)):
    d.ellipse(box, outline=grid, width=4)
d.line((512, 220, 512, 804), fill=grid, width=4)
land = (247, 249, 250, 255)
d.polygon([(150,360),(220,300),(330,315),(390,390),(330,470),(250,475),(215,560),(165,510)], fill=land)
d.polygon([(325,505),(400,535),(420,635),(365,750),(315,650)], fill=land)
d.polygon([(470,350),(570,300),(735,330),(860,420),(780,500),(650,455),(560,520),(485,455)], fill=land)
d.polygon([(550,500),(655,530),(690,635),(620,735),(555,680),(515,575)], fill=land)
d.polygon([(770,650),(845,640),(890,700),(835,750),(780,720)], fill=land)
centered(d, "PT2VHF", 235, 600, 98, 6)
centered(d, "APRS", 425, 810, 225, 10)
centered(d, "CLIENT", 675, 570, 92, 6)
img.save(OUTPUT, format="ICNS")
print(OUTPUT)
