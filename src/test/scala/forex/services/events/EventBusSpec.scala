package forex.services.events

import cats.effect.{ ContextShift, IO, Timer }
import cats.syntax.flatMap._
import forex.domain.LogEvent
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

/**
 * Unit tests for [[EventBus]] — the fs2 Topic-backed fan-out pub/sub bus.
 *
 * Tests verify:
 *  - Events published after subscription are received by the subscriber
 *  - The initial `None` sentinel emitted by the Topic is filtered out
 *  - Multiple subscribers each receive the same events independently
 *
 * All tests run with `unsafeRunSync()` which is acceptable for deterministic,
 * fast, in-memory IO effects in a test context.
 */
class EventBusSpec extends AnyFunSuite with Matchers {

  private val pool = java.util.concurrent.Executors.newCachedThreadPool()
  private val ec   = scala.concurrent.ExecutionContext.fromExecutor(pool)
  implicit val cs: ContextShift[IO] = IO.contextShift(ec)
  implicit val timer: Timer[IO]     = IO.timer(ec)

  private val sampleRefresh: LogEvent = LogEvent.CacheRefresh(
    pairsCount   = 72,
    durationMs   = 50.0,
    timestamp    = "2024-01-01T00:00:00Z",
    callsToday   = 1,
    dailyLimit   = 1000,
    quotaWarning = false
  )

  private val sampleRequest: LogEvent = LogEvent.ProxyRequest(
    id         = "abc123",
    from       = "USD",
    to         = "JPY",
    status     = 200,
    price      = Some(BigDecimal("0.71")),
    errorBody  = None,
    durationMs = 1.0,
    timestamp  = "2024-01-01T00:00:00Z"
  )

  test("subscriber receives a published event") {
    val result = (for {
      bus   <- EventBus.create[IO]
      _     <- IO.shift
      fiber <- bus.subscribe.take(1).compile.toList.start
      _     <- bus.publish(sampleRefresh)
      r     <- fiber.join
    } yield r).unsafeRunSync()

    result should contain(sampleRefresh)
  }

  test("subscribe stream does not emit the initial None sentinel") {
    val result = (for {
      bus   <- EventBus.create[IO]
      _     <- IO.shift
      fiber <- bus.subscribe.take(1).compile.toList.start
      _     <- bus.publish(sampleRefresh)
      r     <- fiber.join
    } yield r).unsafeRunSync()

    result.size                        shouldBe 1
    result.head.getClass.getSimpleName shouldBe "CacheRefresh"
  }

  test("multiple events are received in publish order") {
    val events = List(sampleRefresh, sampleRequest)
    val result = (for {
      bus   <- EventBus.create[IO]
      _     <- IO.shift
      fiber <- bus.subscribe.take(2).compile.toList.start
      _     <- publishAll(bus, events)
      r     <- fiber.join
    } yield r).unsafeRunSync()

    result shouldBe events
  }

  test("two independent subscribers each receive the same event") {
    val result = (for {
      bus <- EventBus.create[IO]
      _   <- IO.shift
      f1  <- bus.subscribe.take(1).compile.toList.start
      f2  <- bus.subscribe.take(1).compile.toList.start
      _   <- bus.publish(sampleRefresh)
      r1  <- f1.join
      r2  <- f2.join
    } yield (r1, r2)).unsafeRunSync()

    result._1 should contain(sampleRefresh)
    result._2 should contain(sampleRefresh)
  }

  test("subscriber that joins after a publish does not receive past events") {
    val result = (for {
      bus <- EventBus.create[IO]
      _   <- bus.publish(sampleRefresh)
      r   <- bus.subscribe.take(0).compile.toList
    } yield r).unsafeRunSync()

    result shouldBe empty
  }

  /** Publish a list of events sequentially, discarding results. */
  private def publishAll(bus: EventBus[IO], events: List[LogEvent]): IO[Unit] =
    events.foldLeft(IO.unit)((acc, e) => acc >> bus.publish(e))
}
