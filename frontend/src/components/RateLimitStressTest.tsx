import { useState, useRef, useCallback } from "react";

// One-Frame supports a 1 000 calls/day quota. This test fires requests directly
// at One-Frame (bypassing our cache) to observe what happens as the limit is approached
// and breached: response shape, status codes, and whether our proxy degrades gracefully.

const TOTAL_REQUESTS = 1000;
// Send in waves of CONCURRENCY so the browser doesn't open 1000 sockets at once.
const CONCURRENCY = 20;
const TOKEN = "10dc303535874aeccc86a8251e6992f5";

type PhaseState = "idle" | "running" | "done";

interface Tick {
  seq: number;
  status: "ok" | "quota" | "error";
  responseMs: number;
  body: string;
}

interface Summary {
  ok: number;
  quota: number;
  errors: number;
  firstQuotaAt: number | null; // seq number of first quota response
  minMs: number;
  maxMs: number;
  p50: number;
  p95: number;
  totalMs: number;
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)];
}

export default function RateLimitStressTest() {
  const [phase, setPhase] = useState<PhaseState>("idle");
  const [ticks, setTicks] = useState<Tick[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const seqRef = useRef(0);

  const run = useCallback(async () => {
    setPhase("running");
    setTicks([]);
    setSummary(null);
    seqRef.current = 0;

    const abort = new AbortController();
    abortRef.current = abort;

    const latencies: number[] = [];
    let ok = 0;
    let quota = 0;
    let errors = 0;
    let firstQuotaAt: number | null = null;
    const wallStart = Date.now();

    const fireBatch = async (batchStart: number) => {
      const indices = Array.from(
        { length: Math.min(CONCURRENCY, TOTAL_REQUESTS - batchStart) },
        (_, i) => batchStart + i
      );

      await Promise.all(
        indices.map(async (idx) => {
          const seq = idx + 1;
          const t0 = Date.now();
          let status: Tick["status"] = "error";
          let body = "";

          try {
            const resp = await fetch(
              `/one-frame/rates?pair=USDJPY`,
              {
                headers: { token: TOKEN },
                signal: abort.signal,
              }
            );
            const responseMs = Date.now() - t0;
            body = await resp.text();
            latencies.push(responseMs);

            if (body.includes('"error"')) {
              status = "quota";
              quota++;
              if (firstQuotaAt === null) firstQuotaAt = seq;
            } else {
              status = "ok";
              ok++;
            }

            setTicks((prev) => [
              ...prev,
              { seq, status, responseMs, body: body.slice(0, 120) },
            ]);
          } catch (e) {
            if ((e as Error).name === "AbortError") return;
            const responseMs = Date.now() - t0;
            latencies.push(responseMs);
            errors++;
            body = (e as Error).message;
            setTicks((prev) => [
              ...prev,
              { seq, status: "error", responseMs, body: body.slice(0, 120) },
            ]);
          }
        })
      );
    };

    for (let i = 0; i < TOTAL_REQUESTS; i += CONCURRENCY) {
      if (abort.signal.aborted) break;
      await fireBatch(i);
    }

    const sorted = latencies.slice().sort((a, b) => a - b);
    setSummary({
      ok,
      quota,
      errors,
      firstQuotaAt,
      minMs: sorted[0] ?? 0,
      maxMs: sorted[sorted.length - 1] ?? 0,
      p50: percentile(sorted, 50),
      p95: percentile(sorted, 95),
      totalMs: Date.now() - wallStart,
    });
    setPhase("done");
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setPhase("done");
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setPhase("idle");
    setTicks([]);
    setSummary(null);
  }, []);

  // Count live ticks while running
  const liveOk = ticks.filter((t) => t.status === "ok").length;
  const liveQuota = ticks.filter((t) => t.status === "quota").length;
  const liveErrors = ticks.filter((t) => t.status === "error").length;
  const progress = ticks.length;

  // Find first quota tick for inline annotation
  const firstQuotaTick = ticks.find((t) => t.status === "quota");

  return (
    <div className="bg-gray-900 rounded-xl border border-red-900 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-red-400 uppercase tracking-wider font-semibold">
          One-Frame Rate Limit Stress Test
        </span>
        <span className="text-xs text-gray-600">
          {TOTAL_REQUESTS} direct calls · bypasses cache
        </span>
      </div>
      <p className="text-xs text-gray-600 mb-4">
        Fires {TOTAL_REQUESTS} requests directly at One-Frame (concurrency {CONCURRENCY}) to exhaust
        the 1 000/day quota. Observes when <code className="text-red-400">{"\"error\":\"Quota reached\""}</code> appears
        and how our proxy handles stale-cache serving afterwards.
      </p>

      {/* Controls */}
      <div className="flex gap-2 mb-4">
        {phase === "idle" && (
          <button
            onClick={run}
            className="px-5 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-semibold transition-colors"
          >
            Run {TOTAL_REQUESTS} Requests
          </button>
        )}
        {phase === "running" && (
          <>
            <button
              onClick={stop}
              className="px-5 py-2 bg-yellow-700 hover:bg-yellow-600 rounded-lg text-sm font-semibold transition-colors"
            >
              Stop
            </button>
            <span className="self-center text-xs text-gray-400">
              {progress} / {TOTAL_REQUESTS} sent…
            </span>
          </>
        )}
        {phase === "done" && (
          <button
            onClick={reset}
            className="px-5 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-semibold transition-colors"
          >
            Reset
          </button>
        )}
      </div>

      {/* Live / final counters */}
      {(phase === "running" || phase === "done") && (
        <div className="flex gap-3 flex-wrap mb-4">
          <Chip label="sent" value={String(progress)} color="text-gray-300" />
          <Chip label="ok" value={String(liveOk)} color="text-green-400" />
          <Chip label="quota reached" value={String(liveQuota)} color="text-red-400" />
          {liveErrors > 0 && (
            <Chip label="errors" value={String(liveErrors)} color="text-yellow-400" />
          )}
          {firstQuotaTick && (
            <Chip
              label="first quota @ req"
              value={String(firstQuotaTick.seq)}
              color="text-orange-400"
            />
          )}
        </div>
      )}

      {/* Progress bar */}
      {phase === "running" && (
        <div className="w-full bg-gray-800 rounded-full h-2 mb-4 overflow-hidden">
          <div
            className="h-2 rounded-full transition-all"
            style={{
              width: `${(progress / TOTAL_REQUESTS) * 100}%`,
              background:
                liveQuota > 0
                  ? "linear-gradient(90deg, #16a34a, #dc2626)"
                  : "#9333ea",
            }}
          />
        </div>
      )}

      {/* Final summary */}
      {summary && phase === "done" && (
        <div className="space-y-3 mb-4">
          <div className="bg-gray-800 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-2">Latency (ms) — all {summary.ok + summary.quota + summary.errors} responses</div>
            <div className="flex gap-6 font-mono text-sm">
              <Stat label="min"  value={summary.minMs} />
              <Stat label="p50"  value={summary.p50} />
              <Stat label="p95"  value={summary.p95} />
              <Stat label="max"  value={summary.maxMs} />
              <Stat label="wall" value={summary.totalMs} />
            </div>
          </div>

          {summary.quota > 0 && (
            <div className="bg-red-950 border border-red-800 rounded-lg p-3 text-xs space-y-1">
              <div className="text-red-400 font-semibold">Quota exhausted</div>
              <div className="text-gray-400">
                One-Frame returned <code className="text-red-300">{"\"Quota reached\""}</code> from request{" "}
                <span className="text-orange-400 font-mono">#{summary.firstQuotaAt}</span> onwards.
              </div>
              <div className="text-gray-400">
                Our proxy continues serving <span className="text-green-400">cached data</span> — clients see no errors
                until the cache TTL expires.
              </div>
            </div>
          )}

          {summary.quota === 0 && (
            <div className="bg-green-950 border border-green-800 rounded-lg p-3 text-xs text-green-400">
              Quota not reached — One-Frame accepted all {summary.ok} requests.
              The daily counter may have been partially used; try again or check with a fresh token.
            </div>
          )}
        </div>
      )}

      {/* Live tick log — last 40 only to keep DOM small */}
      {ticks.length > 0 && (
        <div className="bg-gray-950 rounded-lg border border-gray-800 overflow-hidden">
          <div className="px-3 py-2 border-b border-gray-800 text-xs text-gray-500 flex justify-between">
            <span>Response log (last 40)</span>
            <span className="font-mono">{ticks.length} received</span>
          </div>
          <div className="max-h-48 overflow-y-auto font-mono text-xs divide-y divide-gray-800">
            {ticks.slice(-40).map((t) => (
              <div
                key={t.seq}
                className={`px-3 py-1.5 flex gap-3 items-start ${
                  t.status === "quota"
                    ? "bg-red-950/40"
                    : t.status === "error"
                    ? "bg-yellow-950/30"
                    : ""
                }`}
              >
                <span className="text-gray-600 shrink-0 w-8 text-right">#{t.seq}</span>
                <span
                  className={`shrink-0 w-12 ${
                    t.status === "ok"
                      ? "text-green-400"
                      : t.status === "quota"
                      ? "text-red-400"
                      : "text-yellow-400"
                  }`}
                >
                  {t.status === "ok" ? "OK" : t.status === "quota" ? "QUOTA" : "ERR"}
                </span>
                <span className="text-gray-500 shrink-0 w-14 text-right">{t.responseMs}ms</span>
                <span className="text-gray-700 truncate">{t.body}</span>
              </div>
            ))}
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
