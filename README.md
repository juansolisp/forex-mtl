# forex-mtl

A production-ready Forex rates proxy built with Scala + cats-effect.

- Exposes `GET /rates?from=<CCY>&to=<CCY>` — returns the current exchange rate between two currencies.
- Calls the [One-Frame](https://hub.docker.com/r/paidyinc/one-frame) API in the background every 4 minutes, fetching all 72 currency pairs in a single request.
- Serves all rate requests from an in-memory cache — no per-request HTTP calls.
- Satisfies the constraints: ≤ 1,000 One-Frame calls/day (uses 360), ≥ 10,000 served requests/day, rates ≤ 5 minutes old.
- User-facing login system with session token authentication and a React dashboard.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Docker | 24.x |
| Docker Compose | v2 (plugin) or standalone `docker-compose` |

> Docker is the only hard requirement. No JDK, sbt, or Node.js needed to run the full stack.

---

## Running locally

### 1. Clone the repo

```bash
git clone https://github.com/juansolisp/forex-mtl.git
cd forex-mtl
```

### 2. Check port 80 availability

The frontend container binds to port **80** by default. Port 80 is a privileged port — on Linux it requires root, and on any OS it may already be taken by another service (Apache, Nginx, etc.).

**Check if port 80 is free:**

```bash
# Linux
sudo lsof -i :80

# Mac
sudo lsof -i :80

# Windows (PowerShell)
netstat -ano | findstr :80
```

If the output is empty, port 80 is free and you can skip to step 3.

**If port 80 is taken or you get a permission error**, open `docker-compose.yml` and change the frontend port mapping to any free port. Port 3001 is a good default that rarely conflicts:

```yaml
# docker-compose.yml  — find the frontend service and change this line:

  frontend:
    build: ./frontend
    ports:
      - "3001:80"    # left side = host port (change this), right side = container port (leave as 80)
```

Other valid examples:

```yaml
      - "3000:80"    # common alternative
      - "8080:80"    # another common choice
```

Save the file. The app will then be available at `http://localhost:3001` (or whichever port you chose).

> **Linux only:** even on a free port, running containers on ports below 1024 may require `sudo`. Using port 3001 or higher avoids this entirely.

### 3. Start the full stack

```bash
docker-compose up --build
```

The first run compiles the Scala project from scratch — this takes **3–5 minutes**. Subsequent runs use the Docker layer cache and start in seconds.

Wait until you see this log line from `forex-proxy`:

```
Cache refreshed: 72 pairs loaded
```

That means the cache is warm and rates are ready to serve.

### 4. Open the app

| Service | URL | Notes |
|---------|-----|-------|
| Frontend (React dashboard) | http://localhost:3001 | Or whichever port you set in step 2 |
| Scala proxy (direct API) | http://localhost:9090 | |
| One-Frame upstream | http://localhost:18080 | |

### 5. Log in

The app shows a login page on first load. Use:

| Field | Value |
|-------|-------|
| Username | `user@paidy.com` |
| Password | `forex2025` |

### 6. Stop

```bash
docker-compose down
```

---

## Calling the API directly

The Scala proxy at `http://localhost:9090` uses a fixed shared secret for machine-to-machine authentication. Every request to `/rates` and `/config` must include the header:

```
X-Proxy-Token: 10dc303535874aeccc86a8251e699999
```

This header is added automatically by Nginx when requests go through the frontend (port 80). When calling the proxy **directly** on port 9090 you must include it yourself.

### Get an exchange rate

```bash
curl 'http://localhost:9090/rates?from=USD&to=JPY' \
  -H 'X-Proxy-Token: 10dc303535874aeccc86a8251e699999'
```

```json
{
  "from": "USD",
  "to": "JPY",
  "price": 0.7836,
  "timestamp": "2021-01-01T00:00:00Z"
}
```

Or with wget:

```bash
wget -qO- \
  --header='X-Proxy-Token: 10dc303535874aeccc86a8251e699999' \
  'http://localhost:9090/rates?from=USD&to=JPY'
```

### What happens without the token

```bash
curl 'http://localhost:9090/rates?from=USD&to=JPY'
# HTTP 401
# Missing or invalid X-Proxy-Token header
```

### Supported currencies

`AUD`, `CAD`, `CHF`, `EUR`, `GBP`, `JPY`, `NZD`, `SGD`, `USD`

### Error responses

```bash
# Invalid currency
curl 'http://localhost:9090/rates?from=USD&to=XXX' \
  -H 'X-Proxy-Token: 10dc303535874aeccc86a8251e699999'
# HTTP 400 — Invalid currency: XXX

# Same currency on both sides
curl 'http://localhost:9090/rates?from=USD&to=USD' \
  -H 'X-Proxy-Token: 10dc303535874aeccc86a8251e699999'
# HTTP 400 — from and to must be different currencies

# Missing parameter
curl 'http://localhost:9090/rates?from=USD' \
  -H 'X-Proxy-Token: 10dc303535874aeccc86a8251e699999'
# HTTP 400
```

---

## Authentication endpoints

The `/auth` endpoints are **public** — no `X-Proxy-Token` needed.

### Login

```bash
curl -X POST http://localhost:9090/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"user@paidy.com","password":"forex2025"}'
```

```json
{ "token": "550e8400-e29b-41d4-a716-446655440000" }
```

Wrong credentials → HTTP 401.

### Validate a session token

```bash
curl http://localhost:9090/auth/validate \
  -H 'Authorization: Bearer <token>'
```

HTTP 200 — valid. HTTP 401 — unknown or expired.

### Logout

```bash
curl -X POST http://localhost:9090/auth/logout \
  -H 'Authorization: Bearer <token>'
```

HTTP 204 — token invalidated.

---

## Other endpoints

### Cache status

```bash
curl http://localhost:9090/config/status
```

Returns current refresh interval, last refresh timestamp, and One-Frame quota usage.

### Change refresh interval (90–300 seconds)

```bash
curl -X PUT http://localhost:9090/config/refresh-interval \
  -H 'Content-Type: application/json' \
  -d '{"seconds": 120}'
```

### Server-Sent Events stream

```bash
curl -N http://localhost:9090/events \
  -H 'Accept: text/event-stream'
```

Emits `ProxyRequest`, `CacheRefresh`, `CacheRefreshFailed`, and `Heartbeat` (every 30 s) events as JSON.

---

## Running tests

### Scala unit tests (requires JDK 17 + sbt 1.9)

```bash
sbt test
```

Expected output:

```
[info] Tests: succeeded 100, failed 0, canceled 0, ignored 0, pending 0
[info] All tests passed.
```

### Frontend unit tests (requires Node.js 18+)

```bash
cd frontend
npm install
npm test
```

Expected output:

```
 ✓ src/test/quotaState.test.ts                  (20 tests)
 ✓ src/test/eventLogHelpers.test.ts             (15 tests)
 ✓ src/test/useEventStream.test.ts              (7 tests)
 ✓ src/test/useEventStreamConnection.test.ts    (9 tests)

 Test Files  4 passed (4)
      Tests  51 passed (51)
```

### Integration tests (requires Docker)

```bash
bash scripts/integration-test.sh
```

---

## Configuration

All config lives in `src/main/resources/application.conf`. Environment variables override defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `ONE_FRAME_URL` | `http://localhost:8080` | One-Frame base URL |
| `ONE_FRAME_TOKEN` | `10dc303535874aeccc86a8251e6992f5` | One-Frame auth token |
| `PROXY_TOKEN` | `10dc303535874aeccc86a8251e699999` | `X-Proxy-Token` value clients must send |
| `AUTH_USERNAME` | `user@paidy.com` | Login username |
| `AUTH_PASSWORD` | `forex2025` | Login password |

---

## Architecture

```
Browser (http://localhost:80 via Nginx, or :5173 via Vite dev server)
       │
       ▼
  Nginx / Vite dev proxy
       │  (injects X-Proxy-Token automatically for /rates and /config)
       │
       ├── /auth/*   ──────────────────► AuthHttpRoutes      (public)
       │
       ├── /events ────────────────────► EventsHttpRoutes    (public)
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
│   ├── ApplicationConfig.scala
│   └── Config.scala
├── domain/
│   ├── Currency.scala
│   ├── Rate.scala
│   ├── Price.scala
│   └── Timestamp.scala
├── services/
│   ├── auth/
│   │   └── AuthService.scala           # Ref-backed session store
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
    │   └── AuthHttpRoutes.scala
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
    ├── useAuth.ts                      # Module-singleton auth state
    ├── useEventStream.ts               # SSE connection + event ring buffer
    └── useRefreshInterval.ts           # Polls /config/refresh-interval
```

---

## Caching strategy

One-Frame enforces a hard limit of **1,000 API calls per day**. The proxy must serve at least 10,000 rate requests per day while keeping rates no older than 5 minutes.

| Approach | One-Frame calls/day | Within 1,000 limit | Staleness |
|---|---|---|---|
| Per-request (naive) | up to 10,000+ | No — limit exceeded immediately | Always fresh |
| Poll every 5 min, per pair | up to 288 × 72 = 20,736 | No | < 5 min |
| **Proactive batch (this impl)** | **360** | **Yes — 64% headroom remaining** | **< 4 min** |

### How it works

All 72 pairs (9 currencies × 8 peers) are fetched in a **single** One-Frame request every 4 minutes. Results are stored in `Ref[F, Map[Rate.Pair, Rate]]` — lock-free, thread-safe, no blocking reads.

```
calls/day = (60 min × 24 h) / 4 min × 1 request = 360 calls/day
```

- **360 calls/day** — well within the 1,000/day limit, leaving 640 calls of headroom for retries or interval adjustments
- **< 4 min staleness** — within the 5-minute SLA
- **Unlimited read throughput** — all `/rates` responses are served from the in-memory cache with no upstream calls

The refresh interval can be changed at runtime via `PUT /config/refresh-interval` (90–300 seconds) without restarting the service.
