package forex.domain

import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

/**
 * Unit tests for [[Rate]] and [[Rate.Pair]] construction.
 *
 * These tests are intentionally simple: the domain types are plain case classes with no logic,
 * so the tests serve primarily as compilation guards — they ensure the data model can be
 * constructed and accessed as expected, and will catch any accidental field reordering or
 * type changes during refactoring.
 */
class RateSpec extends AnyFunSuite with Matchers {

  test("Rate.Pair holds from and to currencies") {
    val pair = Rate.Pair(Currency.USD, Currency.JPY)
    pair.from shouldBe Currency.USD
    pair.to   shouldBe Currency.JPY
  }

  test("Rate holds pair, price and timestamp") {
    val pair  = Rate.Pair(Currency.EUR, Currency.USD)
    val price = Price(BigDecimal("1.0823"))
    val ts    = Timestamp.now
    val rate  = Rate(pair, price, ts)

    rate.pair      shouldBe pair
    rate.price     shouldBe price
    rate.timestamp shouldBe ts
  }

  test("all 72 currency pairs can be constructed") {
    val pairs = for {
      from <- Currency.values
      to   <- Currency.values
      if from != to
    } yield Rate.Pair(from, to)

    pairs.size shouldBe 72 // 9 * 8 — confirms Currency.values has exactly 9 entries
  }

  // DOM-08: direction matters — Pair(A,B) and Pair(B,A) are structurally unequal
  test("Rate.Pair(A, B) is not equal to Rate.Pair(B, A)") {
    val ab = Rate.Pair(Currency.USD, Currency.JPY)
    val ba = Rate.Pair(Currency.JPY, Currency.USD)
    ab should not equal ba
  }

  // DOM-09: Rate.Pair can be used as a Map key (relies on case class equals/hashCode)
  test("Rate.Pair is usable as a Map key") {
    val pair  = Rate.Pair(Currency.USD, Currency.JPY)
    val price = Price(BigDecimal("0.71"))
    val rate  = Rate(pair, price, Timestamp.now)
    val m     = Map(pair -> rate)
    m.get(Rate.Pair(Currency.USD, Currency.JPY)) shouldBe Some(rate)
  }

}
