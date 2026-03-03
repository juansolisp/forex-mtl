from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG      = colors.HexColor("#0F1117")
C_SURFACE = colors.HexColor("#1A1D27")
C_ACCENT  = colors.HexColor("#7C3AED")
C_CYAN    = colors.HexColor("#06B6D4")
C_GREEN   = colors.HexColor("#10B981")
C_RED     = colors.HexColor("#EF4444")
C_YELLOW  = colors.HexColor("#F59E0B")
C_ORANGE  = colors.HexColor("#F97316")
C_TEXT    = colors.HexColor("#E2E8F0")
C_MUTED   = colors.HexColor("#94A3B8")
C_BORDER  = colors.HexColor("#2D3748")
C_CODE_BG = colors.HexColor("#0D1117")
C_WHITE   = colors.white
PAGE_W, PAGE_H = A4
USABLE_W = PAGE_W - 28 * mm

# Category accent colours
CAT_COLORS = {
    "fp":     C_ACCENT,
    "http":   C_CYAN,
    "json":   C_GREEN,
    "config": C_YELLOW,
    "log":    C_ORANGE,
    "test":   C_RED,
    "plugin": colors.HexColor("#8B5CF6"),
    "sbt":    colors.HexColor("#EC4899"),
}


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    def s(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)
    return {
        "title":    s("T",  fontSize=26, leading=32, textColor=C_WHITE,
                       fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4),
        "subtitle": s("ST", fontSize=12, leading=16, textColor=C_CYAN,
                       fontName="Helvetica", alignment=TA_CENTER, spaceAfter=2),
        "meta":     s("M",  fontSize=9,  leading=12, textColor=C_MUTED,
                       fontName="Helvetica", alignment=TA_CENTER),
        "cat_text": s("CT", fontSize=11, leading=15, textColor=C_WHITE,
                       fontName="Helvetica-Bold", leftIndent=10),
        "dep_name": s("DN", fontSize=12, leading=16, textColor=C_WHITE,
                       fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=2),
        "dep_meta": s("DM", fontSize=8,  leading=11, textColor=C_MUTED,
                       fontName="Helvetica", spaceAfter=4),
        "h3":       s("H3", fontSize=10, leading=14, textColor=C_YELLOW,
                       fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=3),
        "body":     s("B",  fontSize=9,  leading=14, textColor=C_TEXT,
                       fontName="Helvetica", spaceAfter=4, alignment=TA_JUSTIFY),
        "body_l":   s("BL", fontSize=9,  leading=14, textColor=C_TEXT,
                       fontName="Helvetica", spaceAfter=3),
        "code":     s("C",  fontSize=7.5, leading=11, textColor=C_CYAN,
                       fontName="Courier", spaceAfter=2),
        "bullet":   s("BU", fontSize=9,  leading=13, textColor=C_TEXT,
                       fontName="Helvetica", leftIndent=14, spaceAfter=2),
        "th":       s("TH", fontSize=9,  leading=12, textColor=C_WHITE,
                       fontName="Helvetica-Bold"),
        "td":       s("TD", fontSize=8,  leading=11, textColor=C_TEXT,
                       fontName="Helvetica"),
        "usage":    s("US", fontSize=8,  leading=11, textColor=C_MUTED,
                       fontName="Helvetica-Oblique", spaceAfter=6),
        "label":    s("LB", fontSize=8,  leading=10, textColor=C_WHITE,
                       fontName="Helvetica-Bold", alignment=TA_CENTER),
    }

ST = make_styles()


# ── Helpers ───────────────────────────────────────────────────────────────────
def sp(n=6):
    return Spacer(1, n)

def hr(color=None):
    return HRFlowable(width="100%", thickness=0.4,
                      color=color or C_BORDER, spaceAfter=4, spaceBefore=2)

def category_header(title, cat="fp"):
    color = CAT_COLORS.get(cat, C_ACCENT)
    data = [[Paragraph(title, ST["cat_text"])]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), color),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
    ]))
    return [sp(12), t, sp(8)]

def dep_header(name, version, org, cat="fp"):
    color = CAT_COLORS.get(cat, C_ACCENT)
    # Badge + name row
    badge_data = [[
        Paragraph(name, ST["dep_name"]),
        Paragraph(f"v{version}", ST["label"]),
    ]]
    badge_t = Table(badge_data, colWidths=[USABLE_W - 22*mm, 22*mm])
    badge_t.setStyle(TableStyle([
        ("BACKGROUND",   (1,0), (1,0), color),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
        ("LEFTPADDING",  (0,0), (0,0), 0),
        ("LEFTPADDING",  (1,0), (1,0), 4),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ]))
    org_p = Paragraph(f"<font color='#{C_MUTED.hexval()[2:]}'>{org}</font>", ST["dep_meta"])
    return [badge_t, org_p, hr(color)]

def section_label(text):
    return Paragraph(f"<b>{text}</b>", ST["h3"])

def body(text):
    return Paragraph(text, ST["body"])

def bullet(text, color=None):
    c = color or C_CYAN
    hex_c = c.hexval()[2:]
    dot = f'<font color="#{hex_c}">▸</font>  '
    return Paragraph(dot + text, ST["bullet"])

def usage(text):
    return Paragraph(f"Used in forex-mtl: {text}", ST["usage"])

def code_block(lines):
    text = "<br/>".join(
        l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for l in lines
    )
    data = [[Paragraph(text, ST["code"])]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), C_CODE_BG),
        ("TOPPADDING",   (0,0), (-1,-1), 9),
        ("BOTTOMPADDING",(0,0), (-1,-1), 9),
        ("LEFTPADDING",  (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("BOX",          (0,0), (-1,-1), 0.6, C_ACCENT),
    ]))
    return [t, sp(6)]

def data_table(rows, col_widths=None):
    if col_widths is None:
        col_widths = [USABLE_W / len(rows[0])] * len(rows[0])
    header = [Paragraph(str(c), ST["th"]) for c in rows[0]]
    body_rows = [[Paragraph(str(c), ST["td"]) for c in row] for row in rows[1:]]
    t = Table([header] + body_rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  C_ACCENT),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_SURFACE, C_CODE_BG]),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 7),
        ("RIGHTPADDING",  (0,0), (-1,-1), 7),
        ("GRID",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return [t, sp(6)]

def sep():
    return [sp(4), hr(), sp(4)]


# ── Page template ─────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, PAGE_H - 5, PAGE_W, 5, stroke=0, fill=1)
    canvas.setFillColor(C_SURFACE)
    canvas.rect(0, 0, PAGE_W, 13 * mm, stroke=0, fill=1)
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(14 * mm, 4.5 * mm, "forex-mtl · Dependencies & Plugins Guide")
    canvas.drawRightString(PAGE_W - 14 * mm, 4.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Entry builder ─────────────────────────────────────────────────────────────
def entry(name, version, org, cat, what, problem, concept_lines, example_lines, where):
    """Build a complete dependency entry block."""
    blocks = []
    blocks += dep_header(name, version, org, cat)
    blocks += [section_label("What it is"), body(what), sp(2)]
    blocks += [section_label("Problem it solves"), body(problem), sp(2)]
    blocks += [section_label("Core concept")]
    blocks += code_block(concept_lines)
    blocks += [section_label("Practical example")]
    blocks += code_block(example_lines)
    blocks += [usage(where), sp(4)]
    return blocks


# ── Document ──────────────────────────────────────────────────────────────────
def build():
    out = "/home/juan/paidy/interview/deps_report.pdf"
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=16*mm,  bottomMargin=18*mm,
        title="forex-mtl Dependencies & Plugins Guide",
    )
    s = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    s += [sp(28),
          Paragraph("Dependencies & Plugins", ST["title"]),
          Paragraph("Complete Beginner Guide", ST["subtitle"]),
          sp(6),
          Paragraph("forex-mtl · Scala 2.13 · cats-effect · http4s · circe · 21 entries", ST["meta"]),
          sp(18),
          HRFlowable(width="55%", thickness=1.5, color=C_ACCENT, hAlign="CENTER", spaceAfter=18)]

    # Quick reference table
    s += data_table([
        ["Concern", "Libraries / Plugins"],
        ["FP core types",     "cats-core"],
        ["Async / effects",   "cats-effect  ·  fs2"],
        ["HTTP server",       "http4s-dsl  ·  http4s-blaze-server  ·  http4s-circe"],
        ["HTTP client",       "http4s-blaze-client"],
        ["JSON",              "circe-core  ·  circe-generic  ·  circe-generic-extras  ·  circe-parser"],
        ["Configuration",     "pureconfig"],
        ["Logging",           "logback-classic"],
        ["Unit tests",        "scalatest"],
        ["Property tests",    "scalacheck  ·  cats-scalacheck"],
        ["FP syntax sugar",   "kind-projector (compiler plugin)"],
        ["Code format",       "sbt-scalafmt-coursier"],
        ["Dep updates",       "sbt-updates"],
        ["Dev hot-reload",    "sbt-revolver"],
        ["Fat JAR / Docker",  "sbt-assembly"],
    ], col_widths=[44*mm, USABLE_W - 44*mm])

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: FP Core
    # ═══════════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += category_header("FP Core Ecosystem", "fp")

    # 1. cats-core
    s += entry(
        "cats-core", "2.6.1", "org.typelevel", "fp",
        what="A library of functional programming abstractions — type classes like Functor, "
             "Applicative, Monad, and utilities like Show, Eq, Order.",
        problem="Without it you write the same patterns (map, flatMap, traverse) differently for "
                "every type. Cats gives you a shared vocabulary that works the same way across "
                "Option, Either, List, IO, and your own types.",
        concept_lines=[
            "// Type class — attach behaviour to any type without owning it",
            "Functor      -> has .map",
            "Applicative  -> has .pure + combine independent values",
            "Monad        -> has .flatMap (sequential chaining)",
            "Show         -> has .show  (safe .toString replacement)",
        ],
        example_lines=[
            "import cats.Show",
            "import cats.syntax.show._",
            "",
            "implicit val showCurrency: Show[Currency] = Show.show(_.code)",
            'Currency("USD").show    // "USD"  (not "Currency(USD)")',
            "",
            "// Applicative — combine two Options independently",
            "import cats.syntax.apply._",
            'val pair = (Some("USD"), Some("JPY")).mapN((f,t) => s"$f->$t")',
            '// Some("USD->JPY")',
        ],
        where="Currency.scala (Show instance) · OneFrameDummy.scala (Applicative) · "
              "Program.scala (Functor) · everywhere via cats.syntax.either._"
    )

    s += sep()

    # 2. cats-effect
    s += entry(
        "cats-effect", "2.5.1", "org.typelevel", "fp",
        what="The runtime for functional effects in Scala. Provides IO, Ref, Resource, "
             "and type classes Sync, Concurrent, Timer.",
        problem="Normal Scala code runs side effects immediately and unpredictably. "
                "cats-effect lets you describe effects as values, compose them safely, "
                "and run them only at the edge of your program.",
        concept_lines=[
            'IO[A]           — "a program that will produce A (or fail)"',
            "                  does NOTHING until .unsafeRunSync()",
            "Ref[F, A]       — thread-safe mutable variable inside F",
            "Resource[F, A]  — acquire + guaranteed release (even on error)",
            "Sync[F]         — F can run synchronous side effects",
            "Concurrent[F]   — F can run fibers (lightweight threads)",
            "Timer[F]        — F can sleep / get current time",
        ],
        example_lines=[
            "import cats.effect.{IO, Ref, Resource}",
            "",
            "// IO — describe, don't run",
            "val fetchRate: IO[String] = IO(http.get(\"/rates?pair=USDJPY\"))",
            "// nothing has happened yet",
            "",
            "// Ref — thread-safe counter",
            "for {",
            "  ref <- Ref.of[IO, Int](0)",
            "  _   <- ref.update(_ + 1)",
            "  n   <- ref.get",
            "  _   <- IO(println(n))  // 1",
            "} yield ()",
            "",
            "// Resource — guaranteed cleanup",
            "Resource.make(IO(openConnection))(c => IO(c.close()))",
        ],
        where="Main.scala (IOApp) · Module.scala (Concurrent, Timer) · "
              "Config.scala (Sync.delay) · Cache layer (Ref[F, Map[Pair, Rate]])"
    )

    s += sep()

    # 3. fs2
    s += entry(
        "fs2", "2.5.4", "co.fs2", "fp",
        what="Functional Streams for Scala — processes sequences of data incrementally "
             "with resource management built in.",
        problem="Processing large sequences one element at a time without loading everything "
                "into memory. Also: running tasks on a schedule (cache refresh).",
        concept_lines=[
            "Stream[F, A]  — potentially infinite sequence of A values",
            "               produced inside effect F",
            "",
            "Think: lazy List that can do IO between elements and run forever",
        ],
        example_lines=[
            "import fs2.Stream",
            "import scala.concurrent.duration._",
            "",
            "// Finite stream",
            "Stream.emits(List(1,2,3)).map(_ * 2).compile.toList",
            "// List(2, 4, 6)",
            "",
            "// IO stream",
            "Stream(1,2,3).evalMap(n => IO(println(s\"item $n\")))",
            "             .compile.drain",
            "",
            "// Tick every 4 minutes — used for cache refresh",
            "Stream.fixedDelay[IO](4.minutes)",
            "      .evalMap(_ => IO(println(\"refreshing...\")))",
            "      .compile.drain   // IO[Unit] — runs until cancelled",
        ],
        where="Main.scala (entire app is Stream[F, Unit]) · Config.scala (Stream.eval) · "
              "OneFrameCache (Stream.fixedDelay for background refresh)"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: HTTP
    # ═══════════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += category_header("HTTP  (http4s 0.22.15)", "http")

    # 4. http4s-dsl
    s += entry(
        "http4s-dsl", "0.22.15", "org.http4s", "http",
        what="A Scala DSL for defining HTTP routes using pattern matching syntax.",
        problem="Without it you'd write verbose code to extract method, path, and query params "
                "from a raw Request object.",
        concept_lines=[
            "// Pattern match on the incoming request",
            "case GET -> Root / 'users' / id :? PageParam(page) =>",
            "//   ^      ^              ^         ^",
            "//  method  path         path var  query param",
        ],
        example_lines=[
            "class MyRoutes[F[_]: Sync] extends Http4sDsl[F] {",
            "  object NameParam extends QueryParamDecoderMatcher[String](\"name\")",
            "",
            "  val routes = HttpRoutes.of[F] {",
            "    case GET -> Root / \"hello\"       => Ok(\"Hello!\")",
            "    case GET -> Root / \"hello\" / name => Ok(s\"Hello $name!\")",
            "    case GET -> Root / \"greet\" :? NameParam(n) => Ok(s\"Hi $n!\")",
            "  }",
            "}",
        ],
        where="RatesHttpRoutes.scala (main route pattern) · QueryParams.scala (FromQueryParam, ToQueryParam)"
    )

    s += sep()

    # 5. http4s-blaze-server
    s += entry(
        "http4s-blaze-server", "0.22.15", "org.http4s", "http",
        what="An NIO HTTP/1.1 server — turns your HttpApp[F] into a real running server.",
        problem="You have route definitions but nothing binds them to a port and listens.",
        concept_lines=[
            "HttpRoutes[F]  — partial function, only handles matched routes",
            "HttpApp[F]     — total function, always returns a response (404 on miss)",
            "BlazeServer    — binds HttpApp to host:port, accepts connections",
        ],
        example_lines=[
            "BlazeServerBuilder[IO](global)",
            "  .bindHttp(port = 9090, host = \"0.0.0.0\")",
            "  .withHttpApp(routes.orNotFound)",
            "  .serve                     // Stream[IO, ExitCode]",
            "  .compile.drain",
        ],
        where="Main.scala (BlazeServerBuilder) · Module.scala (middleware applied before server)"
    )

    s += sep()

    # 6. http4s-blaze-client
    s += entry(
        "http4s-blaze-client", "0.22.15", "org.http4s", "http",
        what="HTTP client — makes outbound HTTP requests inside an effect F, "
             "with connection pooling and automatic cleanup.",
        problem="You need to call One-Frame's API. The client manages connection pooling "
                "so you don't leak connections.",
        concept_lines=[
            "Client[F]  — a resource that makes HTTP requests",
            "           — connection pool managed automatically",
            "           — always use via Resource to ensure cleanup",
        ],
        example_lines=[
            "BlazeClientBuilder[IO](global).resource.use { client =>",
            "  val req = Request[IO](Method.GET,",
            "              uri\"http://localhost:8080/rates?pair=USDJPY\")",
            "            .withHeaders(Header(\"token\", \"abc123\"))",
            "",
            "  client.expect[String](req).flatMap(IO(println(_)))",
            "}",
        ],
        where="NOT YET ADDED — needed for OneFrameLive to call One-Frame /rates"
    )

    s += sep()

    # 7. http4s-circe
    s += entry(
        "http4s-circe", "0.22.15", "org.http4s", "http",
        what="Bridge between http4s and circe — makes circe Encoder/Decoder automatically "
             "work as http4s EntityEncoder/EntityDecoder.",
        problem="http4s uses EntityDecoder/Encoder for bodies; circe uses Decoder/Encoder "
                "for JSON. Without this bridge you'd have to wire them manually for every type.",
        concept_lines=[
            "circe Encoder[A]  +  http4s-circe  =  EntityEncoder[F, A]",
            "circe Decoder[A]  +  http4s-circe  =  EntityDecoder[F, A]",
        ],
        example_lines=[
            "implicit val encoder = jsonEncoderOf[F, RateResponse]",
            "",
            "val routes = HttpRoutes.of[F] {",
            "  case GET -> Root / \"rate\" =>",
            "    Ok(RateResponse(\"USD\", \"JPY\", 110.5))",
            "    // body: {\"from\":\"USD\",\"to\":\"JPY\",\"price\":110.5}",
            "}",
        ],
        where="http/package.scala — implicit jsonEncoder/jsonDecoder that power Ok(rate.asGetApiResponse)"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: JSON (circe)
    # ═══════════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += category_header("JSON  (circe 0.14.2)", "json")

    # 8. circe-core
    s += entry(
        "circe-core", "0.14.2", "io.circe", "json",
        what="Core of the circe JSON library — defines Json, Encoder[A], Decoder[A], "
             "HCursor and fundamental JSON operations.",
        problem="Standard java.json or raw string manipulation is unsafe and verbose. "
                "Circe gives you type-safe, compile-time-checked JSON encoding and decoding.",
        concept_lines=[
            "Encoder[A]  — turns A into Json",
            "Decoder[A]  — turns Json into Either[DecodingFailure, A]",
        ],
        example_lines=[
            "import io.circe._, io.circe.syntax._",
            "",
            "case class Price(value: BigDecimal)",
            "implicit val enc: Encoder[Price] =",
            "  Encoder.instance(p => Json.fromBigDecimal(p.value))",
            "implicit val dec: Decoder[Price] =",
            "  Decoder.instance(_.as[BigDecimal].map(Price(_)))",
            "",
            "val json = Price(BigDecimal(\"110.5\")).asJson  // 110.5",
            "val back = json.as[Price]  // Right(Price(110.5))",
        ],
        where="http/rates/Protocol.scala (Encoder[Currency], Encoder[Rate], Encoder[GetApiResponse])"
    )

    s += sep()

    # 9. circe-generic
    s += entry(
        "circe-generic", "0.14.2", "io.circe", "json",
        what="Automatic derivation of Encoder and Decoder for case classes and sealed "
             "traits using Scala macros — no boilerplate.",
        problem="Writing Encoder/Decoder by hand for every case class is tedious. "
                "circe-generic does it automatically based on the shape of your type.",
        concept_lines=[
            "import io.circe.generic.auto._",
            "// That single import gives every case class in scope",
            "// an Encoder and Decoder — compiler generates them",
        ],
        example_lines=[
            "import io.circe.generic.auto._",
            "import io.circe.parser._, io.circe.syntax._",
            "",
            "case class User(name: String, age: Int)",
            'val json = User("Juan", 30).asJson.noSpaces',
            '// {"name":"Juan","age":30}',
            "",
            'val decoded = decode[User](json)',
            '// Right(User("Juan",30))',
        ],
        where="http/rates/Protocol.scala (deriveConfiguredEncoder builds on this)"
    )

    s += sep()

    # 10. circe-generic-extras
    s += entry(
        "circe-generic-extras", "0.14.2", "io.circe", "json",
        what="Extension of circe-generic with snake_case config, value class (AnyVal) "
             "unwrapping, and sealed trait enumeration encoding.",
        problem="By default circe uses camelCase. JSON APIs use snake_case. "
                "Also, without extras, Price(110.5) encodes as {\"value\":110.5} instead of 110.5.",
        concept_lines=[
            "// Configure once — applies everywhere via deriveConfiguredEncoder",
            "implicit val config = Configuration.default.withSnakeCaseMemberNames",
            "",
            "// UnwrappedEncoder — encodes AnyVal as its inner value",
            "// case class Price(value: BigDecimal) extends AnyVal",
            "// encodes as 110.5 not {\"value\": 110.5}",
        ],
        example_lines=[
            "implicit val config = Configuration.default.withSnakeCaseMemberNames",
            "case class ApiResponse(fromCurrency: String, lastUpdated: String)",
            "implicit val enc = deriveConfiguredEncoder[ApiResponse]",
            "",
            'ApiResponse("USD","2024-01-01").asJson.spaces2',
            "// {",
            '//   "from_currency": "USD",',
            '//   "last_updated": "2024-01-01"',
            "// }",
        ],
        where="http/rates/Protocol.scala (snake_case + deriveConfiguredEncoder) · "
              "http/package.scala (UnwrappedEncoder/Decoder for Price, Timestamp)"
    )

    s += sep()

    # 11. circe-parser
    s += entry(
        "circe-parser", "0.14.2", "io.circe", "json",
        what="Parses raw JSON strings into circe's Json type.",
        problem="You receive a JSON string from One-Frame's HTTP response "
                "and need to decode it into Scala types.",
        concept_lines=[
            "parse(string)     -> Either[ParsingFailure, Json]  (parse only)",
            "decode[A](string) -> Either[Error, A]              (parse + decode)",
        ],
        example_lines=[
            "import io.circe.parser._",
            "import io.circe.generic.auto._",
            "",
            "case class Rate(from: String, to: String, price: Double)",
            'val raw = """{"from":"USD","to":"JPY","price":110.5}"""',
            "",
            "// One step",
            "decode[Rate](raw)  // Right(Rate(\"USD\",\"JPY\",110.5))",
            "",
            "// Array — One-Frame returns a list",
            'decode[List[Rate]]("""[{...},{...}]""")',
        ],
        where="OneFrameLive (to build) — parsing JSON array from One-Frame /rates"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: Config & Logging
    # ═══════════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += category_header("Configuration & Logging", "config")

    # 12. pureconfig
    s += entry(
        "pureconfig", "0.17.4", "com.github.pureconfig", "config",
        what="Loads HOCON config files (application.conf) directly into Scala case classes — "
             "no manual parsing, no string lookups.",
        problem="Reading config with plain ConfigFactory gives you stringly-typed access: "
                "config.getString(\"app.http.host\"). PureConfig is type-safe — "
                "missing or wrong-type fields fail at startup with a clear error.",
        concept_lines=[
            "import pureconfig._, pureconfig.generic.auto._",
            "",
            "case class HttpConfig(host: String, port: Int)",
            "case class AppConfig(http: HttpConfig)",
            "",
            "// Loads application.conf, maps app.http -> HttpConfig",
            "val cfg = ConfigSource.default.loadOrThrow[AppConfig]",
            "cfg.http.port   // Int — type safe",
        ],
        example_lines=[
            "# application.conf",
            "app {",
            '  http { host = "0.0.0.0"  port = 9090  timeout = 40 seconds }',
            '  one-frame { base-url = "http://localhost:8080" }',
            "}",
            "",
            "// kebab-case in HOCON -> camelCase in Scala (automatic)",
            "case class OneFrameConfig(baseUrl: String)",
            "",
            "val cfg = ConfigSource.default.at(\"app\").loadOrThrow[AppConfig]",
            'println(cfg.oneFrame.baseUrl)  // "http://localhost:8080"',
        ],
        where="Config.scala (ConfigSource.default.at(\"app\").loadOrThrow) · "
              "ApplicationConfig.scala (the case classes)"
    )

    s += sep()

    # 13. logback-classic
    s += entry(
        "logback-classic", "1.2.3", "ch.qos.logback", "log",
        what="The most widely used JVM logging backend. Implements the SLF4J API.",
        problem="println for logging is unstructured and cannot be turned off. "
                "Logback gives you levelled logging, configurable formats, and the "
                "ability to silence noisy libraries.",
        concept_lines=[
            "SLF4J     — the logging API (what you write in code)",
            "Logback   — the implementation (what writes the output)",
            "logback.xml — configures levels, format, appenders",
            "",
            "Levels: TRACE < DEBUG < INFO < WARN < ERROR",
        ],
        example_lines=[
            "// logback.xml",
            "<configuration>",
            "  <appender name=STDOUT class=ConsoleAppender>",
            "    <pattern>%d{HH:mm:ss} %-5level %logger - %msg%n</pattern>",
            "  </appender>",
            "  <root level=INFO><appender-ref ref=STDOUT/></root>",
            "  <logger name=org.http4s level=WARN/>  <!-- silence noise -->",
            "</configuration>",
            "",
            "// In Scala",
            "private val log = LoggerFactory.getLogger(getClass)",
            "log.info(\"Cache refreshed\")",
            "log.warn(s\"Refresh failed: $err\")",
        ],
        where="src/main/resources/logback.xml"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: Test Dependencies
    # ═══════════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += category_header("Test Dependencies", "test")

    # 14. scalatest
    s += entry(
        "scalatest", "3.2.7", "org.scalatest", "test",
        what="The most popular test framework for Scala — test runner, rich assertions, "
             "multiple test style flavours.",
        problem="You need a structured way to write, organise, and run tests with "
                "human-readable names and clear failure messages.",
        concept_lines=[
            "AnyFunSuite  ->  test(\"name\") { ... }       <- used in forex-mtl",
            "AnyFlatSpec  ->  \"X\" should \"do Y\" in { ... }",
            "AnyWordSpec  ->  \"X\" when \"condition\" should \"do Y\" in { ... }",
        ],
        example_lines=[
            "import org.scalatest.funsuite.AnyFunSuite",
            "import org.scalatest.matchers.should.Matchers",
            "",
            "class CurrencySpec extends AnyFunSuite with Matchers {",
            "",
            "  test(\"fromString returns Right for valid currency\") {",
            "    Currency.fromString(\"JPY\") shouldBe Right(Currency.JPY)",
            "  }",
            "",
            "  test(\"allPairs has exactly 72 elements\") {",
            "    Currency.allPairs should have size 72",
            "  }",
            "}",
            "",
            "// sbt test",
            "// sbt \"testOnly *CurrencySpec\"",
        ],
        where="NOT YET — test files need to be created under src/test/scala/forex/"
    )

    s += sep()

    # 15. scalacheck
    s += entry(
        "scalacheck", "1.15.3", "org.scalacheck", "test",
        what="Property-based testing — write rules that must hold for ANY valid input; "
             "ScalaCheck generates hundreds of random inputs to find failures.",
        problem="Hand-picked test cases only test what you think of. Property tests find "
                "edge cases you never imagined.",
        concept_lines=[
            "Gen[A]          — generator that produces random A values",
            "Arbitrary[A]    — default generator for type A",
            "forAll(gen)(fn) — run fn against many generated values (100 by default)",
        ],
        example_lines=[
            "import org.scalacheck.{Gen, Properties}",
            "import org.scalacheck.Prop.forAll",
            "",
            "val genCurrency: Gen[Currency] = Gen.oneOf(Currency.values)",
            "",
            "val genPair: Gen[Rate.Pair] = for {",
            "  from <- genCurrency",
            "  to   <- genCurrency.suchThat(_ != from)",
            "} yield Rate.Pair(from, to)",
            "",
            "// ScalaCheck runs this 100 times with random inputs",
            "property(\"fromString(show(c)) == Right(c)\") =",
            "  forAll(genCurrency)(c => Currency.fromString(c.show) == Right(c))",
        ],
        where="NOT YET — will test Currency generators and Rate.Pair properties"
    )

    s += sep()

    # 16. cats-scalacheck
    s += entry(
        "cats-scalacheck", "0.3.2", "io.chrisdavenport", "test",
        what="Provides Arbitrary instances for cats types — so ScalaCheck can generate "
             "IO[Int], Either[String, Rate], and other cats types randomly.",
        problem="ScalaCheck generates Int, String, List[A] out of the box. "
                "It does not know how to generate IO[Int] or Either[Error, Rate]. "
                "This library provides those instances.",
        concept_lines=[
            "import io.chrisdavenport.cats.scalacheck._",
            "",
            "// Now these just work:",
            "forAll { (x: IO[Int]) => ... }",
            "forAll { (x: Either[String, Rate]) => ... }",
        ],
        example_lines=[
            "import io.chrisdavenport.cats.scalacheck._",
            "import cats.effect.IO",
            "",
            "class FunctorLawSpec extends AnyFunSuite with Checkers {",
            "  // Arbitrary[IO[Int]] provided by cats-scalacheck",
            "  test(\"IO satisfies functor identity\") {",
            "    check { (fa: IO[Int]) =>",
            "      fa.map(identity).unsafeRunSync() == fa.unsafeRunSync()",
            "    }",
            "  }",
            "}",
        ],
        where="NOT YET — law tests and arbitrary effect values in future tests"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: Compiler Plugins
    # ═══════════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += category_header("Compiler Plugin", "plugin")

    # 17. kind-projector
    s += entry(
        "kind-projector", "0.13.2", "org.typelevel", "plugin",
        what="A Scala compiler plugin that adds clean syntax for type lambdas — "
             "partial application of multi-parameter type constructors.",
        problem="Scala's built-in type lambda syntax is extremely verbose. "
                "Tagless final code constantly needs to partially apply types, "
                "and without this plugin the syntax is unreadable.",
        concept_lines=[
            "// Without kind-projector — verbose",
            "foo[({ type L[A] = Either[String, A] })#L]",
            "",
            "// With kind-projector — clean",
            "foo[Either[String, *]]",
            "",
            "// Added as a compiler plugin, not a runtime dependency",
            "compilerPlugin(Libraries.kindProjector)",
        ],
        example_lines=[
            "def process[F[_]](fa: F[Int]): F[String] = ???",
            "",
            "// Without kind-projector:",
            "process[({ type L[A] = Either[String, A] })#L](Right(42))",
            "",
            "// With kind-projector:",
            "process[Either[String, *]](Right(42))",
            "",
            "// Functor for Map — without / with",
            "implicitly[Functor[({ type L[A] = Map[String, A] })#L]]",
            "implicitly[Functor[Map[String, *]]]",
        ],
        where="Implicitly throughout — enables F[_] patterns in all tagless final code. "
              "EitherT in Program.scala relies on it for the error type lambda."
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION: SBT Plugins
    # ═══════════════════════════════════════════════════════════════════════════
    s += [PageBreak()]
    s += category_header("SBT Plugins  (project/plugins.sbt)", "sbt")

    s += [body("SBT plugins extend the build tool itself — not your application. "
               "They add new sbt tasks and settings."), sp(4)]

    # 18. sbt-scalafmt-coursier
    s += entry(
        "sbt-scalafmt-coursier", "1.16", "com.lucidchart", "sbt",
        what="Integrates the Scalafmt code formatter into sbt. Enforces consistent "
             "code style across all developers.",
        problem="Without a formatter every developer formats code differently, "
                "cluttering code reviews with style noise.",
        concept_lines=[
            "sbt scalafmt       # format all source files in place",
            "sbt scalafmtCheck  # check without modifying (CI gate)",
            "sbt scalafmtAll    # format sources + tests + build files",
            "",
            ".scalafmt.conf defines the rules (max column, alignment, etc.)",
        ],
        example_lines=[
            "# .scalafmt.conf",
            "version = \"3.7.14\"",
            "maxColumn = 100",
            "align.preset = more",
            "",
            "// Before",
            "def get(pair:Rate.Pair):F[Error Either Rate]={ratesService.get(pair)}",
            "",
            "// After sbt scalafmt",
            "def get(pair: Rate.Pair): F[Error Either Rate] =",
            "  ratesService.get(pair)",
        ],
        where=".scalafmt.conf in project root · CI runs sbt scalafmtCheck to block unformatted PRs"
    )

    s += sep()

    # 19. sbt-updates
    s += entry(
        "sbt-updates", "0.5.3", "com.timushev.sbt", "sbt",
        what="Adds sbt dependencyUpdates — checks all dependencies for newer "
             "versions available on Maven.",
        problem="Dependencies go stale. Security vulnerabilities are fixed in new releases. "
                "Without tooling you'd have to check each library manually.",
        concept_lines=[
            "sbt dependencyUpdates   # reports available updates",
            "",
            "It only REPORTS — never modifies build.sbt",
        ],
        example_lines=[
            "$ sbt dependencyUpdates",
            "",
            "[info] Found 3 dependency updates for forex",
            "[info]   co.fs2:fs2-core_2.13       : 2.5.4  -> 3.9.2",
            "[info]   org.http4s:http4s-dsl_2.13  : 0.22.15 -> 0.23.25",
            "[info]   io.circe:circe-core_2.13    : 0.14.2  -> 0.14.6",
        ],
        where="Run manually before starting implementation to check for security patches"
    )

    s += sep()

    # 20. sbt-revolver
    s += entry(
        "sbt-revolver", "0.9.1", "io.spray", "sbt",
        what="Adds reStart / reStop tasks that run your app in a background JVM process "
             "with automatic restart on code changes.",
        problem="Normal dev loop: edit -> Ctrl+C -> sbt run -> wait -> test -> repeat. "
                "With sbt-revolver: sbt ~reStart stays running and auto-restarts on save.",
        concept_lines=[
            "sbt reStart    # start app in background",
            "sbt reStop     # stop it",
            "sbt ~reStart   # watch files, auto-restart on change  <-- the useful one",
        ],
        example_lines=[
            "# Terminal 1 — keep running",
            "$ sbt ~reStart",
            "",
            "# Edit src/main/scala/forex/Module.scala and save...",
            "# sbt auto-recompiles and restarts the server",
            "",
            "# Terminal 2 — test immediately",
            "$ curl localhost:9090/rates?from=USD&to=JPY",
        ],
        where="Local development hot-reload"
    )

    s += sep()

    # 21. sbt-assembly
    s += entry(
        "sbt-assembly", "2.2.0", "com.eed3si9n", "sbt",
        what="Merges your compiled code and ALL dependencies into a single self-contained "
             "fat JAR file.",
        problem="A normal JAR only contains your code. Running it needs all dependency JARs "
                "on the classpath. A fat JAR is self-contained — ship one file, run it anywhere.",
        concept_lines=[
            "sbt assembly  ->  target/scala-2.13/forex-assembly.jar",
            "                  (your code + cats + http4s + circe + ...)",
            "",
            "java -jar forex-assembly.jar   # no classpath needed",
            "",
            "Merge strategy handles file conflicts between dependency JARs:",
            "  META-INF/*     -> discard (duplicates)",
            "  reference.conf -> concat  (MUST merge, not discard!)",
        ],
        example_lines=[
            "// build.sbt",
            "assembly / assemblyJarName := \"forex-assembly.jar\"",
            "assembly / assemblyMergeStrategy := {",
            "  case PathList(\"META-INF\", _*) => MergeStrategy.discard",
            "  case \"reference.conf\"          => MergeStrategy.concat",
            "  case x => (assembly / assemblyMergeStrategy).value(x)",
            "}",
            "",
            "# Dockerfile",
            "FROM sbt:1.9.8-eclipse-temurin-17 AS builder",
            "COPY . .  &&  RUN sbt assembly",
            "FROM eclipse-temurin:17-jre-alpine",
            "COPY --from=builder .../forex-assembly.jar app.jar",
            "ENTRYPOINT [\"java\", \"-jar\", \"app.jar\"]",
        ],
        where="build.sbt (merge strategy) · project/plugins.sbt · Dockerfile (RUN sbt assembly)"
    )

    doc.build(s, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF written: {out}")


if __name__ == "__main__":
    build()
