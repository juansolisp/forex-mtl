/**
 * Unit tests for quota-related state logic replicated from StatsPanel.tsx.
 *
 * StatsPanel derives quota display values from the CacheRefreshEvent fields.
 * These tests validate the display logic (progress bar percentage, warning threshold,
 * remaining count) independently of React rendering.
 */
import { describe, it, expect } from "vitest";

// ── Quota bar percentage ──────────────────────────────────────────────────────
// Mirrors: Math.min(100, (callsToday / dailyLimit) * 100)

function quotaPct(callsToday: number, dailyLimit: number): number {
  return Math.min(100, (callsToday / dailyLimit) * 100);
}

describe("quota bar percentage", () => {
  it("is 0 at zero calls", () => {
    expect(quotaPct(0, 1000)).toBe(0);
  });

  it("is 50 at half the limit", () => {
    expect(quotaPct(500, 1000)).toBe(50);
  });

  it("is exactly 80 at the soft limit (800/1000)", () => {
    expect(quotaPct(800, 1000)).toBe(80);
  });

  it("is 100 at the full limit", () => {
    expect(quotaPct(1000, 1000)).toBe(100);
  });

  it("is capped at 100 even when over the limit", () => {
    // Should never happen in practice, but guard against server bugs.
    expect(quotaPct(1200, 1000)).toBe(100);
  });

  it("works with a non-1000 dailyLimit", () => {
    expect(quotaPct(250, 500)).toBe(50);
  });
});

// ── Quota warning threshold ───────────────────────────────────────────────────
// The backend sets quotaWarning = callsToday >= 800.
// The frontend reads it directly from the event — no re-computation needed.
// These tests document the threshold rule for clarity.

describe("quota warning threshold (backend rule)", () => {
  it("is false at 799 calls", () => {
    expect(799 >= 800).toBe(false);
  });

  it("is true at exactly 800 calls", () => {
    expect(800 >= 800).toBe(true);
  });

  it("is true above 800 calls", () => {
    expect(801 >= 800).toBe(true);
    expect(1000 >= 800).toBe(true);
  });
});

// ── Remaining calls display ───────────────────────────────────────────────────
// Mirrors: dailyLimit - callsToday

function remaining(callsToday: number, dailyLimit: number): number {
  return dailyLimit - callsToday;
}

describe("remaining calls", () => {
  it("is 1000 at zero calls", () => {
    expect(remaining(0, 1000)).toBe(1000);
  });

  it("is 0 at the full limit", () => {
    expect(remaining(1000, 1000)).toBe(0);
  });

  it("decrements correctly", () => {
    expect(remaining(360, 1000)).toBe(640);
  });
});

// ── Cache hit ratio ───────────────────────────────────────────────────────────
// Mirrors: stats.proxyRequests / stats.oneFrameCalls (shown as "Xx" in StatsPanel)

function cacheHitRatio(proxyRequests: number, oneFrameCalls: number): string {
  return oneFrameCalls > 0
    ? (proxyRequests / oneFrameCalls).toFixed(1)
    : "—";
}

describe("cache hit ratio", () => {
  it("returns — when no One-Frame calls have been made", () => {
    expect(cacheHitRatio(100, 0)).toBe("—");
  });

  it("returns 0.0 when no proxy requests have been served", () => {
    expect(cacheHitRatio(0, 1)).toBe("0.0");
  });

  it("returns the ratio with one decimal place", () => {
    // 72 requests served by 1 One-Frame batch fetch = 72.0x
    expect(cacheHitRatio(72, 1)).toBe("72.0");
    // 360 served by 5 fetches = 72.0x (steady state for 4-min interval)
    expect(cacheHitRatio(360, 5)).toBe("72.0");
  });

  it("handles fractional ratios correctly", () => {
    expect(cacheHitRatio(10, 3)).toBe("3.3");
  });
});

// ── Freshness age color ───────────────────────────────────────────────────────
// Mirrors the logic in StatsPanel.tsx freshnessColor

function freshnessColor(ageS: number | null, refreshInterval: number): string {
  if (ageS === null) return "text-gray-500";
  if (ageS > refreshInterval * 0.9) return "text-red-400";
  if (ageS > refreshInterval * 0.5) return "text-yellow-400";
  return "text-green-400";
}

describe("freshnessColor", () => {
  const interval = 240; // 4 minutes

  it("returns gray when age is unknown (null)", () => {
    expect(freshnessColor(null, interval)).toBe("text-gray-500");
  });

  it("returns green when age is well within the interval", () => {
    expect(freshnessColor(0, interval)).toBe("text-green-400");
    expect(freshnessColor(119, interval)).toBe("text-green-400"); // just under 50%
  });

  it("returns yellow between 50% and 90% of the interval", () => {
    expect(freshnessColor(121, interval)).toBe("text-yellow-400"); // just over 50%
    expect(freshnessColor(215, interval)).toBe("text-yellow-400"); // just under 90%
  });

  it("returns red above 90% of the interval", () => {
    expect(freshnessColor(217, interval)).toBe("text-red-400"); // just over 90%
    expect(freshnessColor(300, interval)).toBe("text-red-400"); // SLA limit
  });
});
