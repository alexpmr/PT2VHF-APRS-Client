from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "windows" / "app_icon.ico"


def _font(size: int, bold: bool = True):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for name in candidates:
        path = Path(name)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, minimum: int = 20):
    size = start
    while size >= minimum:
        font = _font(size, True)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=max(1, size // 18))
        if box[2] - box[0] <= max_width:
            return font
        size -= 2
    return _font(minimum, True)


def draw_identity(size: int = 1024) -> Image.Image:
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    cx = size // 2
    top = int(size * 0.16)
    bottom = int(size * 0.84)
    left = int(size * 0.06)
    right = int(size * 0.94)

    # Moldura e oceano.
    draw.ellipse((left, top, right, bottom), fill=(3, 35, 78, 255))
    inset = int(size * 0.018)
    draw.ellipse((left + inset, top + inset, right - inset, bottom - inset), fill=(245, 249, 252, 255))
    inset2 = int(size * 0.035)
    globe = (left + inset2, top + inset2, right - inset2, bottom - inset2)
    draw.ellipse(globe, fill=(8, 92, 171, 255))

    # Grade geográfica simplificada.
    gx0, gy0, gx1, gy1 = globe
    grid = (210, 239, 255, 150)
    width = max(2, size // 220)
    for frac in (0.25, 0.5, 0.75):
        y = int(gy0 + (gy1 - gy0) * frac)
        draw.line((gx0 + 15, y, gx1 - 15, y), fill=grid, width=width)
    for frac in (0.22, 0.38, 0.5, 0.62, 0.78):
        x = int(gx0 + (gx1 - gx0) * frac)
        rx = int((gx1 - gx0) * (0.07 + abs(frac - 0.5) * 0.20))
        draw.ellipse((x - rx, gy0, x + rx, gy1), outline=grid, width=width)

    # Continentes estilizados para manter legibilidade em tamanhos pequenos.
    land = (246, 249, 250, 255)
    draw.polygon([
        (int(size*.16), int(size*.36)), (int(size*.23), int(size*.29)), (int(size*.32), int(size*.31)),
        (int(size*.38), int(size*.38)), (int(size*.33), int(size*.45)), (int(size*.27), int(size*.47)),
        (int(size*.25), int(size*.55)), (int(size*.20), int(size*.51))
    ], fill=land)
    draw.polygon([
        (int(size*.32), int(size*.50)), (int(size*.39), int(size*.55)), (int(size*.40), int(size*.64)),
        (int(size*.35), int(size*.75)), (int(size*.31), int(size*.66))
    ], fill=land)
    draw.polygon([
        (int(size*.47), int(size*.35)), (int(size*.57), int(size*.29)), (int(size*.74), int(size*.32)),
        (int(size*.84), int(size*.42)), (int(size*.77), int(size*.50)), (int(size*.64), int(size*.46)),
        (int(size*.56), int(size*.51)), (int(size*.49), int(size*.45))
    ], fill=land)
    draw.polygon([
        (int(size*.54), int(size*.49)), (int(size*.63), int(size*.52)), (int(size*.67), int(size*.62)),
        (int(size*.61), int(size*.72)), (int(size*.55), int(size*.67)), (int(size*.51), int(size*.57))
    ], fill=land)
    draw.polygon([
        (int(size*.75), int(size*.65)), (int(size*.83), int(size*.64)), (int(size*.87), int(size*.70)),
        (int(size*.82), int(size*.75)), (int(size*.76), int(size*.72))
    ], fill=land)

    def center_text(text: str, y: int, max_width: int, start: int, stroke: int):
        font = fit_font(draw, text, max_width, start)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        x = cx - (box[2] - box[0]) // 2
        # sombra
        draw.text((x + stroke, y + stroke * 2), text, font=font, fill=(0, 20, 40, 190),
                  stroke_width=stroke, stroke_fill=(0, 20, 40, 190))
        draw.text((x, y), text, font=font, fill=(231, 13, 25, 255),
                  stroke_width=stroke, stroke_fill=(255, 255, 255, 255))

    center_text("PT2VHF", int(size * 0.20), int(size * 0.55), int(size * 0.095), max(2, size // 180))
    center_text("APRS", int(size * 0.39), int(size * 0.78), int(size * 0.22), max(3, size // 125))
    center_text("CLIENT", int(size * 0.67), int(size * 0.52), int(size * 0.085), max(2, size // 190))
    return img


img = draw_identity()
img.save(
    OUTPUT,
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(OUTPUT)
