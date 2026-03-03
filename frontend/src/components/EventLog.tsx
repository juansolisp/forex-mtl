import { useState, useRef, useEffect, useMemo, useCallback, Fragment } from "react";
import {
  useEventStream,
  clearEvents,
  getSeq,
  type LogEntry,
  type ProxyRequestEvent,
  type CacheRefreshEvent,
  type CacheRefreshFailedEvent,
} from "../hooks/useEventStream";

// ─── Types ────────────────────────────────────────────────────────────────────

type SortKey =
  | "#"
  | "time"
  | "type"
  | "pair"
  | "status"
  | "duration"
  | "price";

type SortDir = "asc" | "desc";

type FilterType = "all" | "req" | "cache" | "errors" | "failed";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function statusColor(status: number) {
  if (status === 200) return "text-green-400";
  if (status >= 400 && status < 500) return "text-yellow-400";
  return "text-red-400";
}

function durationColor(ms: number) {
  if (ms < 1) return "text-green-400";
  if (ms < 5) return "text-cyan-400";
  if (ms < 50) return "text-yellow-400";
  return "text-red-400";
}

function fmtDuration(ms: number): string {
  if (ms < 1) return ms.toFixed(3);
  if (ms < 10) return ms.toFixed(2);
  if (ms < 100) return ms.toFixed(1);
  return Math.round(ms).toString();
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "2-digit",
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function isProxyRequest(e: LogEntry): e is ProxyRequestEvent {
  return e.type === "ProxyRequest";
}

function isCacheRefresh(e: LogEntry): e is CacheRefreshEvent {
  return e.type === "CacheRefresh";
}

function isCacheRefreshFailed(e: LogEntry): e is CacheRefreshFailedEvent {
  return e.type === "CacheRefreshFailed";
}

function getSortValue(entry: LogEntry, key: SortKey): number | string {
  switch (key) {
    case "#":       return getSeq(entry);
    case "time":    return entry.timestamp;
    case "type":    return entry.type;
    case "pair":    return isProxyRequest(entry) ? `${entry.from}/${entry.to}` : "—";
    case "status":  return isProxyRequest(entry) ? entry.status : isCacheRefreshFailed(entry) ? -1 : 0;
    case "duration": return entry.durationMs;
    case "price":   return isProxyRequest(entry) ? (entry.price ?? -1) : -1;
    default:        return 0;
  }
}

// ─── Detail drawer ────────────────────────────────────────────────────────────

function DetailDrawer({ entry, seq, onClose }: { entry: LogEntry; seq: number; onClose: () => void }) {
  const isReq    = isProxyRequest(entry);
  const isFailed = isCacheRefreshFailed(entry);

  const requestJson = isReq
    ? JSON.stringify({
        method: "GET",
        url: `/rates?from=${entry.from}&to=${entry.to}`,
        headers: { Accept: "application/json" },
      }, null, 2)
    : null;

  const responseBody = isReq
    ? entry.status === 200
      ? { from: entry.from, to: entry.to, price: entry.price, timestamp: entry.timestamp }
      : { error: entry.errorBody }
    : null;

  const responseJson = isReq
    ? JSON.stringify({
        status: entry.status,
        headers: { "Content-Type": "application/json", "X-Request-ID": entry.id },
        body: responseBody,
      }, null, 2)
    : isFailed
    ? JSON.stringify({
        event: "CacheRefreshFailed",
        reason: entry.reason,
        timestamp: entry.timestamp,
      }, null, 2)
    : JSON.stringify({
        event: "CacheRefresh",
        pairsCount: (entry as CacheRefreshEvent).pairsCount,
        durationMs: entry.durationMs,
        timestamp: entry.timestamp,
      }, null, 2);

  const sseRaw = JSON.stringify(
    isReq
      ? { type: entry.type, id: entry.id, from: entry.from, to: entry.to,
          status: entry.status, price: entry.price, errorBody: entry.errorBody,
          durationMs: entry.durationMs, timestamp: entry.timestamp }
      : isFailed
      ? { type: entry.type, reason: entry.reason, timestamp: entry.timestamp }
      : { type: entry.type, pairsCount: (entry as CacheRefreshEvent).pairsCount,
          durationMs: entry.durationMs, timestamp: entry.timestamp },
    null, 2
  );

  return (
    <div className="border-t border-gray-700 bg-gray-950 text-xs font-mono">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <span className="text-gray-400 font-semibold">
          Event #{seq} detail
          {isReq && <span className="ml-2 text-gray-600">id: {entry.id}</span>}
        </span>
        <button onClick={onClose} className="text-gray-600 hover:text-gray-300 text-sm leading-none px-1">
          ✕
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-0 divide-y lg:divide-y-0 lg:divide-x divide-gray-800">
        <div className="p-3">
          <div className="text-gray-600 uppercase tracking-wider text-[10px] mb-2">
            {isReq ? "HTTP Request" : "Trigger"}
          </div>
          <pre className="text-green-300 whitespace-pre-wrap break-all leading-relaxed">
            {requestJson ?? `— internal cache event\n  not triggered by an HTTP request`}
          </pre>
        </div>

        <div className="p-3">
          <div className="text-gray-600 uppercase tracking-wider text-[10px] mb-2">
            {isReq ? "HTTP Response" : "Event Payload"}
          </div>
          <pre className="text-cyan-300 whitespace-pre-wrap break-all leading-relaxed">
            {responseJson}
          </pre>
        </div>

        <div className="p-3">
          <div className="text-gray-600 uppercase tracking-wider text-[10px] mb-2">
            SSE Frame (raw)
          </div>
          <pre className="text-purple-300 whitespace-pre-wrap break-all leading-relaxed">
            {"data: " + sseRaw}
          </pre>
        </div>
      </div>

      <div className="px-4 py-2 border-t border-gray-800 flex gap-6 text-gray-500 flex-wrap">
        <span>timestamp: <span className="text-gray-300">{fmtDate(entry.timestamp)}</span></span>
        <span>duration: <span className={durationColor(entry.durationMs)}>{fmtDuration(entry.durationMs)}ms</span></span>
        {isReq && <span>status: <span className={statusColor(entry.status)}>{entry.status}</span></span>}
        {isReq && entry.price != null && <span>price: <span className="text-cyan-400">{entry.price}</span></span>}
        {isCacheRefresh(entry) && <span>pairs: <span className="text-green-400">{entry.pairsCount}</span></span>}
        {isFailed && <span>reason: <span className="text-orange-400">{entry.reason}</span></span>}
      </div>
    </div>
  );
}

// ─── Column header ────────────────────────────────────────────────────────────

function ColHeader({ label, sortKey, current, dir, onSort, className = "" }: {
  label: string; sortKey: SortKey; current: SortKey; dir: SortDir;
  onSort: (k: SortKey) => void; className?: string;
}) {
  const active = current === sortKey;
  return (
    <th
      className={`px-3 py-2 text-left select-none cursor-pointer whitespace-nowrap text-[11px] uppercase tracking-wider font-medium
        ${active ? "text-purple-400" : "text-gray-500"} hover:text-gray-300 transition-colors ${className}`}
      onClick={() => onSort(sortKey)}
    >
      {label}
      <span className="ml-1 opacity-60">{active ? (dir === "asc" ? "↑" : "↓") : "⇅"}</span>
    </th>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function EventLog() {
  const { entries, connected } = useEventStream();

  const [sortKey, setSortKey] = useState<SortKey>("#");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filterType, setFilterType] = useState<FilterType>("all");
  const [filterText, setFilterText] = useState("");
  const [expandedEntry, setExpandedEntry] = useState<LogEntry | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [paused, setPaused] = useState(false);
  const [pageSize, setPageSize] = useState(100);

  const frozenRef = useRef<LogEntry[]>([]);
  const liveEntries = paused ? frozenRef.current : entries;

  const handlePause = useCallback(() => {
    if (!paused) frozenRef.current = entries;
    setPaused((p) => !p);
  }, [paused, entries]);

  const tableContainerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (autoScroll && !paused && sortKey === "#" && sortDir === "desc") {
      const el = tableContainerRef.current;
      if (el) el.scrollTop = el.scrollHeight;
    }
  }, [entries, autoScroll, paused, sortKey, sortDir]);

  const handleSort = useCallback((key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "#" || key === "time" ? "desc" : "asc");
    }
  }, [sortKey]);

  const { sorted, paginated, stats } = useMemo(() => {
    const text = filterText.trim().toLowerCase();

    const filtered = liveEntries.filter((e) => {
      if (filterType === "req"    && !isProxyRequest(e)) return false;
      if (filterType === "cache"  && !isCacheRefresh(e)) return false;
      if (filterType === "errors" && !(isProxyRequest(e) && e.status !== 200)) return false;
      if (filterType === "failed" && !isCacheRefreshFailed(e)) return false;
      if (text) {
        if (isProxyRequest(e)) {
          return (
            e.from.toLowerCase().includes(text) ||
            e.to.toLowerCase().includes(text) ||
            e.id.toLowerCase().includes(text) ||
            String(e.status).includes(text) ||
            String(e.durationMs).includes(text) ||
            (e.price != null && String(e.price).includes(text))
          );
        } else if (isCacheRefreshFailed(e)) {
          return e.reason.toLowerCase().includes(text);
        } else {
          return String((e as CacheRefreshEvent).pairsCount).includes(text);
        }
      }
      return true;
    });

    const sorted = [...filtered].sort((a, b) => {
      const av = getSortValue(a, sortKey);
      const bv = getSortValue(b, sortKey);
      let cmp = typeof av === "number" && typeof bv === "number"
        ? av - bv
        : String(av).localeCompare(String(bv));
      return sortDir === "asc" ? cmp : -cmp;
    });

    const reqs = liveEntries.filter(isProxyRequest);
    const stats = {
      total: liveEntries.length,
      requests: reqs.length,
      cacheEvents: liveEntries.filter(isCacheRefresh).length,
      errors: reqs.filter((e) => e.status !== 200).length,
      failed: liveEntries.filter(isCacheRefreshFailed).length,
      filtered: filtered.length,
      avgDuration: reqs.length > 0
        ? Math.round(reqs.reduce((s, e) => s + e.durationMs, 0) / reqs.length)
        : null,
    };

    return { sorted, paginated: sorted.slice(0, pageSize), stats };
  }, [liveEntries, filterType, filterText, sortKey, sortDir, pageSize]);

  const handleClear = () => {
    clearEvents();
    setExpandedEntry(null);
    setPaused(false);
  };

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">

      {/* ── Toolbar ── */}
      <div className="px-4 py-3 border-b border-gray-800 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Event Log</span>
          <span
            className={`w-2 h-2 rounded-full ${connected ? "bg-green-400 shadow-[0_0_6px_#4ade80]" : "bg-red-500"}`}
            title={connected ? "SSE connected" : "SSE disconnected"}
          />
        </div>

        <div className="flex gap-1.5 flex-wrap text-[11px]">
          <span className="bg-gray-800 rounded px-2 py-0.5 text-gray-400">{stats.total} total</span>
          <span className="bg-blue-900/40 text-blue-300 rounded px-2 py-0.5">{stats.requests} req</span>
          <span className="bg-green-900/40 text-green-300 rounded px-2 py-0.5">{stats.cacheEvents} cache</span>
          {stats.errors > 0 && (
            <span className="bg-red-900/40 text-red-300 rounded px-2 py-0.5">{stats.errors} errors</span>
          )}
          {stats.failed > 0 && (
            <span className="bg-orange-900/40 text-orange-300 rounded px-2 py-0.5">{stats.failed} failed</span>
          )}
          {stats.avgDuration !== null && (
            <span className="bg-gray-800 rounded px-2 py-0.5 text-gray-500">avg {stats.avgDuration}ms</span>
          )}
        </div>

        <div className="flex-1" />

        <div className="flex gap-1 text-[11px]">
          {(["all", "req", "cache", "errors", "failed"] as FilterType[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilterType(f)}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterType === f ? "bg-purple-700 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="filter…"
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 placeholder-gray-600 focus:outline-none focus:border-purple-600 w-28"
        />

        <select
          value={pageSize}
          onChange={(e) => setPageSize(Number(e.target.value))}
          className="bg-gray-800 border border-gray-700 rounded px-1.5 py-1 text-xs text-gray-400 focus:outline-none"
        >
          {[25, 50, 100, 250, 500, 1000, 2000].map((n) => (
            <option key={n} value={n}>{n} rows</option>
          ))}
        </select>

        <button
          onClick={() => setAutoScroll((a) => !a)}
          className={`px-2 py-1 rounded text-[11px] transition-colors ${
            autoScroll ? "bg-purple-800/60 text-purple-300" : "bg-gray-800 text-gray-500 hover:bg-gray-700"
          }`}
        >
          ↓ auto
        </button>

        <button
          onClick={handlePause}
          className={`px-2 py-1 rounded text-[11px] transition-colors ${
            paused ? "bg-yellow-800/60 text-yellow-300" : "bg-gray-800 text-gray-500 hover:bg-gray-700"
          }`}
        >
          {paused ? "▶ resume" : "⏸ pause"}
        </button>

        <button
          onClick={handleClear}
          className="px-2 py-1 rounded text-[11px] bg-gray-800 text-gray-500 hover:bg-red-900/40 hover:text-red-400 transition-colors"
        >
          ✕ clear
        </button>
      </div>

      {/* ── Table ── */}
      <div ref={tableContainerRef} className="overflow-x-auto overflow-y-auto max-h-[960px] relative">
        {paused && (
          <div className="sticky top-0 z-10 bg-yellow-900/80 text-yellow-300 text-xs text-center py-1 backdrop-blur-sm">
            ⏸ paused — showing {liveEntries.length} frozen events
          </div>
        )}

        {paginated.length === 0 ? (
          <div className="py-12 text-center text-xs text-gray-600">
            {filterText || filterType !== "all"
              ? `No events match the current filter (${stats.total} total)`
              : "Waiting for events…"}
          </div>
        ) : (
          <table className="w-full text-xs font-mono border-collapse min-w-[700px]">
            <thead className="sticky top-0 bg-gray-900 z-10 border-b border-gray-700">
              <tr>
                <ColHeader label="#"        sortKey="#"        current={sortKey} dir={sortDir} onSort={handleSort} className="w-12" />
                <ColHeader label="Time"     sortKey="time"     current={sortKey} dir={sortDir} onSort={handleSort} className="w-20" />
                <ColHeader label="Type"     sortKey="type"     current={sortKey} dir={sortDir} onSort={handleSort} className="w-16" />
                <ColHeader label="Pair"     sortKey="pair"     current={sortKey} dir={sortDir} onSort={handleSort} className="w-20" />
                <ColHeader label="Status"   sortKey="status"   current={sortKey} dir={sortDir} onSort={handleSort} className="w-16" />
                <ColHeader label="Duration" sortKey="duration" current={sortKey} dir={sortDir} onSort={handleSort} className="w-20" />
                <ColHeader label="Price"    sortKey="price"    current={sortKey} dir={sortDir} onSort={handleSort} className="w-28" />
                <th className="px-3 py-2 text-left text-[11px] uppercase tracking-wider font-medium text-gray-500 whitespace-nowrap w-24">
                  Req ID
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {paginated.map((entry) => {
                const seq = getSeq(entry);
                const expanded = expandedEntry === entry;
                const isError = (isProxyRequest(entry) && entry.status !== 200) || isCacheRefreshFailed(entry);

                return (
                  <Fragment key={seq}>
                    <tr
                      onClick={() => setExpandedEntry(expanded ? null : entry)}
                      className={`cursor-pointer transition-colors ${
                        expanded ? "bg-gray-800" : "hover:bg-gray-800/60"
                      } ${isError ? "bg-red-950/20" : ""}`}
                    >
                      <td className="px-3 py-2 text-gray-600 tabular-nums">{seq}</td>

                      <td className="px-3 py-2 text-gray-500 tabular-nums whitespace-nowrap">
                        {fmtTime(entry.timestamp)}
                      </td>

                      <td className="px-3 py-2">
                        {isProxyRequest(entry) ? (
                          <span className="bg-blue-900/40 text-blue-300 px-1.5 py-0.5 rounded text-[10px]">req</span>
                        ) : isCacheRefreshFailed(entry) ? (
                          <span className="bg-orange-900/40 text-orange-300 px-1.5 py-0.5 rounded text-[10px]">fail</span>
                        ) : (
                          <div className="flex flex-col gap-0.5">
                            <span className="bg-green-900/40 text-green-300 px-1.5 py-0.5 rounded text-[10px] self-start">cache</span>
                            <span className="text-gray-600 text-[10px]">{(entry as CacheRefreshEvent).pairsCount} pairs</span>
                          </div>
                        )}
                      </td>

                      <td className="px-3 py-2">
                        {isProxyRequest(entry) ? (
                          <div className="flex flex-col gap-0.5">
                            <span>
                              <span className="text-cyan-500">{entry.from}</span>
                              <span className="text-gray-600">→</span>
                              <span className="text-cyan-400">{entry.to}</span>
                            </span>
                            {entry.errorBody && (
                              <span className="text-red-400 text-[10px]" title={entry.errorBody}>
                                {entry.errorBody.length > 48 ? entry.errorBody.slice(0, 48) + "…" : entry.errorBody}
                              </span>
                            )}
                          </div>
                        ) : isCacheRefreshFailed(entry) ? (
                          <span className="text-orange-400 text-[10px]" title={entry.reason}>
                            {entry.reason.length > 60 ? entry.reason.slice(0, 60) + "…" : entry.reason}
                          </span>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>

                      <td className="px-3 py-2 tabular-nums">
                        {isProxyRequest(entry) ? (
                          <span className={statusColor(entry.status)}>{entry.status}</span>
                        ) : isCacheRefreshFailed(entry) ? (
                          <span className="text-orange-400">ERR</span>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>

                      <td className="px-3 py-2 tabular-nums">
                        <span className={durationColor(entry.durationMs)}>
                          {fmtDuration(entry.durationMs)}<span className="text-gray-600">ms</span>
                        </span>
                      </td>

                      <td className="px-3 py-2 tabular-nums">
                        {isProxyRequest(entry) ? (
                          entry.price != null ? (
                            <span className="text-cyan-400">{entry.price}</span>
                          ) : (
                            <span className="text-gray-600">—</span>
                          )
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>

                      <td className="px-3 py-2 text-gray-600">
                        {isProxyRequest(entry) ? entry.id : <span className="text-gray-700">—</span>}
                      </td>
                    </tr>

                    {expanded && (
                      <tr>
                        <td colSpan={8} className="p-0">
                          <DetailDrawer entry={entry} seq={seq} onClose={() => setExpandedEntry(null)} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Footer ── */}
      <div className="px-4 py-2 border-t border-gray-800 flex items-center justify-between text-[11px] text-gray-600">
        <span>
          {(filterText || filterType !== "all") ? `${stats.filtered} matched · ` : ""}
          showing {Math.min(pageSize, sorted.length)} of {stats.total} events
          {paused && <span className="ml-2 text-yellow-500">[paused]</span>}
        </span>
        <span>click any row to expand · all columns sortable</span>
      </div>

    </div>
  );
}
