package forex.services.events

import cats.effect.Concurrent
import cats.syntax.functor._
import forex.domain.LogEvent
import fs2.Stream
import fs2.concurrent.Topic

/**
 * Fan-out pub/sub bus for [[LogEvent]]s, backed by an fs2 `Topic`.
 *
 * == Why `Option[LogEvent]`? ==
 * `Topic` in fs2 2.5 (CE2) requires an initial value that is immediately replayed to every
 * new subscriber. Using `None` as the sentinel means new subscribers receive one harmless
 * `None` before any real events; `subscribe` filters it out. This avoids needing a dummy
 * "real" event as the initial value.
 *
 * == Fan-out ==
 * Every subscriber (each connected SSE client) receives all events published after it subscribes.
 * Multiple browser tabs can connect simultaneously and each gets its own independent stream.
 *
 * == Back-pressure ==
 * Each subscriber buffer holds 128 events. At typical rates (one refresh per 4 minutes + a
 * few requests per second) this is generous. If a slow SSE client falls behind by more than
 * 128 events, its oldest undelivered events are dropped silently.
 */
trait EventBus[F[_]] {
  /** Publish an event to all current subscribers. Non-blocking, lock-free. */
  def publish(event: LogEvent): F[Unit]

  /** Subscribe to the stream of events. Each subscriber gets all future events. */
  def subscribe: Stream[F, LogEvent]
}

object EventBus {

  /**
   * Allocate a fresh `Topic` and return a live `EventBus`.
   * Must be called once during application startup, before any publisher or subscriber runs.
   */
  def create[F[_]: Concurrent]: F[EventBus[F]] =
    Topic[F, Option[LogEvent]](None).map { topic =>
      new EventBus[F] {
        def publish(event: LogEvent): F[Unit] =
          topic.publish1(Some(event))

        def subscribe: Stream[F, LogEvent] =
          topic.subscribe(128).collect { case Some(e) => e }
      }
    }
}
