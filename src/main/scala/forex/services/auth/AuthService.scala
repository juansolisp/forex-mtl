package forex.services.auth

import cats.effect.Sync
import cats.effect.concurrent.Ref
import cats.syntax.functor._
import forex.config.AuthConfig

trait AuthService[F[_]] {
  /** Returns `Some(token)` on successful login, `None` on bad credentials. */
  def login(username: String, password: String): F[Option[String]]
  /** Returns `true` if the token is a live session. */
  def validate(token: String): F[Boolean]
  /** Invalidates the token (no-op if already gone). */
  def logout(token: String): F[Unit]
}

object AuthService {

  def create[F[_]: Sync](cfg: AuthConfig): F[AuthService[F]] =
    Ref.of[F, Set[String]](Set.empty).map { sessions =>
      new AuthService[F] {

        def login(username: String, password: String): F[Option[String]] =
          if (username == cfg.username && password == cfg.password) {
            val token = java.util.UUID.randomUUID().toString
            sessions.update(_ + token).as(Some(token): Option[String])
          } else {
            Sync[F].pure(None)
          }

        def validate(token: String): F[Boolean] =
          sessions.get.map(_.contains(token))

        def logout(token: String): F[Unit] =
          sessions.update(_ - token)
      }
    }
}
