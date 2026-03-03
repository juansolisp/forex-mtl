# Dependencies & Plugins — Complete Beginner Guide

> Every library and plugin used in forex-mtl, explained from scratch
> with a practical example for each one.

---

## How to read this guide

Each entry follows this structure:

- **What it is** — one sentence
- **The problem it solves** — what you'd have to do without it
- **Core concept** — the key idea in plain language
- **Practical example** — minimal runnable code showing the thing working
- **Where it's used in forex-mtl** — the exact file and line

---

## Table of Contents

### Dependencies
1. [cats-core](#1-cats-core)
2. [cats-effect](#2-cats-effect)
3. [fs2](#3-fs2)
4. [http4s-dsl](#4-http4s-dsl)
5. [http4s-blaze-server](#5-http4s-blaze-server)
6. [http4s-blaze-client](#6-http4s-blaze-client)
7. [http4s-circe](#7-http4s-circe)
8. [circe-core](#8-circe-core)
9. [circe-generic](#9-circe-generic)
10. [circe-generic-extras](#10-circe-generic-extras)
11. [circe-parser](#11-circe-parser)
12. [pureconfig](#12-pureconfig)
13. [logback-classic](#13-logback-classic)

### Test Dependencies
14. [scalatest](#14-scalatest)
15. [scalacheck](#15-scalacheck)
16. [cats-scalacheck](#16-cats-scalacheck)

### Compiler Plugins
17. [kind-projector](#17-kind-projector)

### SBT Plugins
18. [sbt-scalafmt-coursier](#18-sbt-scalafmt-coursier)
19. [sbt-updates](#19-sbt-updates)
20. [sbt-revolver](#20-sbt-revolver)
21. [sbt-assembly](#21-sbt-assembly)

---

---

# Dependencies

---

## 1. cats-core

**Version:** 2.6.1 | **Org:** `org.typelevel`

### What it is
A library of functional programming abstractions — type classes like `Functor`,
`Applicative`, `Monad`, and utilities like `Show`, `Eq`, `Order`.

### The problem it solves
Without it you'd write the same patterns (map, flatMap, traverse) differently for
every type. Cats gives you a shared vocabulary that works the same way across
`Option`, `Either`, `List`, `IO`, and your own types.

### Core concept

A **type class** is a behaviour you attach to a type from outside.
You don't have to own the type to give it new abilities.

```
Functor   → has .map
Applicative → has .pure and can combine independent values
Monad     → has .flatMap (sequential chaining)
Show      → has .show  (safe .toString replacement)
```

### Practical example

```scala
import cats.Show
import cats.syntax.show._

// Give Currency a Show instance
case class Currency(code: String)

implicit val showCurrency: Show[Currency] =
  Show.show(c => c.code)

val usd = Currency("USD")
println(usd.show)   // "USD"
// vs usd.toString  // "Currency(USD)" — ugly, not controlled

// Functor — map over Option without pattern matching
import cats.Functor
import cats.instances.option._

val price: Option[Double] = Some(100.5)
val doubled = Functor[Option].map(price)(_ * 2)
// Some(201.0)

// Applicative — combine two Options independently
import cats.syntax.apply._

val from: Option[String] = Some("USD")
val to:   Option[String] = Some("JPY")
val pair = (from, to).mapN((f, t) => s"$f->$t")
// Some("USD->JPY")
```

### Where it's used in forex-mtl
- `Currency.scala` — `Show[Currency]` instance
- `OneFrameDummy.scala` — `Applicative` constraint (`.pure[F]`)
- `Program.scala` — `Functor` constraint (`.leftMap` via EitherT)
- Throughout — `cats.syntax.either._` for `.asRight`, `.asLeft`

---

## 2. cats-effect

**Version:** 2.5.1 | **Org:** `org.typelevel`

### What it is
The runtime for functional effects in Scala. Provides `IO` (a description of a
side-effecting computation), plus type classes `Sync`, `Async`, `Concurrent`,
`Timer`, `Resource`, and `Ref`.

### The problem it solves
Normal Scala code runs side effects immediately and unpredictably. `cats-effect`
lets you *describe* effects as values, compose them safely, and run them at the
very edge of your program.

### Core concept

```
IO[A]  means: "a program that will eventually produce an A (or fail)"
         — it does nothing until you call .unsafeRunSync()
         — it is a value you can pass around, combine, retry, timeout
```

Key types:

| Type | What it does |
|------|-------------|
| `IO[A]` | Describes a computation returning `A` |
| `Ref[F, A]` | Thread-safe mutable variable inside `F` |
| `Resource[F, A]` | Manages acquisition + guaranteed release of `A` |
| `Sync[F]` | `F` can run synchronous side effects |
| `Concurrent[F]` | `F` can run fibers (lightweight threads) |
| `Timer[F]` | `F` can sleep / get current time |

### Practical example

```scala
import cats.effect.{IO, IOApp, Ref, Resource}
import cats.effect.ExitCode

// IO — describe work, don't run it yet
val readLine: IO[String] = IO(scala.io.StdIn.readLine())
val printHello: IO[Unit] = IO(println("Hello!"))

// Compose with flatMap
val program: IO[Unit] =
  printHello.flatMap(_ => readLine).flatMap(name =>
    IO(println(s"You said: $name"))
  )

// Nothing runs until here:
object Main extends IOApp {
  def run(args: List[String]): IO[ExitCode] =
    program.as(ExitCode.Success)
}

// Ref — thread-safe counter
val counter: IO[Unit] =
  for {
    ref <- Ref.of[IO, Int](0)
    _   <- ref.update(_ + 1)
    _   <- ref.update(_ + 1)
    n   <- ref.get
    _   <- IO(println(s"Count: $n"))   // Count: 2
  } yield ()

// Resource — open file, guarantee close even on error
val fileResource: Resource[IO, java.io.PrintWriter] =
  Resource.make(
    IO(new java.io.PrintWriter("out.txt"))  // acquire
  )(pw => IO(pw.close()))                   // release (always runs)

fileResource.use { pw =>
  IO(pw.println("written safely"))
}
```

### Where it's used in forex-mtl
- `Main.scala` — `IOApp`, `ConcurrentEffect`, `Timer`
- `Module.scala` — `Concurrent`, `Timer` constraints
- `Config.scala` — `Sync[F].delay` to wrap pureconfig loading
- Cache layer (to build) — `Ref[F, Map[Pair, Rate]]` for in-memory state

---

## 3. fs2

**Version:** 2.5.4 | **Org:** `co.fs2`

### What it is
Functional Streams for Scala. A library for processing sequences of data
incrementally, safely, and with resource management built in.

### The problem it solves
Processing large sequences one element at a time without loading everything
into memory. Also: repeating tasks on a schedule, building pipelines of
transformation steps that are easy to compose.

### Core concept

```
Stream[F, A]  — a potentially infinite sequence of A values
               produced inside effect F
```

Think of it as a lazy `List` that can do IO between elements and can run forever.

### Practical example

```scala
import fs2.Stream
import cats.effect.{IO, Timer}
import scala.concurrent.duration._

// A finite stream
val numbers: Stream[IO, Int] =
  Stream.emits(List(1, 2, 3, 4, 5))

// Transform it
val doubled: Stream[IO, Int] = numbers.map(_ * 2)

// Run it — collect all values
doubled.compile.toList.unsafeRunSync()
// List(2, 4, 6, 8, 10)

// A stream that does IO
val lines: Stream[IO, Unit] =
  Stream(1, 2, 3).evalMap(n => IO(println(s"item $n")))

lines.compile.drain.unsafeRunSync()
// item 1
// item 2
// item 3

// A stream that ticks every N seconds (used for cache refresh)
val ticker: Stream[IO, Unit] =
  Stream
    .fixedDelay[IO](4.minutes)   // emits Unit every 4 min
    .evalMap(_ => IO(println("refreshing cache...")))

// Run forever in the background
ticker.compile.drain  // this is an IO[Unit] — runs until cancelled
```

### Where it's used in forex-mtl
- `Main.scala` — the entire app is a `Stream[F, Unit]`
- `Config.scala` — `Stream.eval(...)` to load config as a stream step
- Cache layer (to build) — `Stream.fixedDelay` for background refresh

---

## 4. http4s-dsl

**Version:** 0.22.15 | **Org:** `org.http4s`

### What it is
A Scala DSL (domain-specific language) for defining HTTP routes using
pattern matching syntax.

### The problem it solves
Without it you'd have to write verbose code to extract method, path, and
query params from a raw `Request` object. The DSL gives you readable,
type-safe route definitions.

### Core concept

You pattern match on the incoming `Request` like this:

```scala
case GET -> Root / "users" / id :? PageParam(page) =>
//   ^      ^              ^         ^
//   method path segments  path var  query param
```

### Practical example

```scala
import cats.effect.{IO, Sync}
import org.http4s._
import org.http4s.dsl.Http4sDsl
import org.http4s.implicits._

class MyRoutes[F[_]: Sync] extends Http4sDsl[F] {

  // Query param decoder
  object NameParam extends QueryParamDecoderMatcher[String]("name")

  val routes: HttpRoutes[F] = HttpRoutes.of[F] {

    // GET /hello
    case GET -> Root / "hello" =>
      Ok("Hello, world!")

    // GET /hello/Juan
    case GET -> Root / "hello" / name =>
      Ok(s"Hello, $name!")

    // GET /greet?name=Juan
    case GET -> Root / "greet" :? NameParam(name) =>
      Ok(s"Greetings, $name!")

    // POST /echo
    case req @ POST -> Root / "echo" =>
      req.as[String].flatMap(body => Ok(body))
  }
}
```

### Where it's used in forex-mtl
- `RatesHttpRoutes.scala` — the main route pattern:
  ```scala
  case GET -> Root :? FromQueryParam(from) +& ToQueryParam(to) =>
  ```
- `QueryParams.scala` — `QueryParamDecoderMatcher` for `from` and `to`

---

## 5. http4s-blaze-server

**Version:** 0.22.15 | **Org:** `org.http4s`

### What it is
An NIO (non-blocking I/O) HTTP/1.1 server implementation for http4s.
"Blaze" is the underlying NIO engine.

### The problem it solves
Turns your `HttpApp[F]` (a function `Request => F[Response]`) into an actual
running server bound to a host and port.

### Core concept

```
HttpRoutes[F]  — partial function (only handles matched routes)
HttpApp[F]     — total function (always returns a response, even 404)
BlazeServer    — binds HttpApp to a port and listens for connections
```

### Practical example

```scala
import cats.effect.{IO, IOApp, ExitCode}
import org.http4s.implicits._
import org.http4s.blaze.server.BlazeServerBuilder
import scala.concurrent.ExecutionContext.global

object Main extends IOApp {
  def run(args: List[String]): IO[ExitCode] = {

    val app = new MyRoutes[IO].routes.orNotFound
    //                                 ^
    //                          converts HttpRoutes → HttpApp
    //                          (returns 404 for unmatched routes)

    BlazeServerBuilder[IO](global)
      .bindHttp(port = 9090, host = "0.0.0.0")
      .withHttpApp(app)
      .serve                         // Stream[IO, ExitCode]
      .compile.drain
      .as(ExitCode.Success)
  }
}
```

### Where it's used in forex-mtl
- `Main.scala` — `BlazeServerBuilder[F](ec).bindHttp(...).withHttpApp(...).serve`
- `Module.scala` — middleware applied to routes before passing to blaze

---

## 6. http4s-blaze-client

**Version:** 0.22.15 | **Org:** `org.http4s`

### What it is
The HTTP client counterpart to blaze-server. Makes outbound HTTP requests
inside an effect `F`.

### The problem it solves
You need to call One-Frame's API. This gives you a `Client[F]` — a function
`Request[F] => Resource[F, Response[F]]` — managed safely with connection
pooling and automatic cleanup.

### Core concept

```
Client[F]  — a resource that knows how to make HTTP requests
           — connection pool is managed for you
           — always use via Resource to ensure connections are released
```

### Practical example

```scala
import cats.effect.{IO, IOApp, ExitCode, Resource}
import org.http4s.client.blaze.BlazeClientBuilder
import org.http4s.implicits._
import org.http4s.{Request, Method, Header}
import scala.concurrent.ExecutionContext.global

object ClientExample extends IOApp {
  def run(args: List[String]): IO[ExitCode] = {

    // BlazeClientBuilder returns a Resource — cleans up connection pool on release
    val clientResource: Resource[IO, org.http4s.client.Client[IO]] =
      BlazeClientBuilder[IO](global).resource

    clientResource.use { client =>

      val request = Request[IO](
        method = Method.GET,
        uri    = uri"http://localhost:8080/rates?pair=USDJPY"
      ).withHeaders(Header("token", "10dc303535874aeccc86a8251e6992f5"))

      // .expect decodes the response body as the given type
      client.expect[String](request).flatMap { body =>
        IO(println(body))
      }
    }.as(ExitCode.Success)
  }
}
```

### Where it's used in forex-mtl
- **Not yet added** — needed for `OneFrameLive` to call One-Frame's `/rates`
- `Main.scala` will wrap it in a `Resource` and pass to `OneFrameLive`

---

## 7. http4s-circe

**Version:** 0.22.15 | **Org:** `org.http4s`

### What it is
A bridge between http4s and circe. Makes it trivial to read JSON request
bodies and write JSON response bodies.

### The problem it solves
http4s works with `EntityDecoder` and `EntityEncoder` for reading/writing
bodies. Circe works with `Decoder` and `Encoder` for JSON. This library
connects them so your circe codecs automatically work as http4s entity codecs.

### Core concept

```
circe Encoder[A]  +  http4s-circe  =  EntityEncoder[F, A]  (write JSON response)
circe Decoder[A]  +  http4s-circe  =  EntityDecoder[F, A]  (read JSON request body)
```

### Practical example

```scala
import io.circe.generic.auto._
import org.http4s.circe._
import org.http4s.dsl.Http4sDsl
import cats.effect.Sync

case class RateResponse(from: String, to: String, price: Double)

class ApiRoutes[F[_]: Sync] extends Http4sDsl[F] {

  // jsonEncoderOf bridges circe → http4s
  implicit val encoder = jsonEncoderOf[F, RateResponse]

  val routes = HttpRoutes.of[F] {
    case GET -> Root / "rate" =>
      // Ok() uses the implicit EntityEncoder to serialise to JSON automatically
      Ok(RateResponse("USD", "JPY", 110.5))
      // response body: {"from":"USD","to":"JPY","price":110.5}
  }
}
```

### Where it's used in forex-mtl
- `http/package.scala` — the implicit `jsonEncoder` and `jsonDecoder` that make
  `Ok(rate.asGetApiResponse)` automatically serialize to JSON

---

## 8. circe-core

**Version:** 0.14.2 | **Org:** `io.circe`

### What it is
The core of the circe JSON library. Defines `Json`, `Encoder[A]`, `Decoder[A]`,
`HCursor`, and the fundamental operations for working with JSON in Scala.

### The problem it solves
Standard `java.json` or raw string manipulation is unsafe and verbose. Circe
gives you type-safe, compile-time-checked JSON encoding and decoding.

### Core concept

```
Encoder[A]  — knows how to turn an A into Json
Decoder[A]  — knows how to turn Json into Either[DecodingFailure, A]
```

### Practical example

```scala
import io.circe._
import io.circe.syntax._   // adds .asJson

// Manual encoder
case class Price(value: BigDecimal)

implicit val priceEncoder: Encoder[Price] =
  Encoder.instance(p => Json.fromBigDecimal(p.value))

implicit val priceDecoder: Decoder[Price] =
  Decoder.instance(cursor =>
    cursor.as[BigDecimal].map(Price(_))
  )

val price = Price(BigDecimal("110.5"))

// Encode to Json
val json: Json = price.asJson
println(json)    // 110.5

// Decode from Json
val decoded: Either[DecodingFailure, Price] =
  json.as[Price]
// Right(Price(110.5))
```

### Where it's used in forex-mtl
- `http/rates/Protocol.scala` — `Encoder[Currency]`, `Encoder[Rate]`,
  `Encoder[GetApiResponse]`
- `http/package.scala` — `Encoder[A]` / `Decoder[A]` implicit summoning

---

## 9. circe-generic

**Version:** 0.14.2 | **Org:** `io.circe`

### What it is
Automatic derivation of `Encoder` and `Decoder` for case classes and sealed
traits using Scala macros. You don't write the codec — the compiler generates it.

### The problem it solves
Writing `Encoder` / `Decoder` by hand for every case class is tedious and
error-prone. circe-generic does it automatically based on the shape of your type.

### Core concept

```scala
import io.circe.generic.auto._
// That single import makes every case class in scope automatically
// have an Encoder and Decoder — no boilerplate needed
```

### Practical example

```scala
import io.circe.generic.auto._
import io.circe.parser._
import io.circe.syntax._

case class User(name: String, age: Int)
case class Response(user: User, status: String)

val r = Response(User("Juan", 30), "ok")

// Encode — compiler generated
val json = r.asJson.noSpaces
// {"user":{"name":"Juan","age":30},"status":"ok"}

// Decode — compiler generated
val decoded = decode[Response](json)
// Right(Response(User("Juan",30),"ok"))
```

### Where it's used in forex-mtl
- `http/rates/Protocol.scala` — `deriveConfiguredEncoder` (from generic-extras,
  which builds on generic)
- Used implicitly throughout circe-generic-extras

---

## 10. circe-generic-extras

**Version:** 0.14.2 | **Org:** `io.circe`

### What it is
An extension of circe-generic with extra derivation options — most importantly
the ability to configure naming conventions like `snake_case`, and support for
value classes (`AnyVal`) and sealed trait enumerations.

### The problem it solves
By default circe uses `camelCase` field names matching your Scala code. JSON
APIs commonly use `snake_case`. circe-generic-extras lets you configure this
once and have it apply everywhere.

### Core concept

```scala
implicit val config: Configuration =
  Configuration.default.withSnakeCaseMemberNames

// Now a field named `timeStamp` in Scala encodes as `time_stamp` in JSON
```

Also provides:
- `UnwrappedEncoder` / `UnwrappedDecoder` — encodes `case class Price(value: BigDecimal) extends AnyVal`
  as just `110.5` instead of `{"value": 110.5}`
- `EnumerationEncoder` / `EnumerationDecoder` — encodes sealed traits with no
  fields as plain strings

### Practical example

```scala
import io.circe.generic.extras.Configuration
import io.circe.generic.extras.semiauto.deriveConfiguredEncoder
import io.circe.syntax._

implicit val config: Configuration =
  Configuration.default.withSnakeCaseMemberNames

case class ApiResponse(
    fromCurrency: String,
    toCurrency: String,
    lastUpdated: String
)

implicit val encoder = deriveConfiguredEncoder[ApiResponse]

val r = ApiResponse("USD", "JPY", "2024-01-01T00:00:00Z")
println(r.asJson.spaces2)
// {
//   "from_currency" : "USD",   ← snake_case automatically
//   "to_currency"   : "JPY",
//   "last_updated"  : "2024-01-01T00:00:00Z"
// }
```

### Where it's used in forex-mtl
- `http/rates/Protocol.scala` — `Configuration.default.withSnakeCaseMemberNames`
  + `deriveConfiguredEncoder` for `GetApiResponse`, `Pair`, `Rate`
- `http/package.scala` — `UnwrappedEncoder` / `UnwrappedDecoder` so that
  `Price(110.5)` serializes as `110.5` not `{"value": 110.5}`

---

## 11. circe-parser

**Version:** 0.14.2 | **Org:** `io.circe`

### What it is
Parses raw JSON strings into circe's `Json` type.

### The problem it solves
You receive a JSON string (e.g. from an HTTP response body) and need to decode
it into a Scala type. circe-parser gives you the `parse` and `decode` functions.

### Core concept

```
parse(string)       → Either[ParsingFailure, Json]   (just parse, no type yet)
decode[A](string)   → Either[Error, A]               (parse + decode in one step)
```

### Practical example

```scala
import io.circe.parser._
import io.circe.generic.auto._

case class Rate(from: String, to: String, price: Double)

val raw = """{"from":"USD","to":"JPY","price":110.5}"""

// Two-step
val json    = parse(raw)         // Right(Json object)
val decoded = json.flatMap(_.as[Rate])

// One-step (most common)
val result: Either[io.circe.Error, Rate] = decode[Rate](raw)
// Right(Rate("USD","JPY",110.5))

// Array
val arrayRaw = """[{"from":"USD","to":"JPY","price":110.5}]"""
val rates: Either[io.circe.Error, List[Rate]] = decode[List[Rate]](arrayRaw)
```

### Where it's used in forex-mtl
- `OneFrameLive` (to build) — parsing the JSON array response from One-Frame's
  `/rates` endpoint

---

## 12. pureconfig

**Version:** 0.17.4 | **Org:** `com.github.pureconfig`

### What it is
Loads HOCON configuration files (`application.conf`) directly into Scala case
classes — no manual parsing, no string lookups.

### The problem it solves
Reading config with plain `ConfigFactory` gives you stringly-typed access:
`config.getString("app.http.host")`. PureConfig gives you type-safe, auto-derived
loading: if a field is missing or the wrong type, it fails at startup with a
clear error.

### Core concept

```scala
import pureconfig._
import pureconfig.generic.auto._

case class HttpConfig(host: String, port: Int)
case class AppConfig(http: HttpConfig)

// Loads src/main/resources/application.conf automatically
val config = ConfigSource.default.loadOrThrow[AppConfig]
config.http.port   // Int — type safe, not a string
```

The magic is `pureconfig.generic.auto._` — it uses the same shapeless macro
technique as circe-generic to derive a `ConfigReader` for any case class.

### Practical example

```conf
# application.conf
app {
  http {
    host = "0.0.0.0"
    port = 9090
    timeout = 40 seconds    # FiniteDuration — pureconfig handles this
  }
  one-frame {
    base-url = "http://localhost:8080"
    token    = "abc123"
  }
}
```

```scala
import pureconfig._
import pureconfig.generic.auto._
import scala.concurrent.duration.FiniteDuration

case class HttpConfig(host: String, port: Int, timeout: FiniteDuration)
case class OneFrameConfig(baseUrl: String, token: String)
case class AppConfig(http: HttpConfig, oneFrame: OneFrameConfig)

// one-frame in HOCON → oneFrame in Scala (kebab-case → camelCase automatic)

val config = ConfigSource.default.at("app").loadOrThrow[AppConfig]
println(config.http.port)          // 9090
println(config.oneFrame.baseUrl)   // "http://localhost:8080"
```

### Where it's used in forex-mtl
- `Config.scala` — `ConfigSource.default.at("app").loadOrThrow[ApplicationConfig]`
- `ApplicationConfig.scala` — the case classes that receive the config values

---

## 13. logback-classic

**Version:** 1.2.3 | **Org:** `ch.qos.logback`

### What it is
The most widely used logging backend for the JVM. Implements the SLF4J API.

### The problem it solves
`println` for logging is unstructured and can't be turned off. Logback gives
you levelled logging (DEBUG / INFO / WARN / ERROR), configurable output formats,
and the ability to silence noisy libraries.

### Core concept

```
SLF4J        — the logging API  (what you write in code)
Logback      — the implementation  (what actually writes the output)
logback.xml  — configures where logs go and what level to show
```

### Practical example

```xml
<!-- src/main/resources/logback.xml -->
<configuration>
  <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
      <pattern>%d{HH:mm:ss} %-5level %logger{20} - %msg%n</pattern>
    </encoder>
  </appender>

  <!-- Show INFO and above for everything -->
  <root level="INFO">
    <appender-ref ref="STDOUT"/>
  </root>

  <!-- Silence the noisy http4s access log -->
  <logger name="org.http4s" level="WARN"/>
</configuration>
```

```scala
import org.slf4j.LoggerFactory

class MyService {
  private val log = LoggerFactory.getLogger(getClass)

  def refresh(): Unit = {
    log.info("Starting cache refresh")
    try {
      // ... do work
      log.info("Cache refreshed successfully")
    } catch {
      case e: Exception =>
        log.error(s"Refresh failed: ${e.getMessage}", e)
    }
  }
}
```

### Where it's used in forex-mtl
- `src/main/resources/logback.xml` — console appender, INFO root level,
  http4s logger declared (but no level set — should be WARN)

---

---

# Test Dependencies

---

## 14. scalatest

**Version:** 3.2.7 | **Org:** `org.scalatest`

### What it is
The most popular test framework for Scala. Provides test runner, assertions,
and multiple test style flavours.

### The problem it solves
You need a structured way to write, organize, and run tests. ScalaTest gives
you human-readable test names, rich assertions, and integration with sbt.

### Core concept

Choose a style that matches how you think:

| Style | Looks like |
|-------|-----------|
| `AnyFunSuite` | `test("name") { ... }` |
| `AnyFlatSpec` | `"thing" should "do X" in { ... }` |
| `AnyWordSpec` | `"thing" when "condition" should "do X" in { ... }` |

### Practical example

```scala
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

class CurrencySpec extends AnyFunSuite with Matchers {

  test("USD show is 'USD'") {
    Currency.USD.show shouldBe "USD"
  }

  test("fromString returns Right for valid currency") {
    Currency.fromString("JPY") shouldBe Right(Currency.JPY)
  }

  test("fromString returns Left for unknown currency") {
    Currency.fromString("XXX") shouldBe Left("Unsupported currency: XXX")
  }

  test("allPairs has 72 elements") {
    Currency.allPairs should have size 72
  }

  test("allPairs has no self-pairs") {
    Currency.allPairs.foreach { pair =>
      pair.from should not be pair.to
    }
  }
}
```

Run with:
```bash
sbt test
sbt "testOnly *CurrencySpec"
```

### Where it's used in forex-mtl
- **Not yet** — test files need to be created under `src/test/scala/forex/`

---

## 15. scalacheck

**Version:** 1.15.3 | **Org:** `org.scalacheck`

### What it is
A property-based testing library. Instead of writing specific test cases you
write *properties* — rules that must hold for *any* valid input — and ScalaCheck
generates hundreds of random inputs to try to break them.

### The problem it solves
Hand-picked test cases only test what you think of. Property tests find edge
cases you never imagined — empty strings, negative numbers, Unicode characters,
null-adjacent values.

### Core concept

```
Gen[A]         — a generator that produces random A values
Arbitrary[A]   — a default generator for type A
forAll(gen)(property) — run property against many generated values
```

### Practical example

```scala
import org.scalacheck.{Gen, Arbitrary, Properties}
import org.scalacheck.Prop.forAll

object CurrencyProperties extends Properties("Currency") {

  // Define a generator for Currency
  val genCurrency: Gen[Currency] =
    Gen.oneOf(Currency.values)

  // Generator for a valid pair (from != to)
  val genPair: Gen[Rate.Pair] =
    for {
      from <- genCurrency
      to   <- genCurrency.suchThat(_ != from)
    } yield Rate.Pair(from, to)

  // Property: encoding then decoding a currency gives back the original
  property("fromString(show(c)) == c") = forAll(genCurrency) { c =>
    Currency.fromString(c.show) == Right(c)
  }

  // Property: generated pairs are always in allPairs
  property("generated pair is in allPairs") = forAll(genPair) { pair =>
    Currency.allPairs.contains(pair)
  }

  // ScalaCheck runs this 100 times with random inputs by default
}
```

### Where it's used in forex-mtl
- **Not yet** — will be used to test Currency generators and Rate.Pair properties

---

## 16. cats-scalacheck

**Version:** 0.3.2 | **Org:** `io.chrisdavenport`

### What it is
Provides `Arbitrary` instances for cats types — especially useful for testing
tagless final code where you need to generate `F[A]` values for arbitrary `F`.

### The problem it solves
ScalaCheck can generate `Int`, `String`, `List[A]` out of the box. But it
doesn't know how to generate an `IO[Int]` or `Either[String, Int]`. This
library provides those instances.

### Core concept

```scala
import io.chrisdavenport.cats.scalacheck._

// Now you can write:
forAll { (x: IO[Int]) => ... }
forAll { (x: Either[String, Rate]) => ... }
```

Also provides law testing helpers — verify that your type class instances
(Functor, Monad, etc.) obey the mathematical laws.

### Practical example

```scala
import org.scalacheck.Arbitrary
import io.chrisdavenport.cats.scalacheck._
import cats.effect.IO

// Test that your cache interpreter obeys the Functor laws
// (map identity, map composition)
class CacheFunctorLawSpec extends AnyFunSuite with Checkers {

  // Arbitrary[IO[Int]] is provided by cats-scalacheck
  test("IO satisfies functor identity law") {
    check { (fa: IO[Int]) =>
      fa.map(identity).unsafeRunSync() == fa.unsafeRunSync()
    }
  }
}
```

### Where it's used in forex-mtl
- **Not yet** — will be used for type class law tests and generating arbitrary
  effect values in tests

---

---

# Compiler Plugins

---

## 17. kind-projector

**Version:** 0.13.2 | **Org:** `org.typelevel`

### What it is
A Scala compiler plugin that adds cleaner syntax for **type lambdas** — partial
application of type constructors with multiple type parameters.

### The problem it solves
Scala's built-in type lambda syntax is extremely verbose. When working with
tagless final and higher-kinded types you constantly need to partially apply
types, and without kind-projector the syntax is painful.

### Core concept

```scala
// Without kind-projector — verbose type lambda
type EitherString[A] = Either[String, A]
def foo[F[_]: Functor]: Unit = ???
foo[({ type L[A] = Either[String, A] })#L]   // ← ugly

// With kind-projector — clean syntax
foo[Either[String, *]]    // ← readable
```

### Practical example

```scala
// Without kind-projector:
def process[F[_]](fa: F[Int]): F[String] = ???

// Calling with Either[String, ?]:
process[({ type L[A] = Either[String, A] })#L](Right(42))

// With kind-projector:
process[Either[String, *]](Right(42))

// Another common use — Functor for a multi-param type:
// Without:
implicitly[Functor[({ type L[A] = Map[String, A] })#L]]
// With:
implicitly[Functor[Map[String, *]]]
```

In `build.sbt` it is added as a **compiler plugin**, not a library dependency:

```scala
compilerPlugin(Libraries.kindProjector)
// cross CrossVersion.full — means it's compiled for the exact Scala version
```

### Where it's used in forex-mtl
- Implicitly throughout — enables the `F[_]` patterns in all the tagless final
  code to compile cleanly
- `EitherT` usage in `Program.scala` relies on kind-projector for the error
  type lambda

---

---

# SBT Plugins

> SBT plugins extend the build tool itself, not your application.
> They live in `project/plugins.sbt`.

---

## 18. sbt-scalafmt-coursier

**Version:** 1.16 | **Org:** `com.lucidchart`

### What it is
Integrates the Scalafmt code formatter into sbt. Uses Coursier for downloading
the formatter, which is faster and more reliable than the alternative.

### The problem it solves
Without a formatter, every developer formats code differently. Code reviews get
cluttered with style noise. Scalafmt enforces a consistent, auto-applied style.

### Core concept

Scalafmt reads `.scalafmt.conf` for rules and reformats your `.scala` files
in place. The sbt plugin adds tasks to run it as part of your build.

### Key commands

```bash
sbt scalafmt          # format all source files
sbt scalafmtCheck     # check without modifying (used in CI to fail if unformatted)
sbt scalafmtAll       # format sources + test sources + sbt build files
```

### Practical example

`.scalafmt.conf` in the project root:
```
version = "3.7.14"
maxColumn = 100
align.preset = more
rewrite.rules = [SortImports, RedundantBraces]
```

Before:
```scala
def get(pair:Rate.Pair):F[Error Either Rate]={
ratesService.get(pair)
}
```

After `sbt scalafmt`:
```scala
def get(pair: Rate.Pair): F[Error Either Rate] = {
  ratesService.get(pair)
}
```

### Where it's used in forex-mtl
- `.scalafmt.conf` in project root defines the rules
- CI should run `sbt scalafmtCheck` to fail PRs with unformatted code

---

## 19. sbt-updates

**Version:** 0.5.3 | **Org:** `com.timushev.sbt`

### What it is
Adds a single sbt task that checks all your dependencies for newer versions
available on Maven.

### The problem it solves
Dependencies go stale. Security vulnerabilities are fixed in new releases.
Without tooling you'd have to check each library manually.

### Key command

```bash
sbt dependencyUpdates
```

### Practical example

```
$ sbt dependencyUpdates

[info] Found 3 dependency updates for forex
[info]   co.fs2:fs2-core_2.13               : 2.5.4  -> 3.9.2
[info]   org.http4s:http4s-dsl_2.13         : 0.22.15 -> 0.23.25
[info]   io.circe:circe-core_2.13           : 0.14.2  -> 0.14.6
```

It only reports — it never modifies your `build.sbt`.

### Where it's used in forex-mtl
- Available but not wired into any automated process
- Run manually before starting implementation to know if any deps have security patches

---

## 20. sbt-revolver

**Version:** 0.9.1 | **Org:** `io.spray`

### What it is
Adds `reStart` and `reStop` tasks to sbt that run your application in a
background JVM process, with automatic restart on code changes.

### The problem it solves
The normal development loop without it is:
```
edit code → Ctrl+C → sbt run → wait → test → repeat
```
With sbt-revolver:
```
sbt ~reStart   ← stays running, auto-restarts on file save
```

### Key commands

```bash
sbt reStart      # start app in background
sbt reStop       # stop it
sbt ~reStart     # watch for changes and auto-restart (the useful one)
```

### Practical example

```bash
# Terminal 1 — keep this running while you edit
$ sbt ~reStart

# Edit src/main/scala/forex/Module.scala ...
# Save the file...
# sbt auto-recompiles and restarts the server

# Terminal 2 — test your changes immediately
$ curl localhost:9090/rates?from=USD&to=JPY
```

### Where it's used in forex-mtl
- Available for local development
- Faster feedback loop than stopping/starting sbt manually

---

## 21. sbt-assembly

**Version:** 2.2.0 | **Org:** `com.eed3si9n`

### What it is
Merges your compiled code and all its dependencies into a single self-contained
**fat JAR** file.

### The problem it solves
A normal JAR only contains your code. To run it you need all dependency JARs on
the classpath. A fat JAR contains everything — you ship one file and run it with
`java -jar`. Essential for Docker deployments.

### Core concept

```
sbt assembly  →  target/scala-2.13/forex-assembly.jar
                 ↑
                 contains: your code
                          + cats JARs
                          + http4s JARs
                          + circe JARs
                          + logback JARs
                          + every transitive dependency
```

The **merge strategy** handles conflicts when multiple JARs contain the same
file path:

```scala
// build.sbt
assembly / assemblyJarName := "forex-assembly.jar"

assembly / assemblyMergeStrategy := {
  // Multiple libs all have META-INF/MANIFEST.MF — discard duplicates
  case PathList("META-INF", _*) => MergeStrategy.discard

  // reference.conf is how libraries ship defaults — must merge all of them
  case "reference.conf"         => MergeStrategy.concat

  // Everything else: use the default strategy (first one wins)
  case x => (assembly / assemblyMergeStrategy).value(x)
}
```

### Practical example

```bash
$ sbt assembly
[info] Packaging target/scala-2.13/forex-assembly.jar

$ ls -lh target/scala-2.13/forex-assembly.jar
-rw-r--r-- 1 juan juan 42M forex-assembly.jar
# 42MB because it includes all dependencies

$ java -jar target/scala-2.13/forex-assembly.jar
# Server starts — no classpath flags needed
```

In the Dockerfile:
```dockerfile
# Build stage — compile + assemble
FROM sbt:1.9.8-eclipse-temurin-17 AS builder
COPY . .
RUN sbt assembly

# Runtime stage — just the JRE and the JAR
FROM eclipse-temurin:17-jre-alpine
COPY --from=builder /app/target/scala-2.13/forex-assembly.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Where it's used in forex-mtl
- `build.sbt` — merge strategy configured
- `project/plugins.sbt` — plugin declared
- `Dockerfile` — `RUN sbt assembly` in builder stage

---

---

## Quick Reference

### Dependency map by concern

| Concern | Libraries |
|---------|-----------|
| FP core types | `cats-core` |
| Async / effects | `cats-effect`, `fs2` |
| HTTP server | `http4s-dsl`, `http4s-blaze-server`, `http4s-circe` |
| HTTP client | `http4s-blaze-client` |
| JSON | `circe-core`, `circe-generic`, `circe-generic-extras`, `circe-parser` |
| Configuration | `pureconfig` |
| Logging | `logback-classic` |
| Unit tests | `scalatest` |
| Property tests | `scalacheck`, `cats-scalacheck` |
| FP syntax sugar | `kind-projector` (compiler plugin) |

### Plugin map by task

| Task | Plugin |
|------|--------|
| `sbt scalafmt` | sbt-scalafmt-coursier |
| `sbt dependencyUpdates` | sbt-updates |
| `sbt ~reStart` | sbt-revolver |
| `sbt assembly` | sbt-assembly |
| `F[_]` type lambda syntax | kind-projector |
