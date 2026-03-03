import { useState, useEffect, useMemo } from "react";
import { useEventStream, addHeartbeatListener, type CacheRefreshEvent, type HeartbeatEvent } from "../hooks/useEventStream";
import { useRefreshInterval } from "../hooks/useRefreshInterval";

const SLA_SECONDS = 300; // 5-minute SLA

/**
 * FreshnessBar — live cache-age display driven by SSE events and heartbeats.
 *
 * == How the freshness anchor works ==
 *
 * The "anchor" is the timestamp of the last successful cache refresh. We derive it
 * from three sources in priority order:
 *
 * 1. **SSE CacheRefresh events** (highest priority) — live, millisecond-accurate.
 *    Received immediately when the cache refreshes during an active session.
 *
 * 2. **Heartbeat.lastRefreshedAt** — the server writes the last-refresh timestamp
 *    into every 30-second heartbeat. This resyncs the anchor after:
 *    - Page reload (SSE history is lost, heartbeat arrives within 30s)
 *    - SSE reconnect after a network blip
 *    - Tab returning from background (visibilitychange triggers immediate re-read)
 *
 * 3. **null** — cache has never refreshed (cold start with One-Frame down). The
 *    component shows "—" until the first anchor arrives.
 *
 * == Clock skew correction ==
 *
 * The browser's Date.now() and the server's System.currentTimeMillis() can diverge
 * by seconds (VM clock drift, CI containers, developer laptops). Every Heartbeat
 * carries serverTimeMs. We compute:
 *   clockOffsetMs = serverTimeMs - Date.now()
 * and use (Date.now() + clockOffsetMs) as the "corrected now" in all age calculations.
 * This keeps the elapsed-time display accurate regardless of clock skew.
 *
 * == Page Visibility API ==
 *
 * Browser timers are throttled to once per minute when a tab is backgrounded (Chrome,
 * Firefox, Safari all do this since ~2021). When the user returns to the tab, the 1-second
 * setInterval fires immediately, but `now` may be many seconds stale. We listen for
 * `visibilitychange` and force an immediate `Date.now()` read on tab activation, so the
 * first render after returning is correct.
 */
export default function FreshnessBar() {
  const { entries, clockOffsetMs } = useEventStream();
  const currentInterval = useRefreshInterval();

  // "Corrected now" — server-epoch-ms computed from the browser clock + skew offset.
  // Updated by setInterval(1s) during active tab, and immediately on visibilitychange.
  const [now, setNow] = useState(() => Date.now());

  // The authoritative last-refresh timestamp. Populated from SSE CacheRefresh events
  // (live) and from Heartbeat.lastRefreshedAt (after reconnect / page load).
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string | null>(null);

  // Tick every second while the tab is visible.
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  // Page Visibility API: snap "now" immediately when the user returns to this tab.
  // Without this, the stale `now` from before backgrounding would show a wrong age
  // for up to 60 seconds (browser timer throttle).
  useEffect(() => {
    const handler = () => {
      if (document.visibilityState === "visible") {
        setNow(Date.now());
      }
    };
    document.addEventListener("visibilitychange", handler);
    return () => document.removeEventListener("visibilitychange", handler);
  }, []);

  // Heartbeat listener: resyncs lastRefreshedAt on every heartbeat and triggers a
  // clock-corrected "now" update.
  //
  // WHY always overwrite (not prev ?? hb.lastRefreshedAt):
  // The heartbeat carries the server's current last-refresh timestamp. After a cache
  // refresh happens, the NEXT heartbeat will carry the updated timestamp. If we guard
  // with `prev ??` we only ever set it once and ignore every subsequent heartbeat —
  // the timer would never reset after a refresh. Always accepting the heartbeat value
  // ensures the anchor stays in sync with the server. SSE CacheRefresh events (handled
  // below) still take effect immediately when they arrive, so there is no race.
  useEffect(() => {
    const remove = addHeartbeatListener((hb: HeartbeatEvent) => {
      if (hb.lastRefreshedAt) {
        setLastRefreshedAt(hb.lastRefreshedAt);
      }
      // Force an immediate clock-corrected "now" so the timer doesn't stall between ticks.
      setNow(Date.now());
    });
    return remove;
  }, []);

  // Derive the most recent CacheRefresh event and the refresh history from SSE.
  const { latestSseRefresh, history } = useMemo(() => {
    const refreshes = entries
      .filter((e): e is CacheRefreshEvent => e.type === "CacheRefresh")
      .slice(-20);
    return { latestSseRefresh: refreshes[refreshes.length - 1] ?? null, history: refreshes };
  }, [entries]);

  // SSE CacheRefresh events update the anchor immediately when they arrive.
  useEffect(() => {
    if (latestSseRefresh) {
      setLastRefreshedAt(latestSseRefresh.timestamp);
    }
  }, [latestSseRefresh]);

  // "Corrected now" — apply clock offset from the most recent heartbeat.
  // If clockOffsetMs is 0 (no heartbeat yet), this is just Date.now(), which is fine.
  const correctedNow = now + clockOffsetMs;

  const lastRefreshMs = lastRefreshedAt ? new Date(lastRefreshedAt).getTime() : 0;
  const ageMs = lastRefreshMs > 0 ? correctedNow - lastRefreshMs : null;
  const ageS = ageMs !== null ? Math.max(0, Math.floor(ageMs / 1000)) : null;

  // The bar spans 0 → currentInterval. The SLA cap (300s) is shown as a marker.
  const period = Math.min(currentInterval, SLA_SECONDS);
  const pct = ageS !== null ? Math.min(100, (ageS / period) * 100) : 0;

  const isWarn = ageS !== null && ageS >= period * 0.75 && ageS < period * 0.9;
  const isCritical = ageS !== null && ageS >= period * 0.9;
  const isSlaBreached = ageS !== null && ageS >= SLA_SECONDS;

  const barColor = isSlaBreached
    ? "bg-red-600 animate-pulse"
    : isCritical
    ? "bg-red-500"
    : isWarn
    ? "bg-yellow-400"
    : "bg-green-500";

  const ageColor = isSlaBreached || isCritical
    ? "text-red-400"
    : isWarn
    ? "text-yellow-400"
    : "text-green-400";

  // Average interval between refreshes from SSE history
  const avgIntervalS = useMemo(() => {
    if (history.length < 2) return null;
    const intervals: number[] = [];
    for (let i = 1; i < history.length; i++) {
      const a = new Date(history[i - 1].timestamp).getTime();
      const b = new Date(history[i].timestamp).getTime();
      intervals.push((b - a) / 1000);
    }
    return intervals.reduce((s, v) => s + v, 0) / intervals.length;
  }, [history]);

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider">Cache Freshness</div>

      <p className="text-xs text-gray-600 leading-relaxed">
        Time since the last cache refresh. The 5-minute SLA requires this stays below 300s.
        Yellow at 75% of the refresh interval, red at 90%, pulsing red if the SLA is breached.
      </p>

      {/* Main age display */}
      <div className="flex items-baseline gap-3">
        <span className={`text-5xl font-bold font-mono tabular-nums ${ageColor}`}>
          {ageS !== null ? `${ageS}s` : "—"}
        </span>
        <div className="text-xs text-gray-500 flex flex-col gap-0.5">
          <span>since last refresh</span>
          {ageS !== null && (
            <span className={ageColor}>
              {isSlaBreached
                ? "✗ SLA BREACHED"
                : isCritical
                ? "⚠ approaching SLA"
                : isWarn
                ? "⚡ warming up"
                : "✓ fresh"}
            </span>
          )}
        </div>
        {clockOffsetMs !== 0 && (
          <span className="text-[10px] text-gray-700 ml-auto self-end">
            clock offset: {clockOffsetMs > 0 ? "+" : ""}{clockOffsetMs}ms
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-[11px] text-gray-600 mb-1">
          <span>0s</span>
          <span className="text-gray-500">
            interval: <span className="text-purple-400">{currentInterval}s</span>
          </span>
          <span className={ageS !== null && ageS >= SLA_SECONDS ? "text-red-500" : "text-gray-600"}>
            SLA: {SLA_SECONDS}s
          </span>
        </div>

        <div className="relative h-5 bg-gray-800 rounded-full overflow-hidden">
          {/* SLA marker */}
          <div
            className="absolute top-0 bottom-0 w-px bg-red-700/60 z-10"
            style={{ left: `${Math.min(100, (SLA_SECONDS / period) * 100)}%` }}
          />
          {/* 75% warning marker */}
          <div
            className="absolute top-0 bottom-0 w-px bg-yellow-700/50 z-10"
            style={{ left: "75%" }}
          />
          <div
            className={`h-full rounded-full transition-all duration-1000 ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>

        <div className="flex justify-between text-[10px] text-gray-700 mt-0.5">
          <span>fresh</span>
          <span style={{ marginLeft: "75%" }}>75% warn</span>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <InfoBox
          label="Refreshes seen"
          value={String(history.length)}
          color="text-purple-400"
        />
        <InfoBox
          label="Last pairs count"
          value={latestSseRefresh ? String(latestSseRefresh.pairsCount) : "—"}
          color="text-cyan-400"
        />
        <InfoBox
          label="Last duration"
          value={latestSseRefresh ? `${latestSseRefresh.durationMs.toFixed(0)}ms` : "—"}
          color="text-gray-300"
        />
        <InfoBox
          label="Avg interval"
          value={avgIntervalS !== null ? `${avgIntervalS.toFixed(0)}s` : "—"}
          color={avgIntervalS !== null && avgIntervalS > SLA_SECONDS ? "text-red-400" : "text-green-400"}
        />
      </div>

      {/* Refresh history timeline */}
      {history.length > 0 && (
        <div>
          <div className="text-xs text-gray-600 mb-2">Refresh history (last {history.length})</div>
          <div className="flex flex-col gap-1">
            {[...history].reverse().slice(0, 10).map((r, i) => {
              const ts = new Date(r.timestamp).toLocaleTimeString("en-US", {
                hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit",
              });
              return (
                <div key={i} className="flex items-center gap-3 text-[11px] font-mono">
                  <span className="text-gray-600 w-20 shrink-0">{ts}</span>
                  <span className="text-green-400">{r.pairsCount} pairs</span>
                  <span className="text-gray-600">{r.durationMs.toFixed(0)}ms</span>
                  <div className="flex-1 h-1 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-600 rounded-full"
                      style={{ width: `${Math.min(100, (r.durationMs / 2000) * 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {ageS === null && (
        <div className="text-xs text-gray-600 text-center py-4">
          Waiting for first heartbeat…
        </div>
      )}
    </div>
  );
}

function InfoBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-lg font-bold font-mono ${color}`}>{value}</div>
    </div>
  );
}
