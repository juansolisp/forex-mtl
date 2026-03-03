# forex-mtl · Full Implementation Spec

> This document is the single source of truth for the complete solution design.
> It covers every layer: backend implementation, caching, testing, CI/CD,
> integration testing, and a demo frontend.

---

## Table of Contents

1. [Solution Overview](#1-solution-overview)
2. [Backend Implementation](#2-backend-implementation)
3. [Caching Strategy](#3-caching-strategy)
4. [Error Handling](#4-error-handling)
5. [Configuration](#5-configuration)
6. [Testing Strategy](#6-testing-strategy)
7. [Real Integration Testing](#7-real-integration-testing)
8. [CI/CD Pipeline](#8-cicd-pipeline)
9. [Demo Frontend](#9-demo-frontend)
10. [File & Folder Map](#10-file--folder-map)
11. [Implementation Order](#11-implementation-order)

---

## 1. Solution Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        Demo Frontend                         │
│          React SPA  (Vite · TypeScript · port 5173)          │
└──────────────────────────┬───────────────────────────────────┘
                           │ GET /rates?from=USD&to=JPY
┌──────────────────────────▼───────────────────────────────────┐
│                   forex-proxy  (port 9090)                   │
│              Scala · cats-effect · http4s                    │
│                                                              │
│  RatesHttpRoutes → RatesProgram → RatesService               │
│                                      │                       │
│                         ┌────────────▼────────────┐         │
│                         │   OneFrameCache          │         │
│                         │  Ref[F, Map[Pair,Rate]]  │         │
│                         │  refreshes every 4 min   │         │
│                         └────────────┬────────────┘         │
│                                      │ on miss / refresh     │
│                         ┌────────────▼────────────┐         │
│                         │   OneFrameLive           │         │
│                         │   http4s BlazeClient     │         │
│                         └────────────┬────────────┘         │
└──────────────────────────────────────┼──────────────────────┘
                                       │ GET /rates?pair=...
┌──────────────────────────────────────▼──────────────────────┐
│              paidyinc/one-frame  (port 8080)                 │
│              Docker · 1000 req/day limit                     │
└─────────────────────────────────────────────────────────────┘
```

### Constraint math

| Factor | Value |
|--------|-------|
| One-Frame limit | 1,000 req/day |
| Required throughput | 10,000+ req/day |
| Max staleness | 5 minutes |
| Chosen refresh interval | **4 minutes** |
| Pairs per refresh call | **72** (all at once, single request) |
| Refresh calls/day | 360 << 1,000 ✅ |
| Requests served from cache | unlimited (in-memory Ref) |

---

## 2. Backend Implementation

### 2.1 Missing http4s artifact — `project/Dependencies.scala` + `build.sbt`

`http4s-blaze-client` is not a new library — it is part of http4s (`0.22.15`)
which is already a dependency. http4s intentionally splits server and client
into separate artifacts so you only pull in what you need. The server artifact
is already present; the client artifact is missing.

**`project/Dependencies.scala`** — add the definition alongside the existing http4s lines:
```scala
lazy val http4sClient = http4s("http4s-blaze-client")
```

**`build.sbt`** — add it to `libraryDependencies`:
```scala
Libraries.http4sClient,
```

---

### 2.2 `OneFrameLive` — HTTP client interpreter

**File:** `src/main/scala/forex/services/rates/interpreters/OneFrameLive.scala`

**Responsibility:** Make a real HTTP call to One-Frame, decode the JSON response,
return a map of all pairs.

```
OneFrameLive[F[_]: Sync] extends Algebra[F]  ← NOT used directly by cache
                                                 exposed as a helper: fetchAll
```

**One-Frame response shape to decode:**

```json
[
  {
    "from": "USD",
    "to":   "JPY",
    "bid":  0.61,
    "ask":  0.82,
    "price": 0.715,
    "time_stamp": "2019-01-01T00:00:00.000Z"
  }
]
```

**Key design points:**
- Fetches **all 72 pairs in one call** — build the query string from all
  `Currency` values cross-product with themselves (excluding same-currency pairs)
- Returns `F[Error Either Map[Rate.Pair, Rate]]` to the cache layer
- Token comes from `OneFrameConfig`, not hardcoded
- Use `circe-parser` + manual decoder — `time_stamp` field name differs from
  the domain `timestamp` so auto-derivation needs care

**Pseudo-structure:**

```scala
class OneFrameLive[F[_]: Sync](
    client: Client[F],
    config: OneFrameConfig
) {
  def fetchAll: F[Error Either Map[Rate.Pair, Rate]] = {
    val uri    = buildUri(config.baseUrl, allPairs)
    val request = Request[F](uri = uri)
                    .putHeaders(Header("token", config.token))
    client.expect[List[OneFrameResponse]](request)
          .map(responses => Right(toRateMap(responses)))
          .handleErrorWith(e => F.pure(Left(Error.OneFrameLookupFailed(e.getMessage))))
  }
}
```

---

### 2.3 `OneFrameCache` — cache + background refresh

**File:** `src/main/scala/forex/services/rates/interpreters/OneFrameCache.scala`

**Responsibility:** Maintain a `Ref` of all rates, refresh it on a schedule,
serve reads instantly from memory.

**Implements:** `Algebra[F]` — this is the interpreter wired into Module.

```scala
class OneFrameCache[F[_]: Concurrent: Timer](
    ref:  Ref[F, Map[Rate.Pair, Rate]],
    live: OneFrameLive[F],
    config: OneFrameConfig
) extends Algebra[F] {

  // Called on every consumer request — O(1) map lookup
  override def get(pair: Rate.Pair): F[Error Either Rate] =
    ref.get.map { cache =>
      cache.get(pair).toRight(Error.OneFrameLookupFailed(s"No rate for $pair"))
    }

  // Background loop — runs forever, refreshes every config.refreshInterval
  val backgroundRefresh: Stream[F, Unit] =
    Stream.fixedDelay[F](config.refreshInterval) >>
      Stream.eval(live.fetchAll.flatMap {
        case Right(rates) => ref.set(rates)
        case Left(err)    => Logger[F].warn(s"Refresh failed: $err")
                             // keep stale cache — better than empty
      })
}

object OneFrameCache {
  // Smart constructor — fetches once eagerly before returning,
  // then starts background fiber
  def resource[F[_]: Concurrent: Timer](
      live: OneFrameLive[F],
      config: OneFrameConfig
  ): Resource[F, Algebra[F]] =
    for {
      initial <- Resource.eval(live.fetchAll.rethrow)  // fail fast on startup
      ref     <- Resource.eval(Ref.of[F, Map[Rate.Pair, Rate]](initial))
      cache    = new OneFrameCache[F](ref, live, config)
      _       <- cache.backgroundRefresh.compile.drain.background
    } yield cache
}
```

**Why `Resource`?** It ties the background fiber lifecycle to the application
lifecycle. When the server shuts down, the fiber is automatically cancelled.

---

### 2.4 `Interpreters.scala` — add factory methods

```scala
object Interpreters {
  def dummy[F[_]: Applicative]: Algebra[F] =
    new OneFrameDummy[F]()

  def live[F[_]: Sync](
      client: Client[F],
      config: OneFrameConfig
  ): OneFrameLive[F] =
    new OneFrameLive[F](client, config)

  def cached[F[_]: Concurrent: Timer](
      live: OneFrameLive[F],
      config: OneFrameConfig
  ): Resource[F, Algebra[F]] =
    OneFrameCache.resource[F](live, config)
}
```

---

### 2.5 `Module.scala` — wire everything

```scala
class Module[F[_]: Concurrent: Timer](
    config: ApplicationConfig,
    cache:  RatesService[F]       // injected as Resource
) {
  private val ratesProgram   = RatesProgram[F](cache)
  private val ratesHttpRoutes = new RatesHttpRoutes[F](ratesProgram).routes
  // ... middleware same as before
}
```

`Main.scala` becomes:

```scala
def stream(ec: ExecutionContext): Stream[F, Unit] =
  for {
    config <- Config.stream("app")
    client <- Stream.resource(BlazeClientBuilder[F](ec).resource)
    live    = Interpreters.live[F](client, config.oneFrame)
    cache  <- Stream.resource(Interpreters.cached[F](live, config.oneFrame))
    module  = new Module[F](config, cache)
    _      <- BlazeServerBuilder[F](ec)
                .bindHttp(config.http.port, config.http.host)
                .withHttpApp(module.httpApp)
                .serve
  } yield ()
```

---

## 3. Caching Strategy

### Chosen: Proactive batch in-memory cache

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Proactive batch** (chosen) | Bounded quota usage; O(1) reads; warm on startup | Fetches pairs nobody requested | ✅ Best fit |
| Reactive per-request cache | Only fetches needed pairs | Can burst quota; cold misses | ❌ Quota risk |
| Redis external cache | Persistent across restarts | Overkill; extra infrastructure | ❌ Not needed |
| Streaming `/streaming/rates` | Push-based; no polling | Complex reconnect logic; harder to test | ❌ Overcomplicated |

### Cache state machine

```
App start
    │
    ▼
OneFrameLive.fetchAll()   ← single batch request, all 72 pairs
    │
    ├─ Left(error) ──► FAIL FAST — don't start server with empty cache
    │
    └─ Right(rates) ──► Ref.of(rates)
                            │
                            ├──► Server starts accepting requests
                            │
                            └──► Background fiber:
                                   every 4 min → fetchAll()
                                     ├─ success → ref.set(newRates)
                                     └─ failure → log warn, keep stale cache
                                                  (stale < 5 min SLA for 1 missed refresh)
```

### Staleness guarantee

- Refresh every **4 minutes**
- If one refresh fails, next retry is in 4 more minutes
- Worst case staleness: **8 minutes** (two consecutive failures)
- To guarantee the 5-minute SLA strictly: use **2-minute** refresh interval
  (720 calls/day — still under 1000) or add retry on failure

### All 72 pairs generation

```scala
val allPairs: List[Rate.Pair] =
  for {
    from <- Currency.values   // need to add .values to Currency object
    to   <- Currency.values
    if from != to
  } yield Rate.Pair(from, to)
```

Requires adding `val values: List[Currency]` to the `Currency` companion object.

---

## 4. Error Handling

### Current problem

`RatesHttpRoutes` calls `Sync[F].fromEither` which **throws** on Left,
returning a generic 500. The assignment explicitly asks for descriptive errors.

### Fix: proper HTTP error responses

```scala
// In RatesHttpRoutes
rates.get(request).flatMap {
  case Right(rate) =>
    Ok(rate.asGetApiResponse)
  case Left(err) =>
    err match {
      case Error.RateLookupFailed(msg) =>
        NotFound(ErrorResponse(msg))
      case _ =>
        InternalServerError(ErrorResponse("Unexpected error"))
    }
}
```

```scala
// New error response model in http/rates/Protocol.scala
final case class ErrorResponse(error: String)
implicit val errorEncoder: Encoder[ErrorResponse] = deriveConfiguredEncoder
```

### Fix: `Currency.fromString` is unsafe

Currently throws `MatchError` on unknown input. The query param decoder wraps
this in `QueryParamDecoder` which will return a `400 Bad Request` automatically
if it fails — but the exception message is ugly. Better:

```scala
def fromString(s: String): Either[String, Currency] = s.toUpperCase match {
  case "AUD" => Right(AUD)
  // ...
  case other => Left(s"Unsupported currency: $other")
}
```

Update `QueryParams.scala` to use `QueryParamDecoder.fromUnsafeCast` or
a validated decoder that returns `400` with a clear message.

### Error layer map

```
OneFrameLive error    →  services.rates.errors.Error.OneFrameLookupFailed
        │
        ▼  toProgramError()
programs.rates.errors.Error.RateLookupFailed
        │
        ▼  HTTP route handler
HTTP 404 / 503 with JSON body { "error": "..." }
```

---

## 5. Configuration

### Updated `ApplicationConfig.scala`

```scala
case class ApplicationConfig(
    http:     HttpConfig,
    oneFrame: OneFrameConfig
)

case class HttpConfig(
    host:    String,
    port:    Int,
    timeout: FiniteDuration
)

case class OneFrameConfig(
    baseUrl:         String,
    token:           String,
    refreshInterval: FiniteDuration
)
```

### Updated `application.conf`

```hocon
app {
  http {
    host    = "0.0.0.0"
    port    = 9090
    timeout = 40 seconds
  }

  one-frame {
    base-url         = "http://localhost:8080"
    base-url         = ${?ONE_FRAME_URL}          # overridden by env var in Docker
    token            = "10dc303535874aeccc86a8251e6992f5"
    token            = ${?ONE_FRAME_TOKEN}
    refresh-interval = 4 minutes
  }
}
```

The `${?VAR}` syntax is HOCON's optional env var override — if the env var
is not set the default is used, so local dev works without Docker.

---

## 6. Testing Strategy

### Philosophy

- **Unit tests** — pure logic, no IO, no network, no Docker
- **Integration tests** — require Docker (tagged, opt-in)
- **Property tests** — scalacheck generators for domain types
- **No mocking frameworks** — use tagless final to swap implementations

### 6.1 Test file structure

```
src/test/scala/forex/
├── domain/
│   └── CurrencySpec.scala          — fromString, allPairs generation
├── services/rates/
│   ├── OneFrameCacheSpec.scala     — cache logic, staleness, error fallback
│   └── OneFrameLiveSpec.scala      — JSON decoding, request building
├── programs/rates/
│   └── ProgramSpec.scala           — error mapping toProgramError
├── http/rates/
│   └── RatesHttpRoutesSpec.scala   — route tests with in-memory service
└── it/
    └── IntegrationSpec.scala       — tagged, requires Docker
```

---

### 6.2 Unit Tests

#### `CurrencySpec.scala`

```scala
class CurrencySpec extends AnyFunSuite with Matchers {

  test("fromString returns Right for all valid currencies") {
    Currency.values.foreach { c =>
      Currency.fromString(c.show) shouldBe Right(c)
    }
  }

  test("fromString returns Left for unknown currency") {
    Currency.fromString("XXX") shouldBe Left("Unsupported currency: XXX")
  }

  test("allPairs contains exactly 72 pairs") {
    Currency.allPairs should have size 72
  }

  test("allPairs contains no self-pairs") {
    Currency.allPairs.foreach { p => p.from should not be p.to }
  }

  test("allPairs contains no duplicates") {
    Currency.allPairs.distinct should have size 72
  }
}
```

#### `OneFrameCacheSpec.scala`

```scala
class OneFrameCacheSpec extends AnyFunSuite with Matchers {

  // Build a fake in-memory Algebra for testing — no real HTTP
  def fakeService(rates: Map[Rate.Pair, Rate]): Algebra[IO] =
    new OneFrameCache[IO](
      ref    = Ref.unsafe[IO, Map[Rate.Pair, Rate]](rates),
      live   = ??? // not called in unit tests — use a stub
      config = ???
    )

  test("get returns rate for known pair") {
    val pair = Rate.Pair(Currency.USD, Currency.JPY)
    val rate = Rate(pair, Price(BigDecimal("110.5")), Timestamp.now)
    val svc  = fakeService(Map(pair -> rate))

    svc.get(pair).unsafeRunSync() shouldBe Right(rate)
  }

  test("get returns error for unknown pair") {
    val svc  = fakeService(Map.empty)
    val pair = Rate.Pair(Currency.USD, Currency.JPY)

    svc.get(pair).unsafeRunSync() shouldBe a [Left[_, _]]
  }

  test("background refresh updates the cache") {
    // Use a counter Ref to confirm fetchAll was called
    // ...
  }
}
```

#### `RatesHttpRoutesSpec.scala` — in-memory HTTP testing

```scala
// http4s provides a way to run routes against a fake Request without a real server
class RatesHttpRoutesSpec extends AnyFunSuite with Matchers with Http4sClientDsl[IO] {

  val goodRate = Rate(
    Rate.Pair(Currency.USD, Currency.JPY),
    Price(BigDecimal("110.5")),
    Timestamp.now
  )

  // Fake program — no network needed
  val fakeProgram: RatesProgram[IO] = new rates.Algebra[IO] {
    def get(req: GetRatesRequest): IO[Error Either Rate] =
      IO.pure(Right(goodRate))
  }

  val routes = new RatesHttpRoutes[IO](fakeProgram).routes.orNotFound

  test("GET /rates?from=USD&to=JPY returns 200 with JSON") {
    val req  = Request[IO](GET, uri"/rates?from=USD&to=JPY")
    val resp = routes.run(req).unsafeRunSync()

    resp.status shouldBe Status.Ok
    // decode body and assert fields
  }

  test("GET /rates with unknown currency returns 400") {
    val req  = Request[IO](GET, uri"/rates?from=USD&to=XXX")
    val resp = routes.run(req).unsafeRunSync()

    resp.status shouldBe Status.BadRequest
  }

  test("GET /rates with service error returns 503") {
    val failingProgram: RatesProgram[IO] = new rates.Algebra[IO] {
      def get(req: GetRatesRequest): IO[Error Either Rate] =
        IO.pure(Left(Error.RateLookupFailed("One-Frame unavailable")))
    }
    val failRoutes = new RatesHttpRoutes[IO](failingProgram).routes.orNotFound
    val req  = Request[IO](GET, uri"/rates?from=USD&to=JPY")
    val resp = failRoutes.run(req).unsafeRunSync()

    resp.status shouldBe Status.ServiceUnavailable
  }
}
```

---

### 6.3 Property-Based Tests

```scala
class CurrencyPropertySpec extends AnyFunSuite with ScalaCheckSuite {

  // Arbitrary generator for Currency
  implicit val arbCurrency: Arbitrary[Currency] =
    Arbitrary(Gen.oneOf(Currency.values))

  // Arbitrary generator for Rate.Pair (from != to)
  implicit val arbPair: Arbitrary[Rate.Pair] = Arbitrary(
    for {
      from <- arbitrary[Currency]
      to   <- arbitrary[Currency].suchThat(_ != from)
    } yield Rate.Pair(from, to)
  )

  property("fromString(show(c)) == Right(c) for all currencies") {
    forAll { (c: Currency) =>
      Currency.fromString(c.show) == Right(c)
    }
  }

  property("any valid pair is contained in allPairs") {
    forAll { (pair: Rate.Pair) =>
      Currency.allPairs.contains(pair)
    }
  }
}
```

---

### 6.4 Test commands

```bash
sbt test                   # run all unit tests
sbt "testOnly *CacheSpec"  # run single suite
sbt testCoverage           # if scoverage plugin added
```

---

## 7. Real Integration Testing

### Strategy

Integration tests run against a **real One-Frame Docker container**.
They are tagged so they don't run in normal `sbt test` — only explicitly.

### 7.1 Tag setup

```scala
// src/test/scala/forex/it/DockerTag.scala
import org.scalatest.Tag
object DockerTest extends Tag("forex.it.DockerTest")
```

Run only integration tests:
```bash
sbt "testOnly * -- -n forex.it.DockerTest"
```

### 7.2 `IntegrationSpec.scala`

```scala
class IntegrationSpec extends AnyFunSuite with Matchers with BeforeAndAfterAll {

  // Assumes one-frame is running on localhost:8080
  // In CI: started by docker-compose before this suite runs

  val baseUrl = "http://localhost:9090"   // forex-proxy

  test("GET /rates?from=USD&to=JPY returns 200 and valid price", DockerTest) {
    // Use sttp or http4s client to hit the real running service
    val response = httpGet(s"$baseUrl/rates?from=USD&to=JPY")

    response.status  shouldBe 200
    response.body    should include ("price")
    response.body    should include ("timestamp")
  }

  test("rate is not stale — timestamp within 5 minutes", DockerTest) {
    val response = httpGet(s"$baseUrl/rates?from=EUR&to=GBP")
    val body     = parseJson(response.body)
    val ts       = Instant.parse(body("timestamp").asString)
    val age      = Duration.between(ts, Instant.now())

    age.toMinutes should be < 5L
  }

  test("unknown currency returns 400", DockerTest) {
    val response = httpGet(s"$baseUrl/rates?from=USD&to=XXX")
    response.status shouldBe 400
  }

  test("10000 requests all return 200 without hitting One-Frame limit", DockerTest) {
    // Fire 10000 requests concurrently using fs2 or parallel IO
    val results = (1 to 10000).toList.parTraverse { _ =>
      httpGet(s"$baseUrl/rates?from=USD&to=JPY")
    }.unsafeRunSync()

    results.count(_.status == 200) shouldBe 10000
  }
}
```

### 7.3 Docker Compose for integration tests

```yaml
# docker-compose.it.yml  (separate from dev compose)
services:
  one-frame:
    image: paidyinc/one-frame
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "-H",
             "token: 10dc303535874aeccc86a8251e6992f5",
             "http://localhost:8080/rates?pair=USDJPY"]
      interval: 5s
      timeout: 3s
      retries: 5

  forex-proxy:
    build: .
    ports:
      - "9090:9090"
    depends_on:
      one-frame:
        condition: service_healthy
    environment:
      ONE_FRAME_URL: http://one-frame:8080
    healthcheck:
      test: ["CMD", "curl", "-f",
             "http://localhost:9090/rates?from=USD&to=JPY"]
      interval: 5s
      timeout: 3s
      retries: 10
```

```bash
# Run integration tests locally
docker compose -f docker-compose.it.yml up -d
sbt "testOnly * -- -n forex.it.DockerTest"
docker compose -f docker-compose.it.yml down
```

---

## 8. CI/CD Pipeline

### Platform: GitHub Actions

```
.github/
└── workflows/
    ├── ci.yml      — runs on every push / PR
    └── cd.yml      — runs on merge to main (optional for demo)
```

### 8.1 `ci.yml` — Continuous Integration

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:

  # ── Unit tests ──────────────────────────────────────────────
  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Java 17
        uses: actions/setup-java@v4
        with:
          java-version: "17"
          distribution: "temurin"
          cache: "sbt"

      - name: Run unit tests
        working-directory: forex-mtl
        run: sbt test

      - name: Check formatting
        working-directory: forex-mtl
        run: sbt scalafmtCheck

  # ── Integration tests ───────────────────────────────────────
  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: test       # only run if unit tests pass

    steps:
      - uses: actions/checkout@v4

      - name: Setup Java 17
        uses: actions/setup-java@v4
        with:
          java-version: "17"
          distribution: "temurin"
          cache: "sbt"

      - name: Pull One-Frame image
        run: docker pull paidyinc/one-frame

      - name: Start services
        working-directory: forex-mtl
        run: docker compose -f docker-compose.it.yml up -d --build

      - name: Wait for services healthy
        run: |
          echo "Waiting for forex-proxy..."
          timeout 60 bash -c \
            'until curl -sf http://localhost:9090/rates?from=USD\&to=JPY; do sleep 2; done'

      - name: Run integration tests
        working-directory: forex-mtl
        run: sbt "testOnly * -- -n forex.it.DockerTest"

      - name: Tear down
        if: always()
        working-directory: forex-mtl
        run: docker compose -f docker-compose.it.yml down

  # ── Build fat JAR ───────────────────────────────────────────
  build:
    name: Build Fat JAR
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v4

      - name: Setup Java 17
        uses: actions/setup-java@v4
        with:
          java-version: "17"
          distribution: "temurin"
          cache: "sbt"

      - name: Assemble JAR
        working-directory: forex-mtl
        run: sbt assembly

      - name: Upload JAR artifact
        uses: actions/upload-artifact@v4
        with:
          name: forex-assembly
          path: forex-mtl/target/scala-2.13/forex-assembly.jar
```

### 8.2 `cd.yml` — Build and push Docker image (optional)

```yaml
name: CD

on:
  push:
    branches: [main]

jobs:
  docker:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./forex-mtl
          push: true
          tags: |
            yourusername/forex-proxy:latest
            yourusername/forex-proxy:${{ github.sha }}
```

### 8.3 CI pipeline flow

```
git push / PR
      │
      ▼
  sbt test          ← unit tests + scalafmt check
      │
      ├─ fail ──► ❌ block PR
      │
      ▼
  sbt assembly      ← fat JAR compiles
  integration tests ← docker compose + real One-Frame
      │
      ├─ fail ──► ❌ block PR
      │
      ▼
  merge to main
      │
      ▼
  docker build+push ← CD (optional)
```

---

## 9. Demo Frontend

### Stack

| Tool | Purpose |
|------|---------|
| Vite + React 18 | Build tool + UI framework |
| TypeScript | Type safety |
| Tailwind CSS | Styling — dark theme matching Paidy brand |
| fetch API | HTTP calls to forex-proxy |
| No backend changes needed | Calls existing GET /rates endpoint |

### What it shows

- Currency pair selector (from / to dropdowns)
- Live rate display with timestamp
- "Refresh" button + auto-refresh toggle (every 30s)
- Rate history chart (last 10 fetched values) using a simple SVG sparkline
- Cache age indicator (how old the rate is based on timestamp)
- Error states (unknown pair, service down)

### File structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── components/
    │   ├── CurrencySelector.tsx    — from/to dropdowns
    │   ├── RateDisplay.tsx         — big price + timestamp
    │   ├── Sparkline.tsx           — SVG mini chart of last N rates
    │   ├── CacheAgeBar.tsx         — progress bar 0–5 min staleness
    │   └── ErrorBanner.tsx         — error message display
    ├── hooks/
    │   └── useForexRate.ts         — fetch + polling logic
    └── types.ts                    — RateResponse type
```

### `types.ts`

```typescript
export interface RateResponse {
  from:      string;
  to:        string;
  price:     number;
  timestamp: string;   // ISO 8601
}

export type Currency =
  "AUD" | "CAD" | "CHF" | "EUR" |
  "GBP" | "NZD" | "JPY" | "SGD" | "USD";

export const CURRENCIES: Currency[] = [
  "AUD", "CAD", "CHF", "EUR",
  "GBP", "NZD", "JPY", "SGD", "USD"
];
```

### `useForexRate.ts`

```typescript
import { useState, useEffect, useCallback } from "react";
import { RateResponse, Currency } from "../types";

export function useForexRate(from: Currency, to: Currency, autoRefresh: boolean) {
  const [rate,    setRate]    = useState<RateResponse | null>(null);
  const [error,   setError]   = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<number[]>([]);

  const fetch_ = useCallback(async () => {
    if (from === to) return;
    setLoading(true);
    try {
      const res  = await fetch(`http://localhost:9090/rates?from=${from}&to=${to}`);
      if (!res.ok) {
        const body = await res.json();
        setError(body.error ?? "Request failed");
        return;
      }
      const data: RateResponse = await res.json();
      setRate(data);
      setError(null);
      setHistory(h => [...h.slice(-9), data.price]);
    } catch (e) {
      setError("Service unavailable");
    } finally {
      setLoading(false);
    }
  }, [from, to]);

  useEffect(() => { fetch_(); }, [fetch_]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(fetch_, 30_000);
    return () => clearInterval(id);
  }, [fetch_, autoRefresh]);

  return { rate, error, loading, history, refresh: fetch_ };
}
```

### `App.tsx` (sketch)

```tsx
export default function App() {
  const [from, setFrom]               = useState<Currency>("USD");
  const [to,   setTo]                 = useState<Currency>("JPY");
  const [autoRefresh, setAutoRefresh] = useState(false);
  const { rate, error, loading, history, refresh } =
    useForexRate(from, to, autoRefresh);

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center p-8">
      <h1 className="text-3xl font-bold text-purple-400 mb-8">
        Forex Rate Proxy · Demo
      </h1>

      <CurrencySelector from={from} to={to}
                        onFromChange={setFrom} onToChange={setTo} />

      {error   && <ErrorBanner message={error} />}
      {loading && <p className="text-gray-400">Loading...</p>}
      {rate    && <RateDisplay rate={rate} />}
      {rate    && <CacheAgeBar timestamp={rate.timestamp} maxMinutes={5} />}
      {history.length > 1 && <Sparkline values={history} />}

      <div className="flex gap-4 mt-6">
        <button onClick={refresh}
                className="px-4 py-2 bg-purple-600 rounded hover:bg-purple-700">
          Refresh
        </button>
        <label className="flex items-center gap-2 text-gray-300">
          <input type="checkbox" checked={autoRefresh}
                 onChange={e => setAutoRefresh(e.target.checked)} />
          Auto-refresh (30s)
        </label>
      </div>
    </div>
  );
}
```

### Running the frontend

```bash
cd frontend
npm install
npm run dev   # starts on http://localhost:5173
```

### Add to docker-compose.yml for full-stack demo

```yaml
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    depends_on:
      - forex-proxy
    environment:
      VITE_API_URL: http://localhost:9090
```

Frontend `Dockerfile`:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
```

---

## 10. File & Folder Map

```
interview/
├── STRATEGY.md                          — job strategy & setup notes
├── SPEC.md                              — this document
├── codebase_report.pdf                  — generated analysis report
├── generate_report.py                   — reportlab PDF generator
│
├── forex-mtl/                           — main Scala service
│   ├── build.sbt                        — + http4s-blaze-client, sbt-assembly
│   ├── Dockerfile                       — multi-stage fat JAR build
│   ├── docker-compose.yml               — dev: one-frame + forex-proxy
│   ├── docker-compose.it.yml            — integration tests: healthchecks
│   ├── project/
│   │   ├── Dependencies.scala           — + http4sClient
│   │   └── plugins.sbt                  — + sbt-assembly
│   └── src/
│       ├── main/
│       │   ├── resources/
│       │   │   ├── application.conf     — + one-frame config block
│       │   │   └── logback.xml
│       │   └── scala/forex/
│       │       ├── Main.scala           — updated: Resource-based wiring
│       │       ├── Module.scala         — updated: accepts cache as param
│       │       ├── config/
│       │       │   ├── ApplicationConfig.scala  — + OneFrameConfig
│       │       │   └── Config.scala
│       │       ├── domain/
│       │       │   ├── Currency.scala   — + values list + safe fromString
│       │       │   ├── Price.scala
│       │       │   ├── Rate.scala
│       │       │   └── Timestamp.scala
│       │       ├── services/rates/
│       │       │   ├── algebra.scala
│       │       │   ├── errors.scala
│       │       │   ├── Interpreters.scala       — + live + cached factories
│       │       │   └── interpreters/
│       │       │       ├── OneFrameDummy.scala  — keep (used in tests)
│       │       │       ├── OneFrameLive.scala   — NEW: real HTTP client
│       │       │       └── OneFrameCache.scala  — NEW: Ref + background fiber
│       │       ├── programs/rates/
│       │       │   ├── Algebra.scala
│       │       │   ├── Program.scala
│       │       │   ├── Protocol.scala
│       │       │   └── errors.scala
│       │       └── http/
│       │           ├── package.scala
│       │           └── rates/
│       │               ├── RatesHttpRoutes.scala — updated: proper error handling
│       │               ├── Protocol.scala        — + ErrorResponse
│       │               ├── QueryParams.scala     — updated: safe Currency decoder
│       │               └── Converters.scala
│       └── test/scala/forex/
│           ├── domain/
│           │   └── CurrencySpec.scala
│           ├── services/rates/
│           │   ├── OneFrameCacheSpec.scala
│           │   └── OneFrameLiveSpec.scala
│           ├── programs/rates/
│           │   └── ProgramSpec.scala
│           ├── http/rates/
│           │   └── RatesHttpRoutesSpec.scala
│           └── it/
│               ├── DockerTag.scala
│               └── IntegrationSpec.scala
│
├── frontend/                            — React demo UI
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── types.ts
│       ├── components/
│       │   ├── CurrencySelector.tsx
│       │   ├── RateDisplay.tsx
│       │   ├── Sparkline.tsx
│       │   ├── CacheAgeBar.tsx
│       │   └── ErrorBanner.tsx
│       └── hooks/
│           └── useForexRate.ts
│
└── .github/
    └── workflows/
        ├── ci.yml                       — unit + integration + build
        └── cd.yml                       — docker push on merge to main
```

---

## 11. Implementation Order

Work in this exact order — each step builds on the previous.

```
Step  Deliverable                                  Validates
────  ──────────────────────────────────────────   ─────────────────────────────
  1   Add http4s-blaze-client to build.sbt         sbt compile
  2   Add OneFrameConfig to ApplicationConfig      sbt compile
  3   Update application.conf with one-frame block sbt compile
  4   Fix Currency.fromString → Either             CurrencySpec passes
  5   Add Currency.values list                     CurrencySpec allPairs passes
  6   Implement OneFrameLive (fetchAll)             sbt compile + manual curl test
  7   Implement OneFrameCache (Ref + fiber)        OneFrameCacheSpec passes
  8   Update Interpreters.scala (live + cached)    sbt compile
  9   Update Module.scala + Main.scala             sbt run + docker compose up
 10   Fix HTTP error handling in RatesHttpRoutes   RatesHttpRoutesSpec passes
 11   Write remaining unit tests                   sbt test — all green
 12   Write property tests                         sbt test — all green
 13   Create docker-compose.it.yml                 docker compose -f it up works
 14   Write IntegrationSpec                        integration suite passes
 15   Create .github/workflows/ci.yml              push to GitHub — CI green
 16   Scaffold frontend                            npm run dev shows rate
 17   Polish README with constraint math           ready to submit
```

---

*Last updated: 2026-02-27*
