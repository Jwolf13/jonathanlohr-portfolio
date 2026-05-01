# Module 3 — Backend: The Go API Server
### Building the Engine That Powers Every Feed

---

> **Goal**: Build a production-quality Go API server with real endpoint handlers, proper error handling, structured logging, and clean code organization. By the end, you will have a running backend that all four feeds call correctly.

> **Time**: ~6–8 hours

---

## 3.1 Why Go? (And What Makes It Different)

Go (also called "Golang") was created at Google in 2009. It's the backend language for Channel Stream for four reasons:

1. **Fast**: Go compiles to a single binary. No runtime, no virtual machine. It starts in milliseconds.
2. **Simple**: Go has roughly 25 keywords. JavaScript has 64. Python has 35. Fewer keywords = less to learn.
3. **Concurrent**: Go was built to handle many things at once (serving hundreds of requests simultaneously) without the complexity that plagues other languages.
4. **Readable**: Go code written by a beginner looks almost identical to code written by an expert. This matters when you come back to code six months later.

### Key Differences from JavaScript/Python

| Concept | JavaScript/Python | Go |
|---|---|---|
| **Types** | Dynamic — `x = 5` then `x = "hello"` is fine | Static — `x := 5` means x is always an int |
| **Compilation** | Interpreted at runtime | Compiled to binary before running |
| **Error handling** | Exceptions (try/catch) | Returned values — functions return `(result, error)` |
| **Null values** | `null` or `undefined` | No null — use zero values (`0`, `""`, `false`) |
| **Classes** | `class User {}` | Structs + methods — `type User struct {}` |

### The Error Handling Pattern (IMPORTANT)

In Go, functions that can fail return TWO values: the result AND an error.

```go
// JavaScript style (exceptions):
try {
    let result = doSomething();
    console.log(result);
} catch (err) {
    console.error(err);
}

// Go style (return values):
result, err := doSomething()
if err != nil {          // "if there was an error"
    log.Fatal(err)       // handle it immediately
}
fmt.Println(result)      // now we know result is valid
```

You will see `if err != nil` hundreds of times in Go code. This is intentional — Go forces you to think about errors at every step instead of letting them bubble up invisibly.
test
---

## 3.2 Project Structure (How Go Code Is Organized)

Go has strong conventions about project structure. Channel Stream follows the standard layout:

```
channel-stream/
├── cmd/
│   └── server/
│       └── main.go          ← Entry point. The program starts here.
├── internal/
│   ├── feed/
│   │   ├── feed.go          ← Shared types: FeedItem, SportsResponse, WatchOption, ...
│   │   ├── watchnow.go      ← Watch Now feed logic
│   │   ├── upnext.go        ← Up Next feed logic
│   │   └── sports.go        ← Sports Live + Schedule logic
│   ├── ingestion/
│   │   ├── broadcasts.go    ← Broadcast mapping cache (ESPN network → streaming app)
│   │   └── sports.go        ← ESPN ingestion worker (background goroutine)
│   ├── provider/
│   │   └── provider.go      ← Provider linking/unlinking
│   ├── db/
│   │   └── db.go            ← Database connection setup
│   └── cache/
│       └── cache.go         ← Redis connect, Get/Set/Delete/InvalidateProfileFeeds
├── supabase/
│   ├── migrations/          ← SQL migration files
│   └── seed.sql             ← Test data
├── go.mod                   ← Go module definition (like package.json)
├── go.sum                   ← Checksums for dependencies (don't edit this)
├── .env                     ← Environment variables (not in Git)
└── .gitignore
```

### Why `internal/`?

The `internal/` folder is a Go convention: packages inside `internal/` can ONLY be used by code in the same module. This enforces that your business logic stays private — external packages can't import your internals. It's a built-in modular boundary.

### Why `cmd/`?

`cmd/` holds the entry point(s) to your application. If you had both a web server and a batch job runner, you'd have `cmd/server/main.go` and `cmd/worker/main.go`.

---

## 3.3 Initialize the Go Project

```bash
cd ~/channel-stream

# Initialize Go modules (like npm init but for Go)
go mod init github.com/jwolf13/channel-stream
# Replace YOURUSERNAME with your GitHub username

# Install the dependencies we need:
go get github.com/jackc/pgx/v5        # PostgreSQL driver — talks to Postgres
go get github.com/go-chi/chi/v5       # HTTP router — routes URLs to handlers
go get github.com/redis/go-redis/v9   # Redis client — for caching
go get github.com/joho/godotenv       # Loads .env file into environment
```

After running these, check your `go.mod` file:
```bash
cat go.mod
```

It should list all the packages you just installed. Think of `go.mod` as your `package.json` — it declares your module name and all dependencies.

---

## 3.4 Create the Folder Structure

```bash
mkdir -p cmd/server
mkdir -p internal/feed
mkdir -p internal/provider
mkdir -p internal/db
mkdir -p internal/middleware
```

---

## 3.5 Step 1 — Database Connection (`internal/db/db.go`)

The first thing the server needs is a database connection. We'll create a reusable connection pool.

Create `internal/db/db.go`:

```go
// Package db handles database connection setup.
// A "package" is Go's way of grouping related code.
package db

import (
    "context"   // for timeouts and cancellation
    "fmt"       // for formatting strings (like printf)
    "os"        // for reading environment variables

    "github.com/jackc/pgx/v5/pgxpool"  // PostgreSQL connection pool
)

// Pool is the global database connection pool.
// It's exported (capital P) so other packages can use it.
// A connection pool maintains multiple open connections to the database,
// reusing them for each request instead of opening a new one each time.
var Pool *pgxpool.Pool

// Connect establishes a connection to PostgreSQL.
// Call this once at startup. If it fails, the program should stop.
func Connect() error {
    // Read the database URL from environment variables
    // This is safer than hardcoding: postgresql://postgres:postgres@localhost:54322/postgres
    dbURL := os.Getenv("DATABASE_URL")
    if dbURL == "" {
        // Default to local Supabase if not set
        dbURL = "postgresql://postgres:postgres@localhost:54322/postgres"
    }

    // Create the connection pool
    // context.Background() means "no deadline" — wait as long as needed to connect
    pool, err := pgxpool.New(context.Background(), dbURL)
    if err != nil {
        return fmt.Errorf("cannot create connection pool: %w", err)
        // fmt.Errorf wraps the error with context ("cannot create..." tells us what we were doing)
    }

    // Test the connection by sending a "ping"
    if err := pool.Ping(context.Background()); err != nil {
        return fmt.Errorf("cannot ping database: %w", err)
    }

    Pool = pool  // store globally so all handlers can use it
    fmt.Println("✓ Connected to PostgreSQL")
    return nil   // nil means "no error"
}
```

---

## 3.6 Step 2 — Define Your Data Types (`internal/feed/feed.go`)

Before writing query logic, define what a "feed item" looks like in Go. These are called **structs**.

Create `internal/feed/feed.go`:

```go
package feed

import "time"

// FeedItem represents one piece of content in any feed.
// Think of this as the "shape" of data we return to clients.
//
// The `json:"..."` tags tell Go how to serialize this struct to JSON.
// Go field names are PascalCase (ContentID), JSON keys are snake_case (content_id).
type FeedItem struct {
    ContentID          string    `json:"content_id"`
    Title              string    `json:"title"`
    Type               string    `json:"type"`
    Provider           string    `json:"provider"`
    ProgressPct        int       `json:"progress_pct,omitempty"`   // omitempty: skip if 0
    ResumePositionSec  int       `json:"resume_position_sec,omitempty"`
    Rating             string    `json:"rating,omitempty"`
    Deeplink           string    `json:"deeplink,omitempty"`
    LastWatched        *time.Time `json:"last_watched,omitempty"` // pointer = nullable
    Score              float64   `json:"score,omitempty"`
    Reason             string    `json:"reason,omitempty"` // "continue_watching", "genre_match", etc.
}

// FeedResponse is the wrapper around a list of FeedItems.
// This is what the API actually returns.
type FeedResponse struct {
    Feed        string     `json:"feed"`          // "watch_now", "up_next", "sports_live"
    GeneratedAt time.Time  `json:"generated_at"`
    Items       []FeedItem `json:"items"`
    Count       int        `json:"count"`
}

// SportEvent represents a live or scheduled game.
type SportEvent struct {
    GameID     string      `json:"game_id"`
    League     string      `json:"league"`
    Matchup    string      `json:"matchup"`    // "lakers vs celtics"
    Status     string      `json:"status"`     // "live", "scheduled", "final"
    StartTime  time.Time   `json:"start_time"`
    Score      interface{} `json:"score,omitempty"` // interface{} = any JSON shape
    Broadcast  interface{} `json:"broadcast,omitempty"`
}

// ProviderLink represents a linked streaming service.
type ProviderLink struct {
    Provider     string     `json:"provider"`
    LinkedAt     time.Time  `json:"linked_at"`
    TokenExpires *time.Time `json:"token_expires,omitempty"`
    Status       string     `json:"status"` // "valid", "expired", "expiring_soon"
}
```

---

## 3.7 Step 3 — Up Next Handler (`internal/feed/upnext.go`)

Create `internal/feed/upnext.go`:

```go
package feed

import (
    "context"
    "encoding/json"
    "net/http"
    "time"

    "github.com/jwolf13/channel-stream/internal/db"
)

// GetUpNext handles GET /v1/feed/up-next
// It returns all content the profile is currently watching, sorted by most recent.
func GetUpNext(w http.ResponseWriter, r *http.Request) {
    // 1. Get profile_id from the URL query string
    //    URL: /v1/feed/up-next?profile_id=00000000-0000-0000-0000-000000000002
    profileID := r.URL.Query().Get("profile_id")
    if profileID == "" {
        // If no profile_id provided, use our test profile
        profileID = "00000000-0000-0000-0000-000000000001"
    }

    // 2. Query the database
    rows, err := db.Pool.Query(context.Background(), `
        SELECT
            c.id,
            c.title,
            c.type,
            ws.provider,
            ws.progress_pct,
            ws.position_sec,
            ws.last_watched,
            COALESCE(ca.deeplink_tpl, '') AS deeplink
        FROM watch_state ws
        JOIN content c ON c.id = ws.content_id
        LEFT JOIN content_availability ca
            ON ca.content_id = c.id
            AND ca.provider = ws.provider
        WHERE ws.profile_id = $1
          AND ws.status = 'in_progress'
        ORDER BY ws.last_watched DESC
        LIMIT 20
    `, profileID)
    // $1 is a "parameter placeholder" — pgx replaces it with profileID safely.
    // NEVER concatenate strings directly into SQL: WHERE profile_id = '"+profileID+"'
    // That creates a SQL injection vulnerability — a hacker can destroy your database.

    if err != nil {
        // Something went wrong with the query itself
        http.Error(w, "database error", http.StatusInternalServerError)
        return  // stop here
    }
    defer rows.Close()  // always close rows when done — frees the database connection

    // 3. Scan each row into FeedItem structs
    var items []FeedItem
    for rows.Next() {  // rows.Next() advances to the next row, returns false when done
        var item FeedItem
        var lastWatched time.Time

        err := rows.Scan(
            &item.ContentID,
            &item.Title,
            &item.Type,
            &item.Provider,
            &item.ProgressPct,
            &item.ResumePositionSec,
            &lastWatched,
            &item.Deeplink,
        )
        // The & means "address of" — rows.Scan writes into these variables
        if err != nil {
            http.Error(w, "scan error", http.StatusInternalServerError)
            return
        }

        item.LastWatched = &lastWatched  // convert to pointer
        item.Reason = "continue_watching"
        items = append(items, item)
    }

    // 4. Check if the loop itself had an error
    if rows.Err() != nil {
        http.Error(w, "row iteration error", http.StatusInternalServerError)
        return
    }

    // 5. Build the response
    response := FeedResponse{
        Feed:        "up_next",
        GeneratedAt: time.Now().UTC(),
        Items:       items,
        Count:       len(items),
    }

    // 6. Return as JSON
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}
```

---

## 3.8 Step 4 — Watch Now Handler (`internal/feed/watchnow.go`)

Create `internal/feed/watchnow.go`:

```go
package feed

import (
    "context"
    "encoding/json"
    "net/http"
    "time"

    "github.com/jwolf13/channel-stream/internal/db"
)

// GetWatchNow handles GET /v1/feed/watch-now
// Returns personalized content from the user's linked providers,
// excluding completed content.
func GetWatchNow(w http.ResponseWriter, r *http.Request) {
    profileID := r.URL.Query().Get("profile_id")
    if profileID == "" {
        profileID = "00000000-0000-0000-0000-000000000001"
    }

    // In a real system, we'd look up the account_id from the profile_id.
    // For now, we use our test account.
    accountID := r.URL.Query().Get("account_id")
    if accountID == "" {
        accountID = "00000000-0000-0000-0000-000000000001"
    }

    rows, err := db.Pool.Query(context.Background(), `
        SELECT
            c.id,
            c.title,
            c.type,
            ca.provider,
            COALESCE(c.metadata->>'rating', '0') AS rating,
            COALESCE(ca.deeplink_tpl, '') AS deeplink
        FROM content c
        JOIN content_availability ca ON ca.content_id = c.id
        JOIN provider_links pl
            ON pl.provider = ca.provider
            AND pl.account_id = $2  -- only content from the user's linked providers
        WHERE c.type IN ('series', 'movie')
          AND c.id NOT IN (
              -- exclude content the profile has already completed
              SELECT content_id
              FROM watch_state
              WHERE profile_id = $1
                AND status = 'completed'
          )
        ORDER BY (c.metadata->>'rating')::FLOAT DESC NULLS LAST
        LIMIT 30
    `, profileID, accountID)
    // Note: $1 = profileID, $2 = accountID
    // Parameters are numbered in order of appearance

    if err != nil {
        http.Error(w, "database error", http.StatusInternalServerError)
        return
    }
    defer rows.Close()

    var items []FeedItem
    for rows.Next() {
        var item FeedItem
        err := rows.Scan(
            &item.ContentID,
            &item.Title,
            &item.Type,
            &item.Provider,
            &item.Rating,
            &item.Deeplink,
        )
        if err != nil {
            http.Error(w, "scan error", http.StatusInternalServerError)
            return
        }
        item.Score = 0.5  // placeholder — Phase 2 will compute real scores
        item.Reason = "available_now"
        items = append(items, item)
    }

    if rows.Err() != nil {
        http.Error(w, "row iteration error", http.StatusInternalServerError)
        return
    }

    response := FeedResponse{
        Feed:        "watch_now",
        GeneratedAt: time.Now().UTC(),
        Items:       items,
        Count:       len(items),
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}
```

---

## 3.9 Step 5 — Sports Handler (`internal/feed/sports.go`)

The sports handler is the most interesting piece because it combines:
1. A profile preferences lookup (what teams does this user follow?)
2. A filtered game query (games for those teams in the time window)
3. An in-memory broadcast lookup (ESPN → Disney+, CBS → Paramount+)
4. Redis caching at 90-second TTL

The full file is at `internal/feed/sports.go`. Key functions to understand:

**`GetSportsLive`** — the HTTP handler. Cache check → preferences lookup → `querySportsEvents` → cache set → respond.

**`profilePreferences`** — reads `followed_teams` and `followed_leagues` from the profile's JSONB preferences column:
```go
func profilePreferences(ctx context.Context, profileID string) (teams []string, leagues []string) {
    var prefJSON []byte
    db.Pool.QueryRow(ctx, `SELECT COALESCE(preferences, '{}') FROM profiles WHERE id = $1`,
        profileID).Scan(&prefJSON)

    var prefs struct {
        FollowedTeams   []string `json:"followed_teams"`
        FollowedLeagues []string `json:"followed_leagues"`
    }
    json.Unmarshal(prefJSON, &prefs)
    return prefs.FollowedTeams, prefs.FollowedLeagues
}
```

**`querySportsEvents`** — the core DB query. Two parameters control the time window: `startDayOffset` and `endDayOffset`. Live feed uses `(0, 1)` = today; schedule uses `(0, 7)` = next 7 days.

The SQL passes teams and leagues as arrays. If the arrays are empty (user has no preferences), all games pass through — the "cold start" behavior:
```sql
AND (
    ($3::text[] IS NULL OR cardinality($3::text[]) = 0
     OR home_team_abbr = ANY($3) OR away_team_abbr = ANY($3))
    AND
    ($4::text[] IS NULL OR cardinality($4::text[]) = 0
     OR league = ANY($4))
)
```

**`buildWatchOn`** — converts `["ESPN","ABC"]` into a sorted list of streaming app objects using `ingestion.LookupMapping()` (in-memory, zero DB calls):
```go
func buildWatchOn(broadcastJSON []byte) []WatchOption {
    var networks []string
    json.Unmarshal(broadcastJSON, &networks)
    // ... calls ingestion.LookupMapping(network) for each
    // ... deduplicates, sorts streaming-first
}
```

There are also two new types in `internal/feed/feed.go`:
```go
type WatchOption struct {
    Network       string `json:"network"`
    App           string `json:"app,omitempty"`      // streaming app slug
    AppDisplay    string `json:"app_display"`
    RequiresCable bool   `json:"requires_cable"`
}

type SportEventEnriched struct {
    GameID, Sport, League string
    HomeTeam, AwayTeam    TeamInfo
    StartTime             time.Time
    Status, StatusDetail  string
    Score                 *GameScore
    Venue                 string
    WatchOn               []WatchOption
}
```

---

## 3.10 Step 6 — Provider Handler (`internal/provider/provider.go`)

Create `internal/provider/provider.go`:

```go
package provider

import (
    "context"
    "encoding/json"
    "net/http"
    "time"

    "github.com/jwolf13/channel-stream/internal/db"
    "github.com/jwolf13/channel-stream/internal/feed"
)

// GetLinkedProviders handles GET /v1/providers/linked
func GetLinkedProviders(w http.ResponseWriter, r *http.Request) {
    accountID := r.URL.Query().Get("account_id")
    if accountID == "" {
        accountID = "00000000-0000-0000-0000-000000000001"
    }

    rows, err := db.Pool.Query(context.Background(), `
        SELECT
            provider,
            linked_at,
            token_expires,
            CASE
                WHEN token_expires IS NULL THEN 'never_expires'
                WHEN token_expires < now() THEN 'expired'
                WHEN token_expires < now() + interval '7 days' THEN 'expiring_soon'
                ELSE 'valid'
            END AS status
        FROM provider_links
        WHERE account_id = $1
        ORDER BY provider
    `, accountID)

    if err != nil {
        http.Error(w, "database error", http.StatusInternalServerError)
        return
    }
    defer rows.Close()

    var links []feed.ProviderLink
    for rows.Next() {
        var link feed.ProviderLink
        var tokenExpires *time.Time  // pointer = nullable

        err := rows.Scan(
            &link.Provider,
            &link.LinkedAt,
            &tokenExpires,
            &link.Status,
        )
        if err != nil {
            http.Error(w, "scan error", http.StatusInternalServerError)
            return
        }
        link.TokenExpires = tokenExpires
        links = append(links, link)
    }

    type ProvidersResponse struct {
        AccountID string             `json:"account_id"`
        Providers []feed.ProviderLink `json:"providers"`
        Count     int                `json:"count"`
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(ProvidersResponse{
        AccountID: accountID,
        Providers: links,
        Count:     len(links),
    })
}
```

---

## 3.11 Step 7 — The Entry Point (`cmd/server/main.go`)

This is where everything connects. The key difference from a simple server: we create a cancellable context and start the ingestion worker as a background goroutine before starting the HTTP server.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "github.com/joho/godotenv"

    "github.com/jwolf13/channel-stream/internal/cache"
    "github.com/jwolf13/channel-stream/internal/db"
    "github.com/jwolf13/channel-stream/internal/feed"
    "github.com/jwolf13/channel-stream/internal/ingestion"
    "github.com/jwolf13/channel-stream/internal/provider"
)

func main() {
    if err := godotenv.Load(); err != nil {
        log.Println("No .env file found — using system environment variables")
    }

    // signal.NotifyContext cancels ctx when Ctrl-C or SIGTERM arrives.
    // Every long-running goroutine watches ctx.Done() and stops cleanly.
    ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer cancel()

    if err := db.Connect(); err != nil {
        log.Fatal("Failed to connect to database:", err)
    }
    defer db.Pool.Close()

    if err := cache.Connect(); err != nil {
        log.Println("Warning: Redis unavailable, caching disabled:", err)
        // Not fatal — cache functions are no-ops when Client is nil
    }

    // Start the ESPN ingestion worker in the background.
    // It seeds broadcast mappings, loads them into memory, fetches 3 days of
    // games immediately, then polls ESPN every 60s (live) / 10min (schedule).
    go ingestion.StartSportsWorker(ctx)

    r := chi.NewRouter()
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.RealIP)
    r.Use(corsMiddleware)

    r.Get("/v1/health", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        fmt.Fprintln(w, `{"status":"ok","version":"1.0.0"}`)
    })

    r.Get("/v1/feed/up-next",      feed.GetUpNext)
    r.Get("/v1/feed/watch-now",    feed.GetWatchNow)
    r.Get("/v1/sports/live",       feed.GetSportsLive)
    r.Get("/v1/sports/schedule",   feed.GetSportsSchedule)
    r.Get("/v1/providers/linked",  provider.GetLinkedProviders)

    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }

    fmt.Printf("Channel Stream API running at http://localhost:%s\n", port)
    log.Fatal(http.ListenAndServe(":"+port, r))
}
```

**Why `signal.NotifyContext`?**

Without it, Ctrl-C kills the process immediately and the ingestion worker is terminated mid-write. With it, the ctx is cancelled first, `StartSportsWorker` detects `ctx.Done()` and exits its loop cleanly, then the process exits. No partial writes, no orphaned goroutines.

---

## 3.11b Step 8 — The ESPN Ingestion Worker (`internal/ingestion/sports.go`)

This is the most important new piece of Channel Stream. Instead of hand-entering game data, a background goroutine automatically fetches live data from ESPN every 60 seconds.

### How it works

```
StartSportsWorker(ctx)
    ├── SeedBroadcastMappings(ctx)   — upserts ~35 network→app rows into DB
    ├── LoadMappings(ctx)            — reads all rows into in-memory map
    ├── fetchAll(ctx, 0)             — fetches today's games (all 8 sports), immediately
    ├── fetchAll(ctx, 1)             — fetches tomorrow
    ├── fetchAll(ctx, 2)             — fetches day after
    └── loop:
        ├── liveTicker (60s) → fetchAll(ctx, 0)       — keeps live scores fresh
        └── scheduleTicker (10min) → fetchAll(ctx, 1) + fetchAll(ctx, 2)
```

### ESPN API URL pattern

```
https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={YYYYMMDD}&limit=100
```

Examples:
- `sports/basketball/nba/scoreboard?dates=20260428`
- `sports/football/nfl/scoreboard?dates=20260428`
- `sports/baseball/mlb/scoreboard?dates=20260428`

No API key required. Returns JSON with games, teams, scores, broadcast networks, venue.

### Upsert — why not INSERT?

`INSERT` fails if the row already exists. `INSERT … ON CONFLICT DO UPDATE` ("upsert") handles both cases: new game = insert, existing game = update the live-changing fields.

```sql
INSERT INTO sports_events (id, ...) VALUES (...)
ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status,
    score  = EXCLUDED.score,
    ...
```

`EXCLUDED.status` means "the value we tried to insert" — it's PostgreSQL's syntax for the incoming row in an upsert.

### Broadcast mapping cache

`broadcasts.go` defines an in-memory map: `mappingCache = map[string]BroadcastMapping{}`. At startup, `LoadMappings` fills it from the DB. `LookupMapping("ESPN")` reads from it without touching the DB — this runs for every game in every response, so it needs to be fast.

```go
// protected by a sync.RWMutex — many goroutines can read simultaneously
func LookupMapping(network string) (BroadcastMapping, bool) {
    mappingMu.RLock()
    defer mappingMu.RUnlock()
    m, ok := mappingCache[network]
    return m, ok
}
```

---

## 3.12 Run and Test the Server

### Start It

```bash
# Make sure Supabase is running first:
supabase start

# Start the Go server:
go run ./cmd/server
```

Expected output:
```
No .env file found — using system environment variables
✓ Connected to PostgreSQL
Sports ingestion worker starting…
✓ Seeded 35 broadcast mappings
✓ Loaded 35 broadcast mappings into cache
Channel Stream API running at http://localhost:8080
```

Within a few seconds you'll also see ESPN fetch logs:
```
ingestion NBA (20260428): ...
ingestion NFL (20260428): ...
```

### Test Every Endpoint

Open a new **PowerShell** terminal and run these:

```powershell
# Health check
Invoke-RestMethod http://localhost:8080/v1/health

# Up Next — returns in-progress shows
Invoke-RestMethod http://localhost:8080/v1/feed/up-next

# Watch Now — returns content from linked providers
Invoke-RestMethod http://localhost:8080/v1/feed/watch-now

# Sports Live — returns live/upcoming games for followed teams
# Uses default profile: 00000000-0000-0000-0000-000000000002 (follows LAL, LAD, LAR)
Invoke-RestMethod "http://localhost:8080/v1/sports/live?profile_id=00000000-0000-0000-0000-000000000002"

# Sports Schedule — 7-day view
Invoke-RestMethod "http://localhost:8080/v1/sports/schedule?profile_id=00000000-0000-0000-0000-000000000002"

# Linked Providers — should return 4 providers
Invoke-RestMethod http://localhost:8080/v1/providers/linked
```

The sports endpoints will show seed data immediately and real ESPN data within ~30 seconds (after the first ingestion cycle completes).

`Invoke-RestMethod` automatically parses and pretty-prints JSON on Windows — no extra tools needed.

> **Note for Mac/Linux users:** Replace `Invoke-RestMethod <url>` with `curl <url> | python3 -m json.tool`

### Test in Thunder Client (VS Code)

1. Click the Thunder Client icon in VS Code sidebar (lightning bolt)
2. Click "New Request"
3. Enter: `GET` `http://localhost:8080/v1/feed/up-next`
4. Click Send
5. See the formatted JSON response in the Response panel

This is exactly how you'll demo the API to stakeholders — far more visual than the terminal.

---

## 3.13 See Your Data Now (Before the Frontend Exists)

Module 4 builds the real UI. But you don't have to wait — here are three ways to see your live data right now.

### Option 1 — Browser Preview Page (Most Visual)

A ready-made HTML page in your project root fetches all four feeds and renders them as cards.

**Steps:**
1. Start the Go server in one terminal:
   ```bash
   go run ./cmd/server
   ```
2. Open `preview.html` directly in Chrome or Edge (File → Open, or drag the file into the browser)

You'll see all four feeds rendered as dark-theme cards — Up Next with progress bars, Watch Now with ratings, Sports Live with live/scheduled badges, and Providers with status.

If the API isn't running, the page shows a red status indicator and tells you to start the server.

---

### Option 2 — Raw JSON in the Browser

Every GET endpoint works directly in a browser address bar. Open Chrome or Edge and paste any of these:

```
http://localhost:8080/v1/health
http://localhost:8080/v1/feed/up-next
http://localhost:8080/v1/feed/watch-now
http://localhost:8080/v1/sports/live
http://localhost:8080/v1/providers/linked
```

Chrome and Edge display JSON in a readable, collapsible format. No extra tools needed.

> **Tip**: Install the [JSON Formatter](https://chromewebstore.google.com/detail/json-formatter/bcjindcccaagfpapjjmafapmmgkkhgoa) Chrome extension for colour-coded, collapsible JSON.

---

### Option 3 — Supabase Studio (See the Raw Database)

Open **http://localhost:54323** in your browser while `supabase start` is running.

- **Table Editor** (left sidebar) → click any table to browse rows visually
- **SQL Editor** → paste any of the four queries from Module 2 and run them
- **API** tab → auto-generated REST docs for every table

This is the difference between seeing the API's output and seeing the database directly. Both are useful.

---

## 3.15 Understanding What You Built

Let's trace one request through the code:

```
Browser/Roku sends: GET /v1/feed/up-next?profile_id=p1000...

     ↓
chi router receives the request
Sees "/v1/feed/up-next" → calls feed.GetUpNext(w, r)

     ↓
GetUpNext reads profile_id from URL query params
"profile_id" = "p1000..."

     ↓
db.Pool.Query() sends SQL to PostgreSQL:
"Give me all in-progress content for this profile, 
 joined with content details and deeplinks, 
 sorted by last watched"

     ↓
PostgreSQL runs the query, returns 4 rows

     ↓
rows.Next() loop scans each row into a FeedItem struct:
{ ContentID: "cs_severance_s3e02", Title: "Severance S3E2", ... }

     ↓
Build FeedResponse:
{ feed: "up_next", generated_at: "...", items: [4 items], count: 4 }

     ↓
json.NewEncoder(w).Encode(response)
Converts the struct to JSON text and writes it to the HTTP response

     ↓
Browser receives:
{
  "feed": "up_next",
  "generated_at": "2026-04-27T22:15:00Z",
  "items": [
    { "content_id": "cs_severance_s3e02", "title": "Severance S3E2", ... },
    ...
  ],
  "count": 4
}
```

---

## 3.16 Common Errors and How to Fix Them

### "cannot use X (variable of type Y) as type Z"
Go is strictly typed. If a function expects a `string` and you pass an `int`, it won't compile. Solution: convert the type or check what the function actually needs.

### "imported and not used"
Go requires every imported package to be used. If you import something but don't use it, the code won't compile. Solution: remove the unused import.

### "pgx: cannot scan into *string: oid 114 (json)"
You're trying to scan a JSONB column into a plain string. Use `[]byte` instead, then unmarshal. See the sports handler for an example.

### "connection refused"
The database or Redis isn't running. Run `supabase start` before starting the server.

### "port already in use"
Something is already running on port 8080. Find and kill it: `lsof -i :8080` then `kill -9 <PID>`.

---

## 3.17 Checkpoint

- [ ] `go build ./...` succeeds with no errors
- [ ] `go run ./cmd/server` starts and shows "Sports ingestion worker starting…"
- [ ] All 6 endpoints return JSON responses (including `/v1/sports/schedule`)
- [ ] `/v1/sports/live` returns events with a `watch_on` array containing streaming app info
- [ ] After ~30 seconds, sports events in the DB have real ESPN data (check Supabase Studio)
- [ ] You can explain why we use `INSERT … ON CONFLICT DO UPDATE` instead of plain `INSERT`
- [ ] You can explain the difference between `liveTicker` and `scheduleTicker` in the worker
- [ ] You can explain what `LookupMapping` does and why it uses an in-memory map instead of a DB query
- [ ] You can explain the error handling pattern (`if err != nil`)
- [ ] You've committed your code to GitHub

---

**Next**: [Module 4 → Frontend — Next.js Dashboard](./MODULE_04_FRONTEND_NEXTJS.md)
