# Module 8 — ESPN Data Ingestion

## What this module covers

Your Go backend contains a background worker that continuously pulls live sports
data from ESPN's public scoreboard API and writes it into your PostgreSQL
database. This module explains how that pipeline works, what every piece does,
and how to verify it is running correctly in production.

---

## The big picture

```
ESPN Scoreboard API  (no API key required)
        │
        │  HTTP GET every 60 s (live scores)
        │  HTTP GET every 10 min (upcoming schedule)
        ↓
  ingestion worker  (goroutine inside your Go server)
        │
        │  INSERT … ON CONFLICT DO UPDATE
        ↓
  sports_events table  (PostgreSQL on RDS)
        │
        │  SELECT queries
        ↓
  /v1/sports/live        →  live scores for the frontend
  /v1/sports/schedule    →  upcoming games for the schedule page
```

Everything runs inside the same ECS container as your HTTP server. There is no
separate process, no Lambda, no cron job. The worker starts automatically when
the server starts and stops when the server stops.

---

## Key concepts

### What is a goroutine?

A goroutine is Go's lightweight thread. When `main.go` calls
`go ingestion.StartSportsWorker(ctx)`, the `go` keyword launches the function
in the background. The main server continues starting up without waiting for it.
The worker runs forever (or until the server shuts down) inside its own
goroutine.

**Analogy:** It's like hiring a research assistant who works in a back office
continuously updating a spreadsheet while you answer phones at the front desk.
Both happen at the same time.

### What is an upsert?

The worker uses `INSERT … ON CONFLICT DO UPDATE` — called an upsert. If the
game doesn't exist yet, it inserts a new row. If the game already exists (same
ESPN ID), it updates the score, status, and broadcast info in place. This means
running the worker repeatedly never creates duplicate rows.

### Why ESPN's API requires no key

ESPN exposes a public, undocumented scoreboard API that browsers use to power
ESPN.com. It returns JSON and requires no authentication. The URLs follow a
predictable pattern:

```
https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={YYYYMMDD}
```

Examples:
```
https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20260430
https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates=20260430
https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20260430
```

Because it is undocumented, ESPN can change or remove it without notice. In
practice it has been stable for years.

### What sports are ingested?

The worker polls all eight of these leagues on every cycle:

| League | ESPN slug |
|--------|-----------|
| NFL | `football/nfl` |
| College Football | `football/college-football` |
| NBA | `basketball/nba` |
| College Basketball | `basketball/mens-college-basketball` |
| MLB | `baseball/mlb` |
| College Baseball | `baseball/college-baseball` |
| NHL | `hockey/nhl` |
| MLS | `soccer/usa.1` |

Off-season leagues return an empty events array — the worker logs nothing and
moves on.

---

## How the code works — step by step

### 1. Startup (`StartSportsWorker`)

Located in `internal/ingestion/sports.go`.

```
StartSportsWorker(ctx)
  ├── SeedBroadcastMappings  — write network→app mappings to DB
  ├── LoadMappings            — load those mappings into memory cache
  ├── fetchAll(ctx, 0)        — fetch today's games immediately
  ├── fetchAll(ctx, 1)        — fetch tomorrow
  ├── fetchAll(ctx, 2)        — fetch day after tomorrow
  └── loop forever:
       ├── every 60 s  → fetchAll(ctx, 0)  (keep live scores fresh)
       └── every 10 min → fetchAll(ctx, 1) + fetchAll(ctx, 2)
```

The three immediate fetches at startup mean the API serves real data on the
very first request, not after waiting 60 seconds.

### 2. Fetching from ESPN (`fetchAndUpsert`)

For each sport + date combination:

1. Build the ESPN URL
2. Make an HTTP GET request with a `User-Agent` header
3. Parse the JSON response into Go structs
4. Loop through each event and call `upsertEvent`

### 3. Writing to the database (`upsertEvent`)

For each ESPN event:

1. Find home and away teams from the competitors array
2. Map ESPN's status state (`pre`, `in`, `post`) to our three values: `scheduled`, `live`, `final`
3. Collect national broadcast networks (skip local/regional ones)
4. Build the score JSON (only for live and final games)
5. Parse the start time — ESPN sends dates without seconds (`2026-05-01T01:30Z`),
   so the code tries three formats before falling back to `time.Now()`
6. Run the upsert query

### 4. Broadcast mapping (`broadcasts.go`)

The raw ESPN data contains network names like `"ESPN"`, `"NBC"`, `"Prime Video"`.
The broadcast mapping table converts these to streaming apps:

| Network | Streaming app | Display name |
|---------|---------------|--------------|
| ESPN | Disney+ | Disney+ (ESPN) |
| NBC | Peacock | Peacock |
| CBS | Paramount+ | Paramount+ |
| TNT | Max | Max (TNT) |
| Prime Video | Prime Video | Prime Video |
| FOX | _(none)_ | Fox (cable only) |

These mappings are seeded into the `broadcast_mappings` table at startup and
loaded into an in-memory map so the HTTP handlers never hit the DB for a
broadcast lookup.

---

## Verifying it works

### Check the health endpoint

```powershell
curl https://api.jonathanlohr.com/v1/health
# Expected: {"status":"ok","version":"1.0.0"}
```

### Check live sports data

```powershell
curl "https://api.jonathanlohr.com/v1/sports/live?profile_id=00000000-0000-0000-0000-000000000002"
```

Look for game IDs starting with the league prefix followed by a large number
(e.g. `nba_401869409`, `mlb_401815165`). Those are real ESPN IDs — the worker
is live. IDs starting with `_seed_` are placeholder rows from the seed file and
will be replaced or coexist with real data.

### Check the CloudWatch logs

In AWS Console → **CloudWatch** → **Log groups** → `/ecs/channel-stream-backend`

Open the most recent log stream. At startup you should see:

```
Sports ingestion worker starting…
✓ Seeded 30 broadcast mappings
✓ Loaded 30 broadcast mappings into cache
ingestion NBA (20260430): ...   ← or no message if no error
ingestion MLB (20260430): ...
```

If you see `warn: could not parse date` lines, the ESPN date format changed.
See the Troubleshooting section.

### Redeploy after a code change

```powershell
docker build -t channel-stream-backend .
docker tag channel-stream-backend:latest 435204302991.dkr.ecr.us-east-1.amazonaws.com/channel-stream-backend:latest
docker push 435204302991.dkr.ecr.us-east-1.amazonaws.com/channel-stream-backend:latest
aws ecs update-service --cluster channel-stream --service channel-stream-backend --force-new-deployment
```

Wait ~2 minutes. ECS performs a rolling update — it starts new containers,
waits for them to pass health checks, then removes the old ones. Zero downtime.

---

## What was fixed during initial deployment

### Bug: ESPN dates parsed as `time.Now()`

**Symptom:** All ESPN game `start_time` values were identical and matched the
time the server started, rather than the actual game times.

**Cause:** ESPN returns dates without seconds (`"2026-05-01T01:30Z"`). Go's
`time.RFC3339` parser requires seconds and returns an error for this format.
The fallback was `time.Now()`.

**Fix:** `internal/ingestion/sports.go` now tries three date formats before
falling back:

```go
startTime, err := time.Parse(time.RFC3339, event.Date)
if err != nil {
    startTime, err = time.Parse("2006-01-02T15:04Z", event.Date)
}
if err != nil {
    startTime, err = time.Parse("2006-01-02T15:04:05Z", event.Date)
}
if err != nil {
    startTime = time.Now()
    log.Printf("warn: could not parse date %q for event %s", event.Date, event.ID)
}
```

---

## Troubleshooting

**API returns only seed data (game IDs like `mlb_seed_lad_sfg`)**

The ingestion worker hasn't run yet or couldn't reach the ESPN API. Check:
1. ECS tasks are running: AWS Console → ECS → channel-stream cluster → Services
2. CloudWatch logs show the worker started (look for "Sports ingestion worker starting")
3. The NAT gateway is deployed — private subnets need it to make outbound HTTP calls

**All games show wrong start times (current time instead of game time)**

The ESPN date format changed. Add a log line and check what format is coming
back, then add a new `time.Parse` format to the fallback chain in
`internal/ingestion/sports.go`.

**No NBA games appear even during the season**

Check if it's the playoffs — ESPN sometimes uses a different endpoint slug.
Also verify the `basketball/nba` slug is still correct by opening the ESPN URL
directly in a browser and checking if it returns data.

**Games from last season still showing as "scheduled"**

The worker only updates games it fetches. If a game's date is outside the
fetch window (today + 2 days), its row in the database is never updated and
the status stays whatever it was last set to. Stale rows can be cleaned up
with:

```sql
DELETE FROM sports_events WHERE start_time < NOW() - INTERVAL '7 days';
```

**ESPN returns a 429 (rate limited)**

The worker sends one request per sport per poll cycle. With 8 sports × 3 days
= 24 requests every 10 minutes, this has never been rate-limited in practice.
If it happens, increase the ticker intervals in `StartSportsWorker`.

**`warn: could not parse date` in CloudWatch logs**

ESPN changed their date format. Check the raw format by adding a log line in
`fetchAndUpsert`:

```go
log.Printf("ESPN date sample: %s", result.Events[0].Date)
```

Then add the new format to the parse chain.

---

## Seed data vs real data

The `supabase/seed.sql` file inserts a few placeholder games (`mlb_seed_lad_sfg`,
`nba_seed_lal_bos`) so the frontend has something to display before the ingestion
worker runs for the first time. Once the worker runs, real ESPN games are upserted
alongside them. The seed rows stay in the database — they just become less relevant
as real data fills in.

To remove seed rows once real data is flowing:

```sql
DELETE FROM sports_events WHERE id LIKE '%_seed_%';
```

---

## Adding a new sport

To add WNBA (for example):

1. Open `internal/ingestion/sports.go`
2. Add a line to `allSports`:

```go
{"basketball", "wnba", "WNBA"},
```

3. Rebuild and push the Docker image (same steps as above)

The worker will start polling the new league on its next cycle.

---

**Next**: [Module 9 → Monitoring & Alerts](./MODULE_09_MONITORING.md)
