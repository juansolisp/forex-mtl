package forex

/**
 * Type aliases and companion shortcuts for the services layer.
 *
 * These aliases let the rest of the application reference `RatesService[F]` and
 * `RatesServices` without importing the concrete `rates.Algebra` and `rates.Interpreters`
 * types.  Callers in [[Module]] and [[Main]] import only the service package, not the
 * inner `rates` package — this enforces the layer boundary and makes future refactoring
 * (e.g. adding a second service) non-breaking at call sites.
 */
package object services {
  /** The capability required to look up an exchange rate.  Alias for [[rates.Algebra]]. */
  type RatesService[F[_]] = rates.Algebra[F]

  /** Factory for all [[RatesService]] implementations (dummy, live, cachedLive). */
  final val RatesServices = rates.Interpreters
}
