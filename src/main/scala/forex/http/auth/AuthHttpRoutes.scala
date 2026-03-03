package forex.http.auth

import cats.effect.Concurrent
import cats.syntax.applicative._
import cats.syntax.flatMap._
import forex.services.auth.AuthService
import io.circe.generic.semiauto.{ deriveDecoder, deriveEncoder }
import io.circe.{ Decoder, Encoder }
import org.http4s.{ AuthScheme, Credentials, HttpRoutes, Response, Status }
import org.http4s.dsl.Http4sDsl
import org.http4s.headers.Authorization
import org.http4s.server.Router
import org.http4s.circe.CirceEntityCodec._

final case class LoginRequest(username: String, password: String)
final case class LoginResponse(token: String)

object LoginRequest {
  implicit val decoder: Decoder[LoginRequest] = deriveDecoder
}

object LoginResponse {
  implicit val encoder: Encoder[LoginResponse] = deriveEncoder
  implicit val decoder: Decoder[LoginResponse] = deriveDecoder
}

/**
 * Public HTTP routes for user authentication.
 *
 * These routes are mounted **outside** [[forex.http.AuthMiddleware]] so they are reachable
 * without an `X-Proxy-Token` header — clients need them to obtain a session token in the
 * first place.
 *
 * Routes:
 *  - `POST /auth/login`    — exchange credentials for a session token
 *  - `GET  /auth/validate` — check whether a Bearer token is still valid
 *  - `POST /auth/logout`   — invalidate a Bearer token
 */
class AuthHttpRoutes[F[_]: Concurrent](authService: AuthService[F]) extends Http4sDsl[F] {

  private def extractBearer(req: org.http4s.Request[F]): Option[String] =
    req.headers.get[Authorization].collect {
      case Authorization(Credentials.Token(AuthScheme.Bearer, token)) => token
    }

  private val httpRoutes: HttpRoutes[F] = HttpRoutes.of[F] {

    case req @ POST -> Root / "login" =>
      req.as[LoginRequest].flatMap { body =>
        authService.login(body.username, body.password).flatMap {
          case Some(token) => Ok(LoginResponse(token))
          case None        => Response[F](Status.Unauthorized).pure[F]
        }
      }

    case req @ GET -> Root / "validate" =>
      extractBearer(req) match {
        case None => Response[F](Status.Unauthorized).pure[F]
        case Some(token) =>
          authService.validate(token).flatMap {
            case true  => Ok()
            case false => Response[F](Status.Unauthorized).pure[F]
          }
      }

    case req @ POST -> Root / "logout" =>
      extractBearer(req) match {
        case None => Response[F](Status.Unauthorized).pure[F]
        case Some(token) =>
          authService.logout(token).flatMap(_ => NoContent())
      }
  }

  val routes: HttpRoutes[F] = Router("/auth" -> httpRoutes)
}
