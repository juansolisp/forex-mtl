package forex.http
package config

import cats.effect.{ ContextShift, IO, Timer }
import cats.syntax.flatMap._
import forex.config.OneFrameConfig
import forex.domain.LogEvent
import forex.services.events.EventBus
import forex.services.rates.interpreters.{ OneFrameCache, OneFrameLive }
import fs2.Stream
import io.circe.Json
import io.circe.parser._
import org.http4s._
import org.http4s.implicits._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

import scala.concurrent.duration._

class ConfigHttpRoutesSpec extends AnyFunSuite with Matchers {

  private val pool = java.util.concurrent.Executors.newCachedThreadPool()
  private val ec   = scala.concurrent.ExecutionContext.fromExecutor(pool)
  implicit val cs: ContextShift[IO] = IO.contextShift(ec)
  implicit val timer: Timer[IO]     = IO.timer(ec)

  private val config = OneFrameConfig(
    uri             = "http://one-frame:8080",
    token           = "test-token",
    refreshInterval = 4.minutes
  )

  private val noopBus: EventBus[IO] = new EventBus[IO] {
    def publish(event: LogEvent): IO[Unit] = IO.unit
    def subscribe: Stream[IO, LogEvent]    = Stream.empty
  }

  private val allPairsJson: String = {
    import forex.domain.Currency
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

  private def makeCache(json: String): IO[OneFrameCache[IO]] = {
    val client = org.http4s.client.Client.fromHttpApp[IO](
      HttpRoutes
        .of[IO] { case _ =>
          IO.pure(Response[IO](Status.Ok).withEntity(json))
        }
        .orNotFound
    )
    val live = new OneFrameLive[IO](config, client)
    OneFrameCache.create[IO](live, config.refreshInterval, noopBus).map(_._1)
  }

  private def routes(cache: OneFrameCache[IO]): HttpApp[IO] =
    new ConfigHttpRoutes[IO](cache).routes.orNotFound

  private def jsonRequest(method: Method, uri: Uri, body: Json): Request[IO] =
    Request[IO](method, uri)
      .withEntity(body.noSpaces)
      .withContentType(headers.`Content-Type`(MediaType.application.json))

  // ─── GET /config/status ──────────────────────────────────────────────────────

  test("GET /config/status returns 200 with interval, quota, and null lastRefreshedAt on cold start") {
    val (status, body) = makeCache("[]").flatMap { cache =>
      val app = routes(cache)
      app.run(Request[IO](Method.GET, uri"/config/status"))
        .flatMap(r => r.bodyText.compile.string.map(b => (r.status, b)))
    }.unsafeRunSync()

    status shouldBe Status.Ok
    val json = parse(body).toOption.get
    json.hcursor.get[Long]("intervalSeconds").toOption            shouldBe Some(240L)
    json.hcursor.downField("lastRefreshedAt").focus.map(_.isNull) shouldBe Some(true)
    json.hcursor.get[Int]("callsToday").toOption                  shouldBe Some(0)
    json.hcursor.get[Int]("dailyLimit").toOption                  shouldBe Some(1000)
    json.hcursor.get[Boolean]("quotaWarning").toOption            shouldBe Some(false)
  }

  test("GET /config/status shows callsToday = 1 after one successful refresh") {
    val (status, body) = makeCache(allPairsJson).flatMap { cache =>
      cache.forceRefresh >>
        routes(cache).run(Request[IO](Method.GET, uri"/config/status"))
          .flatMap(r => r.bodyText.compile.string.map(b => (r.status, b)))
    }.unsafeRunSync()

    status shouldBe Status.Ok
    val json = parse(body).toOption.get
    json.hcursor.get[Int]("callsToday").toOption                          shouldBe Some(1)
    json.hcursor.downField("lastRefreshedAt").focus.map(_.isNull)         shouldBe Some(false)
  }

  // ─── GET /config/refresh-interval ────────────────────────────────────────────

  test("GET /config/refresh-interval returns 200 with current interval") {
    val (status, body) = makeCache("[]").flatMap { cache =>
      routes(cache).run(Request[IO](Method.GET, uri"/config/refresh-interval"))
        .flatMap(r => r.bodyText.compile.string.map(b => (r.status, b)))
    }.unsafeRunSync()

    status shouldBe Status.Ok
    val json = parse(body).toOption.get
    json.hcursor.get[Long]("seconds").toOption shouldBe Some(240L)
  }

  // ─── PUT /config/refresh-interval ────────────────────────────────────────────

  test("PUT /config/refresh-interval with valid seconds returns 200 and updated interval") {
    val (status, body) = makeCache(allPairsJson).flatMap { cache =>
      routes(cache).run(jsonRequest(Method.PUT, uri"/config/refresh-interval", Json.obj("seconds" -> Json.fromInt(120))))
        .flatMap(r => r.bodyText.compile.string.map(b => (r.status, b)))
    }.unsafeRunSync()

    status shouldBe Status.Ok
    val json = parse(body).toOption.get
    json.hcursor.get[Long]("seconds").toOption shouldBe Some(120L)
  }

  test("PUT /config/refresh-interval with seconds below 90 returns 400") {
    val (status, body) = makeCache("[]").flatMap { cache =>
      routes(cache).run(jsonRequest(Method.PUT, uri"/config/refresh-interval", Json.obj("seconds" -> Json.fromInt(30))))
        .flatMap(r => r.bodyText.compile.string.map(b => (r.status, b)))
    }.unsafeRunSync()

    status shouldBe Status.BadRequest
    body should include("between")
  }

  test("PUT /config/refresh-interval with seconds above 300 returns 400") {
    val status = makeCache("[]").flatMap { cache =>
      routes(cache).run(jsonRequest(Method.PUT, uri"/config/refresh-interval", Json.obj("seconds" -> Json.fromInt(600))))
        .map(_.status)
    }.unsafeRunSync()

    status shouldBe Status.BadRequest
  }

  test("PUT /config/refresh-interval with boundary value 90 returns 200") {
    val status = makeCache(allPairsJson).flatMap { cache =>
      routes(cache).run(jsonRequest(Method.PUT, uri"/config/refresh-interval", Json.obj("seconds" -> Json.fromInt(90))))
        .map(_.status)
    }.unsafeRunSync()

    status shouldBe Status.Ok
  }

  test("PUT /config/refresh-interval with boundary value 300 returns 200") {
    val status = makeCache(allPairsJson).flatMap { cache =>
      routes(cache).run(jsonRequest(Method.PUT, uri"/config/refresh-interval", Json.obj("seconds" -> Json.fromInt(300))))
        .map(_.status)
    }.unsafeRunSync()

    status shouldBe Status.Ok
  }

  // ─── POST /config/force-refresh ──────────────────────────────────────────────

  test("POST /config/force-refresh returns 200") {
    val (status, body) = makeCache(allPairsJson).flatMap { cache =>
      routes(cache).run(Request[IO](Method.POST, uri"/config/force-refresh"))
        .flatMap(r => r.bodyText.compile.string.map(b => (r.status, b)))
    }.unsafeRunSync()

    status shouldBe Status.Ok
    body should include("refreshed")
  }
}
