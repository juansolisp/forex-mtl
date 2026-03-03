import { useState } from "react";
import { useEventStream, type CacheRefreshEvent } from "../hooks/useEventStream";
import { apiFetch } from "../api";

export default function ForceRefresh() {
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<{
    success: boolean;
    message: string;
    durationMs: number;
  } | null>(null);
  const [history, setHistory] = useState<Array<{ time: string; durationMs: number }>>([]);

  const { entries } = useEventStream();

  // The most recent CacheRefresh SSE event — updates live as events arrive.
  const lastSseRefresh = [...entries]
    .reverse()
    .find((e): e is CacheRefreshEvent => e.type === "CacheRefresh") ?? null;

  async function forceRefresh() {
    setLoading(true);
    setLastResult(null);
    const t0 = Date.now();
    try {
      const resp = await apiFetch("/config/force-refresh", { method: "POST" });
      const durationMs = Date.now() - t0;
      if (resp.ok) {
        setLastResult({ success: true, message: "Cache refreshed successfully", durationMs });
        setHistory((prev) => [
          { time: new Date().toLocaleTimeString("en-US", { hour12: false }), durationMs },
          ...prev.slice(0, 9),
        ]);
      } else {
        const text = await resp.text();
        setLastResult({ success: false, message: `HTTP ${resp.status}: ${text}`, durationMs });
      }
    } catch (e) {
      setLastResult({
        success: false,
        message: String(e),
        durationMs: Date.now() - t0,
      });
    } finally {
      setLoading(false);
    }
  }

  const cacheRefreshes = entries.filter((e) => e.type === "CacheRefresh");
  const totalRefreshes = cacheRefreshes.length;
  const avgDuration =
    totalRefreshes > 0
      ? (cacheRefreshes as CacheRefreshEvent[]).reduce((s, e) => s + e.durationMs, 0) / totalRefreshes
      : null;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider">Force Cache Refresh</div>
      <p className="text-xs text-gray-600 leading-relaxed">
        Triggers an immediate cache refresh by calling One-Frame for all 72 pairs right now,
        bypassing the scheduled refresh interval. The response arrives only after the
        refresh completes. Watch the SSE event log for the CacheRefresh event.
      </p>

      {/* Big button */}
      <div className="flex flex-col items-center gap-3 py-4">
        <button
          onClick={forceRefresh}
          disabled={loading}
          className={`w-48 h-16 rounded-xl text-lg font-bold transition-all
            ${loading
              ? "bg-gray-700 text-gray-500 cursor-not-allowed"
              : "bg-purple-600 hover:bg-purple-500 active:scale-95 text-white shadow-lg shadow-purple-900/50"
            }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Refreshing…
            </span>
          ) : (
            "⚡ Force Refresh"
          )}
        </button>

        {loading && (
          <div className="text-xs text-gray-500 animate-pulse">
            Calling One-Frame for all 72 pairs…
          </div>
        )}
      </div>

      {/* Last result */}
      {lastResult && (
        <div
          className={`rounded-lg p-3 border text-sm ${
            lastResult.success
              ? "border-green-700 bg-green-950/40 text-green-400"
              : "border-red-700 bg-red-950/40 text-red-400"
          }`}
        >
          <div className="font-semibold">{lastResult.success ? "✓" : "✗"} {lastResult.message}</div>
          <div className="text-xs opacity-70 mt-1">Round-trip: {lastResult.durationMs}ms</div>
        </div>
      )}

      {/* Live SSE confirmation */}
      {lastSseRefresh && (
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-2">Latest CacheRefresh SSE event</div>
          <div className="flex gap-4 text-xs font-mono flex-wrap">
            <span>
              <span className="text-gray-600">pairs: </span>
              <span className="text-green-400">{lastSseRefresh.pairsCount}</span>
            </span>
            <span>
              <span className="text-gray-600">duration: </span>
              <span className="text-cyan-400">{lastSseRefresh.durationMs.toFixed(0)}ms</span>
            </span>
            <span>
              <span className="text-gray-600">at: </span>
              <span className="text-gray-300">
                {new Date(lastSseRefresh.timestamp).toLocaleTimeString("en-US", { hour12: false })}
              </span>
            </span>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Total refreshes</div>
          <div className="text-2xl font-bold text-purple-400">{totalRefreshes}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Manual triggers</div>
          <div className="text-2xl font-bold text-cyan-400">{history.length}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Avg duration</div>
          <div className="text-2xl font-bold text-gray-300">
            {avgDuration !== null ? `${avgDuration.toFixed(0)}ms` : "—"}
          </div>
        </div>
      </div>

      {/* Manual trigger history */}
      {history.length > 0 && (
        <div>
          <div className="text-xs text-gray-600 mb-2">Manual trigger history</div>
          <div className="space-y-1">
            {history.map((h, i) => (
              <div key={i} className="flex justify-between text-xs font-mono">
                <span className="text-gray-500">{h.time}</span>
                <span className="text-cyan-400">{h.durationMs}ms</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
