"""PDF das ferramentas de planejamento: análise de enlace, survey de melhor ponto e análise de cobertura
(portado do PT2VHF Mesh Analyzer). Desde a v1.15.0 os mapas usam o mapa de ruas por baixo (pdf_map),
com o desenho esquemático quando não há internet."""
from __future__ import annotations

import math
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String, Line, PolyLine, Polygon, Circle

from xml.sax.saxutils import escape

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle

from . import __version__

NAVY = colors.HexColor("#16273b")
BLUE = colors.HexColor("#2171b5")
TEAL = colors.HexColor("#258779")
GRAY = colors.HexColor("#4a5a68")

ST = getSampleStyleSheet()
ST.add(ParagraphStyle(name="BigTitleMesh", parent=ST["Title"], fontName="Helvetica-Bold", fontSize=22, leading=27,
                      textColor=NAVY, spaceAfter=10))
ST.add(ParagraphStyle(name="ChapterMesh", parent=ST["Heading2"], fontSize=15, leading=18, textColor=BLUE,
                      spaceBefore=10, spaceAfter=8))
ST.add(ParagraphStyle(name="TextMesh", parent=ST["BodyText"], fontSize=9, leading=13, spaceAfter=6))
ST.add(ParagraphStyle(name="Cell", fontName="Helvetica", fontSize=7.5, leading=10))
ST.add(ParagraphStyle(name="HeadCell", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=colors.white))


def number(value, unit="", decimals=1):
    if value is None:
        return "—"
    return f"{float(value):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".") + unit


def _grid(rows, widths=None):
    t = Table([[Paragraph(escape(str(c)), ST["HeadCell"] if i == 0 else ST["Cell"]) for c in row]
               for i, row in enumerate(rows)], colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fa")])]))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    w, _ = landscape(A4)
    canvas.setStrokeColor(colors.HexColor("#d2dce4"))
    canvas.line(12 * mm, 13 * mm, w - 12 * mm, 13 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRAY)
    canvas.drawString(12 * mm, 9 * mm, f"PT2VHF APRS Client v{__version__} | por Alex, PT2VHF")
    canvas.drawRightString(w - 12 * mm, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()

VERDICT_COLORS = {"viable": colors.HexColor("#1e8e4e"), "marginal": colors.HexColor("#c58a00"),
                  "unviable": colors.HexColor("#c0392b")}
PAGE_W, PAGE_H = landscape(A4)
USABLE = PAGE_W - 30 * mm


def _km(m):
    return number(m / 1000, " km", 2)


def _coord(lat, lon):
    return "%.6f, %.6f" % (lat, lon)


def profile_drawing(link, width=USABLE, height=200):
    """Perfil de altimetria: terreno (com curvatura), linha de visada e 1ª zona de Fresnel."""
    d = Drawing(width, height)
    P = link["profile"]
    dist = link["distance_m"] or 1
    hi = max(max(p["terrain_m"], p["los_m"] + p["fresnel_m"]) for p in P)
    lo = min(min(p["ground_m"], p["los_m"] - p["fresnel_m"]) for p in P)
    pad = (hi - lo) * 0.08 or 10
    hi, lo = hi + pad, lo - pad
    left, bottom, right, top = 42, 22, width - 10, height - 8
    X = lambda m: left + (right - left) * m / dist
    Y = lambda v: bottom + (top - bottom) * (v - lo) / ((hi - lo) or 1)
    d.add(Rect(left, bottom, right - left, top - bottom, fillColor=colors.HexColor("#eef4f9"), strokeColor=None))
    for i in range(5):
        v = lo + (hi - lo) * i / 4
        d.add(Line(left, Y(v), right, Y(v), strokeColor=colors.HexColor("#d5dee6"), strokeWidth=0.4))
        d.add(String(left - 4, Y(v) - 3, "%d m" % round(v), fontSize=6.5, fillColor=GRAY, textAnchor="end"))
    for i in range(6):
        m = dist * i / 5
        d.add(String(X(m), bottom - 11, _km(m), fontSize=6.5, fillColor=GRAY, textAnchor="middle"))
    ground = [X(0), bottom] + sum(([X(p["distance_m"]), Y(p["terrain_m"])] for p in P), []) + [X(dist), bottom]
    d.add(Polygon(ground, fillColor=colors.HexColor("#9c7a54"), strokeColor=colors.HexColor("#6d5235"), strokeWidth=0.6))
    upper = sum(([X(p["distance_m"]), Y(p["los_m"] + p["fresnel_m"])] for p in P), [])
    lower = sum(([X(p["distance_m"]), Y(p["los_m"] - p["fresnel_m"])] for p in P), [])
    sixty = sum(([X(p["distance_m"]), Y(p["los_m"] - 0.6 * p["fresnel_m"])] for p in P), [])
    d.add(PolyLine(upper, strokeColor=BLUE, strokeWidth=0.8, strokeDashArray=[3, 2]))
    d.add(PolyLine(lower, strokeColor=BLUE, strokeWidth=0.8, strokeDashArray=[3, 2]))
    d.add(PolyLine(sixty, strokeColor=colors.HexColor("#d9a400"), strokeWidth=0.8, strokeDashArray=[1, 2]))
    d.add(Line(X(0), Y(P[0]["los_m"]), X(dist), Y(P[-1]["los_m"]), strokeColor=TEAL, strokeWidth=1.4))
    for m, v, label in ((0, P[0]["los_m"], "A"), (dist, P[-1]["los_m"], "B")):
        d.add(Line(X(m), Y(v), X(m), Y(P[0 if m == 0 else -1]["ground_m"]), strokeColor=NAVY, strokeWidth=1.2))
        d.add(String(X(m) + (4 if m == 0 else -4), Y(v) + 3, label, fontSize=8, fontName="Helvetica-Bold",
                     fillColor=NAVY, textAnchor="start" if m == 0 else "end"))
    w = link.get("worst")
    if w and w["ratio"] < 0.6:
        t = next(p for p in P if abs(p["distance_m"] - w["distance_m"]) < 1)
        d.add(Circle(X(w["distance_m"]), Y(t["terrain_m"]), 3, fillColor=VERDICT_COLORS["unviable"], strokeColor=colors.white))
    return d


def link_story(link, title):
    p, b = link["params"], link["budget"]
    story = [Paragraph(escape(title), ST["ChapterMesh"])]
    color = VERDICT_COLORS[link["verdict"]].hexval()[2:]
    story.append(Paragraph('<font color="#%s"><b>%s</b></font> — %s %s' % (
        color, escape(link["verdict_label"].upper()), escape(link["reason"]), escape(link["obstruction"])), ST["TextMesh"]))
    story.append(profile_drawing(link))
    story.append(Paragraph("Terreno com curvatura da Terra (k = 4/3) · verde: linha de visada · azul: 1ª zona de Fresnel · "
                           "amarelo: 60% da zona (mínimo recomendado) · ponto vermelho: pior obstrução.", ST["TextMesh"]))
    rows = [["Item", "Valor", "Item", "Valor"],
            ["Ponto A", _coord(link["a"]["lat"], link["a"]["lon"]), "Ponto B", _coord(link["b"]["lat"], link["b"]["lon"])],
            ["Altitude do terreno A", number(link["a"]["ground_m"], " m", 0), "Altitude do terreno B", number(link["b"]["ground_m"], " m", 0)],
            ["Antena A acima do solo", number(p["height_a"], " m"), "Antena B acima do solo", number(p["height_b"], " m")],
            ["Distância", _km(link["distance_m"]), "Azimute A→B / B→A", "%s° / %s°" % (number(link["azimuth_ab"], "", 1), number(link["azimuth_ba"], "", 1))],
            ["Frequência", number(p["freq_mhz"], " MHz", 3), "Sensibilidade do receptor", number(p["sensitivity_dbm"], " dBm")],
            ["Potência TX", "%s (%s)" % (number(p["tx_power_w"], " W"), number(p["tx_power_dbm"], " dBm")), "EIRP", number(b["eirp_dbm"], " dBm")],
            ["Ganho antena A / B", "%s / %s" % (number(p["gain_a_dbi"], " dBi"), number(p["gain_b_dbi"], " dBi")),
             "Perda de cabo A / B", "%s / %s" % (number(p["cable_a_db"], " dB"), number(p["cable_b_db"], " dB"))],
            ["Perda em espaço livre", number(b["fspl_db"], " dB"), "Perda por obstrução (difração)", number(b["diffraction_db"], " dB")],
            ["Sinal estimado no receptor", "%s · %s · %s" % (number(b["rx_dbm"], " dBm"), number(b["rx_uv"], " µV", 2), b["s_meter"]),
             "Margem do enlace", number(b["margin_db"], " dB")]]
    w = link.get("worst")
    if w:
        rows.append(["Pior ponto", "%s de A (%s)" % (_km(w["distance_m"]), _coord(w["lat"], w["lon"])),
                     "Folga / Fresnel livre", "%s / %s" % (number(w["clearance_m"], " m"),
                                                  "0% (sem visada)" if w["ratio"] < 0 else "%d%%" % round(w["ratio"] * 100))])
    s = link.get("suggestion")
    if s:
        fmt = lambda v: "acima de 300 m" if v is None else number(v, " m")
        rows.append(["Antena para liberar 60% de Fresnel", "A: %s (B fixa) · B: %s (A fixa)" % (fmt(s["height_a_m"]), fmt(s["height_b_m"])),
                     "As duas com a mesma altura", fmt(s.get("height_both_m"))])
    o = link.get("observed")
    if o:
        seen = lambda x: "%d pacotes, último em %s" % (x["packets"], str(x["last_seen"] or "—")[:16].replace("T", " ")) if x else "não observado"
        rows.append(["%s ouviu %s por RF" % (o["b"], o["a"]), seen(o["b_heard_a"]),
                     "%s ouviu %s por RF" % (o["a"], o["b"]), seen(o["a_heard_b"])])
    story.append(_grid(rows, [USABLE * 0.2, USABLE * 0.3, USABLE * 0.2, USABLE * 0.3]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(escape(link["notes"]), ST["TextMesh"]))
    return story


def _hypsometric(t):
    stops = [(0.0, (46, 125, 50)), (0.35, (139, 170, 74)), (0.6, (214, 190, 120)), (0.85, (156, 110, 70)), (1.0, (245, 245, 245))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            f = (t - a) / ((b - a) or 1)
            return colors.Color(*[(ca[i] + (cb[i] - ca[i]) * f) / 255 for i in range(3)])
    return colors.Color(*[c / 255 for c in stops[-1][1]])


def survey_map(result, nodes=(), width=USABLE * 0.62, height=330):
    """Mapa esquemático: relevo por cores, polígono, pontos numerados, referência e nós da malha."""
    d = Drawing(width, height)
    poly = result["polygon"]
    lats = [p[0] for p in poly] + [result["reference"]["lat"]]
    lons = [p[1] for p in poly] + [result["reference"]["lon"]]
    lat0 = sum(lats) / len(lats)
    kx = math.cos(math.radians(lat0))
    minx, maxx = min(lons) * kx, max(lons) * kx
    miny, maxy = min(lats), max(lats)
    padx, pady = (maxx - minx) * 0.06 or 0.001, (maxy - miny) * 0.06 or 0.001
    minx, maxx, miny, maxy = minx - padx, maxx + padx, miny - pady, maxy + pady
    scale = min((width - 20) / (maxx - minx), (height - 20) / (maxy - miny))
    ox = 10 + ((width - 20) - (maxx - minx) * scale) / 2
    oy = 10 + ((height - 20) - (maxy - miny) * scale) / 2
    X = lambda lon: ox + (lon * kx - minx) * scale
    Y = lambda lat: oy + (lat - miny) * scale
    d.add(Rect(0, 0, width, height, fillColor=colors.HexColor("#f4f7fa"), strokeColor=colors.HexColor("#cbd6df")))
    lo, hi = result["elevation_range_m"]
    step_deg = result["grid_step_m"] / 111320
    cell = max(1.0, step_deg * scale * 1.02)
    for lat, lon, e in result["grid"]:
        c = _hypsometric((e - lo) / ((hi - lo) or 1))
        d.add(Rect(X(lon) - cell / 2, Y(lat) - cell / 2, cell, cell, fillColor=c, strokeColor=None))
    d.add(Polygon(sum(([X(p[1]), Y(p[0])] for p in poly), []), fillColor=None, strokeColor=NAVY, strokeWidth=1.4))
    for n in nodes:
        if miny <= n["lat"] <= maxy and minx <= n["lon"] * kx <= maxx:
            d.add(Circle(X(n["lon"]), Y(n["lat"]), 2.2, fillColor=colors.HexColor("#5b6b7a"), strokeColor=colors.white, strokeWidth=0.4))
            d.add(String(X(n["lon"]) + 3, Y(n["lat"]) + 2, n["name"][:12], fontSize=5.5, fillColor=colors.HexColor("#33424f")))
    r = result["reference"]
    rx, ry = X(r["lon"]), Y(r["lat"])
    d.add(Polygon([rx, ry + 5, rx + 5, ry, rx, ry - 5, rx - 5, ry], fillColor=colors.HexColor("#7b2cbf"), strokeColor=colors.white))
    for p in result["points"]:
        px, py = X(p["lon"]), Y(p["lat"])
        d.add(Circle(px, py, 6.5, fillColor=colors.HexColor("#c0392b"), strokeColor=colors.white, strokeWidth=1))
        d.add(String(px, py - 2.6, str(p["rank"]), fontSize=7, fontName="Helvetica-Bold", fillColor=colors.white, textAnchor="middle"))
    # Norte e escala.
    d.add(Polygon([width - 18, height - 10, width - 23, height - 24, width - 13, height - 24], fillColor=NAVY, strokeColor=None))
    d.add(String(width - 18, height - 34, "N", fontSize=8, fontName="Helvetica-Bold", fillColor=NAVY, textAnchor="middle"))
    metres_per_pt = 111320 / scale
    target = metres_per_pt * width * 0.25
    nice = min((v for v in (100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000) if v >= target * 0.5), default=50000)
    bar = nice / metres_per_pt
    d.add(Rect(12, 12, bar, 4, fillColor=NAVY, strokeColor=None))
    d.add(String(12, 19, "%s" % (_km(nice) if nice >= 1000 else "%d m" % nice), fontSize=7, fillColor=NAVY))
    return d


def legend_drawing(result, width=USABLE * 0.34):
    d = Drawing(width, 46)
    lo, hi = result["elevation_range_m"]
    for i in range(40):
        d.add(Rect(4 + i * (width - 8) / 40, 22, (width - 8) / 40 + 0.5, 10, fillColor=_hypsometric(i / 39), strokeColor=None))
    d.add(String(4, 10, "%d m" % round(lo), fontSize=7, fillColor=GRAY))
    d.add(String(width - 4, 10, "%d m" % round(hi), fontSize=7, fillColor=GRAY, textAnchor="end"))
    d.add(String(width / 2, 36, "Altitude do terreno", fontSize=7, fillColor=GRAY, textAnchor="middle"))
    return d


def _document(output, title):
    return SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm,
                             topMargin=14 * mm, bottomMargin=18 * mm, title=title, author="Alex, PT2VHF", pageCompression=1)


def _header(story, title, subtitle, name=""):
    story.append(Paragraph(escape(title), ST["BigTitleMesh"]))
    story.append(Paragraph(escape(subtitle + (" — " + name if name else "")), ST["TextMesh"]))
    story.append(Paragraph("Gerado em " + datetime.now().strftime("%d/%m/%Y %H:%M") + " · PT2VHF APRS Client v" + __version__ +
                           " · por Alex, PT2VHF", ST["TextMesh"]))


def _pad_bounds(lats, lons, frac=0.12, min_deg=0.01):
    s, n, w, e = min(lats), max(lats), min(lons), max(lons)
    dy, dx = max(n - s, min_deg) * frac, max(e - w, min_deg) * frac
    return s - dy, w - dx, n + dy, e + dx


def link_map(link, tile_dir=None, fetch=None, width=USABLE * 0.62):
    """Mapa de ruas com a linha A–B, as pontas e o pior obstáculo (None sem tiles)."""
    from . import pdf_map
    a, b = link["a"], link["b"]
    base = pdf_map.render(_pad_bounds([a["lat"], b["lat"]], [a["lon"], b["lon"]], 0.25), 1400, tile_dir, fetch)
    if base is None:
        return None
    from PIL import ImageDraw
    draw = ImageDraw.Draw(base.image)
    pa, pb = base.project(a["lat"], a["lon"]), base.project(b["lat"], b["lon"])
    draw.line([pa, pb], fill=(33, 113, 181), width=6)
    w = link.get("worst")
    if w and w.get("ratio", 1) < 0.6:
        x, y = base.project(w["lat"], w["lon"])
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(192, 57, 43), outline=(255, 255, 255), width=2)
    for (x, y), label in ((pa, "A"), (pb, "B")):
        draw.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(33, 113, 181), outline=(255, 255, 255), width=3)
        draw.text((x - 4, y - 7), label, fill=(255, 255, 255))
    pdf_map.scale_bar(base, (a["lat"] + b["lat"]) / 2)
    pdf_map.attribution(base)
    return pdf_map.to_flowable(base, width)


def link_pdf(link, name="", tile_dir=None, fetch=None):
    output = BytesIO()
    story = []
    _header(story, "Análise de enlace", "Viabilidade entre dois pontos", name)
    flow = link_map(link, tile_dir, fetch, USABLE * 0.7)
    if flow is not None:
        story.append(flow)
        story.append(Paragraph("Mapa: linha azul A–B · ponto vermelho: pior obstáculo · © OpenStreetMap contributors.", ST["TextMesh"]))
        story.append(PageBreak())
    story += link_story(link, "Resultado")
    _document(output, "Análise de enlace").build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()


def survey_base_map(result, nodes=(), tile_dir=None, fetch=None, width=USABLE * 0.62):
    """Mapa de ruas com o polígono, os pontos numerados, a referência e as estações (None sem tiles)."""
    from . import pdf_map
    poly = result["polygon"]
    ref = result["reference"]
    base = pdf_map.render(_pad_bounds([p[0] for p in poly] + [ref["lat"]], [p[1] for p in poly] + [ref["lon"]]),
                          1400, tile_dir, fetch)
    if base is None:
        return None
    from PIL import ImageDraw
    draw = ImageDraw.Draw(base.image, "RGBA")
    pts = [base.project(p[0], p[1]) for p in poly]
    draw.polygon(pts, fill=(22, 39, 59, 30), outline=(22, 39, 59, 255))
    draw.line(pts + [pts[0]], fill=(22, 39, 59, 255), width=4)
    for n in nodes:
        x, y = base.project(n["lat"], n["lon"])
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(91, 107, 122, 255), outline=(255, 255, 255, 255))
        draw.text((x + 7, y - 6), str(n["name"])[:12], fill=(34, 48, 60, 255))
    rx, ry = base.project(ref["lat"], ref["lon"])
    draw.polygon([(rx, ry - 11), (rx + 11, ry), (rx, ry + 11), (rx - 11, ry)], fill=(123, 44, 191, 255), outline=(255, 255, 255, 255))
    for p in result["points"]:
        x, y = base.project(p["lat"], p["lon"])
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=(192, 57, 43, 255), outline=(255, 255, 255, 255), width=2)
        draw.text((x - 4, y - 7), str(p["rank"]), fill=(255, 255, 255, 255))
    pdf_map.scale_bar(base, ref["lat"])
    pdf_map.attribution(base)
    return pdf_map.to_flowable(base, width)


def survey_pdf(result, name="", links=(), nodes=(), tile_dir=None, fetch=None):
    output = BytesIO()
    story = []
    _header(story, "Survey de melhor ponto", "Pontos mais altos dentro da área desenhada", name)
    ref = result["reference"]
    info = [["Item", "Valor"],
            ["Área / perímetro", "%s km² / %s" % (number(result["area_km2"], "", 3), _km(result["perimeter_km"] * 1000))],
            ["Vértices", str(len(result["polygon"]))],
            ["Referência", "%s (%s) · %s" % ("centro do polígono" if ref["kind"] == "centroid" else "ponto escolhido",
                                             _coord(ref["lat"], ref["lon"]), number(ref["elevation_m"], " m", 0))],
            ["Altitudes na área", "%s a %s" % (number(result["elevation_range_m"][0], " m", 0), number(result["elevation_range_m"][1], " m", 0))],
            ["Resolução da busca", "uma amostra a cada %d m, refinada em volta de cada topo" % result["resolution_m"]],
            ["Separação mínima entre pontos", number(result["min_separation_m"], " m", 0)]]
    side = [_grid(info, [USABLE * 0.12, USABLE * 0.22]), Spacer(1, 3 * mm), legend_drawing(result)]
    if result.get("note"):
        side.append(Paragraph(escape(result["note"]), ST["TextMesh"]))
    if result.get("warning"):
        side.append(Paragraph(escape(result["warning"]), ST["TextMesh"]))
    picture = survey_base_map(result, nodes, tile_dir, fetch) or survey_map(result, nodes)
    layout = Table([[picture, side]], colWidths=[USABLE * 0.64, USABLE * 0.36])
    layout.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(layout)
    story.append(Paragraph(("Mapa de ruas (© OpenStreetMap contributors)" if not isinstance(picture, Drawing) else
                            "Relevo por cores (amostras do modelo digital de terreno)") + " · losango roxo: referência · "
                           "círculos vermelhos numerados: pontos, do mais alto (1) para o mais baixo · cinza: estações APRS.", ST["TextMesh"]))
    story.append(PageBreak())
    story.append(Paragraph("Pontos, do mais alto para o mais baixo", ST["ChapterMesh"]))
    rows = [["Nº", "Altitude", "Desnível p/ referência", "Distância", "Direção", "Coordenadas", "Observação"]]
    for p in result["points"]:
        rows.append([str(p["rank"]), number(p["elevation_m"], " m", 0), number(p["delta_m"], " m", 0), _km(p["distance_m"]),
                     "%s (%d°)" % (p["direction"], p["bearing_deg"]), _coord(p["lat"], p["lon"]),
                     "Borda da área: o terreno sobe fora do polígono" if p.get("edge") else "Topo"])
    story.append(_grid(rows, [USABLE * w for w in (0.05, 0.1, 0.14, 0.1, 0.11, 0.2, 0.3)]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Elevações do modelo digital de terreno (~30–40 m), sem prédios, árvores ou torres. Confirme o "
                           "acesso, a posse e a infraestrutura do local antes de instalar.", ST["TextMesh"]))
    for item in links:
        story.append(PageBreak())
        story += link_story(item["link"], "Enlace do ponto %s até %s" % (item.get("rank", "?"), item.get("target", "B")))
    _document(output, "Survey de melhor ponto").build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()


def nearby_stations(stations, result, limit=200):
    poly = result["polygon"]
    lats, lons = [p[0] for p in poly], [p[1] for p in poly]
    pad = 0.02
    out = []
    for st in stations or []:
        lat, lon = st.get("latitude"), st.get("longitude")
        if lat is None or lon is None:
            continue
        lat, lon = float(lat), float(lon)
        if abs(lat) < 1e-6 and abs(lon) < 1e-6:
            continue
        if min(lats) - pad <= lat <= max(lats) + pad and min(lons) - pad <= lon <= max(lons) + pad:
            out.append({"lat": lat, "lon": lon, "name": str(st.get("callsign") or "")})
        if len(out) >= limit:
            break
    return out


# --- Análise de cobertura ------------------------------------------------------
COVERAGE_SCALES = {
    "plasma": [(13, 8, 135), (126, 3, 168), (204, 71, 120), (248, 149, 64), (240, 249, 33)],
    "viridis": [(68, 1, 84), (59, 82, 139), (33, 145, 140), (94, 201, 98), (253, 231, 37)],
    "turbo": [(48, 18, 59), (70, 134, 251), (26, 228, 182), (250, 186, 57), (180, 4, 38)],
    "signal": [(192, 57, 43), (230, 126, 34), (241, 196, 15), (130, 200, 80), (39, 174, 96)],
}
SCALE_NAMES = {"plasma": "Plasma", "viridis": "Viridis", "turbo": "Arco-íris", "signal": "Vermelho → verde"}


def _scale_color(scale, f):
    stops = COVERAGE_SCALES.get(scale) or COVERAGE_SCALES["plasma"]
    x = max(0.0, min(1.0, f)) * (len(stops) - 1)
    i = min(len(stops) - 2, int(x))
    u = x - i
    return colors.Color(*[(stops[i][k] + (stops[i + 1][k] - stops[i][k]) * u) / 255 for k in range(3)])


def coverage_display(display):
    display = display or {}
    lo = float(display.get("min", -130))
    hi = float(display.get("max", -80))
    if lo >= hi:
        lo, hi = -130.0, -80.0
    scale = display.get("scale") if display.get("scale") in COVERAGE_SCALES else "plasma"
    return {"min": lo, "max": hi, "scale": scale, "style": "contours" if display.get("style") == "contours" else "heat"}


def coverage_map(result, display, covered=(), uncovered=(), width=USABLE * 0.62, height=340):
    """Mapa esquemático da cobertura: grade reduzida desenhada em faixas, transmissor e nós."""
    import base64
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=colors.HexColor("#f4f7fa"), strokeColor=colors.HexColor("#cbd6df")))
    size = result["size"]
    grid = base64.b64decode(result["grid"])
    cells = min(180, size)                      # até 180 x 180 células no PDF
    step = size / cells
    side = min(width, height) - 20
    ox, oy = (width - side) / 2, (height - side) / 2
    cw = side / cells
    lo, hi = display["min"], display["max"]
    band = 10.0

    def level(dbm):
        if dbm < lo:
            return None
        if display["style"] == "contours":
            return min(1.0, (math.floor((dbm - lo) / band) * band + band / 2) / (hi - lo))
        return round(min(1.0, (dbm - lo) / (hi - lo)) * 23) / 23        # 24 tons: faixas contínuas no PDF

    for cy in range(cells):
        y = int((cy + 0.5) * step)
        run_start, run_level = None, None
        for cx in range(cells + 1):
            lev = None
            if cx < cells:
                b = grid[y * size + int((cx + 0.5) * step)]
                lev = level(b - 200) if b else None
            if lev != run_level:
                if run_level is not None:
                    d.add(Rect(ox + run_start * cw, oy + side - (cy + 1) * cw, (cx - run_start) * cw + 0.3, cw + 0.3,
                               fillColor=_scale_color(display["scale"], run_level), strokeColor=None))
                run_start, run_level = cx, lev
    cx0, cy0 = ox + side / 2, oy + side / 2
    d.add(Circle(cx0, cy0, side / 2, fillColor=None, strokeColor=colors.HexColor("#7d8b97"), strokeWidth=0.6,
                 strokeDashArray=[3, 3]))
    (s, w), (n, e) = result["bounds"]
    X = lambda lon: ox + (lon - w) / (e - w) * side
    Y = lambda lat: oy + (lat - s) / (n - s) * side
    for items, fill in ((uncovered, "#c0392b"), (covered, "#1e8e4e")):
        for it in items:
            px, py = X(it["lon"]), Y(it["lat"])
            d.add(Circle(px, py, 2.6, fillColor=colors.HexColor(fill), strokeColor=colors.white, strokeWidth=0.5))
            d.add(String(px + 3.5, py + 2, str(it["name"])[:14], fontSize=5.5, fillColor=colors.HexColor("#22303c")))
    d.add(Circle(cx0, cy0, 6, fillColor=colors.HexColor("#59e97e"), strokeColor=colors.white, strokeWidth=1.2))
    d.add(String(cx0, cy0 - 2.4, "TX", fontSize=5.5, fontName="Helvetica-Bold", fillColor=NAVY, textAnchor="middle"))
    d.add(Polygon([width - 18, height - 10, width - 23, height - 24, width - 13, height - 24], fillColor=NAVY, strokeColor=None))
    d.add(String(width - 18, height - 34, "N", fontSize=8, fontName="Helvetica-Bold", fillColor=NAVY, textAnchor="middle"))
    metres_per_pt = result["params"]["max_km"] * 2000 / side
    target = metres_per_pt * side * 0.25
    nice = min((v for v in (1000, 2000, 5000, 10000, 20000, 50000) if v >= target * 0.5), default=50000)
    d.add(Rect(12, 12, nice / metres_per_pt, 4, fillColor=NAVY, strokeColor=None))
    d.add(String(12, 19, _km(nice), fontSize=7, fillColor=NAVY))
    return d


def coverage_legend(display, width=USABLE * 0.34):
    d = Drawing(width, 46)
    for i in range(40):
        d.add(Rect(4 + i * (width - 8) / 40, 22, (width - 8) / 40 + 0.5, 10,
                   fillColor=_scale_color(display["scale"], i / 39), strokeColor=None))
    d.add(String(4, 10, "%d dBm" % round(display["min"]), fontSize=7, fillColor=GRAY))
    d.add(String(width - 4, 10, "%d dBm" % round(display["max"]), fontSize=7, fillColor=GRAY, textAnchor="end"))
    d.add(String(width / 2, 36, "Sinal estimado · " + ("contornos de 10 dB" if display["style"] == "contours" else "mapa de calor"),
                 fontSize=7, fillColor=GRAY, textAnchor="middle"))
    return d


def coverage_base_map(result, display, covered=(), uncovered=(), observed=None, tile_dir=None, fetch=None,
                      width=USABLE * 0.62):
    """Mapa de ruas com a cobertura colorida por cima, o transmissor e as estações (None sem tiles)."""
    import base64
    from . import pdf_map
    (s, w), (n, e) = result["bounds"]
    base = pdf_map.render((s, w, n, e), 1400, tile_dir, fetch)
    if base is None:
        return None
    from PIL import Image, ImageDraw
    size = result["size"]
    grid = base64.b64decode(result["grid"])
    lo, hi = display["min"], display["max"]
    over = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = over.load()
    for y in range(size):
        row = y * size
        for x in range(size):
            b = grid[row + x]
            if not b or b - 200 < lo:
                continue
            dbm = b - 200
            if display["style"] == "contours":
                f = min(1.0, (math.floor((dbm - lo) / 10) * 10 + 5) / (hi - lo))
            else:
                f = min(1.0, (dbm - lo) / (hi - lo))
            c = _scale_color(display["scale"], f)
            px[x, y] = (int(c.red * 255), int(c.green * 255), int(c.blue * 255), 150)
    x0, y0 = base.project(n, w)
    x1, y1 = base.project(s, e)
    over = over.resize((max(1, int(x1 - x0)), max(1, int(y1 - y0))), Image.NEAREST)
    base.image = base.image.convert("RGBA")
    base.image.alpha_composite(over, (int(x0), int(y0)))
    draw = ImageDraw.Draw(base.image)
    for items, fill in ((uncovered, (192, 57, 43)), (covered, (30, 142, 78))):
        for it in items:
            x, y = base.project(it["lat"], it["lon"])
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=fill, outline=(255, 255, 255), width=2)
            draw.text((x + 8, y - 6), str(it["name"])[:12], fill=(20, 30, 40))
    for it in (observed or {}).get("items", []):
        x, y = base.project(it["lat"], it["lon"])
        draw.rectangle((x - 7, y - 7, x + 7, y + 7), outline=(33, 113, 181), width=3)
    c = result["center"]
    cx, cy = base.project(c["lat"], c["lon"])
    draw.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(89, 233, 126), outline=(255, 255, 255), width=3)
    draw.text((cx - 7, cy - 7), "TX", fill=(22, 39, 59))
    base.image = base.image.convert("RGB")
    pdf_map.scale_bar(base, c["lat"])
    pdf_map.attribution(base)
    return pdf_map.to_flowable(base, width)


def coverage_pdf(result, display=None, name="", covered=(), uncovered=(), outside=(), observed=None,
                 tile_dir=None, fetch=None):
    from reportlab.platypus import Table, TableStyle
    from .coverage import CLIMATES
    from .planning import microvolts, s_units
    display = coverage_display(display)
    p = result["params"]
    output = BytesIO()
    story = []
    _header(story, "Análise de cobertura", "Onde o sinal do transmissor chegaria", name or p.get("name", ""))
    c = result["center"]
    watts = p["tx_power_w"]
    info = [["Item", "Valor"],
            ["Transmissor", "%s · %s" % (p.get("name") or "Transmissor", _coord(c["lat"], c["lon"]))],
            ["Terreno / antena", "%s · antena a %s, ganho %s" % (number(c["ground_m"], " m", 0), number(p["tx_height_m"], " m", 1),
                                                              number(p["tx_gain_dbi"], " dBi", 1))],
            ["Potência / frequência", "%s (%s) · %s" % (number(p["tx_power_dbm"], " dBm", 0), number(watts, " W", 2),
                                                         number(p["freq_mhz"], " MHz", 3))],
            ["Receptor", "sensibilidade %s (%s, %s) · altura %s · ganho %s · cabo %s" % (
                number(p["rx_sensitivity_dbm"], " dBm", 1), number(microvolts(p["rx_sensitivity_dbm"]), " µV", 2),
                s_units(p["rx_sensitivity_dbm"]), number(p["rx_height_m"], " m", 1),
                number(p["rx_gain_dbi"], " dBi", 1), number(p["rx_cable_db"], " dB", 1))],
            ["Ambiente", "%s · obstáculos %s · N = %s" % (CLIMATES[p["climate"]][0], number(p["clutter_m"], " m", 1),
                                                         number(p["refractivity_n"], "", 0))],
            ["Simulação", "%s%% dos locais · %s%% do tempo · raio %s%s" % (
                number(p["location_pct"], "", 1), number(p["time_pct"], "", 1), number(p["max_km"], " km", 0),
                " · relevo em alta resolução" if p.get("hires") else "")],
            ["Resultado", "%s com sinal · até %s · margem %s · relevo ~%d m/pixel" % (
                number(result["covered_km2"], " km²", 1), number(result["farthest_km"], " km", 1),
                number(result["fade_margin_db"], " dB", 1), round(result["terrain_m"]))],
            ["Estações conhecidas", "%d com cobertura · %d sem cobertura · %d fora do raio" % (len(covered), len(uncovered), len(outside))]]
    if observed and observed.get("total"):
        info.append(["Previsto × real", "%d de %d estações que ouviram %s por RF estão na área prevista (%d%%)" % (
            observed["agree"], observed["total"], observed["station"], observed["accuracy_pct"])])
    side = [_grid(info, [USABLE * 0.11, USABLE * 0.23]), Spacer(1, 3 * mm), coverage_legend(display),
            Paragraph(escape(result["notes"]), ST["Cell"])]
    picture = coverage_base_map(result, display, covered, uncovered, observed, tile_dir, fetch) or \
        coverage_map(result, display, covered, uncovered)
    layout = Table([[picture, side]], colWidths=[USABLE * 0.64, USABLE * 0.36])
    layout.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(layout)
    story.append(Paragraph("Escala de cores: %s. Círculo verde: transmissor · pontos verdes: estações com cobertura · pontos "
                           "vermelhos: estações sem cobertura · quadrado azul: estação que ouviu o transmissor por RF%s." % (
                               SCALE_NAMES[display["scale"]],
                               " · mapa de ruas © OpenStreetMap contributors" if not isinstance(picture, Drawing) else ""),
                           ST["TextMesh"]))
    story.append(PageBreak())
    story.append(Paragraph("Estações conhecidas com cobertura (%d)" % len(covered), ST["ChapterMesh"]))
    rows = [["Estação", "Sinal estimado", "Distância", "Coordenadas"]]
    rows += [[escape(str(x["name"])), number(x["dbm"], " dBm", 0), number(x["distance_km"], " km", 1), _coord(x["lat"], x["lon"])]
             for x in covered] or [["—", "", "", ""]]
    story.append(_grid(rows, [USABLE * w for w in (0.4, 0.15, 0.15, 0.3)]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Estações conhecidas sem cobertura (%d)" % len(uncovered), ST["ChapterMesh"]))
    rows = [["Estação", "Sinal estimado", "Falta", "Distância", "Coordenadas"]]
    rows += [[escape(str(x["name"])), number(x["dbm"], " dBm", 0) if x["dbm"] is not None else "sem sinal",
              number(x["missing_db"], " dB", 1) if x.get("missing_db") is not None else "—",
              number(x["distance_km"], " km", 1), _coord(x["lat"], x["lon"])] for x in uncovered] or [["—", "", "", "", ""]]
    story.append(_grid(rows, [USABLE * w for w in (0.34, 0.14, 0.1, 0.12, 0.3)]))
    if outside:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Fora do raio calculado (%d)" % len(outside), ST["ChapterMesh"]))
        rows = [["Estação", "Distância", "Coordenadas"]] + [[escape(str(x["name"])), number(x["distance_km"], " km", 1),
                                                         _coord(x["lat"], x["lon"])] for x in outside[:200]]
        story.append(_grid(rows, [USABLE * w for w in (0.45, 0.2, 0.35)]))
    _document(output, "Análise de cobertura").build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()
