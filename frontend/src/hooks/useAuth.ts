import { useState, useEffect } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

export type AuthStatus = "pending" | "authenticated" | "unauthenticated";

type Listener = (status: AuthStatus) => void;

// ─── Module-level singleton ───────────────────────────────────────────────────
// Pattern mirrors useEventStream.ts: state lives at module scope so all hook
// instances share a single source of truth without React context.

const TOKEN_KEY = "forex_session_token";

let globalStatus: AuthStatus = "pending";
const listeners = new Set<Listener>();

function notifyAll() {
  listeners.forEach((l) => l(globalStatus));
}

function setStatus(s: AuthStatus) {
  globalStatus = s;
  notifyAll();
}

// ─── Bootstrap ───────────────────────────────────────────────────────────────
// Called once at module load (bottom of this file).
// Validates any stored token before the first component mounts so that
// already-authenticated users see the dashboard immediately without a flash of
// the login page.

async function bootstrap(): Promise<void> {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    setStatus("unauthenticated");
    return;
  }
  try {
    const resp = await fetch("/auth/validate", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (resp.ok) {
      setStatus("authenticated");
    } else {
      localStorage.removeItem(TOKEN_KEY);
      setStatus("unauthenticated");
    }
  } catch {
    // Network error — treat as unauthenticated so the user can try again.
    localStorage.removeItem(TOKEN_KEY);
    setStatus("unauthenticated");
  }
}

// ─── Public API ──────────────────────────────────────────────────────────────

/** Exchange credentials for a session token. Throws on failure. */
export async function login(username: string, password: string): Promise<void> {
  const resp = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) {
    throw new Error("Invalid username or password");
  }
  const { token } = await resp.json();
  localStorage.setItem(TOKEN_KEY, token);
  setStatus("authenticated");
}

/** Invalidate the current session and redirect to the login page. */
export async function logout(): Promise<void> {
  const token = localStorage.getItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_KEY);
  setStatus("unauthenticated");
  if (token) {
    // Fire-and-forget — the server-side cleanup is best-effort.
    fetch("/auth/logout", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => {});
  }
}

/** React hook that reflects the current auth status. */
export function useAuth(): { status: AuthStatus; login: typeof login; logout: typeof logout } {
  const [status, setLocalStatus] = useState<AuthStatus>(globalStatus);

  useEffect(() => {
    // Sync with module state in case it changed between render and mount.
    setLocalStatus(globalStatus);
    listeners.add(setLocalStatus);
    return () => {
      listeners.delete(setLocalStatus);
    };
  }, []);

  return { status, login, logout };
}

// ─── Kick off validation immediately at module load ───────────────────────────
bootstrap();
