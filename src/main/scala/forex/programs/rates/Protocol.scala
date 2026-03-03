package forex.programs.rates

import forex.domain.Currency

object Protocol {

  /**
   * The program-level request type for a rate lookup.
   *
   * Deliberately kept separate from [[forex.domain.Rate.Pair]] even though both hold a
   * `(from, to)` pair of currencies. The separation serves two purposes:
   *  1. **Decoupling**: the HTTP layer constructs a `GetRatesRequest` from query parameters
   *     without needing to know that the domain models things as a `Rate.Pair`. If the
   *     request type gains new fields in the future (e.g., `amount`, `date`, `rounding`)
   *     the domain model stays unchanged.
   *  2. **Clarity**: at the call site `Program.get(request)` it is unambiguous that the
   *     argument is an HTTP-originating request, not an internal domain value.
   */
  final case class GetRatesRequest(
      from: Currency,
      to: Currency
  )

}
