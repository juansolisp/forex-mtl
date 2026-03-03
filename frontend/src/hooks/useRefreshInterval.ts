/**
 * Module-level singleton for the cache refresh interval.
 *
 * The interval is fetched once from GET /config/refresh-interval on first mount.
 * It only changes when the user explicitly calls setRefreshInterval(). Heartbeat events
 * do NOT change the interval — they only update lastRefreshedAt (handled by FreshnessBar
 * via addHeartbeatListener).
 *
 * lastRefreshedAt is no longer tracked here. FreshnessBar derives it directly from:
 *   1. SSE CacheRefresh events (most authoritative — live, millisecond-accurate)
 *   2. Heartbeat.lastRefreshedAt (resyncs after reconnect, survives page reload)
 * This eliminates the previous setInterval(/config/status) polling entirely.
 */
import { useState, useEffect } from "react";
import { apiFetch } from "../api";

type IntervalListener = (seconds: number) => void;

let globalInterval: number = 240;
let globalLoaded = false;
let globalLoading = false;
let globalTimerId: ReturnType<typeof setInterval> | null = null;

const intervalListeners = new Set<IntervalListener>();

function notifyInterval() {
  intervalListeners.forEach((l) => l(globalInterval));
}

function fetchInterval() {
  if (globalLoading) return;
  globalLoading = true;
  apiFetch("/config/refresh-interval")
    .then((r) => r.json())
    .then((d: { seconds: number }) => {
      globalInterval = d.seconds;
      globalLoaded = true;
      globalLoading = false;
      notifyInterval();
    })
    .catch(() => {
      globalLoading = false;
      // Retry after 5s on failure — bounded single retry, no accumulation.
      setTimeout(fetchInterval, 5_000);
    });
}

function ensureLoaded() {
  if (globalLoaded || globalLoading) return;
  fetchInterval();
  // Single polling timer — created exactly once, stored so it is never duplicated.
  if (globalTimerId === null) {
    globalTimerId = setInterval(fetchInterval, 60_000);
  }
}

/** Subscribe to the shared refresh interval. Re-renders whenever any component changes it. */
export function useRefreshInterval(): number {
  const [interval, setIntervalState] = useState(globalInterval);

  useEffect(() => {
    const listener = (s: number) => setIntervalState(s);
    intervalListeners.add(listener);
    ensureLoaded();
    setIntervalState(globalInterval);
    return () => { intervalListeners.delete(listener); };
  }, []);

  return interval;
}

/**
 * PUT the new interval to the server and broadcast to all subscribers.
 * Throws with the server's error message if the request fails.
 */
export async function setRefreshInterval(seconds: number): Promise<number> {
  const resp = await apiFetch("/config/refresh-interval", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seconds }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.message ?? "request failed");
  globalInterval = data.seconds;
  globalLoaded = true;
  notifyInterval();
  return data.seconds;
}
