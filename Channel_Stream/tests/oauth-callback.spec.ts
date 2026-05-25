/**
 * OAuth callback integration tests.
 *
 * Real Google OAuth cannot run in a headless browser (Google blocks bots),
 * so we simulate it by:
 *   1. Seeding sessionStorage with the PKCE state/verifier the app would have
 *      stored before redirecting to Cognito.
 *   2. Intercepting the Cognito /oauth2/token endpoint and returning a fake
 *      token response — we're testing the frontend wiring, not Cognito itself.
 *   3. Navigating to the callback URL with a fake ?code= and ?state= as
 *      Cognito would after a successful Google login.
 *   4. Asserting the user ends up signed in and on the correct page.
 */

import { test, expect } from "@playwright/test"

const COGNITO_DOMAIN = "https://channel-stream-jl.auth.us-east-1.amazoncognito.com"
const API            = "http://localhost:8080"

function makeJwt(payload: Record<string, string>): string {
  const b64url = (obj: object) =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=/g, "")
  const header = b64url({ alg: "HS256", typ: "JWT" })
  const body   = b64url(payload)
  return `${header}.${body}.fake-signature`
}

const FAKE_ACCESS_TOKEN = makeJwt({
  sub:   "cognito-user-abc123",
  email: "oauthtest@channelstream.test",
  name:  "OAuth Test User",
})

const FAKE_ID_TOKEN = makeJwt({
  sub:   "cognito-user-abc123",
  email: "oauthtest@channelstream.test",
  name:  "OAuth Test User",
})

// ── helpers ───────────────────────────────────────────────────────────────────

/** Mock the Cognito token endpoint and the preferences backend, then load the
 *  callback URL with a fake code+state that matches the seeded sessionStorage. */
async function simulateOAuthCallback(page: import("@playwright/test").Page) {
  const fakeState    = "test-state-xyz"
  const fakeVerifier = "test-verifier-abc"
  const fakeCode     = "fake-auth-code-123"

  // 1. Mock Cognito token exchange — intercept before any navigation
  await page.route(`${COGNITO_DOMAIN}/oauth2/token`, async (route) => {
    await route.fulfill({
      status:      200,
      contentType: "application/json",
      body:        JSON.stringify({
        access_token:  FAKE_ACCESS_TOKEN,
        id_token:      FAKE_ID_TOKEN,
        refresh_token: "fake-refresh-token",
        token_type:    "Bearer",
        expires_in:    3600,
      }),
    })
  })

  // 2. Mock the preferences backend so AuthProvider doesn't error on load
  await page.route(`${API}/v1/me/preferences`, async (route) => {
    await route.fulfill({
      status:      200,
      contentType: "application/json",
      body:        JSON.stringify({ leagues: [], teams: [] }),
    })
  })

  // 3. Navigate to home first so we have an origin to set sessionStorage on
  await page.goto("/")

  // 4. Seed sessionStorage with the PKCE values the app stores before redirecting
  await page.evaluate(
    ({ state, verifier }) => {
      sessionStorage.setItem("pkce_state",    state)
      sessionStorage.setItem("pkce_verifier", verifier)
    },
    { state: fakeState, verifier: fakeVerifier },
  )

  // 5. Navigate to the callback URL as Cognito would redirect after Google login
  await page.goto(`/auth/callback?code=${fakeCode}&state=${fakeState}`)
  await page.waitForLoadState("networkidle")
}

// ── tests ─────────────────────────────────────────────────────────────────────

test.describe("OAuth callback", () => {
  test("shows spinner while processing", async ({ page }) => {
    const fakeState    = "state-spinner"
    const fakeVerifier = "verifier-spinner"

    // Slow the token exchange so we can observe the spinner
    await page.route(`${COGNITO_DOMAIN}/oauth2/token`, async (route) => {
      await new Promise((r) => setTimeout(r, 800))
      await route.fulfill({
        status:      200,
        contentType: "application/json",
        body:        JSON.stringify({
          access_token: FAKE_ACCESS_TOKEN,
          id_token:     FAKE_ID_TOKEN,
          token_type:   "Bearer",
          expires_in:   3600,
        }),
      })
    })

    await page.route(`${API}/v1/me/preferences`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ leagues: [], teams: [] }),
      })
    })

    await page.goto("/")
    await page.evaluate(
      ({ state, verifier }) => {
        sessionStorage.setItem("pkce_state",    state)
        sessionStorage.setItem("pkce_verifier", verifier)
      },
      { state: fakeState, verifier: fakeVerifier },
    )

    await page.goto(`/auth/callback?code=any&state=${fakeState}`)
    await expect(page.getByText("Signing you in")).toBeVisible()
  })

  test("stores access token in sessionStorage after successful exchange", async ({ page }) => {
    await simulateOAuthCallback(page)

    // After redirect, check that the token was stored
    const token = await page.evaluate(() => sessionStorage.getItem("cs_access_token"))
    expect(token).not.toBeNull()
    expect(token).toContain(".")   // has JWT structure
  })

  test("redirects to the app home page (not portfolio root) after sign-in", async ({ page }) => {
    await simulateOAuthCallback(page)

    // Should land on / (local dev has no basePath, so this is localhost:3001/)
    // In production this would be /channel-stream/ — the key check is that
    // it does NOT stay on /auth/callback
    expect(page.url()).not.toContain("/auth/callback")
    expect(page.url()).toMatch(/localhost:3001\/?$/)
  })

  test("user is signed in after callback redirect", async ({ page }) => {
    await simulateOAuthCallback(page)

    // The user name from the JWT payload should appear in the UI
    await expect(page.getByText("OAuth Test User")).toBeVisible()
  })

  test("shows sign-in failed when code is missing", async ({ page }) => {
    await page.goto("/auth/callback")
    await page.waitForLoadState("networkidle")
    await expect(page.getByText("Sign-in failed")).toBeVisible()
  })

  test("shows sign-in failed when state does not match", async ({ page }) => {
    await page.route(`${COGNITO_DOMAIN}/oauth2/token`, async (route) => {
      await route.fulfill({
        status: 400,
        body:   JSON.stringify({ error: "invalid_grant" }),
      })
    })

    await page.goto("/")
    await page.evaluate(() => {
      sessionStorage.setItem("pkce_state",    "correct-state")
      sessionStorage.setItem("pkce_verifier", "some-verifier")
    })

    // Wrong state in URL — should fail
    await page.goto("/auth/callback?code=abc&state=wrong-state")
    await page.waitForLoadState("networkidle")
    await expect(page.getByText("Sign-in failed")).toBeVisible()
  })

  test("shows sign-in failed when Cognito returns an error param", async ({ page }) => {
    await page.goto("/auth/callback?error=access_denied&error_description=User+cancelled")
    await page.waitForLoadState("networkidle")
    await expect(page.getByText("Sign-in failed")).toBeVisible()
  })

  test("shows sign-in failed when token exchange returns non-OK", async ({ page }) => {
    await page.route(`${COGNITO_DOMAIN}/oauth2/token`, async (route) => {
      await route.fulfill({ status: 400, body: JSON.stringify({ error: "invalid_grant" }) })
    })

    await page.goto("/")
    await page.evaluate(() => {
      sessionStorage.setItem("pkce_state",    "s")
      sessionStorage.setItem("pkce_verifier", "v")
    })

    await page.goto("/auth/callback?code=bad&state=s")
    await page.waitForLoadState("networkidle")
    await expect(page.getByText("Sign-in failed")).toBeVisible()
  })

  test("clears PKCE verifier and state after use", async ({ page }) => {
    await simulateOAuthCallback(page)

    const verifier = await page.evaluate(() => sessionStorage.getItem("pkce_verifier"))
    const state    = await page.evaluate(() => sessionStorage.getItem("pkce_state"))
    expect(verifier).toBeNull()
    expect(state).toBeNull()
  })
})
