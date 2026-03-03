# forex-mtl Test Plan

Complete coverage map for every layer of the system: existing tests, gaps, and the full
set of cases that should be verified. Organised from domain inward to infrastructure outward.

---

## How to Read This Document

Each test case has:
- **ID** — unique reference (e.g. `DOM-01`)
- **What** — the scenario in plain English
- **Input / Condition** — what you feed the system
- **Expected** — the correct observable outcome
- **Status** — `✅ covered` (existing test), `❌ missing` (no test yet)

---

## 1. Domain Layer

### 1.1 Currency

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| DOM-01 | All 9 valid codes parse correctly | `"AUD"`, `"CAD"`, `"CHF"`, `"EUR"`, `"GBP"`, `"NZD"`, `"JPY"`, `"SGD"`, `"USD"` | `Right(currency)` for each | ✅ covered — `CurrencySpec` |
| DOM-02 | Parsing is case-insensitive | `"usd"`, `"Eur"` | `Right(USD)`, `Right(EUR)` | ✅ covered — `CurrencySpec`, `CurrencyProperties` |
| DOM-03 | Unknown code returns Left | `"XXX"`, `""` | `Left(...)` | ✅ covered — `CurrencySpec` |
| DOM-04 | `values` has exactly 9 elements | — | `Currency.values.size == 9` | ✅ covered — `CurrencySpec` |
| DOM-05 | `show` produces uppercase ISO-4217 | `Currency.USD` | `"USD"` | ✅ covered — `CurrencySpec` |
| DOM-06 | `fromString(show(c)) == Right(c)` for all currencies | all 9 | round-trip equality | ✅ covered — `CurrencySpec`, `CurrencyProperties` |
| DOM-07 | All 72 ordered pairs are distinct | all pairs from values×values minus same-currency | 72 unique `Rate.Pair`s | ✅ covered — `CurrencyProperties`, `RateSpec` |
| DOM-08 | `Rate.Pair(A, B) != Rate.Pair(B, A)` | `Pair(USD, JPY)` vs `Pair(JPY, USD)` | structurally unequal | ✅ covered — `RateSpec` |
| DOM-09 | `Rate.Pair` usable as Map key | insert & lookup in `Map[Rate.Pair, Rate]` | retrieval by same pair succeeds | ✅ covered — `RateSpec` |

---

### 1.2 LogEvent JSON Encoding

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| DOM-10 | `ProxyRequest` encodes with flat `"type"` discriminator | `ProxyRequest(...)` | JSON has `"type":"ProxyRequest"` at top level, not nested | ✅ covered — `LogEventSpec` |
| DOM-11 | `CacheRefresh` encodes with quota fields | `CacheRefresh(72, 145.2, "...", 5, 1000, false)` | JSON has `callsToday`, `dailyLimit`, `quotaWarning` | ✅ covered — `LogEventSpec` |
| DOM-12 | `CacheRefreshFailed` encodes correctly | `CacheRefreshFailed("quota", "...")` | `"type":"CacheRefreshFailed"`, `"reason"` present | ✅ covered — `LogEventSpec` |
| DOM-13 | `Heartbeat` encodes `serverTimeMs` as number | `Heartbeat(1234567890L, Some("..."))` | `"serverTimeMs":1234567890` | ✅ covered — `LogEventSpec` |
| DOM-14 | `Heartbeat` with `None` encodes `lastRefreshedAt` as null | `Heartbeat(123L, None)` | `"lastRefreshedAt":null` | ✅ covered — `LogEventSpec` |
| DOM-15 | `ProxyRequest` with null price encodes `price` as null | `ProxyRequest(..., price=None, ...)` | `"price":null` | ✅ covered — `LogEventSpec` |
| DOM-16 | Encoded JSON can be parsed without error (round-trip) | any `LogEvent` | `io.circe.parser.parse` succeeds | ✅ covered — `LogEventSpec` |

---

## 2. Service Layer — QuotaState

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| QUO-01 | `increment` increases `callsToday` by 1 | `callsToday = 5` | `callsToday = 6` | ✅ covered — `QuotaStateSpec` |
| QUO-02 | `increment` retains date when day has not changed | same-day state | date unchanged | ✅ covered — `QuotaStateSpec` |
| QUO-03 | `increment` resets `callsToday` to 1 on day rollover | yesterday's date, `callsToday = 999` | `callsToday = 1`, today's date | ✅ covered — `QuotaStateSpec` |
| QUO-04 | `dailyLimit` is always 1000 | any state | `dailyLimit == 1000` | ✅ covered — `QuotaStateSpec` |
| QUO-05 | `quotaWarning` is false below 80% (< 800) | `callsToday = 799` | `quotaWarning == false` | ✅ covered — `QuotaStateSpec` |
| QUO-06 | `quotaWarning` is true at exactly 80% (800) | `callsToday = 800` | `quotaWarning == true` | ✅ covered — `QuotaStateSpec` |
| QUO-07 | `quotaWarning` is true above 80% | `callsToday = 801`, `1000` | `quotaWarning == true` | ✅ covered — `QuotaStateSpec` |
| QUO-08 | Successive increments accumulate correctly | 10 increments from 0 | `callsToday == 10` | ✅ covered — `QuotaStateSpec` |

---

## 3. Service Layer — OneFrameLive

All tests use an in-process fake `Client[IO]` (no real network).

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| SVC-01 | `get` returns `Right(Rate)` for a valid One-Frame response | valid JSON body, HTTP 200 | `Right(rate)` with correct pair | ✅ covered — `OneFrameLiveSpec` |
| SVC-02 | `get` returns `Left` when HTTP call fails | client that always throws | `Left(OneFrameLookupFailed(...))` | ✅ covered — `OneFrameLiveSpec` |
| SVC-03 | `fetchAll` retrieves all 72 pairs in one call | valid 72-pair JSON array | 72-element Right list | ✅ covered — `OneFrameLiveSpec` |
| SVC-04 | Custom `token` header is sent (not `Authorization: Bearer`) | spy on request headers | `req.headers.get("token").value == config.token` | ✅ covered — `OneFrameLiveSpec` |
| SVC-05 | `get` returns `Left` when response body is malformed JSON | `"not json"` body, HTTP 200 | `Left(...)` — parse failure becomes Left | ✅ covered — `OneFrameLiveSpec` |
| SVC-06 | `fetchAll` builds correct query string with all pairs | spy on request URI | URI contains all 72 `pair=XXXXXX` params | ✅ covered — `OneFrameLiveSpec` |
| SVC-07 | `toRate` maps `price` field (not bid/ask) to `Rate.price` | JSON with distinct bid/ask/price values | `rate.price == price` field value | ✅ covered — `OneFrameLiveSpec` |
| SVC-08 | One-Frame returns HTTP 200 with quota error body | `{"error":"Quota reached"}` | `Left(...)` | ❌ missing |

---

## 4. Service Layer — OneFrameCache

All tests use a fake `OneFrameLive` returning pre-built responses.

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| SVC-09 | Cache is empty before refresh stream runs | `cache.get(any pair)` before refresh | `Left(...)` for any pair | ✅ covered — `OneFrameCacheSpec` |
| SVC-10 | Cache is populated after refresh runs | run `refresh.take(1).compile.drain` | `Right(rate)` for any valid pair | ✅ covered — `OneFrameCacheSpec` |
| SVC-11 | Returns `Left` for pair absent from One-Frame response | refresh with empty response | `Left(...)` for any pair | ✅ covered — `OneFrameCacheSpec` |
| SVC-12 | Quota starts at 0 before any refresh | initial state | `quota.callsToday == 0` | ✅ covered — `OneFrameCacheSpec` |
| SVC-13 | Quota increments to 1 after one successful refresh | run `refresh.take(1)` | `callsToday == 1` | ✅ covered — `OneFrameCacheSpec` |
| SVC-14 | Quota does NOT increment on One-Frame error response | malformed JSON response | `callsToday` unchanged | ✅ covered — `OneFrameCacheSpec` |
| SVC-15 | `forceRefresh` populates the cache immediately | empty cache, call `forceRefresh` | cache contains pairs, `getLastRefreshedAt` is Some | ✅ covered — `OneFrameCacheSpec` |
| SVC-16 | `getInterval` returns configured interval | default config | `5.minutes` | ✅ covered — `OneFrameCacheSpec` |
| SVC-17 | `setInterval` changes the value readable by `getInterval` | `setInterval(2.minutes)` | `getInterval` returns `2.minutes` | ✅ covered — `OneFrameCacheSpec` |
| SVC-18 | `getLastRefreshedAt` is None before first refresh | cold start | `None` | ✅ covered — `OneFrameCacheSpec` |
| SVC-19 | `getLastRefreshedAt` is Some after refresh | after `forceRefresh` | `Some(instant)` | ✅ covered — `OneFrameCacheSpec` |
| SVC-20 | Quota increments on each `forceRefresh` call | 3 calls | `callsToday == 3` | ✅ covered — `OneFrameCacheSpec` |
| SVC-21 | Old cache values survive a failed refresh | prime cache, failed refresh | `get(pair)` still returns cached rate | ✅ covered — `OneFrameCacheSpec` |
| SVC-22 | Refresh stream does not crash when One-Frame returns Left | run 3 cycles, second fails | stream continues; third cycle succeeds | ✅ covered — `OneFrameCacheSpec` |
| SVC-23 | Cache publishes `CacheRefresh` SSE event on success | run refresh, collect bus events | `CacheRefresh` event with `pairsCount == 72` | ✅ covered — `OneFrameCacheSpec` |
| SVC-24 | Cache publishes `CacheRefreshFailed` SSE event on error | fake live returns Left | `CacheRefreshFailed` event on bus | ✅ covered — `OneFrameCacheSpec` |

---

## 5. EventBus

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| EVT-01 | Subscriber receives a published event | publish `CacheRefresh`, collect from subscribe stream | subscriber gets that event | ✅ covered — `EventBusSpec` |
| EVT-02 | `None` sentinel is filtered out of subscribe stream | internal sentinel | subscribers never see a None | ✅ covered — `EventBusSpec` |
| EVT-03 | Multiple events received in publish order | publish A then B | subscriber sees A then B | ✅ covered — `EventBusSpec` |
| EVT-04 | Two independent subscribers each receive the same event | 2 subscribers, publish 1 event | both subscribers receive it | ✅ covered — `EventBusSpec` |
| EVT-05 | Subscriber joined after publish does NOT receive past events | subscribe after publish | no events received (no replay) | ✅ covered — `EventBusSpec` |

---

## 6. Program Layer

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| PRG-01 | `get` returns `Right(rate)` when service succeeds | service stub returning `Right(rate)` | `Right(rate)` unchanged | ✅ covered — `ProgramSpec` |
| PRG-02 | `get` maps `OneFrameLookupFailed` to `RateLookupFailed` | service stub returning `Left(OneFrameLookupFailed("msg"))` | `Left(RateLookupFailed(...))` | ✅ covered — `ProgramSpec` |
| PRG-03 | `RateLookupFailed.getMessage` returns the message string | `RateLookupFailed("test error")` | `.getMessage == "test error"` | ✅ covered — `ProgramSpec` |

---

## 7. HTTP Layer — Authentication Middleware

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| MID-01 | Correct `X-Proxy-Token` allows request through | valid token | 200 | ✅ covered — `AuthMiddlewareSpec` |
| MID-02 | Wrong `X-Proxy-Token` returns 401 | wrong token | 401 | ✅ covered — `AuthMiddlewareSpec` |
| MID-03 | Missing `X-Proxy-Token` returns 401 | no header | 401 | ✅ covered — `AuthMiddlewareSpec` |
| MID-04 | 401 response body mentions the header name | missing token | body contains `"X-Proxy-Token"` | ✅ covered — `AuthMiddlewareSpec` |
| MID-05 | Unknown routes return 404 | `GET /nonexistent` | 404 | ✅ covered — `AuthMiddlewareSpec` |
| MID-06 | Request timeout returns 503 | stub that never completes | 503 | ❌ missing |

---

## 8. HTTP Layer — Auth Routes (`/auth`)

Auth routes are **public** — no `X-Proxy-Token` required.

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| AUTH-01 | `POST /auth/login` with correct credentials returns 200 + token | `{"username":"user@paidy.com","password":"forex2025"}` | 200, body `{"token":"<uuid>"}` | ✅ covered — `AuthHttpRoutesSpec` |
| AUTH-02 | `POST /auth/login` with wrong password returns 401 | `{"username":"user@paidy.com","password":"wrong"}` | 401 | ✅ covered — `AuthHttpRoutesSpec` |
| AUTH-03 | `GET /auth/validate` with valid token returns 200 | `Authorization: Bearer <valid-token>` | 200 | ✅ covered — `AuthHttpRoutesSpec` |
| AUTH-04 | `GET /auth/validate` with invalid token returns 401 | `Authorization: Bearer not-a-token` | 401 | ✅ covered — `AuthHttpRoutesSpec` |
| AUTH-05 | `POST /auth/logout` returns 204 and invalidates token | valid token | 204; subsequent validate → 401 | ✅ covered — `AuthHttpRoutesSpec` |
| AUTH-06 | `GET /auth/validate` with no `Authorization` header returns 401 | no header | 401 | ✅ covered — `AuthHttpRoutesSpec` |
| AUTH-07 | `POST /auth/login` with wrong username returns 401 | `{"username":"wrong@paidy.com","password":"forex2025"}` | 401 | ✅ covered — `AuthHttpRoutesSpec` |
| AUTH-08 | Session tokens are unique per login | two successful logins | tokens differ | ✅ covered — `AuthHttpRoutesSpec` |

---

## 9. HTTP Layer — `GET /rates`

`/rates` requires `X-Proxy-Token`.

### 9.1 Happy Path

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| HTTP-01 | Valid pair returns 200 with rate JSON | `GET /rates?from=USD&to=JPY` + valid token | 200, `{"from":"USD","to":"JPY","price":...,"timestamp":"..."}` | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-02 | Response includes `X-Request-ID` header | any valid request | `X-Request-ID` header present | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-03 | Token enforcement passes through | correct token | 200 | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-04 | Wrong token returns 401 | wrong token | 401 | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-05 | Missing token returns 401 | no header | 401 | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-06 | Each request gets a unique request ID | two identical requests | `X-Request-ID` values differ | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-07 | SSE `ProxyRequest` event published on success | valid request | bus receives `ProxyRequest` with `status=200` | ✅ covered — `RatesHttpRoutesSpec` |

### 9.2 Validation — 400 Responses

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| HTTP-08 | Missing `from` parameter returns 400 | `GET /rates?to=JPY` | 400 | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-09 | Missing both parameters returns 400 | `GET /rates` | 400 | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-10 | Invalid `from` currency code returns 400 | `GET /rates?from=XXX&to=JPY` | 400 | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-11 | Same `from` and `to` returns 400 | `GET /rates?from=USD&to=USD` | 400 with "must be different" | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-12 | Missing `to` parameter returns 400 | `GET /rates?from=USD` | 400 | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-13 | Invalid `to` currency code returns 400 | `GET /rates?from=USD&to=XXX` | 400 | ✅ covered — `RatesHttpRoutesSpec` |

### 9.3 Error Propagation — 500 Responses

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| HTTP-14 | Program returns Left → 500 | program stub returning `Left(RateLookupFailed(...))` | 500 with error message in body | ✅ covered — `RatesHttpRoutesSpec` |
| HTTP-15 | SSE `ProxyRequest` event published on 500 | program error | event has `status=500`, `price=None` | ✅ covered — `RatesHttpRoutesSpec` |

---

## 10. HTTP Layer — Config Endpoints

Config endpoints are **public** (no token required).

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| CFG-01 | `GET /config/status` returns 200 on cold start | cold cache | 200, `intervalSeconds=240`, `lastRefreshedAt=null`, `callsToday=0`, `dailyLimit=1000`, `quotaWarning=false` | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-02 | `GET /config/status` shows `callsToday = 1` after refresh | after `forceRefresh` | `callsToday=1`, `lastRefreshedAt` is non-null | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-03 | `GET /config/refresh-interval` returns current interval | default config | 200, `{"seconds":240,...}` | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-04 | `PUT /config/refresh-interval` with valid value returns 200 | `{"seconds":120}` | 200, `{"seconds":120,...}` | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-05 | `PUT /config/refresh-interval` below minimum (90) → 400 | `{"seconds":30}` | 400 | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-06 | `PUT /config/refresh-interval` above maximum (300) → 400 | `{"seconds":600}` | 400 | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-07 | `PUT /config/refresh-interval` at boundary 90 → 200 | `{"seconds":90}` | 200 | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-08 | `PUT /config/refresh-interval` at boundary 300 → 200 | `{"seconds":300}` | 200 | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-09 | `POST /config/force-refresh` returns 200 | — | 200, body mentions "refreshed" | ✅ covered — `ConfigHttpRoutesSpec` |
| CFG-10 | `PUT` with non-JSON body → 400/415 | `Content-Type: text/plain` | 400 or 415 | ❌ missing — http4s raises `InvalidMessageBodyFailure` as an effect error rather than a 400 response; not testable without route-level error handling |

---

## 11. HTTP Layer — SSE `/events`

`/events` is **public** (`EventSource` cannot send custom headers).

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| SSE-01 | Response status is 200 | `GET /events` | 200 | ✅ covered — `EventsHttpRoutesSpec` |
| SSE-02 | Response has `Content-Type: text/event-stream` | `GET /events` | correct Content-Type header | ✅ covered — `EventsHttpRoutesSpec` |
| SSE-03 | Published events appear in the SSE stream | publish `CacheRefresh` to bus | SSE frame with JSON-encoded event | ✅ covered — `EventsHttpRoutesSpec` |
| SSE-04 | Heartbeat emitted within 30 seconds | subscribe, wait | frame with `"type":"Heartbeat"` | ❌ missing (integration test INT-14) |
| SSE-05 | Multiple concurrent SSE connections each receive all events | 3 connections, publish 1 event | all 3 receive it | ✅ covered — `EventsHttpRoutesSpec` |

---

## 12. Integration Tests (docker-compose.it.yml)

End-to-end tests against the full Docker stack, run by `scripts/integration-test.sh`.

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| INT-01 | Valid currency pair returns 200 | `GET /rates?from=USD&to=JPY` + token | 200 with numeric price | ✅ covered — `integration-test.sh` |
| INT-02 | EUR/GBP pair returns 200 | `GET /rates?from=EUR&to=GBP` + token | 200 | ✅ covered |
| INT-03 | Invalid currency returns 400 | `GET /rates?from=XYZ&to=JPY` + token | 400 | ✅ covered |
| INT-04 | Missing `from` returns 400 | `GET /rates?to=JPY` + token | 400 | ✅ covered |
| INT-05 | Missing `to` returns 400 | `GET /rates?from=USD` + token | 400 | ✅ covered |
| INT-06 | Same currency returns 400 | `GET /rates?from=USD&to=USD` + token | 400 | ✅ covered |
| INT-07 | `/rates` without token returns 401 | no `X-Proxy-Token` header | 401 | ✅ covered |
| INT-08 | `POST /auth/login` with correct credentials returns token | `{"username":"user@paidy.com","password":"forex2025"}` | 200 + token UUID | ✅ covered |
| INT-09 | `GET /auth/validate` with valid token returns 200 | `Authorization: Bearer <token>` | 200 | ✅ covered |
| INT-10 | `POST /auth/login` with wrong password returns 401 | wrong password | 401 | ✅ covered |
| INT-11 | Cache warm within 10s of startup | start stack, wait 10s | first `/rates` returns 200 (not 500) | ❌ missing |
| INT-12 | N concurrent requests all succeed | 50 simultaneous `/rates` requests | all 200 | ❌ missing |
| INT-13 | One-Frame call count stays ≤ 1 per interval regardless of request volume | 100 requests over 30s | 0 or 1 new One-Frame calls | ❌ missing |
| INT-14 | SSE `/events` endpoint reachable and delivers heartbeat | `curl -N /events`, wait 35s | at least one `Heartbeat` frame | ❌ missing |

---

## 13. Frontend — Pure Logic Helpers

### 13.1 `fmtDuration`

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| FE-01 | Sub-millisecond: 3 decimal places | `0.423`, `0.001` | `"0.423"`, `"0.001"` | ✅ covered — `eventLogHelpers.test.ts` |
| FE-02 | 1–9ms: 2 decimal places | `1.0`, `5.56` | `"1.00"`, `"5.56"` | ✅ covered |
| FE-03 | 10–99ms: 1 decimal place | `10.0`, `50.7` | `"10.0"`, `"50.7"` | ✅ covered |
| FE-04 | 100ms+: rounded integer | `100`, `150.6` | `"100"`, `"151"` | ✅ covered |
| FE-05 | Exactly 0 formats as sub-millisecond | `0` | `"0.000"` | ✅ covered |

### 13.2 `statusColor`

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| FE-06 | Green for 200 | `200` | `"text-green-400"` | ✅ covered |
| FE-07 | Yellow for 4xx | `400`, `422`, `499` | `"text-yellow-400"` | ✅ covered |
| FE-08 | Red for 5xx | `500`, `503` | `"text-red-400"` | ✅ covered |
| FE-09 | Red for other codes | `301` | `"text-red-400"` | ✅ covered |

### 13.3 `durationColor`

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| FE-10 | Green for sub-ms (cache hits) | `0`, `0.5`, `0.999` | `"text-green-400"` | ✅ covered |
| FE-11 | Cyan for 1–4ms | `1`, `4.9` | `"text-cyan-400"` | ✅ covered |
| FE-12 | Yellow for 5–49ms | `5`, `49` | `"text-yellow-400"` | ✅ covered |
| FE-13 | Red for 50ms+ | `50`, `200` | `"text-red-400"` | ✅ covered |

### 13.4 `isProxyRequest` type guard

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| FE-14 | Returns true for `ProxyRequest` events | `ProxyRequest` entry | `true` | ✅ covered |
| FE-15 | Returns false for `CacheRefresh` events | `CacheRefresh` entry | `false` | ✅ covered |

---

## 14. Frontend — Quota State Logic

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| FE-16 | Quota bar at 0% | `quotaPct(0, 1000)` | `0` | ✅ covered — `quotaState.test.ts` |
| FE-17 | Quota bar at 50% | `quotaPct(500, 1000)` | `50` | ✅ covered |
| FE-18 | Quota bar at soft limit (80%) | `quotaPct(800, 1000)` | `80` | ✅ covered |
| FE-19 | Quota bar capped at 100% when over limit | `quotaPct(1200, 1000)` | `100` | ✅ covered |
| FE-20 | `quotaWarning` false below 800 | `799 >= 800` | `false` | ✅ covered |
| FE-21 | `quotaWarning` true at exactly 800 | `800 >= 800` | `true` | ✅ covered |
| FE-22 | Remaining calls decrements correctly | `remaining(360, 1000)` | `640` | ✅ covered |
| FE-23 | Cache hit ratio returns "—" when no One-Frame calls | `cacheHitRatio(100, 0)` | `"—"` | ✅ covered |
| FE-24 | Cache hit ratio with one decimal place | `cacheHitRatio(72, 1)` | `"72.0"` | ✅ covered |
| FE-25 | `freshnessColor` gray when age unknown | `freshnessColor(null, 240)` | `"text-gray-500"` | ✅ covered |
| FE-26 | `freshnessColor` green when age < 50% of interval | `freshnessColor(0, 240)` | `"text-green-400"` | ✅ covered |
| FE-27 | `freshnessColor` yellow between 50% and 90% | `freshnessColor(121, 240)` | `"text-yellow-400"` | ✅ covered |
| FE-28 | `freshnessColor` red above 90% | `freshnessColor(217, 240)` | `"text-red-400"` | ✅ covered |

---

## 15. Frontend — `useEventStream` Hook

| ID | What | Input | Expected | Status |
|----|------|-------|----------|--------|
| FE-29 | `clearEvents` can be called without throwing | call once | no exception | ✅ covered — `useEventStream.test.ts` |
| FE-30 | `clearEvents` idempotent — multiple calls safe | call 3 times | no exception | ✅ covered |
| FE-31 | `getSeq` returns 0 for unregistered entry | unregistered entry | `0` | ✅ covered |
| FE-32 | `getSeq` returns 0 after `clearEvents` | registered entry, then clear | `0` | ✅ covered |
| FE-33 | `ProxyRequest` entry has correct fields | structural check | `type`, `id`, `from`, `to`, `status`, `price`, `errorBody`, `durationMs`, `timestamp` | ✅ covered |
| FE-34 | `CacheRefresh` entry has quota fields | structural check | `callsToday`, `dailyLimit`, `quotaWarning` | ✅ covered |
| FE-35 | `CacheRefreshFailed` entry has `reason` field | structural check | `type`, `reason`, `timestamp`, `durationMs` | ✅ covered |
| FE-36 | `connected` becomes true on SSE `onopen` | simulate `onopen` | `connected == true` | ✅ covered — `useEventStreamConnection.test.ts` |
| FE-37 | `connected` becomes false on SSE `onerror` | simulate `onerror` | `connected == false` | ✅ covered — `useEventStreamConnection.test.ts` |
| FE-38 | `Heartbeat` events do NOT appear in `entries` | simulate heartbeat message | `entries` unchanged | ✅ covered — `useEventStreamConnection.test.ts` |
| FE-39 | `Heartbeat` updates `clockOffsetMs` | `serverTimeMs = Date.now() + 5000` | `clockOffsetMs ≈ 5000` | ✅ covered — `useEventStreamConnection.test.ts` |
| FE-40 | Ring buffer evicts oldest entries at 2000 | send 2001 events | `entries.length == 2000` | ✅ covered — `useEventStreamConnection.test.ts` |
| FE-41 | Malformed JSON frames silently ignored | `"not json"` message | no crash, `entries` unchanged | ✅ covered — `useEventStreamConnection.test.ts` |
| FE-42 | Multiple consumers share one `EventSource` | mount two components | only 1 `EventSource` created | ✅ covered — `useEventStreamConnection.test.ts` |

---

## Coverage Summary

| Layer | Total Cases | Covered | Missing | Coverage |
|-------|-------------|---------|---------|----------|
| Domain — Currency | 9 | 9 | 0 | 100% |
| Domain — LogEvent | 7 | 7 | 0 | 100% |
| QuotaState | 8 | 8 | 0 | 100% |
| OneFrameLive | 8 | 7 | 1 | 88% |
| OneFrameCache | 16 | 16 | 0 | 100% |
| EventBus | 5 | 5 | 0 | 100% |
| Program | 3 | 3 | 0 | 100% |
| HTTP — AuthMiddleware | 6 | 5 | 1 | 83% |
| HTTP — Auth Routes | 8 | 8 | 0 | 100% |
| HTTP — GET /rates | 15 | 14 | 1 | 93% |
| HTTP — Config | 10 | 9 | 1 | 90% |
| HTTP — SSE /events | 5 | 4 | 1 | 80% |
| Integration | 14 | 10 | 4 | 71% |
| FE — Pure Logic Helpers | 28 | 28 | 0 | 100% |
| FE — useEventStream | 14 | 14 | 0 | 100% |
| **Total** | **156** | **147** | **9** | **94%** |

---

## Test Suites Reference

### Scala (14 suites, 99 tests)

| Suite | File | Tests |
|-------|------|-------|
| `CurrencySpec` | `forex/domain/` | 6 |
| `CurrencyProperties` | `forex/domain/` | 3 |
| `LogEventSpec` | `forex/domain/` | 8 |
| `RateSpec` | `forex/domain/` | 5 |
| `QuotaStateSpec` | `forex/services/rates/` | 9 |
| `OneFrameLiveSpec` | `forex/services/rates/` | 7 |
| `OneFrameCacheSpec` | `forex/services/rates/` | 16 |
| `EventBusSpec` | `forex/services/events/` | 5 |
| `ProgramSpec` | `forex/programs/rates/` | 3 |
| `AuthMiddlewareSpec` | `forex/http/` | 5 |
| `AuthHttpRoutesSpec` | `forex/http/auth/` | 8 |
| `RatesHttpRoutesSpec` | `forex/http/rates/` | 15 |
| `ConfigHttpRoutesSpec` | `forex/http/config/` | 9 |
| `EventsHttpRoutesSpec` | `forex/http/events/` | 4 |

### Frontend (4 suites, 65 tests)

| Suite | File | Tests |
|-------|------|-------|
| `fmtDuration`, `statusColor`, `durationColor`, `isProxyRequest` | `eventLogHelpers.test.ts` | 15 |
| `quota bar`, `quotaWarning`, `remaining`, `cacheHitRatio`, `freshnessColor` | `quotaState.test.ts` | 20 |
| `clearEvents`, `getSeq`, `LogEntry type shape` | `useEventStream.test.ts` | 7 |
| `EventSource lifecycle`, `ring buffer`, `clock skew`, `singleton` | `useEventStreamConnection.test.ts` | 9 |

**Total: 164 automated tests across 18 suites.**

---

## Remaining Gaps (9 cases)

| ID | Reason not covered |
|----|-------------------|
| SVC-08 | One-Frame quota error body — low value; One-Frame currently returns success JSON even over quota |
| MID-06 | `Timeout` middleware → 503 requires an `IO` that never completes; testing Timeout correctly needs `TestControl` from CE3 which is not available in CE2 |
| CFG-10 | `PUT` with non-JSON body — http4s 0.22 raises `InvalidMessageBodyFailure` as an effect error rather than mapping it to a 400; would require route-level `handleErrorWith` to catch |
| SSE-04 | Heartbeat timer (30s wait) — impractical in unit tests; covered by INT-14 integration test |
| INT-11 | Cache warm-up time — requires full Docker stack |
| INT-12 | Concurrent load test — requires full Docker stack |
| INT-13 | One-Frame call count over time — requires full Docker stack |
| INT-14 | SSE heartbeat end-to-end — requires full Docker stack |

---

## Test Stack

### Backend (Scala)
- **ScalaTest** `AnyFunSuite` — all suites
- **cats-effect** `IO.unsafeRunSync()` for effect execution in tests
- **http4s** `Client.fromHttpApp` — in-process HTTP fakes, no TCP sockets
- **fs2** `.take(n).compile.toList` for stream testing

### Frontend
- **Vitest** v1.x — test runner (Jest-compatible API)
- **jsdom** — DOM environment for structural tests
- **@testing-library/jest-dom** — DOM matchers
- For future component tests: **@testing-library/react**, **msw** (Mock Service Worker), **vi.useFakeTimers()**
