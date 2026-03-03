package forex.http
package config

import cats.effect.Concurrent
import cats.syntax.flatMap._
import forex.services.rates.interpreters.OneFrameCache
import io.circe.generic.semiauto._
import io.circe.{ Decoder, Encoder }
import org.http4s.HttpRoutes
import org.http4s.circe.CirceEntityCodec._
import org.http4s.dsl.Http4sDsl
import org.http4s.server.Router

import scala.concurrent.duration._

/**
 * PUT /config/refresh-interval  — change the cache refresh interval at runtime.
 * GET /config/refresh-interval  — read the current interval.
 *
 * The change takes effect immediately: the current sleep is interrupted and a fresh
 * cache fetch runs right away. The interval is validated to the range
 * [90s, 300s] — below 90s risks One-Frame rate limits; above 300s would breach
 * the 5-minute freshness SLA.
 */
class ConfigHttpRoutes[F[_]: Concurrent](cache: OneFrameCache[F]) extends Http4sDsl[F] {

  private[config] val prefixPath = "/config"

  private case class IntervalRequest(seconds: Int)
  private case class IntervalResponse(seconds: Long, message: String)
  private case class RefreshResponse(message: String, pairsCount: Int)
  private case class StatusResponse(
      intervalSeconds: Long,
      lastRefreshedAt: Option[String],
      callsToday: Int,
      dailyLimit: Int,
      quotaWarning: Boolean
  )

  private implicit val intervalReqDecoder: Decoder[IntervalRequest]                = deriveDecoder
  private implicit val intervalResEncoder: Encoder[IntervalResponse]               = deriveEncoder
  private implicit val refreshResEncoder: Encoder[RefreshResponse]                 = deriveEncoder
  @annotation.unused private implicit val statusResEncoder: Encoder[StatusResponse] = deriveEncoder

  private val MinSeconds = 90
  private val MaxSeconds = 300

  private val httpRoutes: HttpRoutes[F] = HttpRoutes.of[F] {

    case GET -> Root / "status" =>
      cache.getInterval.flatMap { interval =>
        cache.getLastRefreshedAt.flatMap { lastRefreshedAt =>
          cache.getQuota.flatMap { quota =>
            Ok(StatusResponse(
              intervalSeconds = interval.toSeconds,
              lastRefreshedAt = lastRefreshedAt.map(_.toString),
              callsToday      = quota.callsToday,
              dailyLimit      = quota.dailyLimit,
              quotaWarning    = quota.quotaWarning
            ))
          }
        }
      }

    case GET -> Root / "refresh-interval" =>
      cache.getInterval.flatMap { current =>
        Ok(IntervalResponse(current.toSeconds, s"current refresh interval is ${current.toSeconds}s"))
      }

    case req @ PUT -> Root / "refresh-interval" =>
      req.as[IntervalRequest].flatMap { body =>
        if (body.seconds < MinSeconds || body.seconds > MaxSeconds) {
          BadRequest(IntervalResponse(
            body.seconds.toLong,
            s"interval must be between ${MinSeconds}s and ${MaxSeconds}s"
          ))
        } else {
          val newInterval = body.seconds.seconds
          // setInterval signals the background fiber to interrupt its current sleep.
          // forceRefresh runs doRefresh directly and completes before we return 200,
          // so the CacheRefresh SSE event is guaranteed to arrive before the frontend
          // processes the PUT response. This eliminates the race window where setInterval
          // fires while the background fiber is already executing doRefresh (and therefore
          // not yet listening on intervalRef.discrete), which would otherwise cause the
          // immediate re-refresh to be silently skipped.
          cache.setInterval(newInterval) >> cache.forceRefresh >>
            Ok(IntervalResponse(
              newInterval.toSeconds,
              s"refresh interval updated to ${newInterval.toSeconds}s — refreshed immediately"
            ))
        }
      }

    // Immediately triggers a cache refresh outside the normal schedule.
    // Responds only after the refresh completes so the client knows the cache is fresh.
    case POST -> Root / "force-refresh" =>
      cache.forceRefresh >>
        Ok(RefreshResponse("cache refreshed", 72))
  }

  val routes: HttpRoutes[F] = Router(prefixPath -> httpRoutes)

}
