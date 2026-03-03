package forex.http

import cats.effect.IO
import org.http4s._
import org.http4s.implicits._
import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers

class AuthMiddlewareSpec extends AnyFunSuite with Matchers {

  implicit val cs: cats.effect.ContextShift[IO] =
    IO.contextShift(scala.concurrent.ExecutionContext.global)

  private val expectedToken = "10dc303535874aeccc86a8251e699999"

  private val stub: HttpRoutes[IO] = HttpRoutes.of[IO] {
    case req if req.method == Method.GET && req.uri.path.renderString == "/rates" =>
      IO.pure(Response[IO](Status.Ok))
  }

  private val app: HttpApp[IO] =
    AuthMiddleware(expectedToken)(stub).orNotFound

  private def run(req: Request[IO]): (Status, String) =
    app.run(req).flatMap(r => r.bodyText.compile.string.map(b => (r.status, b))).unsafeRunSync()

  test("request with correct X-Proxy-Token is allowed through") {
    val req = Request[IO](Method.GET, uri"/rates")
      .putHeaders(Header.Raw(org.typelevel.ci.CIString("X-Proxy-Token"), expectedToken))
    run(req)._1 shouldBe Status.Ok
  }

  test("request with wrong X-Proxy-Token is rejected with 401") {
    val req = Request[IO](Method.GET, uri"/rates")
      .putHeaders(Header.Raw(org.typelevel.ci.CIString("X-Proxy-Token"), "wrong-token"))
    run(req)._1 shouldBe Status.Unauthorized
  }

  test("request with missing X-Proxy-Token is rejected with 401") {
    run(Request[IO](Method.GET, uri"/rates"))._1 shouldBe Status.Unauthorized
  }

  test("401 response body mentions the expected header name") {
    val (_, body) = run(Request[IO](Method.GET, uri"/rates"))
    body should include("X-Proxy-Token")
  }

  test("request to unknown route with correct token returns 404") {
    val req = Request[IO](Method.GET, uri"/nonexistent")
      .putHeaders(Header.Raw(org.typelevel.ci.CIString("X-Proxy-Token"), expectedToken))
    run(req)._1 shouldBe Status.NotFound
  }
}
