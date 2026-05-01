# Module 6 — Testing with Playwright
### Automatically Verifying That Everything Works, Every Time

---

> **Goal**: Write automated tests using Playwright that verify the API endpoints return correct data AND that the UI displays it properly. Learn the difference between unit, integration, and end-to-end tests.

> **Time**: ~4–5 hours

---

## 6.1 The Three Types of Tests

Before writing a single test, understand what you're testing:

### Unit Tests
Test a single function in isolation. No database, no HTTP, no browser.

```go
// Go unit test
func TestFormatResumeTime(t *testing.T) {
    // This function converts seconds to "mm:ss" format
    if got := formatResumeTime(1847); got != "30:47" {
        t.Errorf("want 30:47, got %s", got)
    }
    if got := formatResumeTime(3661); got != "1:01:01" {
        t.Errorf("want 1:01:01, got %s", got)
    }
}
```

Best for: Pure functions with clear inputs and outputs. Runs in milliseconds.

### Integration Tests
Test a module working with real dependencies (real database, real Redis).

```go
// Test the actual Up Next query against a real database
func TestGetUpNextFeed(t *testing.T) {
    // Assumes a test database with known seed data
    req := httptest.NewRequest("GET", "/v1/feed/up-next?profile_id=00000000-0000-0000-0000-000000000002", nil)
    w := httptest.NewRecorder()

    GetUpNext(w, req)

    if w.Code != 200 {
        t.Fatalf("expected 200, got %d", w.Code)
    }
    // Parse response and verify item count
}
```

Best for: Database queries, API handlers, caching logic. Slower than unit tests.

### End-to-End (E2E) Tests
Open a real browser, click through the app, verify the result on screen.

```typescript
// Playwright E2E test
test("Up Next page shows in-progress items", async ({ page }) => {
    await page.goto("/up-next");
    await expect(page.locator("[data-testid='up-next-card']").first()).toBeVisible();
});
```

Best for: Full user flows. Catches bugs that unit and integration tests miss. Slowest.

---

## 6.2 Go Unit Tests (Backend)

Go has built-in testing support. Test files end in `_test.go`.

### Write Your First Unit Test

Create `internal/feed/feed_test.go`:

```go
package feed_test  // Note: _test suffix keeps test code separate from production code

import (
    "testing"
    "time"

    "github.com/jwolf13/channel-stream/internal/feed"
)

// Test function names must start with "Test"
func TestFeedResponseHasCorrectFeedName(t *testing.T) {
    response := feed.FeedResponse{
        Feed:        "up_next",
        GeneratedAt: time.Now(),
        Items:       []feed.FeedItem{},
        Count:       0,
    }

    if response.Feed != "up_next" {
        t.Errorf("expected feed name 'up_next', got '%s'", response.Feed)
    }
}

func TestFeedItemHasRequiredFields(t *testing.T) {
    item := feed.FeedItem{
        ContentID: "cs_severance_s3",
        Title:     "Severance",
        Type:      "series",
        Provider:  "apple_tv_plus",
    }

    if item.ContentID == "" {
        t.Error("ContentID should not be empty")
    }
    if item.Title == "" {
        t.Error("Title should not be empty")
    }
    if item.Type == "" {
        t.Error("Type should not be empty")
    }
}

// Table-driven test: run the same test with multiple inputs
func TestProgressPercentValidation(t *testing.T) {
    tests := []struct {
        name    string
        pct     int
        wantErr bool
    }{
        {"valid 0%",    0,   false},
        {"valid 50%",   50,  false},
        {"valid 100%",  100, false},
        {"invalid -1",  -1,  true},
        {"invalid 101", 101, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            isValid := tt.pct >= 0 && tt.pct <= 100
            if isValid && tt.wantErr {
                t.Errorf("pct=%d: expected invalid but got valid", tt.pct)
            }
            if !isValid && !tt.wantErr {
                t.Errorf("pct=%d: expected valid but got invalid", tt.pct)
            }
        })
    }
}
```

### Run Go Tests

```bash
# Run all tests
go test ./...

# Run with verbose output (see each test name)
go test ./... -v

# Run tests in a specific package
go test ./internal/feed/...

# Run a specific test by name
go test ./internal/feed/... -run TestFeedResponseHasCorrectFeedName

# Run tests and see coverage
go test ./... -cover
# Shows: coverage: 45.2% of statements in ./internal/feed/
```

---

## 6.3 Go Integration Tests (Backend API)

Integration tests use `httptest` — a standard library package that lets you test HTTP handlers without starting a real server.

Create `internal/feed/integration_test.go`:

```go
package feed_test

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/jwolf13/channel-stream/internal/db"
    "github.com/jwolf13/channel-stream/internal/feed"
)

// TestMain runs before all tests in this package.
// Use it to set up shared resources like database connections.
func TestMain(m *testing.M) {
    // Connect to the local Supabase database
    if err := db.Connect(); err != nil {
        panic("test database not available: " + err.Error())
    }
    defer db.Pool.Close()

    m.Run()
}

// Seed data profile/account IDs — match what's in supabase/seed.sql
const (
    testProfileID = "00000000-0000-0000-0000-000000000002"
    testAccountID = "00000000-0000-0000-0000-000000000001"
)

func TestHealthEndpoint(t *testing.T) {
    req := httptest.NewRequest("GET", "/v1/health", nil)
    w := httptest.NewRecorder()

    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        w.Write([]byte(`{"status":"ok"}`))
    })
    handler.ServeHTTP(w, req)

    if w.Code != http.StatusOK {
        t.Errorf("expected status 200, got %d", w.Code)
    }

    var body map[string]string
    json.Unmarshal(w.Body.Bytes(), &body)
    if body["status"] != "ok" {
        t.Errorf("expected status 'ok', got '%s'", body["status"])
    }
}

func TestUpNextEndpointReturnsItems(t *testing.T) {
    req := httptest.NewRequest("GET", "/v1/feed/up-next?profile_id="+testProfileID, nil)
    w := httptest.NewRecorder()

    feed.GetUpNext(w, req)

    if w.Code != http.StatusOK {
        t.Fatalf("expected 200, got %d. Body: %s", w.Code, w.Body.String())
    }

    var response feed.FeedResponse
    if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
        t.Fatalf("response is not valid JSON: %v", err)
    }

    if response.Feed != "up_next" {
        t.Errorf("expected feed='up_next', got '%s'", response.Feed)
    }

    // Seed data has in-progress watch state entries
    if response.Count == 0 {
        t.Error("expected at least 1 item in Up Next, got 0")
    }
}

func TestWatchNowExcludesCompletedContent(t *testing.T) {
    req := httptest.NewRequest("GET",
        "/v1/feed/watch-now?profile_id="+testProfileID+"&account_id="+testAccountID,
        nil)
    w := httptest.NewRecorder()

    feed.GetWatchNow(w, req)

    var response feed.FeedResponse
    json.Unmarshal(w.Body.Bytes(), &response)

    // Verify no completed content appears
    for _, item := range response.Items {
        if item.ContentID == "cs_dune2" {
            t.Error("completed content 'Dune: Part Two' should not appear in Watch Now feed")
        }
    }
}
```

Run the integration tests (requires Supabase running):

```bash
supabase start
go test ./internal/... -v -run TestUpNext
```

---

## 6.4 Playwright Setup

Playwright is already installed in this project — it's in `package.json` under `devDependencies` as `@playwright/test`. The config file `playwright.config.ts` already exists at the project root.

### What's Already Configured

Open `playwright.config.ts` and verify these settings are correct:

```typescript
import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: "./tests",          // tests live in the /tests directory
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL: "http://localhost:3001",   // port 3001 — see package.json
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3001",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
```

**Why port 3001?** `package.json` runs Next.js on 3001 (`"dev": "next dev -p 3001"`) to avoid conflicting with other services that commonly use 3000.

### What Already Exists

`tests/provider-linking.spec.ts` already exists and tests the full OAuth linking/unlinking flow on the `/providers` page. This file is a good reference for how to write tests in this project. The pattern it uses — `clearState()` before each test and `linkProvider()` as a reusable helper — is how you keep tests isolated from each other.

Read through it to understand the test structure before writing new tests.

---

## 6.5 Write E2E Tests for the Dashboard and Feeds

The existing tests cover the provider linking UI. Now add tests for the Dashboard, Up Next, and API behavior.

Create `tests/dashboard.spec.ts`:

```typescript
import { test, expect } from "@playwright/test"

// Helper: wait for the API to respond (the page fetches on mount)
async function waitForData(page: import("@playwright/test").Page) {
    await page.waitForLoadState("networkidle")
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

test.describe("Dashboard", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/")
        await waitForData(page)
    })

    test("shows API connected status", async ({ page }) => {
        // app/page.tsx renders: "API connected" when health check passes
        await expect(page.locator("text=API connected")).toBeVisible({ timeout: 10_000 })
    })

    test("shows all four stat cards", async ({ page }) => {
        await expect(page.locator("text=In Progress")).toBeVisible()
        await expect(page.locator("text=Available Now")).toBeVisible()
        await expect(page.locator("text=Live Sports")).toBeVisible()
        await expect(page.locator("text=Providers")).toBeVisible()
    })

    test("navigation section headers are visible", async ({ page }) => {
        await expect(page.locator("text=Continue Watching")).toBeVisible()
        await expect(page.locator("text=Sports Live")).toBeVisible()
    })

    test("See all links are present", async ({ page }) => {
        await expect(page.locator("a[href='/up-next']")).toBeVisible()
        await expect(page.locator("a[href='/sports']")).toBeVisible()
    })
})

// ── Up Next Page ──────────────────────────────────────────────────────────────

test.describe("Up Next Page", () => {
    test.beforeEach(async ({ page }) => {
        await page.goto("/up-next")
        await waitForData(page)
    })

    test("shows page heading", async ({ page }) => {
        await expect(page.locator("h1")).toHaveText("Continue Watching")
    })

    test("shows at least one in-progress item from seed data", async ({ page }) => {
        // Wait for API data to load — the page starts with a "Loading..." state
        await expect(page.locator("text=Loading...")).not.toBeVisible({ timeout: 8_000 })

        // Seed data has in-progress content — at least one card should appear
        await expect(page.locator("[data-testid='up-next-card']").first()).toBeVisible()
    })

    test("each card shows a Resume button", async ({ page }) => {
        await expect(page.locator("text=Loading...")).not.toBeVisible({ timeout: 8_000 })

        const resumeButton = page.locator("text=▶ Resume").first()
        await expect(resumeButton).toBeVisible()
    })

    test("Resume button links to a provider deeplink", async ({ page }) => {
        await expect(page.locator("text=Loading...")).not.toBeVisible({ timeout: 8_000 })

        const resumeButton = page.locator("a:has-text('▶ Resume')").first()
        const href = await resumeButton.getAttribute("href")
        // href should be a real URL, not "#"
        expect(href).not.toBe("#")
        expect(href).toBeTruthy()
    })
})
```

---

## 6.6 Add Test IDs to Components

Playwright selects elements using locators. The most reliable locator is `data-testid` — a custom attribute that exists only for testing. When you redesign the styles, the test IDs stay the same.

Update `app/up-next/page.tsx` — add `data-testid` to the `UpNextCard` outer div:

```tsx
// Find this div in the UpNextCard function:
<div className="bg-gray-900 rounded-xl p-5 flex items-center gap-5">

// Add data-testid:
<div
  data-testid="up-next-card"
  className="bg-gray-900 rounded-xl p-5 flex items-center gap-5"
>
```

Without `data-testid`, the test `page.locator("[data-testid='up-next-card']")` will find 0 elements and fail. This is the correct fix — add the attribute, don't change the test selector.

Similarly, add test IDs to other components you want to test:

```tsx
// In app/page.tsx StatCard, add data-testid to the outer div:
<div data-testid={`stat-card-${label.toLowerCase().replace(" ", "-")}`} className="bg-gray-900 ...">

// This makes stat cards selectable as:
// page.getByTestId("stat-card-in-progress")
// page.getByTestId("stat-card-available-now")
```

---

## 6.7 Run the Tests

Make sure everything is running first:

```bash
# Terminal 1: Supabase (for the Go backend)
supabase start

# Terminal 2: Go backend
go run ./cmd/server

# Terminal 3: Run Playwright tests
# (playwright starts Next.js automatically via webServer config)
```

Run tests using the npm scripts defined in `package.json`:

```bash
# Run all E2E tests (headless — no browser window)
npm test

# Run with an interactive UI — pick tests, see browser, replay traces
npm run test:ui

# Open the HTML report after a run
npm run test:report

# Run a specific test file
npx playwright test tests/dashboard.spec.ts

# Run a specific test by name
npx playwright test --grep "shows API connected"

# Watch the browser during a test (headed mode)
npx playwright test --headed

# Debug mode — pause at each step
npx playwright test --debug
```

When tests pass:

```
Running 8 tests using 1 worker

  ✓  provider-linking.spec.ts › Provider Dashboard › displays all 8 provider cards (1.2s)
  ✓  provider-linking.spec.ts › OAuth Linking Flow › successfully links a provider (2.8s)
  ✓  dashboard.spec.ts › Dashboard › shows API connected status (1.4s)
  ✓  dashboard.spec.ts › Up Next Page › shows at least one in-progress item (2.1s)
  ...

8 passed (18.3s)
```

---

## 6.8 API Tests (Using Playwright for the Backend)

Playwright can also test your API directly — no browser needed. Use the `request` fixture instead of `page`.

Create `tests/api.spec.ts`:

```typescript
import { test, expect } from "@playwright/test"

// The Go backend runs on 8080 — separate from the Next.js frontend on 3001
const API_BASE = "http://localhost:8080"

// Seed data IDs — match what's in supabase/seed.sql
const PROFILE_ID = "00000000-0000-0000-0000-000000000002"
const ACCOUNT_ID = "00000000-0000-0000-0000-000000000001"

test.describe("Channel Stream API", () => {
    test("health endpoint returns 200", async ({ request }) => {
        // `request` is Playwright's HTTP client — like fetch but with assertions
        const response = await request.get(`${API_BASE}/v1/health`)
        expect(response.status()).toBe(200)

        const body = await response.json()
        expect(body.status).toBe("ok")
    })

    test("up-next returns correct response shape", async ({ request }) => {
        const response = await request.get(
            `${API_BASE}/v1/feed/up-next?profile_id=${PROFILE_ID}`
        )
        expect(response.status()).toBe(200)

        const body = await response.json()
        expect(body.feed).toBe("up_next")
        expect(Array.isArray(body.items)).toBe(true)
        expect(typeof body.count).toBe("number")

        // Verify item shape when results exist
        if (body.items.length > 0) {
            const item = body.items[0]
            expect(item).toHaveProperty("content_id")
            expect(item).toHaveProperty("title")
            expect(item).toHaveProperty("provider")
            expect(item).toHaveProperty("progress_pct")
            expect(item.reason).toBe("continue_watching")
        }
    })

    test("watch-now excludes completed content", async ({ request }) => {
        const response = await request.get(
            `${API_BASE}/v1/feed/watch-now?profile_id=${PROFILE_ID}&account_id=${ACCOUNT_ID}`
        )
        expect(response.status()).toBe(200)

        const body = await response.json()
        expect(body.feed).toBe("watch_now")

        // Seed data marks cs_dune2 as completed — it must NOT appear
        const dune = body.items.find((i: { content_id: string }) => i.content_id === "cs_dune2")
        expect(dune).toBeUndefined()
    })

    test("sports live returns events for followed teams", async ({ request }) => {
        const response = await request.get(
            `${API_BASE}/v1/sports/live?profile_id=${PROFILE_ID}`
        )
        expect(response.status()).toBe(200)

        const body = await response.json()
        expect(body.feed).toBe("sports_live")
        expect(Array.isArray(body.events)).toBe(true)
    })

    test("caching headers are present on feed endpoints", async ({ request }) => {
        // The Go backend must have Redis running for HIT to work.
        // First request = cache MISS (fresh DB query)
        const miss = await request.get(`${API_BASE}/v1/feed/up-next?profile_id=${PROFILE_ID}`)
        expect(miss.headers()["x-cache"]).toBe("MISS")

        // Second request — same key, same profile = cache HIT
        const hit = await request.get(`${API_BASE}/v1/feed/up-next?profile_id=${PROFILE_ID}`)
        expect(hit.headers()["x-cache"]).toBe("HIT")
    })
})
```

**Important**: The API tests hit `localhost:8080` (the Go server) directly, not the Next.js app at `localhost:3001`. You must have `go run ./cmd/server` running for these tests to pass. The `webServer` in `playwright.config.ts` only starts Next.js automatically — start Go manually.

---

## 6.9 The Testing Pyramid

Think of tests in three layers — lower layers are faster and cheaper:

```
        /\
       /  \        E2E Tests (Playwright browser)
      /    \       - Slow (seconds per test)
     /  E2E \      - Fragile (UI selectors can break)
    /────────\     - High confidence: proves the whole system works
   /          \
  / Integration \  Integration Tests (real DB, real cache)
 /              \ - Medium speed (milliseconds)
/────────────────\ - Catches real query and caching bugs
\                /
 \   Unit Tests  /  Unit Tests (pure functions)
  \            /  - Instant (microseconds)
   \──────────/   - Very stable, easy to write
```

For Channel Stream:
- **~60% Unit tests**: Scoring functions, data transformation, validation, key naming helpers
- **~30% Integration tests**: API handlers, database queries, cache HIT/MISS behavior
- **~10% E2E tests**: Critical user flows (load dashboard, view Up Next, click Resume, link a provider)

### Two Separate Test Concerns

The existing `provider-linking.spec.ts` tests the **frontend in isolation** — the OAuth modal, link/unlink UI, coverage percentage, profile management, and `localStorage` persistence. It deliberately does not hit the Go backend. This is intentional: the frontend's linking flow stores state in the browser (no real OAuth in development).

The new `api.spec.ts` tests the **Go backend in isolation** — the real HTTP handlers, real SQL queries, real Redis caching. No browser involved.

Both layers are necessary. A bug in the SQL query won't be caught by `provider-linking.spec.ts`. A bug in the React modal won't be caught by `api.spec.ts`.

---

## 6.10 How to Instruct This Build Without Code Assist

If you're rebuilding Module 6 from scratch and want to describe it to an AI assistant or another developer:

### For Go unit tests:

> "Create `internal/feed/feed_test.go` in `package feed_test`. Import `github.com/jwolf13/channel-stream/internal/feed`. Write three test functions: one that verifies `FeedResponse.Feed` holds the correct string value, one that verifies `FeedItem` fields are not empty when set, and a table-driven test that checks progress percentage validation (0–100 is valid, outside that range is not). Use the standard `testing` package, no external test libraries."

### For Go integration tests:

> "Create `internal/feed/integration_test.go` in `package feed_test`. It needs a `TestMain` that calls `db.Connect()` and panics if unavailable. Define constants `testProfileID = '00000000-0000-0000-0000-000000000002'` and `testAccountID = '00000000-0000-0000-0000-000000000001'`. Write tests using `httptest.NewRequest` and `httptest.NewRecorder` that call `feed.GetUpNext` and `feed.GetWatchNow` directly. Verify the response status is 200, the JSON is valid, the `feed` field matches the expected value, and that completed content (content_id 'cs_dune2') does not appear in the Watch Now response."

### For Playwright E2E tests:

> "Create `tests/dashboard.spec.ts`. The base URL is `http://localhost:3001` (already set in `playwright.config.ts`). Write tests for the dashboard page at `/`: verify 'API connected' text appears, verify the four stat card labels are visible ('In Progress', 'Available Now', 'Live Sports', 'Providers'). Write tests for `/up-next`: verify the heading is 'Continue Watching', verify that after the loading state clears a card with `data-testid='up-next-card'` appears, and verify a Resume link has a non-empty href. Note: `app/up-next/page.tsx` must have `data-testid='up-next-card'` added to the outer div of `UpNextCard` first."

### For API tests:

> "Create `tests/api.spec.ts`. Use `request` fixture (not `page`) to test the Go backend at `http://localhost:8080`. Use profile ID `00000000-0000-0000-0000-000000000002` and account ID `00000000-0000-0000-0000-000000000001`. Test: health returns 200 with `{status:'ok'}`, up-next returns `{feed:'up_next', items:[], count:0}` shape, watch-now does not include `content_id='cs_dune2'`, sports-live returns `{feed:'sports_live', events:[]}` shape, and the second request to up-next has `x-cache: HIT` header. Note the Go server must be started manually — `playwright.config.ts` only auto-starts Next.js."

---

## 6.11 Checkpoint

- [ ] `go test ./...` runs and all Go tests pass
- [ ] `data-testid="up-next-card"` added to `UpNextCard` in `app/up-next/page.tsx`
- [ ] `npm test` runs and all tests pass (both existing `provider-linking.spec.ts` and new specs)
- [ ] `npm run test:ui` opens the interactive test runner
- [ ] `tests/api.spec.ts` verifies cache `HIT`/`MISS` headers correctly
- [ ] You can explain the difference between `tests/provider-linking.spec.ts` (frontend only) and `tests/api.spec.ts` (backend only)
- [ ] You understand why unit, integration, and E2E tests each exist — they catch different bugs
- [ ] Code is committed to GitHub

---

**Next**: [Module 7 → Deployment & DevOps](./MODULE_07_DEPLOYMENT_DEVOPS.md)
