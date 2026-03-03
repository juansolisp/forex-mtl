package forex.services.rates

import java.time.LocalDate

import forex.services.rates.interpreters.QuotaState
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

/**
 * Unit tests for [[QuotaState]] — the in-memory counter that tracks how many
 * successful One-Frame API calls have been made today (UTC day).
 *
 * All cases are deterministic and pure (no IO); QuotaState is a plain case class
 * with no effectful dependencies.
 */
class QuotaStateSpec extends AnyFunSuite with Matchers {

  private val today     = LocalDate.now(java.time.ZoneOffset.UTC)
  private val yesterday = today.minusDays(1)

  test("increment increases callsToday by 1") {
    val qs = QuotaState(5, today)
    qs.increment.callsToday shouldBe 6
  }

  test("increment retains the same date when the day has not changed") {
    val qs = QuotaState(0, today)
    qs.increment.date shouldBe today
  }

  test("increment resets callsToday to 1 when the stored date is yesterday") {
    // Simulates the server running past UTC midnight: the stored date is yesterday,
    // so increment rolls over to a fresh day before counting.
    val stale = QuotaState(999, yesterday)
    val next  = stale.increment
    next.callsToday shouldBe 1
    next.date       shouldBe today
  }

  test("dailyLimit is always 1000") {
    QuotaState(0, today).dailyLimit      shouldBe 1000
    QuotaState(999, today).dailyLimit    shouldBe 1000
    QuotaState(1001, today).dailyLimit   shouldBe 1000
  }

  test("quotaWarning is false below 80% of the daily limit") {
    QuotaState(799, today).quotaWarning shouldBe false
    QuotaState(0,   today).quotaWarning shouldBe false
  }

  test("quotaWarning is true at exactly 80% of the daily limit (800 calls)") {
    QuotaState(800, today).quotaWarning shouldBe true
  }

  test("quotaWarning is true above 80% of the daily limit") {
    QuotaState(801,  today).quotaWarning shouldBe true
    QuotaState(1000, today).quotaWarning shouldBe true
  }

  test("increment from 799 crosses the soft limit — quotaWarning becomes true") {
    val before = QuotaState(799, today)
    val after  = before.increment
    before.quotaWarning shouldBe false
    after.callsToday    shouldBe 800
    after.quotaWarning  shouldBe true
  }

  test("successive increments accumulate correctly") {
    val result = (1 to 10).foldLeft(QuotaState(0, today))((q, _) => q.increment)
    result.callsToday shouldBe 10
  }
}
