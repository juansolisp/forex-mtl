package forex.http
package events

import cats.effect.{ ContextShift, IO, Timer }
import forex.config.OneFrameConfig
import forex.domain.LogEvent
import forex.services.events.EventBus
import forex.services.rates.interpreters.{ OneFrameCache, OneFrameLive }
import org.http4s._
import org.http4s.implicits._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

import scala.concurrent.duration._

/**
 * Unit tests for [[EventsHttpRoutes]] — the SSE endpoint.
 *
 * Tests SSE-01, SSE-02, SSE-03, SSE-05 from the TEST_PLAN.
 * SSE-04 (heartbeat within 30s) is intentionally omitted — it would require waiting 30 seconds
 * and is covered by the integration test INT-14 against the full Docker stack.
 *
 * == Stream collection strategy ==
 * The SSE route returns a streaming body (`busStream.merge(heartbeatStream)`) that never
 * terminates on its own. To collect a bounded prefix we:
 * 1. Start a fiber that collects `resp.bodyText.take(1)` (the first emitted SSE chunk).
 * 2. Publish an event to the bus from the main fiber.
 * 3. Join the collection fiber.
 *
 * Publish unblocks `busStream`, which emits a ServerSentEvent frame that becomes the first
 * element of `bodyText`. The SSE encoder formats it as `data: <json>\n\n` UTF-8 bytes.
 *
 * `Concurrent` is required by `EventBus.create` (fs2 Topic) and `start`/`join` (fibers).
 */
class EventsHttpRoutesSpec extends AnyFunSuite with Matchers {

  private val pool = java.util.concurrent.Executors.newCachedThreadPool()
  private val ec   = scala.concurrent.ExecutionContext.fromExecutor(pool)
  implicit val cs: ContextShift[IO] = IO.contextShift(ec)
  implicit val timer: Timer[IO]     = IO.timer(ec)

  private val config = OneFrameConfig(
    uri             = "http://one-frame:8080",
    token           = "test-token",
    refreshInterval = 5.minutes
  )

  private val sampleRefresh: LogEvent = LogEvent.CacheRefresh(
    pairsCount   = 72,
    durationMs   = 50.0,
    timestamp    = "2024-01-01T00:00:00Z",
    callsToday   = 1,
    dailyLimit   = 1000,
    quotaWarning = false
  )

  /** Build an EventBus and a cold OneFrameCache (no-op HTTP client) for route construction. */
  private def makeRoutes(bus: EventBus[IO]): IO[HttpApp[IO]] = {
    val client = org.http4s.client.Client.fromHttpApp[IO](
      HttpRoutes.of[IO] { case _ => IO.pure(Response[IO](Status.Ok).withEntity("[]")) }.orNotFound
    )
    val live = new OneFrameLive[IO](config, client)
    OneFrameCache.create[IO](live, config.refreshInterval, bus).map { case (cache, _) =>
      new EventsHttpRoutes[IO](bus, cache).routes.orNotFound
    }
  }

  // SSE-01: GET /events returns HTTP 200
  test("GET /events returns 200") {
    val resp = EventBus.create[IO].flatMap { bus =>
      makeRoutes(bus).flatMap(_.run(Request[IO](Method.GET, uri"/events")))
    }.unsafeRunSync()

    resp.status shouldBe Status.Ok
  }

  // SSE-02: response carries Content-Type: text/event-stream
  test("GET /events response has Content-Type text/event-stream") {
    val resp = EventBus.create[IO].flatMap { bus =>
      makeRoutes(bus).flatMap(_.run(Request[IO](Method.GET, uri"/events")))
    }.unsafeRunSync()

    val ct = resp.headers.get(org.typelevel.ci.CIString("Content-Type")).map(_.head.value)
    ct.getOrElse("") should include("text/event-stream")
  }

  // SSE-03: events published to the bus appear as JSON-encoded SSE frames in the body stream
  test("published CacheRefresh event appears as JSON in the SSE body stream") {
    val body = (for {
      bus  <- EventBus.create[IO]
      app  <- makeRoutes(bus)
      resp <- app.run(Request[IO](Method.GET, uri"/events"))
      _    <- IO.shift
      fiber <- resp.bodyText.take(1).compile.toList.start
      _    <- bus.publish(sampleRefresh)
      r    <- fiber.join
    } yield r.mkString).unsafeRunSync()

    body should include("CacheRefresh")
  }

  // SSE-05: multiple concurrent SSE connections each independently receive events from the bus
  test("two concurrent SSE connections each receive the published event") {
    val (body1, body2) = (for {
      bus   <- EventBus.create[IO]
      app   <- makeRoutes(bus)
      req    = Request[IO](Method.GET, uri"/events")
      resp1 <- app.run(req)
      resp2 <- app.run(req)
      _     <- IO.shift
      f1    <- resp1.bodyText.take(1).compile.toList.start
      f2    <- resp2.bodyText.take(1).compile.toList.start
      _     <- bus.publish(sampleRefresh)
      r1    <- f1.join
      r2    <- f2.join
    } yield (r1.mkString, r2.mkString)).unsafeRunSync()

    body1 should include("CacheRefresh")
    body2 should include("CacheRefresh")
  }
}
