package forex

import cats.effect.{ Concurrent, Timer }
import cats.syntax.semigroupk._
import forex.config.ApplicationConfig
import forex.http.auth.AuthHttpRoutes
import forex.http.config.ConfigHttpRoutes
import forex.http.events.EventsHttpRoutes
import forex.http.rates.RatesHttpRoutes
import forex.services._
import forex.services.auth.AuthService
import forex.services.events.EventBus
import forex.services.rates.interpreters.OneFrameCache
import forex.programs._
import org.http4s._
import org.http4s.implicits._
import forex.http.AuthMiddleware
import org.http4s.server.middleware.{ AutoSlash, CORS, Timeout }

/**
 * Dependency-injection wiring for the HTTP server.
 *
 * Accepts already-constructed `ratesService`, `cache`, and `eventBus` rather than building
 * them internally, keeping this class pure (no `IO` or resource allocation) and testable.
 *
 * The wiring order is: service → program → routes → middleware → httpApp.
 * Each layer only knows about the layer immediately below it.
 */
class Module[F[_]: Concurrent: Timer](
    config: ApplicationConfig,
    authService: AuthService[F],
    ratesService: RatesService[F],
    cache: OneFrameCache[F],
    eventBus: EventBus[F]
) {

  // Auth routes are public — mounted outside AuthMiddleware so login/validate/logout
  // are reachable before a session token is available.
  private val authHttpRoutes: HttpRoutes[F] =
    CORS.policy.withAllowOriginAll(
      new AuthHttpRoutes[F](authService).routes
    )

  private val ratesProgram: RatesProgram[F] = RatesProgram[F](ratesService)

  private val ratesHttpRoutes: HttpRoutes[F] = new RatesHttpRoutes[F](ratesProgram, eventBus).routes

  // CORS applied only to SSE and config endpoints — the browser hits these directly.
  // The rates endpoint goes through the Vite proxy so it shares origin and needs no CORS.
  private val eventsHttpRoutes: HttpRoutes[F] =
    CORS.policy.withAllowOriginAll(
      new EventsHttpRoutes[F](eventBus, cache).routes
    )

  private val configHttpRoutes: HttpRoutes[F] =
    CORS.policy.withAllowOriginAll(
      new ConfigHttpRoutes[F](cache).routes
    )

  // Type aliases make the middleware signatures self-documenting.
  // PartialMiddleware transforms HttpRoutes (a partial function that may return 404).
  // TotalMiddleware transforms HttpApp (a total function that always returns a response).
  type PartialMiddleware = HttpRoutes[F] => HttpRoutes[F]
  type TotalMiddleware   = HttpApp[F] => HttpApp[F]

  private val routesMiddleware: PartialMiddleware = { http: HttpRoutes[F] =>
    // AutoSlash normalises trailing slashes so `/rates` and `/rates/` both match the same route.
    // AuthMiddleware rejects requests without the correct X-Proxy-Token header with 401.
    AuthMiddleware(config.proxyToken)(AutoSlash(http))
  }

  private val appMiddleware: TotalMiddleware = { http: HttpApp[F] =>
    // Timeout wraps the entire HttpApp and returns 503 if any handler exceeds the configured
    // duration, preventing slow upstream calls from holding threads indefinitely.
    Timeout(config.http.timeout)(http)
  }

  // Only rates requires X-Proxy-Token. SSE (EventSource can't send headers) and
  // config are public. Auth routes are always public.
  private val protectedRoutes: HttpRoutes[F] =
    routesMiddleware(ratesHttpRoutes)

  // Public routes tried first; protected rates last.
  val httpApp: HttpApp[F] = appMiddleware(
    (authHttpRoutes <+> eventsHttpRoutes <+> configHttpRoutes <+> protectedRoutes).orNotFound
  )

}
