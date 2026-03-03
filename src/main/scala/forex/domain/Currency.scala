package forex.domain

import cats.Show

/**
 * Enumeration of all currencies supported by the One-Frame API.
 *
 * The set is intentionally closed (sealed trait + case objects) for two reasons:
 *  1. One-Frame only accepts these 9 currencies; any other value is an API error.
 *  2. The compiler can verify pattern matches are complete, preventing silent runtime gaps.
 *
 * Adding a new currency requires updating `values` and `fromString` here, then recompiling —
 * the compiler warnings will highlight every match site that needs updating.
 */
sealed trait Currency

object Currency {
  case object AUD extends Currency
  case object CAD extends Currency
  case object CHF extends Currency
  case object EUR extends Currency
  case object GBP extends Currency
  case object NZD extends Currency
  case object JPY extends Currency
  case object SGD extends Currency
  case object USD extends Currency

  /**
   * Complete list of all currencies, used by [[forex.services.rates.interpreters.OneFrameCache]]
   * to enumerate all 72 trading pairs (9 × 8, excluding self-pairs) for the batch refresh request.
   * Keeping this as a `val` rather than computing it via reflection ensures the order is stable
   * and the set is explicitly controlled.
   */
  val values: List[Currency] = List(AUD, CAD, CHF, EUR, GBP, NZD, JPY, SGD, USD)

  /**
   * Canonical string serialisation for a [[Currency]].
   *
   * This instance is used in two places:
   *  - Building the One-Frame query string: `pair=USDJPY` (concatenation of two `show` results)
   *  - JSON-encoding currency values in the HTTP API response
   *
   * The representation matches One-Frame's own convention (three-letter ISO 4217 uppercase codes),
   * so `show` and `fromString` are mutual inverses for all valid currencies.
   */
  implicit val show: Show[Currency] = Show.show {
    case AUD => "AUD"
    case CAD => "CAD"
    case CHF => "CHF"
    case EUR => "EUR"
    case GBP => "GBP"
    case NZD => "NZD"
    case JPY => "JPY"
    case SGD => "SGD"
    case USD => "USD"
  }

  /**
   * Safely parse a currency code from a string.
   *
   * Returns `Right(currency)` on success or `Left(errorMessage)` on failure.
   * The `Either` return type (rather than throwing or returning `Option`) was chosen so that
   * callers can propagate the error message to the client — `QueryParamDecoder` uses `.emap`
   * which requires an `Either[ParseFailure, A]`, and the Left message becomes the 400 body.
   *
   * The match is case-insensitive (`toUpperCase`) so `"usd"`, `"USD"`, and `"Usd"` all parse
   * correctly, making the HTTP API friendlier without relaxing domain invariants.
   */
  def fromString(s: String): Either[String, Currency] = s.toUpperCase match {
    case "AUD" => Right(AUD)
    case "CAD" => Right(CAD)
    case "CHF" => Right(CHF)
    case "EUR" => Right(EUR)
    case "GBP" => Right(GBP)
    case "NZD" => Right(NZD)
    case "JPY" => Right(JPY)
    case "SGD" => Right(SGD)
    case "USD" => Right(USD)
    case other => Left(s"Unknown currency: $other")
  }

}
