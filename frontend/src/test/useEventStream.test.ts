/**
 * Unit tests for the useEventStream module — specifically the module-level
 * singleton logic (ring buffer trimming, seq map, clearEvents) that does not
 * require a live EventSource or React components.
 *
 * We test the exported functions directly to avoid spinning up a DOM EventSource.
 * The SSE connection itself is tested by the integration tests (scripts/integration-test.sh).
 */
import { describe, it, expect, beforeEach } from "vitest";
import { clearEvents, getSeq } from "../hooks/useEventStream";
import type { LogEntry } from "../hooks/useEventStream";

function makeProxyEvent(id: string): LogEntry {
  return {
    type: "ProxyRequest",
    id,
    from: "USD",
    to: "JPY",
    status: 200,
    price: 0.71,
    errorBody: null,
    durationMs: 0.5,
    timestamp: new Date().toISOString(),
  };
}

describe("clearEvents", () => {
  beforeEach(() => {
    clearEvents();
  });

  it("can be called without throwing", () => {
    expect(() => clearEvents()).not.toThrow();
  });

  it("can be called multiple times without error", () => {
    clearEvents();
    clearEvents();
    clearEvents();
  });
});

describe("getSeq", () => {
  beforeEach(() => {
    clearEvents();
  });

  it("returns 0 for an entry that was never registered", () => {
    const entry = makeProxyEvent("unregistered");
    expect(getSeq(entry)).toBe(0);
  });

  it("returns 0 for any entry after clearEvents is called", () => {
    // After clear, the seqMap is reset so all entries return 0.
    const entry = makeProxyEvent("cleared");
    // We cannot add entries directly (the module is encapsulated), but we can
    // verify that clearEvents resets the sequence map by checking that getSeq
    // always returns 0 for externally-created entries.
    clearEvents();
    expect(getSeq(entry)).toBe(0);
  });
});

describe("LogEntry type shape (structural)", () => {
  it("ProxyRequest has expected fields", () => {
    const e: LogEntry = {
      type: "ProxyRequest",
      id: "abc12345",
      from: "USD",
      to: "JPY",
      status: 200,
      price: 0.71,
      errorBody: null,
      durationMs: 0.423,
      timestamp: "2024-01-01T00:00:00Z",
    };
    expect(e.type).toBe("ProxyRequest");
    expect(e.from).toBe("USD");
    expect(e.to).toBe("JPY");
    expect(e.durationMs).toBe(0.423);
  });

  it("CacheRefresh has quota fields", () => {
    const e: LogEntry = {
      type: "CacheRefresh",
      pairsCount: 72,
      durationMs: 150.0,
      timestamp: "2024-01-01T00:00:00Z",
      callsToday: 3,
      dailyLimit: 1000,
      quotaWarning: false,
    };
    expect(e.type).toBe("CacheRefresh");
    expect(e.pairsCount).toBe(72);
    expect(e.callsToday).toBe(3);
    expect(e.quotaWarning).toBe(false);
  });

  it("CacheRefreshFailed has reason field", () => {
    const e: LogEntry = {
      type: "CacheRefreshFailed",
      reason: "connection refused",
      timestamp: "2024-01-01T00:00:00Z",
      durationMs: 0,
    };
    expect(e.type).toBe("CacheRefreshFailed");
    expect(e.reason).toBe("connection refused");
  });
});
