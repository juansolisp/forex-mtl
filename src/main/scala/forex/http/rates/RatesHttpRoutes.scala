package forex.http
package rates

import cats.effect.Sync
import cats.syntax.flatMap._
import cats.syntax.functor._
import cats.syntax.show._
import forex.domain.LogEvent
import forex.programs.RatesProgram
import forex.programs.rates.{ Protocol => RatesProgramProtocol }
import forex.services.events.EventBus
import org.http4s.Header
import org.http4s.HttpRoutes
import org.http4s.dsl.Http4sDsl
import org.http4s.server.Router
import org.typelevel.ci.CIString

/**
 * HTTP routes for the `/rates` endpoint.
 *
 * Handles request validation, delegates to the program layer, and maps results to HTTP responses.
 * Also generates a short `X-Request-ID` for every proxied request, returns it as a response
 * header, and publishes a [[LogEvent.ProxyRequest]] to the SSE bus so connected browsers can
 * observe every request in real time.
 *
 * `Sync` is sufficient (vs. `Concurrent`) because the route only sequences effects linearly:
 * decode params → call program → publish event → encode response.
 */
class RatesHttpRoutes[F[_]: Sync](rates: RatesProgram[F], eventBus: EventBus[F])
    extends Http4sDsl[F] {

  import Converters._, QueryParams._, Protocol._

  private[http] val prefixPath = "/rates"

  private val httpRoutes: HttpRoutes[F] = HttpRoutes.of[F] {
    // `+&` sequences two query parameter extractors. Each yields
    // `Option[ValidatedNel[ParseFailure, Currency]]` (None = absent, Some(Invalid) = bad value).
    // `requireParam` converts None to Invalid so both missing and malformed params produce 400.
    case GET -> Root :? FromQueryParam(optFrom) +& ToQueryParam(optTo) =>
      val validFrom = requireParam("from")(optFrom)
      val validTo   = requireParam("to")(optTo)
      (validFrom.toEither, validTo.toEither) match {

        case (Right(from), Right(to)) if from == to =>
          val requestId = java.util.UUID.randomUUID().toString.take(8)
          val errMsg    = s"'from' and 'to' must be different currencies (got: ${from.show} / ${to.show})"
          // Duration is 0 — rejection is pure (no cache lookup, no I/O).
          BadRequest(errMsg).flatMap { resp =>
            eventBus
              .publish(LogEvent.ProxyRequest(requestId, from.show, to.show, 400, None, Some(errMsg), 0.0, java.time.Instant.now().toString))
              .as(resp.putHeaders(Header.Raw(CIString("X-Request-ID"), requestId)))
          }

        case (Right(from), Right(to)) =>
          // Generate a short ID for this request — first 8 chars of a UUID.
          // Returned as X-Request-ID response header and included in the SSE log event.
          val requestId = java.util.UUID.randomUUID().toString.take(8)
          // nanoTime gives sub-millisecond resolution. currentTimeMillis() has only
          // ~1ms granularity and returns 0 for cache hits that complete in <1ms.
          val startNs = System.nanoTime()

          rates.get(RatesProgramProtocol.GetRatesRequest(from, to)).flatMap {
            case Right(rate) =>
              val durationMs = (System.nanoTime() - startNs) / 1_000_000.0
              val apiResponse = rate.asGetApiResponse
              Ok(apiResponse).flatMap { resp =>
                // price is included in the SSE event so the browser never has to correlate
                // the HTTP response body with the SSE frame — the event is fully self-contained.
                eventBus
                  .publish(LogEvent.ProxyRequest(requestId, from.show, to.show, 200, Some(rate.price.value), None, durationMs, java.time.Instant.now().toString))
                  .as(resp.putHeaders(Header.Raw(CIString("X-Request-ID"), requestId)))
              }

            case Left(err) =>
              val durationMs = (System.nanoTime() - startNs) / 1_000_000.0
              val errMsg = err.getMessage
              // The program error message is safe to expose: it originates from our own
              // `toProgramError` mapping and does not contain stacktraces or internal paths.
              InternalServerError(errMsg).flatMap { resp =>
                eventBus
                  .publish(LogEvent.ProxyRequest(requestId, from.show, to.show, 500, None, Some(errMsg), durationMs, java.time.Instant.now().toString))
                  .as(resp.putHeaders(Header.Raw(CIString("X-Request-ID"), requestId)))
              }
          }

        case _ =>
          // Collect all parse failures from both parameters.
          // `.swap` turns Valid into Invalid; `.toList` gives [] for Valid, [nel] for Invalid;
          // `.flatMap(_.toList)` flattens the NonEmptyList of failures.
          // `.sanitized` strips internal detail for safe external display.
          val errors    = validFrom.swap.toList ++ validTo.swap.toList
          val errMsg    = errors.flatMap(_.toList).map(_.sanitized).mkString(", ")
          val requestId = java.util.UUID.randomUUID().toString.take(8)
          // Use "?" for unknown currencies since parsing failed — we have no Currency values.
          BadRequest(errMsg).flatMap { resp =>
            eventBus
              .publish(LogEvent.ProxyRequest(requestId, "?", "?", 400, None, Some(errMsg), 0.0, java.time.Instant.now().toString))
              .as(resp.putHeaders(Header.Raw(CIString("X-Request-ID"), requestId)))
          }
      }
  }

  // `Router` mounts `httpRoutes` under `prefixPath` ("/rates").
  // The `AutoSlash` middleware in [[forex.Module]] normalises trailing slashes so
  // both `/rates?...` and `/rates/?...` are handled identically.
  val routes: HttpRoutes[F] = Router(
    prefixPath -> httpRoutes
  )

}
