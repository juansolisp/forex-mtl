package forex.services.rates

import forex.domain.Rate
import errors._

/**
 * Abstract algebra (interface) for the rates service layer.
 *
 * Defined as a trait parameterised over an effect type `F[_]` rather than a concrete `IO`
 * so that:
 *  - Tests can substitute `cats.Id` (synchronous, no runtime needed) or a mock `F`
 *  - The algebra can be composed with other algebras in tagless-final style
 *  - The production interpreter (`OneFrameCache`) and the test stub (`OneFrameDummy`)
 *    both satisfy the same contract without sharing any implementation
 *
 * The `Either` in the return type makes error handling explicit at the type level:
 * callers must handle both the success and failure cases rather than catching exceptions.
 */
trait Algebra[F[_]] {

  /**
   * Retrieve the current exchange rate for the given currency pair.
   *
   * @param pair  the source and target currency
   * @return      `Right(rate)` if the rate is available, or `Left(error)` if the upstream
   *              service is unreachable or the pair is not in the cache
   */
  def get(pair: Rate.Pair): F[Error Either Rate]
}
