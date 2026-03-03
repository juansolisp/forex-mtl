package forex.services.rates

import cats.Applicative
import cats.effect.{ Concurrent, Timer }
import forex.config.OneFrameConfig
import forex.services.events.EventBus
import fs2.Stream
import interpreters._
import org.http4s.client.Client

/**
 * Factory object for all [[Algebra]] implementations.
 *
 * Centralising construction here means callers (currently only [[forex.Main]]) import a single
 * object and never reference concrete interpreter classes directly, keeping the wiring
 * independent of implementation details.
 */
object Interpreters {

  /**
   * A no-op stub that always returns `Price(100)` without making any HTTP calls.
   * Useful during early development before One-Frame is available, and in unit tests
   * that need a trivially working service.
   * Requires only `Applicative` — no concurrency or I/O needed.
   */
  def dummy[F[_]: Applicative]: Algebra[F] = new OneFrameDummy[F]()

  /**
   * A live interpreter that calls One-Frame directly for every `get` invocation.
   * Not used in production (the cache is used instead) but exposed here for:
   *  - Integration tests that bypass the cache
   *  - Composition with `cachedLive` below
   */
  def live[F[_]: Concurrent](
      config: OneFrameConfig,
      httpClient: Client[F]
  ): OneFrameLive[F] =
    new OneFrameLive[F](config, httpClient)

  /**
   * The production interpreter: a cache-backed service that satisfies the 1 000 calls/day limit.
   *
   * Returns both:
   *  - the `Algebra[F]` service (backed by an in-memory `Ref` map — pure reads, no HTTP)
   *  - a `Stream[F, Unit]` that must be run concurrently with the HTTP server to populate
   *    and periodically refresh the cache (see [[forex.Main]] for the merge pattern)
   *
   * @param eventBus the SSE event bus — cache refresh events are published here
   */
  /**
   * Returns the concrete `OneFrameCache` (not just `Algebra`) so the caller can also
   * call `setInterval` to change the refresh rate at runtime via the config endpoint.
   */
  def cachedLive[F[_]: Concurrent: Timer](
      config: OneFrameConfig,
      httpClient: Client[F],
      eventBus: EventBus[F]
  ): F[(OneFrameCache[F], Stream[F, Unit])] =
    OneFrameCache.create[F](live(config, httpClient), config.refreshInterval, eventBus)

}
