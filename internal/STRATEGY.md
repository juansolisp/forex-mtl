# Paidy Scala Product Engineer — Interview Strategy & Setup

## Role Overview

**Position:** Scala Product Engineer
**Company:** Paidy (payments platform, fintech)
**Status:** Passed manager round → Take-home coding assignment

---

## Assignment Summary

Build a local proxy for Forex exchange rates — a service that other internal services consume to get exchange rates without caring about third-party provider specifics.

**Core requirements:**
- Return an exchange rate given 2 supported currencies
- Rate must not be older than 5 minutes
- Support at least 10,000 successful requests per day using 1 API token

**Scaffold location:** `/home/juan/paidy/interview/forex-mtl`

---

## One-Frame Service (Third-Party Provider)

### Running locally

```bash
docker pull paidyinc/one-frame
docker run -p 8080:8080 paidyinc/one-frame
```

Restart the container to reset the daily quota during development.

### API

**GET /rates**
```bash
curl -H "token: 10dc303535874aeccc86a8251e6992f5" \
  'localhost:8080/rates?pair=USDJPY&pair=EURUSD'
```
- Query param: `pair` — concatenation of two currency codes (e.g. `USDJPY`), multiple allowed per request
- Header: `token: 10dc303535874aeccc86a8251e6992f5`
- Response: JSON array with `from`, `to`, `bid`, `ask`, `price`, `time_stamp`
- **Limit: 1000 requests/day**

**GET /streaming/rates**
- Same params and auth as `/rates`
- Returns a continuous stream of rate updates
- Not used in this implementation (see design decision below)

### Supported currencies
All ISO 4217 codes supported with randomly generated rates. The scaffold defines 9: AUD, CAD, CHF, EUR, GBP, NZD, JPY, SGD, USD.

---

## Constraint Analysis

| Factor | Value |
|--------|-------|
| One-Frame daily limit | 1,000 requests |
| Max rate staleness | 5 minutes |
| 5-minute windows per day | 288 |
| Currencies in domain | 9 |
| Directed pairs (9×8) | 72 |
| All 72 pairs in 1 request | Yes — One-Frame supports multiple `pair` params |
| Refresh every 4 min = calls/day | **360** — well under 1,000 limit |

**Strategy:** Proactively fetch all 72 pairs in a single batch request every 4 minutes, cache results in memory. Serve all 10k+ daily requests from cache.

---

## Codebase Architecture

The scaffold uses **tagless final / MTL pattern** throughout. Key layers:

```
HTTP Request (GET /rates?from=USD&to=EUR)
    ↓
RatesHttpRoutes        — http4s DSL, query param extraction
    ↓
RatesProgram           — EitherT error mapping, business logic
    ↓
RatesService           — Algebra[F[_]] interface
    ↓
OneFrameLive (to build) — real HTTP client to One-Frame
    + OneFrameCache (to build) — Ref[F, Map[Pair, Rate]] with background refresh
```

### Key files

| File | Status | Notes |
|------|--------|-------|
| `services/rates/Algebra.scala` | Done | `get(pair): F[Error Either Rate]` |
| `services/rates/interpreters/OneFrameDummy.scala` | Stub | Returns hardcoded 100.0 — replace |
| `services/rates/Interpreters.scala` | Done | Add `live` factory method here |
| `programs/rates/Program.scala` | Done | EitherT wrapping, don't touch |
| `http/rates/RatesHttpRoutes.scala` | Done | GET /rates?from=X&to=Y |
| `Module.scala` | Done | Wire new interpreter here |
| `config/ApplicationConfig.scala` | Done | Add OneFrame config (url, token) |

### Architectural patterns used

- **Tagless final**: Algebras are traits with `F[_]` — don't break this pattern
- **EitherT**: Error handling in programs layer
- **Ref[F, ...]**: cats-effect thread-safe mutable state — use this for cache
- **Manual DI**: No framework, wired in `Module.scala`
- **circe-generic-extras**: JSON with snake_case config

---

## Implementation Plan

### Files to create

```
services/rates/interpreters/OneFrameLive.scala   — HTTP client (http4s BlazeClient)
services/rates/interpreters/OneFrameCache.scala  — Ref cache + background fiber refresh
src/test/scala/forex/...                         — tests
```

### Files to modify

```
services/rates/Interpreters.scala     — add live() factory
config/ApplicationConfig.scala        — add OneFrameConfig(url, token, refreshInterval)
src/main/resources/application.conf  — add one-frame config block
Module.scala                          — switch dummy → live + cache
```

### Phase order

1. **Read the codebase** — understand tagless final, EitherT, how Module wires things
2. **Design on paper** — cache data structure, refresh logic, error cases
3. **Config** — add OneFrame URL + token to ApplicationConfig
4. **OneFrameLive** — HTTP client, JSON decoder for One-Frame response, error mapping
5. **OneFrameCache** — `Ref[F, Map[Rate.Pair, Rate]]`, background fiber with `fs2.Stream`
6. **Wire into Module** — replace dummy
7. **Tests** — unit tests for cache, error handling, property tests for pairs
8. **README + polish** — run instructions, design rationale, tradeoff notes

---

## Design Decisions to Document

### Proactive batch caching vs. reactive per-request caching

Chosen: **proactive batch** — fetch all 72 pairs every 4 minutes in one request.

Reactive (cache on first miss, refresh on expiry) would work but risks bursting the quota if many unique pairs are requested simultaneously. Proactive guarantees bounded usage regardless of traffic pattern.

### Polling vs. streaming

Chosen: **polling** (`/rates`) over streaming (`/streaming/rates`).

The 5-minute staleness SLA is well-served by a 4-minute polling interval. Polling is simpler to reason about, test, and operate. Streaming would add complexity (backpressure, reconnection logic) with no benefit at this scale.

### Cache warmup on startup

The cache should be populated before the server starts accepting requests. Use `Resource` or start the background fiber and do an initial fetch before binding the port, to avoid serving empty cache responses on cold start.

---

## Tests to Write

- Unit test: cache returns correct rate for a pair
- Unit test: cache returns error when rate is too old (if implementing timestamp validation)
- Unit test: all 72 pairs are generated correctly from the 9 currencies
- Property test: any valid pair request returns a non-empty result from cache
- Integration test stub: runs against Docker One-Frame service

---

## AI Usage — Honest Framing for Recruiters

**What to say when asked:**

> "Yes, I used AI as a tool — similar to documentation or Stack Overflow. I used it to quickly recall specific http4s client builder syntax and to scaffold circe JSON decoder boilerplate for the One-Frame response format. The architectural decisions — the caching strategy, using `Ref[F, ...]` for thread-safe state, how to fit into the existing tagless final pattern, the constraint math — I worked through myself. Tests were also written by me since they require understanding the actual behavior being tested."

**Why this framing works:**
- Honest — you will be asked follow-up questions; you must own every decision
- Positions AI as a productivity multiplier, not a replacement for thinking
- The hard signals (architecture, patterns, tradeoffs) are demonstrably yours
- Using AI tools competently is itself a signal of good engineering judgment at a modern tech company

---

## Local Docker Setup

### Overview

Two services run via Docker Compose:

| Service | Image | Port |
|---------|-------|------|
| `one-frame` | `paidyinc/one-frame` (pre-built) | 8080 |
| `forex-proxy` | Built from local source | 9090 |

The forex-proxy service exposes port 9090 externally to avoid conflict with one-frame on 8080. Internally, forex-proxy calls one-frame via the Docker network by service name (`http://one-frame:8080`).

### Files

```
interview/forex-mtl/
├── Dockerfile              — multi-stage build for the forex-proxy service
└── docker-compose.yml      — orchestrates both services together
```

### Dockerfile strategy (multi-stage)

**Stage 1 — build:** Uses `sbt` to compile and produce a fat JAR.
**Stage 2 — runtime:** Copies only the JAR into a slim JRE image.

This keeps the final image small and avoids shipping sbt/scala toolchain in production.

```
sbt (builder)  →  target/scala-2.13/forex-assembly-*.jar
                          ↓
eclipse-temurin:17-jre (runtime)  →  lean runnable image
```

### docker-compose.yml structure

```yaml
services:
  one-frame:          # pulled from Docker Hub, no build needed
    image: paidyinc/one-frame
    ports: 8080:8080

  forex-proxy:        # built from local Dockerfile
    build: .
    ports: 9090:9090
    depends_on: one-frame
    environment:
      ONE_FRAME_URL: http://one-frame:8080   # uses Docker network DNS
```

### Workflow

**First run (builds the image):**
```bash
cd /home/juan/paidy/interview/forex-mtl
docker compose up --build
```

**Subsequent runs (no rebuild):**
```bash
docker compose up
```

**Reset One-Frame quota (restart just that container):**
```bash
docker compose restart one-frame
```

**Rebuild only forex-proxy after code changes:**
```bash
docker compose up --build forex-proxy
```

**Tear down:**
```bash
docker compose down
```

### Verify both services are working

```bash
# One-Frame directly
curl -H "token: 10dc303535874aeccc86a8251e6992f5" \
  'localhost:8080/rates?pair=USDJPY'

# Forex proxy (your service)
curl 'localhost:9090/rates?from=USD&to=JPY'
```

### Port mapping rationale

- one-frame stays on 8080 (its default, matches docs)
- forex-proxy uses 9090 externally — avoids conflict, and clearly signals "this is our service"
- Inside Docker network, forex-proxy talks to `one-frame:8080` (no port conflict internally)

### sbt-assembly plugin

The Dockerfile build requires `sbt assembly` to produce a fat JAR. This needs the `sbt-assembly` plugin added to `project/plugins.sbt`:

```scala
addSbtPlugin("com.eed3si9n" % "sbt-assembly" % "2.2.0")
```

And a merge strategy in `build.sbt` to handle duplicate META-INF files:

```scala
assembly / assemblyMergeStrategy := {
  case PathList("META-INF", _*) => MergeStrategy.discard
  case x                        => (assembly / assemblyMergeStrategy).value(x)
}
```

---

## Key Things That Will Impress

1. **Show the constraint math in your README** — proves you understood the problem
2. **Proactive batch caching** — more sophisticated than naive reactive caching
3. **Tests** — most candidates skip them; the scaffold has zero
4. **Unhappy path handling** — One-Frame down, cache empty on startup, malformed response
5. **Stay in the tagless final pattern** — don't break the existing architecture style
6. **Descriptive errors** — the assignment explicitly asks for this
7. **Mention the streaming endpoint tradeoff** — shows you read the full docs
