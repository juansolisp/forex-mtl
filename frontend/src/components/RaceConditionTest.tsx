import { useState } from "react";
import { apiFetch } from "../api";

const CURRENCIES = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SGD", "USD"] as const;
type Currency = (typeof CURRENCIES)[number];

const CONCURRENCY_OPTIONS = [10, 25, 50, 100, 200] as const;

interface RaceResult {
  pair: string;
  sent: number;
  succeeded: number;
  failed: number;
  uniquePrices: number[];
  allSame: boolean;
  minMs: number;
  maxMs: number;
  p50: number;
  p95: number;
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  return sorted[Math.max(0, Math.ceil((p / 100) * sorted.length) - 1)];
}

export default function RaceConditionTest() {
  const [from, setFrom] = useState<Currency>("USD");
  const [to, setTo] = useState<Currency>("JPY");
  const [concurrency, setConcurrency] = useState<number>(50);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RaceResult | null>(null);

  async function runTest() {
    if (from === to) return;
    setRunning(true);
    setResult(null);

    const results = await Promise.all(
      Array.from({ length: concurrency }, async () => {
        const t0 = Date.now();
        try {
          const resp = await apiFetch(`/rates?from=${from}&to=${to}`);
          const latencyMs = Date.now() - t0;
          if (resp.ok) {
            const data = await resp.json();
            return { ok: true, price: data.price as number, latencyMs };
          }
          return { ok: false, price: null, latencyMs };
        } catch {
          return { ok: false, price: null, latencyMs: Date.now() - t0 };
        }
      })
    );

    const succeeded = results.filter((r) => r.ok);
    const failed = results.filter((r) => !r.ok);
    const prices = [...new Set(succeeded.map((r) => r.price!))].sort((a, b) => a - b);
    const latencies = results.map((r) => r.latencyMs).sort((a, b) => a - b);

    setResult({
      pair: `${from}/${to}`,
      sent: concurrency,
      succeeded: succeeded.length,
      failed: failed.length,
      uniquePrices: prices,
      allSame: prices.length <= 1,
      minMs: latencies[0] ?? 0,
      maxMs: latencies[latencies.length - 1] ?? 0,
      p50: percentile(latencies, 50),
      p95: percentile(latencies, 95),
    });

    setRunning(false);
  }

  const canRun = from !== to;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider">Race Condition Test</div>
      <p className="text-xs text-gray-600 leading-relaxed">
        Fires N concurrent requests for the same currency pair. All responses must return
        the exact same price — proving the Ref[F, Map] cache is atomic and concurrent reads
        never observe a torn or partially-updated state.
      </p>

      {/* Pair selector */}
      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="text-xs text-gray-500 block mb-1">FROM</label>
          <select
            value={from}
            onChange={(e) => setFrom(e.target.value as Currency)}
            disabled={running}
            className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-purple-500 disabled:opacity-50"
          >
            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <span className="text-gray-600 pb-1.5">→</span>

        <div>
          <label className="text-xs text-gray-500 block mb-1">TO</label>
          <select
            value={to}
            onChange={(e) => setTo(e.target.value as Currency)}
            disabled={running}
            className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-purple-500 disabled:opacity-50"
          >
            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {from === to && (
          <span className="text-red-400 text-xs pb-1.5">from ≠ to required</span>
        )}
      </div>

      {/* Concurrency selector */}
      <div>
        <label className="text-xs text-gray-500 block mb-1">Concurrent requests</label>
        <div className="flex gap-1 flex-wrap">
          {CONCURRENCY_OPTIONS.map((n) => (
            <button
              key={n}
              onClick={() => setConcurrency(n)}
              disabled={running}
              className={`px-3 py-1 rounded text-sm font-mono transition-colors disabled:opacity-40
                ${concurrency === n ? "bg-purple-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={runTest}
        disabled={running || !canRun}
        className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 rounded-lg text-sm font-semibold transition-colors"
      >
        {running ? `Firing ${concurrency} concurrent requests…` : `Run Race Test (${concurrency})`}
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-3">
          {/* Pass/fail assertion */}
          <div
            className={`rounded-lg p-4 border text-sm font-mono ${
              result.allSame && result.failed === 0
                ? "border-green-700 bg-green-950/40 text-green-400"
                : result.allSame
                ? "border-yellow-700 bg-yellow-950/40 text-yellow-400"
                : "border-red-700 bg-red-950/40 text-red-400"
            }`}
          >
            {result.allSame && result.failed === 0 ? (
              <div>
                <div className="font-bold text-base mb-1">✓ PASS — No race condition detected</div>
                <div className="text-sm opacity-80">
                  All {result.succeeded} concurrent responses returned the same price:{" "}
                  <span className="text-cyan-400">{result.uniquePrices[0]}</span>
                </div>
              </div>
            ) : result.allSame ? (
              <div>
                <div className="font-bold text-base mb-1">
                  ⚠ PARTIAL — Prices consistent but {result.failed} request(s) failed
                </div>
                <div className="text-sm opacity-80">
                  Price: <span className="text-cyan-400">{result.uniquePrices[0]}</span>
                  {" · "}{result.failed} failures (network/timeout)
                </div>
              </div>
            ) : (
              <div>
                <div className="font-bold text-base mb-1">✗ FAIL — Inconsistent prices!</div>
                <div className="text-sm opacity-80">
                  Got {result.uniquePrices.length} distinct prices: {result.uniquePrices.join(", ")}
                </div>
              </div>
            )}
          </div>

          {/* Summary chips */}
          <div className="flex gap-2 flex-wrap text-xs">
            <Chip label="pair" value={result.pair} color="text-gray-300" />
            <Chip label="sent" value={String(result.sent)} color="text-gray-300" />
            <Chip label="ok" value={String(result.succeeded)} color="text-green-400" />
            {result.failed > 0 && (
              <Chip label="failed" value={String(result.failed)} color="text-red-400" />
            )}
            <Chip
              label="unique prices"
              value={String(result.uniquePrices.length)}
              color={result.uniquePrices.length === 1 ? "text-green-400" : "text-red-400"}
            />
          </div>

          {/* Latency */}
          <div className="bg-gray-800 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-2">Latency (ms)</div>
            <div className="flex gap-6 font-mono text-sm flex-wrap">
              {[
                { label: "min", value: result.minMs },
                { label: "p50", value: result.p50 },
                { label: "p95", value: result.p95 },
                { label: "max", value: result.maxMs },
              ].map(({ label, value }) => (
                <div key={label}>
                  <div className="text-gray-600 text-xs">{label}</div>
                  <div className="text-cyan-400 font-bold">{value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* All unique prices detail */}
          {result.uniquePrices.length > 1 && (
            <div className="bg-red-950/20 border border-red-800 rounded-lg p-3">
              <div className="text-xs text-red-400 mb-1 font-semibold">Distinct prices observed:</div>
              <div className="font-mono text-sm text-red-300">
                {result.uniquePrices.join(" · ")}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Chip({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-gray-800 rounded px-2 py-1">
      <span className="text-gray-500">{label} </span>
      <span className={`font-mono font-bold ${color}`}>{value}</span>
    </div>
  );
}
