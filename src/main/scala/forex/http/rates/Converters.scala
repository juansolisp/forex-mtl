package forex.http.rates

import forex.domain._

object Converters {
  import Protocol._

  /**
   * Extension method that converts a domain [[Rate]] into the HTTP API response type.
   *
   * Implemented as an `AnyVal` extension class for zero-cost wrapping — no object is allocated
   * at runtime. Scoped to `private[rates]` so it is visible within the `rates` HTTP package
   * (used in [[RatesHttpRoutes]]) but not leaked to other packages.
   *
   * The conversion flattens `rate.pair.from / rate.pair.to` into top-level `from` / `to`
   * fields, matching the flat response shape defined in [[Protocol.GetApiResponse]].
   */
  private[rates] implicit class GetApiResponseOps(val rate: Rate) extends AnyVal {
    def asGetApiResponse: GetApiResponse =
      GetApiResponse(
        from = rate.pair.from,
        to = rate.pair.to,
        price = rate.price,
        timestamp = rate.timestamp
      )
  }

}
