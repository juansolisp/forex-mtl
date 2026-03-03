import { useState, useRef } from "react";
import { useEventStream } from "../hooks/useEventStream";
import { apiFetch } from "../api";

const CURRENCIES = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SGD", "USD"] as const;
type Currency = (typeof CURRENCIES)[number];

const BURST_SIZES = [10, 50, 100, 200] as const;

interface BurstResult {
  sent: number;
  succeeded: number;
  failed: number;
  p50: number;
  p95: number;
  p99: number;
  minMs: number;
  maxMs: number;
  totalMs: number;
}

/** Random pair guaranteed to have from != to. */
function randomPair(): [Currency, Currency] {
  const from = CURRENCIES[Math.floor(Math.random() * CURRENCIES.length)];
  let to = CURRENCIES[Math.floor(Math.random() * CURRENCIES.length)];
  while (to === from) {
    to = CURRENCIES[Math.floor(Math.random() * CURRENCIES.length)];
  }
  return [from, to];
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)];
}

/**
 * Fires N concurrent /rates requests with random currency pairs.
 *
 * After the burst completes, the results panel shows:
 *   - Success/fail counts (should be all success if One-Frame is up)
 *   - Latency percentiles: p50 is the median user-perceived latency;
 *     p95/p99 show tail behaviour under concurrency.
 *   - One-Frame calls before vs after: should be 0 new calls if the
 *     cache was already warm — proving the cache absorbs burst traffic.
 */
export default function BurstTest() {
  const [burstSize, setBurstSize] = useState<number>(50);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<BurstResult | null>(null);

  // Snapshot the One-Frame call count at burst start to measure delta.
  const { entries } = useEventStream();
  const oneFrameCountRef = useRef(0);

  function countOneFrameCalls(evts: typeof entries) {
    return evts.filter((e) => e.type === "CacheRefresh").length;
  }

  async function runBurst() {
    setRunning(true);
    setResult(null);

    const before = countOneFrameCalls(entries);
    oneFrameCountRef.current = before;

    const pairs = Array.from({ length: burstSize }, () => randomPair());

    const latencies: number[] = [];
    let succeeded = 0;
    let failed = 0;

    const start = Date.now();

    await Promise.all(
      pairs.map(async ([from, to]) => {
        const t0 = Date.now();
        try {
          const resp = await apiFetch(`/rates?from=${from}&to=${to}`);
          latencies.push(Date.now() - t0);
          if (resp.ok) {
            succeeded++;
          } else {
            failed++;
          }
        } catch {
          latencies.push(Date.now() - t0);
          failed++;
        }
      })
    );

    const totalMs = Date.now() - start;

    // Brief pause so SSE CacheRefresh events from the burst can propagate
    // before we read the live count in the next render cycle.
    await new Promise((r) => setTimeout(r, 500));

    const sorted = latencies.slice().sort((a, b) => a - b);

    setResult({
      sent: burstSize,
      succeeded,
      failed,
      p50: percentile(sorted, 50),
      p95: percentile(sorted, 95),
      p99: percentile(sorted, 99),
      minMs: sorted[0] ?? 0,
      maxMs: sorted[sorted.length - 1] ?? 0,
      totalMs,
    });

    setRunning(false);
  }

  // Derive the delta live: current count minus the snapshot captured at burst start.
  // oneFrameCountRef.current is set in runBurst() before firing requests.
  const liveOneFrameCount = countOneFrameCalls(entries);
  const afterDelta = result !== null
    ? liveOneFrameCount - oneFrameCountRef.current
    : null;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Burst Load Test</div>

      <div className="flex flex-wrap gap-3 items-center mb-4">
        <div>
          <label className="text-xs text-gray-500 block mb-1">Requests</label>
          <div className="flex gap-1">
            {BURST_SIZES.map((n) => (
              <button
                key={n}
                onClick={() => setBurstSize(n)}
                className={`px-3 py-1 rounded text-sm font-mono transition-colors ${
                  burstSize === n
                    ? "bg-purple-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={runBurst}
          disabled={running}
          className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 rounded-lg text-sm font-semibold transition-colors mt-4"
        >
          {running ? `Running ${burstSize} requests…` : `Run Burst (${burstSize})`}
        </button>
      </div>

      {result && (
        <div className="space-y-3">
          {/* Summary row */}
          <div className="flex gap-3 flex-wrap">
            <Chip label="sent" value={String(result.sent)} color="text-gray-300" />
            <Chip label="ok" value={String(result.succeeded)} color="text-green-400" />
            {result.failed > 0 && (
              <Chip label="failed" value={String(result.failed)} color="text-red-400" />
            )}
            <Chip label="wall time" value={`${result.totalMs}ms`} color="text-yellow-400" />
          </div>

          {/* Latency row */}
          <div className="bg-gray-800 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-2">Latency (ms)</div>
            <div className="flex gap-6 font-mono text-sm">
              <Stat label="min" value={result.minMs} />
              <Stat label="p50" value={result.p50} />
              <Stat label="p95" value={result.p95} />
              <Stat label="p99" value={result.p99} />
              <Stat label="max" value={result.maxMs} />
            </div>
          </div>

          {/* Cache absorption proof */}
          <div className="bg-gray-800 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-2">
              One-Frame calls during burst
            </div>
            <div className="flex items-baseline gap-2">
              <span
                className={`text-2xl font-bold ${
                  afterDelta === 0 ? "text-green-400" : "text-yellow-400"
                }`}
              >
                +{afterDelta ?? "…"}
              </span>
              <span className="text-xs text-gray-500">
                {afterDelta === 0
                  ? "cache absorbed all requests — zero new One-Frame calls"
                  : "new batch fetch(es) triggered"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Chip({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-gray-800 rounded px-2 py-1 text-xs">
      <span className="text-gray-500">{label} </span>
      <span className={`font-mono font-bold ${color}`}>{value}</span>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="text-gray-600 text-xs">{label}</div>
      <div className="text-cyan-400 font-bold">{value}</div>
    </div>
  );
}
