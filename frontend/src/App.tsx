import { useState, useEffect } from "react";
import paidyLogo from "./logo/paidy.png";
import { logout } from "./hooks/useAuth";
import EventLog from "./components/EventLog";
import StatsPanel from "./components/StatsPanel";
import RefreshControl from "./components/RefreshControl";
import BurstTest from "./components/BurstTest";
import AllPairsGrid from "./components/AllPairsGrid";
import RateLimitCalculator from "./components/RateLimitCalculator";
import FreshnessBar from "./components/FreshnessBar";
import ForceRefresh from "./components/ForceRefresh";
import RaceConditionTest from "./components/RaceConditionTest";
import ValidationMatrix from "./components/ValidationMatrix";
import RateLimitStressTest from "./components/RateLimitStressTest";
import { useEventStream } from "./hooks/useEventStream";
import { apiFetch } from "./api";

const CURRENCIES = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SGD", "USD"] as const;
type Currency = (typeof CURRENCIES)[number];

interface RateResponse {
  from: string;
  to: string;
  price: number;
  timestamp: string;
}

interface RequestLog {
  id: number;
  requestId: string | null;
  from: Currency;
  to: Currency;
  result: RateResponse | null;
  error: string | null;
  durationMs: number;
  time: string;
}

// ─── Tab bar ─────────────────────────────────────────────────────────────────

type Tab = "main" | "logs";

function useHashTab(): [Tab, (t: Tab) => void] {
  const [tab, setTabState] = useState<Tab>(() =>
    window.location.hash === "#logs" ? "logs" : "main"
  );

  useEffect(() => {
    const handler = () =>
      setTabState(window.location.hash === "#logs" ? "logs" : "main");
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  const setTab = (t: Tab) => {
    window.location.hash = t === "logs" ? "logs" : "";
  };

  return [tab, setTab];
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [from, setFrom] = useState<Currency>("USD");
  const [to, setTo] = useState<Currency>("JPY");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [log, setLog] = useState<RequestLog[]>([]);
  const [counter, setCounter] = useState(0);

  const [tab, setTab] = useHashTab();
  const { entries, connected } = useEventStream();

  // Count unseen errors/failures while the logs tab is not active.
  const [seenLogCount, setSeenLogCount] = useState(0);
  const errorCount = entries.filter(
    (e) => e.type === "CacheRefreshFailed" || (e.type === "ProxyRequest" && e.status !== 200)
  ).length;
  const unseenErrors = Math.max(0, errorCount - seenLogCount);

  // Clear unseen badge when user switches to logs tab.
  useEffect(() => {
    if (tab === "logs") setSeenLogCount(errorCount);
  }, [tab, errorCount]);

  const fetchRate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    const start = Date.now();

    try {
      const resp = await apiFetch(`/rates?from=${from}&to=${to}`);
      const durationMs = Date.now() - start;
      const requestId = resp.headers.get("X-Request-ID");
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${text}`);
      }
      const data: RateResponse = await resp.json();
      setResult(data);
      setLog((prev) => [
        { id: counter, requestId, from, to, result: data, error: null, durationMs, time: new Date().toLocaleTimeString() },
        ...prev.slice(0, 19),
      ]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      setLog((prev) => [
        { id: counter, requestId: null, from, to, result: null, error: msg, durationMs: Date.now() - start, time: new Date().toLocaleTimeString() },
        ...prev.slice(0, 19),
      ]);
    } finally {
      setLoading(false);
      setCounter((c) => c + 1);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-mono">

      {/* ── Persistent tab bar ── */}
      <div className="sticky top-0 z-50 bg-gray-950 border-b border-gray-800">
        <div className="max-w-4xl mx-auto px-6 flex items-center gap-1 h-12">
          {/* Title */}
          <span className="text-purple-400 font-bold text-sm mr-4">forex-mtl</span>

          {/* Main tab */}
          <button
            onClick={() => setTab("main")}
            className={`px-4 py-1.5 rounded-t text-sm font-medium transition-colors ${
              tab === "main"
                ? "text-white border-b-2 border-purple-500"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            Dashboard
          </button>

          {/* Logs tab with SSE dot + unread badge */}
          <button
            onClick={() => setTab("logs")}
            className={`relative px-4 py-1.5 rounded-t text-sm font-medium transition-colors ${
              tab === "logs"
                ? "text-white border-b-2 border-purple-500"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            Logs
            {/* SSE connection dot */}
            <span
              className={`ml-1.5 inline-block w-1.5 h-1.5 rounded-full align-middle ${
                connected ? "bg-green-400" : "bg-red-500"
              }`}
            />
            {/* Unread error badge */}
            {unseenErrors > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-600 text-white text-[10px] font-bold rounded-full min-w-[16px] h-4 flex items-center justify-center px-1">
                {unseenErrors > 99 ? "99+" : unseenErrors}
              </span>
            )}
          </button>

          {/* Spacer pushes logo + sign-out to the far right */}
          <div className="flex-1" />

          {/* Sign out */}
          <button
            onClick={() => logout()}
            className="text-xs text-gray-500 hover:text-gray-300 px-2 transition-colors"
          >
            Sign out
          </button>

          {/* Paidy logo — right-aligned */}
          <img src={paidyLogo} alt="Paidy" className="h-6 ml-4 object-contain bg-white rounded px-1" />
        </div>
      </div>

      {/* ── Main tab ── always mounted, hidden when logs active */}
      <div className={tab === "main" ? "" : "hidden"}>
        <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">

          {/* Live stats + cache refresh interval */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <StatsPanel />
            <RefreshControl />
          </div>

          {/* Query form */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">FROM</label>
                <select
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 focus:outline-none focus:border-purple-500"
                  value={from}
                  onChange={(e) => setFrom(e.target.value as Currency)}
                >
                  {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div className="text-gray-600 pb-2 text-lg">→</div>

              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">TO</label>
                <select
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-100 focus:outline-none focus:border-purple-500"
                  value={to}
                  onChange={(e) => setTo(e.target.value as Currency)}
                >
                  {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <button
                onClick={fetchRate}
                disabled={loading}
                className="px-6 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 rounded-lg font-semibold transition-colors"
              >
                {loading ? "…" : "Get Rate"}
              </button>
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className="bg-gray-900 rounded-xl p-6 border border-cyan-800">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-xs text-gray-500 mb-1">EXCHANGE RATE</div>
                  <div className="text-3xl font-bold text-cyan-400">{result.price}</div>
                  <div className="text-gray-400 text-sm mt-1">
                    1 {result.from} = {result.price} {result.to}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-500">TIMESTAMP</div>
                  <div className="text-xs text-gray-400 mt-1">{result.timestamp}</div>
                  {log[0]?.requestId && (
                    <div className="text-xs text-gray-600 mt-1">id: {log[0].requestId}</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-950 border border-red-800 rounded-xl p-4 text-red-300 text-sm">
              {error}
            </div>
          )}

          {/* Request log */}
          {log.length > 0 && (
            <div className="bg-gray-900 rounded-xl border border-gray-800">
              <div className="px-4 py-3 border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                Request Log
              </div>
              <div className="divide-y divide-gray-800">
                {log.map((entry) => (
                  <div key={entry.id} className="px-4 py-3 flex justify-between text-sm gap-3">
                    <span className="text-gray-300 shrink-0">{entry.from} → {entry.to}</span>
                    {entry.result ? (
                      <span className="text-cyan-400">{entry.result.price}</span>
                    ) : (
                      <span className="text-red-400">error</span>
                    )}
                    {entry.requestId && (
                      <span className="text-gray-600 text-xs shrink-0">[{entry.requestId}]</span>
                    )}
                    <span className="text-gray-600 shrink-0">{entry.durationMs}ms</span>
                    <span className="text-gray-600 shrink-0">{entry.time}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <BurstTest />
          <RateLimitStressTest />
          <AllPairsGrid />
          <RateLimitCalculator />
          <FreshnessBar />
          <ForceRefresh />
          <RaceConditionTest />
          <ValidationMatrix />

        </div>
      </div>

      {/* ── Logs tab ── always mounted, hidden when main active */}
      <div className={tab === "logs" ? "" : "hidden"}>
        <div className="max-w-4xl mx-auto px-6 py-6">
          <EventLog />
        </div>
      </div>

    </div>
  );
}
