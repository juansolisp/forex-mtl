package forex.services.rates.interpreters

import java.time.{ Instant, LocalDate, ZoneOffset }

import cats.effect.{ Concurrent, Sync, Timer }
import cats.effect.concurrent.Ref
import cats.syntax.applicativeError._
import cats.syntax.flatMap._
import cats.syntax.functor._
import forex.domain._
import forex.services.events.EventBus
import forex.services.rates.Algebra
import forex.services.rates.errors._
import fs2.Stream
import fs2.concurrent.SignallingRef
import org.slf4j.LoggerFactory

import scala.concurrent.duration.FiniteDuration

/** How many successful One-Frame calls have been made today (UTC day). */
final case class QuotaState(callsToday: Int, date: LocalDate) {
  val dailyLimit: Int    = 1000
  val softLimit: Int     = (dailyLimit * 0.8).toInt   // 800
  val quotaWarning: Boolean = callsToday >= softLimit

  /** Roll to a fresh day if needed, then increment the counter. */
  def increment: QuotaState = {
    val today = LocalDate.now(ZoneOffset.UTC)
    val base  = if (date != today) QuotaState(0, today) else this
    base.copy(callsToday = base.callsToday + 1)
  }
}

/**
 * An in-memory cache of all 72 currency pair rates, backed by [[OneFrameLive]].
 *
 * == Motivation ==
 * One-Frame enforces a 1 000 API calls/day limit. Naively forwarding each incoming request
 * to One-Frame would exhaust this budget within minutes under any real load. Instead, the
 * cache proactively fetches all 72 pairs in a single request every 4 minutes (360 calls/day)
 * and serves all individual `get` calls from memory with zero latency and zero quota cost.
 *
 * == Thread Safety ==
 * `Ref[F, Map[Rate.Pair, Rate]]` is cats-effect's lock-free atomic reference — reads and
 * writes are non-blocking and safe under concurrent access from multiple http4s fibers.
 * There is no need for explicit locking or synchronisation.
 *
 * == Lifecycle ==
 * The `refresh` stream is public and must be merged into the application stream in
 * [[forex.Main]]. If it is not run, the cache remains empty and all `get` calls return `Left`.
 *
 * @param live            the underlying HTTP client used only during refresh cycles
 * @param ref             the shared mutable cell holding the current cache state
 * @param refreshInterval how long to wait between successive batch fetches
 * @param eventBus        bus to publish [[LogEvent.CacheRefresh]] events after each successful refresh
 */
class OneFrameCache[F[_]: Concurrent: Timer](
    live: OneFrameLive[F],
    ref: Ref[F, Map[Rate.Pair, Rate]],
    intervalRef: SignallingRef[F, FiniteDuration],
    lastRefreshedAtRef: Ref[F, Option[Instant]],
    quotaRef: Ref[F, QuotaState],
    eventBus: EventBus[F]
) extends Algebra[F] {

  private val logger = LoggerFactory.getLogger(getClass)

  // Enumerate all 72 ordered pairs: 9 currencies × 8 others (self-pairs excluded).
  // Computed once at construction time and reused on every refresh cycle.
  private val allPairs: List[Rate.Pair] =
    for {
      from <- Currency.values
      to   <- Currency.values
      if from != to
    } yield Rate.Pair(from, to)

  /**
   * Look up a rate from the in-memory map. O(1), no HTTP call.
   * Returns `Left` if the cache has never been populated or the pair was absent from
   * the last One-Frame response.
   */
  override def get(pair: Rate.Pair): F[Error Either Rate] =
    ref.get.map { cache =>
      cache.get(pair).toRight(Error.OneFrameLookupFailed(s"Rate for $pair not in cache"))
    }

  /**
   * An fs2 `Stream` that keeps the cache up to date.
   *
   * Structure: `Stream.eval(doRefresh)` runs the initial fetch immediately on startup
   * (before the HTTP server starts accepting requests in [[forex.Main]]), ensuring the cache
   * is warm. The `++` then appends a periodic stream that re-fetches every `refreshInterval`.
   *
   * This stream must be merged (not sequenced) with the server stream so both run
   * concurrently for the lifetime of the application.
   */
  /** Update the refresh interval at runtime. Interrupts the current sleep immediately. */
  def setInterval(d: FiniteDuration): F[Unit] = intervalRef.set(d)

  /** Current interval (for reporting in the config endpoint response). */
  def getInterval: F[FiniteDuration] = intervalRef.get

  /** Timestamp of the last successful cache refresh, or None if it hasn't run yet. */
  def getLastRefreshedAt: F[Option[Instant]] = lastRefreshedAtRef.get

  /** Current One-Frame quota consumption for today (UTC). */
  def getQuota: F[QuotaState] = quotaRef.get

  /** Trigger an immediate cache refresh outside the normal schedule. */
  def forceRefresh: F[Unit] = doRefresh

  /**
   * Refresh stream that reacts to interval changes immediately.
   *
   * After each refresh, we race the current sleep against the `intervalRef.discrete` signal.
   * `discrete` emits whenever `setInterval` is called. If the signal fires before the sleep
   * completes, the sleep is cancelled and a new refresh runs right away — effectively
   * restarting the countdown from zero with the new interval.
   */
  val refresh: Stream[F, Unit] =
    Stream.eval(doRefresh) ++
      Stream.repeatEval {
        val currentSleep: F[Unit] =
          intervalRef.get.flatMap(d => Timer[F].sleep(d))

        // Race the sleep against the next interval-change signal.
        // - Left  (sleep won): interval did not change, proceed normally.
        // - Right (signal won): setInterval was called mid-sleep; refresh immediately.
        val interruptibleSleep: F[Unit] =
          Concurrent[F].race(
            currentSleep,
            intervalRef.discrete.drop(1).head.compile.drain
          ).void

        interruptibleSleep >> doRefresh
      }

  private def doRefresh: F[Unit] = {
    val startNs = System.nanoTime()
    live
      .fetchAll(allPairs)
      .flatMap {
        case Right(rates) =>
          val newCache   = rates.map(r => r.pair -> r).toMap
          val durationMs = (System.nanoTime() - startNs) / 1_000_000.0
          val now        = Instant.now()
          val timestamp  = now.toString
          // Atomically replace the entire map so readers never observe a half-populated cache.
          ref.set(newCache) >>
            lastRefreshedAtRef.set(Some(now)) >>
            // Increment today's One-Frame call counter and capture the new state for the SSE event.
            quotaRef.updateAndGet(_.increment).flatMap { quota =>
              eventBus.publish(LogEvent.CacheRefresh(
                pairsCount   = newCache.size,
                durationMs   = durationMs,
                timestamp    = timestamp,
                callsToday   = quota.callsToday,
                dailyLimit   = quota.dailyLimit,
                quotaWarning = quota.quotaWarning
              ))
            } >>
            Sync[F].delay(logger.info(s"Cache refreshed: ${newCache.size} pairs"))
        case Left(err) =>
          // Log the error but do NOT fail the stream. The old cache entries remain valid
          // and will continue to be served until the next successful refresh.
          val reason = err.toString
          Sync[F].delay(logger.error(s"Cache refresh failed: $reason")) >>
            eventBus.publish(LogEvent.CacheRefreshFailed(reason, Instant.now().toString))
      }
      // Guard against unexpected exceptions so the refresh stream never crashes.
      .handleErrorWith { e =>
        val reason = Option(e.getMessage).getOrElse(e.getClass.getSimpleName)
        Sync[F].delay(logger.error(s"Cache refresh threw: $reason")) >>
          eventBus.publish(LogEvent.CacheRefreshFailed(reason, Instant.now().toString))
      }
  }

}

object OneFrameCache {

  /**
   * Effectful constructor: allocates the `Ref` (requires `F`) and returns the cache
   * together with its refresh stream.
   *
   * The caller (currently [[forex.services.rates.Interpreters.cachedLive]]) receives both
   * and is responsible for running the stream alongside the HTTP server.
   */
  def create[F[_]: Concurrent: Timer](
      live: OneFrameLive[F],
      refreshInterval: FiniteDuration,
      eventBus: EventBus[F]
  ): F[(OneFrameCache[F], Stream[F, Unit])] =
    for {
      ref                <- Ref.of[F, Map[Rate.Pair, Rate]](Map.empty)
      intervalRef        <- SignallingRef[F, FiniteDuration](refreshInterval)
      lastRefreshedAtRef <- Ref.of[F, Option[Instant]](None)
      quotaRef           <- Ref.of[F, QuotaState](QuotaState(0, LocalDate.now(ZoneOffset.UTC)))
      cache               = new OneFrameCache[F](live, ref, intervalRef, lastRefreshedAtRef, quotaRef, eventBus)
    } yield (cache, cache.refresh)

}
