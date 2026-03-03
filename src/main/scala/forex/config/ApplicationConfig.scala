package forex.config

import scala.concurrent.duration.FiniteDuration

/**
 * Root configuration for the application, loaded from `application.conf` under the `app` key.
 *
 * PureConfig maps HOCON keys to field names using its default snake-case-to-camelCase convention:
 * e.g. the HOCON key `one-frame` maps to the field `oneFrame` here.
 */
case class AuthConfig(username: String, password: String)

case class ApplicationConfig(
    http: HttpConfig,
    /** Token that every client must send in the `X-Proxy-Token` request header. */
    proxyToken: String,
    /** Credentials for the user-facing login endpoint. */
    auth: AuthConfig,
    /** Configuration for the upstream One-Frame currency rates API. */
    oneFrame: OneFrameConfig
)

/**
 * HTTP server settings for the forex proxy itself.
 *
 * HOCON path: `app.http`
 *
 * @param host    bind address; `"0.0.0.0"` means all interfaces (required inside Docker)
 * @param port    listening port; 9090 avoids collision with One-Frame which uses 8080
 * @param timeout maximum time allowed for a single request before the Timeout middleware
 *                returns 503; set in [[forex.Module]] via `appMiddleware`
 */
case class HttpConfig(
    host: String,
    port: Int,
    timeout: FiniteDuration
)

/**
 * Connection and behaviour settings for the One-Frame upstream API.
 *
 * HOCON path: `app.one-frame`
 *
 * @param uri             base URL of the One-Frame service (e.g. `"http://one-frame:8080"`);
 *                        overridable via the `ONE_FRAME_URL` environment variable for Docker
 * @param token           authentication token sent in the custom `token` request header
 *                        (One-Frame uses a non-standard header, not Bearer auth)
 * @param refreshInterval how often [[forex.services.rates.interpreters.OneFrameCache]] fetches
 *                        all 72 currency pairs; 4 minutes keeps the proxy within the 1 000
 *                        calls/day limit (360 calls/day) while satisfying the 5-minute
 *                        freshness SLA
 */
case class OneFrameConfig(
    uri: String,
    token: String,
    refreshInterval: FiniteDuration
)
