package forex.services.rates.interpreters

import cats.effect.Sync
import cats.syntax.applicativeError._
import cats.syntax.either._
import cats.syntax.functor._
import forex.config.OneFrameConfig
import forex.domain._
import forex.services.rates.Algebra
import forex.services.rates.errors._
import io.circe.Decoder
import io.circe.generic.extras.Configuration
import io.circe.generic.extras.semiauto.deriveConfiguredDecoder
import org.http4s.Uri
import org.http4s.client.Client
import org.http4s.circe.CirceEntityDecoder._
import org.http4s.{ Header, Request }
import org.typelevel.ci.CIString

/**
 * Live HTTP client for the One-Frame currency rates API.
 *
 * Requires `Sync` (rather than the more powerful `Concurrent`) because every operation is a
 * single sequential HTTP call — no concurrency primitives (fibers, `Ref`, `Deferred`) are needed
 * here. `Sync` provides `delay` for wrapping side effects and `flatMap` for sequencing.
 *
 * In production this class is wrapped by [[OneFrameCache]], which calls `fetchAll` on a
 * schedule and serves individual `get` requests from an in-memory map without hitting HTTP.
 * The [[Algebra]] `get` method is still implemented for completeness and for use in tests.
 */
class OneFrameLive[F[_]: Sync](config: OneFrameConfig, httpClient: Client[F]) extends Algebra[F] {

  import OneFrameLive._

  /**
   * Fetch the rate for a single pair from One-Frame.
   *
   * Delegates to `fetchPairs` with a single-element list and extracts the matching rate.
   * The `.find` is needed because One-Frame always returns a list, even for a single pair.
   */
  override def get(pair: Rate.Pair): F[Error Either Rate] =
    fetchPairs(List(pair)).map {
      case Right(rates) =>
        rates.find(_.pair == pair).toRight(Error.OneFrameLookupFailed(s"pair not found in response"))
      case Left(e) => Left(e)
    }

  /**
   * Fetch all requested pairs in a single One-Frame HTTP call.
   *
   * Called by [[OneFrameCache]] during its refresh cycle to populate the entire cache with
   * one request rather than 72 individual calls. This is the core mechanism that keeps
   * daily call counts well within the 1 000/day limit.
   */
  def fetchAll(pairs: List[Rate.Pair]): F[Error Either List[Rate]] =
    fetchPairs(pairs)

  private def fetchPairs(pairs: List[Rate.Pair]): F[Error Either List[Rate]] = {
    // One-Frame query string format: ?pair=USDJPY&pair=EURUSD&...
    // Each pair is the concatenation of the two ISO currency codes (no separator).
    // `Currency.show` provides the canonical uppercase string representation.
    val pairParams = pairs.map { p =>
      s"pair=${Currency.show.show(p.from)}${Currency.show.show(p.to)}"
    }.mkString("&")

    Uri
      .fromString(s"${config.uri}/rates?$pairParams")
      .leftMap(e => Error.OneFrameLookupFailed(e.message))
      .fold(
        // URI parse failure (malformed config.uri) — surface as a typed Left immediately
        err => Sync[F].pure(Left(err)),
        uri => {
          val request = Request[F](uri = uri)
            // One-Frame uses a custom `token` header for authentication, NOT the standard
            // `Authorization: Bearer <token>` scheme. Using the wrong header name results
            // in a 401 with no response body.
            .putHeaders(Header.Raw(CIString("token"), config.token))
          httpClient
            .expect[List[OneFrameResponse]](request)
            .map(responses => responses.map(toRate).asRight[Error])
            // Convert any network-level or decoding exception into a typed Left so the cache
            // refresh loop can handle it without crashing the application stream.
            .handleErrorWith { e =>
              Sync[F].pure(Left(Error.OneFrameLookupFailed(e.getMessage)))
            }
        }
      )
  }

}

object OneFrameLive {

  // One-Frame returns JSON with snake_case keys (e.g. `time_stamp`).
  // circe-generic-extras' `withSnakeCaseMemberNames` maps them to camelCase Scala fields
  // (e.g. `timeStamp`) automatically during derivation of `OneFrameResponse`'s decoder.
  implicit val circeConfig: Configuration =
    Configuration.default.withSnakeCaseMemberNames

  /**
   * Internal DTO for decoding One-Frame's raw JSON response.
   *
   * Both `bid` and `ask` are captured from the response even though the proxy only uses
   * `price` (the mid-price). Keeping them in the DTO avoids a decoder failure if One-Frame
   * adds or changes fields, and makes the raw data available for future use.
   */
  final case class OneFrameResponse(
      from: String,
      to: String,
      bid: BigDecimal,
      ask: BigDecimal,
      price: BigDecimal,   // mid-price: (bid + ask) / 2, as computed by One-Frame
      timeStamp: String
  )

  implicit val decoder: Decoder[OneFrameResponse] = deriveConfiguredDecoder

  private def toRate(r: OneFrameResponse): Rate = {
    // One-Frame only returns currencies from its own supported set, so `fromString` will
    // always succeed in practice. The `getOrElse(Currency.USD)` fallback is a defensive
    // measure against unexpected server responses (e.g., a future One-Frame version adding
    // a currency we haven't added to our enum yet); it prevents a crash at the cost of
    // silently mis-mapping an unknown currency to USD. In that scenario the cache refresh
    // log will show 72 pairs stored, but affected pairs will return wrong data — a known,
    // acceptable tradeoff given the API contract.
    val from = Currency.fromString(r.from).getOrElse(Currency.USD)
    val to   = Currency.fromString(r.to).getOrElse(Currency.USD)
    Rate(Rate.Pair(from, to), Price(r.price), Timestamp(java.time.OffsetDateTime.parse(r.timeStamp)))
  }

}
