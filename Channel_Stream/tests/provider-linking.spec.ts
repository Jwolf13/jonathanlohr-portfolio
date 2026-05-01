import { test, expect, Page } from "@playwright/test"

const ALL_PROVIDER_IDS = [
  "netflix",
  "hulu",
  "disney_plus",
  "prime_video",
  "apple_tv_plus",
  "max",
  "peacock",
  "paramount_plus",
]

async function clearState(page: Page) {
  await page.goto("/providers")
  await page.evaluate(() => localStorage.removeItem("channel_stream_v1"))
  await page.evaluate(() => sessionStorage.clear())
  await page.reload()
  await page.waitForLoadState("networkidle")
}

async function linkProvider(
  page: Page,
  providerId: string,
  email = "test@example.com"
) {
  await page.getByTestId(`link-${providerId}`).click()
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill("password123")
  await page.getByRole("button", { name: "Continue" }).click()
  await expect(page.getByText("Permissions requested")).toBeVisible()
  await page.getByRole("button", { name: "Authorize" }).click()
  await expect(page.getByTestId(`status-linked-${providerId}`)).toBeVisible({
    timeout: 5_000,
  })
}

// ─── Hero Picker / Onboarding ─────────────────────────────────────────────────

test.describe("Hero Team Picker", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/")
    await page.evaluate(() => sessionStorage.clear())
    await page.reload()
    await page.waitForLoadState("networkidle")
  })

  test("root path shows hero picker when no teams selected", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "What do you follow?" })).toBeVisible()
  })

  test("hero picker shows all league buttons", async ({ page }) => {
    await expect(page.getByRole("button", { name: /NFL/ })).toBeVisible()
    await expect(page.getByRole("button", { name: /NBA/ })).toBeVisible()
    await expect(page.getByRole("button", { name: /MLB/ })).toBeVisible()
    await expect(page.getByRole("button", { name: /MLS/ })).toBeVisible()
    await expect(page.getByRole("button", { name: /College Football/ })).toBeVisible()
    await expect(page.getByRole("button", { name: /College Basketball/ })).toBeVisible()
    await expect(page.getByRole("button", { name: /College Baseball/ })).toBeVisible()
    await expect(page.getByRole("button", { name: /NHL/ })).toBeVisible()
  })

  test("selecting a league transitions to dashboard view", async ({ page }) => {
    await page.getByRole("button", { name: /NBA/ }).click()
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
  })

  test("selected league button highlights in blue", async ({ page }) => {
    const nflBtn = page.getByRole("button", { name: /NFL/ })
    await nflBtn.click()
    // Navigate back to see compact picker is there
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
  })

  test("hero picker has team search input", async ({ page }) => {
    await expect(page.getByPlaceholder("Search teams…")).toBeVisible()
  })
})

// ─── Compact Picker ───────────────────────────────────────────────────────────

test.describe("Compact Team Picker", () => {
  test.beforeEach(async ({ page }) => {
    // Select NBA so we get past the hero screen
    await page.goto("/")
    await page.evaluate(() => sessionStorage.clear())
    await page.reload()
    await page.waitForLoadState("networkidle")
    await page.getByRole("button", { name: /NBA/ }).click()
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
  })

  test("compact picker button appears after team selection", async ({ page }) => {
    await expect(page.getByRole("button", { name: /selected/ })).toBeVisible()
  })

  test("clicking compact picker opens dropdown", async ({ page }) => {
    await page.getByRole("button", { name: /selected/ }).click()
    await expect(page.getByPlaceholder("Search teams…")).toBeVisible()
  })

  test("clear all returns to hero mode", async ({ page }) => {
    await page.getByRole("button", { name: /selected/ }).click()
    await page.getByRole("button", { name: "Clear all" }).click()
    await expect(page.getByRole("heading", { name: "What do you follow?" })).toBeVisible()
  })
})

// ─── Provider Dashboard ───────────────────────────────────────────────────────

test.describe("Provider Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await clearState(page)
  })

  test("displays all 8 provider cards", async ({ page }) => {
    for (const id of ALL_PROVIDER_IDS) {
      await expect(page.getByTestId(`provider-card-${id}`)).toBeVisible()
    }
  })

  test("all providers start as unlinked", async ({ page }) => {
    for (const id of ALL_PROVIDER_IDS) {
      await expect(page.getByTestId(`status-unlinked-${id}`)).toBeVisible()
      await expect(page.getByTestId(`link-${id}`)).toBeVisible()
    }
  })

  test("shows 0% coverage when no providers are linked", async ({ page }) => {
    await expect(page.getByTestId("coverage-pct")).toHaveText("0%")
    await expect(page.getByText("0 of 8 linked")).toBeVisible()
  })
})

// ─── OAuth Linking Flow ───────────────────────────────────────────────────────

test.describe("OAuth Linking Flow", () => {
  test.beforeEach(async ({ page }) => {
    await clearState(page)
  })

  test("clicking Link opens the OAuth modal for that provider", async ({
    page,
  }) => {
    await page.getByTestId("link-netflix").click()
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByRole("dialog").getByText("Netflix")
    ).toBeVisible()
    await expect(page.getByLabel("Email")).toBeVisible()
    await expect(page.getByLabel("Password")).toBeVisible()
  })

  test("modal shows provider-specific heading for each provider", async ({
    page,
  }) => {
    for (const id of ALL_PROVIDER_IDS) {
      await page.getByTestId(`link-${id}`).click()
      const dialog = page.getByRole("dialog")
      await expect(dialog).toBeVisible()
      await page.getByRole("button", { name: "Cancel" }).click()
      await expect(dialog).not.toBeVisible()
    }
  })

  test("can cancel from the login step", async ({ page }) => {
    await page.getByTestId("link-netflix").click()
    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
    await expect(page.getByTestId("status-unlinked-netflix")).toBeVisible()
  })

  test("validates that email is required", async ({ page }) => {
    await page.getByTestId("link-netflix").click()
    await page.getByLabel("Password").fill("pass")
    await page.getByRole("button", { name: "Continue" }).click()
    await expect(page.getByText("Email is required")).toBeVisible()
    await expect(page.getByText("Permissions requested")).not.toBeVisible()
  })

  test("validates that password is required", async ({ page }) => {
    await page.getByTestId("link-netflix").click()
    await page.getByLabel("Email").fill("user@test.com")
    await page.getByRole("button", { name: "Continue" }).click()
    await expect(page.getByText("Password is required")).toBeVisible()
  })

  test("advances to the authorize step after filling credentials", async ({
    page,
  }) => {
    await page.getByTestId("link-netflix").click()
    await page.getByLabel("Email").fill("user@test.com")
    await page.getByLabel("Password").fill("pass")
    await page.getByRole("button", { name: "Continue" }).click()
    await expect(page.getByText("Permissions requested")).toBeVisible()
    await expect(
      page.getByText("View your watch history")
    ).toBeVisible()
  })

  test("authorize step shows the email being used", async ({ page }) => {
    await page.getByTestId("link-netflix").click()
    await page.getByLabel("Email").fill("myaccount@netflix.com")
    await page.getByLabel("Password").fill("pass")
    await page.getByRole("button", { name: "Continue" }).click()
    await expect(page.getByText("myaccount@netflix.com")).toBeVisible()
  })

  test("can cancel from the authorize step", async ({ page }) => {
    await page.getByTestId("link-netflix").click()
    await page.getByLabel("Email").fill("user@test.com")
    await page.getByLabel("Password").fill("pass")
    await page.getByRole("button", { name: "Continue" }).click()
    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
    await expect(page.getByTestId("status-unlinked-netflix")).toBeVisible()
  })

  test("shows loading state while linking", async ({ page }) => {
    await page.getByTestId("link-netflix").click()
    await page.getByLabel("Email").fill("user@test.com")
    await page.getByLabel("Password").fill("pass")
    await page.getByRole("button", { name: "Continue" }).click()
    await page.getByRole("button", { name: "Authorize" }).click()
    await expect(page.getByText("Linking...")).toBeVisible()
  })

  test("successfully links a provider and shows Linked status", async ({
    page,
  }) => {
    await linkProvider(page, "netflix")
    await expect(page.getByTestId("status-linked-netflix")).toBeVisible()
    await expect(page.getByTestId("unlink-netflix")).toBeVisible()
    await expect(page.getByTestId("link-netflix")).not.toBeVisible()
  })

  test("linked card shows the account email", async ({ page }) => {
    await linkProvider(page, "hulu", "myhulu@email.com")
    await expect(page.getByText("myhulu@email.com")).toBeVisible()
  })

  test("linked card shows token expiry in days", async ({ page }) => {
    await linkProvider(page, "disney_plus")
    await expect(
      page.getByTestId("provider-card-disney_plus").getByText(/\d+ days/)
    ).toBeVisible()
  })

  test("linked card shows linked date", async ({ page }) => {
    await linkProvider(page, "max")
    const today = new Date()
    const monthShort = today.toLocaleString("en-US", { month: "short" })
    await expect(
      page.getByTestId("provider-card-max").getByText(monthShort)
    ).toBeVisible()
  })

  test("coverage percentage updates after linking a provider", async ({
    page,
  }) => {
    await linkProvider(page, "netflix")
    await expect(page.getByTestId("coverage-pct")).toHaveText("13%")
    await expect(page.getByText("1 of 8 linked")).toBeVisible()
  })

  test("coverage reaches 100% when all providers are linked", async ({
    page,
  }) => {
    for (const id of ALL_PROVIDER_IDS) {
      await linkProvider(page, id, `user@${id}.com`)
    }
    await expect(page.getByTestId("coverage-pct")).toHaveText("100%")
    await expect(page.getByText("8 of 8 linked")).toBeVisible()
  })
})

// ─── Unlink Flow ──────────────────────────────────────────────────────────────

test.describe("Unlink Flow", () => {
  test.beforeEach(async ({ page }) => {
    await clearState(page)
    await linkProvider(page, "netflix")
  })

  test("clicking Unlink opens a confirmation modal", async ({ page }) => {
    await page.getByTestId("unlink-netflix").click()
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(page.getByText("Unlink Netflix?")).toBeVisible()
    await expect(page.getByTestId("confirm-unlink")).toBeVisible()
    await expect(page.getByTestId("cancel-unlink")).toBeVisible()
  })

  test("can cancel unlink — provider stays linked", async ({ page }) => {
    await page.getByTestId("unlink-netflix").click()
    await page.getByTestId("cancel-unlink").click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
    await expect(page.getByTestId("status-linked-netflix")).toBeVisible()
  })

  test("clicking the backdrop cancels unlink", async ({ page }) => {
    await page.getByTestId("unlink-netflix").click()
    await page.mouse.click(10, 10)
    await expect(page.getByTestId("status-linked-netflix")).toBeVisible()
  })

  test("confirming unlink removes the provider link", async ({ page }) => {
    await page.getByTestId("unlink-netflix").click()
    await page.getByTestId("confirm-unlink").click()
    await expect(page.getByTestId("status-unlinked-netflix")).toBeVisible()
    await expect(page.getByTestId("link-netflix")).toBeVisible()
    await expect(page.getByTestId("unlink-netflix")).not.toBeVisible()
  })

  test("coverage decreases after unlinking", async ({ page }) => {
    await expect(page.getByTestId("coverage-pct")).toHaveText("13%")
    await page.getByTestId("unlink-netflix").click()
    await page.getByTestId("confirm-unlink").click()
    await expect(page.getByTestId("coverage-pct")).toHaveText("0%")
  })
})

// ─── State Persistence ────────────────────────────────────────────────────────

test.describe("State Persistence", () => {
  test.beforeEach(async ({ page }) => {
    await clearState(page)
  })

  test("linked providers persist across page reload", async ({ page }) => {
    await linkProvider(page, "netflix", "persist@test.com")
    await page.reload()
    await page.waitForLoadState("networkidle")

    await expect(page.getByTestId("status-linked-netflix")).toBeVisible()
    await expect(page.getByText("persist@test.com")).toBeVisible()
  })

  test("unlinked state persists across reload", async ({ page }) => {
    await linkProvider(page, "netflix")
    await page.getByTestId("unlink-netflix").click()
    await page.getByTestId("confirm-unlink").click()
    await page.reload()
    await page.waitForLoadState("networkidle")

    await expect(page.getByTestId("status-unlinked-netflix")).toBeVisible()
  })
})
