package forex.domain

/**
 * A wrapper around a monetary price value.
 *
 * Extends `AnyVal` for a zero-cost abstraction: the JVM erases the wrapper at runtime,
 * so there is no object allocation overhead while still giving the type system a distinct
 * type that cannot be confused with other `BigDecimal` fields (e.g., timestamps or IDs).
 *
 * `BigDecimal` is used rather than `Double` or `Float` to avoid floating-point rounding
 * errors that are unacceptable in financial calculations.
 */
case class Price(value: BigDecimal) extends AnyVal

object Price {
  /**
   * Convenience constructor accepting a Java `Integer`.
   * Kept from the original scaffold primarily for test convenience — tests can write
   * `Price(100)` rather than `Price(BigDecimal(100))` without importing BigDecimal implicits.
   */
  def apply(value: Integer): Price =
    Price(BigDecimal(value))
}
