# Local Testing Guide
### Every tool you have — how to use it, right now

---

> **Read this before Module 6.** Module 6 teaches you to *write* Playwright tests. This guide teaches you to *run* what already exists and verify everything is working at every layer.

---

## What You're Testing (5 Layers)

| Layer | Tool | What it checks |
|---|---|---|
| Go compiles | `go build` | No syntax or type errors in backend code |
| Backend API | curl / PowerShell / Thunder Client | Endpoints return correct JSON |
| Database | Supabase Studio | Rows are correct; queries work |
| Frontend | Browser | Page loads, data displays |
| E2E (automated) | Playwright | Full user flows pass in a real browser |

Work through them in order. A problem at layer 1 breaks everything below it.

---

## Step 1 — Verify the Go Backend Compiles

```bash
go build ./...
```

**Pass:** no output, exits 0.
**Fail:** an error with file + line number. Fix that line, re-run.

This is the fastest possible check. Run it every time you edit a `.go` file before doing anything else.

---

## Step 2 — Start the Services

You need two terminals running at the same time.

**Terminal 1 — Database:**
```bash
supabase start
```
Wait for: `Studio URL: http://localhost:54323`

If you changed the schema or seed data since last run:
```bash
supabase db reset
```

**Terminal 2 — Go backend:**
```bash
go run ./cmd/server
```
Wait for:
```
Sports ingestion worker starting…
✓ Seeded 35 broadcast mappings
✓ Loaded 35 broadcast mappings into cache
Channel Stream API running at http://localhost:8080
```

Leave both running. Open a third terminal for the tests below.

---

## Step 3 — Hit Every API Endpoint Manually

Choose one method: **curl** (any terminal) or **PowerShell** (Windows) or **Thunder Client** (VS Code).

### Option A — curl (bash / Git Bash / WSL)

```bash
# Health — should return {"status":"ok","version":"1.0.0"}
curl http://localhost:8080/v1/health

# Sports live — should return events with watch_on arrays
curl "http://localhost:8080/v1/sports/live?profile_id=00000000-0000-0000-0000-000000000002"

# Sports schedule — 7-day window
curl "http://localhost:8080/v1/sports/schedule?profile_id=00000000-0000-0000-0000-000000000002"

# Up Next
curl http://localhost:8080/v1/feed/up-next

# Linked Providers
curl http://localhost:8080/v1/providers/linked
```

Pipe to pretty-print:
```bash
curl http://localhost:8080/v1/health | python3 -m json.tool
```

### Option B — PowerShell

```powershell
Invoke-RestMethod http://localhost:8080/v1/health
Invoke-RestMethod "http://localhost:8080/v1/sports/live?profile_id=00000000-0000-0000-0000-000000000002"
Invoke-RestMethod http://localhost:8080/v1/feed/up-next
Invoke-RestMethod http://localhost:8080/v1/providers/linked
```

PowerShell automatically parses and pretty-prints JSON — no extra tools needed.

### Option C — Thunder Client (VS Code)

1. Click the lightning bolt icon in the left sidebar
2. Click **New Request**
3. Set method to `GET`, paste any URL above
4. Click **Send**
5. See formatted JSON in the Response panel

**Look for** on every sports response:
- `"events"` array is present (may be empty if no games today — that's fine)
- Each event has `"watch_on"` — a list of streaming options
- Events with `"status": "live"` have `"score"` populated
- `X-Cache: MISS` on the first request, `X-Cache: HIT` on the second (within 90s)

---

## Step 4 — Check the Database in Supabase Studio

Open **http://localhost:54323** in a browser.

### Table Editor

Left sidebar → **Table Editor** → click a table to browse rows.

What to verify:

| Table | What to look for |
|---|---|
| `profiles` | One row — `id` = `00000000-...-000002`, `preferences` has `followed_teams` |
| `sports_events` | Rows being written (refresh after ~30s — the worker is populating these) |
| `broadcast_mappings` | 35 rows — ESPN, CBS, TNT, FOX, etc. |
| `provider_links` | 4 rows — netflix, hulu, disney_plus, apple_tv_plus |

### SQL Editor

Left sidebar → **SQL Editor** — paste and run any query:

```sql
-- Check that the sports feed query works
SELECT id, sport, league, home_team_abbr, away_team_abbr, status, broadcast
FROM sports_events
WHERE start_time >= now() - interval '3 hours'
  AND start_time <= now() + interval '24 hours'
  AND status != 'final'
ORDER BY start_time ASC
LIMIT 10;
```

```sql
-- Check broadcast mappings loaded correctly
SELECT network, streaming_app, app_display, requires_cable
FROM broadcast_mappings
ORDER BY sort_order;
```

```sql
-- Verify Jon's profile preferences
SELECT id, name, preferences
FROM profiles
WHERE id = '00000000-0000-0000-0000-000000000002';
```

---

## Step 5 — Check the Frontend Loads

**Terminal 3:**
```bash
npm run dev
```

Open **http://localhost:3001** in a browser.

What to verify:
- Page loads without a blank white screen or console errors
- Open DevTools (F12) → Console tab — no red errors
- Open DevTools → Network tab — filter by `XHR` — you should see requests to `localhost:8080`

If the page is blank or shows an error, the issue is in the Next.js code, not the Go backend.

---

## Step 6 — Run the Playwright E2E Tests

This runs the existing test suite in `tests/provider-linking.spec.ts` — 30+ tests that automatically open a browser and click through real UI flows.

**Make sure the frontend is NOT already running** — Playwright starts its own server.

### Headless (fast, no browser window)
```bash
npm test
```

Output looks like:
```
  ✓ displays all 8 provider cards (1.2s)
  ✓ all providers start as unlinked (0.8s)
  ✓ successfully links a provider and shows Linked status (2.1s)
  ...
30 passed (45s)
```

### With browser UI visible (watch it run)
```bash
npm run test:ui
```

Opens the Playwright UI — you can see each test, click to replay it step by step, see screenshots of every action.

### Run a single test file
```bash
npx playwright test tests/provider-linking.spec.ts
```

### Run tests matching a name
```bash
npx playwright test --grep "links a provider"
```

### View the HTML report after a run
```bash
npm run test:report
```

Opens a browser with a full report: which tests passed/failed, how long each took, screenshots on failure.

---

## Quick Checklist Before You Commit Code

```
[ ] go build ./...                           passes with no output
[ ] go run ./cmd/server                      shows ESPN worker starting log
[ ] curl /v1/sports/live                     returns events with watch_on
[ ] curl /v1/health                          returns {"status":"ok"}
[ ] Supabase Studio: sports_events           has rows (after ~30s)
[ ] Supabase Studio: broadcast_mappings      has 35 rows
[ ] http://localhost:3001                    loads without console errors
[ ] npm test                                 all Playwright tests pass
```

If you can check every box, the app is working at every layer.

---

## Common Failures and Fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `go build` error | Syntax error in Go file | Read the error line number, fix it |
| `connection refused` on port 8080 | Go server not running | Run `go run ./cmd/server` |
| `connection refused` on port 54322 | Supabase not running | Run `supabase start` |
| Sports events empty after 60s | ESPN API unreachable | Check internet connection; ESPN is a public API |
| `X-Cache` always MISS | Redis not running | OK — API still works, just no caching |
| Playwright: `page.getByTestId("...")` not found | Frontend element missing | The UI component doesn't have the expected `data-testid` yet |
| Playwright: `net::ERR_CONNECTION_REFUSED` | Port 3001 not listening | Stop any other Next.js process; Playwright starts its own |

---

**Next**: [Module 6 → Writing Your Own Playwright Tests](./MODULE_06_TESTING_PLAYWRIGHT.md)
