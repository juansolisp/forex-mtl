from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable

# ── Palette ──────────────────────────────────────────────────────────────────
C_BG        = colors.HexColor("#0F1117")   # page background (simulated via section boxes)
C_SURFACE   = colors.HexColor("#1A1D27")
C_ACCENT    = colors.HexColor("#7C3AED")   # purple
C_ACCENT2   = colors.HexColor("#06B6D4")   # cyan
C_GREEN     = colors.HexColor("#10B981")
C_RED       = colors.HexColor("#EF4444")
C_YELLOW    = colors.HexColor("#F59E0B")
C_TEXT      = colors.HexColor("#E2E8F0")
C_MUTED     = colors.HexColor("#94A3B8")
C_BORDER    = colors.HexColor("#2D3748")
C_CODE_BG   = colors.HexColor("#0D1117")
C_WHITE     = colors.white
PAGE_W, PAGE_H = A4


# ── Custom flowables ──────────────────────────────────────────────────────────
class ColorRect(Flowable):
    """Full-width filled rectangle — used as section header banners."""
    def __init__(self, width, height, fill, radius=4):
        Flowable.__init__(self)
        self.width  = width
        self.height = height
        self.fill   = fill
        self.radius = radius

    def draw(self):
        self.canv.setFillColor(self.fill)
        self.canv.roundRect(0, 0, self.width, self.height,
                            self.radius, stroke=0, fill=1)


class SideBar(Flowable):
    """Vertical coloured left-border bar."""
    def __init__(self, height, color=None, width=4):
        Flowable.__init__(self)
        self.height     = height
        self.bar_color  = color or C_ACCENT
        self.bar_width  = width
        self.width      = width

    def draw(self):
        self.canv.setFillColor(self.bar_color)
        self.canv.rect(0, 0, self.bar_width, self.height, stroke=0, fill=1)


# ── Style helpers ─────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()

    def s(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        # document title
        "title": s("DocTitle",
                   fontSize=28, leading=34, textColor=C_WHITE,
                   fontName="Helvetica-Bold", alignment=TA_CENTER,
                   spaceAfter=4),

        "subtitle": s("DocSubtitle",
                      fontSize=13, leading=18, textColor=C_ACCENT2,
                      fontName="Helvetica", alignment=TA_CENTER,
                      spaceAfter=2),

        "meta": s("Meta",
                  fontSize=9, leading=13, textColor=C_MUTED,
                  fontName="Helvetica", alignment=TA_CENTER),

        # section heading rendered inside a purple banner
        "section": s("Section",
                     fontSize=13, leading=16, textColor=C_WHITE,
                     fontName="Helvetica-Bold", alignment=TA_LEFT,
                     leftIndent=8, spaceAfter=0),

        # sub-section
        "h2": s("H2",
                fontSize=11, leading=15, textColor=C_ACCENT2,
                fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),

        "h3": s("H3",
                fontSize=10, leading=14, textColor=C_YELLOW,
                fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=3),

        # normal body
        "body": s("Body",
                  fontSize=9, leading=14, textColor=C_TEXT,
                  fontName="Helvetica", spaceAfter=4, alignment=TA_JUSTIFY),

        "body_l": s("BodyL",
                    fontSize=9, leading=14, textColor=C_TEXT,
                    fontName="Helvetica", spaceAfter=3),

        # inline code / monospace
        "code": s("Code",
                  fontSize=8, leading=12, textColor=C_ACCENT2,
                  fontName="Courier", spaceAfter=3,
                  backColor=C_CODE_BG, leftIndent=6, rightIndent=6,
                  borderPadding=(3, 3, 3, 3)),

        # bullet
        "bullet": s("Bul",
                    fontSize=9, leading=13, textColor=C_TEXT,
                    fontName="Helvetica", leftIndent=14, spaceAfter=2,
                    bulletIndent=4, bulletFontName="Helvetica",
                    bulletFontSize=9),

        # status badge helpers (we render these as small tables)
        "badge_done":    s("BD", fontSize=8, leading=10, textColor=C_WHITE,
                           fontName="Helvetica-Bold", alignment=TA_CENTER),
        "badge_stub":    s("BS", fontSize=8, leading=10, textColor=C_WHITE,
                           fontName="Helvetica-Bold", alignment=TA_CENTER),
        "badge_missing": s("BM", fontSize=8, leading=10, textColor=C_WHITE,
                           fontName="Helvetica-Bold", alignment=TA_CENTER),
        "table_cell":    s("TC", fontSize=8, leading=11, textColor=C_TEXT,
                           fontName="Helvetica"),
        "table_code":    s("TCC", fontSize=8, leading=11, textColor=C_ACCENT2,
                           fontName="Courier"),
        "table_head":    s("TH", fontSize=9, leading=12, textColor=C_WHITE,
                           fontName="Helvetica-Bold"),
        "muted":         s("Muted", fontSize=8, leading=11, textColor=C_MUTED,
                           fontName="Helvetica"),
    }


ST = _styles()
USABLE_W = PAGE_W - 28*mm   # left+right margins


def section_header(title, color=None):
    """Returns [ColorRect, overlaid Paragraph] pair acting as a section banner."""
    fill = color or C_ACCENT
    banner_h = 22
    # We use a 1-cell table so text sits on top of the background
    data = [[Paragraph(title, ST["section"])]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), fill),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0,0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return [Spacer(1, 8), t, Spacer(1, 6)]


def hr(color=None):
    return HRFlowable(width="100%", thickness=0.5,
                      color=color or C_BORDER, spaceAfter=6, spaceBefore=2)


def badge(text, color):
    data = [[Paragraph(text, ST["badge_done"])]]
    t = Table(data, colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), color),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROUNDEDCORNERS", [3]),
    ]))
    return t


def status_table(rows, col_widths=None):
    """Render a styled data table. rows[0] is header."""
    if col_widths is None:
        col_widths = [USABLE_W / len(rows[0])] * len(rows[0])

    def cell(val, is_header=False, is_code=False, status=None):
        if status == "done":
            return Paragraph(val, ST["badge_done"])
        if is_header:
            return Paragraph(str(val), ST["table_head"])
        if is_code:
            return Paragraph(str(val), ST["table_code"])
        return Paragraph(str(val), ST["table_cell"])

    header = [cell(c, is_header=True) for c in rows[0]]
    body   = []
    for row in rows[1:]:
        body.append([Paragraph(str(c), ST["table_cell"]) for c in row])

    t = Table([header] + body, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        # header
        ("BACKGROUND",   (0, 0), (-1,  0), C_ACCENT),
        ("TEXTCOLOR",    (0, 0), (-1,  0), C_WHITE),
        ("FONTNAME",     (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1,  0), 9),
        ("TOPPADDING",   (0, 0), (-1,  0), 6),
        ("BOTTOMPADDING",(0, 0), (-1,  0), 6),
        # body
        ("BACKGROUND",   (0, 1), (-1, -1), C_SURFACE),
        ("ROWBACKGROUNDS",(0,1), (-1, -1), [C_SURFACE, C_CODE_BG]),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("TOPPADDING",   (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        # grid
        ("GRID",         (0, 0), (-1, -1), 0.4, C_BORDER),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ])
    t.setStyle(style)
    return t


def code_block(lines):
    joined = "<br/>".join(lines)
    data = [[Paragraph(joined, ST["code"])]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), C_CODE_BG),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("BOX",          (0, 0), (-1, -1), 0.5, C_ACCENT),
    ]))
    return [t, Spacer(1, 5)]


def bullet(text, color=None):
    dot = f'<font color="#{(color or C_ACCENT2).hexval()[2:]}">▸</font>  '
    return Paragraph(dot + text, ST["bullet"])


def info_box(text, color=None):
    c = color or C_ACCENT
    data = [[Paragraph(text, ST["body_l"])]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_SURFACE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBEFORE",    (0, 0), (0, -1), 4, c),
        ("BOX",           (0, 0), (-1, -1), 0.4, C_BORDER),
    ]))
    return [t, Spacer(1, 5)]


# ── Page decorations ──────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    # Dark background
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # Top bar
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, PAGE_H - 6, PAGE_W, 6, stroke=0, fill=1)
    # Bottom bar
    canvas.setFillColor(C_SURFACE)
    canvas.rect(0, 0, PAGE_W, 14*mm, stroke=0, fill=1)
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(14*mm, 5*mm, "Paidy Forex-MTL — Codebase Analysis Report")
    canvas.drawRightString(PAGE_W - 14*mm, 5*mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Build document ────────────────────────────────────────────────────────────
def build():
    out = "/home/juan/paidy/interview/codebase_report.pdf"
    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=18*mm,  bottomMargin=20*mm,
        title="Paidy Forex-MTL Codebase Report",
        author="Analysis",
    )

    story = []
    sp = lambda n=6: Spacer(1, n)

    # ── Cover ─────────────────────────────────────────────────────────────────
    story += [
        sp(30),
        Paragraph("forex-mtl", ST["title"]),
        Paragraph("Codebase Analysis Report", ST["subtitle"]),
        sp(6),
        Paragraph("Paidy · Scala Product Engineer · Take-Home Assignment", ST["meta"]),
        Paragraph("Scala 2.13 · cats-effect · http4s · circe · tagless final", ST["meta"]),
        sp(20),
        HRFlowable(width="60%", thickness=1.5, color=C_ACCENT,
                   hAlign="CENTER", spaceAfter=20),
    ]

    # ── 1. Project Overview ───────────────────────────────────────────────────
    story += section_header("1 · Project Overview")
    story += [
        Paragraph(
            "forex-mtl is a scaffold for a Forex rates proxy service. "
            "It is built with <b>Scala 2.13</b>, the <b>cats / cats-effect</b> FP ecosystem, "
            "and follows the <b>tagless final</b> (MTL) architectural pattern throughout. "
            "The service exposes a single HTTP endpoint that returns a cached exchange rate "
            "for two currencies, acting as an abstraction layer over the third-party "
            "<b>One-Frame</b> provider.",
            ST["body"]),
        sp(4),
    ]

    overview_rows = [
        ["Property", "Value"],
        ["Language",       "Scala 2.13.12"],
        ["Build tool",     "sbt 1.x  +  sbt-assembly (fat JAR)"],
        ["Effect system",  "cats-effect 2.5.1  (IO, Concurrent, Timer, Sync)"],
        ["HTTP server",    "http4s-blaze-server 0.22.15"],
        ["HTTP client",    "not yet added — needed for One-Frame live interpreter"],
        ["JSON",           "circe 0.14.2  (generic-extras, snake_case)"],
        ["Config",         "pureconfig 0.17.4  (HOCON / application.conf)"],
        ["Streaming",      "fs2 2.5.4  (used for startup stream and background fibers)"],
        ["Logging",        "logback-classic 1.2.3  (SLF4J backend, stdout only)"],
        ["Testing libs",   "scalatest 3.2.7 · scalacheck 1.15.3 · cats-scalacheck 0.3.2"],
        ["Linting",        "strict scalacOptions (-Xfatal-warnings, -Xlint:*)"],
        ["Fat JAR",        "sbt-assembly 2.2.0  (added for Docker build)"],
        ["Code style",     "scalafmt via sbt-scalafmt-coursier 1.16"],
        ["Dev reload",     "sbt-revolver 0.9.1  (sbt ~reStart)"],
        ["Dep updates",    "sbt-updates 0.5.3  (sbt dependencyUpdates)"],
    ]
    story.append(status_table(overview_rows,
                               col_widths=[55*mm, USABLE_W - 55*mm]))
    story.append(sp(8))

    # ── 2. Architecture ───────────────────────────────────────────────────────
    story += section_header("2 · Architecture — Tagless Final / MTL Pattern", C_ACCENT)
    story += [
        Paragraph(
            "Every layer exposes a <b>trait Algebra[F[_]]</b> — an interface parameterised "
            "over an abstract effect type <b>F</b>. Concrete implementations are injected at "
            "the wiring point (<b>Module.scala</b>). This means the business logic never "
            "depends on IO directly; it can be tested with any effect (e.g. SyncIO, cats "
            "State) without changing production code.",
            ST["body"]),
        sp(4),
    ]
    story += code_block([
        "HTTP Request  GET /rates?from=USD&amp;to=EUR",
        "      │",
        "      ▼",
        "RatesHttpRoutes[F]      ← http4s DSL, query-param extraction, JSON encoding",
        "      │  calls",
        "      ▼",
        "RatesProgram[F]         ← EitherT error mapping, protocol translation",
        "      │  calls",
        "      ▼",
        "RatesService Algebra[F] ← thin interface: get(pair): F[Error Either Rate]",
        "      │  implemented by",
        "      ▼",
        "OneFrameDummy[F]        ← STUB (hardcoded 100.0)  ← YOU REPLACE THIS",
        "      ↕  will become",
        "OneFrameCache[F]        ← Ref[F, Map[Pair, Rate]] + background fs2 refresh",
        "      ↕  wrapping",
        "OneFrameLive[F]         ← real http4s BlazeClient → One-Frame API",
    ])
    story += [
        Paragraph("Effect constraints per layer:", ST["h3"]),
        sp(2),
    ]
    constraints_rows = [
        ["Layer", "File", "Constraint", "Why"],
        ["Service algebra",  "services/rates/algebra.scala",          "none",        "Pure interface — no constraint needed"],
        ["Dummy interpreter","interpreters/OneFrameDummy.scala",       "Applicative", "Only needs .pure[F] — minimal constraint"],
        ["Program",          "programs/rates/Program.scala",           "Functor",     "Only maps over F — leftMap via EitherT"],
        ["HTTP routes",      "http/rates/RatesHttpRoutes.scala",       "Sync",        "flatMap + fromEither need Sync"],
        ["Module wiring",    "Module.scala",                           "Concurrent + Timer", "Timeout middleware needs both"],
        ["Application",      "Main.scala",                             "ConcurrentEffect + Timer", "BlazeServer + stream compilation"],
    ]
    story.append(status_table(constraints_rows,
                               col_widths=[30*mm, 52*mm, 38*mm, USABLE_W-120*mm]))
    story.append(sp(8))

    # ── 3. Dependency Injection / Module Wiring ───────────────────────────────
    story += section_header("3 · Dependency Injection & Module Wiring", C_ACCENT)
    story += [
        Paragraph(
            "There is <b>no DI framework</b>. All wiring is done manually in "
            "<b>Module.scala</b> using plain constructor injection. This is idiomatic "
            "for the cats-effect / tagless-final style.",
            ST["body"]),
        sp(4),
    ]
    story += code_block([
        "// Module.scala (simplified)",
        "class Module[F[_]: Concurrent: Timer](config: ApplicationConfig) {",
        "  private val ratesService  = RatesServices.dummy[F]          // ← SWAP THIS",
        "  private val ratesProgram  = RatesProgram[F](ratesService)",
        "  private val ratesRoutes   = new RatesHttpRoutes[F](ratesProgram).routes",
        "  val httpApp: HttpApp[F]   = appMiddleware(routesMiddleware(ratesRoutes).orNotFound)",
        "}",
    ])
    story += [
        Paragraph(
            "Middleware applied:",
            ST["h3"]),
        bullet("<b>AutoSlash</b> — strips trailing slash so /rates/ == /rates"),
        bullet("<b>Timeout</b> — kills requests that exceed config.http.timeout (40 s)"),
        sp(6),
    ]

    # ── 4. Domain Model ───────────────────────────────────────────────────────
    story += section_header("4 · Domain Model", C_ACCENT)
    domain_rows = [
        ["Type", "Kind", "Key detail"],
        ["Currency",   "sealed trait + 9 case objects", "AUD CAD CHF EUR GBP NZD JPY SGD USD · Show instance · fromString (unsafe — throws on unknown)"],
        ["Price",      "case class extends AnyVal",      "Wraps BigDecimal — zero-overhead at runtime"],
        ["Timestamp",  "case class extends AnyVal",      "Wraps OffsetDateTime — .now factory"],
        ["Rate",       "case class",                     "pair: Rate.Pair · price: Price · timestamp: Timestamp"],
        ["Rate.Pair",  "nested case class",              "from: Currency · to: Currency"],
    ]
    story.append(status_table(domain_rows,
                               col_widths=[28*mm, 48*mm, USABLE_W-76*mm]))
    story += [
        sp(6),
        Paragraph(
            "<b>⚠ Known issue:</b> Currency.fromString throws a MatchError on unknown "
            "currency strings rather than returning an Option or Either. This is an "
            "<b>unsafe method</b> the assignment hints you should fix.",
            ST["body"]),
        sp(6),
    ]

    # ── 5. Configuration ──────────────────────────────────────────────────────
    story += section_header("5 · Configuration", C_ACCENT)
    story += [
        Paragraph(
            "Configuration is loaded via <b>pureconfig</b> from <b>application.conf</b> "
            "(HOCON format). The Config object wraps loading in an <b>fs2.Stream</b> so "
            "the startup sequence is composable with the server stream.",
            ST["body"]),
        sp(4),
    ]
    story += code_block([
        "// application.conf",
        'app {',
        '  http {',
        '    host    = "0.0.0.0"',
        '    port    = 9090       // changed from 8080 to avoid One-Frame collision',
        '    timeout = 40 seconds',
        '  }',
        '}',
        "",
        "// ApplicationConfig.scala",
        "case class ApplicationConfig(http: HttpConfig)",
        "case class HttpConfig(host: String, port: Int, timeout: FiniteDuration)",
        "",
        "// Config.scala — loads at startup",
        'Config.stream[F]("app")  // returns Stream[F, ApplicationConfig]',
    ])
    story += [
        Paragraph(
            "<b>What needs to be added:</b> A OneFrameConfig case class "
            "(url, token, refreshInterval) and corresponding HOCON block. "
            "The Docker Compose file passes ONE_FRAME_URL and ONE_FRAME_TOKEN as "
            "environment variables that should override application.conf values.",
            ST["body"]),
        sp(6),
    ]

    # ── 6. HTTP Layer ─────────────────────────────────────────────────────────
    story += section_header("6 · HTTP Layer", C_ACCENT)
    story += [
        Paragraph("Server: <b>http4s BlazeServer</b> on configured host:port.", ST["body"]),
        Paragraph("Single public endpoint:", ST["h3"]),
    ]
    story += code_block([
        "GET /rates?from={CURRENCY}&amp;to={CURRENCY}",
        "",
        "// Success 200",
        '{',
        '  "from"      : "USD",',
        '  "to"        : "JPY",',
        '  "price"     : 100.0,',
        '  "timestamp" : "2024-01-01T12:00:00Z"',
        '}',
        "",
        "// Error (currently unhandled — throws, returns 500)",
        '{ ... }   ← needs proper error response',
    ])

    http_rows = [
        ["File", "Responsibility", "Status"],
        ["RatesHttpRoutes.scala", "Route definition, query param extraction, JSON response", "✅ Done"],
        ["QueryParams.scala",     "Decodes ?from= and ?to= as Currency",                    "✅ Done — but Currency.fromString is unsafe"],
        ["Protocol.scala",        "GetApiRequest / GetApiResponse, circe encoders",         "✅ Done"],
        ["Converters.scala",      "Rate → GetApiResponse extension method",                  "✅ Done"],
        ["http/package.scala",    "Implicit circe ↔ http4s entity encoders/decoders",       "✅ Done"],
    ]
    story.append(status_table(http_rows,
                               col_widths=[50*mm, 80*mm, USABLE_W-130*mm]))
    story += [
        sp(6),
        Paragraph(
            "<b>⚠ Error handling gap:</b> RatesHttpRoutes calls "
            "<b>Sync[F].fromEither</b> which throws on Left — the error bubbles "
            "up as a 500 with no descriptive body. The assignment explicitly asks "
            "for descriptive error responses.",
            ST["body"]),
        sp(6),
    ]

    story.append(PageBreak())

    # ── 7. Service / Interpreter Layer ────────────────────────────────────────
    story += section_header("7 · Service / Interpreter Layer", C_ACCENT)
    story += [
        Paragraph(
            "The service layer defines a single-method algebra and currently ships "
            "one <b>dummy</b> interpreter. The live interpreter and cache are the "
            "core deliverables of this assignment.",
            ST["body"]),
        sp(4),
    ]
    story += code_block([
        "// Algebra — the contract",
        "trait Algebra[F[_]] {",
        "  def get(pair: Rate.Pair): F[Error Either Rate]",
        "}",
        "",
        "// OneFrameDummy — current stub",
        "class OneFrameDummy[F[_]: Applicative] extends Algebra[F] {",
        "  override def get(pair: Rate.Pair): F[Error Either Rate] =",
        "    Rate(pair, Price(BigDecimal(100)), Timestamp.now).asRight[Error].pure[F]",
        "  // always returns 100.0 — never calls One-Frame",
        "}",
    ])

    interp_rows = [
        ["Interpreter", "File", "Status", "Notes"],
        ["OneFrameDummy",  "interpreters/OneFrameDummy.scala", "🔶 Stub",    "Always returns 100.0 — no HTTP calls"],
        ["OneFrameLive",   "(to create)",                      "❌ Missing", "http4s BlazeClient → One-Frame /rates"],
        ["OneFrameCache",  "(to create)",                      "❌ Missing", "Ref[F, Map[Pair,Rate]] + fs2 background refresh"],
    ]
    story.append(status_table(interp_rows,
                               col_widths=[32*mm, 52*mm, 24*mm, USABLE_W-108*mm]))
    story.append(sp(8))

    # ── 8. Programs Layer ─────────────────────────────────────────────────────
    story += section_header("8 · Programs Layer", C_ACCENT)
    story += [
        Paragraph(
            "The programs layer provides a thin translation between the HTTP "
            "protocol model and the service algebra. It uses <b>EitherT</b> to "
            "map service-layer errors to program-layer errors.",
            ST["body"]),
        sp(4),
    ]
    story += code_block([
        "class Program[F[_]: Functor](ratesService: RatesService[F]) extends Algebra[F] {",
        "  override def get(request: GetRatesRequest): F[Error Either Rate] =",
        "    EitherT(ratesService.get(Rate.Pair(request.from, request.to)))",
        "      .leftMap(toProgramError(_))",
        "      .value",
        "}",
        "",
        "// Error mapping",
        "def toProgramError(e: RatesServiceError): Error = e match {",
        "  case OneFrameLookupFailed(msg) => RateLookupFailed(msg)",
        "}",
    ])
    story.append(sp(8))

    # ── 9. Persistence / Cache ────────────────────────────────────────────────
    story += section_header("9 · Persistence & Cache Strategy", C_RED)
    story += [
        Paragraph(
            "<b>There is no persistence layer.</b> The scaffold is entirely in-memory "
            "and stateless. There is <b>no cache</b> pre-configured — this is the "
            "primary gap to fill.",
            ST["body"]),
        sp(4),
    ]
    story += info_box(
        "<b>Required cache design:</b>  Use <b>cats-effect Ref[F, Map[Rate.Pair, Rate]]</b> "
        "as a thread-safe in-memory store. A background <b>fs2.Stream</b> fiber refreshes "
        "all 72 currency pairs every 4 minutes via a single batch request to One-Frame. "
        "The cache is warm before the server accepts connections (startup fetch). "
        "No Cassandra, Redis, or Postgres is needed — pure in-process state.",
        C_RED,
    )

    cache_math_rows = [
        ["Factor", "Value", "Notes"],
        ["One-Frame daily limit",     "1,000 req/day",  "Hard quota per token"],
        ["Max rate staleness",        "5 minutes",       "Assignment requirement"],
        ["Refresh interval (chosen)", "4 minutes",       "Stays 1 min inside SLA"],
        ["Pairs per request",         "72 (all at once)","9 currencies × 8 = 72 directed pairs"],
        ["Requests per day",          "360",             "24h × 60m ÷ 4m = 360 << 1000 ✅"],
        ["Requests served from cache","10,000+/day",     "All served from Ref — no One-Frame hit"],
    ]
    story.append(status_table(cache_math_rows,
                               col_widths=[50*mm, 38*mm, USABLE_W-88*mm]))
    story.append(sp(8))

    # ── 10. Logging ───────────────────────────────────────────────────────────
    story += section_header("10 · Logging", C_ACCENT)
    story += [
        Paragraph(
            "Logging uses <b>Logback</b> (SLF4J backend) configured via "
            "<b>logback.xml</b>. Current setup is minimal — stdout only, INFO level.",
            ST["body"]),
        sp(4),
    ]
    story += code_block([
        "&lt;configuration&gt;",
        "  &lt;appender name=STDOUT class=ConsoleAppender&gt;",
        "    &lt;pattern&gt;%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n&lt;/pattern&gt;",
        "  &lt;/appender&gt;",
        "  &lt;root level=INFO&gt;&lt;appender-ref ref=STDOUT/&gt;&lt;/root&gt;",
        "  &lt;logger name=http4s/&gt;  &lt;!-- http4s logs suppressed --&gt;",
        "&lt;/configuration&gt;",
    ])
    story += [
        Paragraph("<b>Gaps:</b>", ST["h3"]),
        bullet("No structured logging (no JSON log output)"),
        bullet("No log level differentiation per package"),
        bullet("http4s logger is declared but has no level — defaults to root INFO"),
        bullet("No log statements in any application code (Dummy, Program, Routes)"),
        bullet("Recommendation: add cats-effect IOApp logging or log4cats for structured FP-safe logging"),
        sp(6),
    ]

    # ── 11. Testing ───────────────────────────────────────────────────────────
    story += section_header("11 · Testing", C_RED)
    story += [
        Paragraph(
            "<b>There are zero tests.</b> The test dependencies are declared in "
            "build.sbt but no test source files exist under src/test/.",
            ST["body"]),
        sp(4),
    ]

    test_dep_rows = [
        ["Library", "Version", "Purpose"],
        ["scalatest",      "3.2.7",  "Primary test framework — FlatSpec, AnyFunSuite, etc."],
        ["scalacheck",     "1.15.3", "Property-based testing — generators for currencies, pairs"],
        ["cats-scalacheck", "0.3.2", "Cats type class law testing + Arbitrary instances for F[_]"],
    ]
    story.append(status_table(test_dep_rows,
                               col_widths=[40*mm, 22*mm, USABLE_W-62*mm]))
    story += [
        sp(6),
        Paragraph("Tests to write:", ST["h3"]),
        bullet("Unit: cache returns correct Rate for a valid pair"),
        bullet("Unit: cache returns error when no data available (startup edge case)"),
        bullet("Unit: all 72 pairs generated from 9 currencies (no duplicates, no self-pairs)"),
        bullet("Unit: toProgramError maps all service errors correctly"),
        bullet("Unit: Currency.fromString returns expected values (fix the unsafe version first)"),
        bullet("Property: forAll(validPair) → cache.get returns Right(_)"),
        bullet("Integration (optional): starts Docker one-frame, calls live endpoint"),
        sp(6),
    ]

    # ── 12. Plugins Explained ─────────────────────────────────────────────────
    story += section_header("12 · SBT Plugins Explained", C_ACCENT)
    plugin_rows = [
        ["Plugin", "Version", "What it does"],
        ["sbt-scalafmt-coursier", "1.16",  "Runs scalafmt code formatter — sbt scalafmtAll / scalafmtCheck"],
        ["sbt-updates",          "0.5.3",  "sbt dependencyUpdates — shows which deps have newer versions"],
        ["sbt-revolver",         "0.9.1",  "sbt ~reStart — hot-reload dev server on file change"],
        ["sbt-assembly",         "2.2.0",  "sbt assembly — builds fat JAR for Docker deployment"],
        ["kind-projector",       "0.13.2", "Compiler plugin: enables F[_] type lambda syntax λ[α => F[α]]"],
    ]
    story.append(status_table(plugin_rows,
                               col_widths=[48*mm, 20*mm, USABLE_W-68*mm]))
    story.append(sp(8))

    # ── 13. Dependencies Explained ────────────────────────────────────────────
    story += section_header("13 · Dependencies Explained", C_ACCENT)

    story += [Paragraph("Core FP Ecosystem", ST["h2"])]
    story += [
        bullet("<b>cats 2.6.1</b> — type class hierarchy: Functor, Applicative, Monad, Show, etc."),
        bullet("<b>cats-effect 2.5.1</b> — IO monad, Concurrent, Timer, Sync, Resource — the runtime effect system"),
        bullet("<b>fs2 2.5.4</b> — functional streaming; used for the startup config stream and will be used for the background cache refresh fiber"),
        sp(4),
    ]
    story += [Paragraph("HTTP", ST["h2"])]
    story += [
        bullet("<b>http4s-dsl 0.22.15</b> — Scala DSL for defining routes (case GET -> Root :? ...)"),
        bullet("<b>http4s-blaze-server 0.22.15</b> — NIO HTTP/1.1 server (BlazeServerBuilder)"),
        bullet("<b>http4s-circe 0.22.15</b> — bridges http4s entity encoding with circe JSON"),
        bullet("<b>http4s BlazeClient</b> — <i>not yet added</i>, needed for OneFrameLive"),
        sp(4),
    ]
    story += [Paragraph("JSON", ST["h2"])]
    story += [
        bullet("<b>circe-core 0.14.2</b> — Encoder / Decoder type classes"),
        bullet("<b>circe-generic 0.14.2</b> — auto-derivation of codecs via macros"),
        bullet("<b>circe-generic-extras 0.14.2</b> — extras: snake_case config, UnwrappedEncoder/Decoder for value classes, EnumerationEncoder/Decoder"),
        bullet("<b>circe-parser 0.14.2</b> — parse(String): Either[ParsingFailure, Json]"),
        sp(4),
    ]
    story += [Paragraph("Configuration & Infrastructure", ST["h2"])]
    story += [
        bullet("<b>pureconfig 0.17.4</b> — automatic HOCON → case class loading; pureconfig.generic.auto._ drives derivation"),
        bullet("<b>logback-classic 1.2.3</b> — SLF4J backend; configured via logback.xml"),
        sp(6),
    ]

    # ── 14. What is Done vs Missing ───────────────────────────────────────────
    story += section_header("14 · What Is Done vs. What Is Missing", C_ACCENT)

    done_missing_rows = [
        ["Component", "Status", "Notes"],
        ["Domain models (Currency, Price, Rate, Timestamp)", "✅ Done",    "Complete — note Currency.fromString is unsafe"],
        ["Service Algebra (interface)",                      "✅ Done",    "Clean tagless final trait"],
        ["OneFrameDummy interpreter",                        "🔶 Stub",    "Returns 100.0, no HTTP — replace with live+cache"],
        ["Programs layer (Program.scala)",                   "✅ Done",    "EitherT error mapping is correct"],
        ["HTTP routes (RatesHttpRoutes)",                    "✅ Done",    "Route works but error handling is incomplete"],
        ["HTTP QueryParams",                                 "✅ Done",    "Currency.fromString unsafe — fix in implementation"],
        ["HTTP Protocol (encoders)",                         "✅ Done",    "snake_case JSON, value class support"],
        ["Converters",                                       "✅ Done",    "Rate → GetApiResponse"],
        ["http/package.scala implicits",                     "✅ Done",    "Entity encoder/decoder bridge"],
        ["Module wiring",                                    "✅ Done",    "Switch dummy → live+cache when ready"],
        ["Config (ApplicationConfig)",                       "🔶 Partial", "Missing: OneFrameConfig (url, token, refreshInterval)"],
        ["application.conf",                                 "🔶 Partial", "Missing: one-frame config block"],
        ["OneFrameLive interpreter",                         "❌ Missing", "http4s client + JSON decoder for One-Frame response"],
        ["OneFrameCache interpreter",                        "❌ Missing", "Ref[F, Map[Pair,Rate]] + background fs2 refresh"],
        ["HTTP client dependency",                           "❌ Missing", "http4s-blaze-client not in build.sbt"],
        ["Error responses (HTTP 4xx)",                       "❌ Missing", "fromEither throws → 500; needs proper error handling"],
        ["Currency.fromString safety",                       "❌ Missing", "Throws MatchError — should return Either/Option"],
        ["Tests",                                            "❌ Missing", "No test files exist; deps declared but unused"],
        ["Dockerfile",                                       "✅ Done",    "Multi-stage sbt assembly build"],
        ["docker-compose.yml",                               "✅ Done",    "one-frame + forex-proxy services"],
        ["README",                                           "❌ Missing", "Run instructions, design rationale, constraint math"],
    ]
    story.append(status_table(done_missing_rows,
                               col_widths=[80*mm, 22*mm, USABLE_W-102*mm]))
    story.append(sp(8))

    # ── 15. Compiler Flags ────────────────────────────────────────────────────
    story += section_header("15 · Strict Compiler Flags", C_ACCENT)
    story += [
        Paragraph(
            "build.sbt enables an extensive set of strict compiler options. "
            "Every warning is a compile error (<b>-Xfatal-warnings</b>). "
            "This means your new code must be warning-free or the build fails.",
            ST["body"]),
        sp(4),
    ]
    flags_rows = [
        ["Flag", "Effect"],
        ["-Xfatal-warnings",         "All warnings are compile errors"],
        ["-Xlint:*",                 "Full lint suite (unused imports, type shadows, etc.)"],
        ["-Ywarn-unused:*",          "Warns on unused imports, params, locals, privates, implicits"],
        ["-Ywarn-dead-code",         "Warns on unreachable code branches"],
        ["-Ywarn-value-discard",     "Warns when a non-Unit expression result is ignored"],
        ["-Ywarn-macros:after",      "Suppresses false positives from generic derivation macros"],
        ["-language:higherKinds",    "Required for F[_] style higher-kinded types"],
        ["-language:implicitConversions", "Required for implicit class ops (GetApiResponseOps)"],
        ["-Xcheckinit",              "Throws on access to uninitialised fields"],
    ]
    story.append(status_table(flags_rows,
                               col_widths=[65*mm, USABLE_W-65*mm]))
    story.append(sp(8))

    # ── 16. Implementation Checklist ──────────────────────────────────────────
    story += section_header("16 · Implementation Checklist", C_GREEN)
    checklist = [
        ("Add http4s-blaze-client to build.sbt",                                       C_RED),
        ("Add OneFrameConfig to ApplicationConfig + application.conf",                  C_RED),
        ("Implement OneFrameLive — http4s client, circe decoder, error mapping",        C_RED),
        ("Implement OneFrameCache — Ref + fs2.Stream scheduler + startup warmup",       C_RED),
        ("Add live() + cached() factory methods to Interpreters.scala",                 C_RED),
        ("Wire live+cache into Module.scala (replace dummy)",                           C_RED),
        ("Fix Currency.fromString — return Either[String, Currency] or Option",         C_YELLOW),
        ("Fix HTTP error handling — return 4xx with descriptive JSON body",             C_YELLOW),
        ("Write unit tests for cache, pairs generation, error mapping",                 C_YELLOW),
        ("Write property tests with scalacheck for Currency / Pair Arbitraries",        C_YELLOW),
        ("Write README with run instructions and design rationale",                     C_GREEN),
        ("Verify sbt assembly produces working fat JAR",                                C_GREEN),
        ("Test docker compose up --build end-to-end",                                  C_GREEN),
    ]
    for text, color in checklist:
        story.append(bullet(text, color))
    story.append(sp(10))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF generated: {out}")


if __name__ == "__main__":
    build()
