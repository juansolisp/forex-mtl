package forex

import cats.effect.Sync
import io.circe.generic.extras.decoding.{ EnumerationDecoder, UnwrappedDecoder }
import io.circe.generic.extras.encoding.{ EnumerationEncoder, UnwrappedEncoder }
import io.circe.{ Decoder, Encoder }
import org.http4s.{ EntityDecoder, EntityEncoder }
import org.http4s.circe._

/**
 * Implicit conversions shared across all `forex.http` sub-packages.
 *
 * Defined once in this package object rather than repeated in every route/protocol file.
 * All implicits here are automatically in scope for any file under `forex.http.*`.
 */
package object http {

  /**
   * JSON encoder for `AnyVal` wrapper types (e.g. [[forex.domain.Price]], [[forex.domain.Timestamp]]).
   * circe-generic-extras' `UnwrappedEncoder` serialises `Price(0.71)` as `0.71` (not `{"value":0.71}`),
   * producing clean JSON responses without manual encoder definitions for each wrapper.
   */
  implicit def valueClassEncoder[A: UnwrappedEncoder]: Encoder[A] = implicitly
  implicit def valueClassDecoder[A: UnwrappedDecoder]: Decoder[A] = implicitly

  // Sealed-trait enumeration encoders/decoders (not currently used but provided for completeness
  // in case circe-generic-extras derives encoders for Currency via @JsonCodec in the future).
  implicit def enumEncoder[A: EnumerationEncoder]: Encoder[A] = implicitly
  implicit def enumDecoder[A: EnumerationDecoder]: Decoder[A] = implicitly

  /**
   * Bridge from circe's `Decoder[A]` / `Encoder[A]` to http4s's `EntityDecoder[F, A]` /
   * `EntityEncoder[F, A]`. Without these, http4s cannot read or write JSON request/response
   * bodies even if circe encoders are in scope.
   *
   * The `<: Product` bound limits these to case classes (products), which is everything
   * we encode/decode in the HTTP layer.
   */
  implicit def jsonDecoder[A <: Product: Decoder, F[_]: Sync]: EntityDecoder[F, A] = jsonOf[F, A]
  implicit def jsonEncoder[A <: Product: Encoder, F[_]]: EntityEncoder[F, A] = jsonEncoderOf[F, A]

}
