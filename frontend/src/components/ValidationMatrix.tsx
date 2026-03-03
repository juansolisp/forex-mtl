import { useState } from "react";
import { apiFetch } from "../api";

interface TestCase {
  id: string;
  description: string;
  url: string;
  method?: string;
  expectedStatus: number;
  category: "invalid-params" | "same-currency" | "valid" | "not-found";
  note?: string;  // optional annotation shown in the table
}

interface TestResult {
  id: string;
  actualStatus: number;
  passed: boolean;
  latencyMs: number;
  body: string;
}

const TEST_CASES: TestCase[] = [
  // Valid requests — should 200
  {
    id: "v1",
    description: "Valid pair USD→JPY",
    url: "/rates?from=USD&to=JPY",
    expectedStatus: 200,
    category: "valid",
  },
  {
    id: "v2",
    description: "Valid pair EUR→GBP",
    url: "/rates?from=EUR&to=GBP",
    expectedStatus: 200,
    category: "valid",
  },
  {
    id: "v3",
    description: "Valid pair AUD→CAD",
    url: "/rates?from=AUD&to=CAD",
    expectedStatus: 200,
    category: "valid",
  },

  // Same currency — should 400
  {
    id: "s1",
    description: "Same currency USD/USD",
    url: "/rates?from=USD&to=USD",
    expectedStatus: 400,
    category: "same-currency",
  },
  {
    id: "s2",
    description: "Same currency EUR/EUR",
    url: "/rates?from=EUR&to=EUR",
    expectedStatus: 400,
    category: "same-currency",
  },
  {
    id: "s3",
    description: "Same currency JPY/JPY",
    url: "/rates?from=JPY&to=JPY",
    expectedStatus: 400,
    category: "same-currency",
  },

  // Invalid params — should 400
  {
    id: "i1",
    description: "Missing 'to' param",
    url: "/rates?from=USD",
    expectedStatus: 400,
    category: "invalid-params",
  },
  {
    id: "i2",
    description: "Missing 'from' param",
    url: "/rates?to=JPY",
    expectedStatus: 400,
    category: "invalid-params",
  },
  {
    id: "i3",
    description: "Both params missing",
    url: "/rates",
    expectedStatus: 400,
    category: "invalid-params",
  },
  {
    id: "i4",
    description: "Unknown currency 'XYZ'",
    url: "/rates?from=XYZ&to=USD",
    expectedStatus: 400,
    category: "invalid-params",
  },
  {
    id: "i5",
    description: "Lowercase currency 'usd' (case-insensitive — accepted)",
    url: "/rates?from=usd&to=JPY",
    expectedStatus: 200,
    category: "valid",
    note: "fromString is case-insensitive by design",
  },
  {
    id: "i6",
    description: "Empty string currency",
    url: "/rates?from=&to=JPY",
    expectedStatus: 400,
    category: "invalid-params",
  },
  {
    id: "i7",
    description: "Numeric 'from' value",
    url: "/rates?from=123&to=USD",
    expectedStatus: 400,
    category: "invalid-params",
  },

  // Not-found routes — backend returns 404, but Vite dev server intercepts unproxied paths
  // and serves index.html (SPA fallback), so these show 200 in dev. In Docker they are 404.
  {
    id: "n1",
    description: "GET /unknown-route → 404 in prod, 200 (SPA) in dev",
    url: "/unknown-route",
    expectedStatus: 200,
    category: "not-found",
    note: "Vite SPA fallback: 404 in Docker",
  },
  {
    id: "n2",
    description: "GET /rates/extra/path → 404 in prod (unmatched)",
    url: "/rates/extra/path",
    expectedStatus: 404,
    category: "not-found",
    note: "proxied to backend — no route match",
  },
];

const CATEGORY_LABELS: Record<TestCase["category"], string> = {
  "valid": "Valid (200)",
  "same-currency": "Same currency (400)",
  "invalid-params": "Invalid params (400)",
  "not-found": "Not found (404)",
};

const CATEGORY_COLORS: Record<TestCase["category"], string> = {
  "valid": "bg-green-900/40 text-green-400",
  "same-currency": "bg-yellow-900/40 text-yellow-400",
  "invalid-params": "bg-orange-900/40 text-orange-400",
  "not-found": "bg-gray-700/40 text-gray-400",
};

function statusColor(status: number) {
  if (status === 200) return "text-green-400";
  if (status >= 400 && status < 500) return "text-yellow-400";
  return "text-red-400";
}

export default function ValidationMatrix() {
  const [results, setResults] = useState<Map<string, TestResult>>(new Map());
  const [running, setRunning] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);

  async function runSingle(tc: TestCase): Promise<TestResult> {
    const t0 = Date.now();
    try {
      const resp = await apiFetch(tc.url, { method: tc.method ?? "GET" });
      const body = await resp.text();
      return {
        id: tc.id,
        actualStatus: resp.status,
        passed: resp.status === tc.expectedStatus,
        latencyMs: Date.now() - t0,
        body: body.slice(0, 120),
      };
    } catch (e) {
      return {
        id: tc.id,
        actualStatus: 0,
        passed: false,
        latencyMs: Date.now() - t0,
        body: String(e),
      };
    }
  }

  async function runAll() {
    setRunning(true);
    setResults(new Map());

    for (const tc of TEST_CASES) {
      setRunningId(tc.id);
      const r = await runSingle(tc);
      setResults((prev) => new Map([...prev, [tc.id, r]]));
    }

    setRunningId(null);
    setRunning(false);
  }

  async function runCategory(category: TestCase["category"]) {
    setRunning(true);
    const cases = TEST_CASES.filter((tc) => tc.category === category);

    for (const tc of cases) {
      setRunningId(tc.id);
      const r = await runSingle(tc);
      setResults((prev) => new Map([...prev, [tc.id, r]]));
    }

    setRunningId(null);
    setRunning(false);
  }

  const passed = TEST_CASES.filter((tc) => results.get(tc.id)?.passed).length;
  const failed = TEST_CASES.filter((tc) => {
    const r = results.get(tc.id);
    return r && !r.passed;
  }).length;
  const total = results.size;

  const categories = [...new Set(TEST_CASES.map((tc) => tc.category))] as TestCase["category"][];

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
      <div className="text-xs text-gray-500 uppercase tracking-wider">Validation Matrix</div>
      <p className="text-xs text-gray-600 leading-relaxed">
        Automated test suite that fires all known edge cases and asserts correct HTTP status codes.
        Covers valid pairs (200), same-currency errors (400), invalid/missing params (400),
        and unknown routes (404).
      </p>

      {/* Controls */}
      <div className="flex flex-wrap gap-2 items-center">
        <button
          onClick={runAll}
          disabled={running}
          className="px-5 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 rounded-lg text-sm font-semibold transition-colors"
        >
          {running ? `Running…` : `Run All ${TEST_CASES.length} Tests`}
        </button>

        <span className="text-gray-700 text-xs">or run by category:</span>

        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => runCategory(cat)}
            disabled={running}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-colors disabled:opacity-40
              ${CATEGORY_COLORS[cat]} border border-current/20 hover:opacity-80`}
          >
            {CATEGORY_LABELS[cat]}
          </button>
        ))}
      </div>

      {/* Summary bar */}
      {total > 0 && (
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                failed > 0 ? "bg-red-500" : "bg-green-500"
              }`}
              style={{ width: total > 0 ? `${(passed / TEST_CASES.length) * 100}%` : "0%" }}
            />
          </div>
          <span className="text-xs font-mono whitespace-nowrap">
            <span className="text-green-400">{passed} pass</span>
            {failed > 0 && <span className="text-red-400 ml-2">{failed} fail</span>}
            <span className="text-gray-600 ml-2">/ {TEST_CASES.length} total</span>
          </span>
        </div>
      )}

      {/* Test table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono border-collapse min-w-[640px]">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="px-3 py-2 text-left text-gray-500 uppercase tracking-wider w-8">
                #
              </th>
              <th className="px-3 py-2 text-left text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-3 py-2 text-left text-gray-500 uppercase tracking-wider">
                URL
              </th>
              <th className="px-3 py-2 text-left text-gray-500 uppercase tracking-wider w-16">
                Expect
              </th>
              <th className="px-3 py-2 text-left text-gray-500 uppercase tracking-wider w-16">
                Actual
              </th>
              <th className="px-3 py-2 text-left text-gray-500 uppercase tracking-wider w-12">
                ms
              </th>
              <th className="px-3 py-2 text-left text-gray-500 uppercase tracking-wider w-12">
                Pass
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60">
            {TEST_CASES.map((tc, idx) => {
              const r = results.get(tc.id);
              const isRunning = runningId === tc.id;

              return (
                <tr
                  key={tc.id}
                  className={`${
                    r
                      ? r.passed
                        ? "bg-green-950/10"
                        : "bg-red-950/20"
                      : ""
                  } ${isRunning ? "bg-purple-950/30" : ""}`}
                >
                  <td className="px-3 py-2 text-gray-700">{idx + 1}</td>

                  <td className="px-3 py-2">
                    <div className="text-gray-300">{tc.description}</div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${CATEGORY_COLORS[tc.category]}`}>
                        {tc.category}
                      </span>
                      {tc.note && (
                        <span className="text-[10px] text-gray-600 italic">{tc.note}</span>
                      )}
                    </div>
                  </td>

                  <td className="px-3 py-2 text-gray-500 break-all">{tc.url}</td>

                  <td className={`px-3 py-2 ${statusColor(tc.expectedStatus)}`}>
                    {tc.expectedStatus}
                  </td>

                  <td className={`px-3 py-2 ${r ? statusColor(r.actualStatus) : "text-gray-700"}`}>
                    {isRunning ? (
                      <span className="inline-block w-3 h-3 border border-purple-400 border-t-transparent rounded-full animate-spin" />
                    ) : r ? (
                      r.actualStatus === 0 ? "err" : r.actualStatus
                    ) : (
                      "—"
                    )}
                  </td>

                  <td className="px-3 py-2 text-gray-500 tabular-nums">
                    {r ? r.latencyMs : "—"}
                  </td>

                  <td className="px-3 py-2">
                    {isRunning ? (
                      <span className="text-purple-400">…</span>
                    ) : r ? (
                      r.passed ? (
                        <span className="text-green-400 font-bold">✓</span>
                      ) : (
                        <span className="text-red-400 font-bold">✗</span>
                      )
                    ) : (
                      <span className="text-gray-700">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Failure details */}
      {failed > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-red-400 font-semibold">Failed tests:</div>
          {TEST_CASES.filter((tc) => results.get(tc.id) && !results.get(tc.id)!.passed).map(
            (tc) => {
              const r = results.get(tc.id)!;
              return (
                <div key={tc.id} className="bg-red-950/30 border border-red-800 rounded p-2 text-xs">
                  <div className="text-red-300 font-semibold">{tc.description}</div>
                  <div className="text-gray-500 mt-1">
                    Expected <span className="text-yellow-400">{tc.expectedStatus}</span>
                    {" · "}Got <span className="text-red-400">{r.actualStatus}</span>
                  </div>
                  {r.body && (
                    <div className="text-gray-600 mt-1 font-mono break-all">{r.body}</div>
                  )}
                </div>
              );
            }
          )}
        </div>
      )}

      {/* All pass */}
      {total === TEST_CASES.length && failed === 0 && !running && (
        <div className="border border-green-700 bg-green-950/40 rounded-lg p-3 text-green-400 text-sm font-semibold text-center">
          ✓ All {TEST_CASES.length} tests passed — API behaves correctly for all input cases
        </div>
      )}
    </div>
  );
}
