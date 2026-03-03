/**
 * Thin fetch wrapper that automatically injects the X-Proxy-Token header on every
 * request sent to the forex-mtl backend.
 *
 * All components must use apiFetch() instead of the raw fetch() global so that the
 * auth token is never accidentally omitted.
 */

const PROXY_TOKEN = "10dc303535874aeccc86a8251e699999";

export function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  headers.set("X-Proxy-Token", PROXY_TOKEN);
  return fetch(input, { ...init, headers });
}
