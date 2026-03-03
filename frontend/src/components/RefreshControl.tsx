import { useState } from "react";
import { useRefreshInterval, setRefreshInterval } from "../hooks/useRefreshInterval";

const PRESETS = [
  { label: "90s",  seconds: 90  },
  { label: "2m",   seconds: 120 },
  { label: "3m",   seconds: 180 },
  { label: "4m",   seconds: 240 },
  { label: "5m",   seconds: 300 },
] as const;

export default function RefreshControl() {
  const current = useRefreshInterval();
  const [pending, setPending] = useState<number | null>(null);
  const [error, setError]     = useState<string | null>(null);

  async function apply(seconds: number) {
    setPending(seconds);
    setError(null);
    try {
      await setRefreshInterval(seconds);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "request failed");
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-500 uppercase tracking-wider">
          Cache Refresh Interval
        </span>
        <span className="text-xs text-gray-600">
          current:{" "}
          <span className="text-purple-400 font-mono">{current}s</span>
        </span>
      </div>

      <div className="flex gap-2">
        {PRESETS.map(({ label, seconds }) => {
          const isActive  = current === seconds;
          const isPending = pending === seconds;
          return (
            <button
              key={seconds}
              onClick={() => apply(seconds)}
              disabled={pending !== null}
              className={`flex-1 py-2 rounded-lg text-sm font-mono font-semibold transition-colors
                ${isActive
                  ? "bg-purple-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200"}
                disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isPending ? "…" : label}
            </button>
          );
        })}
      </div>

      {error && (
        <div className="mt-2 text-xs text-red-400">{error}</div>
      )}

      <div className="mt-2 text-[11px] text-gray-700">
        resets the refresh timer immediately · valid range 90s – 5m
      </div>
    </div>
  );
}
