package forex.programs.rates

import forex.domain.Rate
import errors._

/**
 * Abstract algebra for the rates program layer.
 *
 * This algebra is deliberately separate from [[forex.services.rates.Algebra]]:
 *  - It accepts a [[Protocol.GetRatesRequest]] (an HTTP-level input type) rather than a
 *    raw `Rate.Pair`, decoupling the HTTP layer from the service layer's domain types.
 *  - It returns [[errors.Error]] (a program-level error) rather than
 *    [[forex.services.rates.errors.Error]], so the HTTP routes never need to import
 *    service-layer internals. The translation happens once in [[Program]].
 *  - Future programs (e.g. a batch-quote endpoint) can implement this algebra without
 *    changing the service algebra.
 */
trait Algebra[F[_]] {
  def get(request: Protocol.GetRatesRequest): F[Error Either Rate]
}
