import { useState, useRef } from "react";
import { useEventStream } from "../hooks/useEventStream";
import { apiFetch } from "../api";

const CURRENCIES = ["AUD", "CAD", "CHF", "EUR", "GBP", "JPY", "NZD", "SGD", "USD"] as const;
type Currency = (typeof CURRENCIES)[number];

type CellState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ok"; price: number }
  | { status: "error"; msg: string };

type Grid = Record<string, CellState>;

function pairKey(from: Currency, to: Currency) {
  return `${from}/${to}`;
}

/**
 * 9×9 currency pair grid.
 *
 * Clicking "Fetch All 72 Pairs" fires all requests concurrently (Promise.all).
 * All 72 responses should succeed immediately from the in-memory cache with
 * no new One-Frame calls, proving:
 *   1. All pairs are pre-fetched and stored (not just the ones queried).
 *   2. Concurrent access is race-condition free (Ref[F, Map] is atomic).
 *   3. The entire result set is served without a single upstream call.
 *
 * Diagonal cells (USD/USD etc.) are skipped — the proxy returns 400 for
 * same-currency pairs, which would clutter the grid. They are shown as "—".
 */
export default function AllPairsGrid() {
  const [grid, setGrid] = useState<Grid>({});
  const [running, setRunning] = useState(false);
  const [fetchTime, setFetchTime] = useState<number | null>(null);

  const { entries } = useEventStream();
  // Snapshot the One-Frame call count at button-click time, not render time.
  const oneFrameBeforeRef = useRef(0);

  function setCell(from: Currency, to: Currency, state: CellState) {
    setGrid((prev) => ({ ...prev, [pairKey(from, to)]: state }));
  }

  async function fetchAll() {
    setRunning(true);
    setFetchTime(null);
    oneFrameBeforeRef.current = entries.filter((e) => e.type === "CacheRefresh").length;

    // Mark all non-diagonal cells as loading immediately.
    const loadingGrid: Grid = {};
    for (const from of CURRENCIES) {
      for (const to of CURRENCIES) {
        if (from !== to) {
          loadingGrid[pairKey(from, to)] = { status: "loading" };
        }
      }
    }
    setGrid(loadingGrid);

    const start = Date.now();

    await Promise.all(
      CURRENCIES.flatMap((from) =>
        CURRENCIES.filter((to) => to !== from).map(async (to) => {
          try {
            const resp = await apiFetch(`/rates?from=${from}&to=${to}`);
            if (resp.ok) {
              const data = await resp.json();
              setCell(from, to, { status: "ok", price: data.price });
            } else {
              const text = await resp.text();
              setCell(from, to, { status: "error", msg: `${resp.status}: ${text.slice(0, 40)}` });
            }
          } catch (e) {
            setCell(from, to, { status: "error", msg: String(e).slice(0, 40) });
          }
        })
      )
    );

    setFetchTime(Date.now() - start);
    setRunning(false);
  }

  // Live delta: current count minus snapshot captured at button click.
  const oneFrameAfter = entries.filter((e) => e.type === "CacheRefresh").length;
  const delta = fetchTime !== null ? oneFrameAfter - oneFrameBeforeRef.current : null;

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-500 uppercase tracking-wider">All 72 Pairs Grid</span>
        <button
          onClick={fetchAll}
          disabled={running}
          className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 rounded-lg text-sm font-semibold transition-colors"
        >
          {running ? "Fetching…" : "Fetch All 72 Pairs"}
        </button>
      </div>

      {fetchTime !== null && (
        <div className="text-xs text-gray-600 mb-2">
          Completed in <span className="text-gray-400">{fetchTime}ms</span>
          {delta === 0 ? (
            <span className="text-green-400 ml-2">· 0 new One-Frame calls (all from cache)</span>
          ) : delta !== null ? (
            <span className="text-yellow-400 ml-2">· +{delta} One-Frame calls</span>
          ) : null}
        </div>
      )}

      {/* Column headers */}
      <div className="overflow-x-auto">
        <table className="text-xs font-mono border-collapse w-full min-w-[480px]">
          <thead>
            <tr>
              <th className="text-gray-600 p-1 text-right pr-2">FROM ↓ TO →</th>
              {CURRENCIES.map((c) => (
                <th key={c} className="text-gray-500 p-1 text-center w-12">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CURRENCIES.map((from) => (
              <tr key={from}>
                <td className="text-gray-500 p-1 text-right pr-2">{from}</td>
                {CURRENCIES.map((to) => {
                  if (from === to) {
                    return (
                      <td key={to} className="p-1 text-center text-gray-700">
                        —
                      </td>
                    );
                  }
                  const cell = grid[pairKey(from, to)];
                  return (
                    <td key={to} className="p-1 text-center">
                      <CellDisplay cell={cell} />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CellDisplay({ cell }: { cell: CellState | undefined }) {
  if (!cell || cell.status === "idle") {
    return <span className="text-gray-700">·</span>;
  }
  if (cell.status === "loading") {
    return (
      <span className="inline-block w-8 h-3 bg-gray-700 rounded animate-pulse" />
    );
  }
  if (cell.status === "ok") {
    // Format price: show up to 4 significant digits to fit in small cells.
    const formatted =
      cell.price >= 100
        ? cell.price.toFixed(1)
        : cell.price >= 10
        ? cell.price.toFixed(2)
        : cell.price.toFixed(3);
    return <span className="text-cyan-400">{formatted}</span>;
  }
  // error
  return (
    <span className="text-red-500" title={cell.msg}>
      err
    </span>
  );
}
