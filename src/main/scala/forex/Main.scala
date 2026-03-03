package forex

import scala.concurrent.ExecutionContext
import cats.effect._
import forex.config._
import forex.services.RatesServices
import forex.services.auth.AuthService
import forex.services.events.EventBus
import fs2.Stream
import org.http4s.blaze.client.BlazeClientBuilder
import org.http4s.blaze.server.BlazeServerBuilder

object Main extends IOApp {

  override def run(args: List[String]): IO[ExitCode] =
    new Application[IO].stream(executionContext).compile.drain.as(ExitCode.Success)

}

/**
 * Application wiring expressed as a single fs2 `Stream`.
 *
 * Defined as a class (not a singleton object) so that:
 *  - It can be parameterised over any `F[_]` satisfying `ConcurrentEffect` and `Timer`
 *  - Tests can instantiate it with a test-friendly effect type without `IOApp` machinery
 *
 * The `stream` method composes config loading, HTTP client lifecycle, event bus creation,
 * cache initialisation, and the HTTP server into one merged stream. When any component
 * fails or completes, the entire merged stream terminates, ensuring clean shutdown.
 */
class Application[F[_]: ConcurrentEffect: Timer] {

  def stream(ec: ExecutionContext): Stream[F, Unit] =
    for {
      // Load application.conf under the "app" key. Fails fast at startup if config is invalid.
      config <- Config.stream("app")

      // BlazeClientBuilder manages the HTTP connection pool as a cats `Resource`.
      // `Stream.resource(...)` lifts the Resource into the stream so the pool is acquired
      // before any requests are made and released when the stream terminates.
      httpClient <- Stream.resource(BlazeClientBuilder[F](ec).resource)

      // Create the SSE event bus — must be alive before any publisher or subscriber starts.
      eventBus <- Stream.eval(EventBus.create[F])

      // Create the in-memory auth service (session tokens stored in a Ref[F, Set[String]]).
      authService <- Stream.eval(AuthService.create[F](config.auth))

      // `cachedLive` returns (service, refreshStream) inside F — `.eval` runs that effect.
      // The service reads from an in-memory Ref; the refreshStream must be run concurrently
      // to populate and refresh that Ref from One-Frame.
      (cache, cacheRefresh) <- Stream.eval(
                                 RatesServices.cachedLive[F](config.oneFrame, httpClient, eventBus)
                               )

      module = new Module[F](config, authService, cache, cache, eventBus)

      // `merge` runs `cacheRefresh` and the HTTP server stream concurrently.
      // Both are infinite streams — if either ends or raises an unhandled error,
      // the merged stream terminates, cleanly shutting down both components.
      // `.serve` emits `ExitCode` values; `.drain` discards them.
      _ <- cacheRefresh.merge(
             BlazeServerBuilder[F](ec)
               .bindHttp(config.http.port, config.http.host)
               .withHttpApp(module.httpApp)
               .serve
               .drain
           )
    } yield ()

}
