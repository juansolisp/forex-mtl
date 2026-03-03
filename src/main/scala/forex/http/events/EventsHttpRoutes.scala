package forex.http
package events

import cats.effect.{ Concurrent, Timer }
import cats.syntax.functor._
import forex.domain.LogEvent
import forex.services.events.EventBus
import forex.services.rates.interpreters.OneFrameCache
import io.circe.syntax._
import org.http4s.HttpRoutes
import org.http4s.MediaType
import org.http4s.ServerSentEvent
import org.http4s.dsl.Http4sDsl
import org.http4s.headers.`Content-Type`
import org.http4s.server.Router

import scala.concurrent.duration._

/**
 * GET /events — Server-Sent Events endpoint.
 *
 * Each SSE frame contains the JSON-encoded [[LogEvent]] in its `data` field.
 * Four event types are emitted:
 *  - [[LogEvent.ProxyRequest]]       — for every /rates request handled
 *  - [[LogEvent.CacheRefresh]]       — after each One-Frame batch fetch
 *  - [[LogEvent.CacheRefreshFailed]] — when a refresh attempt fails
 *  - [[LogEvent.Heartbeat]]          — every 30 seconds per open connection (see below)
 *
 * == Heartbeat Design ==
 * The heartbeat solves two independent problems:
 *
 * 1. **Proxy / NAT keepalive**: Nginx (and many corporate proxies) close idle HTTP connections
 *    after 60 seconds of silence. A cache refresh only happens every 4 minutes, so without a
 *    heartbeat the SSE connection is silently killed between refreshes. We set
 *    `proxy_read_timeout 600s` in Nginx, and emit a heartbeat every 30 seconds so even
 *    reduced timeouts on third-party proxies are unlikely to trigger.
 *
 * 2. **Clock skew correction**: The browser's `Date.now()` and the server's
 *    `System.currentTimeMillis()` can diverge — especially on VMs and CI containers. The
 *    `Heartbeat` carries the server's epoch-ms at emission time. The browser computes
 *    `clockOffsetMs = serverTimeMs - Date.now()` and adds that offset to all
 *    elapsed-time calculations, eliminating the skew without NTP access from JavaScript.
 *
 * == Stream topology ==
 * Each SSE connection gets its own heartbeat stream merged with the shared event bus stream:
 * {{{
 *   eventBus.subscribe  ─┐
 *                         ├─ merge ─→ SSE bytes
 *   heartbeatStream    ─┘
 * }}}
 * The heartbeat stream is connection-local (not published to the bus) because it carries
 * `System.currentTimeMillis()` at emit time — publishing it would race with consumption
 * and the timestamp would be stale by the time other connections received it.
 *
 * `Concurrent` (not merely `Sync`) is required because subscribing to an fs2 `Topic`
 * involves concurrent state in the underlying `PubSub` structure. `Timer` is required
 * for `Stream.fixedDelay`.
 *
 * The `Content-Type` header is set explicitly to `text/event-stream` — without it, http4s
 * would infer `application/octet-stream` from the raw byte stream, and browsers would not
 * treat the response as SSE.
 */
class EventsHttpRoutes[F[_]: Concurrent: Timer](eventBus: EventBus[F], cache: OneFrameCache[F])
    extends Http4sDsl[F] {

  private[events] val prefixPath = "/events"

  private val httpRoutes: HttpRoutes[F] = HttpRoutes.of[F] {
    case GET -> Root =>
      // Shared bus stream: CacheRefresh, ProxyRequest, CacheRefreshFailed events.
      val busStream = eventBus.subscribe.map { event =>
        ServerSentEvent(data = Some(event.asJson.noSpaces))
      }

      // Per-connection heartbeat stream: emits immediately, then every 30 seconds.
      // Reads lastRefreshedAt from the cache ref on each emission so it reflects the
      // most recent successful refresh (or null on cold start).
      val heartbeatStream =
        fs2.Stream.repeatEval {
          cache.getLastRefreshedAt.map { lastRefreshedAt =>
            val event: LogEvent = LogEvent.Heartbeat(
              serverTimeMs    = System.currentTimeMillis(),
              lastRefreshedAt = lastRefreshedAt.map(_.toString)
            )
            ServerSentEvent(data = Some(event.asJson.noSpaces))
          }
        }.metered(30.seconds)

      // Merge: both streams run concurrently for the lifetime of this connection.
      // `ServerSentEvent.encoder` formats each event as `data: …\n\n` wire bytes.
      val sseStream = busStream.merge(heartbeatStream)

      Ok(sseStream.through(ServerSentEvent.encoder[F]), `Content-Type`(MediaType.`text/event-stream`))
  }

  val routes: HttpRoutes[F] = Router(prefixPath -> httpRoutes)

}
