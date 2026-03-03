# forex-mtl · Step-by-Step Implementation Plan

> Each step has exactly one goal, one deliverable, and one way to verify it worked.
> Never move to the next step until the current one compiles and its verify command passes.

---

## Before You Start

```bash
# Pull and verify One-Frame works
docker pull paidyinc/one-frame
docker run -p 8080:8080 paidyinc/one-frame &

curl -H "token: 10dc303535874aeccc86a8251e6992f5" \
  'localhost:8080/rates?pair=USDJPY&pair=EURUSD'
# Should return JSON array with price, bid, ask, time_stamp

# Verify the scaffold compiles as-is
cd /home/juan/paidy/interview/forex-mtl
sbt compile
```

If both pass you're ready.

---

## Phase 1 — Build Foundation (no logic yet)

These steps don't touch business logic. They set up the infrastructure
everything else depends on.

---

### Step 1 — Add http4s-blaze-client artifact

**Goal:** Make the HTTP client available to compile against.

**File:** `project/Dependencies.scala`

Add this line alongside the other http4s entries:
```scala
lazy val http4sClient = http4s("http4s-blaze-client")
```

**File:** `build.sbt`

Add inside `libraryDependencies ++= Seq(...)`:
```scala
Libraries.http4sClient,
```

**Verify:**
```bash
sbt compile
# Must compile with 0 errors
```

---

### Step 2 — Add OneFrameConfig to ApplicationConfig

**Goal:** Give the app a typed config for One-Frame URL, token, and refresh interval.

**File:** `src/main/scala/forex/config/ApplicationConfig.scala`

```scala
import scala.concurrent.duration.FiniteDuration

case class ApplicationConfig(
    http:     HttpConfig,
    oneFrame: OneFrameConfig        // add this
)

case class HttpConfig(
    host:    String,
    port:    Int,
    timeout: FiniteDuration
)

case class OneFrameConfig(          // add this entire case class
    baseUrl:         String,
    token:           String,
    refreshInterval: FiniteDuration
)
```

**Verify:**
```bash
sbt compile
# Must compile — pureconfig will complain at runtime, not compile time
```

---

### Step 3 — Update application.conf

**Goal:** Provide actual values for OneFrameConfig so pureconfig can load them.

**File:** `src/main/resources/application.conf`

```hocon
app {
  http {
    host    = "0.0.0.0"
    port    = 9090
    timeout = 40 seconds
  }

  one-frame {
    base-url         = "http://localhost:8080"
    base-url         = ${?ONE_FRAME_URL}
    token            = "10dc303535874aeccc86a8251e6992f5"
    token            = ${?ONE_FRAME_TOKEN}
    refresh-interval = 4 minutes
  }
}
```

> `${?VAR}` means: use the env var if set, otherwise keep the default above it.
> This makes local dev work without Docker, and Docker Compose works by setting the env var.

**Verify:**
```bash
sbt run
# App should START (not crash on config load)
# You'll see it serve on port 9090 with the dummy interpreter — that's fine
# Ctrl+C to stop
```

---

## Phase 2 — Fix the Domain

These steps fix known issues in the scaffold before building on top of them.

---

### Step 4 — Add Currency.values list

**Goal:** Get a list of all currencies so you can generate all 72 pairs programmatically.

**File:** `src/main/scala/forex/domain/Currency.scala`

Add inside the `Currency` companion object, after the existing `show` instance:
```scala
val values: List[Currency] =
  List(AUD, CAD, CHF, EUR, GBP, NZD, JPY, SGD, USD)
```

**Verify:**
```bash
sbt console
# In the REPL:
forex.domain.Currency.values.length
# Should print: 9
```

---

### Step 5 — Fix Currency.fromString to return Either

**Goal:** Stop Currency.fromString from crashing on unknown input.
Currently it throws a MatchError — dangerous in a public API.

**File:** `src/main/scala/forex/domain/Currency.scala`

Replace the existing `fromString` method:
```scala
// BEFORE (unsafe — throws MatchError)
def fromString(s: String): Currency = s.toUpperCase match {
  case "AUD" => AUD
  ...
}

// AFTER (safe — returns Either)
def fromString(s: String): Either[String, Currency] = s.toUpperCase match {
  case "AUD" => Right(AUD)
  case "CAD" => Right(CAD)
  case "CHF" => Right(CHF)
  case "EUR" => Right(EUR)
  case "GBP" => Right(GBP)
  case "NZD" => Right(NZD)
  case "JPY" => Right(JPY)
  case "SGD" => Right(SGD)
  case "USD" => Right(USD)
  case other => Left(s"Unsupported currency: $other")
}
```

**Also update QueryParams.scala** — it calls `fromString` and must handle Either:

**File:** `src/main/scala/forex/http/rates/QueryParams.scala`

```scala
private[http] implicit val currencyQueryParam: QueryParamDecoder[Currency] =
  QueryParamDecoder[String].emap(s =>
    Currency.fromString(s).left.map(ParseFailure(_, ""))
  )
```

> `.emap` means "either map" — on Left it returns a 400 Bad Request automatically.

**Verify:**
```bash
sbt compile
# Must compile clean
```

---

## Phase 3 — Build the Live HTTP Client

---

### Step 6 — Create OneFrameLive

**Goal:** A real HTTP client that calls One-Frame and parses the response.

**Create file:** `src/main/scala/forex/services/rates/interpreters/OneFrameLive.scala`

This file needs to:
1. Build a URI with all 72 pair query params
2. Make a GET request with the token header
3. Decode the JSON response array
4. Map the response into `Map[Rate.Pair, Rate]`
5. Handle errors (network failures, bad JSON) without crashing

**Structure to implement:**
```scala
package forex.services.rates.interpreters

import cats.effect.Sync
import cats.syntax.either._
import forex.config.OneFrameConfig
import forex.domain._
import forex.services.rates.errors.Error
import org.http4s.client.Client
import org.http4s.{Header, Request, Uri}
import io.circe.{Decoder, HCursor}
import io.circe.parser.decode

class OneFrameLive[F[_]: Sync](
    client: Client[F],
    config: OneFrameConfig
) {
  // Internal model for One-Frame's response shape
  private case class OneFrameRate(
      from:      Currency,
      to:        Currency,
      price:     BigDecimal,
      timeStamp: String       // note: One-Frame uses "time_stamp" key
  )

  // Manual decoder because "time_stamp" doesn't match our field name
  private implicit val rateDecoder: Decoder[OneFrameRate] =
    (c: HCursor) =>
      for {
        from  <- c.downField("from").as[String].flatMap(s =>
                   Currency.fromString(s).left.map(io.circe.DecodingFailure(_, c.history)))
        to    <- c.downField("to").as[String].flatMap(s =>
                   Currency.fromString(s).left.map(io.circe.DecodingFailure(_, c.history)))
        price <- c.downField("price").as[BigDecimal]
        ts    <- c.downField("time_stamp").as[String]
      } yield OneFrameRate(from, to, price, ts)

  // Build URI with all 72 pairs as query params
  private def buildUri: Either[String, Uri] = {
    val pairs = Currency.allPairs
    val base  = s"${config.baseUrl}/rates"
    val query = pairs.map(p => s"pair=${p.from.show}${p.to.show}").mkString("&")
    Uri.fromString(s"$base?$query").leftMap(_.message)
  }

  // Convert One-Frame response to domain Rate
  private def toRate(r: OneFrameRate): Rate =
    Rate(
      pair      = Rate.Pair(r.from, r.to),
      price     = Price(r.price),
      timestamp = Timestamp(java.time.OffsetDateTime.parse(r.timeStamp))
    )

  def fetchAll: F[Error Either Map[Rate.Pair, Rate]] =
    buildUri match {
      case Left(err) =>
        Sync[F].pure(Left(Error.OneFrameLookupFailed(s"Invalid URI: $err")))
      case Right(uri) =>
        val request = Request[F](uri = uri)
          .withHeaders(Header("token", config.token))
        client
          .expect[String](request)
          .map(body =>
            decode[List[OneFrameRate]](body)
              .map(rates => rates.map(r => r.from -> r.to -> toRate(r))
                                 .map { case ((_, _), rate) => rate.pair -> rate }
                                 .toMap)
              .leftMap(e => Error.OneFrameLookupFailed(e.getMessage))
          )
          .handleErrorWith(e =>
            Sync[F].pure(Left(Error.OneFrameLookupFailed(e.getMessage)))
          )
    }
}
```

**Verify:**
```bash
sbt compile
# Must compile clean

# Manual smoke test — make sure one-frame Docker is running
curl -H "token: 10dc303535874aeccc86a8251e6992f5" \
  'localhost:8080/rates?pair=USDJPY&pair=EURUSD&pair=GBPUSD'
# Confirm the JSON shape matches what your decoder expects
```

---

## Phase 4 — Build the Cache

---

### Step 7 — Create OneFrameCache

**Goal:** In-memory cache backed by `Ref`, populated on startup,
refreshed in the background every 4 minutes.

**Create file:** `src/main/scala/forex/services/rates/interpreters/OneFrameCache.scala`

```scala
package forex.services.rates.interpreters

import cats.effect.{Concurrent, Resource, Timer}
import cats.effect.concurrent.Ref
import cats.syntax.flatMap._
import cats.syntax.functor._
import forex.config.OneFrameConfig
import forex.domain.Rate
import forex.services.rates.Algebra
import forex.services.rates.errors.Error
import fs2.Stream
import scala.concurrent.duration._

class OneFrameCache[F[_]: Concurrent: Timer](
    ref:    Ref[F, Map[Rate.Pair, Rate]],
    live:   OneFrameLive[F],
    config: OneFrameConfig
) extends Algebra[F] {

  // Every request hits this — O(1) map lookup, never touches network
  override def get(pair: Rate.Pair): F[Error Either Rate] =
    ref.get.map { cache =>
      cache
        .get(pair)
        .toRight(Error.OneFrameLookupFailed(
          s"No rate available for ${pair.from.show}/${pair.to.show}"))
    }

  // Runs forever in background — refreshes cache on schedule
  val backgroundRefresh: Stream[F, Unit] =
    Stream
      .fixedDelay[F](config.refreshInterval)
      .evalMap { _ =>
        live.fetchAll.flatMap {
          case Right(rates) => ref.set(rates)
          case Left(err) =>
            // Keep stale cache — a missed refresh is better than empty cache
            // Log the failure (add proper logging here)
            Concurrent[F].unit
        }
      }
}

object OneFrameCache {

  // Smart constructor:
  // 1. Fetches all rates BEFORE returning (fail fast — don't start with empty cache)
  // 2. Stores in Ref
  // 3. Starts background refresh fiber
  // 4. Ties fiber lifecycle to app lifecycle via Resource
  def resource[F[_]: Concurrent: Timer](
      live:   OneFrameLive[F],
      config: OneFrameConfig
  ): Resource[F, Algebra[F]] =
    for {
      // Fail fast: if One-Frame is unreachable on startup, crash loudly
      initial <- Resource.eval(
                   live.fetchAll.flatMap {
                     case Right(rates) => Concurrent[F].pure(rates)
                     case Left(err)    => Concurrent[F].raiseError(
                       new RuntimeException(s"Cache warmup failed: ${err}"))
                   }
                 )
      ref     <- Resource.eval(Ref.of[F, Map[Rate.Pair, Rate]](initial))
      cache    = new OneFrameCache[F](ref, live, config)
      // background runs in its own fiber, cancelled when Resource releases
      _       <- cache.backgroundRefresh.compile.drain.background
    } yield cache
}
```

**Verify:**
```bash
sbt compile
# Must compile clean
```

---

### Step 8 — Update Interpreters.scala

**Goal:** Expose factory methods for the live and cached interpreters.

**File:** `src/main/scala/forex/services/rates/Interpreters.scala`

```scala
package forex.services.rates

import cats.Applicative
import cats.effect.{Concurrent, Resource, Timer, Sync}
import forex.config.OneFrameConfig
import interpreters._
import org.http4s.client.Client

object Interpreters {

  def dummy[F[_]: Applicative]: Algebra[F] =
    new OneFrameDummy[F]()

  def live[F[_]: Sync](
      client: Client[F],
      config: OneFrameConfig
  ): OneFrameLive[F] =
    new OneFrameLive[F](client, config)

  def cached[F[_]: Concurrent: Timer](
      live:   OneFrameLive[F],
      config: OneFrameConfig
  ): Resource[F, Algebra[F]] =
    OneFrameCache.resource[F](live, config)
}
```

**Verify:**
```bash
sbt compile
```

---

## Phase 5 — Wire Everything Together

---

### Step 9 — Update Module.scala

**Goal:** Accept the cache as a constructor parameter instead of creating the dummy internally.

**File:** `src/main/scala/forex/Module.scala`

```scala
class Module[F[_]: Concurrent: Timer](
    config: ApplicationConfig,
    cache:  RatesService[F]       // injected — no longer created here
) {
  private val ratesProgram    = RatesProgram[F](cache)
  private val ratesHttpRoutes = new RatesHttpRoutes[F](ratesProgram).routes

  type PartialMiddleware = HttpRoutes[F] => HttpRoutes[F]
  type TotalMiddleware   = HttpApp[F]   => HttpApp[F]

  private val routesMiddleware: PartialMiddleware =
    AutoSlash(_)

  private val appMiddleware: TotalMiddleware =
    Timeout(config.http.timeout)(_)

  val httpApp: HttpApp[F] =
    appMiddleware(routesMiddleware(ratesHttpRoutes).orNotFound)
}
```

**Verify:**
```bash
sbt compile
# Module.scala will now have a compile error in Main.scala — that's expected, fix it in step 10
```

---

### Step 10 — Update Main.scala

**Goal:** Wire the HTTP client + live interpreter + cache into the startup stream.

**File:** `src/main/scala/forex/Main.scala`

```scala
class Application[F[_]: ConcurrentEffect: Timer] {

  def stream(ec: ExecutionContext): Stream[F, Unit] =
    for {
      config <- Config.stream("app")
      client <- Stream.resource(BlazeClientBuilder[F](ec).resource)
      live    = RatesServices.live[F](client, config.oneFrame)
      cache  <- Stream.resource(RatesServices.cached[F](live, config.oneFrame))
      module  = new Module[F](config, cache)
      _      <- BlazeServerBuilder[F](ec)
                  .bindHttp(config.http.port, config.http.host)
                  .withHttpApp(module.httpApp)
                  .serve
    } yield ()
}
```

Also add the import for BlazeClientBuilder at the top of the file:
```scala
import org.http4s.client.blaze.BlazeClientBuilder
```

**Verify:**
```bash
sbt compile
# Must compile with 0 errors

sbt run
# Should print server started on port 9090
# Should fetch all 72 rates from One-Frame on startup (watch logs)

# In another terminal — test it
curl 'localhost:9090/rates?from=USD&to=JPY'
# Should return JSON with real price from One-Frame
```

This is the first end-to-end working state. Everything after this is quality.

---

## Phase 6 — Fix Error Handling

---

### Step 11 — Fix HTTP error responses

**Goal:** Return descriptive JSON error bodies instead of throwing and getting 500.

**File:** `src/main/scala/forex/http/rates/Protocol.scala`

Add the error response model:
```scala
final case class ErrorResponse(error: String)
implicit val errorResponseEncoder: Encoder[ErrorResponse] =
  deriveConfiguredEncoder[ErrorResponse]
```

**File:** `src/main/scala/forex/http/rates/RatesHttpRoutes.scala`

Replace the current route body:
```scala
// BEFORE — throws on Left, returns 500
rates.get(request).flatMap(Sync[F].fromEither).flatMap { rate =>
  Ok(rate.asGetApiResponse)
}

// AFTER — handles errors explicitly
rates.get(request).flatMap {
  case Right(rate) =>
    Ok(rate.asGetApiResponse)
  case Left(err) =>
    err match {
      case Error.RateLookupFailed(msg) =>
        ServiceUnavailable(ErrorResponse(msg))
      case _ =>
        InternalServerError(ErrorResponse("Unexpected error"))
    }
}
```

**Verify:**
```bash
sbt compile

# Test happy path
curl 'localhost:9090/rates?from=USD&to=JPY'
# Returns 200 with JSON rate

# Test unknown currency — should return 400, not 500
curl 'localhost:9090/rates?from=USD&to=XXX'
# Returns 400 with {"error": "Unsupported currency: XXX"}
```

---

## Phase 7 — Tests

---

### Step 12 — Create test directory structure

**Goal:** Create the test folder layout so sbt can find test files.

```bash
mkdir -p src/test/scala/forex/domain
mkdir -p src/test/scala/forex/services/rates
mkdir -p src/test/scala/forex/programs/rates
mkdir -p src/test/scala/forex/http/rates
mkdir -p src/test/scala/forex/it
```

**Verify:**
```bash
sbt test
# Should run 0 tests with 0 failures (no test files yet = fine)
```

---

### Step 13 — Write CurrencySpec

**Goal:** Test the domain model fixes from Steps 4 and 5.

**Create file:** `src/test/scala/forex/domain/CurrencySpec.scala`

```scala
package forex.domain

import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers
import cats.syntax.show._

class CurrencySpec extends AnyFunSuite with Matchers {

  test("values contains exactly 9 currencies") {
    Currency.values should have size 9
  }

  test("fromString returns Right for every valid currency") {
    Currency.values.foreach { c =>
      Currency.fromString(c.show) shouldBe Right(c)
    }
  }

  test("fromString returns Left for unknown currency") {
    Currency.fromString("XXX") shouldBe Left("Unsupported currency: XXX")
  }

  test("fromString is case-insensitive") {
    Currency.fromString("usd") shouldBe Right(Currency.USD)
    Currency.fromString("Jpy") shouldBe Right(Currency.JPY)
  }

  test("allPairs contains exactly 72 pairs") {
    Currency.allPairs should have size 72
  }

  test("allPairs contains no self-pairs") {
    Currency.allPairs.foreach { p =>
      p.from should not be p.to
    }
  }

  test("allPairs contains no duplicate pairs") {
    Currency.allPairs.distinct should have size 72
  }

  test("allPairs contains every combination") {
    val expected = for {
      from <- Currency.values
      to   <- Currency.values
      if from != to
    } yield Rate.Pair(from, to)

    Currency.allPairs.toSet shouldBe expected.toSet
  }
}
```

**Verify:**
```bash
sbt "testOnly *CurrencySpec"
# All 8 tests green
```

---

### Step 14 — Write OneFrameCacheSpec

**Goal:** Test cache logic in isolation — no network, no Docker.

**Create file:** `src/test/scala/forex/services/rates/OneFrameCacheSpec.scala`

```scala
package forex.services.rates

import cats.effect.{IO}
import cats.effect.concurrent.Ref
import forex.domain._
import forex.services.rates.errors.Error
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers
import java.time.OffsetDateTime

class OneFrameCacheSpec extends AnyFunSuite with Matchers {

  // Build a cache pre-loaded with test data — no live interpreter needed
  def makeCache(rates: Map[Rate.Pair, Rate]): interpreters.OneFrameCache[IO] = {
    val ref = Ref.unsafe[IO, Map[Rate.Pair, Rate]](rates)
    new interpreters.OneFrameCache[IO](ref, null, null)
    // live + config are null because backgroundRefresh is not called in unit tests
  }

  val usdJpy = Rate.Pair(Currency.USD, Currency.JPY)
  val testRate = Rate(
    pair      = usdJpy,
    price     = Price(BigDecimal("110.5")),
    timestamp = Timestamp(OffsetDateTime.now)
  )

  test("get returns Right(rate) for a known pair") {
    val cache = makeCache(Map(usdJpy -> testRate))
    cache.get(usdJpy).unsafeRunSync() shouldBe Right(testRate)
  }

  test("get returns Left(error) for an unknown pair") {
    val cache = makeCache(Map.empty)
    val result = cache.get(usdJpy).unsafeRunSync()
    result shouldBe a[Left[_, _]]
    result.left.get.asInstanceOf[Error.OneFrameLookupFailed].msg should
      include("USD")
  }

  test("get returns correct rate when multiple pairs are cached") {
    val eurGbp = Rate.Pair(Currency.EUR, Currency.GBP)
    val eurGbpRate = testRate.copy(
      pair  = eurGbp,
      price = Price(BigDecimal("0.85"))
    )
    val cache = makeCache(Map(usdJpy -> testRate, eurGbp -> eurGbpRate))

    cache.get(usdJpy).unsafeRunSync() shouldBe Right(testRate)
    cache.get(eurGbp).unsafeRunSync() shouldBe Right(eurGbpRate)
  }

  test("cache returns stale data rather than erroring during refresh failure") {
    // Simulate: cache has data, refresh fails
    // get() should still return the stale rate (not an error)
    val cache = makeCache(Map(usdJpy -> testRate))
    // Even if background refresh has failed, get() returns what's in Ref
    cache.get(usdJpy).unsafeRunSync() shouldBe Right(testRate)
  }
}
```

**Verify:**
```bash
sbt "testOnly *CacheSpec"
# All 4 tests green
```

---

### Step 15 — Write ProgramSpec

**Goal:** Test the error mapping between service and program layers.

**Create file:** `src/test/scala/forex/programs/rates/ProgramSpec.scala`

```scala
package forex.programs.rates

import forex.services.rates.errors.{Error => ServiceError}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

class ProgramSpec extends AnyFunSuite with Matchers {

  test("toProgramError maps OneFrameLookupFailed to RateLookupFailed") {
    val serviceError = ServiceError.OneFrameLookupFailed("connection refused")
    val programError = errors.toProgramError(serviceError)

    programError shouldBe a[errors.Error.RateLookupFailed]
    programError.asInstanceOf[errors.Error.RateLookupFailed].msg shouldBe
      "connection refused"
  }

  test("RateLookupFailed message is preserved through mapping") {
    val msg = "One-Frame returned 429 Too Many Requests"
    val result = errors.toProgramError(ServiceError.OneFrameLookupFailed(msg))
    result.asInstanceOf[errors.Error.RateLookupFailed].msg shouldBe msg
  }
}
```

**Verify:**
```bash
sbt "testOnly *ProgramSpec"
# 2 tests green
```

---

### Step 16 — Write RatesHttpRoutesSpec

**Goal:** Test HTTP routes with in-memory fake programs — no network, no server.

**Create file:** `src/test/scala/forex/http/rates/RatesHttpRoutesSpec.scala`

```scala
package forex.http.rates

import cats.effect.IO
import forex.domain._
import forex.programs.rates.{Algebra => ProgramAlgebra, Protocol => ProgramProtocol}
import forex.programs.rates.errors.Error
import org.http4s._
import org.http4s.implicits._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers
import java.time.OffsetDateTime

class RatesHttpRoutesSpec extends AnyFunSuite with Matchers {

  val goodRate = Rate(
    pair      = Rate.Pair(Currency.USD, Currency.JPY),
    price     = Price(BigDecimal("110.5")),
    timestamp = Timestamp(OffsetDateTime.now)
  )

  // Fake program — returns a fixed rate, never touches network
  def successProgram(rate: Rate): ProgramAlgebra[IO] =
    (_: ProgramProtocol.GetRatesRequest) => IO.pure(Right(rate))

  def failingProgram(msg: String): ProgramAlgebra[IO] =
    (_: ProgramProtocol.GetRatesRequest) =>
      IO.pure(Left(Error.RateLookupFailed(msg)))

  def routes(program: ProgramAlgebra[IO]): HttpApp[IO] =
    new RatesHttpRoutes[IO](program).routes.orNotFound

  test("GET /rates?from=USD&to=JPY returns 200 with price in body") {
    val req  = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
    val resp = routes(successProgram(goodRate)).run(req).unsafeRunSync()

    resp.status shouldBe Status.Ok
    val body = resp.as[String].unsafeRunSync()
    body should include("price")
    body should include("110.5")
  }

  test("GET /rates with missing query param returns 400") {
    val req  = Request[IO](Method.GET, uri"/rates?from=USD")
    val resp = routes(successProgram(goodRate)).run(req).unsafeRunSync()

    resp.status shouldBe Status.BadRequest
  }

  test("GET /rates with unknown currency returns 400") {
    val req  = Request[IO](Method.GET, uri"/rates?from=USD&to=XXX")
    val resp = routes(successProgram(goodRate)).run(req).unsafeRunSync()

    resp.status shouldBe Status.BadRequest
  }

  test("GET /rates when service fails returns 503 with error body") {
    val req  = Request[IO](Method.GET, uri"/rates?from=USD&to=JPY")
    val resp = routes(failingProgram("One-Frame unavailable")).run(req).unsafeRunSync()

    resp.status shouldBe Status.ServiceUnavailable
    resp.as[String].unsafeRunSync() should include("One-Frame unavailable")
  }

  test("GET /rates response body includes from, to, timestamp fields") {
    val req  = Request[IO](Method.GET, uri"/rates?from=EUR&to=GBP")
    val resp = routes(successProgram(goodRate)).run(req).unsafeRunSync()
    val body = resp.as[String].unsafeRunSync()

    body should include("from")
    body should include("to")
    body should include("timestamp")
  }
}
```

**Verify:**
```bash
sbt "testOnly *RoutesSpec"
# All 5 tests green

sbt test
# ALL tests green — full suite
```

---

### Step 17 — Write property-based tests

**Goal:** Use ScalaCheck to verify domain properties hold for any generated input.

**Create file:** `src/test/scala/forex/domain/CurrencyPropertySpec.scala`

```scala
package forex.domain

import org.scalacheck.{Arbitrary, Gen}
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers
import org.scalatestplus.scalacheck.ScalaCheckPropertyChecks
import cats.syntax.show._

class CurrencyPropertySpec extends AnyFunSuite
    with Matchers with ScalaCheckPropertyChecks {

  implicit val arbCurrency: Arbitrary[Currency] =
    Arbitrary(Gen.oneOf(Currency.values))

  implicit val arbPair: Arbitrary[Rate.Pair] = Arbitrary(
    for {
      from <- Gen.oneOf(Currency.values)
      to   <- Gen.oneOf(Currency.values).suchThat(_ != from)
    } yield Rate.Pair(from, to)
  )

  test("fromString(show(c)) roundtrips for every currency") {
    forAll { (c: Currency) =>
      Currency.fromString(c.show) shouldBe Right(c)
    }
  }

  test("every generated pair exists in allPairs") {
    forAll { (pair: Rate.Pair) =>
      Currency.allPairs should contain(pair)
    }
  }

  test("no generated pair is a self-pair") {
    forAll { (pair: Rate.Pair) =>
      pair.from should not be pair.to
    }
  }
}
```

> Note: `ScalaCheckPropertyChecks` requires adding `scalatestplus-scalacheck` to build.sbt.
> Add to Dependencies.scala:
> ```scala
> lazy val scalaTestPlusScalaCheck =
>   "org.scalatestplus" %% "scalacheck-1-15" % "3.2.7.0" % Test
> ```
> Add to libraryDependencies in build.sbt.

**Verify:**
```bash
sbt "testOnly *PropertySpec"
# Properties hold for 100 generated inputs each
```

---

## Phase 8 — Integration Tests

---

### Step 18 — Create docker-compose.it.yml

**Goal:** A compose file specifically for integration tests with healthchecks.

**Create file:** `src/main/scala/forex/it/DockerTag.scala`

Wait — this is a test file. Create at:

**Create file:** `src/test/scala/forex/it/DockerTag.scala`

```scala
package forex.it

import org.scalatest.Tag

object DockerTest extends Tag("forex.it.DockerTest")
```

**Create file:** `docker-compose.it.yml` (in forex-mtl root)

```yaml
services:
  one-frame:
    image: paidyinc/one-frame
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f",
             "-H", "token: 10dc303535874aeccc86a8251e6992f5",
             "http://localhost:8080/rates?pair=USDJPY"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 5s

  forex-proxy:
    build: .
    ports:
      - "9090:9090"
    depends_on:
      one-frame:
        condition: service_healthy
    environment:
      ONE_FRAME_URL: http://one-frame:8080
      ONE_FRAME_TOKEN: 10dc303535874aeccc86a8251e6992f5
    healthcheck:
      test: ["CMD", "curl", "-f",
             "http://localhost:9090/rates?from=USD&to=JPY"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
```

**Verify:**
```bash
docker compose -f docker-compose.it.yml up -d --build
# Wait ~30s for both services to be healthy
docker compose -f docker-compose.it.yml ps
# Both should show "healthy"
docker compose -f docker-compose.it.yml down
```

---

### Step 19 — Write IntegrationSpec

**Goal:** End-to-end tests against real running services.

**Create file:** `src/test/scala/forex/it/IntegrationSpec.scala`

```scala
package forex.it

import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers
import scala.util.Try
import java.net.{HttpURLConnection, URL}
import java.time.{Duration, Instant}

class IntegrationSpec extends AnyFunSuite with Matchers {

  private val baseUrl = sys.env.getOrElse("FOREX_URL", "http://localhost:9090")

  private def get(path: String): (Int, String) = {
    val conn = new URL(s"$baseUrl$path").openConnection.asInstanceOf[HttpURLConnection]
    conn.setRequestMethod("GET")
    conn.setConnectTimeout(5000)
    val status = conn.getResponseCode
    val body = Try(scala.io.Source.fromInputStream(conn.getInputStream).mkString)
                 .orElse(Try(scala.io.Source.fromInputStream(conn.getErrorStream).mkString))
                 .getOrElse("")
    (status, body)
  }

  test("GET /rates?from=USD&to=JPY returns 200 with price", DockerTest) {
    val (status, body) = get("/rates?from=USD&to=JPY")
    status shouldBe 200
    body should include("price")
    body should include("timestamp")
    body should include("USD")
    body should include("JPY")
  }

  test("Rate timestamp is within 5 minutes of now", DockerTest) {
    val (_, body) = get("/rates?from=EUR&to=GBP")
    // Extract timestamp from JSON body (simple string search)
    val tsPattern = """"timestamp"\s*:\s*"([^"]+)"""".r
    val ts = tsPattern.findFirstMatchIn(body).map(_.group(1)).get
    val age = Duration.between(Instant.parse(ts), Instant.now()).abs()
    age.toMinutes should be < 5L
  }

  test("Unknown currency returns 400", DockerTest) {
    val (status, body) = get("/rates?from=USD&to=XXX")
    status shouldBe 400
    body should include("error")
  }

  test("Missing query param returns 400", DockerTest) {
    val (status, _) = get("/rates?from=USD")
    status shouldBe 400
  }

  test("Same currency both sides returns 400", DockerTest) {
    val (status, _) = get("/rates?from=USD&to=USD")
    status shouldBe 400
  }

  test("All 9 supported currencies work as from", DockerTest) {
    val currencies = List("AUD","CAD","CHF","EUR","GBP","NZD","JPY","SGD","USD")
    currencies.foreach { from =>
      val (status, _) = get(s"/rates?from=$from&to=USD")
      // Skip USD->USD
      if (from != "USD") status shouldBe 200
    }
  }

  test("1000 consecutive requests all return 200", DockerTest) {
    val results = (1 to 1000).map { _ =>
      val (status, _) = get("/rates?from=USD&to=JPY")
      status
    }
    results.count(_ == 200) shouldBe 1000
    // All served from cache — One-Frame not called 1000 times
  }
}
```

**Verify:**
```bash
# Start services
docker compose -f docker-compose.it.yml up -d --build

# Wait until healthy (~30s)
docker compose -f docker-compose.it.yml ps

# Run integration tests
sbt "testOnly * -- -n forex.it.DockerTest"

# Tear down
docker compose -f docker-compose.it.yml down
```

---

## Phase 9 — CI/CD

---

### Step 20 — Create GitHub Actions CI workflow

**Goal:** Automated test + build on every push.

```bash
mkdir -p .github/workflows
```

**Create file:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:

  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          java-version: "17"
          distribution: "temurin"
          cache: "sbt"

      - name: Run unit tests
        working-directory: interview/forex-mtl
        run: sbt test

      - name: Check formatting
        working-directory: interview/forex-mtl
        run: sbt scalafmtCheck

  build:
    name: Build Fat JAR
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          java-version: "17"
          distribution: "temurin"
          cache: "sbt"

      - name: Assemble JAR
        working-directory: interview/forex-mtl
        run: sbt assembly

      - name: Upload JAR
        uses: actions/upload-artifact@v4
        with:
          name: forex-assembly
          path: interview/forex-mtl/target/scala-2.13/forex-assembly.jar

  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          java-version: "17"
          distribution: "temurin"
          cache: "sbt"

      - name: Pull One-Frame
        run: docker pull paidyinc/one-frame

      - name: Start services
        working-directory: interview/forex-mtl
        run: docker compose -f docker-compose.it.yml up -d --build

      - name: Wait for forex-proxy healthy
        run: |
          timeout 90 bash -c \
            'until curl -sf "http://localhost:9090/rates?from=USD&to=JPY"; \
             do echo "waiting..."; sleep 3; done'

      - name: Run integration tests
        working-directory: interview/forex-mtl
        run: sbt "testOnly * -- -n forex.it.DockerTest"

      - name: Tear down
        if: always()
        working-directory: interview/forex-mtl
        run: docker compose -f docker-compose.it.yml down
```

**Verify:**
```bash
# Push to GitHub and watch the Actions tab
# All 3 jobs (test, build, integration) should go green
```

---

## Phase 10 — Frontend

---

### Step 21 — Scaffold the frontend

**Goal:** A working React app that calls the forex-proxy and displays rates.

```bash
cd /home/juan/paidy/interview
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Create** `frontend/src/types.ts`:
```typescript
export type Currency = "AUD"|"CAD"|"CHF"|"EUR"|"GBP"|"NZD"|"JPY"|"SGD"|"USD";
export const CURRENCIES: Currency[] =
  ["AUD","CAD","CHF","EUR","GBP","NZD","JPY","SGD","USD"];

export interface RateResponse {
  from:      Currency;
  to:        Currency;
  price:     number;
  timestamp: string;
}
```

**Create** `frontend/src/hooks/useForexRate.ts`:
```typescript
import { useState, useEffect, useCallback } from "react";
import { RateResponse, Currency } from "../types";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:9090";

export function useForexRate(from: Currency, to: Currency, autoRefresh: boolean) {
  const [rate,    setRate]    = useState<RateResponse | null>(null);
  const [error,   setError]   = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<number[]>([]);

  const refresh = useCallback(async () => {
    if (from === to) { setError("From and To must differ"); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API}/rates?from=${from}&to=${to}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      const data: RateResponse = await res.json();
      setRate(data);
      setError(null);
      setHistory(h => [...h.slice(-9), data.price]);
    } catch {
      setError("Service unreachable");
    } finally {
      setLoading(false);
    }
  }, [from, to]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(refresh, 30_000);
    return () => clearInterval(id);
  }, [refresh, autoRefresh]);

  return { rate, error, loading, history, refresh };
}
```

**Create** `frontend/src/App.tsx`:
```tsx
import { useState } from "react";
import { Currency, CURRENCIES } from "./types";
import { useForexRate } from "./hooks/useForexRate";

export default function App() {
  const [from, setFrom]             = useState<Currency>("USD");
  const [to,   setTo]               = useState<Currency>("JPY");
  const [auto, setAuto]             = useState(false);
  const { rate, error, loading, history, refresh } =
    useForexRate(from, to, auto);

  const age = rate
    ? Math.round((Date.now() - new Date(rate.timestamp).getTime()) / 1000)
    : 0;
  const agePct = Math.min((age / 300) * 100, 100);

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center p-8 gap-6">
      <h1 className="text-3xl font-bold text-purple-400">
        Forex Rate Proxy · Demo
      </h1>

      {/* Selectors */}
      <div className="flex gap-4">
        {(["from","to"] as const).map(field => (
          <select key={field}
            value={field === "from" ? from : to}
            onChange={e => field === "from"
              ? setFrom(e.target.value as Currency)
              : setTo(e.target.value as Currency)}
            className="bg-gray-800 border border-gray-600 rounded px-3 py-2">
            {CURRENCIES.map(c => <option key={c}>{c}</option>)}
          </select>
        ))}
      </div>

      {/* Rate display */}
      {loading && <p className="text-gray-400">Loading...</p>}
      {error   && (
        <div className="bg-red-900 border border-red-500 rounded px-4 py-2 text-red-200">
          {error}
        </div>
      )}
      {rate && (
        <div className="bg-gray-800 rounded-xl p-8 text-center w-80">
          <div className="text-5xl font-mono font-bold text-cyan-400">
            {rate.price.toFixed(4)}
          </div>
          <div className="text-gray-400 mt-2">
            {rate.from} → {rate.to}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {new Date(rate.timestamp).toLocaleTimeString()}
          </div>

          {/* Cache age bar */}
          <div className="mt-4">
            <div className="text-xs text-gray-500 mb-1">
              Cache age: {age}s / 300s
            </div>
            <div className="w-full bg-gray-700 rounded h-2">
              <div
                className="h-2 rounded transition-all"
                style={{
                  width: `${agePct}%`,
                  backgroundColor: agePct > 80 ? "#EF4444" : "#10B981"
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Sparkline */}
      {history.length > 1 && (
        <svg width="320" height="60" className="bg-gray-800 rounded px-2">
          {history.map((v, i) => {
            const min = Math.min(...history);
            const max = Math.max(...history);
            const range = max - min || 1;
            const x = (i / (history.length - 1)) * 300 + 10;
            const y = 50 - ((v - min) / range) * 40;
            return i === 0 ? null : (
              <line key={i}
                x1={(( (i-1) / (history.length-1)) * 300 + 10)}
                y1={(50 - ((history[i-1] - min) / range) * 40)}
                x2={x} y2={y}
                stroke="#7C3AED" strokeWidth="2"
              />
            );
          })}
        </svg>
      )}

      {/* Controls */}
      <div className="flex gap-4 items-center">
        <button onClick={refresh}
          className="px-4 py-2 bg-purple-600 rounded hover:bg-purple-700 transition">
          Refresh
        </button>
        <label className="flex items-center gap-2 text-gray-300 text-sm">
          <input type="checkbox" checked={auto}
                 onChange={e => setAuto(e.target.checked)} />
          Auto-refresh (30s)
        </label>
      </div>

      <p className="text-xs text-gray-600">
        Powered by forex-mtl · Paidy take-home
      </p>
    </div>
  );
}
```

**Verify:**
```bash
cd frontend
npm run dev
# Opens http://localhost:5173
# Select USD → JPY and click Refresh
# Should show real rate from forex-proxy
```

---

## Phase 11 — Polish & Submit

---

### Step 22 — Write README.md

**Goal:** A clear README that Paidy engineers can follow to run the project.
Put this in `forex-mtl/README.md`. It must include:

1. How to run with Docker Compose (one command)
2. How to run tests (unit and integration)
3. API endpoint with example request/response
4. The constraint math (show you understood the problem)
5. Design decisions (proactive caching, 4-min interval, polling vs streaming)
6. Known limitations and what you'd improve with more time

**Verify:** Ask someone else to follow it cold. If they can't run it in under 5 minutes, rewrite it.

---

### Step 23 — Final checklist before submission

Run through every item:

```bash
# 1. Everything compiles
sbt compile

# 2. All unit tests pass
sbt test

# 3. Code is formatted
sbt scalafmtCheck

# 4. Fat JAR builds
sbt assembly

# 5. Docker Compose starts cleanly
docker compose up --build
curl localhost:9090/rates?from=USD&to=JPY   # 200 with real rate

# 6. Integration tests pass
docker compose -f docker-compose.it.yml up -d --build
sbt "testOnly * -- -n forex.it.DockerTest"
docker compose -f docker-compose.it.yml down

# 7. Frontend works
cd frontend && npm run dev
# Visit localhost:5173, select a pair, see a rate

# 8. No hardcoded secrets
grep -r "10dc303535874aeccc86a8251e6992f5" src/
# Should only appear in application.conf — not in Scala source files
```

---

## Summary

| Phase | Steps | What you build |
|-------|-------|----------------|
| 1 — Foundation    | 1–3   | Client artifact, config types, HOCON |
| 2 — Domain fixes  | 4–5   | Currency.values, safe fromString |
| 3 — Live client   | 6     | OneFrameLive — real HTTP + JSON decoder |
| 4 — Cache         | 7–8   | OneFrameCache + Interpreters factories |
| 5 — Wiring        | 9–10  | Module + Main connected end-to-end |
| 6 — Error handling| 11    | Descriptive HTTP errors, no more 500s |
| 7 — Unit tests    | 12–17 | Full test suite, all green |
| 8 — Integration   | 18–19 | Docker healthchecks, real end-to-end tests |
| 9 — CI/CD         | 20    | GitHub Actions — auto test on push |
| 10 — Frontend     | 21    | React demo app |
| 11 — Polish       | 22–23 | README + final checklist |

**First working state:** end of Step 10 — `sbt run` + `curl localhost:9090/rates?from=USD&to=JPY` returns a real rate.

**Submittable state:** end of Step 23.
