package forex.http

import cats.data.{ Kleisli, OptionT }
import cats.effect.Sync
import cats.syntax.applicative._
import org.http4s.{ HttpRoutes, Request, Response, Status }
import org.typelevel.ci.CIString

/**
 * Simple fixed-token authentication middleware.
 *
 * Every request must carry the header `X-Proxy-Token` with the configured value.
 * Requests with a missing or incorrect token are rejected with 401 before reaching
 * any route handler.
 *
 * Usage:
 * {{{
 *   val protectedRoutes = AuthMiddleware(expectedToken)(myRoutes)
 * }}}
 */
object AuthMiddleware {

  private val tokenHeader = CIString("X-Proxy-Token")

  /**
   * Wraps `routes` so that every request is validated against `expectedToken`.
   * Returns 401 Unauthorized for missing or wrong tokens; otherwise delegates to `routes`.
   */
  def apply[F[_]: Sync](expectedToken: String)(routes: HttpRoutes[F]): HttpRoutes[F] =
    Kleisli { (req: Request[F]) =>
      val tokenOpt = req.headers.get(tokenHeader).map(_.head.value)
      tokenOpt match {
        case Some(t) if t == expectedToken =>
          routes(req)
        case _ =>
          OptionT.liftF(
            Response[F](Status.Unauthorized)
              .withEntity("Missing or invalid X-Proxy-Token header")
              .pure[F]
          )
      }
    }

}
