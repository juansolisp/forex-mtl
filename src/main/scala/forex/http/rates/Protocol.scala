package forex.http
package rates

import forex.domain.Currency.show
import forex.domain.Rate.Pair
import forex.domain._
import io.circe._
import io.circe.generic.extras.Configuration
import io.circe.generic.extras.semiauto.deriveConfiguredEncoder

object Protocol {

  // All JSON keys in the API response use snake_case (e.g. `time_stamp`) to match
  // the One-Frame convention and common REST API expectations.
  implicit val configuration: Configuration = Configuration.default.withSnakeCaseMemberNames

  /**
   * Represents an incoming GET request parsed from query parameters.
   * Defined here for symmetry with `GetApiResponse` and to support a future POST variant
   * that would read currencies from a JSON body. Currently, request validation is performed
   * entirely in [[QueryParams]] using `ValidatingQueryParamDecoderMatcher`.
   */
  final case class GetApiRequest(
      from: Currency,
      to: Currency
  )

  /**
   * The external API response returned to clients.
   *
   * Fields are flat (not nested under `pair`) for a simpler consumer experience:
   * `{"from":"USD","to":"JPY","price":0.71,"timestamp":"..."}` rather than
   * `{"pair":{"from":"USD","to":"JPY"},"price":...}`.
   */
  final case class GetApiResponse(
      from: Currency,
      to: Currency,
      price: Price,
      timestamp: Timestamp
  )

  // Currency is encoded as its ISO string ("USD", "JPY", etc.) by delegating to
  // the `Show[Currency]` instance, which is the canonical serialisation.
  implicit val currencyEncoder: Encoder[Currency] =
    Encoder.instance[Currency] { show.show _ andThen Json.fromString }

  implicit val pairEncoder: Encoder[Pair] =
    deriveConfiguredEncoder[Pair]

  implicit val rateEncoder: Encoder[Rate] =
    deriveConfiguredEncoder[Rate]

  // `GetApiResponse` serialises to: {"from":"USD","to":"JPY","price":0.71,"timestamp":"..."}
  // Price and Timestamp are unwrapped to their underlying types by the
  // `valueClassEncoder` implicit defined in [[forex.http.package]].
  implicit val responseEncoder: Encoder[GetApiResponse] =
    deriveConfiguredEncoder[GetApiResponse]

}
