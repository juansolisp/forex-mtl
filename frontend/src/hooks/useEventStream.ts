import { useEffect, useRef, useState } from "react";

export interface ProxyRequestEvent {
  type: "ProxyRequest";
  id: string;
  from: string;
  to: string;
  status: number;
  price: number | null;
  errorBody: string | null;
  durationMs: number;  // sub-millisecond float, e.g. 0.423
  timestamp: string;
}

export interface CacheRefreshEvent {
  type: "CacheRefresh";
  pairsCount: number;
  durationMs: number;  // sub-millisecond float
  timestamp: string;
  callsToday: number;
  dailyLimit: number;
  quotaWarning: boolean;
}

export interface CacheRefreshFailedEvent {
  type: "CacheRefreshFailed";
  reason: string;
  timestamp: string;
  durationMs: 0;  // placeholder so LogEntry columns work uniformly
}

/**
 * Emitted by the server every 30 seconds per open SSE connection.
 *
 * Two purposes:
 * 1. **Keepalive** — prevents Nginx / NAT tables from closing idle connections
 *    during the quiet window between cache refreshes (up to 4 minutes).
 * 2. **Clock skew correction** — `serverTimeMs` is the server's epoch-ms at emit time.
 *    The browser computes `clockOffsetMs = serverTimeMs - Date.now()` and applies it to
 *    all elapsed-time calculations, eliminating server/browser clock divergence.
 *
 * `lastRefreshedAt` is the ISO-8601 UTC timestamp of the last successful cache refresh,
 * or null on a cold start where One-Frame was never reachable. This seeds the freshness
 * timer correctly after an SSE reconnect without requiring a separate HTTP poll.
 */
export interface HeartbeatEvent {
  type: "Heartbeat";
  serverTimeMs: number;
  lastRefreshedAt: string | null;
}

export type LogEntry = ProxyRequestEvent | CacheRefreshEvent | CacheRefreshFailedEvent;

const MAX_EVENTS = 2000;

// ─── Module-level singleton ───────────────────────────────────────────────────

type Listener = (entries: LogEntry[], connected: boolean, clockOffsetMs: number) => void;

let globalEntries: LogEntry[] = [];
let globalConnected = false;
let globalClockOffsetMs = 0;   // server epoch ms minus browser epoch ms at last heartbeat
let globalEs: EventSource | null = null;
const listeners = new Set<Listener>();

let globalSeq = 0;
const seqMap = new Map<LogEntry, number>();

/**
 * Callbacks invoked whenever a Heartbeat arrives.
 * FreshnessBar and other components register here to react to heartbeat data
 * (lastRefreshedAt, clockOffsetMs) without needing to parse the full LogEntry union.
 */
type HeartbeatListener = (hb: HeartbeatEvent) => void;
const heartbeatListeners = new Set<HeartbeatListener>();

export function addHeartbeatListener(l: HeartbeatListener): () => void {
  heartbeatListeners.add(l);
  return () => heartbeatListeners.delete(l);
}

function notifyAll() {
  listeners.forEach((l) => l(globalEntries, globalConnected, globalClockOffsetMs));
}

function ensureConnected() {
  if (globalEs) return;
  const es = new EventSource("/events");
  globalEs = es;

  es.onopen = () => {
    globalConnected = true;
    notifyAll();
  };

  es.onmessage = (e) => {
    try {
      const parsed = JSON.parse(e.data) as LogEntry | HeartbeatEvent;

      if (parsed.type === "Heartbeat") {
        // Clock skew correction: compute offset once per heartbeat.
        // Positive offset → server clock is ahead of browser clock.
        globalClockOffsetMs = parsed.serverTimeMs - Date.now();
        heartbeatListeners.forEach((l) => l(parsed));
        notifyAll();   // refresh clockOffsetMs in all subscribers
        return;
      }

      // Regular LogEntry — append to the ring buffer.
      globalSeq++;
      seqMap.set(parsed, globalSeq);
      globalEntries = [...globalEntries, parsed];
      if (globalEntries.length > MAX_EVENTS) {
        const dropped = globalEntries.slice(0, globalEntries.length - MAX_EVENTS);
        dropped.forEach((d) => seqMap.delete(d));
        globalEntries = globalEntries.slice(-MAX_EVENTS);
      }
      notifyAll();
    } catch {
      // ignore malformed frames
    }
  };

  es.onerror = () => {
    globalConnected = false;
    notifyAll();
  };
}

export function clearEvents() {
  globalEntries = [];
  globalSeq = 0;
  seqMap.clear();
  notifyAll();
}

export function getSeq(entry: LogEntry): number {
  return seqMap.get(entry) ?? 0;
}

/** Current clock offset: add to Date.now() to get server-corrected time. */
export function getClockOffsetMs(): number {
  return globalClockOffsetMs;
}

export function useEventStream() {
  const [entries, setEntries] = useState<LogEntry[]>(globalEntries);
  const [connected, setConnected] = useState(globalConnected);
  const [clockOffsetMs, setClockOffsetMs] = useState(globalClockOffsetMs);

  const listenerRef = useRef<Listener>((e, c, o) => {
    setEntries(e);
    setConnected(c);
    setClockOffsetMs(o);
  });

  useEffect(() => {
    const listener = listenerRef.current;
    listeners.add(listener);
    ensureConnected();
    setEntries(globalEntries);
    setConnected(globalConnected);
    setClockOffsetMs(globalClockOffsetMs);
    return () => {
      listeners.delete(listener);
    };
  }, []);

  return { entries, connected, clockOffsetMs };
}
