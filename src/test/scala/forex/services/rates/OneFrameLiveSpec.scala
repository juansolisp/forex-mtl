package forex.services.rates

import cats.effect.IO
import forex.config.OneFrameConfig
import forex.domain._
import forex.services.rates.interpreters.OneFrameLive
import org.http4s._
import org.http4s.client.Client
import org.http4s.implicits._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers
import scala.concurrent.duration._

/**
 * Unit tests for [[OneFrameLive]] using an in-process fake HTTP client.
 *
 * No real network calls are made. `Client.fromHttpApp` builds a client that dispatches
 * requests to a provided `HttpApp[IO]` in memory, giving us full control over the
 * "server" response without spinning up a real HTTP server. This makes the tests fast,
 * deterministic, and executable in CI without any running services.
 */
class OneFrameLiveSpec extends AnyFunSuite with Matchers {

  private val config = OneFrameConfig(
    uri             = "http://one-frame:8080",
    token           = "test-token",
    refreshInterval = 4.minutes
  )

  /**
   * Build a fake HTTP client that ignores the request and always returns `body` with HTTP 200.
   * Used for happy-path tests where the exact request shape is not under test.
   */
  private def fakeClient(body: String): Client[IO] =
    Client.fromHttpApp[IO](
      HttpRoutes
        .of[IO] { case _ =>
          IO.pure(Response[IO](Status.Ok).withEntity(body))
        }
        .orNotFound
    )

  private val sampleJson =
    """[{"from":"USD","to":"JPY","bid":0.61,"ask":0.82,"price":0.71,"time_stamp":"2021-01-01T00:00:00.000Z"}]"""

  test("get returns Right(Rate) when One-Frame responds correctly") {
    val client = fakeClient(sampleJson)
    val live   = new OneFrameLive[IO](config, client)
    val pair   = Rate.Pair(Currency.USD, Currency.JPY)

    val result = live.get(pair).unsafeRunSync()
    result shouldBe a[Right[_, _]]
    result.map(_.pair) shouldBe Right(pair)
  }

  test("get returns Left when HTTP call fails") {
    val failingClient = Client.fromHttpApp[IO](
      HttpRoutes
        .of[IO] { case _ =>
          IO.raiseError(new RuntimeException("connection refused"))
        }
        .orNotFound
    )
    val live = new OneFrameLive[IO](config, failingClient)
    val pair = Rate.Pair(Currency.USD, Currency.JPY)

    val result = live.get(pair).unsafeRunSync()
    result shouldBe a[Left[_, _]]
  }

  test("fetchAll retrieves all pairs in one call") {
    val pairs = for {
      from <- Currency.values
      to   <- Currency.values
      if from != to
    } yield Rate.Pair(from, to)

    // Build JSON response with all 72 pairs
    val allRatesJson = pairs
      .map { p =>
        val f = cats.Show[Currency].show(p.from)
        val t = cats.Show[Currency].show(p.to)
        s"""{"from":"$f","to":"$t","bid":0.5,"ask":0.6,"price":0.55,"time_stamp":"2021-01-01T00:00:00.000Z"}"""
      }
      .mkString("[", ",", "]")

    val client = fakeClient(allRatesJson)
    val live   = new OneFrameLive[IO](config, client)

    val result = live.fetchAll(pairs).unsafeRunSync()
    result shouldBe a[Right[_, _]]
    result.map(_.size) shouldBe Right(72)
  }

  test("token is set in request header") {
    // Spy client that captures the value of the `token` header before returning a valid response.
    // This verifies that OneFrameLive sends the custom `token` header (not `Authorization: Bearer`)
    // as required by the One-Frame API contract.
    var capturedToken: Option[String] = None
    val spyClient = Client.fromHttpApp[IO](
      HttpRoutes
        .of[IO] { case req =>
          capturedToken = req.headers.get(org.typelevel.ci.CIString("token")).map(_.head.value)
          IO.pure(Response[IO](Status.Ok).withEntity(sampleJson))
        }
        .orNotFound
    )
    val live = new OneFrameLive[IO](config, spyClient)
    live.get(Rate.Pair(Currency.USD, Currency.JPY)).unsafeRunSync()
    capturedToken shouldBe Some("test-token")
  }

  // SVC-05: malformed JSON response body → Left (parse failure is handled gracefully)
  test("get returns Left when response body is malformed JSON") {
    val client = fakeClient("not valid json at all")
    val live   = new OneFrameLive[IO](config, client)
    val result = live.get(Rate.Pair(Currency.USD, Currency.JPY)).unsafeRunSync()
    result shouldBe a[Left[_, _]]
  }

  // SVC-06: fetchAll builds the query string with all pairs in the format One-Frame expects
  test("fetchAll URI contains pair params for all requested pairs") {
    val pairs = List(Rate.Pair(Currency.USD, Currency.JPY), Rate.Pair(Currency.EUR, Currency.GBP))
    var capturedUri: Option[String] = None
    val spyClient = Client.fromHttpApp[IO](
      HttpRoutes
        .of[IO] { case req =>
          capturedUri = Some(req.uri.renderString)
          // Return a minimal valid response so the call doesn't fail
          val json =
            """[{"from":"USD","to":"JPY","bid":0.5,"ask":0.6,"price":0.55,"time_stamp":"2021-01-01T00:00:00.000Z"},
              |{"from":"EUR","to":"GBP","bid":0.8,"ask":0.9,"price":0.85,"time_stamp":"2021-01-01T00:00:00.000Z"}]"""
              .stripMargin
          IO.pure(Response[IO](Status.Ok).withEntity(json))
        }
        .orNotFound
    )
    val live = new OneFrameLive[IO](config, spyClient)
    live.fetchAll(pairs).unsafeRunSync()
    capturedUri.getOrElse("") should include("pair=USDJPY")
    capturedUri.getOrElse("") should include("pair=EURGBP")
  }

  // SVC-07: toRate maps the `price` field (not bid or ask) onto Rate.price
  test("toRate uses the price field, not bid or ask") {
    // Provide distinct bid / ask / price values so the wrong field would be detectable.
    val json =
      """[{"from":"USD","to":"JPY","bid":0.10,"ask":0.20,"price":0.99,"time_stamp":"2021-01-01T00:00:00.000Z"}]"""
    val client = fakeClient(json)
    val live   = new OneFrameLive[IO](config, client)
    val result = live.get(Rate.Pair(Currency.USD, Currency.JPY)).unsafeRunSync()
    result shouldBe a[Right[_, _]]
    result.map(_.price.value) shouldBe Right(BigDecimal("0.99"))
  }

}
