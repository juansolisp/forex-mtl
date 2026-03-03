package forex.domain

import io.circe.syntax._
import io.circe.parser._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

/**
 * Unit tests for [[LogEvent]] JSON encoding.
 *
 * The browser's SSE handler switches on the flat `"type"` discriminator field to decide
 * which TypeScript interface to use.  These tests verify that the Circe encoder merges
 * the discriminator into the JSON object correctly for every variant — a regression here
 * would silently break the frontend log panel.
 */
class LogEventSpec extends AnyFunSuite with Matchers {

  test("ProxyRequest encodes with type = ProxyRequest") {
    val event: LogEvent = LogEvent.ProxyRequest(
      id         = "abc12345",
      from       = "USD",
      to         = "JPY",
      status     = 200,
      price      = Some(BigDecimal("0.71")),
      errorBody  = None,
      durationMs = 1.234,
      timestamp  = "2024-01-01T00:00:00Z"
    )
    val json = event.asJson
    json.hcursor.get[String]("type").toOption shouldBe Some("ProxyRequest")
    json.hcursor.get[String]("from").toOption shouldBe Some("USD")
    json.hcursor.get[String]("to").toOption   shouldBe Some("JPY")
    json.hcursor.get[Int]("status").toOption  shouldBe Some(200)
  }

  test("CacheRefresh encodes with type = CacheRefresh and quota fields") {
    val event: LogEvent = LogEvent.CacheRefresh(
      pairsCount   = 72,
      durationMs   = 150.0,
      timestamp    = "2024-01-01T00:00:00Z",
      callsToday   = 5,
      dailyLimit   = 1000,
      quotaWarning = false
    )
    val json = event.asJson
    json.hcursor.get[String]("type").toOption       shouldBe Some("CacheRefresh")
    json.hcursor.get[Int]("pairsCount").toOption    shouldBe Some(72)
    json.hcursor.get[Int]("callsToday").toOption    shouldBe Some(5)
    json.hcursor.get[Int]("dailyLimit").toOption    shouldBe Some(1000)
    json.hcursor.get[Boolean]("quotaWarning").toOption shouldBe Some(false)
  }

  test("CacheRefreshFailed encodes with type = CacheRefreshFailed") {
    val event: LogEvent = LogEvent.CacheRefreshFailed(
      reason    = "connection refused",
      timestamp = "2024-01-01T00:00:00Z"
    )
    val json = event.asJson
    json.hcursor.get[String]("type").toOption   shouldBe Some("CacheRefreshFailed")
    json.hcursor.get[String]("reason").toOption shouldBe Some("connection refused")
  }

  test("Heartbeat encodes with type = Heartbeat and serverTimeMs") {
    val event: LogEvent = LogEvent.Heartbeat(
      serverTimeMs    = 1704067200000L,
      lastRefreshedAt = Some("2024-01-01T00:00:00Z")
    )
    val json = event.asJson
    json.hcursor.get[String]("type").toOption        shouldBe Some("Heartbeat")
    json.hcursor.get[Long]("serverTimeMs").toOption  shouldBe Some(1704067200000L)
  }

  test("Heartbeat with no lastRefreshedAt encodes lastRefreshedAt as null") {
    val event: LogEvent = LogEvent.Heartbeat(serverTimeMs = 0L, lastRefreshedAt = None)
    val json = event.asJson
    json.hcursor.downField("lastRefreshedAt").focus.map(_.isNull) shouldBe Some(true)
  }

  test("type discriminator field is present in JSON output (no wrapper object)") {
    // The browser expects flat JSON like {"type":"ProxyRequest","from":"USD",...}
    // not nested like {"ProxyRequest":{"from":"USD",...}}.
    val event: LogEvent = LogEvent.CacheRefreshFailed("err", "2024-01-01T00:00:00Z")
    val jsonStr = event.asJson.noSpaces
    // Type field at top level, not nested
    jsonStr should include("\"type\":\"CacheRefreshFailed\"")
    jsonStr should include("\"reason\":\"err\"")
    jsonStr should not include "CacheRefreshFailed\":{" // no nesting
  }

  test("ProxyRequest with error encodes errorBody and null price") {
    val event: LogEvent = LogEvent.ProxyRequest(
      id         = "xyz",
      from       = "USD",
      to         = "USD",  // same-pair error
      status     = 400,
      price      = None,
      errorBody  = Some("'from' and 'to' must be different"),
      durationMs = 0.0,
      timestamp  = "2024-01-01T00:00:00Z"
    )
    val json = event.asJson
    json.hcursor.get[Int]("status").toOption       shouldBe Some(400)
    json.hcursor.downField("price").focus.map(_.isNull)     shouldBe Some(true)
    json.hcursor.downField("errorBody").as[Option[String]].toOption.flatten shouldBe Some("'from' and 'to' must be different")
  }

  test("round-trip: encoded JSON can be parsed back") {
    // Ensures the JSON is well-formed (no encoding errors).
    val event: LogEvent = LogEvent.CacheRefresh(72, 100.0, "2024-01-01T00:00:00Z", 3, 1000, false)
    val jsonStr = event.asJson.noSpaces
    parse(jsonStr).isRight shouldBe true
  }
}
