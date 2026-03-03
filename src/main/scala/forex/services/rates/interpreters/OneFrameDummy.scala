package forex.services.rates.interpreters

import forex.services.rates.Algebra
import cats.Applicative
import cats.syntax.applicative._
import cats.syntax.either._
import forex.domain.{ Price, Rate, Timestamp }
import forex.services.rates.errors._

/**
 * A stub implementation of [[Algebra]] for development and testing.
 *
 * Always returns `Price(100)` with the current timestamp for any requested pair,
 * without making any network calls. This was the initial implementation used to verify
 * the HTTP routing and JSON serialisation layers before One-Frame integration was added.
 *
 * Requires only `Applicative` (not `Sync` or `Concurrent`) because the computation is
 * purely in-memory — `pure` lifts the value into `F` without any I/O.
 */
class OneFrameDummy[F[_]: Applicative] extends Algebra[F] {

  override def get(pair: Rate.Pair): F[Error Either Rate] =
    Rate(pair, Price(BigDecimal(100)), Timestamp.now).asRight[Error].pure[F]

}
