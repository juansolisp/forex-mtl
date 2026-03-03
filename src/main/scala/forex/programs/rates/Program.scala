package forex.programs.rates

import cats.Functor
import cats.data.EitherT
import errors._
import forex.domain._
import forex.services.RatesService

/**
 * Bridge between the rates service algebra and the rates program algebra.
 *
 * Its single responsibility is translating the `GetRatesRequest` into a `Rate.Pair` and
 * mapping service-level errors to program-level errors. No business logic lives here.
 *
 * `Functor` is the minimum required type class: `EitherT.leftMap` only needs `map`
 * (provided by `Functor`), not `flatMap` or `Applicative`. Declaring the weakest
 * sufficient constraint makes the class usable with `cats.Id` in unit tests without
 * pulling in a full `Monad` instance.
 */
class Program[F[_]: Functor](
    ratesService: RatesService[F]
) extends Algebra[F] {

  override def get(request: Protocol.GetRatesRequest): F[Error Either Rate] =
    // EitherT wraps F[Either[E, A]] to give access to `.leftMap` without manual pattern matching.
    // After `.leftMap` translates the error type, `.value` unwraps back to F[Either[Error, Rate]].
    EitherT(ratesService.get(Rate.Pair(request.from, request.to))).leftMap(toProgramError(_)).value

}

object Program {

  def apply[F[_]: Functor](
      ratesService: RatesService[F]
  ): Algebra[F] = new Program[F](ratesService)

}
