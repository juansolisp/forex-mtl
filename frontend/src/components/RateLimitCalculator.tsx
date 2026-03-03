import { useState, useMemo } from "react";
import { useRefreshInterval, setRefreshInterval } from "../hooks/useRefreshInterval";

const ONE_FRAME_DAILY_LIMIT = 1000;
const SECONDS_PER_DAY = 86400;

const PRESETS = [
  { label: "90s",  seconds: 90  },
  { label: "2m",   seconds: 120 },
  { label: "3m",   seconds: 180 },
  { label: "4m",   seconds: 240 },
  { label: "5m",   seconds: 300 },
] as const;

export default function RateLimitCalculator() {
  const currentInterval = useRefreshInterval();
  // customSeconds drives the simulation slider independently of the live server value.
  // Starts null so the slider initialises from currentInterval on first render.
  const [customSeconds, setCustomSeconds] = useState<number | null>(null);

  const displaySeconds = customSeconds ?? currentInterval;

  const stats = useMemo(() => {
    const s = displaySeconds;
    const callsPerDay  = Math.floor(SECONDS_PER_DAY / s);
    const callsPerHour = Math.floor(3600 / s);
    const pctOfLimit   = (callsPerDay / ONE_FRAME_DAILY_LIMIT) * 100;
    const headroom     = ONE_FRAME_DAILY_LIMIT - callsPerDay;
    return { callsPerDay, callsPerHour, pctOfLimit, headroom };
  }, [displaySeconds]);

  const barColor =
    stats.pctOfLimit > 90 ? "bg-red-500" :
    stats.pctOfLimit > 60 ? "bg-yellow-500" : "bg-green-500";

  const textColor =
    stats.pctOfLimit > 90 ? "text-red-400" :
    stats.pctOfLimit > 60 ? "text-yellow-400" : "text-green-400";

  async function applyToServer() {
    const s = displaySeconds;
    if (s < 90 || s > 300) return;
    try {
      await setRefreshInterval(s);
      setCustomSeconds(null); // snap back to tracking server value
    } catch { /* ignore */ }
  }

  const isDirty = customSeconds !== null && customSeconds !== currentInterval;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider">Rate Limit Calculator</div>
      <p className="text-xs text-gray-600 leading-relaxed">
        One-Frame enforces 1 000 calls/day. Adjust the refresh interval to see how many calls
        the proxy would make and how much headroom remains.
      </p>

      {/* Preset buttons */}
      <div>
        <div className="text-xs text-gray-500 mb-2">
          Presets
          <span className="ml-2 text-gray-700">
            (server: <span className="text-purple-400">{currentInterval}s</span>)
          </span>
        </div>
        <div className="flex gap-2 flex-wrap">
          {PRESETS.map(({ label, seconds }) => (
            <button
              key={seconds}
              onClick={() => setCustomSeconds(seconds)}
              className={`px-3 py-1.5 rounded text-sm font-mono transition-colors
                ${displaySeconds === seconds
                  ? "bg-purple-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Custom slider */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Custom interval</span>
          <span className="font-mono text-gray-300">{displaySeconds}s</span>
        </div>
        <input
          type="range"
          min={60}
          max={600}
          step={10}
          value={displaySeconds}
          onChange={(e) => setCustomSeconds(Number(e.target.value))}
          className="w-full accent-purple-500"
        />
        <div className="flex justify-between text-[10px] text-gray-700 mt-0.5">
          <span>60s</span>
          <span>600s</span>
        </div>
      </div>

      {/* Usage bar */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-500">Daily API usage</span>
          <span className={`font-mono font-bold ${textColor}`}>
            {stats.callsPerDay} / {ONE_FRAME_DAILY_LIMIT} calls ({stats.pctOfLimit.toFixed(1)}%)
          </span>
        </div>
        <div className="h-4 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${barColor}`}
            style={{ width: `${Math.min(100, stats.pctOfLimit)}%` }}
          />
        </div>
        {stats.pctOfLimit > 100 && (
          <div className="text-xs text-red-400 mt-1">
            ✗ Exceeds 1 000/day limit — One-Frame will reject requests
          </div>
        )}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <CalcBox label="Calls / day"   value={String(stats.callsPerDay)}  color={textColor} />
        <CalcBox label="Calls / hour"  value={String(stats.callsPerHour)} color="text-cyan-400" />
        <CalcBox
          label="Headroom"
          value={String(stats.headroom)}
          color={stats.headroom > 0 ? "text-green-400" : "text-red-400"}
          sub="calls remaining"
        />
        <CalcBox label="Max proxy RPS" value="unlimited" color="text-purple-400" sub="cache absorbs all" />
      </div>

      {/* Apply to server — only shown when slider diverges from live value */}
      {isDirty && (
        <div className="flex items-center gap-3 text-xs text-gray-500 bg-gray-800 rounded-lg p-3">
          <span>
            Simulating <span className="text-gray-300 font-mono">{displaySeconds}s</span>.
            Server is at <span className="text-purple-400 font-mono">{currentInterval}s</span>.
          </span>
          <button
            onClick={applyToServer}
            disabled={displaySeconds < 90 || displaySeconds > 300}
            className="ml-auto px-3 py-1 bg-purple-700 hover:bg-purple-600 disabled:bg-gray-700 disabled:text-gray-600 rounded text-xs font-semibold transition-colors"
          >
            Apply to server
          </button>
        </div>
      )}

      {/* Key insight */}
      <div className="text-[11px] text-gray-700 border-t border-gray-800 pt-3">
        At the default 240s (4 min): {Math.floor(86400 / 240)} calls/day — well below the 1 000 limit,
        with {1000 - Math.floor(86400 / 240)} calls/day headroom for manual operations.
        The 5-minute SLA requires ≥ 1 refresh every 300s, so the valid range is 90–300s.
      </div>
    </div>
  );
}

function CalcBox({ label, value, color, sub }: { label: string; value: string; color: string; sub?: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-xl font-bold font-mono ${color}`}>{value}</div>
      {sub && <div className="text-[10px] text-gray-600 mt-0.5">{sub}</div>}
    </div>
  );
}
