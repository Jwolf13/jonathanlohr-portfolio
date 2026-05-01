# Channel Stream — Local Dev & Testing Guide

A step-by-step guide to get Channel Stream running on your machine and testing every phase. Written like it's your first time doing this.

---

## Step 0: Install the Prerequisites

You need these tools installed before anything else. Open your terminal and check each one.

### Docker Desktop (runs your local databases)

Download from https://www.docker.com/products/docker-desktop/ and install. After install, open Docker Desktop and let it start up. Verify it's running:

```bash
docker --version
# should print something like: Docker version 24.x.x
```

### Node.js (runs Supabase CLI and client tools)

Download from https://nodejs.org/ (pick the LTS version). Verify:

```bash
node --version
# should print something like: v20.x.x

npm --version
# should print something like: 10.x.x
```

### Supabase CLI

> **Note**: `npm install -g supabase` is no longer supported. Use one of the methods below.

**macOS / Linux (Homebrew):**
```bash
brew install supabase/tap/supabase
```

**Windows (Scoop — recommended):**
```powershell
# Install Scoop if you don't have it
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
irm get.scoop.sh | iex

# Add the Supabase bucket and install
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

Verify:
```bash
supabase --version
# should print something like: 2.x.x
```

### Go (your backend language)

Download from https://go.dev/dl/. Verify:

```bash
go version
# should print something like: go1.22.x
```

---

## Step 1: Create Your Project Folder

```bash
mkdir channel-stream
cd channel-stream
```

This is your home base. Everything lives here.

---

## Step 2: Initialize Supabase Locally

This sets up a local copy of Supabase on your machine — a full Postgres database, auth system, and API, all running in Docker containers. No cloud account needed yet.

```bash
supabase init
```

This creates a `supabase/` folder with config files. Now start it:

```bash
supabase start
```

**First time? This will take 2–5 minutes** — it's downloading Docker images. When it's done, you'll see output like:

```
API URL: http://localhost:54321
DB URL: postgresql://postgres:postgres@localhost:54322/postgres
Studio URL: http://localhost:54323
anon key: eyJhbGci...
service_role key: eyJhbGci...
```
 🔧 Development Tools                 │
├─────────┬────────────────────────────┤
│ Studio  │ http://127.0.0.1:54323     │
│ Mailpit │ http://127.0.0.1:54324     │
│ MCP     │ http://127.0.0.1:54321/mcp │
╰─────────┴────────────────────────────╯

╭──────────────────────────────────────────────────────╮
│ 🌐 APIs                                              │
├────────────────┬─────────────────────────────────────┤
│ Project URL    │ http://127.0.0.1:54321              │
│ REST           │ http://127.0.0.1:54321/rest/v1      │
│ GraphQL        │ http://127.0.0.1:54321/graphql/v1   │
│ Edge Functions │ http://127.0.0.1:54321/functions/v1 │
╰────────────────┴─────────────────────────────────────╯

╭───────────────────────────────────────────────────────────────╮
│ ⛁ Database                                                    │
├─────┬─────────────────────────────────────────────────────────┤
│ URL │ postgresql://postgres:postgres@127.0.0.1:54322/postgres │
╰─────┴─────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────╮
│ 🔑 Authentication Keys                                       │
├─────────────┬────────────────────────────────────────────────┤
│ Publishable │ sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH │
│ Secret      │ (redacted — check your Supabase dashboard)       │
╰─────────────┴────────────────────────────────────────────────╯

╭───────────────────────────────────────────────────────────────────────────────╮
│ 📦 Storage (S3)                                                               │
├────────────┬──────────────────────────────────────────────────────────────────┤
│ URL        │ http://127.0.0.1:54321/storage/v1/s3                             │
│ Access Key │ 625729a08b95bf1b7ff351a663f3a23c                                 │
│ Secret Key │ 850181e4652dd023b7a98c58ae0d2d34bd487ee0cc3254aed6eda37307425907 │
│ Region     │ local                                                            │
╰────────────┴──────────────────────────

**Save these values.** The Studio URL is your local dashboard — open it in your browser. It looks just like the Supabase cloud dashboard you saw in that screenshot.
Log in
  supabase login

  # 3. Link to your online project (use your project ref from the URL)
  supabase link --project-ref agvmmloaizlljaolvlmf

  # 4. Pull the existing remote schema down locally
  supabase db pull

  # 5. Later, when you've written migrations locally, push them up
  supabase db push

### Quick test: Is it working?

Open http://localhost:54323 in your browser. You should see the Supabase Studio dashboard with an empty database. If you see it, you're good.

---

## Step 3: Create Your Database Tables

Now we'll create the tables from the system design. Supabase uses "migrations" — SQL files that build your database step by step.

### Create your first migration

```bash
supabase migration new create_initial_schema
```

This creates a file at `supabase/migrations/<timestamp>_create_initial_schema.sql`. Open it and paste this:

```sql
-- ============================================
-- CHANNEL STREAM — INITIAL SCHEMA
-- ============================================

-- ACCOUNTS: a household that signs up
CREATE TABLE accounts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- PROFILES: each person in the household (up to 6)
CREATE TABLE profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  UUID REFERENCES accounts(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    avatar_url  TEXT,
    preferences JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- PROVIDER LINKS: which streaming services are connected
CREATE TABLE provider_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID REFERENCES accounts(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL,
    access_token    TEXT NOT NULL,
    refresh_token   TEXT,
    token_expires   TIMESTAMPTZ,
    linked_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(account_id, provider)
);

-- CONTENT: the unified catalog of all movies/shows/episodes
CREATE TABLE content (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('movie', 'series', 'episode', 'sport_event')),
    parent_id   TEXT REFERENCES content(id),
    metadata    JSONB NOT NULL DEFAULT '{}',
    artwork     JSONB,
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- CONTENT AVAILABILITY: which content is on which provider
CREATE TABLE content_availability (
    content_id      TEXT REFERENCES content(id),
    provider        TEXT NOT NULL,
    region          TEXT DEFAULT 'US',
    deeplink_tpl    TEXT NOT NULL,
    available_from  TIMESTAMPTZ,
    available_until TIMESTAMPTZ,
    PRIMARY KEY (content_id, provider, region)
);

-- WATCH STATE: where the user left off on each piece of content
CREATE TABLE watch_state (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID REFERENCES profiles(id) ON DELETE CASCADE,
    content_id      TEXT REFERENCES content(id),
    provider        TEXT NOT NULL,
    progress_pct    SMALLINT DEFAULT 0,
    position_sec    INT DEFAULT 0,
    status          TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    last_watched    TIMESTAMPTZ DEFAULT now(),
    synced_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(profile_id, content_id)
);

-- SPORTS EVENTS: games and matches
CREATE TABLE sports_events (
    id              TEXT PRIMARY KEY,
    league          TEXT NOT NULL,
    home_team_id    TEXT NOT NULL,
    away_team_id    TEXT NOT NULL,
    start_time      TIMESTAMPTZ NOT NULL,
    status          TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'live', 'final')),
    score           JSONB,
    broadcast       JSONB,
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- INTERACTIONS: tracks every click, dismiss, save (for recommendations)
CREATE TABLE interactions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY,
    profile_id      UUID NOT NULL,
    content_id      TEXT NOT NULL,
    action          TEXT NOT NULL CHECK (action IN ('view', 'click', 'dismiss', 'save', 'complete')),
    context         JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- INDEXES for fast queries
CREATE INDEX idx_profiles_account ON profiles(account_id);
CREATE INDEX idx_watch_state_profile ON watch_state(profile_id, last_watched DESC);
CREATE INDEX idx_sports_events_time ON sports_events(start_time) WHERE status != 'final';
CREATE INDEX idx_interactions_profile ON interactions(profile_id, created_at DESC);
CREATE INDEX idx_content_type ON content(type);
```

### Apply the migration

```bash
supabase db reset
```

This drops the database and re-runs all migrations from scratch. You'll see your tables appear in Studio.

### Verify: Check your tables

Open http://localhost:54323 → click **Table Editor** in the sidebar. You should see all 7 tables listed. Click on any table to see its columns. If they match the SQL above, you're golden.

---

## Step 4: Seed It with Fake Data

An empty database is hard to test with. Let's add some fake data so you can see feeds working.

Create a seed file:

```bash
touch supabase/seed.sql
```

Paste this into `supabase/seed.sql`:

```sql
-- ============================================
-- SEED DATA — fake but realistic
-- ============================================

-- 1. Create a test account
INSERT INTO accounts (id, email) VALUES
    ('a1000000-0000-0000-0000-000000000001', 'jon@test.com');

-- 2. Create a test profile
INSERT INTO profiles (id, account_id, name, preferences) VALUES
    ('p1000000-0000-0000-0000-000000000001', 'a1000000-0000-0000-0000-000000000001', 'Jon', 
     '{"genres": ["sci-fi", "thriller", "drama"], "teams": ["lakers", "dodgers", "rams"]}');

-- 3. Link some providers
INSERT INTO provider_links (account_id, provider, access_token, token_expires) VALUES
    ('a1000000-0000-0000-0000-000000000001', 'netflix', 'fake-token-netflix', now() + interval '30 days'),
    ('a1000000-0000-0000-0000-000000000001', 'hulu', 'fake-token-hulu', now() + interval '30 days'),
    ('a1000000-0000-0000-0000-000000000001', 'disney_plus', 'fake-token-disney', now() + interval '30 days'),
    ('a1000000-0000-0000-0000-000000000001', 'apple_tv_plus', 'fake-token-apple', now() + interval '30 days');

-- 4. Add some content to the catalog
INSERT INTO content (id, title, type, metadata) VALUES
    ('cs_severance_s3',     'Severance',              'series',  '{"genres": ["sci-fi", "thriller"], "year": 2025, "rating": 8.9}'),
    ('cs_severance_s3e02',  'Severance S3E2',         'episode', '{"season": 3, "episode": 2, "runtime_min": 52}'),
    ('cs_shogun',           'Shogun',                 'series',  '{"genres": ["drama", "historical"], "year": 2024, "rating": 8.7}'),
    ('cs_dune2',            'Dune: Part Two',         'movie',   '{"genres": ["sci-fi", "action"], "year": 2024, "rating": 8.5, "runtime_min": 166}'),
    ('cs_bear_s3',          'The Bear',               'series',  '{"genres": ["drama", "comedy"], "year": 2024, "rating": 8.6}'),
    ('cs_fallout',          'Fallout',                'series',  '{"genres": ["sci-fi", "action"], "year": 2024, "rating": 8.4}'),
    ('cs_ripley',           'Ripley',                 'series',  '{"genres": ["thriller", "drama"], "year": 2024, "rating": 8.2}'),
    ('cs_civil_war',        'Civil War',              'movie',   '{"genres": ["thriller", "action"], "year": 2024, "rating": 7.0, "runtime_min": 109}'),
    ('cs_challengers',      'Challengers',            'movie',   '{"genres": ["drama", "romance"], "year": 2024, "rating": 7.8, "runtime_min": 131}'),
    ('cs_3body',            '3 Body Problem',         'series',  '{"genres": ["sci-fi", "drama"], "year": 2024, "rating": 7.5}');

-- 4b. Link episodes to their series
UPDATE content SET parent_id = 'cs_severance_s3' WHERE id = 'cs_severance_s3e02';

-- 5. Set provider availability (who has what)
INSERT INTO content_availability (content_id, provider, deeplink_tpl) VALUES
    ('cs_severance_s3',     'apple_tv_plus', 'https://tv.apple.com/show/severance/{content_id}'),
    ('cs_severance_s3e02',  'apple_tv_plus', 'https://tv.apple.com/episode/{content_id}'),
    ('cs_shogun',           'hulu',          'https://www.hulu.com/series/{content_id}'),
    ('cs_dune2',            'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_bear_s3',          'hulu',          'https://www.hulu.com/series/{content_id}'),
    ('cs_fallout',          'amazon_prime',  'https://www.amazon.com/dp/{content_id}'),
    ('cs_ripley',           'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_civil_war',        'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_challengers',      'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_3body',            'netflix',       'https://www.netflix.com/title/{content_id}');

-- 6. Set some watch states (Jon is mid-way through several shows)
INSERT INTO watch_state (profile_id, content_id, provider, progress_pct, position_sec, status, last_watched) VALUES
    ('p1000000-0000-0000-0000-000000000001', 'cs_severance_s3e02', 'apple_tv_plus', 62, 1847, 'in_progress', now() - interval '2 hours'),
    ('p1000000-0000-0000-0000-000000000001', 'cs_shogun',          'hulu',          35, 1200, 'in_progress', now() - interval '1 day'),
    ('p1000000-0000-0000-0000-000000000001', 'cs_bear_s3',         'hulu',          80, 2100, 'in_progress', now() - interval '3 days'),
    ('p1000000-0000-0000-0000-000000000001', 'cs_dune2',           'netflix',       100, 9960, 'completed',   now() - interval '5 days'),
    ('p1000000-0000-0000-0000-000000000001', 'cs_ripley',          'netflix',       15, 420,  'in_progress', now() - interval '7 days');

-- 7. Add some sports events
INSERT INTO sports_events (id, league, home_team_id, away_team_id, start_time, status, score, broadcast) VALUES
    ('nba_20260427_lal_bos', 'NBA', 'lakers', 'celtics', now() + interval '2 hours', 'scheduled', 
     '{"home": 0, "away": 0}', '{"providers": ["espn_plus"], "channels": ["ESPN"]}'),
    ('mlb_20260427_lad_sfg', 'MLB', 'dodgers', 'giants', now() - interval '1 hour', 'live',
     '{"home": 4, "away": 2, "inning": "6th"}', '{"providers": ["apple_tv_plus"], "channels": ["Apple TV+"]}'),
    ('nfl_draft_2026', 'NFL', 'nfl', 'nfl', now() + interval '3 days', 'scheduled',
     null, '{"providers": ["espn_plus", "peacock"], "channels": ["ESPN", "NFL Network"]}');

-- 8. Add some interaction events
INSERT INTO interactions (profile_id, content_id, action, context) VALUES
    ('p1000000-0000-0000-0000-000000000001', 'cs_severance_s3e02', 'click', '{"feed": "up_next", "position": 1}'),
    ('p1000000-0000-0000-0000-000000000001', 'cs_dune2', 'complete', '{"feed": "watch_now", "position": 3}'),
    ('p1000000-0000-0000-0000-000000000001', 'cs_3body', 'dismiss', '{"feed": "watch_now", "position": 5}'),
    ('p1000000-0000-0000-0000-000000000001', 'cs_fallout', 'save', '{"feed": "watch_now", "position": 7}');
```

Apply the seed:

```bash
supabase db reset
```

This runs your migration AND your seed file. Now check Studio — your tables should have real data in them.

---

## Step 5: Test Your Data with SQL Queries

Before writing any Go code, let's make sure the data works. Open Supabase Studio → **SQL Editor** (left sidebar) and run these queries one at a time.

### Test 1: "Up Next" — What is Jon currently watching?

```sql
SELECT 
    ws.status,
    ws.progress_pct || '%' AS progress,
    ws.position_sec AS resume_at_sec,
    c.title,
    ws.provider,
    ws.last_watched
FROM watch_state ws
JOIN content c ON c.id = ws.content_id
WHERE ws.profile_id = 'p1000000-0000-0000-0000-000000000001'
  AND ws.status = 'in_progress'
ORDER BY ws.last_watched DESC;
```

**Expected result**: 4 rows — Severance (most recent), Shogun, The Bear, Ripley. Dune is excluded because it's completed. This IS the Up Next feed.

### Test 2: "Watch Now" — What should Jon watch next?

```sql
SELECT 
    c.title,
    c.type,
    ca.provider,
    c.metadata->>'rating' AS rating,
    c.metadata->'genres' AS genres
FROM content c
JOIN content_availability ca ON ca.content_id = c.id
JOIN provider_links pl ON pl.provider = ca.provider 
    AND pl.account_id = 'a1000000-0000-0000-0000-000000000001'
WHERE c.type IN ('series', 'movie')
  AND c.id NOT IN (
      SELECT content_id FROM watch_state 
      WHERE profile_id = 'p1000000-0000-0000-0000-000000000001' 
        AND status = 'completed'
  )
ORDER BY (c.metadata->>'rating')::FLOAT DESC;
```

**Expected result**: All content Jon has access to (via his linked providers), minus anything he already completed (Dune), sorted by rating. This is a simplified Watch Now feed.

### Test 3: "Sports Live Now" — What games does Jon care about?

```sql
SELECT 
    se.league,
    se.home_team_id || ' vs ' || se.away_team_id AS matchup,
    se.status,
    se.score,
    se.start_time,
    se.broadcast->'channels' AS channels
FROM sports_events se
WHERE se.home_team_id IN ('lakers', 'dodgers', 'rams')
   OR se.away_team_id IN ('lakers', 'dodgers', 'rams')
ORDER BY 
    CASE se.status WHEN 'live' THEN 0 WHEN 'scheduled' THEN 1 ELSE 2 END,
    se.start_time;
```

**Expected result**: Dodgers vs Giants (live, showing first), Lakers vs Celtics (upcoming). The NFL draft doesn't match Jon's teams directly.

### Test 4: Provider link check — What does Jon have access to?

```sql
SELECT provider, linked_at, token_expires 
FROM provider_links 
WHERE account_id = 'a1000000-0000-0000-0000-000000000001';
```

**Expected result**: 4 rows — netflix, hulu, disney_plus, apple_tv_plus.

---

## Step 6: Set Up the Go Backend

Now let's create a minimal Go server that exposes the feeds as API endpoints.

### Initialize the Go project

```bash
# from the channel-stream root folder
go mod init github.com/yourusername/channel-stream
```

### Install dependencies

```bash
go get github.com/jackc/pgx/v5          # Postgres driver
go get github.com/go-chi/chi/v5         # HTTP router (lightweight)
go get github.com/redis/go-redis/v9     # Redis client
```

### Create the folder structure

```bash
mkdir -p cmd/server
mkdir -p internal/feed
mkdir -p internal/sports
mkdir -p internal/provider
```

Your project now looks like:

```
channel-stream/
├── cmd/server/         ← main.go lives here (the entry point)
├── internal/feed/      ← Watch Now, Up Next, Curated Channels logic
├── internal/sports/    ← Sports Live Now logic
├── internal/provider/  ← Provider linking, token management
├── supabase/           ← migrations and seed data
├── go.mod
└── PRD.md
```

### Create a minimal server

Create `cmd/server/main.go`:

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/jackc/pgx/v5/pgxpool"
)

var db *pgxpool.Pool

func main() {
	// Connect to local Supabase Postgres
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgresql://postgres:postgres@localhost:54322/postgres"
	}

	var err error
	db, err = pgxpool.New(context.Background(), dbURL)
	if err != nil {
		log.Fatal("Cannot connect to database:", err)
	}
	defer db.Close()

	// Verify connection
	if err := db.Ping(context.Background()); err != nil {
		log.Fatal("Cannot ping database:", err)
	}
	fmt.Println("Connected to Supabase Postgres")

	// Set up routes
	r := chi.NewRouter()
	r.Use(middleware.Logger)

	r.Get("/v1/health", handleHealth)
	r.Get("/v1/feed/up-next", handleUpNext)
	r.Get("/v1/feed/watch-now", handleWatchNow)
	r.Get("/v1/sports/live", handleSportsLive)
	r.Get("/v1/providers/linked", handleLinkedProviders)

	fmt.Println("Server running at http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", r))
}

// ---------- HANDLERS ----------

func handleHealth(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func handleUpNext(w http.ResponseWriter, r *http.Request) {
	profileID := r.URL.Query().Get("profile_id")
	if profileID == "" {
		profileID = "p1000000-0000-0000-0000-000000000001" // test default
	}

	rows, err := db.Query(context.Background(), `
		SELECT c.id, c.title, c.type, ws.provider, ws.progress_pct, 
		       ws.position_sec, ws.last_watched, ca.deeplink_tpl
		FROM watch_state ws
		JOIN content c ON c.id = ws.content_id
		LEFT JOIN content_availability ca ON ca.content_id = c.id AND ca.provider = ws.provider
		WHERE ws.profile_id = $1 AND ws.status = 'in_progress'
		ORDER BY ws.last_watched DESC
	`, profileID)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()

	var items []map[string]interface{}
	for rows.Next() {
		var id, title, ctype, provider, deeplink string
		var pct int
		var posSec int
		var lastWatched interface{}

		rows.Scan(&id, &title, &ctype, &provider, &pct, &posSec, &lastWatched, &deeplink)
		items = append(items, map[string]interface{}{
			"content_id":         id,
			"title":              title,
			"type":               ctype,
			"provider":           provider,
			"progress_pct":       pct,
			"resume_position_sec": posSec,
			"deeplink":           deeplink,
			"last_watched":       lastWatched,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"feed":  "up_next",
		"items": items,
	})
}

func handleWatchNow(w http.ResponseWriter, r *http.Request) {
	profileID := r.URL.Query().Get("profile_id")
	if profileID == "" {
		profileID = "p1000000-0000-0000-0000-000000000001"
	}

	accountID := "a1000000-0000-0000-0000-000000000001" // simplified for testing

	rows, err := db.Query(context.Background(), `
		SELECT c.id, c.title, c.type, ca.provider, c.metadata->>'rating' AS rating,
		       c.metadata->'genres' AS genres, ca.deeplink_tpl
		FROM content c
		JOIN content_availability ca ON ca.content_id = c.id
		JOIN provider_links pl ON pl.provider = ca.provider AND pl.account_id = $2
		WHERE c.type IN ('series', 'movie')
		  AND c.id NOT IN (
		      SELECT content_id FROM watch_state 
		      WHERE profile_id = $1 AND status = 'completed'
		  )
		ORDER BY (c.metadata->>'rating')::FLOAT DESC
		LIMIT 30
	`, profileID, accountID)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()

	var items []map[string]interface{}
	for rows.Next() {
		var id, title, ctype, provider, deeplink string
		var rating string
		var genres interface{}

		rows.Scan(&id, &title, &ctype, &provider, &rating, &genres, &deeplink)
		items = append(items, map[string]interface{}{
			"content_id": id,
			"title":      title,
			"type":       ctype,
			"provider":   provider,
			"rating":     rating,
			"genres":     genres,
			"deeplink":   deeplink,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"feed":  "watch_now",
		"items": items,
	})
}

func handleSportsLive(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(context.Background(), `
		SELECT id, league, home_team_id, away_team_id, start_time, 
		       status, score, broadcast
		FROM sports_events
		WHERE status IN ('live', 'scheduled')
		ORDER BY 
		    CASE status WHEN 'live' THEN 0 ELSE 1 END,
		    start_time
	`)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()

	var items []map[string]interface{}
	for rows.Next() {
		var id, league, home, away, status string
		var startTime interface{}
		var score, broadcast interface{}

		rows.Scan(&id, &league, &home, &away, &startTime, &status, &score, &broadcast)
		items = append(items, map[string]interface{}{
			"game_id":   id,
			"league":    league,
			"matchup":   home + " vs " + away,
			"start_time": startTime,
			"status":    status,
			"score":     score,
			"broadcast": broadcast,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"feed":  "sports_live",
		"items": items,
	})
}

func handleLinkedProviders(w http.ResponseWriter, r *http.Request) {
	accountID := r.URL.Query().Get("account_id")
	if accountID == "" {
		accountID = "a1000000-0000-0000-0000-000000000001"
	}

	rows, err := db.Query(context.Background(), `
		SELECT provider, linked_at, token_expires FROM provider_links
		WHERE account_id = $1
	`, accountID)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()

	var items []map[string]interface{}
	for rows.Next() {
		var provider string
		var linkedAt, expires interface{}
		rows.Scan(&provider, &linkedAt, &expires)
		items = append(items, map[string]interface{}{
			"provider":      provider,
			"linked_at":     linkedAt,
			"token_expires": expires,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"providers": items,
	})
}
```

### Run it

```bash
go run ./cmd/server
```

You should see:

```
Connected to Supabase Postgres
Server running at http://localhost:8080
```

---

## Step 7: Test Every Endpoint

Open a new terminal tab and run these curl commands. Each one tests a different feed from your PRD.

### Health check

```bash
curl http://localhost:8080/v1/health
```

Expected: `{"status":"ok"}`

### Up Next feed (PRD 5.4)

```bash
curl http://localhost:8080/v1/feed/up-next | python3 -m json.tool
```

Expected: 4 items — Severance (62%), Shogun (35%), The Bear (80%), Ripley (15%), sorted by most recently watched. Each item has a `resume_position_sec` and `deeplink`.

### Watch Now feed (PRD 5.3)

```bash
curl http://localhost:8080/v1/feed/watch-now | python3 -m json.tool
```

Expected: Content sorted by rating, excluding completed Dune, only from Jon's linked providers (netflix, hulu, disney_plus, apple_tv_plus). Fallout is excluded because Jon has no amazon_prime link.

### Sports Live (PRD 5.5)

```bash
curl http://localhost:8080/v1/sports/live | python3 -m json.tool
```

Expected: Dodgers vs Giants (live) and Lakers vs Celtics (scheduled), with broadcast info showing which channel/provider carries each game.

### Linked Providers (PRD 5.1)

```bash
curl http://localhost:8080/v1/providers/linked | python3 -m json.tool
```

Expected: 4 providers with their linked dates and token expiry times.

---

## Step 8: Add Redis Caching (Phase 1 Optimization)

### Start Redis locally

```bash
docker run -d --name channel-stream-redis -p 6379:6379 redis:7-alpine
```

Verify it's running:

```bash
docker exec channel-stream-redis redis-cli ping
# Expected: PONG
```

### How it fits in

Redis sits between your API handlers and the database. The flow becomes:

1. Request comes in for Up Next feed
2. Check Redis for key `feed:p1000000...:up_next`
3. **Cache hit** → return cached JSON instantly (< 5ms)
4. **Cache miss** → query Postgres, build the feed, store in Redis with a 10-minute TTL, return

You'll add this to each handler as you build out Phase 1. The pattern is the same every time — check cache, miss → query → store → return.

### Quick test with redis-cli

```bash
# Set a value
docker exec channel-stream-redis redis-cli SET test:key "hello from channel stream"

# Get it back
docker exec channel-stream-redis redis-cli GET test:key
# Expected: "hello from channel stream"

# Set with expiration (TTL 600 seconds = 10 minutes)
docker exec channel-stream-redis redis-cli SET feed:test "cached feed json" EX 600

# Check remaining TTL
docker exec channel-stream-redis redis-cli TTL feed:test
# Expected: ~600 (counting down)
```

---

## Step 9: Testing Checklist by Phase

Use this to track what to test as you build each phase.

### Phase 1 — MVP Tests

```
DATABASE
[ ] All 7 tables created with correct columns and constraints
[ ] Seed data loads without errors
[ ] Up Next query returns only in_progress items, sorted by last_watched
[ ] Watch Now query excludes completed content and unlinked providers
[ ] Sports query returns live games first, then scheduled
[ ] Provider links query returns only linked providers for the account

API ENDPOINTS
[ ] GET /v1/health returns 200
[ ] GET /v1/feed/up-next returns correct items with resume positions
[ ] GET /v1/feed/watch-now returns scored content, no completed items
[ ] GET /v1/sports/live returns games with broadcast info
[ ] GET /v1/providers/linked returns linked providers
[ ] Invalid profile_id returns empty results, not a crash
[ ] Missing query params fall back to defaults gracefully

EDGE CASES
[ ] User with no linked providers → Watch Now returns empty feed
[ ] User with no watch state → Up Next returns empty feed
[ ] User who completed everything → Watch Now excludes all completed
[ ] Expired provider token → token_expires in the past (test re-auth flow)
[ ] No live sports right now → Sports feed returns only scheduled games
```

### Phase 2 — Multi-Platform Tests

```
MULTI-PROFILE
[ ] Create second profile under same account
[ ] Each profile has independent watch state
[ ] Each profile has independent preferences
[ ] Profile switching returns different feed results

CURATED CHANNELS
[ ] Channel endpoint returns sequential content
[ ] Content only from linked providers
[ ] Channels respect genre/mood filters

MOBILE COMPANION
[ ] Preference update from mobile reflects in TV feed within 3 seconds
[ ] Queue addition from mobile appears in Up Next on TV
```

### Phase 3 — Scale Tests

```
PERFORMANCE
[ ] Feed generation < 300ms with Redis cache hit
[ ] Feed generation < 1.5s on cache miss
[ ] 50 concurrent requests don't degrade response time
[ ] Redis cache invalidation works on watch state update

SPORTS MODULE
[ ] WebSocket connection receives live score updates
[ ] Score updates arrive within 60 seconds of real change
[ ] WebSocket reconnects gracefully after disconnect
```

---

## Step 10: Useful Commands Reference

Commands you'll run often, all in one place.

```bash
# --- SUPABASE ---
supabase start                    # start local Supabase
supabase stop                     # stop local Supabase
supabase db reset                 # wipe DB and re-run migrations + seed
supabase migration new <name>     # create a new migration file
supabase status                   # show local URLs and keys

# --- GO SERVER ---
go run ./cmd/server               # start the server
go test ./...                     # run all tests
go build -o channel-stream ./cmd/server  # build a binary

# --- REDIS ---
docker start channel-stream-redis       # start Redis container
docker stop channel-stream-redis        # stop Redis container
docker exec channel-stream-redis redis-cli  # open Redis CLI

# --- TESTING ---
curl http://localhost:8080/v1/health
curl http://localhost:8080/v1/feed/up-next | python3 -m json.tool
curl http://localhost:8080/v1/feed/watch-now | python3 -m json.tool
curl http://localhost:8080/v1/sports/live | python3 -m json.tool

# --- CLEANUP ---
supabase stop                     # stop Supabase containers
docker stop channel-stream-redis  # stop Redis
docker rm channel-stream-redis    # remove Redis container
```
