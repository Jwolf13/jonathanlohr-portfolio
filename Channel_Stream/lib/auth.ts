// PKCE OAuth utilities for Cognito + Google sign-in.
// All token storage uses sessionStorage — tokens are automatically cleared
// when the user closes the tab or browser, which satisfies the "session only"
// requirement for unauthenticated users.

export const COGNITO_DOMAIN = process.env.NEXT_PUBLIC_COGNITO_DOMAIN ?? ""
export const CLIENT_ID      = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID ?? ""
export const REDIRECT_URI   = process.env.NEXT_PUBLIC_REDIRECT_URI ?? ""

// ── PKCE helpers ──────────────────────────────────────────────────────────────

function randomString(length = 64): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
  const arr   = crypto.getRandomValues(new Uint8Array(length))
  return Array.from(arr, (b) => chars[b % chars.length]).join("")
}

async function sha256(plain: string): Promise<ArrayBuffer> {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(plain))
}

function base64UrlEncode(buf: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(buf)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "")
}

// ── Auth flow ─────────────────────────────────────────────────────────────────

/** Redirect the browser to the Cognito Google sign-in page. */
export async function startLogin(): Promise<void> {
  const verifier  = randomString(64)
  const challenge = base64UrlEncode(await sha256(verifier))
  const state     = randomString(16)

  sessionStorage.setItem("pkce_verifier", verifier)
  sessionStorage.setItem("pkce_state",    state)

  const params = new URLSearchParams({
    response_type:         "code",
    client_id:             CLIENT_ID,
    redirect_uri:          REDIRECT_URI,
    scope:                 "openid email profile",
    state,
    code_challenge:        challenge,
    code_challenge_method: "S256",
    identity_provider:     "Google",
  })

  window.location.href = `${COGNITO_DOMAIN}/oauth2/authorize?${params}`
}

export interface TokenSet {
  access_token:  string
  id_token:      string
  refresh_token?: string
}

/** Exchange the authorization code for tokens. Called from the callback page. */
export async function exchangeCode(code: string, state: string): Promise<TokenSet | null> {
  const savedState   = sessionStorage.getItem("pkce_state")
  const codeVerifier = sessionStorage.getItem("pkce_verifier")

  if (state !== savedState || !codeVerifier) return null

  sessionStorage.removeItem("pkce_verifier")
  sessionStorage.removeItem("pkce_state")

  const res = await fetch(`${COGNITO_DOMAIN}/oauth2/token`, {
    method:  "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body:    new URLSearchParams({
      grant_type:    "authorization_code",
      client_id:     CLIENT_ID,
      redirect_uri:  REDIRECT_URI,
      code,
      code_verifier: codeVerifier,
    }),
  })

  if (!res.ok) return null
  return res.json() as Promise<TokenSet>
}

// ── Token storage (sessionStorage = tab-scoped, clears on close) ──────────────

export function storeTokens(tokens: TokenSet): void {
  sessionStorage.setItem("cs_access_token",  tokens.access_token)
  sessionStorage.setItem("cs_id_token",      tokens.id_token)
  if (tokens.refresh_token) {
    sessionStorage.setItem("cs_refresh_token", tokens.refresh_token)
  }
}

export function getStoredToken(): string | null {
  return sessionStorage.getItem("cs_access_token")
}

export function clearTokens(): void {
  sessionStorage.removeItem("cs_access_token")
  sessionStorage.removeItem("cs_id_token")
  sessionStorage.removeItem("cs_refresh_token")
}

/** Parse the payload section of a JWT without verifying the signature. */
export function parseJwtPayload(token: string): Record<string, unknown> {
  try {
    const payload = token.split(".")[1]
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")))
  } catch {
    return {}
  }
}
