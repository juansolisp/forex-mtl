package forex.domain

import io.circe.Encoder
import io.circe.Json
import io.circe.generic.semiauto.deriveEncoder

/**
 * ADT of observable events published to the SSE bus and consumed by the browser.
 *
 * Two variants:
 *  - [[ProxyRequest]]  — one event per incoming GET /rates request
 *  - [[CacheRefresh]]  — one event per One-Frame batch fetch
 *
 * The discriminator field `"type"` is merged into the JSON so the browser
 * can switch on event type without a wrapper object.
 */
sealed trait LogEvent

object LogEvent {

  /**
   * Emitted by [[forex.http.rates.RatesHttpRoutes]] after every /rates response.
   *
   * @param id         short UUID prefix (8 chars) — also sent as `X-Request-ID` response header
   * @param from       source currency code
   * @param to         target currency code
   * @param status     HTTP response status code (200 or 500)
   * @param price      exchange rate returned to the client; None on error responses
   * @param errorBody  error message returned to the client; None on success
   * @param durationMs wall-clock time from request received to response sent
   * @param timestamp  ISO-8601 instant the request was processed
   */
  final case class ProxyRequest(
      id: String,
      from: String,
      to: String,
      status: Int,
      price: Option[BigDecimal],
      errorBody: Option[String],
      durationMs: Double,
      timestamp: String
  ) extends LogEvent

  /**
   * Emitted by [[forex.services.rates.interpreters.OneFrameCache]] after each successful
   * batch refresh from One-Frame.
   *
   * @param pairsCount number of currency pairs stored (72 under normal conditions)
   * @param durationMs wall-clock time for the One-Frame HTTP call
   * @param timestamp  ISO-8601 instant the refresh completed
   */
  final case class CacheRefresh(
      pairsCount: Int,
      durationMs: Double,
      timestamp: String,
      callsToday: Int,
      dailyLimit: Int,
      quotaWarning: Boolean   // true when callsToday >= 80% of dailyLimit
  ) extends LogEvent

  /**
   * Emitted by [[forex.services.rates.interpreters.OneFrameCache]] when a refresh cycle
   * fails — either a typed error from One-Frame (e.g. quota exceeded) or an unexpected
   * exception. Streaming failures to the browser makes them visible without tailing logs.
   *
   * @param reason  human-readable error description
   * @param timestamp ISO-8601 instant the failure was observed
   */
  final case class CacheRefreshFailed(
      reason: String,
      timestamp: String
  ) extends LogEvent

  /**
   * Emitted by [[forex.http.events.EventsHttpRoutes]] every 30 seconds on each open SSE
   * connection. Serves two purposes:
   *
   * 1. **Keep-alive**: prevents proxies and NAT tables from closing idle connections
   *    during quiet periods (no requests, waiting for the next cache refresh).
   *
   * 2. **Clock sync**: carries the server's current epoch milliseconds alongside the
   *    last-refresh timestamp. The browser computes `clockOffsetMs = serverTimeMs - Date.now()`
   *    and applies that offset to all elapsed-time calculations, eliminating the
   *    server/browser clock-skew problem without requiring NTP access from JavaScript.
   *
   * @param serverTimeMs     server's `System.currentTimeMillis()` at the moment of emission
   * @param lastRefreshedAt  ISO-8601 timestamp of the last successful cache refresh, or null
   *                         if the cache has never been populated (e.g. cold start with
   *                         One-Frame unreachable)
   */
  final case class Heartbeat(
      serverTimeMs: Long,
      lastRefreshedAt: Option[String]
  ) extends LogEvent

  implicit val proxyRequestEncoder: Encoder[ProxyRequest]             = deriveEncoder[ProxyRequest]
  implicit val cacheRefreshEncoder: Encoder[CacheRefresh]             = deriveEncoder[CacheRefresh]
  implicit val cacheRefreshFailedEncoder: Encoder[CacheRefreshFailed] = deriveEncoder[CacheRefreshFailed]
  implicit val heartbeatEncoder: Encoder[Heartbeat]                   = deriveEncoder[Heartbeat]

  // Flat JSON with a "type" discriminator field so the browser can switch without nesting:
  // {"type":"ProxyRequest","id":"a3f9bc12","from":"USD","to":"JPY","status":200,...}
  implicit val logEventEncoder: Encoder[LogEvent] = Encoder.instance {
    case e: ProxyRequest =>
      proxyRequestEncoder(e).deepMerge(Json.obj("type" -> Json.fromString("ProxyRequest")))
    case e: CacheRefresh =>
      cacheRefreshEncoder(e).deepMerge(Json.obj("type" -> Json.fromString("CacheRefresh")))
    case e: CacheRefreshFailed =>
      cacheRefreshFailedEncoder(e).deepMerge(Json.obj("type" -> Json.fromString("CacheRefreshFailed")))
    case e: Heartbeat =>
      heartbeatEncoder(e).deepMerge(Json.obj("type" -> Json.fromString("Heartbeat")))
  }
}
