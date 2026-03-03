package forex.http.rates

import cats.effect.IO
import cats.effect.concurrent.Ref
import forex.domain.{ Currency, LogEvent, Price, Rate, Timestamp }
import forex.programs.rates.{ Algebra => ProgramAlgebra, Protocol => ProgramProtocol }
import forex.programs.rates.errors.{ Error => ProgramError }
import forex.services.events.EventBus
import fs2.Stream
import org.http4s._
import org.http4s.implicits._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

/**
 * Unit tests for [[RatesHttpRoutes]] exercising request validation and response mapping.
 *
 * The program layer is replaced by a stub (`makeProgram`) so these tests are purely about
 * HTTP concerns: query param parsing, status codes, and response body shape. No service or
 * cache logic runs. This isolation means a failure here points unambiguously to the HTTP layer.
 *
 * `IO` is used (rather than `Id`) because http4s route handlers operate in `F[Response[F]]`,
 * and `Id` cannot represent asynchronous HTTP effects. `ContextShift` is required by the
 * http4s blaze test infrastructure for running `IO` computations synchronously.
 */
class RatesHttpRoutesSpec extends AnyFunSuite with Matchers {

  implicit val cs: cats.effect.ContextShift[IO] = IO.contextShift(scala.concurrent.ExecutionContext.global)

  /** A no-op event bus for tests — discards all published events. */
  private val noopBus: EventBus[IO] = new EventBus[IO] {
    def publish(event: LogEvent): IO[Unit] = IO.unit
    def subscribe: Stream[IO, LogEvent]    = Stream.empty
  }

  private val fixedRate = Rate(
    Rate.Pair(Currency.USD, Currency.JPY),
    Price(BigDecimal("0.71")),
    Timestamp.now
  )

  /**
   * Build a stub program that always returns the given `result`, ignoring the request.
   * Allows each test to control exactly what the program layer returns without any real logic.
   */
  private def makeProgram(result: ProgramError Either Rate): ProgramAlgebra[IO] =
    new ProgramAlgebra[IO] {
      override def get(req: ProgramProtocol.GetRatesRequest): IO[ProgramError Either Rate] =
        IO.pure(result)
    }

  private def routes(program: ProgramAlgebra[IO]): HttpApp[IO] =
    new RatesHttpRoutes[IO](program, noopBus).routes.orNotFound

  /** Run a request and return (status, body) — body consumed inside the IO chain. */
  private def run(app: HttpApp[IO], req: Request[IO]): (Status, String) =
    app.run(req).flatMap(r => r.bodyText.compile.string.map(b => (r.status, b))).unsafeRunSync()

  test("GET /rates?from=USD&to=JPY returns 200 with rate JSON") {
    val app           = routes(makeProgram(Right(fixedRate)))
    val req           = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
    val (status, body) = run(app, req)

    status shouldBe Status.Ok
    body should include("price")
    body should include("USD")
    body should include("JPY")
  }

  test("GET /rates?from=INVALID&to=JPY returns 400") {
    // "INVALID" does not parse as a Currency; the ValidatingQueryParamDecoderMatcher
    // yields Invalid, and the route handler returns 400 with a sanitized error message.
    val app  = routes(makeProgram(Right(fixedRate)))
    val req  = Request[IO](Method.GET, uri"/rates?from=INVALID&to=JPY")
    run(app, req)._1 shouldBe Status.BadRequest
  }

  test("GET /rates?from=USD&to=JPY returns 500 when program fails") {
    val app = routes(makeProgram(Left(ProgramError.RateLookupFailed("upstream error"))))
    val req = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
    run(app, req)._1 shouldBe Status.InternalServerError
  }

  test("GET /rates without params returns 400") {
    // With no query params, both OptionalValidatingQueryParamDecoderMatcher extractors return None.
    // `requireParam` converts None → Invalid, so the `_` branch fires and returns 400.
    // Previously (with ValidatingQueryParamDecoderMatcher) the route didn't match at all,
    // resulting in 404. The switch to OptionalValidating fixes that.
    val app = routes(makeProgram(Right(fixedRate)))
    val req = Request[IO](Method.GET, uri"/rates")
    run(app, req)._1 shouldBe Status.BadRequest
  }

  test("GET /rates?from=USD&to=USD returns 400 (same currency)") {
    // The route explicitly guards against from == to with a dedicated 400 branch.
    // Without this check, a client could ask for the USD/USD pair which One-Frame
    // does not return — the cache would yield a Left and the client would get a 500
    // instead of the more informative 400.
    val app            = routes(makeProgram(Right(fixedRate)))
    val req            = Request[IO](Method.GET, uri"/rates?from=USD&to=USD")
    val (status, body) = run(app, req)

    status shouldBe Status.BadRequest
    body should include("must be different")
  }

  test("GET /rates response includes X-Request-ID header") {
    val app  = routes(makeProgram(Right(fixedRate)))
    val req  = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
    val resp = app.run(req).unsafeRunSync()

    resp.status shouldBe Status.Ok
    resp.headers.get(org.typelevel.ci.CIString("X-Request-ID")) shouldBe defined
  }

  // ─── Auth middleware integration ─────────────────────────────────────────────

  private val proxyToken = "10dc303535874aeccc86a8251e699999"

  /**
   * Build routes wrapped with [[forex.http.AuthMiddleware]], matching how [[forex.Module]]
   * wires things in production. This exercises the auth layer end-to-end with real routes.
   */
  private def protectedRoutes(program: ProgramAlgebra[IO]): HttpApp[IO] =
    forex.http.AuthMiddleware(proxyToken)(
      new RatesHttpRoutes[IO](program, noopBus).routes
    ).orNotFound

  test("GET /rates with correct X-Proxy-Token returns 200") {
    val app = protectedRoutes(makeProgram(Right(fixedRate)))
    val req = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
      .putHeaders(Header.Raw(org.typelevel.ci.CIString("X-Proxy-Token"), proxyToken))
    run(app, req)._1 shouldBe Status.Ok
  }

  test("GET /rates with wrong X-Proxy-Token returns 401") {
    val app = protectedRoutes(makeProgram(Right(fixedRate)))
    val req = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
      .putHeaders(Header.Raw(org.typelevel.ci.CIString("X-Proxy-Token"), "bad-token"))
    run(app, req)._1 shouldBe Status.Unauthorized
  }

  test("GET /rates without X-Proxy-Token returns 401") {
    val app = protectedRoutes(makeProgram(Right(fixedRate)))
    val req = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
    run(app, req)._1 shouldBe Status.Unauthorized
  }

  // HTTP-06: each request gets a unique X-Request-ID
  test("two requests get different X-Request-ID values") {
    val app = routes(makeProgram(Right(fixedRate)))
    val req = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
    val (id1, id2) = (for {
      r1 <- app.run(req)
      r2 <- app.run(req)
    } yield (
      r1.headers.get(org.typelevel.ci.CIString("X-Request-ID")).map(_.head.value),
      r2.headers.get(org.typelevel.ci.CIString("X-Request-ID")).map(_.head.value)
    )).unsafeRunSync()

    id1 shouldBe defined
    id2 shouldBe defined
    id1 should not equal id2
  }

  // HTTP-07: successful /rates request publishes a ProxyRequest SSE event with status=200
  test("successful GET /rates publishes ProxyRequest event with status 200") {
    val events = (for {
      captured <- Ref.of[IO, List[LogEvent]](Nil)
      captureBus = new EventBus[IO] {
        def publish(event: LogEvent): IO[Unit] = captured.update(_ :+ event)
        def subscribe: Stream[IO, LogEvent]    = Stream.empty
      }
      app = new RatesHttpRoutes[IO](makeProgram(Right(fixedRate)), captureBus).routes.orNotFound
      req = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
      _      <- app.run(req)
      result <- captured.get
    } yield result).unsafeRunSync()

    events should have size 1
    events.head shouldBe a[LogEvent.ProxyRequest]
    events.head.asInstanceOf[LogEvent.ProxyRequest].status shouldBe 200
  }

  // HTTP-12: missing `to` parameter returns 400
  test("GET /rates?from=USD (missing to) returns 400") {
    val app = routes(makeProgram(Right(fixedRate)))
    val req = Request[IO](Method.GET, uri"/rates?from=USD")
    run(app, req)._1 shouldBe Status.BadRequest
  }

  // HTTP-13: invalid `to` currency returns 400
  test("GET /rates?from=USD&to=INVALID returns 400") {
    val app = routes(makeProgram(Right(fixedRate)))
    val req = Request[IO](Method.GET, uri"/rates?from=USD&to=INVALID")
    run(app, req)._1 shouldBe Status.BadRequest
  }

  // HTTP-15: program error → /rates publishes ProxyRequest SSE event with status=500 and no price
  test("failed GET /rates publishes ProxyRequest event with status 500 and no price") {
    val events = (for {
      captured <- Ref.of[IO, List[LogEvent]](Nil)
      captureBus = new EventBus[IO] {
        def publish(event: LogEvent): IO[Unit] = captured.update(_ :+ event)
        def subscribe: Stream[IO, LogEvent]    = Stream.empty
      }
      errorProgram = makeProgram(Left(forex.programs.rates.errors.Error.RateLookupFailed("err")))
      app = new RatesHttpRoutes[IO](errorProgram, captureBus).routes.orNotFound
      req = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
      _      <- app.run(req)
      result <- captured.get
    } yield result).unsafeRunSync()

    events should have size 1
    events.head shouldBe a[LogEvent.ProxyRequest]
    val e = events.head.asInstanceOf[LogEvent.ProxyRequest]
    e.status shouldBe 500
    e.price  shouldBe None
  }

}
