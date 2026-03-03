package forex.programs.rates

import forex.services.rates.errors.{ Error => RatesServiceError }

object errors {

  /**
   * Sum type of all errors that can be returned by the rates program layer.
   *
   * Extends `Exception` so that instances can be used with `EitherT.fromEither` and other
   * cats utilities that expect a `Throwable` upper bound. The `getMessage` override is
   * necessary because Scala case classes do not automatically forward constructor arguments
   * to `Exception`'s message field — without the override, `getMessage` would return `null`.
   */
  sealed trait Error extends Exception

  object Error {
    /**
     * The rate for the requested pair could not be retrieved.
     *
     * @param msg the reason, forwarded from the service layer and safe to include
     *            in the HTTP 500 response body (see [[forex.http.rates.RatesHttpRoutes]])
     */
    final case class RateLookupFailed(msg: String) extends Error {
      override def getMessage: String = msg
    }
  }

  /**
   * The single mapping point from service errors to program errors.
   *
   * Centralising this here means that if a new [[RatesServiceError]] variant is added,
   * the compiler will flag this match as incomplete — ensuring the new error
   * is handled before it can silently propagate as an unmatched case.
   */
  def toProgramError(error: RatesServiceError): Error = error match {
    case RatesServiceError.OneFrameLookupFailed(msg) => Error.RateLookupFailed(msg)
  }
}
