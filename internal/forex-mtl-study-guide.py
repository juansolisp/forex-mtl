#!/usr/bin/env python3
"""
forex-mtl Complete Technical Study Guide — PDF Generator
Produces a comprehensive interview-preparation document.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether, Preformatted
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.platypus.doctemplate import NextPageTemplate
import sys

# ─── Colour palette ──────────────────────────────────────────────────────────
PURPLE      = colors.HexColor('#7c3aed')
PURPLE_LIGHT= colors.HexColor('#ede9fe')
CYAN        = colors.HexColor('#0891b2')
CYAN_LIGHT  = colors.HexColor('#cffafe')
GREEN       = colors.HexColor('#16a34a')
GREEN_LIGHT = colors.HexColor('#dcfce7')
ORANGE      = colors.HexColor('#ea580c')
ORANGE_LIGHT= colors.HexColor('#ffedd5')
RED         = colors.HexColor('#dc2626')
GRAY_950    = colors.HexColor('#0a0a0a')
GRAY_900    = colors.HexColor('#111827')
GRAY_800    = colors.HexColor('#1f2937')
GRAY_700    = colors.HexColor('#374151')
GRAY_600    = colors.HexColor('#4b5563')
GRAY_400    = colors.HexColor('#9ca3af')
GRAY_200    = colors.HexColor('#e5e7eb')
GRAY_100    = colors.HexColor('#f3f4f6')
WHITE       = colors.white
BLACK       = colors.black
CODE_BG     = colors.HexColor('#f8f8f8')
CODE_BORDER = colors.HexColor('#d1d5db')

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm

# ─── Document class with headers/footers ─────────────────────────────────────
class ForexDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN + 0.5*cm,
            bottomMargin=MARGIN + 0.5*cm,
        )
        self.chapter_name = ""
        content_frame = Frame(
            MARGIN, MARGIN + 0.8*cm,
            PAGE_W - 2*MARGIN, PAGE_H - 2*MARGIN - 1.4*cm,
            id='content'
        )
        cover_frame = Frame(
            0, 0, PAGE_W, PAGE_H, id='cover'
        )
        self.addPageTemplates([
            PageTemplate(id='cover', frames=[cover_frame], onPage=self._cover_page),
            PageTemplate(id='normal', frames=[content_frame], onPage=self._normal_page),
        ])

    def _cover_page(self, canvas, doc):
        cover_page(canvas, doc)

    def _normal_page(self, canvas, doc):
        canvas.saveState()
        # Header rule
        canvas.setStrokeColor(PURPLE)
        canvas.setLineWidth(1.5)
        canvas.line(MARGIN, PAGE_H - MARGIN - 0.2*cm,
                    PAGE_W - MARGIN, PAGE_H - MARGIN - 0.2*cm)
        # Header text
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(GRAY_600)
        canvas.drawString(MARGIN, PAGE_H - MARGIN + 0.1*cm, "forex-mtl — Technical Study Guide")
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 0.1*cm,
                               self.chapter_name)
        # Footer rule
        canvas.setStrokeColor(GRAY_200)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, MARGIN + 0.6*cm, PAGE_W - MARGIN, MARGIN + 0.6*cm)
        # Footer text
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(GRAY_600)
        canvas.drawCentredString(PAGE_W/2, MARGIN + 0.2*cm, str(doc.page))
        canvas.drawString(MARGIN, MARGIN + 0.2*cm, "Paidy Interview Preparation")
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN + 0.2*cm, "Confidential")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if hasattr(flowable, 'chapter_mark'):
            self.chapter_name = flowable.chapter_mark

# ─── Style sheet ─────────────────────────────────────────────────────────────
def make_styles():
    s = {}

    s['body'] = ParagraphStyle('body',
        fontName='Helvetica', fontSize=10, leading=15,
        textColor=GRAY_800, spaceAfter=6, spaceBefore=0,
        alignment=TA_JUSTIFY)

    s['body_small'] = ParagraphStyle('body_small',
        fontName='Helvetica', fontSize=9, leading=13,
        textColor=GRAY_700, spaceAfter=4)

    s['h1'] = ParagraphStyle('h1',
        fontName='Helvetica-Bold', fontSize=20, leading=26,
        textColor=PURPLE, spaceAfter=4, spaceBefore=18,
        borderPad=0)

    s['h2'] = ParagraphStyle('h2',
        fontName='Helvetica-Bold', fontSize=14, leading=19,
        textColor=GRAY_900, spaceAfter=6, spaceBefore=14)

    s['h3'] = ParagraphStyle('h3',
        fontName='Helvetica-Bold', fontSize=11.5, leading=16,
        textColor=PURPLE, spaceAfter=4, spaceBefore=10)

    s['h4'] = ParagraphStyle('h4',
        fontName='Helvetica-Bold', fontSize=10.5, leading=14,
        textColor=GRAY_700, spaceAfter=3, spaceBefore=8)

    s['bullet'] = ParagraphStyle('bullet',
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=GRAY_800, spaceAfter=3,
        leftIndent=14, bulletIndent=0,
        bulletFontName='Helvetica', bulletFontSize=10)

    s['bullet2'] = ParagraphStyle('bullet2',
        fontName='Helvetica', fontSize=9.5, leading=13,
        textColor=GRAY_700, spaceAfter=2,
        leftIndent=28, bulletIndent=14)

    s['code_inline'] = ParagraphStyle('code_inline',
        fontName='Courier', fontSize=9, leading=12,
        textColor=GRAY_800, spaceAfter=4)

    s['caption'] = ParagraphStyle('caption',
        fontName='Helvetica-Oblique', fontSize=8.5, leading=12,
        textColor=GRAY_600, spaceAfter=6, alignment=TA_CENTER)

    s['qa_q'] = ParagraphStyle('qa_q',
        fontName='Helvetica-Bold', fontSize=10.5, leading=14,
        textColor=PURPLE, spaceAfter=3, spaceBefore=10)

    s['qa_a'] = ParagraphStyle('qa_a',
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=GRAY_800, spaceAfter=6, leftIndent=12)

    s['toc1'] = ParagraphStyle('toc1',
        fontName='Helvetica-Bold', fontSize=11, leading=16,
        textColor=GRAY_900, spaceAfter=4)

    s['toc2'] = ParagraphStyle('toc2',
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=GRAY_700, spaceAfter=2, leftIndent=16)

    s['note_text'] = ParagraphStyle('note_text',
        fontName='Helvetica', fontSize=9.5, leading=13.5,
        textColor=GRAY_800, spaceAfter=0)

    return s

# ─── Flowable helpers ─────────────────────────────────────────────────────────

def chapter_mark(name):
    """Invisible paragraph that updates the running header."""
    class CM(Paragraph):
        def __init__(self, n):
            super().__init__('', ParagraphStyle('_'))
            self.chapter_mark = n
        def wrap(self, aw, ah): return 0, 0
        def draw(self): pass
    return CM(name)

def rule(color=GRAY_200, thickness=0.5):
    return HRFlowable(width='100%', thickness=thickness, color=color,
                      spaceAfter=6, spaceBefore=6)

def chapter_heading(num, title, styles):
    elems = []
    elems.append(chapter_mark(f"Ch.{num} — {title}"))
    # Purple top bar
    elems.append(HRFlowable(width='100%', thickness=4, color=PURPLE,
                             spaceAfter=6, spaceBefore=2))
    label = Paragraph(f'<font color="#7c3aed" size="9">CHAPTER {num}</font>', styles['body_small'])
    heading = Paragraph(title, styles['h1'])
    elems.append(label)
    elems.append(heading)
    elems.append(HRFlowable(width='100%', thickness=0.5, color=GRAY_200,
                             spaceAfter=10, spaceBefore=2))
    return elems

def section(title, styles):
    return [
        Spacer(1, 6),
        Paragraph(title, styles['h2']),
        HRFlowable(width='100%', thickness=1, color=GRAY_200, spaceAfter=4),
    ]

def subsection(title, styles):
    return [Paragraph(title, styles['h3'])]

def subsubsection(title, styles):
    return [Paragraph(title, styles['h4'])]

def p(text, styles, style='body'):
    return Paragraph(text, styles[style])

def bp(text, styles):
    return Paragraph(f"• {text}", styles['bullet'])

def bp2(text, styles):
    return Paragraph(f"– {text}", styles['bullet2'])

def sp(n=1):
    return Spacer(1, n * 4)

def code_block(text, styles, caption=None):
    """Gray-backgrounded code block."""
    elems = []
    lines = text.strip('\n')
    pre = Preformatted(lines, ParagraphStyle('code',
        fontName='Courier', fontSize=8.2, leading=11.5,
        textColor=GRAY_800,
        leftIndent=8, rightIndent=8,
        spaceBefore=2, spaceAfter=2,
        backColor=CODE_BG,
        borderColor=CODE_BORDER, borderWidth=0.5,
        borderPad=6))
    elems.append(pre)
    if caption:
        elems.append(Paragraph(caption, styles['caption']))
    return elems

def callout(title, text, styles, color=PURPLE):
    """Colored left-border callout box."""
    data = [[
        Table([['']], colWidths=[4], rowHeights=[None],
              style=TableStyle([('BACKGROUND', (0,0), (-1,-1), color),
                                ('LEFTPADDING', (0,0), (-1,-1), 0),
                                ('RIGHTPADDING', (0,0), (-1,-1), 0)])),
        Table([
            [Paragraph(f'<b>{title}</b>', ParagraphStyle('ct',
                fontName='Helvetica-Bold', fontSize=9.5, leading=13,
                textColor=color, spaceAfter=2))],
            [Paragraph(text, ParagraphStyle('cb',
                fontName='Helvetica', fontSize=9.5, leading=13.5,
                textColor=GRAY_800))],
        ], colWidths=[PAGE_W - 2*MARGIN - 4 - 16],
           style=TableStyle([
               ('LEFTPADDING', (0,0), (-1,-1), 8),
               ('TOPPADDING', (0,0), (-1,-1), 6),
               ('BOTTOMPADDING', (0,0), (-1,-1), 6),
               ('RIGHTPADDING', (0,0), (-1,-1), 6),
           ]))
    ]]
    t = Table(data, colWidths=[4, PAGE_W - 2*MARGIN - 4],
              style=TableStyle([
                  ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9f7ff')),
                  ('BOX', (0,0), (-1,-1), 0.5, CODE_BORDER),
                  ('LEFTPADDING', (0,0), (0,-1), 0),
                  ('RIGHTPADDING', (0,0), (0,-1), 0),
                  ('TOPPADDING', (0,0), (-1,-1), 0),
                  ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                  ('VALIGN', (0,0), (-1,-1), 'TOP'),
              ]))
    return [t, Spacer(1, 8)]

def interview_qa(q, a, styles):
    return [
        Paragraph(f"❓ {q}", styles['qa_q']),
        Paragraph(a, styles['qa_a']),
    ]

def key_point(text, styles):
    return callout("KEY INTERVIEW POINT", text, styles, PURPLE)

def warning_box(text, styles):
    return callout("COMMON MISTAKE / GOTCHA", text, styles, ORANGE)

def info_box(text, styles):
    return callout("WHY THIS MATTERS", text, styles, CYAN)

# ─── Cover page ───────────────────────────────────────────────────────────────
def cover_page(canvas, doc):
    w, h = A4
    # Dark background top half
    canvas.setFillColor(GRAY_900)
    canvas.rect(0, h*0.45, w, h*0.55, fill=1, stroke=0)
    # Purple accent bar
    canvas.setFillColor(PURPLE)
    canvas.rect(0, h*0.43, w, h*0.02+2, fill=1, stroke=0)
    # Title
    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 36)
    canvas.drawCentredString(w/2, h*0.72, "forex-mtl")
    canvas.setFont('Helvetica', 18)
    canvas.setFillColor(colors.HexColor('#c4b5fd'))
    canvas.drawCentredString(w/2, h*0.65, "Complete Technical Study Guide")
    canvas.setFont('Helvetica', 12)
    canvas.setFillColor(GRAY_400)
    canvas.drawCentredString(w/2, h*0.60, "Interview Preparation — Architecture, Design Decisions & Implementation")
    # Bottom section
    canvas.setFillColor(GRAY_800)
    canvas.setFont('Helvetica', 11)
    # Tech badges
    badges = ["Scala 2.13", "cats-effect 2", "fs2 2.x", "http4s 0.22",
              "circe", "Docker", "React + Vite", "Nginx"]
    x = MARGIN
    y = h * 0.36
    canvas.setFillColor(PURPLE)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(MARGIN, y + 0.3*cm, "Technology Stack:")
    y -= 0.2*cm
    for i, badge in enumerate(badges):
        bx = MARGIN + (i % 4) * ((w - 2*MARGIN) / 4)
        by = y - (i // 4) * 0.7*cm
        canvas.setFillColor(colors.HexColor('#ede9fe'))
        canvas.roundRect(bx, by, (w - 2*MARGIN)/4 - 0.3*cm, 0.55*cm, 4, fill=1, stroke=0)
        canvas.setFillColor(PURPLE)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawCentredString(bx + (w - 2*MARGIN)/8 - 0.15*cm, by + 0.15*cm, badge)
    # Bottom metadata
    canvas.setFillColor(GRAY_600)
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(w/2, MARGIN, "Paidy Take-Home Assignment  ·  Confidential")
    # Architecture diagram (ASCII art area)
    canvas.setFillColor(CODE_BG)
    canvas.roundRect(MARGIN, h*0.12, w - 2*MARGIN, h*0.15, 6, fill=1, stroke=0)
    canvas.setStrokeColor(CODE_BORDER)
    canvas.setLineWidth(0.5)
    canvas.roundRect(MARGIN, h*0.12, w - 2*MARGIN, h*0.15, 6, fill=0, stroke=1)
    canvas.setFillColor(GRAY_700)
    canvas.setFont('Courier', 8.5)
    arch_lines = [
        "Browser (React SPA) ──Nginx:3001──┬── /rates  ──────► forex-proxy:9090 ──► One-Frame:8080",
        "                                   ├── /events (SSE) ► forex-proxy:9090",
        "                                   └── /config ──────► forex-proxy:9090",
        "",
        "forex-proxy internals:  HTTP Routes ─► Program Layer ─► OneFrameCache (Ref[F,Map]) ─► One-Frame",
        "                        EventBus (fs2 Topic) ◄─────── CacheRefresh, ProxyRequest, Heartbeat",
    ]
    for i, line in enumerate(arch_lines):
        canvas.drawString(MARGIN + 0.4*cm, h*0.25 - i * 0.35*cm, line)

# ─── Build content ────────────────────────────────────────────────────────────
def build_story(styles):
    story = []

    # ── COVER (handled by onFirstPage) ──────────────────────────────────────
    story.append(NextPageTemplate('normal'))
    story.append(PageBreak())

    # ── TABLE OF CONTENTS ───────────────────────────────────────────────────
    story.append(chapter_mark("Table of Contents"))
    story.append(HRFlowable(width='100%', thickness=4, color=PURPLE, spaceAfter=6))
    story.append(Paragraph('<font color="#7c3aed" size="9">NAVIGATION</font>', styles['body_small']))
    story.append(Paragraph("Table of Contents", styles['h1']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRAY_200, spaceAfter=14))

    toc_data = [
        ("1", "The Problem and Why It's Hard", "The math, the constraints, the core tension"),
        ("2", "Technology Stack", "Why each library was chosen"),
        ("3", "Layered Architecture", "The onion model, tagless final, layer responsibilities"),
        ("4", "The Domain Layer", "Currency, Rate, Price, Timestamp — why each design choice"),
        ("5", "The Service Layer", "Algebra, OneFrameLive, OneFrameCache, EventBus"),
        ("6", "The Program Layer", "EitherT, error translation, why this layer exists"),
        ("7", "The HTTP Layer", "Query params, routes, SSE, middleware stack"),
        ("8", "Application Wiring (Main.scala)", "Stream composition, resource management"),
        ("9", "Docker and Infrastructure", "Multi-stage builds, Nginx, docker-compose"),
        ("10","The Frontend Architecture", "Module singletons, hooks, SSE, heartbeats"),
        ("11","Testing Strategy", "What's tested, how, and why no real network"),
        ("12","Key Interview Q&A", "The questions you will be asked, with full answers"),
    ]

    for num, title, desc in toc_data:
        row = Table([[
            Paragraph(f'<b>{num}.</b>', ParagraphStyle('_n',
                fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=PURPLE)),
            Paragraph(f'<b>{title}</b><br/><font size="9" color="#4b5563">{desc}</font>',
                ParagraphStyle('_t', fontName='Helvetica', fontSize=11, leading=15)),
        ]], colWidths=[0.8*cm, PAGE_W - 2*MARGIN - 0.8*cm],
            style=TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('LINEBELOW', (1,0), (1,0), 0.3, GRAY_200),
            ]))
        story.append(row)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 1
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("1", "The Problem and Why It's Hard", styles)

    story.append(p(
        "The forex-mtl assignment sounds simple at first: <i>build a proxy service that returns "
        "currency exchange rates</i>. But hiding inside that simple sentence is a fundamental "
        "engineering tension that drives every single design decision in this project. "
        "Understanding this tension — and being able to articulate it clearly — is the most "
        "important thing you can do in your interview.", styles))
    story.append(sp(2))

    story += section("1.1  The Assignment Constraints", styles)
    story.append(p("You are given:", styles))
    story += [
        bp("<b>One-Frame API</b> — an upstream currency rates service. It works, it's reliable, but it enforces a hard <b>1,000 API calls per day</b> limit. Exceed it and you get errors for the rest of the day.", styles),
        bp("A requirement that rates served to clients are <b>never more than 5 minutes stale</b> (the freshness SLA).", styles),
        bp("The expectation that <b>multiple clients can query rates simultaneously</b> — concurrent load is expected.", styles),
        bp("9 currencies: AUD, CAD, CHF, EUR, GBP, NZD, JPY, SGD, USD. Clients can request any pair.", styles),
    ]
    story.append(sp(2))

    story += section("1.2  Why a Naive Approach Fails Immediately", styles)
    story.append(p(
        "The simplest possible implementation: when a client asks for USD→JPY, forward the "
        "request to One-Frame and return the result. Let's see what happens:", styles))
    story.append(sp())
    story += code_block("""\
Scenario: A frontend dashboard refreshes rates every 10 seconds for 9 currency pairs.
That's 9 pairs × 6 refreshes/minute = 54 One-Frame calls/minute.
In 24 hours: 54 × 60 × 24 = 77,760 calls.

The limit is 1,000 calls/day.

We would exhaust the daily budget in: 1,000 ÷ 54 = 18.5 minutes.""", styles,
        caption="Naive forwarding burns the daily quota in under 20 minutes")

    story.append(p(
        "This is not a corner case or an edge case. This is what happens under any realistic "
        "load. The naive approach doesn't just fail to scale — it fails immediately, in minutes, "
        "even with a single user.", styles))
    story.append(sp(2))

    story += section("1.3  The Core Tension", styles)
    story.append(p(
        "<b>Clients want fresh data on every request. The upstream enforces a strict call budget.</b>", styles))
    story.append(p(
        "Every architectural decision in this project is a direct consequence of resolving this "
        "tension without sacrificing either correctness (5-minute freshness SLA) or scalability "
        "(arbitrary client load).", styles))
    story.append(sp(2))

    story += section("1.4  The Math That Drives Everything", styles)
    story.append(p(
        "Before writing a single line of code, you need to run the numbers. This is the "
        "calculation that determines the refresh interval:", styles))
    story += code_block("""\
Currencies: 9 (AUD, CAD, CHF, EUR, GBP, NZD, JPY, SGD, USD)
Pairs:       9 × 8 = 72  (self-pairs like USD/USD excluded — One-Frame doesn't support them)

Budget:      1,000 calls/day ÷ 24 hours = 41.6 calls/hour

Strategy:    Fetch ALL 72 pairs in ONE batch call every N minutes.
             Each batch = 1 API call (not 72!). One-Frame supports multi-pair queries.

At N = 4 min:  (60 ÷ 4) × 24 = 360 calls/day  →  64% below limit ✓
               4 minutes + 1 minute buffer = 5-minute maximum staleness = exactly the SLA ✓

At N = 5 min:  (60 ÷ 5) × 24 = 288 calls/day  →  would satisfy the SLA at the boundary
               (chosen not to, as it leaves zero safety buffer)

At N = 4 min:  Safety margin = 5 min SLA - 4 min interval = 1 minute buffer ✓""", styles,
        caption="The calculation that determines the 4-minute refresh interval")

    story += key_point(
        "When asked 'why 4 minutes?', answer with this math. Show that you derived the "
        "interval from first principles: budget constraint (1000/day), SLA requirement (5 min), "
        "and batch strategy (all 72 pairs in one call). The number is not arbitrary.", styles)
    story.append(sp(2))

    story += section("1.5  The Solution: Proactive Batch Caching", styles)
    story.append(p(
        "The solution is <b>proactive batch caching</b>: every 4 minutes, fetch all 72 currency "
        "pairs in a single One-Frame API call, store them in memory, and serve all client "
        "requests from the in-memory map without ever calling One-Frame again until the next "
        "scheduled refresh.", styles))
    story += code_block("""\
Time 0:00   → Cache refresh: fetch 72 pairs (1 API call)
Time 0:01   → Client asks for USD/JPY → served from cache (0 API calls)
Time 0:02   → 50 clients ask for various pairs → all served from cache (0 API calls)
Time 4:00   → Cache refresh: fetch 72 pairs (1 API call)
Time 4:01   → Client asks for EUR/GBP → served from cache (0 API calls)
...
In 24 hours: 360 API calls, unlimited client requests served.""", styles,
        caption="The proactive cache completely decouples client load from upstream API calls")

    story.append(p(
        "This pattern has a name in distributed systems: <b>read-through caching with "
        "proactive refresh</b>. But in this implementation, there is no 'read-through' — the "
        "cache is <i>always</i> pre-populated before clients ever ask. If the cache is empty "
        "(cold start), clients get an error. That's acceptable because the initial warm-up "
        "happens before the HTTP server starts accepting connections.", styles))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 2
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("2", "Technology Stack", styles)
    story.append(p(
        "Understanding <i>why</i> each technology was chosen is as important as knowing "
        "how to use it. An interviewer will ask 'why http4s over Akka HTTP?' or 'why "
        "cats-effect?' — you need a real answer, not 'because it was in the scaffold'.", styles))
    story.append(sp(2))

    stack_data = [
        ["Technology", "Version", "Why This Choice"],
        ["Scala", "2.13.12", "Scaffold requirement; mature generics (kind-projector), -Xfatal-warnings discipline"],
        ["cats-effect", "2.5.1", "CE2 (not CE3) — required by http4s 0.22.x; provides IO, Concurrent, Timer typeclasses"],
        ["fs2", "2.5.4", "CE2-compatible functional streams; used for cache refresh loop and SSE fan-out"],
        ["http4s", "0.22.15", "Purely functional HTTP — composes with cats-effect natively; type-safe routes"],
        ["circe", "0.14.2", "JSON codec derivation; circe-generic-extras for snake_case mapping with One-Frame"],
        ["pureconfig", "0.17.4", "Type-safe HOCON config — maps snake-case config keys to camelCase Scala fields"],
        ["logback", "1.2.x", "SLF4J backend; standard for JVM logging"],
        ["ScalaTest + ScalaCheck", "3.2.x / 1.0.x", "Unit + property-based testing; cats-scalacheck for CE2 test support"],
    ]
    t = Table(stack_data,
              colWidths=[3.5*cm, 2.5*cm, PAGE_W - 2*MARGIN - 6*cm],
              style=TableStyle([
                  ('BACKGROUND', (0,0), (-1,0), PURPLE),
                  ('TEXTCOLOR', (0,0), (-1,0), WHITE),
                  ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                  ('FONTSIZE', (0,0), (-1,-1), 9),
                  ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                  ('BACKGROUND', (0,1), (-1,-1), WHITE),
                  ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_100]),
                  ('GRID', (0,0), (-1,-1), 0.3, GRAY_200),
                  ('VALIGN', (0,0), (-1,-1), 'TOP'),
                  ('TOPPADDING', (0,0), (-1,-1), 5),
                  ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                  ('LEFTPADDING', (0,0), (-1,-1), 6),
              ]))
    story.append(t)
    story.append(sp(3))

    story += section("2.1  Why cats-effect 2 (CE2), Not CE3?", styles)
    story.append(p(
        "This is a question you will absolutely be asked. The short answer: <b>because "
        "http4s 0.22 requires CE2</b>. The http4s 0.23 series migrated to CE3. The "
        "scaffold specified http4s 0.22, so CE2 it is.", styles))
    story.append(p(
        "The practical difference for this project: CE2 uses separate typeclasses "
        "<code>Concurrent[F]</code>, <code>Timer[F]</code>, <code>ContextShift[F]</code>. "
        "CE3 unified these into <code>Async[F]</code> and <code>Temporal[F]</code>. "
        "The code uses CE2 idioms throughout — any CE3 syntax would fail to compile.", styles))

    story += section("2.2  Why http4s Over Akka HTTP / Play?", styles)
    story.append(p(
        "http4s is the idiomatic choice in the cats-effect ecosystem. Key advantages:", styles))
    story += [
        bp("<b>Pure functional composition</b> — HttpRoutes is literally a function from Request to Option[Response], composable with standard FP combinators.", styles),
        bp("<b>Effect-typed</b> — routes return <code>F[Response]</code>, not <code>Future[Response]</code>. Effects compose naturally with the rest of the codebase.", styles),
        bp("<b>No actor system overhead</b> — Akka HTTP requires an ActorSystem; http4s with Blaze uses NIO directly.", styles),
        bp("<b>Consistent algebra</b> — the same <code>Client[F]</code> type is used for both the HTTP server and the One-Frame client, with identical semantics.", styles),
    ]

    story += section("2.3  Why fs2 for Streams?", styles)
    story.append(p(
        "fs2 (Functional Streams for Scala) provides the backbone for two critical features:", styles))
    story += [
        bp("<b>Cache refresh loop</b> — the periodic background job is modeled as an infinite <code>Stream[F, Unit]</code>. This integrates naturally with the http4s server stream via <code>.merge</code>, giving them a shared lifecycle.", styles),
        bp("<b>SSE fan-out</b> — <code>fs2.concurrent.Topic</code> is a pub/sub mechanism where one publisher notifies N subscribers. Each browser SSE connection is a subscriber.", styles),
    ]

    story += section("2.4  Strict Compilation Flags", styles)
    story.append(p(
        "The <code>build.sbt</code> includes <code>-Xfatal-warnings</code> and several "
        "<code>-Ywarn-unused:*</code> flags. This means <b>every warning is a build error</b>. "
        "The code has zero dead imports, zero unused variables, zero unchecked pattern matches. "
        "When you see <code>@annotation.unused</code> on a val, it means the val IS used — "
        "but by the implicit system, not by the compiler's usage analysis.", styles))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 3
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("3", "Layered Architecture", styles)
    story.append(p(
        "The project is structured in concentric layers — the classic 'onion architecture' "
        "pattern. Each layer knows only about the layer immediately below it. This is not "
        "just aesthetic; it has concrete consequences for testability and maintainability.", styles))
    story.append(sp(2))

    story += code_block("""\
┌──────────────────────────────────────────────────────────────────────┐
│  Main.scala          — Application entry point, stream wiring        │
├──────────────────────────────────────────────────────────────────────┤
│  Module.scala        — Dependency injection, middleware stack         │
├────────────────┬─────────────────────────────────────────────────────┤
│  HTTP Layer    │  /rates  /events  /config                           │
│                │  RatesHttpRoutes  EventsHttpRoutes  ConfigHttpRoutes │
├────────────────┼─────────────────────────────────────────────────────┤
│  Program Layer │  RatesProgram                                        │
│                │  (error translation between service ↔ HTTP layers)  │
├────────────────┼─────────────────────────────────────────────────────┤
│  Service Layer │  Algebra[F] ← OneFrameCache ← OneFrameLive         │
│                │  EventBus (fs2 Topic pub/sub)                        │
├────────────────┼─────────────────────────────────────────────────────┤
│  Domain Layer  │  Currency, Rate, Rate.Pair, Price, Timestamp        │
│                │  (pure data — no effects, no dependencies)          │
└────────────────┴─────────────────────────────────────────────────────┘""", styles,
        caption="The layered architecture — each layer depends only on the one below")

    story += section("3.1  Why These Layers?", styles)
    story.append(p(
        "Each layer exists for a reason. Here is the rule for each boundary:", styles))

    story += [
        bp("<b>HTTP → Program</b>: The HTTP layer never imports service-layer error types. It only knows about program-layer errors. This means you can completely restructure service errors without touching a single HTTP file.", styles),
        bp("<b>Program → Service</b>: The program layer translates between error hierarchies and coordinates service calls. It has no HTTP knowledge.", styles),
        bp("<b>Service → Domain</b>: Services work with domain objects (Currency, Rate). They don't know about JSON, HTTP status codes, or query parameters.", styles),
        bp("<b>Domain</b>: Pure data. No effects, no dependencies, no IO. Can be tested with zero boilerplate.", styles),
    ]

    story += section("3.2  Tagless Final — The Core Pattern", styles)
    story.append(p(
        "Every service, program, and route is parameterized over an effect type <code>F[_]</code>. "
        "This is the tagless final pattern. You will almost certainly be asked about this.", styles))
    story += code_block("""\
// The service algebra — NOT tied to IO
trait Algebra[F[_]] {
  def get(pair: Rate.Pair): F[Error Either Rate]
}

// In production: F = IO
// In synchronous tests: F = cats.Id
// In custom test effects: F = EitherT[IO, TestError, ?]

// The program layer
class Program[F[_]: Functor](service: Algebra[F]) {
  def get(request: GetRatesRequest): F[program.Error Either Rate] =
    service.get(Rate.Pair(request.from, request.to))
      .map(_.leftMap(toProgramError))
}""", styles, caption="Tagless final: the same code works with any effect type")

    story.append(p(
        "The practical benefit: <code>ProgramSpec</code> tests the program logic using "
        "<code>cats.Id</code> as <code>F</code>. <code>Id[A] = A</code> — there is no "
        "effect at all. No IO, no threads, no scheduling. The test is a pure function call "
        "that returns synchronously. This makes tests fast, deterministic, and portable.", styles))

    story += key_point(
        "When asked about tagless final, say: 'It lets me write business logic once and "
        "test it without IO. In production F = IO; in tests F = Id. The code is identical "
        "— only the effect interpretation changes. This is the algebraic interpretation "
        "pattern: define a DSL (the algebra), provide multiple interpreters.'", styles)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 4
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("4", "The Domain Layer", styles)
    story.append(p(
        "The domain layer is the innermost ring. It contains pure data types with no "
        "dependencies on HTTP, JSON, or effects. Every other layer depends on this one, "
        "but this layer depends on nothing.", styles))
    story.append(sp(2))

    story += section("4.1  Currency — The Sealed Enumeration", styles)
    story += code_block("""\
sealed trait Currency
object Currency {
  case object AUD extends Currency
  case object CAD extends Currency
  case object CHF extends Currency
  case object EUR extends Currency
  case object GBP extends Currency
  case object NZD extends Currency
  case object JPY extends Currency
  case object SGD extends Currency
  case object USD extends Currency

  val values: List[Currency] = List(AUD, CAD, CHF, EUR, GBP, NZD, JPY, SGD, USD)

  def fromString(s: String): Either[String, Currency] =
    s.toUpperCase match {
      case "AUD" => Right(AUD)
      // ... etc
      case other => Left(s"Unknown currency: $other")
    }

  implicit val show: Show[Currency] = Show.show(_.toString)
}""", styles)

    story.append(p("<b>Why sealed?</b> The Scala compiler can verify that pattern matches are "
        "exhaustive. If you add a 10th currency later and forget to handle it in a match, "
        "the compiler will warn you (or with -Xfatal-warnings, refuse to compile).", styles))
    story.append(p("<b>Why <code>values: List[Currency]</code>?</b> The cache needs to enumerate "
        "all pairs to build the batch request to One-Frame. Without <code>values</code>, you'd "
        "need reflection or a manual list somewhere else. Having it in the domain type keeps "
        "the knowledge co-located with the type.", styles))
    story.append(p("<b>Why <code>fromString</code> returns <code>Either</code>?</b> The scaffold "
        "had a partial function (threw an exception on invalid input). Replacing it with Either "
        "forces every call site to handle the failure case explicitly. The HTTP layer uses this "
        "to produce proper 400 responses instead of 500s.", styles))
    story.append(p("<b>Why case-insensitive parsing (<code>.toUpperCase</code>)?</b> Clients "
        "might send <code>usd</code> instead of <code>USD</code>. Being strict here would "
        "produce unnecessary 400 errors for valid input.", styles))

    story += section("4.2  Rate and Rate.Pair — Typed Domain Objects", styles)
    story += code_block("""\
final case class Rate(pair: Rate.Pair, price: Price, timestamp: Timestamp)

object Rate {
  final case class Pair(from: Currency, to: Currency)
}""", styles)

    story.append(p("<b>Why <code>Rate.Pair</code> instead of <code>(Currency, Currency)</code>?</b> "
        "A tuple has no semantic meaning. <code>Rate.Pair(USD, JPY)</code> is self-documenting "
        "and can't be accidentally mixed up with <code>(Currency, Currency)</code> in another "
        "context. It's also used as a <code>Map</code> key — case classes have structural "
        "equality and hashCode out of the box.", styles))
    story.append(p("<b>Why mid-price?</b> One-Frame returns bid, ask, and price (mid). For a "
        "rate lookup service, mid-price is the correct value to expose — it's the "
        "market-neutral rate. The bid/ask spread is relevant for executing trades, not "
        "for informational rate queries.", styles))

    story += section("4.3  Price and Timestamp — AnyVal Wrappers", styles)
    story += code_block("""\
final class Price(val value: BigDecimal) extends AnyVal
final class Timestamp(val value: OffsetDateTime) extends AnyVal""", styles)

    story.append(p("<b>Why AnyVal?</b> AnyVal is a zero-cost abstraction. At the JVM level, "
        "<code>Price</code> is erased to <code>BigDecimal</code> — no wrapper object is "
        "allocated. You get type safety (can't accidentally pass a price where a timestamp "
        "is expected) without any runtime overhead.", styles))
    story.append(p("<b>Why BigDecimal for Price?</b> Never use <code>Double</code> for financial "
        "values. Double is a floating-point type with binary representation errors. "
        "<code>0.1 + 0.2 = 0.30000000000000004</code> in Double. BigDecimal is "
        "arbitrary-precision decimal — exact arithmetic.", styles))
    story.append(p("<b>Why OffsetDateTime for Timestamp?</b> <code>LocalDateTime</code> has no "
        "timezone information — ambiguous across regions. <code>OffsetDateTime</code> carries "
        "the UTC offset, making it unambiguous. When serialized to ISO-8601 "
        "(<code>2024-01-15T10:30:00Z</code>), it can be parsed correctly anywhere.", styles))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 5
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("5", "The Service Layer In Depth", styles)
    story.append(p(
        "The service layer is where the core business logic lives. This chapter explains "
        "every design decision in the cache implementation, which is the heart of the "
        "entire project.", styles))

    story += section("5.1  The Algebra — Defining the Contract", styles)
    story += code_block("""\
// src/main/scala/forex/services/rates/algebra.scala
trait Algebra[F[_]] {
  def get(pair: Rate.Pair): F[Error Either Rate]
}""", styles)

    story.append(p("This two-line trait is the contract. Everything else is an implementation detail. "
        "The key properties:", styles))
    story += [
        bp("<b>F[_]</b> — the effect type parameter. Callers don't need to know if the implementation uses IO, Future, or Id.", styles),
        bp("<b>Error Either Rate</b> — explicit error handling. The Either forces call sites to handle failures. No exceptions propagating through the call stack.", styles),
        bp("<b>Single method</b> — small, focused algebras are easier to mock, stub, and test than large ones.", styles),
    ]

    story += section("5.2  OneFrameLive — The Real HTTP Client", styles)
    story.append(p("OneFrameLive makes the actual HTTP calls to One-Frame. Key implementation details:", styles))
    story += code_block("""\
// The One-Frame API contract:
// GET /rates?pair=USDJPY&pair=EURUSD&...   (multiple pairs in one request)
// Header: token: 10dc303535874aeccc86a8251e6992f5   (NOT Authorization: Bearer)
// Response: JSON array of rate objects with snake_case field names

// Query string construction
val query = pairs.map(p => s"pair=${p.from}${p.to}").mkString("&")
val uri   = config.uri / "rates" +? ("pair", ...) // http4s Uri builder

// Authentication header — custom scheme, not Bearer
val req = GET(uri).withHeaders(Header("token", config.token))

// JSON decoding — One-Frame uses snake_case
// time_stamp → timeStamp requires circe-generic-extras with snake case config
implicit val circeConfig = Configuration.default.withSnakeCaseMemberNames

// Error handling — catch all network exceptions, return Left
client.run(req).use(_.as[List[OneFrameResponse]])
  .map(responses => Right(responses.map(toRate)))
  .handleErrorWith(e => F.pure(Left(Error.OneFrameLookupFailed(e.getMessage))))""", styles,
        caption="OneFrameLive — the HTTP client layer")

    story += warning_box(
        "The token header is NOT 'Authorization: Bearer TOKEN'. It is a custom header named "
        "'token' with the raw token as its value. This is a One-Frame-specific API requirement. "
        "Sending it as a Bearer token would result in authentication failures. Always read "
        "API documentation rather than assuming standard conventions.", styles)

    story += section("5.3  OneFrameCache — The Core Innovation", styles)
    story.append(p(
        "OneFrameCache is the most important and technically interesting class in the entire "
        "project. Every interview question about this project will eventually circle back here. "
        "Understand every line.", styles))

    story += subsection("5.3.1  The State: Ref[F, Map[Rate.Pair, Rate]]", styles)
    story += code_block("""\
// The in-memory cache: a map from currency pair to the most recently fetched rate
private val ref: Ref[F, Map[Rate.Pair, Rate]]

// Ref is cats-effect's atomic reference — like AtomicReference, but composable
// with the effect system. Key properties:
//   - ref.get: F[Map]      — read, always non-blocking
//   - ref.set(m): F[Unit]  — atomic write, non-blocking
//   - ref.update(f): F[Unit] — atomic read-modify-write

// A single lock-free, thread-safe cell. No synchronized blocks, no semaphores.

override def get(pair: Rate.Pair): F[Error Either Rate] =
  ref.get.map { cache =>
    cache.get(pair).toRight(Error.OneFrameLookupFailed(s"Rate for $pair not in cache"))
  }""", styles)

    story.append(p("This is O(1) for every client request. The map lookup is pure and cheap. "
        "No network calls, no locking, no blocking.", styles))

    story += subsection("5.3.2  The 72 Pairs: Computed Once at Construction", styles)
    story += code_block("""\
private val allPairs: List[Rate.Pair] =
  for {
    from <- Currency.values    // 9 currencies
    to   <- Currency.values    // 9 currencies
    if from != to              // exclude USD/USD, EUR/EUR, etc.
  } yield Rate.Pair(from, to)

// Result: 9 × 8 = 72 pairs, computed ONCE when the cache is created.
// Reused on every refresh cycle — no allocation per refresh.""", styles)

    story += subsection("5.3.3  The Refresh Stream — The Most Important Code", styles)
    story.append(p(
        "The refresh stream is an infinite fs2 stream that keeps the cache up to date. "
        "Read this carefully:", styles))
    story += code_block("""\
val refresh: Stream[F, Unit] =
  // Part 1: immediate warm-up fetch on startup
  Stream.eval(doRefresh) ++
  // Part 2: periodic refresh loop, forever
  Stream.repeatEval {
    val currentSleep: F[Unit] =
      intervalRef.get.flatMap(d => Timer[F].sleep(d))

    // Race the scheduled sleep against the interval-change signal.
    // If the user calls PUT /config/refresh-interval:
    //   → intervalRef.set(newDuration) fires
    //   → intervalRef.discrete emits the new value
    //   → the race resolves, cancelling the sleep fiber
    //   → doRefresh runs immediately (no waiting for old sleep to finish)
    val interruptibleSleep: F[Unit] =
      Concurrent[F].race(
        currentSleep,                                    // Left: sleep normally
        intervalRef.discrete.drop(1).head.compile.drain  // Right: interval changed
      ).void

    interruptibleSleep >> doRefresh
  }""", styles, caption="The refresh stream — the backbone of the caching system")

    story.append(p("<b>Why <code>Stream.eval(doRefresh)</code> first?</b> This runs the initial "
        "warm-up fetch BEFORE the HTTP server accepts any connections (because in Main.scala, "
        "the cache refresh stream is started before the server stream). If we didn't do this, "
        "the first client request would hit an empty cache and get an error.", styles))
    story.append(p("<b>Why <code>Concurrent.race</code>?</b> After each refresh, the code sleeps "
        "for the configured interval. But if the user changes the interval via the API, they "
        "expect it to take effect immediately — not after the current sleep finishes. "
        "<code>race</code> runs two F[_] concurrently. The first one to complete wins. The "
        "other is cancelled. If the sleep wins, the interval didn't change. If the signal "
        "wins, the interval changed and we refresh immediately.", styles))

    story += key_point(
        "'How does immediate interval change work?' — Concurrent.race. We race the sleep "
        "against intervalRef.discrete (a stream that emits whenever setInterval is called). "
        "When setInterval fires, the discrete stream emits, the race resolves, the sleep "
        "fiber is cancelled, and doRefresh runs immediately. This is pure functional "
        "concurrency — no threads, no locks, no callbacks.", styles)

    story += subsection("5.3.4  doRefresh — The Atomic Update", styles)
    story += code_block("""\
private def doRefresh: F[Unit] = {
  val startNs = System.nanoTime()
  live.fetchAll(allPairs).flatMap {
    case Right(rates) =>
      val newCache   = rates.map(r => r.pair -> r).toMap
      val durationMs = (System.nanoTime() - startNs) / 1_000_000.0
      val now        = Instant.now()

      // Atomically replace the ENTIRE map.
      // Readers never see a half-populated cache.
      // A client reading during a refresh sees either the old complete map
      // or the new complete map — never a mix.
      ref.set(newCache) >>
        lastRefreshedAtRef.set(Some(now)) >>
        eventBus.publish(LogEvent.CacheRefresh(newCache.size, durationMs, now.toString)) >>
        Sync[F].delay(logger.info(s"Cache refreshed: ${newCache.size} pairs"))

    case Left(err) =>
      // LOG AND CONTINUE — do NOT crash the stream.
      // Stale data is better than no data.
      val reason = err.toString
      Sync[F].delay(logger.error(s"Cache refresh failed: $reason")) >>
        eventBus.publish(LogEvent.CacheRefreshFailed(reason, Instant.now().toString))
  }
  .handleErrorWith { e =>
    // Guard against unexpected exceptions — same error-is-logged-not-fatal pattern
    val reason = Option(e.getMessage).getOrElse(e.getClass.getSimpleName)
    Sync[F].delay(logger.error(s"Cache refresh threw: $reason")) >>
      eventBus.publish(LogEvent.CacheRefreshFailed(reason, Instant.now().toString))
  }
}""", styles)

    story += info_box(
        "The pattern 'log the error, keep serving stale data' is a deliberate resilience "
        "decision. If One-Frame is temporarily down, clients still receive the last known "
        "rates rather than errors. The SSE bus broadcasts the failure event to any connected "
        "browsers in real time, so operators can see the problem without tailing logs.", styles)

    story += section("5.4  EventBus — Fan-Out Pub/Sub", styles)
    story += code_block("""\
// fs2.concurrent.Topic[F, Option[LogEvent]]
// Topic is a functional pub/sub channel:
//   - publish: sends to ALL current subscribers simultaneously
//   - subscribe: returns Stream[F, LogEvent] — each subscription is independent

class EventBus[F[_]: Concurrent](topic: Topic[F, Option[LogEvent]]) {

  def publish(event: LogEvent): F[Unit] =
    topic.publish1(Some(event))

  def subscribe: Stream[F, LogEvent] =
    topic.subscribe(128)      // 128-event buffer per subscriber
         .collect { case Some(e) => e }  // filter out the initial None
}""", styles)

    story.append(p("The <code>128</code> buffer means: if a subscriber is slow (a browser with "
        "a laggy connection), the producer (cache refresh, HTTP handler) doesn't wait. Up to "
        "128 events queue up; if the subscriber falls further behind, events are dropped "
        "silently. This is the correct behavior for a logging/monitoring bus.", styles))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 6
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("6", "The Program Layer", styles)
    story.append(p(
        "The program layer exists solely to translate between error types and to isolate "
        "the HTTP layer from the service layer. It is thin by design.", styles))
    story.append(sp(2))

    story += section("6.1  Why Does This Layer Exist?", styles)
    story.append(p(
        "Consider the alternative: the HTTP route imports <code>services.rates.errors.Error</code> "
        "directly and pattern-matches on it to decide the HTTP response code. Now, if you "
        "rename that error type or add a new variant, you must change the HTTP layer too. "
        "The program layer breaks this coupling.", styles))
    story += code_block("""\
// Service layer error (services.rates.errors):
sealed trait Error
object Error {
  final case class OneFrameLookupFailed(msg: String) extends Error
}

// Program layer error (programs.rates.errors):
sealed trait Error extends Exception
object Error {
  final case class RateLookupFailed(msg: String) extends Error {
    override def getMessage: String = msg  // needed — case class doesn't forward to Exception
  }
}

// Translation function — the ONLY place where service errors become program errors:
def toProgramError(e: service.Error): program.Error =
  program.Error.RateLookupFailed(e.toString)""", styles)

    story += section("6.2  EitherT — Clean Error Propagation", styles)
    story += code_block("""\
def get(request: GetRatesRequest): F[program.Error Either Rate] =
  EitherT(service.get(Rate.Pair(request.from, request.to)))
    .leftMap(toProgramError)
    .value

// Without EitherT, this would be:
service.get(pair).map(_.left.map(toProgramError))

// With EitherT it's more readable and composes with further operations if needed.
// EitherT is a monad transformer — wraps F[Either[E,A]] and provides
// map, flatMap, leftMap that work on the inner Either.""", styles)

    story.append(p("The <code>Functor</code> constraint (<code>F[_]: Functor</code>) is the "
        "minimum required for <code>EitherT.leftMap</code>. Using the most minimal constraint "
        "is good practice — it makes the code more general and tests easier to write.", styles))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 7
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("7", "The HTTP Layer", styles)
    story.append(p(
        "The HTTP layer is the boundary between the internal system and the outside world. "
        "Every request enters here. Every response exits here. Error handling, input "
        "validation, request tracing, and SSE streaming are all managed here.", styles))

    story += section("7.1  Query Parameter Validation", styles)
    story.append(p(
        "The scaffold had broken query parameter handling that returned 404 instead of 400 "
        "for missing or invalid parameters. The fix uses http4s's validating extractors:", styles))
    story += code_block("""\
// Step 1: Teach http4s how to parse a Currency from a query string value
implicit val currencyDecoder: QueryParamDecoder[Currency] =
  QueryParamDecoder[String].emap { s =>
    Currency.fromString(s)           // returns Either[String, Currency]
      .leftMap(ParseFailure(_, ""))  // lifts Left into ParseFailure
  }

// Step 2: Named extractors for the 'from' and 'to' parameters
// OptionalValidating = matches even when param is absent (returns Invalid),
//                      rather than falling through to a 404.
object FromQueryParam extends OptionalValidatingQueryParamDecoderMatcher[Currency]("from")
object ToQueryParam   extends OptionalValidatingQueryParamDecoderMatcher[Currency]("to")

// Step 3: In the route, convert None (absent) to Invalid for uniform handling
def requireParam[A](v: Option[ValidatedNel[ParseFailure, A]], name: String) =
  v.getOrElse(Validated.invalidNel(ParseFailure(s"Missing '$name' query parameter", "")))""", styles)

    story += info_box(
        "The key insight: OptionalValidating matches the route EVEN when parameters are "
        "absent, returning Invalid. A Required matcher would make the route fall through to "
        "a 404 when 'from' or 'to' is missing. We want 400 (bad request), not 404 (not found). "
        "Using Optional gives us control over the error response.", styles)

    story += section("7.2  The Rates Route — Step by Step", styles)
    story.append(p("Walk through exactly what happens on every GET /rates request:", styles))
    story += code_block("""\
GET /rates?from=USD&to=JPY
        ↓
1. http4s matches the route pattern: GET -> Root :? FromQueryParam(vFrom) +& ToQueryParam(vTo)

2. Extract and validate both params:
   vFrom = Some(Valid(USD))   or  Some(Invalid(NEL[ParseFailure]))  or  None
   vTo   = Some(Valid(JPY))   or  ...

3. requireParam converts None → Invalid, so we always have ValidatedNel

4. Check: from != to (self-pairs not supported)
   USD → USD is invalid (exchange rate with yourself is 1.0, meaningless)

5. If either is Invalid: collect all ParseFailures, join messages, return 400
   → "Invalid 'from' currency: Unknown currency: FOO"

6. If both Valid:
   a. Generate requestId = UUID.randomUUID().toString.take(8)
   b. Record startNs = System.nanoTime()
   c. Call program.get(GetRatesRequest(from, to))

7. program.get delegates to cache.get(Rate.Pair(from, to))
   → O(1) map lookup, zero network calls

8. On Right(rate):
   a. Format JSON response: {"from":"USD","to":"JPY","price":149.50,"timestamp":"..."}
   b. Compute durationMs = (System.nanoTime() - startNs) / 1_000_000.0
   c. Publish ProxyRequest SSE event to EventBus
   d. Return 200 with X-Request-ID header

9. On Left(programError):
   a. Publish ProxyRequest SSE event (status=500)
   b. Return 500 with error message""", styles, caption="Complete flow of a GET /rates request")

    story += section("7.3  SSE Endpoint — Per-Connection Stream Topology", styles)
    story += code_block("""\
GET /events
        ↓
// Each connection gets TWO streams merged together:

// Stream 1: shared EventBus subscription (fan-out)
//   - CacheRefresh events (every 4 minutes, published by OneFrameCache)
//   - ProxyRequest events (per client request, published by RatesHttpRoutes)
//   - CacheRefreshFailed events (on errors, published by OneFrameCache)
val busStream = eventBus.subscribe.map { event =>
  ServerSentEvent(data = Some(event.asJson.noSpaces))
}

// Stream 2: per-connection heartbeat (every 30 seconds, NOT shared via bus)
//   - serverTimeMs: for clock skew correction in the browser
//   - lastRefreshedAt: resyncs the freshness timer after reconnect
val heartbeatStream =
  fs2.Stream.repeatEval {
    for {
      lastRefreshedAt <- cache.getLastRefreshedAt  // reads from Ref — no network
      serverTimeMs     = System.currentTimeMillis()
    } yield ServerSentEvent(data = Some(
      LogEvent.Heartbeat(serverTimeMs, lastRefreshedAt.map(_.toString)).asJson.noSpaces
    ))
  }.metered(30.seconds)

// Merged: both run concurrently for this connection's lifetime
val sseStream = busStream.merge(heartbeatStream)
Ok(sseStream.through(ServerSentEvent.encoder[F]),
   `Content-Type`(MediaType.`text/event-stream`))""", styles)

    story += key_point(
        "Why is the heartbeat per-connection rather than published to the EventBus? Because "
        "the heartbeat carries System.currentTimeMillis() at emission time. If published via "
        "the bus, the timestamp would be generated at publish time but received by subscribers "
        "milliseconds (or seconds) later — making the clock skew calculation wrong. Each "
        "connection generates its own heartbeat with its own 'now'.", styles)

    story += section("7.4  The Middleware Stack", styles)
    story += code_block("""\
// Composition order (outer to inner):
appMiddleware(routesMiddleware(allRoutes).orNotFound)

// routesMiddleware:
AutoSlash(http)
// → normalizes /rates/ to /rates so both URLs work

// .orNotFound:
// → converts HttpRoutes[F] (partial, may 404) to HttpApp[F] (total, always responds)
// → unmatched routes become 404 responses

// appMiddleware:
Timeout(config.http.timeout)(http)
// → any handler taking > 40s returns 503 Service Unavailable
// → prevents slow upstream calls from holding threads indefinitely

// CORS — applied ONLY to /events and /config
CORS.policy.withAllowOriginAll(eventsRoutes)
// → /rates does NOT have CORS because it's called through Nginx (same origin)
// → /events and /config are called directly by the browser (cross-origin in dev)""", styles)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 8
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("8", "Application Wiring: Main.scala", styles)
    story.append(p(
        "Main.scala is where everything comes together. It is the entry point and the "
        "wiring diagram of the entire application. The most important concept here is "
        "<b>stream composition</b> — how the cache refresh loop and the HTTP server "
        "run concurrently with a shared lifecycle.", styles))

    story += code_block("""\
// The complete application startup sequence (simplified):

object Main extends IOApp {
  def run(args: List[String]): IO[ExitCode] = {
    // 1. Load config from application.conf via PureConfig
    Config.stream[IO].flatMap { config =>

    // 2. HTTP connection pool for One-Frame client calls
    BlazeClientBuilder[IO](global).resource.use { client =>

    // 3. Event bus for SSE fan-out
    EventBus.create[IO].flatMap { eventBus =>

    // 4. Cache + refresh stream (returns BOTH)
    RatesServices.cachedLive[IO](client, config.oneFrame, eventBus).flatMap {
      case (cacheService, cacheRefreshStream) =>

    // 5. Module wires all dependencies into HttpApp
    val module = new Module[IO](config, cacheService, cache, eventBus)

    // 6. HTTP server stream
    BlazeServerBuilder[IO](global)
      .bindHttp(config.http.port, config.http.host)
      .withHttpApp(module.httpApp)
      .serve

    // THE KEY LINE:
    // Run cache refresh AND HTTP server concurrently.
    // Neither can run without the other.
    // If either terminates (crash, shutdown), the merged stream stops.
    .drain
    .merge(cacheRefreshStream)  // ← this is where it all comes together
  }}}}}
}""", styles, caption="Main.scala stream composition")

    story += section("8.1  Why .merge and Not >> (Sequential)?", styles)
    story += code_block("""\
// WRONG: sequential
cacheRefreshStream >> httpServerStream
// This would run the cache refresh FIRST (infinite loop), server NEVER starts.

// WRONG: concurrent but unlinked
// Running them in separate threads and hoping for the best.

// CORRECT: merge
httpServerStream.merge(cacheRefreshStream)
// Both run concurrently as separate fibers managed by cats-effect.
// If either terminates:
//   - server crashes → merged stream ends → app shuts down
//   - cache stream panics → merged stream ends → app shuts down
// Their lifecycles are tied together. Clean, no orphaned fibers.""", styles)

    story += key_point(
        "stream.merge() is how you compose concurrent, long-lived streams in fs2. It's "
        "like running two threads, but managed by the effect system — no raw threads, no "
        "synchronized, no ExecutionContext juggling. The merged stream ends when either "
        "sub-stream ends, giving you automatic lifecycle management.", styles)

    story += section("8.2  Resource Management", styles)
    story.append(p(
        "<code>BlazeClientBuilder[F](ec).resource</code> is a cats-effect "
        "<code>Resource[F, Client[F]]</code>. Resource guarantees that:", styles))
    story += [
        bp("The HTTP connection pool is created <i>before</i> the server starts accepting requests.", styles),
        bp("The pool is cleanly shut down <i>after</i> the server stops, even if the shutdown is triggered by an exception.", styles),
        bp("No connection pool is leaked if startup fails partway through.", styles),
    ]
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 9
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("9", "Docker and Infrastructure", styles)
    story.append(p(
        "The project is fully containerized with three services: the Scala backend, the "
        "React frontend served by Nginx, and the One-Frame API. Understanding the Docker "
        "setup is essential for explaining how the system runs.", styles))

    story += section("9.1  Backend Dockerfile — Multi-Stage Build", styles)
    story += code_block("""\
# Stage 1: Build (hseeberger/scala-sbt — ~2GB with JDK + sbt)
FROM hseeberger/scala-sbt:17.0.2_1.6.2_2.13.8 AS builder

WORKDIR /app

# Copy build files FIRST — Docker layer cache.
# If only source changes (not build.sbt), this layer is reused.
# sbt update (dependency download) = the expensive step.
COPY build.sbt .
COPY project/ project/
RUN sbt update                    # download all dependencies → cached in Docker layer

COPY src/ src/
RUN sbt assembly                  # compile + create fat JAR

# Stage 2: Runtime (eclipse-temurin JRE — ~80MB, no build tools)
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app
COPY --from=builder /app/target/scala-2.13/forex-assembly.jar ./forex-assembly.jar

EXPOSE 9090
CMD ["java", "-jar", "forex-assembly.jar"]""", styles,
        caption="Backend Dockerfile — multi-stage build separates build tools from runtime")

    story.append(p("<b>Why multi-stage?</b> The builder image needs JDK, sbt, and all build "
        "tooling — approximately 2GB. The runtime image only needs the JRE and the fat JAR "
        "— approximately 80-100MB. Shipping build tools in production is both wasteful and "
        "a security risk (attack surface).", styles))
    story.append(p("<b>Why fat JAR (sbt-assembly)?</b> A fat JAR packages all dependencies "
        "into a single file. No classpath configuration needed at runtime — just "
        "<code>java -jar forex-assembly.jar</code>. The assembly merge strategy handles "
        "conflicts: META-INF signatures are discarded (conflicting JARs each have their own "
        "signature; combining them invalidates all); <code>reference.conf</code> files are "
        "concatenated (multiple libraries use this for default configuration).", styles))

    story += section("9.2  Frontend Dockerfile — Node Builder + Nginx Runtime", styles)
    story += code_block("""\
# Stage 1: Build the React SPA
FROM node:20-alpine AS builder
WORKDIR /app

# Copy package files first — npm ci layer cached until package-lock.json changes
COPY package.json package-lock.json ./
RUN npm ci                          # clean install — reproducible, from lockfile

COPY . .
RUN npm run build                   # Vite produces /app/dist/

# Stage 2: Nginx serves static files and reverse-proxies API calls
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80""", styles, caption="Frontend Dockerfile — Vite builds the SPA, Nginx serves it")

    story += section("9.3  Nginx Configuration — Critical for SSE", styles)
    story += code_block("""\
# nginx.conf — key sections

# API proxy to backend
location /rates {
    proxy_pass http://forex-proxy:9090;
}

# SSE endpoint — CRITICAL configuration
location /events {
    proxy_pass http://forex-proxy:9090;
    proxy_set_header Connection "";     # disable upgrade to keep-alive (SSE uses chunked)
    proxy_http_version 1.1;             # HTTP/1.1 required for chunked transfer
    proxy_buffering off;                # NEVER buffer SSE — frames must reach browser immediately
    proxy_cache off;
    chunked_transfer_encoding on;
    proxy_read_timeout 600s;            # ← THIS IS THE CRITICAL LINE
}

# SPA fallback — React Router client-side routing
location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;  # any unmatched path → index.html
}""", styles)

    story += warning_box(
        "proxy_read_timeout 600s is the single most important Nginx setting in this project. "
        "The default is 60 seconds. If no data flows on an HTTP connection for 60 seconds, "
        "Nginx silently terminates it. Our cache refreshes every 240 seconds — the SSE "
        "connection would die every 60 seconds without this setting. The symptom: the "
        "browser UI shows 'disconnected' and the freshness timer breaks. The SSE heartbeat "
        "(every 30 seconds) provides an additional defense against proxies we don't control.", styles)

    story += section("9.4  Docker Compose — Three-Service Orchestration", styles)
    story += code_block("""\
services:
  one-frame:                          # The upstream rates API
    image: paidyinc/one-frame
    ports:
      - "18080:8080"                  # 18080 externally to avoid conflicts with other services

  forex-proxy:                        # Our Scala service
    build: .
    ports:
      - "9090:9090"
    environment:
      - ONE_FRAME_URL=http://one-frame:8080    # Docker internal DNS — not localhost!
      - ONE_FRAME_TOKEN=10dc303535874aeccc86a8251e6992f5
    depends_on:
      - one-frame

  frontend:                           # React SPA served by Nginx
    build: ./frontend
    ports:
      - "3001:80"                     # Port 3001 — 3000 was taken by another local service
    depends_on:
      - forex-proxy
      - one-frame""", styles)

    story.append(p("<b>Key docker-compose insight</b>: Services communicate via Docker's internal "
        "DNS using service names as hostnames (<code>one-frame</code>, <code>forex-proxy</code>). "
        "The <code>ONE_FRAME_URL</code> environment variable overrides the default localhost URI "
        "so the forex-proxy container talks to the one-frame container, not itself.", styles))
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 10
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("10", "The Frontend Architecture", styles)
    story.append(p(
        "The frontend is a React + Vite + Tailwind single-page application. It serves as "
        "a real-time dashboard for monitoring the proxy service. While it wasn't strictly "
        "required by the assignment, it demonstrates the system working end-to-end and "
        "provides visual proof that all constraints are met.", styles))

    story += section("10.1  Module-Level Singletons — The Core Pattern", styles)
    story.append(p(
        "The most important architectural pattern in the frontend is the "
        "<b>module-level singleton with React subscriber hooks</b>. You'll see this in "
        "useEventStream.ts and useRefreshInterval.ts.", styles))
    story += code_block("""\
// Instead of React Context or Redux, we use module-level globals:

// Module scope (not React, not component) — one instance for the entire app lifetime
let globalEntries: LogEntry[] = [];
let globalConnected = false;
let globalClockOffsetMs = 0;
let globalEs: EventSource | null = null;
const listeners = new Set<Listener>();

// The hook subscribes/unsubscribes on mount/unmount
export function useEventStream() {
  const [entries, setEntries] = useState(globalEntries);
  const [connected, setConnected] = useState(globalConnected);
  const [clockOffsetMs, setClockOffsetMs] = useState(globalClockOffsetMs);

  useEffect(() => {
    const listener = (e, c, o) => { setEntries(e); setConnected(c); setClockOffsetMs(o); };
    listeners.add(listener);
    ensureConnected();    // creates EventSource exactly once (guarded by globalEs)
    return () => listeners.delete(listener);  // cleanup on unmount
  }, []);

  return { entries, connected, clockOffsetMs };
}""", styles)

    story.append(p("<b>Why not React Context?</b> Context re-renders the entire subtree on every "
        "update. With SSE events arriving frequently (every request, every 30 seconds), this "
        "would cause excessive re-renders. Module-level globals with targeted setState calls "
        "only re-render the specific components that subscribe.", styles))
    story.append(p("<b>Why not Redux?</b> Redux is appropriate for complex state with many "
        "interactions between slices. Here, each piece of state has a single data source "
        "(SSE stream or one HTTP endpoint). The singleton pattern is simpler and sufficient.", styles))

    story += section("10.2  The SSE Heartbeat — Solving Three Problems at Once", styles)
    story.append(p(
        "The server emits a Heartbeat event every 30 seconds per open SSE connection. "
        "This single feature solves three distinct problems:", styles))

    problems = [
        ("Problem 1: Proxy/NAT Timeout",
         "TCP connections through proxies (Nginx, corporate firewalls, NAT) are closed "
         "if idle for too long. Default Nginx proxy_read_timeout is 60 seconds. Cache "
         "refreshes every 240 seconds. Solution: emit a heartbeat every 30 seconds to "
         "keep the connection alive."),
        ("Problem 2: Clock Skew",
         "The browser's Date.now() and the server's System.currentTimeMillis() can "
         "diverge by seconds on VMs, CI containers, and developer laptops. The heartbeat "
         "carries serverTimeMs. The browser computes: clockOffsetMs = serverTimeMs - "
         "Date.now(). All age calculations use Date.now() + clockOffsetMs."),
        ("Problem 3: Cold Start / Reconnect",
         "After a page reload or SSE reconnect, the browser has no knowledge of when "
         "the last cache refresh happened. The heartbeat carries lastRefreshedAt — the "
         "ISO-8601 UTC timestamp of the last successful cache refresh. The freshness "
         "timer is seeded from this within 30 seconds of connection."),
    ]
    for title, desc in problems:
        story += callout(title, desc, styles, CYAN)

    story += section("10.3  FreshnessBar — The Hardest Component", styles)
    story.append(p(
        "The cache freshness timer had multiple bugs that required deep investigation. "
        "Understanding the root causes prepares you to explain the solution.", styles))

    story += subsection("10.3.1  Root Cause Analysis of the Bugs", styles)
    story += code_block("""\
// BUG 1: setInterval accumulation
function ensureLoaded() {
  if (globalLoaded || globalLoading) return;
  fetchStatus();
  setInterval(fetchStatus, 30_000);  // ← ID not stored!
}
// Problem: when fetchStatus() fails, globalLoading resets to false but
// globalLoaded stays false. Next component mount calls ensureLoaded() again.
// Creates another interval. With 5 components using this hook, mounting,
// unmounting, and HMR (hot module replacement) in dev, dozens of intervals
// accumulate → /config/status is called multiple times per second.

// BUG 2: Nginx proxy_read_timeout 60s
// SSE connections die silently after 60s of no data.
// The browser EventSource auto-reconnects, but the UI briefly shows "disconnected"
// and any events during the reconnect window are missed.

// BUG 3: Background tab timer throttling
// Chrome/Firefox throttle setInterval to once per minute in backgrounded tabs.
// When the user returns to the tab, the setNow(Date.now()) tick fires,
// but it may not fire for up to 60 seconds — the displayed age is stale.

// BUG 4: Clock skew
// Server timestamps are in UTC server time. Browser Date.now() is in browser
// local time. On machines with drifted clocks, the computed age is wrong.""", styles)

    story += subsection("10.3.2  The Final Solution", styles)
    story += code_block("""\
// 1. Store timer ID — prevents accumulation
let globalTimerId: ReturnType<typeof setInterval> | null = null;
if (globalTimerId === null) {
  globalTimerId = setInterval(fetchInterval, 60_000);
}

// 2. Derive lastRefreshedAt from SSE/heartbeat — eliminate polling
// Priority order:
//   (a) SSE CacheRefresh event — live, millisecond-accurate
//   (b) Heartbeat.lastRefreshedAt — server pushes every 30s (survives reconnect)
//   (c) null — cold start, show "Waiting for first heartbeat..."

// 3. Apply clock offset to all age calculations
const correctedNow = Date.now() + clockOffsetMs;  // clockOffsetMs from heartbeat
const ageMs = correctedNow - new Date(lastRefreshedAt).getTime();

// 4. visibilitychange — snap timer on tab activation
useEffect(() => {
  const handler = () => {
    if (document.visibilityState === 'visible') setNow(Date.now());
  };
  document.addEventListener('visibilitychange', handler);
  return () => document.removeEventListener('visibilitychange', handler);
}, []);""", styles)

    story += section("10.4  Frontend Components Overview", styles)
    comp_data = [
        ["Component", "Purpose", "Key Technical Detail"],
        ["StatsPanel", "Live aggregate metrics: One-Frame call count, cache ratio, avg latency", "Derives metrics from SSE event stream history"],
        ["FreshnessBar", "Visual cache age timer with SLA warning thresholds", "Heartbeat-driven; clock-skew corrected; visibilitychange handler"],
        ["RefreshControl", "Slider to change the cache refresh interval (90-300s)", "PUT /config/refresh-interval; triggers immediate reset via Concurrent.race"],
        ["AllPairsGrid", "Grid showing all 72 current exchange rates", "Reads from SSE CacheRefresh event payloads"],
        ["BurstTest", "Fire N concurrent requests, measure latency percentiles", "Promise.all with AbortController; p50/p95/p99 computation"],
        ["RateLimitStressTest", "1000 direct One-Frame requests to observe quota behavior", "Bypasses cache via /one-frame Nginx proxy; detects {\"error\":\"Quota reached\"} in HTTP 200 body"],
        ["EventLog", "Scrollable log of all SSE events with filtering and sorting", "Virtual rendering via manual slice; DetailDrawer for full event inspection"],
        ["ValidationMatrix", "Tests all error cases: invalid currency, self-pair, missing params", "Declarative test matrix; runs all cases in parallel; shows pass/fail badges"],
        ["ForceRefresh", "POST /config/force-refresh button", "Triggers immediate doRefresh outside the normal schedule"],
    ]
    t = Table(comp_data,
              colWidths=[3.8*cm, 5.5*cm, PAGE_W - 2*MARGIN - 9.3*cm],
              style=TableStyle([
                  ('BACKGROUND', (0,0), (-1,0), PURPLE),
                  ('TEXTCOLOR', (0,0), (-1,0), WHITE),
                  ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                  ('FONTSIZE', (0,0), (-1,-1), 8.5),
                  ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                  ('BACKGROUND', (0,1), (-1,-1), WHITE),
                  ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_100]),
                  ('GRID', (0,0), (-1,-1), 0.3, GRAY_200),
                  ('VALIGN', (0,0), (-1,-1), 'TOP'),
                  ('TOPPADDING', (0,0), (-1,-1), 5),
                  ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                  ('LEFTPADDING', (0,0), (-1,-1), 5),
              ]))
    story.append(t)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 11
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("11", "Testing Strategy", styles)
    story.append(p(
        "Every test in this project runs in-process with no real network calls, no real "
        "One-Frame server, and no Docker. Tests are deterministic, fast, and CI-friendly. "
        "The tagless final pattern makes this possible.", styles))

    story += section("11.1  Test Philosophy", styles)
    story.append(p(
        "The guiding principle: <b>test at the boundary that matters, fake everything below it</b>.", styles))
    story += [
        bp("<b>OneFrameLiveSpec</b> — tests the HTTP client layer with a fake in-process server. Verifies correct URL construction, correct header (token), correct JSON parsing.", styles),
        bp("<b>OneFrameCacheSpec</b> — tests the cache lifecycle. Verifies empty → populated transition, correct map lookup, error handling.", styles),
        bp("<b>RatesHttpRoutesSpec</b> — tests the HTTP boundary with a stub program. Verifies correct status codes, response bodies, query parameter validation.", styles),
        bp("<b>ProgramSpec</b> — tests error translation with cats.Id (pure, synchronous). Verifies service errors become program errors.", styles),
    ]

    story += section("11.2  OneFrameLiveSpec — Fake HTTP Client", styles)
    story += code_block("""\
// Create an in-process HTTP client that returns a pre-built response
def fakeClient(body: String, status: Status = Status.Ok): Client[IO] =
  Client.fromHttpApp(
    HttpRoutes.of[IO] { case _ => Response[IO](status).withEntity(body) }
      .orNotFound
  )

// Test: successful fetch
test("get returns Right when API responds with valid JSON") {
  val json = `[{"from":"USD","to":"JPY","price":149.5,"time_stamp":"..."}]`
  val client = fakeClient(json)
  val live   = new OneFrameLive[IO](client, config)
  live.get(Rate.Pair(USD, JPY)).unsafeRunSync() should be (Right(_))
}

// Test: token header is sent (NOT Authorization: Bearer)
test("token header is sent on every request") {
  var capturedToken = ""
  val spyClient = Client.fromHttpApp(
    HttpRoutes.of[IO] { case req =>
      capturedToken = req.headers.get("token").map(_.value).getOrElse("")
      Ok(validJson)
    }.orNotFound
  )
  val live = new OneFrameLive[IO](spyClient, config)
  live.get(Rate.Pair(USD, JPY)).unsafeRunSync()
  capturedToken shouldBe config.token
}""", styles)

    story += section("11.3  OneFrameCacheSpec — Testing the Stream", styles)
    story += code_block("""\
test("cache is empty before refresh") {
  val (cache, _) = OneFrameCache.create[IO](fakeLive, 4.minutes, fakeBus).unsafeRunSync()
  cache.get(Rate.Pair(USD, JPY)).unsafeRunSync() shouldBe a [Left[_, _]]
}

test("cache is populated after refresh stream runs") {
  val (cache, refreshStream) =
    OneFrameCache.create[IO](fakeLive, 4.minutes, fakeBus).unsafeRunSync()

  // Run ONLY the initial eval — not the infinite periodic loop
  refreshStream.take(1).compile.drain.unsafeRunSync()
  //             ^^^^^^^^
  // This is the crucial line. Without .take(1), the stream runs forever.
  // Stream.eval(doRefresh) is the first element.
  // .take(1) consumes exactly that element and stops.

  cache.get(Rate.Pair(USD, JPY)).unsafeRunSync() shouldBe a [Right[_, _]]
}""", styles)

    story += section("11.4  RatesHttpRoutesSpec — Testing the HTTP Boundary", styles)
    story += code_block("""\
// Stub program — returns a fixed result regardless of input
class StubProgram(result: Either[ProgramError, Rate]) extends RatesAlgebra[IO] {
  def get(req: GetRatesRequest): IO[Either[ProgramError, Rate]] = IO.pure(result)
}

// Test: valid request returns 200
test("200 for valid USD to JPY request") {
  val program = new StubProgram(Right(sampleRate))
  val routes  = new RatesHttpRoutes[IO](program, fakeEventBus).routes
  val request = Request[IO](GET, uri"/rates?from=USD&to=JPY")

  routes.orNotFound(request).unsafeRunSync().status shouldBe Status.Ok
}

// Test: invalid currency code returns 400
test("400 for invalid currency code") {
  val routes  = new RatesHttpRoutes[IO](stubProgram, fakeEventBus).routes
  val request = Request[IO](GET, uri"/rates?from=XXX&to=JPY")

  routes.orNotFound(request).unsafeRunSync().status shouldBe Status.BadRequest
}

// Test: missing parameter returns 400 (not 404!)
test("400 for missing from parameter") {
  val routes  = new RatesHttpRoutes[IO](stubProgram, fakeEventBus).routes
  val request = Request[IO](GET, uri"/rates?to=JPY")  // 'from' missing

  routes.orNotFound(request).unsafeRunSync().status shouldBe Status.BadRequest
}""", styles)

    story += section("11.5  ProgramSpec — Pure Testing with cats.Id", styles)
    story += code_block("""\
// cats.Id is the identity monad: Id[A] = A
// A service returning Id[Either[E, A]] returns Either[E, A] directly — no IO, no Future

class StubService(result: Either[ServiceError, Rate]) extends Algebra[Id] {
  def get(pair: Rate.Pair): Id[Error Either Rate] = result
}

test("Right passes through without modification") {
  val service = new StubService(Right(sampleRate))
  val program = new Program[Id](service)
  program.get(GetRatesRequest(USD, JPY)) shouldBe Right(sampleRate)
}

test("Service Left is translated to program Left") {
  val serviceError = Error.OneFrameLookupFailed("test error")
  val service      = new StubService(Left(serviceError))
  val program      = new Program[Id](service)

  program.get(GetRatesRequest(USD, JPY)) should matchPattern {
    case Left(program.Error.RateLookupFailed(_)) =>
  }
}""", styles)

    story += key_point(
        "ProgramSpec uses cats.Id as F. This means the test calls program.get(...) and gets "
        "back a plain Either immediately — no IO.unsafeRunSync(), no timeouts, no threads. "
        "This is the power of tagless final: the business logic is completely decoupled from "
        "the execution model.", styles)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # CHAPTER 12
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("12", "Key Interview Questions and Answers", styles)
    story.append(p(
        "This chapter contains the questions you are most likely to be asked, with complete "
        "answers. Study each answer until you can reproduce it from memory. Then practice "
        "saying it out loud — the way you explain something matters as much as the content.", styles))
    story.append(sp(2))

    story += section("12.1  Architecture Questions", styles)

    story += interview_qa(
        "Walk me through the overall architecture of your solution.",
        "The system has five layers: domain (pure data types), service (OneFrameCache backed "
        "by Ref[F, Map], with a proactive batch refresh stream), program (error translation), "
        "HTTP (http4s routes with validation), and wiring (Main.scala merges the cache refresh "
        "stream with the server stream so they run concurrently). The key insight: instead of "
        "forwarding each client request to One-Frame, I fetch all 72 pairs in one batch call "
        "every 4 minutes and serve everything from memory. This keeps us at 360 API calls/day "
        "— well under the 1,000 limit — while serving unlimited client requests.",
        styles)

    story += interview_qa(
        "Why 4 minutes specifically?",
        "The math: 5-minute freshness SLA minus 1-minute safety buffer equals 4-minute "
        "maximum refresh interval. At 4 minutes: (60÷4)×24 = 360 calls/day, which is 64% "
        "below the 1,000/day limit. I could go up to 5 minutes but that leaves zero buffer "
        "if a refresh is slightly delayed.",
        styles)

    story += interview_qa(
        "What happens if One-Frame is down?",
        "The cache continues to serve stale data. In doRefresh, both the typed error path "
        "(Left from fetchAll) and the exception path (handleErrorWith) log the failure, publish "
        "a CacheRefreshFailed event to the SSE bus so connected browsers can see it in real "
        "time, and return without crashing the refresh stream. The old cache map remains intact. "
        "The SLA would eventually be violated if One-Frame stays down, but clients continue to "
        "get responses rather than errors.",
        styles)

    story += interview_qa(
        "How do you handle thread safety?",
        "Ref[F, Map[Rate.Pair, Rate]] from cats-effect. It's a lock-free atomic reference — "
        "implemented as AtomicReference under the hood but wrapped in the effect system for "
        "composability. ref.get is non-blocking. ref.set replaces the entire map atomically — "
        "a reader in the middle of a refresh sees either the old complete map or the new "
        "complete map, never a partially-updated state. No synchronized, no locks, no "
        "semaphores.",
        styles)

    story += section("12.2  Functional Programming Questions", styles)

    story += interview_qa(
        "What is tagless final and why did you use it?",
        "Tagless final is a design pattern where your service algebras are parameterized over "
        "an effect type F[_] instead of a concrete type like IO. In production, F = IO. In "
        "tests, F = cats.Id, which means Id[A] = A — no effects at all. The same code runs "
        "synchronously in tests, removing any need for IO.unsafeRunSync() or async test "
        "boilerplate. ProgramSpec tests the entire program layer this way. It also means you "
        "can run the same logic with different effect types — IO for production, Task for "
        "different runtimes, Resource for scoped computations.",
        styles)

    story += interview_qa(
        "Explain Concurrent.race and why you use it.",
        "Concurrent.race takes two F[_] computations and runs them in parallel. The first one "
        "to complete wins — its result is returned. The other fiber is cancelled. I use it in "
        "the cache refresh loop to implement immediate interval changes. After each refresh, I "
        "race the scheduled sleep (Timer.sleep(interval)) against intervalRef.discrete — a "
        "stream that emits whenever setInterval is called. If the user changes the interval "
        "via the API, discrete emits immediately, the race resolves, the sleep fiber is "
        "cancelled, and doRefresh runs immediately. Without race, the user would have to "
        "wait for the current sleep to finish before the new interval took effect.",
        styles)

    story += interview_qa(
        "What is fs2.concurrent.Topic and how does it provide fan-out?",
        "Topic is a functional pub/sub primitive. Each call to .subscribe() returns an "
        "independent Stream that receives every event published to the topic. When "
        "eventBus.publish(event) is called, every subscriber simultaneously receives that "
        "event — it's broadcast, not unicast. Each subscriber has its own buffer (128 events) "
        "so a slow browser connection doesn't block the One-Frame refresh or other browser "
        "connections. This is the foundation of the SSE endpoint: each browser connection "
        "is one subscriber.",
        styles)

    story += section("12.3  HTTP and Validation Questions", styles)

    story += interview_qa(
        "How does query parameter validation work?",
        "I use OptionalValidatingQueryParamDecoderMatcher with a QueryParamDecoder[Currency] "
        "that calls Currency.fromString and lifts the Either into ParseFailure via .emap. "
        "The key is 'Optional' — it matches even when the parameter is absent, returning "
        "Invalid rather than falling through to a 404. This gives me control over the error "
        "response: I convert None to Invalid, collect all failures from both parameters using "
        "ValidatedNel's applicative accumulation, and return a single 400 with all error "
        "messages. Using Required would have sent clients a confusing 404 for missing params.",
        styles)

    story += interview_qa(
        "Why does the endpoint return 400 instead of 404 for missing parameters?",
        "404 means 'the resource does not exist.' The /rates endpoint definitely exists — "
        "the problem is that the request is malformed (missing a required parameter). 400 "
        "means 'bad request' — the client sent an invalid request. From the client's "
        "perspective, a 404 response to a missing query parameter is confusing and hard to "
        "debug. 400 with a clear error message ('Missing from query parameter') is actionable.",
        styles)

    story += interview_qa(
        "Why is there a program layer between the service and HTTP layers?",
        "Decoupling error types. The HTTP layer should not import service-layer error types "
        "directly — doing so couples the HTTP layer to the service implementation. The program "
        "layer translates service errors (services.rates.errors.Error) into program errors "
        "(programs.rates.errors.Error) and that is the ONLY place where this translation "
        "happens. If I restructure service errors, only the program layer changes — not a "
        "single HTTP file needs to be touched.",
        styles)

    story += section("12.4  Infrastructure Questions", styles)

    story += interview_qa(
        "Why multi-stage Docker builds?",
        "To minimize the production image size and attack surface. The builder stage needs "
        "the full JDK, sbt, and all build tooling — approximately 2GB. The runtime stage "
        "only needs the JRE and the assembled fat JAR — approximately 80-100MB. Shipping "
        "build tools in a production container is unnecessary: it increases image transfer "
        "time, uses more disk, and exposes more potential attack surface (sbt, scalac, "
        "and their dependencies are not needed at runtime).",
        styles)

    story += interview_qa(
        "What's the most important Nginx setting in your deployment and why?",
        "proxy_read_timeout 600s on the /events location. The default is 60 seconds. Nginx "
        "closes a connection if no data flows for that duration. Our cache refreshes every "
        "240 seconds — the SSE connection would be silently killed after 60 seconds, causing "
        "the browser to show 'disconnected' and lose the freshness timer. 600 seconds gives "
        "10 minutes of silence tolerance. The 30-second SSE heartbeat provides additional "
        "protection against third-party proxies we don't control.",
        styles)

    story += interview_qa(
        "How do services communicate inside Docker Compose?",
        "Via Docker's internal DNS. Each service is reachable by its service name as a "
        "hostname. forex-proxy connects to one-frame at http://one-frame:8080 (not localhost). "
        "The Nginx container connects to forex-proxy at http://forex-proxy:9090. The "
        "ONE_FRAME_URL environment variable overrides the default localhost URI from "
        "application.conf with the Docker-internal hostname.",
        styles)

    story += section("12.5  Real-World Scenarios", styles)

    story += interview_qa(
        "How does your system handle a sudden spike of 1000 concurrent requests?",
        "All 1000 requests are served from the in-memory cache map — O(1) lookups per "
        "request. Each request is handled by a separate cats-effect fiber (lightweight, "
        "not OS thread). The Blaze server uses NIO non-blocking I/O so a burst of 1000 "
        "requests doesn't require 1000 threads. No One-Frame API calls are made for any "
        "of the 1000 requests. The only bottleneck is CPU for JSON serialization, which "
        "is fast for the small Rate objects.",
        styles)

    story += interview_qa(
        "What happens when One-Frame returns HTTP 200 with an error body?",
        "One-Frame returns HTTP 200 with {\"error\":\"Quota reached\"} when the rate limit is "
        "exceeded. This was discovered empirically with the RateLimitStressTest component. "
        "The backend currently treats this as a JSON parse failure (the expected List "
        "structure is absent) and logs it as a cache refresh error. The old cache remains "
        "valid. The frontend stress test detects quota by checking the response body for "
        "the 'error' key regardless of HTTP status — you can't rely on status codes here.",
        styles)

    story += interview_qa(
        "If you had more time, what would you improve?",
        "Three things: First, structured logging with correlation IDs (the requestId from "
        "X-Request-ID) so you can trace a client request through all log lines. Second, "
        "metrics (Prometheus/Micrometer) for cache hit rate, refresh duration, and error "
        "rate — the SSE event stream provides this for the demo but not for production "
        "monitoring. Third, a more sophisticated error model: the current cache-empty "
        "response is a generic Left; it would be better to distinguish 'never populated' "
        "(cold start) from 'pair not in last response' (One-Frame data issue).",
        styles)

    story.append(sp(3))
    story += section("12.6  One-Minute Summary (For When They Ask 'Tell Me About Your Solution')", styles)
    story += callout(
        "THE ELEVATOR PITCH",
        "I built a Scala proxy for a currency rates API with a 1,000 calls/day limit. "
        "The core problem: naive request forwarding exhausts the budget in 20 minutes. "
        "My solution: a proactive in-memory cache that fetches all 72 currency pairs in "
        "one batch call every 4 minutes (360 calls/day), then serves all client requests "
        "from a thread-safe Ref. The refresh loop is an fs2 stream merged with the HTTP "
        "server stream — they share a lifecycle. I used cats-effect 2 and http4s 0.22 "
        "(CE2 ecosystem) with tagless final throughout for testability. The test suite "
        "uses in-process fake clients — no real network, fully deterministic. For the "
        "demo, I added a React frontend with SSE-based live monitoring, and deployed "
        "everything in Docker Compose with a multi-stage build for a minimal runtime image.",
        styles, PURPLE)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # APPENDIX: Request Flow Diagrams
    # ════════════════════════════════════════════════════════════════════════
    story += chapter_heading("A", "Appendix: Complete Request Flow Diagrams", styles)

    story += section("A.1  GET /rates — Complete Flow", styles)
    story += code_block("""\
Browser                Nginx:3001            forex-proxy:9090         One-Frame:8080
   |                       |                        |                        |
   |  GET /rates?from=USD  |                        |                        |
   |  &to=JPY              |                        |                        |
   |──────────────────────►|                        |                        |
   |                       |  proxy_pass            |                        |
   |                       |──────────────────────►|                        |
   |                       |                        |                        |
   |                       |          RatesHttpRoutes.routes                 |
   |                       |          1. Extract from=USD, to=JPY           |
   |                       |          2. Validate (Currency.fromString)     |
   |                       |          3. from != to check                   |
   |                       |          4. Generate requestId (UUID[:8])      |
   |                       |          5. Record startNs = nanoTime()        |
   |                       |                        |                        |
   |                       |          program.get(GetRatesRequest(USD,JPY)) |
   |                       |          └─ cache.get(Rate.Pair(USD, JPY))     |
   |                       |             └─ ref.get.map(_.get(pair))        |
   |                       |                   ↑ O(1) memory lookup         |
   |                       |                   ↑ ZERO One-Frame calls       |
   |                       |                        |                        |
   |                       |          6. Format JSON response               |
   |                       |          7. Compute durationMs                 |
   |                       |          8. Publish ProxyRequest to EventBus   |
   |                       |          9. Return 200 + X-Request-ID header   |
   |                       |                        |                        |
   |                       |◄──────────────────────|                        |
   |◄──────────────────────|                        |                        |
   |  200 {"from":"USD",   |                        |                        |
   |  "to":"JPY",          |                        |                        |
   |  "price":149.50,...}  |                        |                        |""", styles)

    story += section("A.2  Cache Refresh Loop — Complete Flow", styles)
    story += code_block("""\
OneFrameCache                       One-Frame:8080           EventBus (Topic)
      |                                    |                        |
      | [App startup — BEFORE server]      |                        |
      |                                    |                        |
      | Stream.eval(doRefresh)             |                        |
      | ── fetchAll(72 pairs) ────────────►|                        |
      |                                    | GET /rates?pair=AUDUSD |
      |                                    | &pair=AUDCAD&...       |
      |                                    | (all 72 pairs, 1 call) |
      |◄───────────────────────────────────|                        |
      | JSON array [72 rate objects]       |                        |
      |                                    |                        |
      | ref.set(newMap)  ← atomic swap     |                        |
      | lastRefreshedAtRef.set(Some(now))  |                        |
      | eventBus.publish(CacheRefresh(...))────────────────────────►|
      |                                    |                        | → all SSE connections
      |                                    |                        | receive CacheRefresh event
      |                                    |                        |
      | [Wait 4 minutes — interruptible]   |                        |
      | Concurrent.race(                   |                        |
      |   Timer.sleep(4.min),              |                        |
      |   intervalRef.discrete.take(1)     |                        |
      | )                                  |                        |
      |                                    |                        |
      | [4 minutes later, or interval changed]                     |
      | ── fetchAll(72 pairs) ────────────►|                        |
      | ... repeat forever ...             |                        |""", styles)

    story += section("A.3  SSE Connection — Stream Topology", styles)
    story += code_block("""\
Browser EventSource              Nginx                  EventsHttpRoutes
      |                            |                            |
      | GET /events                |                            |
      |───────────────────────────►|  proxy_pass               |
      |                            |───────────────────────────►|
      |                            |                            |
      |                            |           Create two streams:
      |                            |                            |
      |                            |     busStream = eventBus.subscribe
      |                            |         (shared fan-out from Topic)
      |                            |                            |
      |                            |     heartbeatStream = Stream.repeatEval {
      |                            |         cache.getLastRefreshedAt >>
      |                            |         F.pure(Heartbeat(now, lastRefreshedAt))
      |                            |     }.metered(30.seconds)
      |                            |                            |
      |                            |     sseStream = busStream.merge(heartbeatStream)
      |                            |                            |
      |                            |◄───────────────────────────|
      |◄───────────────────────────|  200 text/event-stream     |
      |                            |                            |
      | [30 seconds later]         |                            |
      |◄── data: {"type":"Heartbeat","serverTimeMs":1709...,"lastRefreshedAt":"..."}\n\n
      |                            |                            |
      | [4 minutes later — cache refresh happens]              |
      |◄── data: {"type":"CacheRefresh","pairsCount":72,"durationMs":145.2,...}\n\n
      |                            |                            |
      | [client makes a rates request]                         |
      |◄── data: {"type":"ProxyRequest","from":"USD","to":"JPY","status":200,...}\n\n""", styles)

    story.append(PageBreak())

    # Final page
    story += chapter_heading("B", "Appendix: Quick Reference Card", styles)
    story.append(p("Key numbers, URLs, and facts to memorize:", styles))
    story.append(sp(2))

    ref_data = [
        ["Item", "Value", "Why It Matters"],
        ["One-Frame rate limit", "1,000 calls/day", "The fundamental constraint driving all design decisions"],
        ["Freshness SLA", "5 minutes", "Rates must never be more than 300 seconds stale"],
        ["Cache refresh interval", "4 minutes (240s)", "= 5 min SLA - 1 min buffer; 360 calls/day"],
        ["Total currency pairs", "72", "9 × 8 = 72 (self-pairs excluded)"],
        ["One-Frame auth header", "token: <value>", "NOT Authorization: Bearer"],
        ["forex-proxy port", "9090", "Application port"],
        ["Nginx frontend port", "3001", "External-facing SPA port"],
        ["One-Frame port", "18080 (external)", "8080 internal Docker; 18080 external"],
        ["SSE heartbeat interval", "30 seconds", "Keepalive + clock skew correction + lastRefreshedAt"],
        ["Nginx proxy_read_timeout", "600 seconds", "Critical for SSE — default 60s kills connections"],
        ["EventBus buffer", "128 events", "Per-subscriber drop buffer for slow connections"],
        ["cats-effect version", "CE2 (2.5.1)", "Required by http4s 0.22; CE3 is different"],
        ["fs2 version", "2.5.4", "CE2-compatible stream library"],
        ["Concurrent.race", "in refresh loop", "Enables immediate interval changes"],
        ["Ref[F, Map]", "the cache store", "Lock-free, atomic, thread-safe map"],
        ["Price type", "BigDecimal", "Never Double for financial values"],
        ["Timestamp type", "OffsetDateTime", "Timezone-aware; LocalDateTime is ambiguous"],
    ]
    t = Table(ref_data,
              colWidths=[4.5*cm, 4*cm, PAGE_W - 2*MARGIN - 8.5*cm],
              style=TableStyle([
                  ('BACKGROUND', (0,0), (-1,0), PURPLE),
                  ('TEXTCOLOR', (0,0), (-1,0), WHITE),
                  ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                  ('FONTSIZE', (0,0), (-1,-1), 8.5),
                  ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                  ('BACKGROUND', (0,1), (-1,-1), WHITE),
                  ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, GRAY_100]),
                  ('GRID', (0,0), (-1,-1), 0.3, GRAY_200),
                  ('VALIGN', (0,0), (-1,-1), 'TOP'),
                  ('TOPPADDING', (0,0), (-1,-1), 5),
                  ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                  ('LEFTPADDING', (0,0), (-1,-1), 5),
              ]))
    story.append(t)
    story.append(sp(4))

    story += callout("FINAL STUDY TIP",
        "The most important thing in the interview is not memorizing code — it is understanding "
        "WHY each decision was made. Every technical choice in this project flows from two "
        "constraints: (1) 1,000 calls/day limit, and (2) 5-minute freshness SLA. If you "
        "can explain the math, derive the refresh interval, explain why Ref is thread-safe, "
        "and describe what Concurrent.race does — you will demonstrate the depth of understanding "
        "that Paidy is looking for.",
        styles, GREEN)

    return story

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    output_path = "/home/juan/paidy/interview/forex-mtl-study-guide.pdf"
    doc = ForexDoc(output_path)
    styles = make_styles()

    # Build full story
    story = build_story(styles)

    doc.build(story)
    print(f"PDF generated: {output_path}")

if __name__ == "__main__":
    main()
