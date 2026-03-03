package forex.http.rates

import cats.data.{ Validated, ValidatedNel }
import forex.domain.Currency
import org.http4s.QueryParamDecoder
import org.http4s.ParseFailure
import org.http4s.dsl.impl.OptionalValidatingQueryParamDecoderMatcher

object QueryParams {

  /**
   * A `QueryParamDecoder` that parses a query string value into a [[Currency]].
   *
   * `.emap` lifts `Currency.fromString`'s `Either` into `Either[ParseFailure, Currency]`,
   * which is the type http4s expects. When the Left branch is taken, http4s records the
   * `ParseFailure` and the route handler sees an `Invalid` result, enabling a clean 400
   * response rather than a 500 or unmatched route.
   */
  private[http] implicit val currencyQueryParam: QueryParamDecoder[Currency] =
    QueryParamDecoder[String].emap { s =>
      Currency.fromString(s).left.map(msg => ParseFailure(msg, msg))
    }

  /**
   * Extractor for the `from` query parameter.
   *
   * `OptionalValidatingQueryParamDecoderMatcher` is used (rather than the non-optional variant)
   * because it matches the route regardless of whether the param is present, absent, or invalid.
   * This gives us a single route arm that handles all cases and always returns 400 (never 404)
   * for bad or missing parameters.
   *
   * Yields `Option[ValidatedNel[ParseFailure, Currency]]`:
   *   - `None`          → param was absent from the query string
   *   - `Some(Invalid)` → param was present but failed to parse
   *   - `Some(Valid)`   → param was present and parsed successfully
   */
  object FromQueryParam extends OptionalValidatingQueryParamDecoderMatcher[Currency]("from")

  /** Extractor for the `to` query parameter. Same rationale as [[FromQueryParam]]. */
  object ToQueryParam   extends OptionalValidatingQueryParamDecoderMatcher[Currency]("to")

  /**
   * Converts an `Option[ValidatedNel[ParseFailure, Currency]]` to a plain
   * `ValidatedNel[ParseFailure, Currency]`, treating `None` (absent param) as an error.
   *
   * This lets the route handler use the same `Invalid` / `Valid` matching for absent params
   * as for malformed ones, producing a uniform 400 in both cases.
   */
  def requireParam(name: String)(opt: Option[ValidatedNel[ParseFailure, Currency]]): ValidatedNel[ParseFailure, Currency] =
    opt.getOrElse(Validated.invalidNel(ParseFailure(s"Missing query parameter: '$name'", s"Missing query parameter: '$name'")))

}
