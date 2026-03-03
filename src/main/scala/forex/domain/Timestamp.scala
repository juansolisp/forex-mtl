package forex.domain

import java.time.OffsetDateTime

/**
 * A wrapper around the instant at which an exchange rate was recorded.
 *
 * Extends `AnyVal` for zero-cost wrapping (no runtime allocation).
 *
 * `OffsetDateTime` is chosen over `Instant` or `LocalDateTime` because:
 *  - One-Frame returns timestamps with an explicit UTC offset (e.g. `"2021-01-01T00:00:00.000Z"`)
 *  - `OffsetDateTime.parse` handles this format directly without a custom formatter
 *  - The offset is preserved in the value and round-trips cleanly through JSON serialisation,
 *    so clients receive the same timezone information One-Frame provided
 */
case class Timestamp(value: OffsetDateTime) extends AnyVal

object Timestamp {
  /** Capture the current wall-clock time as a [[Timestamp]]. Used in stubs and tests. */
  def now: Timestamp =
    Timestamp(OffsetDateTime.now)
}
