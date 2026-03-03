package forex.domain

import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

/**
 * Unit tests for [[Currency]] parsing, serialisation, and enumeration.
 *
 * Tests are deliberately example-based (not property-based) here for readability.
 * Property-based coverage (round-trip, full pair count) lives in [[CurrencyProperties]].
 */
class CurrencySpec extends AnyFunSuite with Matchers {

  test("fromString returns Right for all valid currency codes") {
    val validCodes = List("AUD", "CAD", "CHF", "EUR", "GBP", "NZD", "JPY", "SGD", "USD")
    validCodes.foreach { code =>
      Currency.fromString(code) shouldBe a[Right[_, _]]
    }
  }

  test("fromString is case-insensitive") {
    Currency.fromString("usd") shouldBe Right(Currency.USD)
    Currency.fromString("Eur") shouldBe Right(Currency.EUR)
  }

  test("fromString returns Left for unknown currency") {
    Currency.fromString("XYZ") shouldBe a[Left[_, _]]
    Currency.fromString("")    shouldBe a[Left[_, _]]
  }

  test("values contains all 9 currencies") {
    Currency.values.size shouldBe 9
    Currency.values should contain allOf (
      Currency.AUD, Currency.CAD, Currency.CHF, Currency.EUR,
      Currency.GBP, Currency.NZD, Currency.JPY, Currency.SGD, Currency.USD
    )
  }

  test("show produces correct string representation") {
    cats.Show[Currency].show(Currency.USD) shouldBe "USD"
    cats.Show[Currency].show(Currency.JPY) shouldBe "JPY"
  }

  test("fromString and show are inverses") {
    Currency.values.foreach { c =>
      val shown = cats.Show[Currency].show(c)
      Currency.fromString(shown) shouldBe Right(c)
    }
  }

}
