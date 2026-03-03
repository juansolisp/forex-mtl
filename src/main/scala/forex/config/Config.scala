package forex.config

import cats.effect.Sync
import fs2.Stream

import pureconfig.ConfigSource
import pureconfig.generic.auto._

object Config {

  /**
   * Load [[ApplicationConfig]] from the default config source (application.conf on the classpath)
   * at the given HOCON path, wrapped in an fs2 `Stream`.
   *
   * Returning a `Stream[F, ApplicationConfig]` rather than `F[ApplicationConfig]` keeps the
   * wiring in `Main.scala` uniform: the entire application is expressed as a single `Stream`
   * that is composed with `for`-comprehension, and config loading participates naturally.
   * It also leaves the door open for hot-reload in the future — a `Stream` could emit new
   * config values on file-change signals without changing the wiring contract.
   *
   * `loadOrThrow` is intentional: a misconfigured application should fail at startup with a
   * clear error rather than silently using defaults and misbehaving at runtime.
   *
   * @param path the property path inside the default configuration (e.g. `"app"`)
   */
  def stream[F[_]: Sync](path: String): Stream[F, ApplicationConfig] = {
    Stream.eval(Sync[F].delay(
      ConfigSource.default.at(path).loadOrThrow[ApplicationConfig]))
  }

}
