"""PDF das ferramentas de planejamento: análise de enlace e survey de melhor ponto (portado do PT2VHF Mesh Analyzer)."""
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
    story.append(Paragraph("Gerado em " + datetime.now().strftime("%d/%m/%Y %H:%M") + " · PT2VHF APRS Client · por Alex, PT2VHF", ST["TextMesh"]))


def link_pdf(link, name=""):
    output = BytesIO()
    story = []
    _header(story, "Análise de enlace", "Viabilidade entre dois pontos", name)
    story += link_story(link, "Resultado")
    _document(output, "Análise de enlace").build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()


def survey_pdf(result, name="", links=(), nodes=()):
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
    layout = Table([[survey_map(result, nodes), side]], colWidths=[USABLE * 0.64, USABLE * 0.36])
    layout.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(layout)
    story.append(Paragraph("Relevo por cores (amostras do modelo digital de terreno) · losango roxo: referência · "
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
