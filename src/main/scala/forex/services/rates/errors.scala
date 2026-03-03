package forex.services.rates

object errors {

  /**
   * Sum type of all errors that can be produced by the rates service layer.
   *
   * Keeping errors sealed and service-local means the HTTP layer never imports this type
   * directly — it works with [[forex.programs.rates.errors.Error]] instead, and
   * [[forex.programs.rates.errors.toProgramError]] performs the translation.
   * This layering prevents accidental coupling between HTTP response codes and internal
   * service failure modes.
   */
  sealed trait Error

  object Error {
    /**
     * Raised when the One-Frame API call fails for any reason:
     * network timeout, non-200 response, JSON decode failure, or a requested pair
     * being absent from the response body.
     *
     * @param msg human-readable description of the failure, safe to propagate to logs
     *            and (after translation) to the HTTP error response body
     */
    final case class OneFrameLookupFailed(msg: String) extends Error
  }

}
