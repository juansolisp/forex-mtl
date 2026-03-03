package forex.programs.rates

import cats.Id
import forex.domain._
import forex.services.rates.{ Algebra => RatesAlgebra }
import forex.services.rates.errors.{ Error => ServiceError }
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

/**
 * Unit tests for [[Program]] — the bridge between service and program error types.
 *
 * `cats.Id` is used as the effect type instead of `IO`.  `Id[A]` is just `A`, so all
 * operations are pure and synchronous with no runtime required.  This is possible because
 * `Program` only requires `Functor`, and `cats.Id` has a `Functor` instance.  Using `Id`
 * here keeps the tests fast and dependency-free while still exercising the real `Program`
 * implementation (not a mock).
 */
class ProgramSpec extends AnyFunSuite with Matchers {

  private def makeService(result: ServiceError Either Rate): RatesAlgebra[Id] =
    new RatesAlgebra[Id] {
      override def get(pair: Rate.Pair): Id[ServiceError Either Rate] = result
    }

  test("get returns Right(Rate) when service succeeds") {
    val pair    = Rate.Pair(Currency.USD, Currency.JPY)
    val rate    = Rate(pair, Price(BigDecimal("0.71")), Timestamp.now)
    val service = makeService(Right(rate))
    val program = Program[Id](service)

    val result = program.get(Protocol.GetRatesRequest(Currency.USD, Currency.JPY))
    result shouldBe Right(rate)
  }

  test("get maps service error to program error") {
    // Verifies that `toProgramError` is applied: `OneFrameLookupFailed` becomes `RateLookupFailed`.
    // The test checks the runtime class name rather than importing the concrete error type,
    // keeping the test decoupled from the exact program error hierarchy.
    val serviceErr = ServiceError.OneFrameLookupFailed("upstream down")
    val service    = makeService(Left(serviceErr))
    val program    = Program[Id](service)

    val result = program.get(Protocol.GetRatesRequest(Currency.USD, Currency.JPY))
    result shouldBe a[Left[_, _]]
    result.left.map(_.getClass.getSimpleName) shouldBe Left("RateLookupFailed")
  }

  // PRG-03: RateLookupFailed.getMessage returns the message string (not null)
  test("RateLookupFailed.getMessage returns the wrapped message") {
    val err = errors.Error.RateLookupFailed("test error message")
    err.getMessage shouldBe "test error message"
  }

}
