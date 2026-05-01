# Module 2 — Database: PostgreSQL & Supabase
### How Channel Stream Stores Everything Permanently

---

> **Goal**: Understand relational databases from first principles, build the full Channel Stream schema from scratch, write the SQL queries that power each feed, and use Supabase Studio to visualize your data.

> **Time**: ~3–4 hours

---test 

## 2.1 What Is a Relational Database? (Really)

A relational database organizes data into **tables** (like spreadsheets) where each **row** is one record and each **column** is one piece of information about that record.

The "relational" part means tables can **reference each other** — instead of repeating information, you link it.

### The Wrong Way (Repeating Data)

Imagine storing watch history WITHOUT a relational database:

```
Title           Provider    User Email        User Genres
Severance       Apple TV+   jon@test.com      sci-fi, thriller
Shogun          Hulu        jon@test.com      sci-fi, thriller
Severance       Apple TV+   sarah@test.com    drama, romance
```

Problems:
- If Jon changes his email, you have to update it in EVERY row he has a watch record
- If Jon watches 500 shows, his email and genres are repeated 500 times (wasted space)
- If you make a typo updating one row, you have inconsistent data

### The Right Way (Relational — Linking Tables)

```
accounts table:          profiles table:              watch_state table:
─────────────            ───────────────              ──────────────────
id | email               id | account_id | name        profile_id | content_id | progress
a1 | jon@test.com        p1 | a1         | Jon         p1         | cs_sev     | 62%
a2 | sarah@test.com      p2 | a2         | Sarah       p1         | cs_sho     | 35%
                         p3 | a2         | Kids        p2         | cs_sev     | 15%
```

Now if Jon changes his email, you update ONE row in `accounts`. Everything else automatically uses the new email because it just has a reference to his `id`.

This is called **data normalization** and it's one of the most important concepts in databases.

---

## 2.2 Understanding Primary Keys and Foreign Keys

### Primary Key
Every table has a **primary key** — a unique ID for each row. In Channel Stream, we use UUIDs.

A UUID looks like: `a1000000-0000-0000-0000-000000000001`

It's a random 36-character string. The benefit: they're globally unique — you'll never have two UUIDs that match, even across different databases.

```sql
-- accounts table primary key:
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
-- "This column is the unique ID for each row.
--  If you don't provide one, generate a random UUID automatically."
```

### Foreign Key
A **foreign key** is a column in one table that references the primary key in another table.

```sql
-- profiles table references accounts table:
account_id UUID REFERENCES accounts(id) ON DELETE CASCADE
-- "This column must match an existing accounts.id value.
--  If that account is deleted, also delete this profile."
```

The `ON DELETE CASCADE` part means: if you delete an account, all its profiles automatically delete too. Without this, you'd have "orphan" profiles with no account.

---

## 2.3 Understanding Data Types

Every column in a table has a **type** — it constrains what kind of data can go in it.

| Type | What It Stores | Channel Stream Example |
|---|---|---|
| `UUID` | A unique identifier | `id`, `account_id`, `profile_id` |
| `TEXT` | Any string of text, any length | `email`, `title`, `provider` |
| `TIMESTAMPTZ` | A date and time with timezone | `created_at`, `last_watched` |
| `SMALLINT` | Small whole number (-32768 to 32767) | `progress_pct` (0-100) |
| `INT` | Larger whole number | `position_sec` (seconds of video watched) |
| `BIGINT` | Very large whole number | `id` on the interactions table (could be billions) |
| `JSONB` | JSON stored as binary (fast to query) | `metadata`, `preferences`, `score` |
| `BOOLEAN` | True or false | (not used in this schema, but common) |

### Why JSONB for metadata?

Content metadata is unpredictable. A movie has: `runtime_min`. An episode has: `season`, `episode`. A sports event has: `inning` or `quarter`. Instead of adding dozens of columns for every possible field, we put variable data in `JSONB`:

```sql
-- Instead of 20 columns:
-- runtime_min INT, season SMALLINT, episode SMALLINT, inning TEXT, ...

-- We use one JSONB column:
metadata JSONB NOT NULL DEFAULT '{}'
-- Which can hold: {"runtime_min": 166} for a movie
-- Or: {"season": 3, "episode": 2} for an episode
-- Or: {"inning": "6th", "outs": 2} for a sports event
```

The downside: JSONB fields are harder to query and enforce constraints on. Use regular columns for data you query often (like `type` or `title`), and JSONB for variable, nested data.

---

## 2.4 Start Supabase Locally

Before creating any tables, start your local database:

```bash
cd ~/channel-stream
supabase start
```

First time? This downloads Docker images — can take 5 minutes. When done:

```
Started supabase local development setup.

         API URL: http://localhost:54321
     GraphQL URL: http://localhost:54321/graphql/v1
          DB URL: postgresql://postgres:postgres@localhost:54322/postgres
      Studio URL: http://localhost:54323
    Inbucket URL: http://localhost:54324
        anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Open Supabase Studio**: http://localhost:54323

You should see a dashboard with an empty database. This is your local development environment — mess with it as much as you want, it won't affect anything real.

---

## 2.5 Create the Schema (Database Migration)

### What Is a Migration?

A **migration** is a SQL file that describes a change to the database. Migrations run in order, so you always know the exact state of your database.

Rule: Never edit your database directly in production. Always create a migration, test it locally, then apply it to production.

### Create Your First Migration

```bash
supabase migration new create_initial_schema
```

This creates: `supabase/migrations/20260427000000_create_initial_schema.sql`

The number at the start is a timestamp — it ensures migrations run in the right order.

Open this file in VS Code and paste the complete schema:

```sql
-- ============================================================
-- CHANNEL STREAM — INITIAL SCHEMA
-- ============================================================
-- Run order: this file runs first.
-- Applied with: supabase db reset
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- ACCOUNTS: one per household (the billing/login entity)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE accounts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,  -- UNIQUE means no two accounts can have the same email
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────
-- PROFILES: each person in the household (up to 6 per account)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  UUID REFERENCES accounts(id) ON DELETE CASCADE,  -- if account deleted, profile deleted too
    name        TEXT NOT NULL,
    avatar_url  TEXT,  -- nullable — not every profile has a custom avatar
    preferences JSONB DEFAULT '{}',  -- stores: { "followed_teams": ["LAL","KC"], "followed_leagues": ["nba","nfl"] }
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- This index speeds up "give me all profiles for this account" queries
CREATE INDEX idx_profiles_account ON profiles(account_id);

-- ─────────────────────────────────────────────────────────────
-- PROVIDER LINKS: which streaming services each account has connected
-- ─────────────────────────────────────────────────────────────
CREATE TABLE provider_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID REFERENCES accounts(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL,  -- 'netflix', 'hulu', 'disney_plus', 'apple_tv_plus', etc.
    access_token    TEXT NOT NULL,  -- OAuth access token (would be encrypted in production)
    refresh_token   TEXT,           -- nullable — not all providers use refresh tokens
    token_expires   TIMESTAMPTZ,    -- when the access_token expires
    linked_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(account_id, provider)    -- one link per provider per account
);

-- ─────────────────────────────────────────────────────────────
-- CONTENT: the unified catalog of all movies, shows, episodes
-- ─────────────────────────────────────────────────────────────
CREATE TABLE content (
    id          TEXT PRIMARY KEY,   -- our internal ID, e.g. 'cs_tt1234567'
                                    -- TEXT (not UUID) because we control the format
    title       TEXT NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('movie', 'series', 'episode', 'sport_event')),
    -- CHECK constraint: the database itself rejects any row where type is not one of these values
    parent_id   TEXT REFERENCES content(id),  -- episode's parent is its series
                                              -- nullable: movies and series have no parent
    metadata    JSONB NOT NULL DEFAULT '{}',  -- year, genres, cast, ratings, runtime (varies by type)
    artwork     JSONB,                        -- { "poster": "https://...", "backdrop": "https://..." }
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common query patterns:
CREATE INDEX idx_content_type ON content(type);  -- "give me all movies"
CREATE INDEX idx_content_metadata ON content USING GIN(metadata);
-- GIN index: special index for JSONB — enables fast queries like:
-- WHERE metadata @> '{"genres": ["sci-fi"]}'  (content that has sci-fi as a genre)

-- ─────────────────────────────────────────────────────────────
-- CONTENT AVAILABILITY: which content is available on which provider
-- ─────────────────────────────────────────────────────────────
-- This is a "join table" — it links content to providers.
-- One movie can be on multiple providers (Netflix AND Hulu, for example).
CREATE TABLE content_availability (
    content_id      TEXT REFERENCES content(id),
    provider        TEXT NOT NULL,  -- 'netflix', 'hulu', etc.
    region          TEXT DEFAULT 'US',
    deeplink_tpl    TEXT NOT NULL,  -- template: 'https://netflix.com/title/{content_id}'
    available_from  TIMESTAMPTZ,    -- nullable: some content is always available
    available_until TIMESTAMPTZ,    -- nullable: some content never expires
    PRIMARY KEY (content_id, provider, region)
    -- Composite primary key: a piece of content can only appear once per provider per region
);

-- ─────────────────────────────────────────────────────────────
-- WATCH STATE: where each profile left off on each piece of content
-- ─────────────────────────────────────────────────────────────
CREATE TABLE watch_state (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID REFERENCES profiles(id) ON DELETE CASCADE,
    content_id      TEXT REFERENCES content(id),
    provider        TEXT NOT NULL,    -- which provider they watched on
    progress_pct    SMALLINT DEFAULT 0 CHECK (progress_pct BETWEEN 0 AND 100),
    position_sec    INT DEFAULT 0,    -- resume position in seconds
    status          TEXT DEFAULT 'in_progress'
                    CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    last_watched    TIMESTAMPTZ DEFAULT now(),
    synced_at       TIMESTAMPTZ DEFAULT now(),  -- when we last pulled this from the provider
    UNIQUE(profile_id, content_id)  -- one watch state per profile per piece of content
);

-- Speeds up "give me everything this profile is watching" queries
CREATE INDEX idx_watch_state_profile ON watch_state(profile_id, last_watched DESC);

-- ─────────────────────────────────────────────────────────────
-- SPORTS EVENTS: games upserted from ESPN every 60 seconds
-- ─────────────────────────────────────────────────────────────
-- The ingestion worker writes here. The feed handlers read from here.
-- Game ID format: "{league}_{espnID}" e.g., "nba_401234567"
CREATE TABLE sports_events (
    id               TEXT PRIMARY KEY,
    sport            TEXT,              -- 'basketball', 'football', 'baseball', 'hockey', 'soccer'
    league           TEXT NOT NULL,    -- 'nba', 'nfl', 'mlb', 'nhl', 'usa.1', 'college-football'
    home_team_id     TEXT NOT NULL,
    home_team_name   TEXT,             -- 'Los Angeles Lakers'
    home_team_abbr   TEXT,             -- 'LAL'  ← used for team preference filtering
    away_team_id     TEXT NOT NULL,
    away_team_name   TEXT,
    away_team_abbr   TEXT,
    start_time       TIMESTAMPTZ NOT NULL,
    status           TEXT DEFAULT 'scheduled'
                     CHECK (status IN ('scheduled', 'live', 'final')),
    period_display   TEXT,             -- 'Q3 4:12', 'Bot 6th', '2nd Period'
    clock_display    TEXT,             -- raw clock string from ESPN
    score            JSONB,            -- {"home": "87", "away": "91"} — strings, not ints
    broadcast        JSONB,            -- ["ESPN","ABC"] — network name strings
    venue            TEXT,
    updated_at       TIMESTAMPTZ DEFAULT now()
);

-- Index on start_time for the WHERE start_time BETWEEN queries
CREATE INDEX idx_sports_events_time ON sports_events(start_time);
-- Indexes for team and league filtering
CREATE INDEX idx_sports_home_abbr ON sports_events(home_team_abbr);
CREATE INDEX idx_sports_away_abbr ON sports_events(away_team_abbr);
CREATE INDEX idx_sports_league    ON sports_events(league);
CREATE INDEX idx_sports_sport     ON sports_events(sport);

-- ─────────────────────────────────────────────────────────────
-- BROADCAST MAPPINGS: network name → streaming app
-- ─────────────────────────────────────────────────────────────
-- Seeded from code on every startup. Rarely changes (only when rights deals change).
-- ~35 rows. Read into memory at startup; never queried at request time.
CREATE TABLE broadcast_mappings (
    network         TEXT PRIMARY KEY,   -- 'ESPN', 'CBS', 'TNT', 'FOX'
    streaming_app   TEXT,               -- 'disney_plus', 'peacock' — NULL = cable only
    app_display     TEXT NOT NULL,      -- 'Disney+ (ESPN)', 'Fox (cable/satellite or local OTA)'
    requires_cable  BOOLEAN NOT NULL DEFAULT false,
    sort_order      INT NOT NULL DEFAULT 99  -- lower = show this option first
);

-- ─────────────────────────────────────────────────────────────
-- INTERACTIONS: every user action (for recommendation training)
-- ─────────────────────────────────────────────────────────────
-- This is an "append-only" table — rows are never updated, only inserted.
-- It's the raw event log for everything a user does.
CREATE TABLE interactions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY,  -- auto-incrementing integer (faster than UUID for high-volume inserts)
    profile_id      UUID NOT NULL,
    content_id      TEXT NOT NULL,
    action          TEXT NOT NULL
                    CHECK (action IN ('view', 'click', 'dismiss', 'save', 'complete')),
    context         JSONB,  -- {"feed": "watch_now", "position": 3, "session_id": "..."}
    created_at      TIMESTAMPTZ DEFAULT now()
);
-- Note: No foreign key on profile_id here — interactions are fire-and-forget.
-- We don't want an interaction insert to fail because the profile was just deleted.

CREATE INDEX idx_interactions_profile ON interactions(profile_id, created_at DESC);
```

### Apply the Migration

```bash
supabase db reset
```

This wipes the database and re-runs all migrations. In development, you run this constantly. In production, you NEVER use `db reset` — you apply migrations incrementally.

### Verify in Studio

Open http://localhost:54323 → Table Editor (left sidebar)

You should see all 7 tables. Click `content` — you should see columns: `id`, `title`, `type`, `parent_id`, `metadata`, `artwork`, `updated_at`.

---

## 2.6 Seed Data (Realistic Fake Data for Testing)

An empty database is hard to develop against. Create seed data that mirrors what a real user would have.

Open `supabase/seed.sql` (or create it if it doesn't exist) and paste:

```sql
-- ============================================================
-- CHANNEL STREAM — SEED DATA
-- Realistic fake data for local development and testing
-- ============================================================

-- ─── 1. TEST ACCOUNT ────────────────────────────────────────
INSERT INTO accounts (id, email) VALUES
    ('00000000-0000-0000-0000-000000000001', 'jon@test.com');


-- ─── 2. TEST PROFILE ────────────────────────────────────────
-- followed_teams: ESPN team abbreviations. followed_leagues: ESPN league slugs.
INSERT INTO profiles (id, account_id, name, preferences) VALUES
    ('00000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000001',
     'Jon',
     '{"followed_teams": ["LAL", "LAD", "LAR"], "followed_leagues": ["nba", "mlb", "nfl"]}');


-- ─── 3. PROVIDER LINKS ──────────────────────────────────────
INSERT INTO provider_links (account_id, provider, access_token, token_expires) VALUES
    ('00000000-0000-0000-0000-000000000001', 'netflix',       'fake-token-netflix',  now() + interval '30 days'),
    ('00000000-0000-0000-0000-000000000001', 'hulu',          'fake-token-hulu',     now() + interval '30 days'),
    ('00000000-0000-0000-0000-000000000001', 'disney_plus',   'fake-token-disney',   now() + interval '30 days'),
    ('00000000-0000-0000-0000-000000000001', 'apple_tv_plus', 'fake-token-apple',    now() + interval '30 days');


-- ─── 4. CONTENT CATALOG ─────────────────────────────────────
INSERT INTO content (id, title, type, metadata) VALUES
    ('cs_severance_s3',  'Severance',        'series',  '{"genres": ["sci-fi", "thriller"], "year": 2025, "rating": 8.9}'),
    ('cs_shogun',        'Shogun',           'series',  '{"genres": ["drama", "historical"], "year": 2024, "rating": 8.7}'),
    ('cs_bear_s3',       'The Bear',         'series',  '{"genres": ["drama", "comedy"], "year": 2024, "rating": 8.6}'),
    ('cs_dune2',         'Dune: Part Two',   'movie',   '{"genres": ["sci-fi", "action"], "year": 2024, "rating": 8.5, "runtime_min": 166}'),
    ('cs_fallout',       'Fallout',          'series',  '{"genres": ["sci-fi", "action"], "year": 2024, "rating": 8.4}'),
    ('cs_ripley',        'Ripley',           'series',  '{"genres": ["thriller", "drama"], "year": 2024, "rating": 8.2}'),
    ('cs_challengers',   'Challengers',      'movie',   '{"genres": ["drama", "romance"], "year": 2024, "rating": 7.8, "runtime_min": 131}'),
    ('cs_3body',         '3 Body Problem',   'series',  '{"genres": ["sci-fi", "drama"], "year": 2024, "rating": 7.5}'),
    ('cs_civil_war',     'Civil War',        'movie',   '{"genres": ["thriller", "action"], "year": 2024, "rating": 7.0, "runtime_min": 109}');

INSERT INTO content (id, title, type, parent_id, metadata) VALUES
    ('cs_severance_s3e02', 'Severance S3E2: "Hello, Ms. Cobel"', 'episode', 'cs_severance_s3',
     '{"season": 3, "episode": 2, "runtime_min": 52}');


-- ─── 5. PROVIDER AVAILABILITY ───────────────────────────────
INSERT INTO content_availability (content_id, provider, deeplink_tpl) VALUES
    ('cs_severance_s3',    'apple_tv_plus', 'https://tv.apple.com/show/severance/{content_id}'),
    ('cs_severance_s3e02', 'apple_tv_plus', 'https://tv.apple.com/episode/{content_id}'),
    ('cs_shogun',          'hulu',          'https://www.hulu.com/series/{content_id}'),
    ('cs_bear_s3',         'hulu',          'https://www.hulu.com/series/{content_id}'),
    ('cs_dune2',           'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_ripley',          'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_challengers',     'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_3body',           'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_civil_war',       'netflix',       'https://www.netflix.com/title/{content_id}'),
    ('cs_fallout',         'amazon_prime',  'https://www.amazon.com/dp/{content_id}');


-- ─── 6. WATCH STATE ─────────────────────────────────────────
INSERT INTO watch_state (profile_id, content_id, provider, progress_pct, position_sec, status, last_watched) VALUES
    ('00000000-0000-0000-0000-000000000002', 'cs_severance_s3e02', 'apple_tv_plus',  62, 1847, 'in_progress', now() - interval '2 hours'),
    ('00000000-0000-0000-0000-000000000002', 'cs_shogun',          'hulu',           35, 1200, 'in_progress', now() - interval '1 day'),
    ('00000000-0000-0000-0000-000000000002', 'cs_bear_s3',         'hulu',           80, 2100, 'in_progress', now() - interval '3 days'),
    ('00000000-0000-0000-0000-000000000002', 'cs_dune2',           'netflix',       100, 9960, 'completed',   now() - interval '5 days'),
    ('00000000-0000-0000-0000-000000000002', 'cs_ripley',          'netflix',        15,  420, 'in_progress', now() - interval '7 days');


-- ─── 7. SPORTS EVENTS ───────────────────────────────────────
-- broadcast is now a JSON array of network name strings: ["ESPN","ABC"]
-- The ingestion worker overwrites these on first run.
INSERT INTO sports_events (
    id, sport, league,
    home_team_id, home_team_name, home_team_abbr,
    away_team_id, away_team_name, away_team_abbr,
    start_time, status, period_display, clock_display,
    score, broadcast, venue
) VALUES
    ('nba_seed_lal_bos', 'basketball', 'nba',
     '6', 'Los Angeles Lakers', 'LAL',
     '2', 'Boston Celtics', 'BOS',
     now() + interval '2 hours', 'scheduled', '', '',
     null, '["ESPN"]'::jsonb, 'Crypto.com Arena'),

    ('mlb_seed_lad_sfg', 'baseball', 'mlb',
     '19', 'Los Angeles Dodgers', 'LAD',
     '26', 'San Francisco Giants', 'SF',
     now() - interval '1 hour', 'live', 'Bot 6th', '0:00',
     '{"home": "4", "away": "2"}'::jsonb, '["Apple TV+"]'::jsonb, 'Dodger Stadium'),

    ('nfl_seed_kc_buf', 'football', 'nfl',
     '12', 'Kansas City Chiefs', 'KC',
     '2', 'Buffalo Bills', 'BUF',
     now() + interval '3 days', 'scheduled', '', '',
     null, '["CBS", "Paramount+"]'::jsonb, 'Arrowhead Stadium');


-- ─── 8. INTERACTION EVENTS ──────────────────────────────────
INSERT INTO interactions (profile_id, content_id, action, context) VALUES
    ('00000000-0000-0000-0000-000000000002', 'cs_severance_s3e02', 'click',    '{"feed": "up_next",   "position": 1}'),
    ('00000000-0000-0000-0000-000000000002', 'cs_dune2',           'complete', '{"feed": "watch_now", "position": 3}'),
    ('00000000-0000-0000-0000-000000000002', 'cs_3body',           'dismiss',  '{"feed": "watch_now", "position": 5}'),
    ('00000000-0000-0000-0000-000000000002', 'cs_fallout',         'save',     '{"feed": "watch_now", "position": 7}');
```

Apply the seed:
```bash
supabase db reset
```

---

## 2.7 The Four Core SQL Queries (Run These in Studio)

Open http://localhost:54323 → SQL Editor

These four queries ARE the four feeds. Understanding them means understanding the app.

### Query 1: Up Next Feed

```sql
-- "Show me everything Jon is currently watching, most recent first"
SELECT
    ws.progress_pct || '%' AS progress,
    ws.position_sec AS resume_at_seconds,
    c.title,
    c.type,
    ws.provider,
    ws.last_watched,
    ca.deeplink_tpl AS deeplink
FROM watch_state ws
JOIN content c ON c.id = ws.content_id
LEFT JOIN content_availability ca
    ON ca.content_id = c.id
    AND ca.provider = ws.provider
WHERE ws.profile_id = '00000000-0000-0000-0000-000000000002'
  AND ws.status = 'in_progress'  -- only shows in progress (not completed)
ORDER BY ws.last_watched DESC;   -- most recently watched first

-- Expected: 4 rows — Severance (2hr ago), Shogun (1 day), The Bear (3 days), Ripley (7 days)
-- NOT Dune: it's completed
```

### Query 2: Watch Now Feed (simplified)

```sql
-- "What content does Jon have access to that he hasn't finished?"
SELECT
    c.title,
    c.type,
    ca.provider,
    c.metadata->>'rating' AS rating,  -- ->> extracts JSON field as text
    c.metadata->'genres' AS genres    -- -> extracts JSON field as JSON
FROM content c
JOIN content_availability ca ON ca.content_id = c.id
JOIN provider_links pl
    ON pl.provider = ca.provider
    AND pl.account_id = '00000000-0000-0000-0000-000000000001'
WHERE c.type IN ('series', 'movie')  -- no episodes or sport_events on Watch Now
  AND c.id NOT IN (
      -- exclude content the profile has already completed
      SELECT content_id
      FROM watch_state
      WHERE profile_id = '00000000-0000-0000-0000-000000000002'
        AND status = 'completed'
  )
ORDER BY (c.metadata->>'rating')::FLOAT DESC  -- highest rated first
LIMIT 30;

-- Expected: 7 rows — Severance, Shogun, Bear, Ripley, Challengers, 3 Body Problem, Civil War
-- NOT Dune: status = 'completed' (excluded by the NOT IN subquery)
-- NOT Fallout: available on amazon_prime which Jon hasn't linked (excluded by the JOIN on provider_links)
```

### Query 3: Sports Live Now

```sql
-- "What games are live or upcoming today for Jon's followed teams?"
-- Jon follows teams: LAL, LAD, LAR  |  leagues: nba, mlb, nfl
SELECT
    se.sport,
    se.league,
    se.home_team_name || ' vs ' || se.away_team_name AS matchup,
    se.status,
    se.period_display,
    se.score,
    se.start_time,
    se.broadcast AS networks,  -- ["ESPN","ABC"] — translated to streaming apps in Go
    se.venue
FROM sports_events se
WHERE se.start_time >= now() - interval '3 hours'  -- catch in-progress games
  AND se.start_time <= now() + interval '24 hours'
  AND se.status != 'final'
  AND (
      home_team_abbr = ANY(ARRAY['LAL','LAD','LAR'])
      OR away_team_abbr = ANY(ARRAY['LAL','LAD','LAR'])
  )
  AND league = ANY(ARRAY['nba','mlb','nfl'])
ORDER BY
    CASE se.status WHEN 'live' THEN 0 WHEN 'scheduled' THEN 1 ELSE 2 END,
    se.start_time ASC;

-- Expected with seed data: 2 rows
--   1. LAD vs SF (live, Bot 6th) — comes first
--   2. LAL vs BOS (scheduled, +2 hours)
```

### Query 4: Provider Linking Status

```sql
-- "What providers does Jon have linked?"
SELECT
    provider,
    linked_at,
    token_expires,
    CASE
        WHEN token_expires IS NULL        THEN 'never_expires'
        WHEN token_expires < now()        THEN 'expired'
        WHEN token_expires < now() + interval '7 days' THEN 'expiring_soon'
        ELSE 'valid'
    END AS token_status
FROM provider_links
WHERE account_id = '00000000-0000-0000-0000-000000000001'
ORDER BY provider;

-- Expected: 4 rows — apple_tv_plus, disney_plus, hulu, netflix (alphabetical)
-- All with token_status = 'valid' (tokens expire 30 days from seed time)
```

---

## 2.8 Migrations in Practice — Adding a Column Later

Imagine in Phase 2 you need to add a `display_order` column to profiles (for ordering profiles on the account switcher screen).

```bash
supabase migration new add_display_order_to_profiles
```

Open the new file and write:

```sql
-- Add display order to profiles
ALTER TABLE profiles
ADD COLUMN display_order SMALLINT DEFAULT 0;

-- Update existing profiles to have sequential order
WITH ordered AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY created_at) AS rn
    FROM profiles
)
UPDATE profiles
SET display_order = ordered.rn
FROM ordered
WHERE profiles.id = ordered.id;
```

```bash
supabase db reset
```

Now check Studio — profiles table has the new column.

This is the migration workflow: write SQL, reset locally, verify, then apply to production (without reset — just the new file).

---

## 2.9 Understanding Indexes

An index is like the index in the back of a book — it lets the database find data quickly without scanning every row.

```sql
-- WITHOUT an index on profile_id, this query scans every row in watch_state:
SELECT * FROM watch_state WHERE profile_id = 'p1000000...' AND status = 'in_progress';
-- At 10M rows, this takes seconds.

-- WITH this index (already in our schema):
CREATE INDEX idx_watch_state_profile ON watch_state(profile_id, last_watched DESC);
-- The database jumps directly to Jon's rows and returns them in order. Milliseconds.
```

Rules of thumb:
- **Always index foreign keys** (columns that reference another table's ID)
- **Always index columns you filter on** (`WHERE status = 'in_progress'`)
- **Always index columns you sort on** (`ORDER BY last_watched DESC`)
- **Don't over-index**: every index slows down INSERT/UPDATE operations (it has to update the index too)

---

## 2.10 Checkpoint: Questions to Answer Without Looking

- [ ] What is a primary key? Why do we use UUIDs?
- [ ] What is a foreign key? What does `ON DELETE CASCADE` do?
- [ ] What is the difference between `TEXT` and `JSONB`?
- [ ] What is a migration and why do we use them instead of editing the database directly?
- [ ] What does `JOIN` do in a SQL query?
- [ ] What does an index do and when should you add one?
- [ ] Why is Fallout excluded from Jon's Watch Now feed even though it's in the catalog?
- [ ] Run the Up Next query in Studio and verify you get 4 rows.

---

**Next**: [Module 3 → Backend — Go API Server](./MODULE_03_BACKEND_GO.md)
