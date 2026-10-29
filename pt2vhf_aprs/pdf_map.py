"""Mapa de ruas (OpenStreetMap) por baixo dos desenhos dos PDFs de planejamento (v1.15.0).

Os tiles são baixados uma vez e guardados no computador; sem internet (ou se a maioria dos
tiles falhar) a função devolve None e o PDF usa o desenho esquemático de antes.
Atribuição obrigatória: "© OpenStreetMap contributors".
"""
from __future__ import annotations

import math
import urllib.request
from io import BytesIO
from pathlib import Path

from . import __version__

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "PT2VHF-APRS-Client/%s (+https://www.pt2vhf.com)" % __version__
MAX_TILES = 48


def _world_px(lat, lon, z):
    n = 256 * 2 ** z
    lat = max(-85.0511, min(85.0511, lat))
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def _http_tile(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


class BaseMap:
    """Imagem do mapa base recortada nos limites pedidos, com projeção lat/lon → pixel."""

    def __init__(self, image, z, x0, y0, scale):
        self.image, self.z, self.x0, self.y0, self.scale = image, z, x0, y0, scale

    def project(self, lat, lon):
        x, y = _world_px(lat, lon, self.z)
        return (x - self.x0) * self.scale, (y - self.y0) * self.scale

    def metres_per_px(self, lat):
        return 2 * math.pi * 6371000 * math.cos(math.radians(lat)) / (256 * 2 ** self.z) / self.scale


def render(bounds, width_px=1400, tile_dir=None, fetch=None):
    """BaseMap cobrindo bounds = (sul, oeste, norte, leste), ou None se não houver tiles."""
    try:
        from PIL import Image
    except ImportError:
        return None
    s, w, n, e = bounds
    fetch = fetch or _http_tile
    z = 3
    for zz in range(16, 2, -1):
        x0, y0 = _world_px(n, w, zz)
        x1, y1 = _world_px(s, e, zz)
        tiles = (int(x1 // 256) - int(x0 // 256) + 1) * (int(y1 // 256) - int(y0 // 256) + 1)
        if x1 - x0 <= width_px * 1.6 and tiles <= MAX_TILES:
            z = zz
            break
    x0, y0 = _world_px(n, w, z)
    x1, y1 = _world_px(s, e, z)
    tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
    canvas = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (238, 241, 244))
    total = ok = 0
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            total += 1
            data = None
            path = Path(tile_dir) / str(z) / str(tx) / ("%d.png" % ty) if tile_dir else None
            if path is not None and path.exists():
                data = path.read_bytes()
            if data is None:
                try:
                    data = fetch(TILE_URL.format(z=z, x=tx % 2 ** z, y=ty))
                except Exception:
                    continue
                if path is not None:
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(data)
                    except OSError:
                        pass
            try:
                canvas.paste(Image.open(BytesIO(data)).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
                ok += 1
            except Exception:
                continue
    if not total or ok < total * 0.6:
        return None
    crop = canvas.crop((int(x0 - tx0 * 256), int(y0 - ty0 * 256), int(x1 - tx0 * 256), int(y1 - ty0 * 256)))
    scale = width_px / max(1, crop.width)
    image = crop.resize((width_px, max(1, int(crop.height * scale))), Image.LANCZOS)
    return BaseMap(image, z, x0, y0, scale)


def attribution(base):
    from PIL import ImageDraw
    draw = ImageDraw.Draw(base.image)
    text = "© OpenStreetMap contributors"
    w, h = base.image.size
    draw.rectangle((w - 200, h - 18, w, h), fill=(255, 255, 255))
    draw.text((w - 195, h - 15), text, fill=(60, 60, 60))


def scale_bar(base, lat):
    from PIL import ImageDraw
    draw = ImageDraw.Draw(base.image)
    mpp = base.metres_per_px(lat)
    target = mpp * base.image.size[0] * 0.2
    nice = min((v for v in (100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000) if v >= target * 0.5), default=50000)
    bar = nice / mpp
    h = base.image.size[1]
    draw.rectangle((14, h - 30, 14 + bar + 12, h - 8), fill=(255, 255, 255))
    draw.rectangle((20, h - 16, 20 + bar, h - 12), fill=(22, 39, 59))
    draw.text((20, h - 28), ("%d km" % (nice // 1000)) if nice >= 1000 else "%d m" % nice, fill=(22, 39, 59))


def to_flowable(base, width_pt, max_height_pt=340):
    """Imagem do reportlab na largura pedida, reduzida para caber em max_height_pt (proporção mantida)."""
    from reportlab.platypus import Image as RLImage
    out = BytesIO()
    base.image.save(out, format="PNG", optimize=True)
    out.seek(0)
    w, h = base.image.size
    width = min(width_pt, max_height_pt * w / h)
    return RLImage(out, width=width, height=width * h / w)
