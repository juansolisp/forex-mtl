package forex

/**
 * Type aliases and companion shortcuts for the programs layer.
 *
 * `RatesProgram[F]` is the type imported by [[http.rates.RatesHttpRoutes]]; using the alias
 * means the HTTP layer never imports `programs.rates.*` directly, preserving the
 * separation between HTTP and program layers.  If the program implementation changes
 * (e.g. a second program for batch quotes) only this alias and [[Module]] need updating.
 */
package object programs {
  /** The capability required to service a rate-lookup HTTP request.  Alias for [[rates.Algebra]]. */
  type RatesProgram[F[_]] = rates.Algebra[F]

  /** Factory for [[RatesProgram]] instances. */
  final val RatesProgram = rates.Program
}
