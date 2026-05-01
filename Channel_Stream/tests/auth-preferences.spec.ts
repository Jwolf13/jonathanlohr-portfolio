/**
 * Auth + preferences integration tests.
 *
 * We cannot drive real Google OAuth in a headless browser, so these tests:
 *   1. Inject a fake (structurally-valid) JWT into sessionStorage to simulate
 *      a logged-in user.
 *   2. Intercept the backend preferences endpoints so Cognito validation is
 *      bypassed — we're testing the frontend wiring, not Cognito itself.
 *   3. Verify team selections are saved and restored across reloads.
 */

import { test, expect, Page } from "@playwright/test"

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Build a minimal fake JWT with the given payload (no real signature). */
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

const FAKE_TOKEN = makeJwt({
  sub:   "test-user-sub-123",
  email: "playwright@channelstream.test",
  name:  "Playwright Tester",
})

const API = "http://localhost:8080"

/**
 * Inject a fake access token and mock the preferences backend.
 * - GET  /v1/me/preferences → returns `savedPrefs`
 * - PUT  /v1/me/preferences → stores body in `capturedPut` and echoes it back
 */
async function loginWithMockedPrefs(
  page: Page,
  savedPrefs: { leagues: string[]; teams: string[] },
  capturedPut?: { body: { leagues: string[]; teams: string[] } | null },
) {
  // Intercept before navigation so the first load is already mocked
  await page.route(`${API}/v1/me/preferences`, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status:      200,
        contentType: "application/json",
        body:        JSON.stringify(savedPrefs),
      })
    } else if (route.request().method() === "PUT") {
      const body = route.request().postDataJSON() as { leagues: string[]; teams: string[] }
      if (capturedPut) capturedPut.body = body
      await route.fulfill({
        status:      200,
        contentType: "application/json",
        body:        JSON.stringify(body),
      })
    } else {
      await route.continue()
    }
  })

  await page.goto("/")
  // Inject token so AuthProvider.initUser() finds it on this page load
  await page.evaluate((token) => {
    sessionStorage.setItem("cs_access_token", token)
  }, FAKE_TOKEN)
  // Full reload — same path as what the callback page does after token exchange
  await page.reload()
  await page.waitForLoadState("networkidle")
}

// ── Sign-in UI ────────────────────────────────────────────────────────────────

test.describe("Sign-in UI", () => {
  test("shows Sign up / Sign in button when not logged in", async ({ page }) => {
    await page.goto("/")
    await page.evaluate(() => sessionStorage.clear())
    await page.reload()
    await page.waitForLoadState("networkidle")
    await expect(page.getByRole("button", { name: /Sign up \/ Sign in/i })).toBeVisible()
  })

  test("sign-in button redirects toward Cognito / Google", async ({ page }) => {
    await page.goto("/")
    await page.evaluate(() => sessionStorage.clear())
    await page.reload()

    // Intercept the navigation so we don't actually leave the page
    let redirectUrl = ""
    page.on("request", (req) => {
      if (req.url().includes("cognito") || req.url().includes("google")) {
        redirectUrl = req.url()
      }
    })

    // The button triggers window.location.href = Cognito URL
    // We can't follow it in CI, so just verify the URL shape
    const [popup] = await Promise.all([
      // Catch any navigation that occurs
      page.waitForNavigation({ timeout: 3000, waitUntil: "commit" }).catch(() => null),
      page.getByRole("button", { name: /Sign up \/ Sign in/i }).click(),
    ])

    // Either we navigated or we captured a request — either way Cognito domain appears
    const destination = popup?.url() ?? redirectUrl ?? page.url()
    expect(destination).toMatch(/cognito|accounts\.google|channel-stream-jl/)
  })
})

// ── Logged-in state ───────────────────────────────────────────────────────────

test.describe("Logged-in user", () => {
  test("shows user avatar and name, not sign-in button", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: [], teams: [] })

    await expect(page.getByRole("button", { name: /Sign up \/ Sign in/i })).not.toBeVisible()
    await expect(page.getByText("Playwright Tester")).toBeVisible()
  })

  test("shows hero picker when saved preferences are empty", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: [], teams: [] })

    await expect(page.getByRole("heading", { name: "What do you follow?" })).toBeVisible()
  })

  test("restores saved league selections from the backend", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: ["nba"], teams: [] })

    // NBA was saved → dashboard (not hero) is shown
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
    // The compact picker button reflects 1 filter active
    await expect(page.getByRole("button", { name: /1 selected/ })).toBeVisible()
  })

  test("restores multiple leagues from backend", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: ["nba", "mlb"], teams: [] })

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
    await expect(page.getByRole("button", { name: /2 selected/ })).toBeVisible()
  })
})

// ── Preferences save ──────────────────────────────────────────────────────────

test.describe("Preferences are saved when teams change", () => {
  test("PUT /v1/me/preferences called after selecting a league (logged in)", async ({ page }) => {
    const captured: { body: { leagues: string[]; teams: string[] } | null } = { body: null }
    await loginWithMockedPrefs(page, { leagues: [], teams: [] }, captured)

    // Start at hero screen — select NBA
    await page.getByRole("button", { name: /NBA/ }).click()

    // Wait for save to fire (it's fire-and-forget with catch)
    await page.waitForTimeout(300)

    expect(captured.body).not.toBeNull()
    expect(captured.body!.leagues).toContain("nba")
  })

  test("PUT includes existing teams when a new league is added", async ({ page }) => {
    const captured: { body: { leagues: string[]; teams: string[] } | null } = { body: null }
    // Start with NBA already selected; user picks MLB
    await loginWithMockedPrefs(page, { leagues: ["nba"], teams: [] }, captured)

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()

    // Open compact picker and add MLB
    await page.getByRole("button", { name: /selected/ }).click()
    await page.getByRole("button", { name: /MLB/ }).click()
    await page.waitForTimeout(300)

    expect(captured.body).not.toBeNull()
    expect(captured.body!.leagues).toContain("nba")
    expect(captured.body!.leagues).toContain("mlb")
  })

  test("clearing all preferences sends empty leagues and teams", async ({ page }) => {
    const captured: { body: { leagues: string[]; teams: string[] } | null } = { body: null }
    await loginWithMockedPrefs(page, { leagues: ["nba"], teams: [] }, captured)

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()

    // Open compact picker and clear all
    await page.getByRole("button", { name: /selected/ }).click()
    await page.getByRole("button", { name: "Clear all" }).click()
    await page.waitForTimeout(300)

    expect(captured.body).not.toBeNull()
    expect(captured.body!.leagues).toHaveLength(0)
    expect(captured.body!.teams).toHaveLength(0)
  })
})

// ── Sign-out ──────────────────────────────────────────────────────────────────

test.describe("Sign-out", () => {
  test("clears user and returns to hero picker", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: ["nba"], teams: [] })
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()

    await page.getByRole("button", { name: "Sign out" }).click()

    // User gone, hero picker back
    await expect(page.getByRole("button", { name: /Sign up \/ Sign in/i })).toBeVisible()
    await expect(page.getByRole("heading", { name: "What do you follow?" })).toBeVisible()
  })

  test("sign-out clears sessionStorage tokens", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: ["nba"], teams: [] })
    await page.getByRole("button", { name: "Sign out" }).click()

    const token = await page.evaluate(() => sessionStorage.getItem("cs_access_token"))
    expect(token).toBeNull()
  })

  test("after sign-out, signing in again starts fresh from backend prefs", async ({ page }) => {
    const captured: { body: { leagues: string[]; teams: string[] } | null } = { body: null }
    await loginWithMockedPrefs(page, { leagues: ["nba"], teams: [] }, captured)
    await page.getByRole("button", { name: "Sign out" }).click()

    // Simulate a fresh sign-in: inject token again
    await page.evaluate((token) => sessionStorage.setItem("cs_access_token", token), FAKE_TOKEN)
    await page.reload()
    await page.waitForLoadState("networkidle")

    // Backend still returns nba → dashboard shown
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
  })
})

// ── Sports and Schedule pages respect saved prefs ─────────────────────────────

test.describe("Sports and Schedule pages with saved prefs", () => {
  test("sports page compact picker shows selected count", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: ["nba", "mlb"], teams: [] })
    await page.goto("/sports")
    await page.waitForLoadState("networkidle")

    await expect(page.getByRole("button", { name: /2 selected/ })).toBeVisible()
  })

  test("schedule page compact picker shows selected count", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: ["nba"], teams: [] })
    await page.goto("/schedule")
    await page.waitForLoadState("networkidle")

    await expect(page.getByRole("button", { name: /1 selected/ })).toBeVisible()
  })

  test("sports page shows 'use filter' prompt when nothing selected", async ({ page }) => {
    await loginWithMockedPrefs(page, { leagues: [], teams: [] })
    await page.goto("/sports")
    await page.waitForLoadState("networkidle")

    // If there are live games, should see the "use filter above" prompt
    // (or the "no games live" empty state — both are acceptable)
    const hasPrompt = await page.getByText(/Use the filter above/).isVisible().catch(() => false)
    const hasEmpty  = await page.getByText(/No games live right now/).isVisible().catch(() => false)
    expect(hasPrompt || hasEmpty).toBe(true)
  })
})
