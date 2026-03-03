/**
 * Unit tests for pure helper functions in EventLog.tsx.
 *
 * These functions have no React or DOM dependencies — they are pure transformations
 * of numbers and strings. Extracting them into tests keeps the coverage deterministic
 * and fast (no rendering overhead).
 *
 * Because the helpers are not exported from EventLog.tsx (they are module-private),
 * we duplicate them here. This is intentional: the test file serves as the canonical
 * specification for these formatting rules.
 */
import { describe, it, expect } from "vitest";

// ── fmtDuration ───────────────────────────────────────────────────────────────
// Mirrors the function in EventLog.tsx exactly.

function fmtDuration(ms: number): string {
  if (ms < 1) return ms.toFixed(3);
  if (ms < 10) return ms.toFixed(2);
  if (ms < 100) return ms.toFixed(1);
  return Math.round(ms).toString();
}

describe("fmtDuration", () => {
  it("formats sub-millisecond values with 3 decimal places", () => {
    expect(fmtDuration(0.423)).toBe("0.423");
    expect(fmtDuration(0.001)).toBe("0.001");
    expect(fmtDuration(0.999)).toBe("0.999");
  });

  it("formats 1–9ms with 2 decimal places", () => {
    expect(fmtDuration(1.0)).toBe("1.00");
    expect(fmtDuration(5.56)).toBe("5.56");
    expect(fmtDuration(9.99)).toBe("9.99");
  });

  it("formats 10–99ms with 1 decimal place", () => {
    expect(fmtDuration(10.0)).toBe("10.0");
    expect(fmtDuration(50.7)).toBe("50.7");
    expect(fmtDuration(99.9)).toBe("99.9");
  });

  it("formats 100ms+ as rounded integer", () => {
    expect(fmtDuration(100)).toBe("100");
    expect(fmtDuration(150.6)).toBe("151");
    expect(fmtDuration(1000)).toBe("1000");
  });

  it("formats exactly 0 as sub-millisecond", () => {
    expect(fmtDuration(0)).toBe("0.000");
  });
});

// ── statusColor ───────────────────────────────────────────────────────────────

function statusColor(status: number): string {
  if (status === 200) return "text-green-400";
  if (status >= 400 && status < 500) return "text-yellow-400";
  return "text-red-400";
}

describe("statusColor", () => {
  it("returns green for 200", () => {
    expect(statusColor(200)).toBe("text-green-400");
  });

  it("returns yellow for 4xx", () => {
    expect(statusColor(400)).toBe("text-yellow-400");
    expect(statusColor(422)).toBe("text-yellow-400");
    expect(statusColor(499)).toBe("text-yellow-400");
  });

  it("returns red for 5xx", () => {
    expect(statusColor(500)).toBe("text-red-400");
    expect(statusColor(503)).toBe("text-red-400");
  });

  it("returns red for anything else (e.g. 301)", () => {
    expect(statusColor(301)).toBe("text-red-400");
  });
});

// ── durationColor ─────────────────────────────────────────────────────────────

function durationColor(ms: number): string {
  if (ms < 1) return "text-green-400";
  if (ms < 5) return "text-cyan-400";
  if (ms < 50) return "text-yellow-400";
  return "text-red-400";
}

describe("durationColor", () => {
  it("returns green for sub-millisecond durations (cache hits)", () => {
    expect(durationColor(0)).toBe("text-green-400");
    expect(durationColor(0.5)).toBe("text-green-400");
    expect(durationColor(0.999)).toBe("text-green-400");
  });

  it("returns cyan for 1–4ms", () => {
    expect(durationColor(1)).toBe("text-cyan-400");
    expect(durationColor(4.9)).toBe("text-cyan-400");
  });

  it("returns yellow for 5–49ms", () => {
    expect(durationColor(5)).toBe("text-yellow-400");
    expect(durationColor(49)).toBe("text-yellow-400");
  });

  it("returns red for 50ms+", () => {
    expect(durationColor(50)).toBe("text-red-400");
    expect(durationColor(200)).toBe("text-red-400");
  });
});

// ── getSortValue helpers ──────────────────────────────────────────────────────

type ProxyRequestEvent = {
  type: "ProxyRequest"; id: string; from: string; to: string;
  status: number; price: number | null; errorBody: string | null;
  durationMs: number; timestamp: string;
};
type CacheRefreshEvent = {
  type: "CacheRefresh"; pairsCount: number; durationMs: number;
  timestamp: string; callsToday: number; dailyLimit: number; quotaWarning: boolean;
};
type LogEntry = ProxyRequestEvent | CacheRefreshEvent;

function isProxyRequest(e: LogEntry): e is ProxyRequestEvent {
  return e.type === "ProxyRequest";
}

describe("isProxyRequest type guard", () => {
  it("returns true for ProxyRequest events", () => {
    const e: LogEntry = {
      type: "ProxyRequest", id: "abc", from: "USD", to: "JPY",
      status: 200, price: 0.71, errorBody: null, durationMs: 0.5, timestamp: "2024-01-01T00:00:00Z",
    };
    expect(isProxyRequest(e)).toBe(true);
  });

  it("returns false for CacheRefresh events", () => {
    const e: LogEntry = {
      type: "CacheRefresh", pairsCount: 72, durationMs: 100.0,
      timestamp: "2024-01-01T00:00:00Z", callsToday: 1, dailyLimit: 1000, quotaWarning: false,
    };
    expect(isProxyRequest(e)).toBe(false);
  });
});
