package forex.domain

import cats.Show
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

/**
 * Property-style tests for [[Currency]] using plain ScalaTest.
 *
 * Written as table-driven tests over `Currency.values` rather than using ScalaCheck generators
 * because the currency domain is finite and fixed — full enumeration is both possible
 * and clearer than probabilistic sampling. A property failure here means a logic error in
 * `show` or `fromString` for a specific currency, which is easy to diagnose.
 */
class CurrencyProperties extends AnyFunSuite with Matchers {

  test("show then fromString is identity for all currencies") {
    Currency.values.foreach { c =>
      Currency.fromString(Show[Currency].show(c)) shouldBe Right(c)
    }
  }

  test("fromString with lowercase still succeeds") {
    Currency.values.foreach { c =>
      Currency.fromString(Show[Currency].show(c).toLowerCase) shouldBe Right(c)
    }
  }

  test("all 72 distinct pairs have unique (from, to) keys") {
    // Validates that `Currency.values` produces no duplicates, which would cause the cache
    // to store fewer than 72 entries and silently fail for the duplicate pairs.
    val pairs = for {
      from <- Currency.values
      to   <- Currency.values
      if from != to
    } yield (from, to)

    pairs.distinct.size shouldBe pairs.size
    pairs.size shouldBe 72
  }

}
