import { useMemo, useState, useEffect } from "react";
import { useEventStream } from "../hooks/useEventStream";
import { useRefreshInterval } from "../hooks/useRefreshInterval";

/**
 * Derives live statistics from the SSE event stream.
 *
 * Key metrics that prove the assignment requirements are met:
 *   - One-Frame calls: count of CacheRefresh events. Should be ~1 per 4 minutes,
 *     regardless of how many proxy requests are served. This proves the cache
 *     absorbs traffic and keeps the call count << 1000/day.
 *   - Proxy requests: count of ProxyRequest events. Can grow arbitrarily.
 *   - Cache hit rate: (proxyRequests / oneFrameCalls) shows how many client
 *     requests each One-Frame call serves.
 *   - Pairs in last refresh: from the most recent CacheRefresh event.
 *   - Freshness age: seconds since the last CacheRefresh, counting up live.
 *     The 5-minute SLA requires this stays below 300s.
 */
export default function StatsPanel() {
  const { entries, connected } = useEventStream();
  const refreshInterval = useRefreshInterval();
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const stats = useMemo(() => {
    let proxyRequests = 0;
    let oneFrameCalls = 0;
    let lastCacheRefresh: string | null = null;
    let lastPairsCount = 0;
    let totalProxyMs = 0;
    let callsToday = 0;
    let dailyLimit = 1000;
    let quotaWarning = false;

    for (const e of entries) {
      if (e.type === "ProxyRequest") {
        proxyRequests++;
        totalProxyMs += e.durationMs;
      } else if (e.type === "CacheRefresh") {
        oneFrameCalls++;
        lastCacheRefresh = e.timestamp;
        lastPairsCount = e.pairsCount;
        callsToday   = e.callsToday;
        dailyLimit   = e.dailyLimit;
        quotaWarning = e.quotaWarning;
      }
    }

    const avgLatencyMs =
      proxyRequests > 0 ? totalProxyMs / proxyRequests : null;

    return { proxyRequests, oneFrameCalls, lastCacheRefresh, lastPairsCount, avgLatencyMs,
             callsToday, dailyLimit, quotaWarning };
  }, [entries]);

  const freshnessAgeS = stats.lastCacheRefresh
    ? Math.floor((now - new Date(stats.lastCacheRefresh).getTime()) / 1000)
    : null;

  const freshnessColor =
    freshnessAgeS === null
      ? "text-gray-500"
      : freshnessAgeS > refreshInterval * 0.9
      ? "text-red-400"
      : freshnessAgeS > refreshInterval * 0.5
      ? "text-yellow-400"
      : "text-green-400";

  const cacheHitRatio =
    stats.oneFrameCalls > 0
      ? (stats.proxyRequests / stats.oneFrameCalls).toFixed(1)
      : "—";

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-500 uppercase tracking-wider">Live Stats</span>
        <span className="flex items-center gap-1.5 text-xs">
          <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-green-400" : "bg-red-500"}`} />
          <span className={connected ? "text-green-400" : "text-red-400"}>
            {connected ? "connected" : "disconnected"}
          </span>
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {/* One-Frame calls */}
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">One-Frame calls</div>
          <div className="text-2xl font-bold text-purple-400">{stats.oneFrameCalls}</div>
          <div className="text-xs text-gray-600 mt-1">batch fetches</div>
        </div>

        {/* Proxy requests served */}
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Requests served</div>
          <div className="text-2xl font-bold text-cyan-400">{stats.proxyRequests}</div>
          <div className="text-xs text-gray-600 mt-1">from cache</div>
        </div>

        {/* Cache efficiency */}
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Cache ratio</div>
          <div className="text-2xl font-bold text-green-400">{cacheHitRatio}x</div>
          <div className="text-xs text-gray-600 mt-1">req / 1 fetch</div>
        </div>

        {/* Rate freshness */}
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Cache age</div>
          <div className={`text-2xl font-bold ${freshnessColor}`}>
            {freshnessAgeS !== null ? `${freshnessAgeS}s` : "—"}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {stats.lastPairsCount > 0 ? `${stats.lastPairsCount} pairs` : "no refresh yet"}
          </div>
        </div>
      </div>

      {/* One-Frame quota bar */}
      {stats.callsToday > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">One-Frame quota today</span>
            <span className={`text-xs font-mono font-bold ${stats.quotaWarning ? "text-yellow-400" : "text-green-400"}`}>
              {stats.callsToday} / {stats.dailyLimit}
              {stats.quotaWarning && <span className="ml-1 text-yellow-400">⚠ &gt;80%</span>}
            </span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                stats.quotaWarning ? "bg-yellow-400" : "bg-green-500"
              }`}
              style={{ width: `${Math.min(100, (stats.callsToday / stats.dailyLimit) * 100)}%` }}
            />
          </div>
          <div className="text-[10px] text-gray-700 mt-0.5 text-right">
            {stats.dailyLimit - stats.callsToday} remaining · resets at UTC midnight
          </div>
        </div>
      )}

      {/* Avg latency */}
      {stats.avgLatencyMs !== null && (
        <div className="mt-3 text-xs text-gray-600 text-right">
          avg proxy latency: <span className="text-gray-400">{stats.avgLatencyMs!.toFixed(2)}ms</span>
        </div>
      )}
    </div>
  );
}
