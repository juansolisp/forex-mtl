# forex-mtl

A production-ready Forex rates proxy built with Scala + cats-effect, designed as a Paidy take-home assignment.

## What it does

- Exposes `GET /rates?from=<CCY>&to=<CCY>` — returns the current exchange rate between two currencies.
- Calls the [One-Frame](https://hub.docker.com/r/paidyinc/one-frame) API in the background every 4 minutes, fetching all 72 currency pairs in a single request.
- Serves all rate requests from an in-memory cache — no per-request HTTP calls.
- Satisfies the constraints: ≤ 1,000 One-Frame calls/day (uses 360), ≥ 10,000 served requests/day, rates ≤ 5 minutes old.
- User-facing login system with session token authentication and a React dashboard.

---

## Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Docker + Docker Compose | 24.x / v2 | Required for all run modes |
| Java (JDK) | 11 | Only needed for `sbt run` (local mode) |
| sbt | 1.8.0 | Only needed for `sbt run` / `sbt test` |
| Node.js + npm | 18 | Only needed for the frontend in dev mode |

> **Docker-only path:** Docker is the only hard requirement. No JDK, sbt, or Node.js needed to run the full stack.

---

## Quick start

### Option 1 — Full stack with Docker Compose (recommended)

Builds the Scala proxy JAR and the React frontend, then starts all three services:

```bash
docker compose up --build
```

| Service | Address | Description |
|---------|---------|-------------|
| `frontend` | http://localhost:3001 | React dashboard (Nginx, Docker only) |
| `forex-proxy` | http://localhost:9090 | Scala rates proxy |
| `one-frame` | http://localhost:18080 | Upstream One-Frame API |

Wait for the proxy log line `Cache refreshed: 72 pairs` (appears within ~2 seconds), then open **http://localhost:3001** (Docker) or **http://localhost:5173** (Vite dev server).

You will be presented with a login page. Use the credentials below.

#### Test user credentials

| Field | Value |
|-------|-------|
| Username | `user@paidy.com` |
| Password | `forex2025` |

After login the dashboard is shown. Click **Sign out** in the top-right to return to the login page.

To stop:

```bash
docker compose down
```

To rebuild a single service after code changes:

```bash
docker compose build forex-proxy   # rebuild the Scala proxy
docker compose build frontend      # rebuild the React UI
docker compose up -d               # restart changed containers
```

---

### Option 2 — Run locally with sbt (requires JDK 11 + sbt 1.8.0)

One-Frame must be running before you start the proxy, because the cache fetches on startup:

```bash
# Terminal 1 — start One-Frame
docker run --rm -p 8080:8080 paidyinc/one-frame
```

```bash
# Terminal 2 — compile and run the proxy
cd interview/forex-mtl
sbt run
```

The proxy listens on `http://localhost:9090`. One-Frame's default URL (`http://localhost:8080`) is already set in `application.conf`.

```bash
# Authenticate
curl -X POST http://localhost:9090/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"user@paidy.com","password":"forex2025"}'
# → {"token":"<uuid>"}

# Use the token
curl 'http://localhost:9090/rates?from=USD&to=JPY' \
  -H 'X-Proxy-Token: 10dc303535874aeccc86a8251e699999'
```

---

### Option 3 — Frontend in dev mode (requires Node.js 18+)

Runs the Vite dev server with hot-reload. The Scala proxy must already be running (Docker Compose or `sbt run`).

```bash
cd interview/forex-mtl/frontend
npm install
npm run dev
# Open http://localhost:5173
```

Vite proxies `/auth`, `/rates`, `/events`, `/config`, and `/one-frame` to the backend automatically.

---

## Running tests

### Scala unit tests

All tests run without any running services. External HTTP calls are replaced with in-process fakes (`Client.fromHttpApp`).

**With sbt (requires JDK 11 + sbt 1.8):**
```bash
cd interview/forex-mtl
sbt test
```

**With Docker (no local JDK required):**
```bash
docker run --rm -v "$(pwd)":/app -w /app \
  hseeberger/scala-sbt:17.0.2_1.6.2_2.13.8 sbt test
```

**Expected output:**
```
[info] Total number of tests run: 100
[info] Suites: completed 14, aborted 0
[info] Tests: succeeded 100, failed 0, canceled 0, ignored 0, pending 0
[info] All tests passed.
```

#### Scala test suites

| Suite | Location | What it tests |
|-------|----------|---------------|
| `CurrencySpec` | `forex/domain/` | `fromString` parsing, case-insensitivity, `show`, round-trip identity |
| `CurrencyProperties` | `forex/domain/` | Exhaustive table-driven coverage of all 9 currencies; 72 distinct pair uniqueness |
| `RateSpec` | `forex/domain/` | `Rate` / `Rate.Pair` construction, direction inequality, Map key usage |
| `LogEventSpec` | `forex/domain/` | Circe JSON encoding for all event types |
| `QuotaStateSpec` | `forex/services/rates/` | `QuotaState.increment` arithmetic; UTC day rollover; soft-limit threshold |
| `OneFrameLiveSpec` | `forex/services/rates/` | Happy-path HTTP call; connection failure → `Left`; custom `token` header; malformed JSON → `Left`; query string shape; price field mapping |
| `OneFrameCacheSpec` | `forex/services/rates/` | Empty-cache `Left`; populated after refresh; quota increment; `forceRefresh`; `setInterval`; stale cache survives failed refresh; stream resilience; SSE event publishing |
| `EventBusSpec` | `forex/services/events/` | Fan-out delivery; `None` sentinel filtered; no replay for late subscribers |
| `ProgramSpec` | `forex/programs/rates/` | `Right(Rate)` pass-through; error mapping; `getMessage` |
| `AuthMiddlewareSpec` | `forex/http/` | Token enforcement; 401 body; 404 for unknown routes |
| `RatesHttpRoutesSpec` | `forex/http/rates/` | 200 with rate JSON; 400 invalid/same/missing currency; 500 on program error; `X-Request-ID` header; unique IDs; SSE event publishing |
| `ConfigHttpRoutesSpec` | `forex/http/config/` | Status, refresh-interval GET/PUT, force-refresh, non-JSON body → 400/415 |
| `EventsHttpRoutesSpec` | `forex/http/events/` | 200 status; `text/event-stream` Content-Type; events appear in stream; multiple concurrent connections |
| `AuthHttpRoutesSpec` | `forex/http/auth/` | Login 200+token; wrong credentials 401; validate valid/invalid/missing token; logout; unique tokens |

---

### Frontend unit tests

```bash
cd interview/forex-mtl/frontend
npm install
npm test
```

**Expected output:**
```
 ✓ src/test/quotaState.test.ts                  (20 tests)
 ✓ src/test/eventLogHelpers.test.ts             (15 tests)
 ✓ src/test/useEventStream.test.ts              (7 tests)
 ✓ src/test/useEventStreamConnection.test.ts    (9 tests)

 Test Files  4 passed (4)
      Tests  51 passed (51)
```

---

### Integration tests (requires Docker)

Starts One-Frame and the proxy via `docker-compose.it.yml`, waits for health checks, then runs a suite of `curl`-based assertions:

```bash
bash interview/forex-mtl/scripts/integration-test.sh
```

---

## API reference

### Authentication

All auth endpoints are public (no `X-Proxy-Token` required).

#### `POST /auth/login`

```bash
curl -X POST http://localhost:9090/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"user@paidy.com","password":"forex2025"}'
```

**200 OK:**
```json
{ "token": "550e8400-e29b-41d4-a716-446655440000" }
```

**401 Unauthorized** — wrong credentials.

#### `GET /auth/validate`

```bash
curl http://localhost:9090/auth/validate \
  -H 'Authorization: Bearer <token>'
```

**200 OK** — token is valid. **401** — token unknown or expired.

#### `POST /auth/logout`

```bash
curl -X POST http://localhost:9090/auth/logout \
  -H 'Authorization: Bearer <token>'
```

**204 No Content** — token invalidated.

---

### `GET /rates`

Requires header `X-Proxy-Token: 10dc303535874aeccc86a8251e699999`.

| Parameter | Type   | Required | Example | Description |
|-----------|--------|----------|---------|-------------|
| `from`    | string | yes      | `USD`   | Source currency (ISO 4217) |
| `to`      | string | yes      | `JPY`   | Target currency (ISO 4217) |

**Supported currencies:** `AUD`, `CAD`, `CHF`, `EUR`, `GBP`, `JPY`, `NZD`, `SGD`, `USD`

```bash
curl 'http://localhost:9090/rates?from=USD&to=JPY' \
  -H 'X-Proxy-Token: 10dc303535874aeccc86a8251e699999'
```

**200 OK:**
```json
{
  "from": "USD",
  "to": "JPY",
  "price": 0.7836,
  "timestamp": "2021-01-01T00:00:00Z"
}
```

**400** — invalid currency, same-currency pair, or missing parameter.
**500** — cache not yet warm or upstream failure.

---

### `GET /events`

Server-Sent Events stream. Public (no token required — `EventSource` cannot send custom headers).

```bash
curl -N http://localhost:9090/events -H 'Accept: text/event-stream'
```

Emits `ProxyRequest`, `CacheRefresh`, `CacheRefreshFailed`, and `Heartbeat` (every 30 s) events as JSON.

---

### `GET /config/status`

```bash
curl http://localhost:9090/config/status
```

Returns current refresh interval, last refresh timestamp, and One-Frame quota usage.

### `PUT /config/refresh-interval`

Change the cache refresh interval at runtime (90–300 seconds). Takes effect immediately.

```bash
curl -X PUT http://localhost:9090/config/refresh-interval \
  -H 'Content-Type: application/json' \
  -d '{"seconds": 120}'
```

---

## Configuration

All config lives in `src/main/resources/application.conf`. Environment variables override defaults:

| Variable          | Default                             | Description |
|-------------------|-------------------------------------|-------------|
| `ONE_FRAME_URL`   | `http://localhost:8080`             | One-Frame base URL |
| `ONE_FRAME_TOKEN` | `10dc303535874aeccc86a8251e6992f5` | One-Frame auth token |
| `PROXY_TOKEN`     | `10dc303535874aeccc86a8251e699999` | `X-Proxy-Token` value clients must send |
| `AUTH_USERNAME`   | `user@paidy.com`                    | Login username |
| `AUTH_PASSWORD`   | `forex2025`                         | Login password |

---

## Architecture

```
Browser (http://localhost:3001 via Docker Nginx, or :5173 via Vite dev)
       │
       ▼
  Nginx / Vite dev proxy
       │
       ├── /auth/*   ──────────────────► AuthHttpRoutes      (public)
       │                                    AuthService (Ref[F, Set[String]])
       │
       ├── /events ────────────────────► EventsHttpRoutes    (public — EventSource can't send headers)
       ├── /config ────────────────────► ConfigHttpRoutes    (public)
       │
       └── /rates  ────────────────────► X-Proxy-Token check
                                              │
                                         RatesHttpRoutes
                                              │
                                         OneFrameCache ←── Ref[F, Map[Rate.Pair, Rate]]
                                                                  ▲
                                                          background refresh stream
                                                                  │
                                                          OneFrameLive → One-Frame API
```

The app uses the **tagless final / MTL** pattern throughout:
- `Algebra[F[_]]` traits define capabilities
- Concrete implementations are injected at `Module.scala`
- `cats-effect IO` is the only concrete effect at the entry point (`Main.scala`)

---

## Project structure

```
src/main/scala/forex/
├── Main.scala
├── Module.scala                        # Dependency wiring
├── config/
│   ├── ApplicationConfig.scala         # HttpConfig, AuthConfig, OneFrameConfig
│   └── Config.scala
├── domain/
│   ├── Currency.scala
│   ├── Rate.scala
│   ├── Price.scala
│   └── Timestamp.scala
├── services/
│   ├── auth/
│   │   └── AuthService.scala           # Ref-backed session store (login/validate/logout)
│   ├── rates/
│   │   ├── algebra.scala
│   │   ├── errors.scala
│   │   ├── Interpreters.scala
│   │   └── interpreters/
│   │       ├── OneFrameLive.scala      # HTTP client for One-Frame
│   │       └── OneFrameCache.scala     # In-memory cache + background refresh
│   └── events/
│       └── EventBus.scala              # fs2 Topic-backed SSE bus
├── programs/rates/
│   ├── Program.scala
│   └── errors.scala
└── http/
    ├── AuthMiddleware.scala             # X-Proxy-Token enforcement
    ├── auth/
    │   └── AuthHttpRoutes.scala         # POST /auth/login, GET /auth/validate, POST /auth/logout
    ├── rates/
    │   └── RatesHttpRoutes.scala
    ├── events/
    │   └── EventsHttpRoutes.scala
    └── config/
        └── ConfigHttpRoutes.scala

frontend/src/
├── main.tsx                            # Root: spinner → LoginPage → App
├── App.tsx                             # Dashboard with tab bar + sign out
├── LoginPage.tsx                       # Full-screen login form
├── api.ts                              # apiFetch() — injects X-Proxy-Token
└── hooks/
    ├── useAuth.ts                      # Module-singleton auth state + bootstrap
    ├── useEventStream.ts               # SSE connection + event ring buffer
    └── useRefreshInterval.ts           # Polls /config/refresh-interval
```

---

## Caching strategy

| Approach | One-Frame calls/day | Staleness guarantee |
|---|---|---|
| Per-request (naive) | up to 10,000+ | Fresh, but exceeds limit |
| **Proactive batch (this impl)** | **360** | **< 4 min (well within 5 min SLA)** |

All 72 pairs (9 currencies × 8 peers) are fetched in a single request every 4 minutes. Results are stored in `Ref[F, Map[Rate.Pair, Rate]]` — lock-free, thread-safe, no blocking reads.
