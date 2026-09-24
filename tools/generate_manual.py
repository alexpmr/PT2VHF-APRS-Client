from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
BLUE = colors.HexColor("#075CA9")
DARK_BLUE = colors.HexColor("#062D63")
RED = colors.HexColor("#E70D18")
LIGHT_BLUE = colors.HexColor("#EAF5FD")
LIGHT_GREY = colors.HexColor("#F3F6F8")
TEXT = colors.HexColor("#243440")
MUTED = colors.HexColor("#5F7180")


def normalize(text: str) -> str:
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2192", "->")
        .replace("\u00a0", " ")
        .replace("\u2026", "...")
    )


def current_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def current_changelog(version: str) -> list[str]:
    path = ROOT / "CHANGELOG.md"
    if not path.exists():
        return ["CHANGELOG.md não encontrado no build."]
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## v{re.escape(version)}\b[^\n]*\n(?P<body>.*?)(?=^## v|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ["Não foi encontrada uma seção específica para esta versão no CHANGELOG.md."]
    items: list[str] = []
    for line in match.group("body").splitlines():
        line = line.strip()
        if line.startswith("- "):
            items.append(normalize(line[2:].strip()))
    return items or [normalize(match.group("body").strip())]


def safe_markup(text: str) -> str:
    text = normalize(text)
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", escaped)
    return escaped


class BrandLogo(Flowable):
    def __init__(self, width=15.5 * cm, height=8.2 * cm):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        c.saveState()
        c.setFillColor(colors.white)
        c.roundRect(0, 0, w, h, 18, fill=1, stroke=0)

        cx, cy = w / 2, h / 2
        rx, ry = w * 0.46, h * 0.38
        c.setFillColor(DARK_BLUE)
        c.ellipse(cx-rx, cy-ry, cx+rx, cy+ry, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.ellipse(cx-rx*0.955, cy-ry*0.93, cx+rx*0.955, cy+ry*0.93, fill=1, stroke=0)
        c.setFillColor(BLUE)
        c.ellipse(cx-rx*0.92, cy-ry*0.88, cx+rx*0.92, cy+ry*0.88, fill=1, stroke=0)

        c.setStrokeColor(colors.Color(0.84, 0.94, 1, alpha=0.65))
        c.setLineWidth(1.2)
        for frac in (-0.5, 0, 0.5):
            y = cy + frac * ry
            c.line(cx-rx*0.86, y, cx+rx*0.86, y)
        for frac in (-0.55, -0.28, 0, 0.28, 0.55):
            x = cx + frac * rx
            spread = rx * (0.16 + abs(frac) * 0.24)
            c.ellipse(x-spread, cy-ry*0.84, x+spread, cy+ry*0.84, fill=0, stroke=1)

        c.setFillColor(colors.HexColor("#F7FAFC"))
        c.circle(cx-rx*0.47, cy+ry*0.10, ry*0.23, fill=1, stroke=0)
        c.circle(cx-rx*0.31, cy-ry*0.21, ry*0.17, fill=1, stroke=0)
        c.circle(cx+rx*0.25, cy+ry*0.10, ry*0.30, fill=1, stroke=0)
        c.circle(cx+rx*0.36, cy-ry*0.20, ry*0.20, fill=1, stroke=0)

        c.setFillColor(RED)
        c.setStrokeColor(colors.white)
        c.setLineWidth(1.5)
        c.setFont("Helvetica-Bold", 27)
        c.drawCentredString(cx, cy + ry*0.52, "PT2VHF")
        c.setFont("Helvetica-Bold", 58)
        c.drawCentredString(cx, cy - 18, "APRS")
        c.setFont("Helvetica-Bold", 25)
        c.drawCentredString(cx, cy - ry*0.59, "CLIENT")
        c.restoreState()


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=24, leading=29, textColor=DARK_BLUE, alignment=TA_CENTER, spaceAfter=8
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontName="Helvetica",
            fontSize=11, leading=16, textColor=MUTED, alignment=TA_CENTER
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=18, leading=22, textColor=DARK_BLUE, spaceBefore=8, spaceAfter=9
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=13, leading=17, textColor=BLUE, spaceBefore=7, spaceAfter=5
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.5, leading=14.5, textColor=TEXT, alignment=TA_LEFT, spaceAfter=6
        ),
        "small": ParagraphStyle(
            "small", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8.2, leading=12, textColor=MUTED, spaceAfter=4
        ),
        "code": ParagraphStyle(
            "code", parent=base["BodyText"], fontName="Courier",
            fontSize=8.3, leading=12, textColor=colors.HexColor("#102B3C"),
            backColor=LIGHT_GREY, borderColor=colors.HexColor("#D5E0E7"),
            borderWidth=0.5, borderPadding=6, spaceBefore=4, spaceAfter=7
        ),
        "callout": ParagraphStyle(
            "callout", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=9.2, leading=14, textColor=DARK_BLUE,
            backColor=LIGHT_BLUE, borderColor=colors.HexColor("#A8D4F2"),
            borderWidth=0.7, borderPadding=8, spaceBefore=5, spaceAfter=8
        ),
    }


def bullet_list(items: list[str], st, level=0):
    rows = []
    for item in items:
        rows.append(ListItem(Paragraph(safe_markup(item), st["body"]), leftIndent=12))
    return ListFlowable(rows, bulletType="bullet", start="circle", leftIndent=16 + level * 8, bulletFontSize=6)


def section(story, st, title: str, paragraphs: list[str] | None = None, bullets: list[str] | None = None):
    story.append(Paragraph(safe_markup(title), st["h1"]))
    if paragraphs:
        for p in paragraphs:
            story.append(Paragraph(safe_markup(p), st["body"]))
    if bullets:
        story.append(bullet_list(bullets, st))
        story.append(Spacer(1, 4))


def add_footer(canvas, doc, version):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#D5E0E7"))
    canvas.setLineWidth(0.5)
    canvas.line(1.7*cm, 1.25*cm, width-1.7*cm, 1.25*cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(1.7*cm, 0.86*cm, f"PT2VHF APRS Client v{version} - Manual do Usuário")
    canvas.drawRightString(width-1.7*cm, 0.86*cm, f"Página {doc.page}")
    canvas.restoreState()


def add_screenshot(story, st, screenshots_dir: Path | None, filename: str, caption: str) -> None:
    if not screenshots_dir:
        return
    path = screenshots_dir / filename
    if not path.exists():
        return
    story.append(Spacer(1, 6))
    img = Image(str(path), width=16.3*cm, height=9.17*cm)
    img.hAlign = "CENTER"
    story.append(img)
    story.append(Paragraph(caption, st["small"]))
    story.append(Spacer(1, 8))


def cover_background(canvas, doc, version: str) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.circle(width*0.88, height*0.88, 5.2*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.Color(1, 1, 1, alpha=.05))
    canvas.circle(width*0.15, height*0.14, 4.2*cm, fill=1, stroke=0)
    canvas.restoreState()


def build_manual(output: Path, screenshots_dir: Path | None = None, logo_path: Path | None = None) -> None:
    version = current_version()
    changes = current_changelog(version)
    st = styles()

    doc = SimpleDocTemplate(
        str(output), pagesize=A4,
        rightMargin=1.7*cm, leftMargin=1.7*cm,
        topMargin=1.55*cm, bottomMargin=1.65*cm,
        title=f"PT2VHF APRS Client v{version} - Manual do Usuário",
        author="Alex, PT2VHF",
        subject="Instalação, configuração e uso do PT2VHF APRS Client",
    )
    story = []

    logo_path = logo_path or (ROOT / "pt2vhf_aprs" / "static" / "img" / "app_logo.png")
    story.append(Spacer(1, 0.9*cm))
    if logo_path.exists():
        logo = Image(str(logo_path), width=16.0*cm, height=12.0*cm)
        logo.hAlign = "CENTER"
        story.append(logo)
    else:
        story.append(BrandLogo())
    story.append(Spacer(1, 0.32*cm))
    cover_title = ParagraphStyle("cover_title", parent=st["title"], textColor=colors.white, fontSize=26, leading=31)
    cover_sub = ParagraphStyle("cover_sub", parent=st["subtitle"], textColor=colors.HexColor("#DDEEFF"), fontSize=12)
    story.append(Paragraph(f"PT2VHF APRS Client v{version}", cover_title))
    story.append(Paragraph("Manual do Usuário", cover_sub))
    story.append(Spacer(1, 0.10*cm))
    story.append(Paragraph("Instalação, configuração e operação", cover_sub))
    story.append(Spacer(1, 0.25*cm))
    story.append(Paragraph("Por Alex, PT2VHF", cover_sub))
    story.append(Spacer(1, 0.7*cm))
    story.append(Paragraph(
        "Este manual é gerado automaticamente pelo processo de release usando o número da versão e o CHANGELOG do próprio projeto. "
        "Assim, a documentação acompanha a versão publicada.", st["callout"]
    ))
    story.append(PageBreak())

    section(story, st, "Sumário", bullets=[
        "1. Visão geral e novidades da versão",
        "2. Download e requisitos",
        "3. Instalação em Windows, Linux e macOS",
        "4. Primeira configuração e coordenadas",
        "5. APRS-IS e editor gráfico de filtros",
        "6. Mapa e topologia observada",
        "7. Mensagens, estações e Log",
        "8. Aparência, backup e atualização",
        "9. Diagnóstico, segurança e changelog",
    ])
    story.append(PageBreak())

    section(story, st, "1. Visão geral", [
        "O PT2VHF APRS Client é um cliente APRS-IS com mapa, mensagens, estações, log, tracklogs, topologia observada e banco SQLite local.",
        "A interface foi projetada para uso direto por radioamadores, com distribuição pronta para Windows, Linux e macOS."
    ], [
        "Mapa baseado em Leaflet com OpenStreetMap, OpenTopoMap e imagem de satélite.",
        "Mensagens APRS individuais com ACK/REJ, boletins e histórico local.",
        "Topologia observada a partir dos paths APRS recebidos.",
        "Configuração visual de mapa, tracklogs, topologia, tema, fontes e idioma.",
        "Backup e restauração da configuração em JSON.",
        "Verificação de versão e acesso às Releases oficiais."
    ])

    story.append(Paragraph("Conteúdo deste manual", st["h2"]))
    story.append(bullet_list([
        "Instalação em Windows, Linux e macOS.",
        "Configuração inicial da estação e conexão APRS-IS.",
        "Coordenadas em formato decimal ou graus/minutos/segundos e localização atual.",
        "Filtro APRS-IS manual e editor gráfico.",
        "Mapa, topologia, mensagens, estações e log.",
        "Aparência, idioma, backup, atualização e diagnóstico.",
        "Changelog da versão atual."
    ], st))

    section(story, st, "2. Novidades da versão", [
        f"A seção abaixo é extraída automaticamente do CHANGELOG.md correspondente à v{version}."
    ])
    story.append(bullet_list(changes, st))
    story.append(PageBreak())

    section(story, st, "3. Download e requisitos", [
        "Baixe somente arquivos publicados na Release oficial do repositório PT2VHF-APRS-Client.",
        "O aplicativo usa conexão com a Internet para APRS-IS, consulta de atualização e tiles dos mapas. A interface local e o banco permanecem no computador."
    ])
    data = [
        ["Sistema", "Arquivo recomendado", "Observação"],
        ["Windows x64", f"PT2VHF_APRS_Client_Setup_x64_v{version}.exe", "Instalador principal"],
        ["Windows x64", f"PT2VHF_APRS_Client_Portable_x64_v{version}.exe", "Executável portátil"],
        ["Linux amd64", f"pt2vhf-aprs-client_{version}_amd64.deb", "Debian/Ubuntu"],
        ["Linux x86_64", f"PT2VHF_APRS_Client_Linux_x86_64_v{version}.tar.gz", "Pacote portátil"],
        ["macOS Apple Silicon", f"PT2VHF_APRS_Client_macOS_arm64_v{version}.dmg", "M1/M2/M3/M4 e compatíveis"],
        ["macOS Intel", f"PT2VHF_APRS_Client_macOS_x86_64_v{version}.dmg", "Mac Intel"],
    ]
    table = Table(data, colWidths=[3.3*cm, 9.0*cm, 4.0*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), DARK_BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 7.7),
        ("LEADING", (0,0), (-1,-1), 10),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#C9D6DF")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))

    section(story, st, "4. Instalação no Windows", [
        "Para a maioria dos usuários, utilize o instalador Setup. A versão Portable não precisa ser instalada e usa o mesmo banco local da versão instalada."
    ], [
        "Execute o instalador e siga as telas.",
        "Se o Windows informar editor desconhecido, confirme apenas se o arquivo veio da Release oficial.",
        "O banco fica em %LOCALAPPDATA%\\PT2VHF APRS Client\\data\\pt2vhf_aprs.db.",
        "A janela integrada usa Microsoft Edge WebView2. Se o runtime não estiver disponível, o programa pode usar o navegador como fallback."
    ])

    section(story, st, "5. Instalação no Linux", [
        "No Debian, Ubuntu e derivados, prefira o pacote .deb. Em outras distribuições x86_64, use o tar.gz."
    ], [
        f"Debian/Ubuntu: sudo apt install ./pt2vhf-aprs-client_{version}_amd64.deb",
        "Pacote portátil: descompacte o tar.gz e execute o binário incluído.",
        "Os dados ficam por padrão em ~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db.",
        "Se a janela WebView não estiver disponível, o navegador local é usado como fallback."
    ])

    section(story, st, "6. Instalação no macOS", [
        "Use o DMG correspondente à arquitetura do Mac: arm64 para Apple Silicon ou x86_64 para Intel."
    ], [
        "Abra o DMG e arraste PT2VHF APRS Client.app para Applications.",
        "Os builds podem não estar notarizados. Se o Gatekeeper bloquear a primeira abertura, use Ajustes do Sistema > Privacidade e Segurança > Abrir Mesmo Assim, desde que o arquivo tenha vindo da Release oficial.",
        "Não desative globalmente o Gatekeeper.",
        "Os dados ficam em ~/Library/Application Support/PT2VHF APRS Client/data/pt2vhf_aprs.db."
    ])
    story.append(PageBreak())

    section(story, st, "7. Primeira configuração", [
        "A Configuração é dividida em dois grupos: APRS / Estação e Aplicativo. Isso evita misturar parâmetros de rádio/rede com preferências visuais.",
        "Antes de conectar ao APRS-IS, preencha Indicativo, Latitude, Longitude e Altitude. Caso tente conectar sem esses dados, o programa abre Configuração > APRS / Estação e leva o foco ao primeiro campo ausente."
    ])
    story.append(Paragraph("Campos principais", st["h2"]))
    story.append(bullet_list([
        "Indicativo: indicativo-base do radioamador, sem SSID.",
        "SSID: identificador APRS de 0 a 15.",
        "Passcode APRS-IS: calculado automaticamente a partir do indicativo-base.",
        "Comentário: texto curto transmitido no beacon.",
        "Latitude, Longitude e Altitude: posição da estação.",
        "Ícone APRS: símbolo mostrado no mapa.",
        "Servidor, porta, filtro e intervalo de beacon: parâmetros de conexão APRS-IS."
    ], st))

    section(story, st, "8. Coordenadas", [
        "Você pode informar latitude e longitude em decimal ou em graus/minutos/segundos (DMS). No modo DMS, a aplicação converte os valores para decimal antes de salvar.",
        "Na primeira execução, o cliente solicita permissão de localização ao navegador/WebView/SO. Se autorizada, latitude e longitude são pré-preenchidas e o mapa é centralizado na posição atual.",
        "O botão Usar minha localização atual permite repetir a operação posteriormente sem tornar o mapa dependente de recentralização contínua."
    ])
    story.append(Paragraph(
        "Se a plataforma não fornecer altitude confiável, o cliente usa 0 m para não impedir a conexão e sinaliza claramente que esse valor deve ser revisado. Uma altitude informada manualmente não é substituída por 0 m em execuções futuras.",
        st["callout"]
    ))

    section(story, st, "9. APRS-IS e filtros", [
        "O servidor padrão é soam.aprs2.net na porta 14580. Se esse endereço não puder ser alcançado, o cliente pode tentar rotate.aprs2.net como alternativa. O campo de servidor continua editável e oferece sugestões regionais.",
        "O filtro padrão de novas instalações é r/2000, que o aplicativo expande usando as coordenadas configuradas. O campo manual continua sempre disponível e o editor gráfico serve como assistente para compor a mesma string de filtro."
    ])
    story.append(Paragraph("Editor gráfico", st["h2"]))
    story.append(bullet_list([
        "Filtro radial: usa a posição da estação e um raio em quilômetros.",
        "Prefixos: gera componentes como p/PT2/PY2.",
        "Indicativos exatos: gera componentes como b/PT2VHF-15/PY2ABC.",
        "Tipos de pacote: gera componente t/... para posições, mensagens, meteorologia, telemetria, objetos e itens.",
        "O botão Gerar filtro escreve a string final no campo manual para revisão antes de salvar."
    ], st))
    story.append(Paragraph(
        "Filtro vazio: ao salvar as configurações APRS com o campo vazio, o programa pede confirmação. Dependendo do servidor e da porta, uma conexão sem filtro personalizado pode receber um fluxo muito maior de tráfego. Use filtro vazio somente de forma consciente.",
        st["callout"]
    ))

    add_screenshot(story, st, screenshots_dir, "map.png", "Tela principal: mapa e estações APRS.")
    section(story, st, "10. Mapa e topologia observada", [
        "O mapa mostra estações com posição conhecida e mantém tracklogs das estações móveis. Na primeira execução, quando a localização é autorizada, ele abre centralizado na posição atual do usuário. O carregamento do Leaflet é independente do restante da interface: se o provedor do mapa estiver lento ou indisponível, as outras abas continuam funcionando."
    ], [
        "Tipos de mapa: OpenStreetMap, OpenTopoMap e Satélite.",
        "Tracklogs: cor e espessura configuráveis.",
        "Topologia observada: pode ser ligada/desligada e filtrada por 1 h, 6 h, 24 h ou 7 dias.",
        "Enlaces RF e via IGate possuem cores independentes e espessura configurável.",
        "Restaurar topologia padrão retorna RF #35a7ff, IGate #b06cff e 2 px."
    ])

    add_screenshot(story, st, screenshots_dir, "config-aprs.png", "Configuração APRS/Estação com coordenadas e parâmetros APRS-IS.")
    add_screenshot(story, st, screenshots_dir, "filter-editor.png", "Editor gráfico de filtro APRS-IS, mantendo a string manual editável.")
    section(story, st, "11. Mensagens", [
        "A aba Mensagens apresenta o histórico em fluxo de chat, com mensagens antigas acima e novas abaixo. Também pode agrupar conversas por remetente."
    ], [
        "Clique em um indicativo De ou Para para preencher o destinatário.",
        "Enter envia; Shift+Enter cria nova linha.",
        "Mensagens longas são divididas em partes APRS, cada uma com seu próprio ID e ACK.",
        "ACK é mostrado como Lido; REJ indica rejeição.",
        "Boletins gerais e de grupo são suportados.",
        "Na aba Mensagens, novas mensagens usam um aviso compacto, não bloqueante, com fechamento manual e temporizador configurável."
    ])

    add_screenshot(story, st, screenshots_dir, "messages.png", "Aba Mensagens em fluxo de chat.")
    section(story, st, "12. Estações e Log", [
        "A aba Estações lista os últimos dados conhecidos e permite abrir a estação diretamente no mapa.",
        "O Log APRS-IS mostra tráfego TNC2 RX/TX e é a principal ferramenta para diagnosticar conexão, autenticação e filtro. Na conexão inicial, a v1.4 encerra as tentativas após três ciclos sem sucesso e mostra o erro final ao usuário."
    ], [
        "verified no logresp confirma autenticação APRS-IS.",
        "Linhas iniciadas por # são mensagens de controle do servidor.",
        "O passcode é mascarado no Log.",
        "O histórico de log é limitado aos registros mais recentes para evitar crescimento sem controle."
    ])

    add_screenshot(story, st, screenshots_dir, "stations.png", "Aba Estações com os últimos dados conhecidos.")
    add_screenshot(story, st, screenshots_dir, "log.png", "Log APRS-IS para diagnóstico de RX/TX.")
    section(story, st, "13. Aparência, idioma e preferências", [
        "Em Configuração > Aplicativo, escolha tema Escuro ou Claro, idioma Português ou English, fontes e tamanhos das telas.",
        "O Português é o idioma padrão. A troca para English é aplicada à interface e fica persistida após salvar.",
        "Também é possível habilitar a abertura simultânea no navegador ao iniciar."
    ])

    add_screenshot(story, st, screenshots_dir, "config-app.png", "Configuração do aplicativo, incluindo tema e formatação por tela.")
    section(story, st, "14. Backup, atualização e banco local", [
        "A exportação JSON salva a configuração. O arquivo pode conter o passcode APRS-IS em texto legível; armazene-o em local seguro.",
        "As atualizações preservam o banco local. Antes de mudanças importantes, é recomendável fazer backup do arquivo SQLite."
    ])
    story.append(Paragraph("Locais do banco", st["h2"]))
    story.append(Paragraph(
        "Windows: %LOCALAPPDATA%\\PT2VHF APRS Client\\data\\pt2vhf_aprs.db<br/>"
        "Linux: ~/.local/share/PT2VHF-APRS-Client/data/pt2vhf_aprs.db<br/>"
        "macOS: ~/Library/Application Support/PT2VHF APRS Client/data/pt2vhf_aprs.db",
        st["code"]
    ))

    section(story, st, "15. Diagnóstico rápido", bullets=[
        "Não conecta: confira servidor, porta, Internet, indicativo e passcode.",
        "Mensagem de campos obrigatórios: abra Configuração > APRS / Estação e preencha Indicativo, Latitude, Longitude e Altitude.",
        "Conecta sem estações: confira o filtro e procure erros no Log.",
        "Mapa sem tiles: confira o acesso à Internet e o provedor de mapas.",
        "Localização atual não funciona: confira a permissão de localização do sistema/WebView/navegador.",
        "Topologia vazia: confirme que a opção está ativa e que existem paths observados entre nós com posições conhecidas.",
        "Sem som de mensagem: confira a opção em Aparência e o volume do sistema."
    ])

    section(story, st, "16. Segurança e privacidade", bullets=[
        "A interface HTTP local escuta em 127.0.0.1; não exponha a porta diretamente à Internet.",
        "Trate o arquivo de backup JSON como sensível por causa do passcode APRS-IS.",
        "Use somente releases do repositório oficial.",
        "Não desative mecanismos de segurança do Windows ou macOS de forma global apenas para executar o aplicativo.",
        "Consulte PRIVACY.md, SECURITY.md e THIRD_PARTY_NOTICES.md no repositório."
    ])

    story.append(PageBreak())
    section(story, st, f"17. Changelog - v{version}", [
        "Conteúdo extraído automaticamente do CHANGELOG.md durante a geração deste manual."
    ])
    story.append(bullet_list(changes, st))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Projeto: https://github.com/alexpmr/PT2VHF-APRS-Client<br/>"
        "Autor: Alex, PT2VHF",
        st["small"]
    ))

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.build(
        story,
        onFirstPage=lambda canvas, d: cover_background(canvas, d, version),
        onLaterPages=lambda canvas, d: add_footer(canvas, d, version),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--screenshots-dir")
    parser.add_argument("--logo")
    args = parser.parse_args()
    build_manual(
        Path(args.output),
        Path(args.screenshots_dir) if args.screenshots_dir else None,
        Path(args.logo) if args.logo else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
