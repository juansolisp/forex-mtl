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
C_TEXT    = colors.HexColor("#E2E8F0")
C_MUTED   = colors.HexColor("#94A3B8")
C_BORDER  = colors.HexColor("#2D3748")
C_CODE_BG = colors.HexColor("#0D1117")
C_WHITE   = colors.white
PAGE_W, PAGE_H = A4
USABLE_W = PAGE_W - 28 * mm


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
        "h1_text":  s("H1", fontSize=12, leading=16, textColor=C_WHITE,
                       fontName="Helvetica-Bold", leftIndent=10),
        "h2":       s("H2", fontSize=11, leading=15, textColor=C_CYAN,
                       fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),
        "h3":       s("H3", fontSize=10, leading=14, textColor=C_YELLOW,
                       fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=3),
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
        "td_code":  s("TC", fontSize=8,  leading=11, textColor=C_CYAN,
                       fontName="Courier"),
        "muted":    s("MU", fontSize=8,  leading=11, textColor=C_MUTED,
                       fontName="Helvetica"),
        "note":     s("N",  fontSize=8.5, leading=13, textColor=C_YELLOW,
                       fontName="Helvetica", spaceAfter=4),
    }

ST = make_styles()


# ── Helpers ───────────────────────────────────────────────────────────────────
def sp(n=6):
    return Spacer(1, n)

def hr(color=None):
    return HRFlowable(width="100%", thickness=0.5,
                      color=color or C_BORDER, spaceAfter=5, spaceBefore=2)

def section(title, color=None):
    fill = color or C_ACCENT
    data = [[Paragraph(title, ST["h1_text"])]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), fill),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
    ]))
    return [sp(10), t, sp(6)]

def subsection(title, color=None):
    c = color or C_CYAN
    return [Paragraph(title, ST["h2"]), hr(c)]

def h3(title):
    return Paragraph(title, ST["h3"])

def body(text):
    return Paragraph(text, ST["body"])

def bullet(text, color=None):
    c = color or C_CYAN
    hex_c = c.hexval()[2:]
    dot = f'<font color="#{hex_c}">▸</font>  '
    return Paragraph(dot + text, ST["bullet"])

def note(text):
    data = [[Paragraph(f"⚠  {text}", ST["note"])]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), C_SURFACE),
        ("LINEBEFORE",   (0,0), (0,-1),  4, C_YELLOW),
        ("BOX",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",   (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0), (-1,-1), 7),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
    ]))
    return [t, sp(5)]

def info(text, color=None):
    c = color or C_CYAN
    data = [[Paragraph(text, ST["body_l"])]]
    t = Table(data, colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), C_SURFACE),
        ("LINEBEFORE",   (0,0), (0,-1),  4, c),
        ("BOX",          (0,0), (-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",   (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0), (-1,-1), 7),
        ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
    ]))
    return [t, sp(5)]

def code_block(lines, lang=""):
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
    return [t, sp(5)]

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
    canvas.drawString(14 * mm, 4.5 * mm, "forex-mtl · Full Implementation Spec")
    canvas.drawRightString(PAGE_W - 14 * mm, 4.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Document ──────────────────────────────────────────────────────────────────
def build():
    out = "/home/juan/paidy/interview/spec_report.pdf"
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=16*mm,  bottomMargin=18*mm,
        title="forex-mtl Implementation Spec",
    )
    s = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    s += [sp(28),
          Paragraph("forex-mtl", ST["title"]),
          Paragraph("Full Implementation Spec", ST["subtitle"]),
          sp(6),
          Paragraph("Caching · Testing · CI/CD · Integration Tests · Frontend", ST["meta"]),
          sp(18),
          HRFlowable(width="55%", thickness=1.5, color=C_ACCENT, hAlign="CENTER", spaceAfter=18)]

    # ── 1. Solution Overview ──────────────────────────────────────────────────
    s += section("1 · Solution Overview")
    s += info("The forex-proxy service sits between internal consumers and the One-Frame provider. "
              "It caches all 72 currency pairs in memory, refreshes on a schedule, and serves "
              "requests at unlimited throughput while staying inside One-Frame's 1,000 req/day limit.")
    s += data_table([
        ["Factor", "Value", "Notes"],
        ["One-Frame limit",        "1,000 req/day",    "Hard quota per token"],
        ["Required throughput",    "10,000+ req/day",  "Assignment requirement"],
        ["Max staleness",          "5 minutes",        "Assignment requirement"],
        ["Refresh interval",       "4 minutes",        "Configurable via application.conf"],
        ["Pairs per refresh call", "72",               "All 9×8 pairs in one request"],
        ["Refresh calls/day",      "360",              "360 << 1,000 ✅"],
        ["Requests from cache",    "Unlimited",        "O(1) Ref lookup, no network"],
    ], col_widths=[42*mm, 32*mm, USABLE_W - 74*mm])

    s += subsection("Architecture")
    s += code_block([
        "Demo Frontend  (React · Vite · port 5173)",
        "      |  GET /rates?from=USD&to=JPY",
        "      v",
        "forex-proxy  (Scala · cats-effect · http4s · port 9090)",
        "  RatesHttpRoutes -> RatesProgram -> RatesService",
        "                                        |",
        "                          OneFrameCache (Ref[F, Map[Pair,Rate]])",
        "                                        |  every 4 min",
        "                          OneFrameLive  (http4s BlazeClient)",
        "                                        |",
        "paidyinc/one-frame  (Docker · port 8080 · 1000 req/day)",
    ])

    # ── 2. Backend Implementation ─────────────────────────────────────────────
    s += [PageBreak()]
    s += section("2 · Backend Implementation")

    s += subsection("2.1  Missing http4s Artifact")
    s += [body("http4s-blaze-client is part of http4s (already a dependency) but shipped as a "
               "separate artifact. The server artifact is present; the client is not.")]
    s += code_block([
        "// project/Dependencies.scala — add alongside existing http4s lines",
        'lazy val http4sClient = http4s("http4s-blaze-client")',
        "",
        "// build.sbt — add to libraryDependencies",
        "Libraries.http4sClient,",
    ])

    s += subsection("2.2  OneFrameLive — HTTP Client Interpreter")
    s += [body("New file: <b>services/rates/interpreters/OneFrameLive.scala</b>"),
          body("Fetches all 72 pairs in a single One-Frame request. Returns "
               "<b>F[Error Either Map[Rate.Pair, Rate]]</b> to the cache layer.")]
    s += code_block([
        "class OneFrameLive[F[_]: Sync](client: Client[F], config: OneFrameConfig) {",
        "  def fetchAll: F[Error Either Map[Rate.Pair, Rate]] = {",
        "    val uri     = buildUri(config.baseUrl, allPairs)  // 72 pair= params",
        "    val request = Request[F](uri = uri)",
        '                   .putHeaders(Header("token", config.token))',
        "    client.expect[List[OneFrameResponse]](request)",
        "          .map(rs => Right(toRateMap(rs)))",
        "          .handleErrorWith(e =>",
        "            F.pure(Left(Error.OneFrameLookupFailed(e.getMessage))))",
        "  }",
        "}",
    ])

    s += subsection("2.3  OneFrameCache — Cache + Background Refresh")
    s += [body("New file: <b>services/rates/interpreters/OneFrameCache.scala</b>"),
          body("Implements Algebra[F] — the interpreter wired into Module. "
               "Holds a Ref of all rates. Background fs2 fiber refreshes on schedule. "
               "Smart constructor fetches eagerly on startup.")]
    s += code_block([
        "class OneFrameCache[F[_]: Concurrent: Timer](",
        "    ref: Ref[F, Map[Rate.Pair, Rate]],",
        "    live: OneFrameLive[F], config: OneFrameConfig",
        ") extends Algebra[F] {",
        "",
        "  // O(1) map lookup on every request",
        "  override def get(pair: Rate.Pair): F[Error Either Rate] =",
        "    ref.get.map(_.get(pair).toRight(",
        '      Error.OneFrameLookupFailed(s"No rate for $pair")))',
        "",
        "  // Background loop — runs forever",
        "  val backgroundRefresh: Stream[F, Unit] =",
        "    Stream.fixedDelay[F](config.refreshInterval) >>",
        "      Stream.eval(live.fetchAll.flatMap {",
        "        case Right(rates) => ref.set(rates)",
        "        case Left(err)    => Logger[F].warn(s\"Refresh failed: $err\")",
        "      })",
        "}",
        "",
        "object OneFrameCache {",
        "  def resource[F[_]: Concurrent: Timer](...): Resource[F, Algebra[F]] =",
        "    for {",
        "      initial <- Resource.eval(live.fetchAll.rethrow)  // fail fast",
        "      ref     <- Resource.eval(Ref.of[F, Map[Rate.Pair, Rate]](initial))",
        "      cache    = new OneFrameCache[F](ref, live, config)",
        "      _       <- cache.backgroundRefresh.compile.drain.background",
        "    } yield cache",
        "}",
    ])

    s += subsection("2.4  Module + Main Wiring")
    s += code_block([
        "// Main.scala",
        "for {",
        '  config <- Config.stream("app")',
        "  client <- Stream.resource(BlazeClientBuilder[F](ec).resource)",
        "  live    = Interpreters.live[F](client, config.oneFrame)",
        "  cache  <- Stream.resource(Interpreters.cached[F](live, config.oneFrame))",
        "  module  = new Module[F](config, cache)",
        "  _      <- BlazeServerBuilder[F](ec)",
        "              .bindHttp(config.http.port, config.http.host)",
        "              .withHttpApp(module.httpApp)",
        "              .serve",
        "} yield ()",
    ])

    # ── 3. Caching Strategy ───────────────────────────────────────────────────
    s += [PageBreak()]
    s += section("3 · Caching Strategy")
    s += data_table([
        ["Approach", "Pros", "Cons", "Verdict"],
        ["Proactive batch (chosen)", "Bounded quota; O(1) reads; warm startup", "Fetches unused pairs", "✅ Best fit"],
        ["Reactive per-request",     "Only fetches needed pairs",               "Quota burst risk; cold misses", "❌"],
        ["Redis external cache",     "Persistent across restarts",              "Overkill; extra infra", "❌"],
        ["Streaming /streaming/rates","Push-based; no polling",                 "Reconnect complexity; harder to test", "❌"],
    ], col_widths=[40*mm, 46*mm, 52*mm, 20*mm])

    s += subsection("Cache State Machine")
    s += code_block([
        "App start",
        "    |",
        "    v",
        "OneFrameLive.fetchAll()  <-- single batch, all 72 pairs",
        "    |",
        "    +-- Left(error) --> FAIL FAST (don't start with empty cache)",
        "    |",
        "    +-- Right(rates) --> Ref.of(rates)",
        "                             |",
        "                             +--> Server accepts requests",
        "                             |",
        "                             +--> Background fiber every 4 min:",
        "                                    success --> ref.set(newRates)",
        "                                    failure --> log warn, keep stale",
    ])
    s += [h3("Staleness Guarantee")]
    s += [bullet("Refresh every <b>4 minutes</b> → worst-case staleness 4 min (within 5 min SLA)"),
          bullet("If one refresh fails → next retry in 4 min → worst case 8 min"),
          bullet("For strict guarantee: use <b>2-minute</b> interval (720 calls/day) + retry on failure"),
          bullet("Interval is configurable in application.conf — no code change needed to tune")]

    s += subsection("All-Pairs Generation")
    s += code_block([
        "// Add to Currency companion object",
        "val values: List[Currency] =",
        "  List(AUD, CAD, CHF, EUR, GBP, NZD, JPY, SGD, USD)",
        "",
        "val allPairs: List[Rate.Pair] =",
        "  for {",
        "    from <- values",
        "    to   <- values",
        "    if from != to",
        "  } yield Rate.Pair(from, to)",
        "// 9 * 8 = 72 directed pairs",
    ])

    # ── 4. Error Handling ─────────────────────────────────────────────────────
    s += section("4 · Error Handling")
    s += note("RatesHttpRoutes currently calls Sync[F].fromEither which THROWS on Left, "
              "returning a generic 500. The assignment explicitly asks for descriptive errors.")
    s += subsection("Fix: Proper HTTP Error Responses")
    s += code_block([
        "// RatesHttpRoutes — replace flatMap(Sync[F].fromEither) with:",
        "rates.get(request).flatMap {",
        "  case Right(rate) => Ok(rate.asGetApiResponse)",
        "  case Left(err)   => err match {",
        '    case Error.RateLookupFailed(msg) => NotFound(ErrorResponse(msg))',
        '    case _  => InternalServerError(ErrorResponse("Unexpected error"))',
        "  }",
        "}",
        "",
        "// Add to http/rates/Protocol.scala",
        "final case class ErrorResponse(error: String)",
        "implicit val errorEncoder = deriveConfiguredEncoder[ErrorResponse]",
    ])
    s += subsection("Fix: Currency.fromString is Unsafe")
    s += code_block([
        "// Current — throws MatchError on unknown input",
        "def fromString(s: String): Currency = s.toUpperCase match { ... }",
        "",
        "// Fixed — returns Either",
        "def fromString(s: String): Either[String, Currency] = s.toUpperCase match {",
        '  case "AUD" => Right(AUD)',
        "  // ...",
        '  case other => Left(s"Unsupported currency: $other")',
        "}",
    ])
    s += subsection("Error Layer Map")
    s += data_table([
        ["Layer", "Error Type", "HTTP Response"],
        ["OneFrameLive",  "Error.OneFrameLookupFailed(msg)", "—"],
        ["toProgramError","Error.RateLookupFailed(msg)",     "—"],
        ["HTTP routes",   "Left(RateLookupFailed)",          '404 {"error": "..."}'],
        ["Unknown currency","QueryParamDecoder failure",     '400 {"error": "..."}'],
    ], col_widths=[38*mm, 72*mm, USABLE_W - 110*mm])

    # ── 5. Configuration ──────────────────────────────────────────────────────
    s += section("5 · Configuration")
    s += code_block([
        "// ApplicationConfig.scala",
        "case class ApplicationConfig(http: HttpConfig, oneFrame: OneFrameConfig)",
        "case class OneFrameConfig(",
        "    baseUrl: String,",
        "    token: String,",
        "    refreshInterval: FiniteDuration",
        ")",
        "",
        "// application.conf",
        "app {",
        "  http { host = 0.0.0.0  port = 9090  timeout = 40 seconds }",
        "  one-frame {",
        '    base-url         = "http://localhost:8080"',
        "    base-url         = ${?ONE_FRAME_URL}     # Docker override",
        '    token            = "10dc303535874aeccc86a8251e6992f5"',
        "    token            = ${?ONE_FRAME_TOKEN}",
        "    refresh-interval = 4 minutes",
        "  }",
        "}",
    ])
    s += [body("The <b>${?VAR}</b> syntax is HOCON optional env var override — "
               "if the env var is absent the default is used, so local dev works without Docker.")]

    # ── 6. Testing Strategy ───────────────────────────────────────────────────
    s += [PageBreak()]
    s += section("6 · Testing Strategy")
    s += info("No mocking frameworks. Use tagless final — swap real implementations "
              "with in-memory fakes by changing what F is.", C_GREEN)

    s += data_table([
        ["Test type", "File", "What it tests"],
        ["Unit",       "domain/CurrencySpec",             "fromString, allPairs size, no self-pairs, no duplicates"],
        ["Unit",       "services/OneFrameCacheSpec",       "get returns rate, get returns error on miss, refresh updates Ref"],
        ["Unit",       "services/OneFrameLiveSpec",        "JSON decoding, request URI construction, error mapping"],
        ["Unit",       "programs/ProgramSpec",             "toProgramError maps all service errors correctly"],
        ["Unit",       "http/RatesHttpRoutesSpec",         "200 on valid pair, 400 on bad currency, 503 on service error"],
        ["Property",   "domain/CurrencyPropertySpec",      "fromString(show(c)) == c for all c; allPairs contains any valid pair"],
        ["Integration","it/IntegrationSpec (tagged)",      "Real Docker One-Frame; staleness; 10k requests; 400 on unknown"],
    ], col_widths=[22*mm, 52*mm, USABLE_W - 74*mm])

    s += subsection("Key Test Patterns")
    s += code_block([
        "// In-memory HTTP route test — no real server needed",
        "val fakeProgram: RatesProgram[IO] = new rates.Algebra[IO] {",
        "  def get(req: GetRatesRequest): IO[Error Either Rate] =",
        "    IO.pure(Right(goodRate))",
        "}",
        "val routes = new RatesHttpRoutes[IO](fakeProgram).routes.orNotFound",
        "val resp = routes.run(Request[IO](GET, uri\"/rates?from=USD&to=JPY\"))",
        "                  .unsafeRunSync()",
        "resp.status shouldBe Status.Ok",
        "",
        "// Property test — ScalaCheck generates 100 random currencies",
        "property(\"fromString(show(c)) == Right(c)\") = forAll(genCurrency) { c =>",
        "  Currency.fromString(c.show) == Right(c)",
        "}",
    ])
    s += [body("Run commands:")]
    s += code_block([
        "sbt test                              # unit + property tests",
        'sbt "testOnly *CacheSpec"             # single suite',
        'sbt "testOnly * -- -n forex.it.DockerTest"  # integration only',
    ])

    # ── 7. Integration Testing ────────────────────────────────────────────────
    s += section("7 · Real Integration Testing")
    s += [body("Integration tests use a <b>ScalaTest Tag</b> so they are opt-in and never "
               "run accidentally in normal <b>sbt test</b>.")]
    s += code_block([
        "// DockerTag.scala",
        'object DockerTest extends Tag("forex.it.DockerTest")',
        "",
        "// IntegrationSpec.scala",
        'test("rate not stale — timestamp within 5 min", DockerTest) {',
        '  val resp = httpGet("http://localhost:9090/rates?from=USD&to=JPY")',
        "  val age  = Duration.between(parseTimestamp(resp), Instant.now())",
        "  age.toMinutes should be < 5L",
        "}",
        "",
        'test("10000 requests all return 200", DockerTest) {',
        "  val results = (1 to 10000).toList.parTraverse { _ =>",
        '    httpGet("http://localhost:9090/rates?from=USD&to=JPY")',
        "  }.unsafeRunSync()",
        "  results.count(_.status == 200) shouldBe 10000",
        "}",
    ])
    s += subsection("docker-compose.it.yml — with Healthchecks")
    s += code_block([
        "services:",
        "  one-frame:",
        "    image: paidyinc/one-frame",
        "    ports: [8080:8080]",
        "    healthcheck:",
        '      test: ["CMD", "curl", "-f", "-H",',
        '             "token: 10dc303535874aeccc86a8251e6992f5",',
        '             "http://localhost:8080/rates?pair=USDJPY"]',
        "      interval: 5s  retries: 5",
        "",
        "  forex-proxy:",
        "    build: .",
        "    ports: [9090:9090]",
        "    depends_on:",
        "      one-frame: {condition: service_healthy}",
        "    environment:",
        "      ONE_FRAME_URL: http://one-frame:8080",
        "    healthcheck:",
        '      test: ["CMD","curl","-f",',
        '             "http://localhost:9090/rates?from=USD&to=JPY"]',
        "      interval: 5s  retries: 10",
    ])

    # ── 8. CI/CD ──────────────────────────────────────────────────────────────
    s += [PageBreak()]
    s += section("8 · CI/CD Pipeline  (GitHub Actions)")

    s += code_block([
        "git push / PR",
        "      |",
        "      v",
        "  [test] sbt test + sbt scalafmtCheck",
        "      |-- fail --> block PR",
        "      |",
        "      v",
        "  [build] sbt assembly --> upload forex-assembly.jar artifact",
        "  [integration] docker compose up + sbt testOnly DockerTest",
        "      |-- fail --> block PR",
        "      |",
        "      v",
        "  merge to main",
        "      |",
        "      v",
        "  [cd] docker build + push to Docker Hub (optional)",
    ])

    s += subsection("ci.yml Highlights")
    s += data_table([
        ["Job", "Trigger", "Steps"],
        ["test",        "every push / PR", "checkout · setup-java (cache sbt) · sbt test · sbt scalafmtCheck"],
        ["integration", "after test pass", "pull one-frame · docker compose up --build · wait healthy · sbt testOnly · compose down"],
        ["build",       "after test pass", "sbt assembly · upload JAR artifact"],
        ["cd / docker", "merge to main",   "docker login · docker build+push :latest + :sha"],
    ], col_widths=[24*mm, 32*mm, USABLE_W - 56*mm])
    s += [body("Java setup uses <b>cache: sbt</b> in setup-java — caches ~/.sbt and ~/.ivy2 between "
               "runs so subsequent CI builds only re-download changed dependencies.")]

    # ── 9. Demo Frontend ──────────────────────────────────────────────────────
    s += section("9 · Demo Frontend")
    s += data_table([
        ["Tool", "Purpose"],
        ["Vite + React 18",   "Build tool + UI framework"],
        ["TypeScript",        "Type safety for API response shapes"],
        ["Tailwind CSS",      "Dark theme styling matching Paidy brand"],
        ["fetch API",         "HTTP calls to forex-proxy — no extra client library"],
        ["SVG sparkline",     "Rate history chart — last 10 fetched values"],
    ], col_widths=[40*mm, USABLE_W - 40*mm])

    s += subsection("What It Shows")
    s += [bullet("Currency pair selector — from/to dropdowns with all 9 currencies"),
          bullet("Live rate display — large price with formatted timestamp"),
          bullet("Cache age bar — progress bar showing 0–5 min staleness from timestamp"),
          bullet("Sparkline chart — SVG mini chart of last 10 rate values"),
          bullet("Refresh button + auto-refresh toggle (every 30s)"),
          bullet("Error states — unknown pair (400), service down (503)")]

    s += subsection("useForexRate Hook")
    s += code_block([
        "export function useForexRate(from, to, autoRefresh) {",
        "  const [rate, setRate]       = useState(null);",
        "  const [error, setError]     = useState(null);",
        "  const [history, setHistory] = useState([]);",
        "",
        "  const fetch_ = useCallback(async () => {",
        "    const res = await fetch(",
        "      `http://localhost:9090/rates?from=${from}&to=${to}`",
        "    );",
        "    if (!res.ok) { setError((await res.json()).error); return; }",
        "    const data = await res.json();",
        "    setRate(data);",
        "    setHistory(h => [...h.slice(-9), data.price]);",
        "  }, [from, to]);",
        "",
        "  // auto-refresh every 30s",
        "  useEffect(() => {",
        "    if (!autoRefresh) return;",
        "    const id = setInterval(fetch_, 30_000);",
        "    return () => clearInterval(id);",
        "  }, [fetch_, autoRefresh]);",
        "}",
    ])
    s += [body("Run: <b>cd frontend && npm install && npm run dev</b> — starts on port 5173. "
               "Add to docker-compose.yml with <b>depends_on: forex-proxy</b> for full-stack demo.")]

    # ── 10. Implementation Order ──────────────────────────────────────────────
    s += [PageBreak()]
    s += section("10 · Implementation Order")
    s += data_table([
        ["Step", "Deliverable", "Validates with"],
        ["1",  "Add http4s-blaze-client to Dependencies.scala + build.sbt", "sbt compile"],
        ["2",  "Add OneFrameConfig to ApplicationConfig",                   "sbt compile"],
        ["3",  "Update application.conf with one-frame block",              "sbt compile"],
        ["4",  "Fix Currency.fromString → Either + add .values list",       "CurrencySpec passes"],
        ["5",  "Implement OneFrameLive (fetchAll)",                         "sbt compile + curl one-frame"],
        ["6",  "Implement OneFrameCache (Ref + fs2 fiber + Resource)",      "OneFrameCacheSpec passes"],
        ["7",  "Update Interpreters.scala (live + cached factories)",       "sbt compile"],
        ["8",  "Update Module.scala + Main.scala",                          "sbt run + docker compose up"],
        ["9",  "Fix HTTP error handling in RatesHttpRoutes",                "RatesHttpRoutesSpec passes"],
        ["10", "Write remaining unit + property tests",                     "sbt test — all green"],
        ["11", "Create docker-compose.it.yml",                              "docker compose -f it up works"],
        ["12", "Write IntegrationSpec",                                     "integration suite passes"],
        ["13", "Create .github/workflows/ci.yml",                           "push to GitHub → CI green"],
        ["14", "Scaffold frontend",                                          "npm run dev shows rate"],
        ["15", "Write README with constraint math + design rationale",       "ready to submit"],
    ], col_widths=[12*mm, 90*mm, USABLE_W - 102*mm])

    doc.build(s, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF written: {out}")


if __name__ == "__main__":
    build()
