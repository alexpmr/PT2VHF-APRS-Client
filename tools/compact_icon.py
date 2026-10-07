"""Ícone compacto do PT2VHF APRS Client para tamanhos 16–256 px.

A logomarca institucional permanece em app_logo.png (cabeçalho e manual).
Apenas o ícone de sistema é simplificado; cores preservam a identidade do
produto e o pictograma se mantém legível sem texto em 16x16.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BRAND_SOURCE = ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png"


def render_compact_icon(size: int = 1024) -> Image.Image:
    if not BRAND_SOURCE.exists():
        raise FileNotFoundError(f"Logo oficial ausente: {BRAND_SOURCE}")
    # A fonte institucional é validada, mas não reduzida integralmente ao
    # favicon: texto e ornamentos desapareciam nas miniaturas de 16/24 px.
    with Image.open(BRAND_SOURCE) as logo:
        if min(logo.size) < 128:
            raise ValueError("A logo institucional tem resolução insuficiente.")
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((34, 34, 990, 990), radius=217, fill=(13, 32, 47, 255))
    d.rounded_rectangle((65, 65, 959, 959), radius=187, outline=(79, 176, 218, 255), width=28)
    # Símbolo esquemático de antena e ondas RF: sem texto minúsculo,
    # sem detalhes instáveis quando o ícone é reduzido.
    blue = (98, 208, 243, 255)
    yellow = (247, 194, 62, 255)
    d.arc((242, 187, 782, 727), 202, 338, fill=blue, width=54)
    d.arc((328, 278, 696, 646), 206, 334, fill=blue, width=50)
    d.ellipse((457, 383, 567, 493), fill=yellow)
    d.rounded_rectangle((475, 462, 549, 776), radius=33, fill=yellow)
    d.line((359, 795, 665, 795), fill=yellow, width=65)
    d.ellipse((323, 759, 396, 832), fill=yellow)
    d.ellipse((628, 759, 701, 832), fill=yellow)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)
