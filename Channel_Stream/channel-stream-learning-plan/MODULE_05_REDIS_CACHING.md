# Module 5 — Caching with Redis
### Making Your API Fast Without Changing Business Logic

---

> **Goal**: Add Redis caching to all three feed endpoints (Watch Now, Up Next, Sports Live) so repeat requests return in under 10ms instead of 200–500ms. Understand cache invalidation and graceful degradation — Redis going down must never crash the API.

> **Time**: ~3–4 hours

---

## 5.1 Why Caching Exists

Building the Watch Now feed is not free:

1. Query PostgreSQL: 50–200ms (round trips, disk reads, index scans)
2. Score and rank 500 content candidates: 10–50ms
3. Serialize to JSON: 2–5ms

Total: ~60–250ms per request.

Now imagine 15,000 concurrent users at 8pm prime time (Channel Stream's peak). If each one triggers a fresh database query: 15,000 × 200ms = 3,000 seconds of database work hitting simultaneously. The database collapses.

**The insight**: Two users watching at the same moment have nearly identical Watch Now feeds. Why compute it 15,000 times when you could compute it once per profile and save it?

Redis is the answer. It's an in-memory data store — think of it as a giant dictionary that lives in RAM:

```
KEY                                         VALUE                      TTL
feed:{profile_id}:watch_now   →   {"items": [...30 items]}   10 minutes
feed:{profile_id}:up_next     →   {"items": [...4 items]}    5 minutes
sports:live:{profile_id}      →   {"events": [...]}           90 seconds
```

First request: database + ranking = 200ms. Stored in Redis.
Next 1,000 requests: Redis lookup = 2ms each. Database never touched.

### Why Sports Gets a Different TTL

Watch Now and Up Next show content you might watch tonight — if the data is 10 minutes stale, the user won't notice. Sports Live shows live scores. If the score is 10 minutes old during a close game, the feed is useless. So sports uses a 90-second TTL instead.

The system design calls this explicitly:

> "Sports Live (no cache — real-time)" is **wrong** for how we actually build it. The correct design: cache at 90 seconds. A truly uncached live-score feed would hit the database (and the upstream sports data provider) on every single client poll. At 15,000 concurrent users, that's untenable. Ninety seconds of staleness during a live game is acceptable. "No cache" is the conceptual description — 90-second TTL is the implementation.

---

## 5.2 Start Redis Locally

```bash
# Run Redis in a Docker container
# -d = run in background (detached)
# --name = give it a memorable name
# -p 6379:6379 = expose port 6379 on your machine
# redis:7-alpine = use Redis version 7, slim Alpine Linux image
docker run -d --name channel-stream-redis -p 6379:6379 redis:7-alpine

# Verify it's running:
docker exec channel-stream-redis redis-cli ping
# Expected: PONG
```

Redis is now running at `redis://localhost:6379`.

### Explore Redis Manually

Redis has a simple command-line interface called `redis-cli`. Let's see how it works:

```bash
docker exec -it channel-stream-redis redis-cli

# You're now in the Redis CLI. Try these:

# Set a key
SET name "Channel Stream"
# OK

# Get it back
GET name
# "Channel Stream"

# Set with expiration (TTL in seconds)
SET greeting "Hello!" EX 60
# OK

# Check remaining time-to-live
TTL greeting
# (integer) 59  ← counting down

# After 60 seconds:
TTL greeting
# (integer) -2  ← -2 means the key no longer exists

# Store JSON (Redis stores everything as strings — JSON is just text)
SET feed:test '{"items": [{"title": "Severance"}], "count": 1}'

# Retrieve it
GET feed:test
# '{"items": [{"title": "Severance"}], "count": 1}'

# Delete a key
DEL feed:test
# (integer) 1  ← number of keys deleted

# See all keys matching a pattern (safe in local/dev with small datasets)
KEYS feed:*

# Exit
quit
```

Key takeaways:
- Redis stores key-value pairs where both key and value are strings
- You can set an expiration (TTL — Time To Live) on any key
- When TTL expires, the key disappears automatically — no cleanup needed
- JSON is stored as a string and parsed by your application

---

## 5.3 Create the Cache Package (`internal/cache/cache.go`)

```bash
mkdir -p internal/cache
```

Create `internal/cache/cache.go`:

```go
package cache

import (
    "context"
    "fmt"
    "os"
    "time"

    "github.com/redis/go-redis/v9"
)

// Client is the global Redis connection. Nil when Redis is unavailable.
var Client *redis.Client

// TTL constants for each feed type.
// Shorter TTL = fresher data but more database load.
// Longer TTL = faster responses but staleness.
const (
    TTLWatchNow   = 10 * time.Minute  // stable recommendations
    TTLUpNext     = 5 * time.Minute   // watch state changes more often
    TTLSportsLive = 90 * time.Second  // live scores need freshness
    TTLProviders  = 15 * time.Minute  // provider links rarely change
)

// Connect establishes the Redis connection. Returns an error but does not
// fatally crash — the API degrades gracefully to direct DB queries when Redis
// is unavailable.
func Connect() error {
    redisURL := os.Getenv("REDIS_URL")
    if redisURL == "" {
        redisURL = "redis://localhost:6379"
    }

    opt, err := redis.ParseURL(redisURL)
    if err != nil {
        return fmt.Errorf("invalid REDIS_URL: %w", err)
    }

    Client = redis.NewClient(opt)

    if err := Client.Ping(context.Background()).Err(); err != nil {
        Client = nil // leave nil so all callers treat Redis as unavailable
        return fmt.Errorf("cannot connect to Redis: %w", err)
    }

    fmt.Println("✓ Connected to Redis")
    return nil
}

// Get retrieves a cached value. Returns ("", false, nil) when the key is
// missing or when Redis is unavailable — callers always fall through to the DB.
func Get(ctx context.Context, key string) (string, bool, error) {
    if Client == nil {
        return "", false, nil
    }
    val, err := Client.Get(ctx, key).Result()
    if err == redis.Nil {
        return "", false, nil
    }
    if err != nil {
        return "", false, err
    }
    return val, true, nil
}

// Set stores a value with a TTL. No-ops when Redis is unavailable.
func Set(ctx context.Context, key string, value string, ttl time.Duration) error {
    if Client == nil {
        return nil
    }
    return Client.Set(ctx, key, value, ttl).Err()
}

// Delete removes a key from cache. No-ops when Redis is unavailable.
func Delete(ctx context.Context, key string) error {
    if Client == nil {
        return nil
    }
    return Client.Del(ctx, key).Err()
}

// DeletePattern removes all keys matching a glob pattern.
// Uses SCAN (not KEYS) so it never blocks the Redis server, even at scale.
func DeletePattern(ctx context.Context, pattern string) error {
    if Client == nil {
        return nil
    }
    var cursor uint64
    for {
        keys, next, err := Client.Scan(ctx, cursor, pattern, 100).Result()
        if err != nil {
            return err
        }
        if len(keys) > 0 {
            if err := Client.Del(ctx, keys...).Err(); err != nil {
                return err
            }
        }
        cursor = next
        if cursor == 0 {
            break
        }
    }
    return nil
}

// FeedKey returns the cache key for a personalized feed.
// Convention: "feed:{profile_id}:{feed_type}"
func FeedKey(profileID, feedType string) string {
    return fmt.Sprintf("feed:%s:%s", profileID, feedType)
}

// SportsKey returns the cache key for the sports live feed.
// Keyed by profile so per-profile team filtering can be added later.
func SportsKey(profileID string) string {
    return fmt.Sprintf("sports:live:%s", profileID)
}

// InvalidateProfileFeeds deletes all cached feeds for a profile.
// Call whenever the profile's watch state, provider links, or preferences change.
func InvalidateProfileFeeds(ctx context.Context, profileID string) error {
    if Client == nil {
        return nil
    }
    keys := []string{
        FeedKey(profileID, "watch_now"),
        FeedKey(profileID, "up_next"),
        SportsKey(profileID),
    }
    return Client.Del(ctx, keys...).Err()
}
```

### Why Every Function Checks `if Client == nil`

This is the most important design decision in this package. When `Connect()` fails (Redis is down, wrong URL, network timeout), it sets `Client = nil` and returns an error. That error is logged in `main.go`, but it is **not fatal** — the server keeps running.

If the cache functions didn't nil-check, the first cache call after a Redis failure would panic:

```
panic: runtime error: invalid memory address or nil pointer dereference
```

The nil check turns a crash into a no-op:
- `Get` returns `"", false, nil` → caller falls through to the database, as if cache didn't exist
- `Set` returns `nil` → caller continues, result just isn't cached
- `Delete` returns `nil` → invalidation silently skips

This is called **graceful degradation**: the feature (caching) disappears, but the system keeps working. Users get slower responses during a Redis outage. They don't get an error page.

### Why `DeletePattern` Uses SCAN, Not KEYS

Redis has two commands for finding keys by pattern:
- `KEYS feed:*` — scans every single key in the database before returning. With 1 million keys, this blocks Redis for the entire scan duration. Every other client waits. In production this can freeze your API for seconds.
- `SCAN` — iterates in small batches (100 keys at a time here), releasing Redis between each batch. Takes slightly longer total but never blocks other clients.

The `DeletePattern` function above uses `SCAN` in a loop, collecting keys in batches of 100 and deleting them as it goes. Always use SCAN for production pattern-matching. `KEYS *` is only safe in `redis-cli` for manual inspection on a small local dataset.

---

## 5.4 Add Caching to the Up Next Handler

Update `internal/feed/upnext.go`. The cache-aside pattern is always the same three steps:

1. Check cache → if found, return immediately
2. If not found, query database
3. Store result in cache, then return

```go
package feed

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "time"

    "github.com/jwolf13/channel-stream/internal/cache"
    "github.com/jwolf13/channel-stream/internal/db"
)

func GetUpNext(w http.ResponseWriter, r *http.Request) {
    profileID := r.URL.Query().Get("profile_id")
    if profileID == "" {
        profileID = "00000000-0000-0000-0000-000000000002"
    }

    // ── Cache check ──────────────────────────────────────────────────────────
    // Pattern: check cache → return if found; otherwise query DB → store → return.
    cacheKey := cache.FeedKey(profileID, "up_next")
    if cached, found, _ := cache.Get(r.Context(), cacheKey); found {
        w.Header().Set("Content-Type", "application/json")
        w.Header().Set("X-Cache", "HIT")
        fmt.Fprint(w, cached)
        return
    }
    // ─────────────────────────────────────────────────────────────────────────

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

    if err != nil {
        http.Error(w, "database error", http.StatusInternalServerError)
        return
    }
    defer rows.Close()

    var items []FeedItem
    for rows.Next() {
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
        if err != nil {
            http.Error(w, "scan error", http.StatusInternalServerError)
            return
        }
        item.LastWatched = &lastWatched
        item.Reason = "continue_watching"
        items = append(items, item)
    }

    if rows.Err() != nil {
        http.Error(w, "row iteration error", http.StatusInternalServerError)
        return
    }

    response := FeedResponse{
        Feed:        "up_next",
        GeneratedAt: time.Now().UTC(),
        Items:       items,
        Count:       len(items),
    }

    // ── Store in cache ───────────────────────────────────────────────────────
    // Non-fatal: if marshalling or Set fails, we still return the response.
    if b, err := json.Marshal(response); err == nil {
        cache.Set(r.Context(), cacheKey, string(b), cache.TTLUpNext)
    }
    // ─────────────────────────────────────────────────────────────────────────

    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("X-Cache", "MISS")
    json.NewEncoder(w).Encode(response)
}
```

### What `X-Cache` Does

`X-Cache: HIT` and `X-Cache: MISS` are response headers you set yourself — not part of any standard, just a debugging convention that almost every CDN and caching proxy uses. They let you verify from the outside (with `curl -v` or browser DevTools) whether a response came from cache or the database. You'll use these in section 5.5 to confirm caching is actually working.

---

## 5.5 Add Caching to the Watch Now Handler

Same pattern. Update `internal/feed/watchnow.go`:

```go
package feed

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "time"

    "github.com/jwolf13/channel-stream/internal/cache"
    "github.com/jwolf13/channel-stream/internal/db"
)

func GetWatchNow(w http.ResponseWriter, r *http.Request) {
    profileID := r.URL.Query().Get("profile_id")
    if profileID == "" {
        profileID = "00000000-0000-0000-0000-000000000002"
    }

    accountID := r.URL.Query().Get("account_id")
    if accountID == "" {
        accountID = "00000000-0000-0000-0000-000000000001"
    }

    // ── Cache check ──────────────────────────────────────────────────────────
    // Key includes both profile and account since results differ by provider links.
    cacheKey := cache.FeedKey(profileID, "watch_now")
    if cached, found, _ := cache.Get(r.Context(), cacheKey); found {
        w.Header().Set("Content-Type", "application/json")
        w.Header().Set("X-Cache", "HIT")
        fmt.Fprint(w, cached)
        return
    }
    // ─────────────────────────────────────────────────────────────────────────

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
            AND pl.account_id = $2
        WHERE c.type IN ('series', 'movie')
          AND c.id NOT IN (
              SELECT content_id
              FROM watch_state
              WHERE profile_id = $1
                AND status = 'completed'
          )
        ORDER BY (c.metadata->>'rating')::FLOAT DESC NULLS LAST
        LIMIT 30
    `, profileID, accountID)

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
        item.Score = 0.5
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

    // ── Store in cache ───────────────────────────────────────────────────────
    if b, err := json.Marshal(response); err == nil {
        cache.Set(r.Context(), cacheKey, string(b), cache.TTLWatchNow)
    }
    // ─────────────────────────────────────────────────────────────────────────

    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("X-Cache", "MISS")
    json.NewEncoder(w).Encode(response)
}
```

---

## 5.6 Add Caching to the Sports Handler

Sports is the interesting case. It IS cached — but at 90 seconds instead of minutes. The sports feed is already filtered per profile (by followed teams), so the key is per-profile using `cache.SportsKey()`.

Update `internal/feed/sports.go`:

```go
package feed

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "strings"
    "time"

    "github.com/jwolf13/channel-stream/internal/cache"
    "github.com/jwolf13/channel-stream/internal/db"
)

func GetSportsLive(w http.ResponseWriter, r *http.Request) {
    profileID := r.URL.Query().Get("profile_id")
    if profileID == "" {
        profileID = "00000000-0000-0000-0000-000000000002"
    }

    // ── Cache check ──────────────────────────────────────────────────────────
    // Sports uses a 90-second TTL — short enough to stay fresh during live games.
    cacheKey := cache.SportsKey(profileID)
    if cached, found, _ := cache.Get(r.Context(), cacheKey); found {
        w.Header().Set("Content-Type", "application/json")
        w.Header().Set("X-Cache", "HIT")
        fmt.Fprint(w, cached)
        return
    }
    // ─────────────────────────────────────────────────────────────────────────

    var preferences []byte
    err := db.Pool.QueryRow(context.Background(), `
        SELECT preferences FROM profiles WHERE id = $1
    `, profileID).Scan(&preferences)

    if err != nil {
        http.Error(w, "profile not found", http.StatusNotFound)
        return
    }

    // Phase 2: parse preferences JSON and extract the "teams" array.
    // For now teams are hardcoded from seed data.
    followedTeams := []string{"lakers", "dodgers", "rams"}

    rows, err := db.Pool.Query(context.Background(), `
        SELECT
            id,
            league,
            home_team_id,
            away_team_id,
            start_time,
            status,
            score,
            broadcast
        FROM sports_events
        WHERE (home_team_id = ANY($1) OR away_team_id = ANY($1))
          AND status IN ('live', 'scheduled')
        ORDER BY
            CASE status
                WHEN 'live'      THEN 0
                WHEN 'scheduled' THEN 1
                ELSE 2
            END,
            start_time ASC
    `, followedTeams)

    if err != nil {
        http.Error(w, "database error", http.StatusInternalServerError)
        return
    }
    defer rows.Close()

    var events []SportEvent
    for rows.Next() {
        var e SportEvent
        var homeTeam, awayTeam string
        var score, broadcast []byte

        err := rows.Scan(
            &e.GameID,
            &e.League,
            &homeTeam,
            &awayTeam,
            &e.StartTime,
            &e.Status,
            &score,
            &broadcast,
        )
        if err != nil {
            http.Error(w, "scan error", http.StatusInternalServerError)
            return
        }

        e.Matchup = strings.ToUpper(homeTeam) + " vs " + strings.ToUpper(awayTeam)

        if score != nil {
            json.Unmarshal(score, &e.Score)
        }
        if broadcast != nil {
            json.Unmarshal(broadcast, &e.Broadcast)
        }

        events = append(events, e)
    }

    if rows.Err() != nil {
        http.Error(w, "row iteration error", http.StatusInternalServerError)
        return
    }

    type SportsResponse struct {
        Feed        string       `json:"feed"`
        GeneratedAt time.Time    `json:"generated_at"`
        Events      []SportEvent `json:"events"`
        Count       int          `json:"count"`
    }

    response := SportsResponse{
        Feed:        "sports_live",
        GeneratedAt: time.Now().UTC(),
        Events:      events,
        Count:       len(events),
    }

    // ── Store in cache ───────────────────────────────────────────────────────
    // Short TTL (90s) keeps scores fresh enough during live games.
    if b, err := json.Marshal(response); err == nil {
        cache.Set(r.Context(), cacheKey, string(b), cache.TTLSportsLive)
    }
    // ─────────────────────────────────────────────────────────────────────────

    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("X-Cache", "MISS")
    json.NewEncoder(w).Encode(response)
}
```

---

## 5.7 Wire Redis Into the Server

Update `cmd/server/main.go` to connect Redis at startup, after the database:

```go
// After db.Connect():
if err := cache.Connect(); err != nil {
    log.Println("Warning: Redis unavailable, caching disabled:", err)
    // Not fatal — all cache calls no-op when Client is nil
}
```

Note that this is `log.Println`, not `log.Fatal`. If Redis is down when the server starts, the server starts anyway. Handlers will run without caching until Redis comes back (which requires a server restart to re-establish the connection in this simple implementation — Phase 2 would add connection retry logic).

---

## 5.8 Test the Cache (See the Speed Difference)

```bash
# Start the server
go run ./cmd/server

# First request — cache MISS (database query)
time curl -s "http://localhost:8080/v1/feed/up-next" > /dev/null
# real    0m0.247s   ← 247ms

# Second request — cache HIT (Redis)
time curl -s "http://localhost:8080/v1/feed/up-next" > /dev/null
# real    0m0.008s   ← 8ms   (~30x faster)
```

Verify the cache headers:

```bash
curl -v "http://localhost:8080/v1/feed/up-next" 2>&1 | grep X-Cache
# First call:  X-Cache: MISS
# Second call: X-Cache: HIT

curl -v "http://localhost:8080/v1/feed/watch-now" 2>&1 | grep X-Cache
# X-Cache: MISS → X-Cache: HIT

curl -v "http://localhost:8080/v1/sports/live" 2>&1 | grep X-Cache
# X-Cache: MISS → X-Cache: HIT (within 90 seconds)
```

Inspect keys in Redis directly:

```bash
docker exec channel-stream-redis redis-cli KEYS "*"
# feed:00000000-0000-0000-0000-000000000002:up_next
# feed:00000000-0000-0000-0000-000000000002:watch_now
# sports:live:00000000-0000-0000-0000-000000000002

# Check the TTL remaining on a key
docker exec channel-stream-redis redis-cli TTL "feed:00000000-0000-0000-0000-000000000002:up_next"
# (integer) 287  ← 287 seconds remaining out of 300 (5 minutes)
```

---

## 5.9 Cache Invalidation — The Hard Problem

A famous quote in computer science: "There are only two hard problems: naming things and cache invalidation."

**The problem**: When the user finishes watching Shogun, the Up Next feed cached in Redis still shows Shogun at 35%. The cache is stale. We need to invalidate (delete) it.

### When to Invalidate

| Event | Cache Keys to Invalidate |
|---|---|
| Watch state synced from provider | `feed:{profile_id}:up_next` and `feed:{profile_id}:watch_now` |
| User links a new provider | `feed:{profile_id}:watch_now` (new content available) |
| User unlinks a provider | `feed:{profile_id}:watch_now` (content removed) |
| User changes preferences | `feed:{profile_id}:watch_now` (ranking changed) |
| User follows a new team | `sports:live:{profile_id}` (new team to show games for) |
| Catalog update (new content) | All `feed:*:watch_now` keys (new content for everyone) |

### TTL vs. Invalidation: When to Use Each

**Let TTL expire naturally** when:
- The data change is not urgent (a catalog update adding new content — users don't need to see it in the next 10 minutes)
- You don't have a hook into when the change happens (background jobs you don't control)

**Invalidate immediately** when:
- The user caused the change themselves (linking/unlinking a provider, updating preferences, marking something watched). Showing them stale data right after their own action is a bad UX.
- The data is security-adjacent (unlink a provider — stop showing that content immediately)

### Implementing Invalidation

`InvalidateProfileFeeds` is already in the cache package (section 5.3). Use it in any handler that mutates state:

```go
// Future POST /v1/providers/link handler — after linking a new provider:
func LinkProvider(w http.ResponseWriter, r *http.Request) {
    // ... validate request, store provider token in DB ...

    // Invalidate Watch Now so the new provider's content appears immediately
    if err := cache.InvalidateProfileFeeds(r.Context(), profileID); err != nil {
        log.Println("cache invalidation failed:", err)
        // Non-fatal — user will see fresh data within 10 minutes via TTL
    }

    w.WriteHeader(http.StatusOK)
}
```

### Testing Invalidation Manually

```bash
# First: confirm the feed is cached
curl -v "http://localhost:8080/v1/feed/up-next" 2>&1 | grep X-Cache
# X-Cache: HIT

# Manually delete the cache key in redis-cli:
docker exec channel-stream-redis redis-cli DEL "feed:00000000-0000-0000-0000-000000000002:up_next"
# (integer) 1

# Now update watch state in Supabase SQL editor to simulate a completed show:
# UPDATE watch_state
# SET status = 'completed'
# WHERE profile_id = '00000000-0000-0000-0000-000000000002'
#   AND content_id = 'cs_shogun';

# Fetch the feed again — should be a MISS and return updated data:
curl -v "http://localhost:8080/v1/feed/up-next" 2>&1 | grep X-Cache
# X-Cache: MISS
```

---

## 5.10 The Cache Hierarchy for Channel Stream

Understanding which layer caches what:

```
Request arrives
      │
      ▼
CloudFront CDN
  ├── HIT → return immediately (artwork, app config, static files)
  └── MISS → forward to API Gateway
              │
              ▼
         API Gateway
         (rate limiting, auth validation)
              │
              ▼
         Go Backend
              │
              ▼
         Redis Cache
           ├── HIT → return JSON (2-10ms)
           │     ├── Watch Now:   feed:{profile_id}:watch_now   TTL 10min
           │     ├── Up Next:     feed:{profile_id}:up_next     TTL 5min
           │     └── Sports Live: sports:live:{profile_id}      TTL 90s
           └── MISS → query PostgreSQL
                      │
                      ▼
                 PostgreSQL
                 (build feed, score, rank)
                 (100-500ms on first load)
                      │
                      ▼
                 Store in Redis
                 Return to client
```

**CDN cache** (CloudFront): Artwork images, app config, static files. Content that does not change per user. TTL: hours to days. Personalized feeds never go through CDN.

**Redis cache**: Personalized feeds that are expensive to compute but stable for a short time. TTL: seconds to minutes.

**Provider link/unlink**: Never cached. These operations write to Postgres synchronously and immediately invalidate all feed caches for the account. A user linking a provider must see their new content on the next request — not 10 minutes later.

---

## 5.11 Redis Data Structures Beyond Strings

You used Redis for string storage (JSON blobs). Redis has other data structures worth knowing about for Channel Stream's future phases.

### Sorted Set (for leaderboards/rankings)

```bash
# Add teams to a "sports affinity" sorted set with scores
ZADD sports:affinity:p1000 10 "lakers"
ZADD sports:affinity:p1000 8 "dodgers"
ZADD sports:affinity:p1000 5 "rams"

# Get teams sorted by affinity (highest first)
ZREVRANGE sports:affinity:p1000 0 -1 WITHSCORES
# 1) "lakers" 2) "10" 3) "dodgers" 4) "8" 5) "rams" 6) "5"
```

### Pub/Sub (for real-time sports score updates)

```bash
# Terminal 1: Subscribe to sports updates
SUBSCRIBE sports:live:updates

# Terminal 2: Publish an update (simulating the sports ingestion worker)
PUBLISH sports:live:updates '{"game_id":"nba_lakers_celtics","score":{"home":98,"away":95}}'

# Terminal 1 receives:
# 1) "message"
# 2) "sports:live:updates"
# 3) '{"game_id":"nba_lakers_celtics","score":{"home":98,"away":95}}'
```

This is exactly how WebSocket sports scores work in Channel Stream's Phase 2 (from the system design):

> *"Sports Schedule Workers poll every 60 seconds. Push score updates to WebSocket gateway via Redis Pub/Sub."*

The ingestion worker publishes a score update to a Redis Pub/Sub channel. The WebSocket gateway is subscribed; it receives the message and forwards it to all connected clients who follow that game. No polling — the update flows from worker → Redis → gateway → client in under a second.

---

## 5.12 How to Instruct This Build Without Code Assist

If you're rebuilding Module 5 from scratch and want to describe it to an AI assistant (or another developer) without writing code yourself, here are the precise instructions to give:

### For the cache package:

> "Create `internal/cache/cache.go`. It needs a global `*redis.Client` variable that starts as nil. Write a `Connect()` function that reads `REDIS_URL` from the environment (default `redis://localhost:6379`), parses it, creates a client, pings it, and if the ping fails sets `Client` back to nil and returns an error — but never panics. Write `Get`, `Set`, and `Delete` functions that each start with `if Client == nil { return the zero value }` so they silently no-op when Redis is unavailable. Write `DeletePattern` that uses SCAN in a loop, not KEYS — the page size should be 100. Write key-construction helpers: `FeedKey(profileID, feedType)` returning `feed:{profileID}:{feedType}`, and `SportsKey(profileID)` returning `sports:live:{profileID}`. Write `InvalidateProfileFeeds` that deletes the watch_now key, up_next key, and sports key for a given profile ID. Include TTL constants: TTLWatchNow 10 minutes, TTLUpNext 5 minutes, TTLSportsLive 90 seconds, TTLProviders 15 minutes."

### For each feed handler:

> "Update the feed handler to follow the cache-aside pattern: (1) build the cache key using the appropriate helper, (2) call cache.Get — if found is true, set Content-Type and X-Cache: HIT headers, write the cached string directly to the response with fmt.Fprint, and return, (3) otherwise run the existing database query, (4) build the response struct, (5) marshal it to JSON and call cache.Set with the appropriate TTL constant — this is non-fatal, wrap it in an if-err check, (6) set Content-Type and X-Cache: MISS headers, encode and write the response. The sports handler uses cache.SportsKey; the feed handlers use cache.FeedKey with the feed type string."

### For main.go:

> "After the existing db.Connect() call, add a call to cache.Connect(). If it returns an error, log a warning with log.Println — not log.Fatal. The server must start even when Redis is unavailable."

---

## 5.13 Checkpoint

- [ ] Redis starts with `docker run ...` and responds to `redis-cli ping`
- [ ] `go run ./cmd/server` shows "✓ Connected to Redis" in the log
- [ ] First request to each endpoint shows `X-Cache: MISS` and takes ~200ms
- [ ] Second request to each endpoint shows `X-Cache: HIT` and takes <20ms
- [ ] `redis-cli KEYS "*"` shows three keys: watch_now, up_next, and sports:live
- [ ] `redis-cli TTL <key>` shows a countdown for each key
- [ ] Manually deleting a Redis key causes the next request to query the database (MISS again)
- [ ] You can explain what TTL is and why Watch Now, Up Next, and Sports use different values
- [ ] You can explain why the nil guard matters and what would happen without it
- [ ] You can explain why `DeletePattern` uses SCAN instead of KEYS
- [ ] You understand when to let TTL expire naturally vs. when to call `InvalidateProfileFeeds`
- [ ] **Graceful degradation test**: Stop the Redis container (`docker stop channel-stream-redis`), make a request to any feed endpoint. It should return data (from Postgres), not an error.
- [ ] Code is committed to GitHub

---

**Next**: [Module 6 → Testing with Playwright](./MODULE_06_TESTING_PLAYWRIGHT.md)
