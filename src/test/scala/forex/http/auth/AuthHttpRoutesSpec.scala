package forex.http.auth

import cats.effect.IO
import io.circe.parser.decode
import org.http4s._
import org.http4s.headers.`Content-Type`
import org.http4s.implicits._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers
import forex.config.AuthConfig
import forex.services.auth.AuthService

class AuthHttpRoutesSpec extends AnyFunSuite with Matchers {

  implicit val cs: cats.effect.ContextShift[IO] =
    IO.contextShift(scala.concurrent.ExecutionContext.global)

  private val cfg = AuthConfig("user@paidy.com", "forex2025")

  private def mkApp(): HttpApp[IO] =
    AuthService.create[IO](cfg).map { svc =>
      new AuthHttpRoutes[IO](svc).routes.orNotFound
    }.unsafeRunSync()

  private def loginReq(username: String, password: String): Request[IO] =
    Request[IO](Method.POST, uri"/auth/login")
      .withEntity(s"""{"username":"$username","password":"$password"}""")
      .withContentType(`Content-Type`(MediaType.application.json))

  private def validateReq(token: String): Request[IO] =
    Request[IO](Method.GET, uri"/auth/validate")
      .putHeaders(Header.Raw(org.typelevel.ci.CIString("Authorization"), s"Bearer $token"))

  private def logoutReq(token: String): Request[IO] =
    Request[IO](Method.POST, uri"/auth/logout")
      .putHeaders(Header.Raw(org.typelevel.ci.CIString("Authorization"), s"Bearer $token"))

  /** Run a request, returning (status, body) — body consumed inside the IO chain. */
  private def run(app: HttpApp[IO], req: Request[IO]): (Status, String) =
    app.run(req).flatMap(r => r.bodyText.compile.string.map(b => (r.status, b))).unsafeRunSync()

  test("POST /auth/login with correct credentials returns 200 and a token") {
    val app = mkApp()
    val (status, body) = run(app, loginReq("user@paidy.com", "forex2025"))

    status shouldBe Status.Ok
    val parsed = decode[LoginResponse](body)
    parsed.isRight shouldBe true
    parsed.foreach(_.token should not be empty)
  }

  test("POST /auth/login with wrong password returns 401") {
    run(mkApp(), loginReq("paidy", "wrongpassword"))._1 shouldBe Status.Unauthorized
  }

  test("GET /auth/validate with a valid token returns 200") {
    val app = mkApp()
    val (_, loginBody) = run(app, loginReq("user@paidy.com", "forex2025"))
    val token = decode[LoginResponse](loginBody).toOption.get.token
    run(app, validateReq(token))._1 shouldBe Status.Ok
  }

  test("GET /auth/validate with an invalid token returns 401") {
    run(mkApp(), validateReq("not-a-real-token"))._1 shouldBe Status.Unauthorized
  }

  test("POST /auth/logout invalidates token — subsequent validate returns 401") {
    val app = mkApp()
    val (_, loginBody) = run(app, loginReq("user@paidy.com", "forex2025"))
    val token = decode[LoginResponse](loginBody).toOption.get.token

    run(app, logoutReq(token))._1 shouldBe Status.NoContent
    run(app, validateReq(token))._1 shouldBe Status.Unauthorized
  }

  test("GET /auth/validate without Authorization header returns 401") {
    run(mkApp(), Request[IO](Method.GET, uri"/auth/validate"))._1 shouldBe Status.Unauthorized
  }

  test("POST /auth/login with wrong username returns 401") {
    run(mkApp(), loginReq("wrong@paidy.com", "forex2025"))._1 shouldBe Status.Unauthorized
  }

  test("two successful logins produce unique session tokens") {
    val app = mkApp()
    val (t1, t2) = (for {
      r1 <- app.run(loginReq("user@paidy.com", "forex2025"))
      b1 <- r1.bodyText.compile.string
      r2 <- app.run(loginReq("user@paidy.com", "forex2025"))
      b2 <- r2.bodyText.compile.string
    } yield (decode[LoginResponse](b1).toOption.get.token, decode[LoginResponse](b2).toOption.get.token))
      .unsafeRunSync()

    t1 should not equal t2
  }
}
