package forex.services.rates

import cats.effect.{ ContextShift, IO, Timer }
import cats.syntax.flatMap._
import forex.config.OneFrameConfig
import forex.domain.{ Currency, LogEvent, Rate }
import forex.services.events.EventBus
import forex.services.rates.interpreters.{ OneFrameCache, OneFrameLive }
import fs2.Stream
import org.http4s._
import org.http4s.client.Client
import org.http4s.implicits._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

import scala.concurrent.duration._

/**
 * Unit tests for [[OneFrameCache]] using an in-process fake HTTP client.
 *
 * Tests focus on the cache state machine:
 *  - empty before refresh is run
 *  - populated after refresh is run
 *  - returns Left for pairs absent from the One-Frame response
 *  - quota counter increments on each successful refresh
 *  - forceRefresh populates the cache outside the normal schedule
 *
 * The `Timer` and `ContextShift` instances are required by `Concurrent` and `Stream.fixedDelay`
 * inside the cache, even though the periodic delay is never actually awaited in these tests.
 */
class OneFrameCacheSpec extends AnyFunSuite with Matchers {

  private val pool = java.util.concurrent.Executors.newCachedThreadPool()
  private val ec   = scala.concurrent.ExecutionContext.fromExecutor(pool)
  implicit val cs: ContextShift[IO] = IO.contextShift(ec)
  implicit val timer: Timer[IO]     = IO.timer(ec)

  private val config = OneFrameConfig(
    uri             = "http://one-frame:8080",
    token           = "test-token",
    refreshInterval = 5.minutes
  )

  /** No-op event bus — discards all published events, allowing tests to run without a Topic. */
  private val noopBus: EventBus[IO] = new EventBus[IO] {
    def publish(event: LogEvent): IO[Unit] = IO.unit
    def subscribe: Stream[IO, LogEvent]    = Stream.empty
  }

  private val allPairsJson: String = {
    val pairs = for {
      from <- Currency.values
      to   <- Currency.values
      if from != to
    } yield (from, to)
    pairs
      .map { case (f, t) =>
        val fs = cats.Show[Currency].show(f)
        val ts = cats.Show[Currency].show(t)
        s"""{"from":"$fs","to":"$ts","bid":0.5,"ask":0.6,"price":0.55,"time_stamp":"2021-01-01T00:00:00.000Z"}"""
      }
      .mkString("[", ",", "]")
  }

  private def liveWithJson(json: String): OneFrameLive[IO] = {
    val client = Client.fromHttpApp[IO](
      HttpRoutes
        .of[IO] { case _ =>
          IO.pure(Response[IO](Status.Ok).withEntity(json))
        }
        .orNotFound
    )
    new OneFrameLive[IO](config, client)
  }

  test("get returns Left when cache is empty") {
    val result = OneFrameCache
      .create[IO](liveWithJson("[]"), config.refreshInterval, noopBus)
      .flatMap { case (cache, _) =>
        // The refresh stream is deliberately not run here — we want to test the empty state.
        cache.get(Rate.Pair(Currency.USD, Currency.JPY))
      }
      .unsafeRunSync()

    result shouldBe a[Left[_, _]]
  }

  test("get returns Right after refresh stream populates cache") {
    val result = (for {
      pair          <- OneFrameCache.create[IO](liveWithJson(allPairsJson), config.refreshInterval, noopBus)
      (cache, refresh) = pair
      _             <- IO.shift
      _             <- refresh.take(1).compile.drain
      r             <- cache.get(Rate.Pair(Currency.USD, Currency.JPY))
    } yield r).unsafeRunSync()

    result shouldBe a[Right[_, _]]
    result.map(_.pair) shouldBe Right(Rate.Pair(Currency.USD, Currency.JPY))
  }

  test("cache returns Left if pair was not in One-Frame response") {
    val result = (for {
      pair          <- OneFrameCache.create[IO](liveWithJson("[]"), config.refreshInterval, noopBus)
      (cache, refresh) = pair
      _             <- IO.shift
      _             <- refresh.take(1).compile.drain
      r             <- cache.get(Rate.Pair(Currency.USD, Currency.JPY))
    } yield r).unsafeRunSync()

    result shouldBe a[Left[_, _]]
  }

  test("quota starts at 0 before any refresh") {
    val quota = OneFrameCache
      .create[IO](liveWithJson("[]"), config.refreshInterval, noopBus)
      .flatMap { case (cache, _) => cache.getQuota }
      .unsafeRunSync()

    quota.callsToday shouldBe 0
  }

  test("quota increments to 1 after one successful refresh") {
    val quota = (for {
      pair          <- OneFrameCache.create[IO](liveWithJson(allPairsJson), config.refreshInterval, noopBus)
      (cache, refresh) = pair
      _             <- IO.shift
      _             <- refresh.take(1).compile.drain
      q             <- cache.getQuota
    } yield q).unsafeRunSync()

    quota.callsToday shouldBe 1
  }

  test("quota increments on each forceRefresh call") {
    val quota = OneFrameCache
      .create[IO](liveWithJson(allPairsJson), config.refreshInterval, noopBus)
      .flatMap { case (cache, _) =>
        cache.forceRefresh >>
          cache.forceRefresh >>
          cache.forceRefresh >>
          cache.getQuota
      }
      .unsafeRunSync()

    quota.callsToday shouldBe 3
  }

  test("quota does NOT increment when One-Frame returns an error response") {
    val quota = (for {
      pair          <- OneFrameCache.create[IO](liveWithJson("not-json"), config.refreshInterval, noopBus)
      (cache, refresh) = pair
      _             <- IO.shift
      _             <- refresh.take(1).compile.drain
      q             <- cache.getQuota
    } yield q).unsafeRunSync()

    quota.callsToday shouldBe 0
  }

  test("forceRefresh populates the cache immediately") {
    val result = OneFrameCache
      .create[IO](liveWithJson(allPairsJson), config.refreshInterval, noopBus)
      .flatMap { case (cache, _) =>
        cache.forceRefresh >> cache.get(Rate.Pair(Currency.EUR, Currency.USD))
      }
      .unsafeRunSync()

    result shouldBe a[Right[_, _]]
  }

  test("getInterval returns the initial configured interval") {
    val interval = OneFrameCache
      .create[IO](liveWithJson("[]"), config.refreshInterval, noopBus)
      .flatMap { case (cache, _) => cache.getInterval }
      .unsafeRunSync()

    interval shouldBe 5.minutes
  }

  test("setInterval updates the interval returned by getInterval") {
    val interval = OneFrameCache
      .create[IO](liveWithJson("[]"), config.refreshInterval, noopBus)
      .flatMap { case (cache, _) =>
        cache.setInterval(2.minutes) >> cache.getInterval
      }
      .unsafeRunSync()

    interval shouldBe 2.minutes
  }

  test("getLastRefreshedAt returns None before any refresh") {
    val ts = OneFrameCache
      .create[IO](liveWithJson("[]"), config.refreshInterval, noopBus)
      .flatMap { case (cache, _) => cache.getLastRefreshedAt }
      .unsafeRunSync()

    ts shouldBe None
  }

  test("getLastRefreshedAt returns Some after a successful refresh") {
    val ts = OneFrameCache
      .create[IO](liveWithJson(allPairsJson), config.refreshInterval, noopBus)
      .flatMap { case (cache, _) =>
        cache.forceRefresh >> cache.getLastRefreshedAt
      }
      .unsafeRunSync()

    ts shouldBe a[Some[_]]
  }

  // SVC-21: stale cache values survive a failed refresh — old entries remain accessible
  test("cache retains old rates after a failed refresh") {
    // First prime the cache with good data, then trigger a bad refresh and verify the old rate is still present.
    import cats.effect.concurrent.Ref
    // Use a Ref to switch between good and bad responses
    val result = Ref.of[IO, String](allPairsJson).flatMap { responseRef =>
      val switchableClient = org.http4s.client.Client.fromHttpApp[IO](
        HttpRoutes
          .of[IO] { case _ =>
            responseRef.get.flatMap(json => IO.pure(Response[IO](Status.Ok).withEntity(json)))
          }
          .orNotFound
      )
      val switchableLive = new OneFrameLive[IO](config, switchableClient)
      OneFrameCache.create[IO](switchableLive, config.refreshInterval, noopBus).flatMap { case (cache, _) =>
        // Warm the cache with good data
        cache.forceRefresh >>
          // Switch to returning bad JSON
          responseRef.set("not-json") >>
          // Failed refresh — cache should keep old rates
          cache.forceRefresh >>
          cache.get(Rate.Pair(Currency.USD, Currency.JPY))
      }
    }.unsafeRunSync()

    result shouldBe a[Right[_, _]]
  }

  // SVC-22: refresh stream is resilient — continues after a One-Frame error cycle
  // We use forceRefresh (which calls doRefresh directly) to sequence: good → bad → good,
  // bypassing the interruptibleSleep in the periodic refresh stream.
  test("cache continues serving rates after a failed refresh cycle") {
    import cats.effect.concurrent.Ref
    // Sequence: good → bad → good responses via forceRefresh calls
    val responses = List(allPairsJson, "not-json", allPairsJson)
    val result = Ref.of[IO, List[String]](responses).flatMap { responseRef =>
      val switchableClient = org.http4s.client.Client.fromHttpApp[IO](
        HttpRoutes
          .of[IO] { case _ =>
            responseRef.modify {
              case head :: tail => (tail, head)
              case Nil          => (Nil, "not-json")
            }.flatMap(json => IO.pure(Response[IO](Status.Ok).withEntity(json)))
          }
          .orNotFound
      )
      val switchableLive = new OneFrameLive[IO](config, switchableClient)
      OneFrameCache.create[IO](switchableLive, config.refreshInterval, noopBus).flatMap { case (cache, _) =>
        // Three forceRefresh calls: good, bad, good — doRefresh handles errors without crashing.
        cache.forceRefresh >>   // good: populates cache
          cache.forceRefresh >> // bad: logs error, cache retains old values
          cache.forceRefresh >> // good: repopulates cache
          cache.get(Rate.Pair(Currency.USD, Currency.JPY))
      }
    }.unsafeRunSync()

    // After good→bad→good cycle the cache should have a valid rate
    result shouldBe a[Right[_, _]]
  }

  // SVC-23: successful refresh publishes a CacheRefresh SSE event on the bus
  test("refresh publishes CacheRefresh event to the event bus") {
    import cats.effect.concurrent.Ref
    val result = (for {
      ref <- Ref.of[IO, List[LogEvent]](Nil)
      captureBus = new EventBus[IO] {
        def publish(event: LogEvent): IO[Unit] = ref.update(_ :+ event)
        def subscribe: fs2.Stream[IO, LogEvent] = fs2.Stream.empty
      }
      _      <- IO.shift
      result <- OneFrameCache.create[IO](liveWithJson(allPairsJson), config.refreshInterval, captureBus).flatMap { case (_, refresh) =>
                  refresh.take(1).compile.drain >> ref.get
                }
    } yield result).unsafeRunSync()

    result should have size 1
    result.head shouldBe a[LogEvent.CacheRefresh]
    result.head.asInstanceOf[LogEvent.CacheRefresh].pairsCount shouldBe 72
  }

  // SVC-24: failed refresh publishes a CacheRefreshFailed SSE event on the bus
  test("refresh publishes CacheRefreshFailed event on One-Frame error") {
    import cats.effect.concurrent.Ref
    val result = (for {
      ref <- Ref.of[IO, List[LogEvent]](Nil)
      captureBus = new EventBus[IO] {
        def publish(event: LogEvent): IO[Unit] = ref.update(_ :+ event)
        def subscribe: fs2.Stream[IO, LogEvent] = fs2.Stream.empty
      }
      _      <- IO.shift
      result <- OneFrameCache.create[IO](liveWithJson("not-json"), config.refreshInterval, captureBus).flatMap { case (_, refresh) =>
                  refresh.take(1).compile.drain >> ref.get
                }
    } yield result).unsafeRunSync()

    result should have size 1
    result.head shouldBe a[LogEvent.CacheRefreshFailed]
  }
}
