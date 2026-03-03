package forex.domain

/**
 * An immutable snapshot of an exchange rate at a specific point in time.
 *
 * Immutability is deliberate: a `Rate` value is fetched from One-Frame and stored in the cache;
 * it should never be mutated in place. Staleness is handled by replacing the entire cache map
 * on each refresh rather than updating individual entries.
 *
 * @param pair      the currency pair this rate applies to
 * @param price     the mid-price (average of bid and ask) as reported by One-Frame
 * @param timestamp the moment One-Frame computed this rate; used to detect stale data if needed
 */
case class Rate(
    pair: Rate.Pair,
    price: Price,
    timestamp: Timestamp
)

object Rate {

  /**
   * A type-safe, ordered currency pair.
   *
   * Using a dedicated `final case class` rather than a raw `(Currency, Currency)` tuple avoids
   * accidental confusion between `(from, to)` and `(to, from)` at call sites, and allows the
   * pair to be used as a `Map` key with structural equality (case class `equals`/`hashCode`).
   *
   * Nesting inside `Rate` keeps the domain model cohesive: a `Pair` only makes sense
   * in the context of a `Rate`.
   *
   * @param from the currency being converted from (the base currency)
   * @param to   the currency being converted to (the quote currency)
   */
  final case class Pair(
      from: Currency,
      to: Currency
  )
}
