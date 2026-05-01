# Channel Stream — Product Requirements Document

---

## 1. Overview

Channel Stream tells sports fans exactly **where and how to watch** the games they care about — live scores, broadcast network, and which streaming app to open, all in one place.

We do not host video. We are the discovery and navigation layer between a fan's followed teams and the apps that carry their games.

**Tech Stack**: Go (backend API + ingestion worker), PostgreSQL via Supabase (data store), Redis (caching), Next.js (web frontend).

---

## 2. Problem

The average sports fan follows multiple teams across multiple sports. Every game day, they face the same friction:

- **Network fragmentation**: A single NFL Sunday might require CBS, Fox, ESPN, Peacock, and Prime Video to watch all the games.
- **Subscription uncertainty**: Fans don't know which streaming service they already have carries a given game.
- **App switching**: Checking ESPN, then the league app, then their provider app just to find out if the game has started.
- **Missed games**: Not realizing a team they follow is playing because they didn't check the right app.

There is no single place that says: "Your team plays tonight. Here's the score right now. Open Disney+ to watch it."

---

## 3. Goals

- Show live scores for followed teams with ≤ 90-second lag
- Identify the exact streaming app (and whether it requires cable) for every broadcast
- Support 8 sports: NFL, NBA, MLB, NHL, MLS, College Football, Men's College Basketball, College Baseball
- Present a 7-day schedule filtered to teams and leagues the user follows
- Require zero manual data entry — ESPN's public API provides all game and broadcast data

### Non-goals

- We do **not** stream, host, or proxy video
- We do **not** track watch history across streaming services
- We do **not** build provider OAuth linking (no API exists for Netflix/Hulu watch state)
- We do **not** build mobile apps in Phase 1 (web first)
- We do **not** support international leagues or markets in Phase 1

---

## 4. Target User

**Primary**: US sports fan who subscribes to 2–4 streaming services and follows 2–5 teams across multiple sports. Tired of opening five apps to find out if a game is on.

**Personas**:

- **The Multi-Sport Fan**: Follows the NBA, NFL, and a college team. Wants a single feed showing today's games across all three leagues with scores and broadcast info.
- **The Cord-Cutter**: Cancelled cable 2 years ago. Doesn't know which games they can watch on streaming vs. which ones require cable. Needs clarity.
- **The Casual Fan**: Doesn't check scores obsessively but wants to know if their team is in a close game right now before deciding to tune in.

---

## 5. Core Features

### 5.1 Sports Live Feed

Real-time display of games in progress and games scheduled for today for the user's followed teams.

- Live scores updated every 60 seconds from ESPN's unofficial API
- Game status: `scheduled`, `live` (with period/inning/quarter + clock), or `final`
- For each game: home team, away team, venue, broadcast networks
- For each broadcast network: which streaming app carries it and whether cable is required
- Sorted: live games first (by recency/closeness), then upcoming by start time
- Cached per profile at 90-second TTL

**API endpoint**: `GET /v1/sports/live?profile_id={uuid}`

**Response shape**:
```json
{
  "feed": "sports_live",
  "generated_at": "2026-04-28T20:00:00Z",
  "count": 3,
  "events": [
    {
      "game_id": "nba_401234567",
      "sport": "basketball",
      "league": "nba",
      "home_team": { "id": "6", "name": "Los Angeles Lakers", "abbr": "LAL" },
      "away_team": { "id": "2", "name": "Boston Celtics", "abbr": "BOS" },
      "start_time": "2026-04-28T19:30:00Z",
      "status": "live",
      "status_detail": "Q3 4:12",
      "score": { "home": "87", "away": "91" },
      "venue": "Crypto.com Arena",
      "watch_on": [
        { "network": "ESPN", "app": "disney_plus", "app_display": "Disney+ (ESPN)", "requires_cable": false }
      ]
    }
  ]
}
```

### 5.2 Sports Schedule Feed

All non-final games for the next 7 days for the user's followed teams and leagues.

- Same shape as Live Feed
- Cached per profile at 5-minute TTL (less time-sensitive than live scores)
- Useful for planning: "What's on this weekend?"

**API endpoint**: `GET /v1/sports/schedule?profile_id={uuid}`

### 5.3 Team & League Following

User preferences stored as JSONB in the `profiles` table.

- `followed_teams`: list of ESPN team abbreviations (e.g., `["LAL", "LAD", "KC"]`)
- `followed_leagues`: list of ESPN league slugs (e.g., `["nba", "mlb", "nfl"]`)
- Cold-start behavior: if no preferences set, show all games across all supported sports
- Preference keys are validated against ESPN's known abbreviations/slugs

### 5.4 Broadcast Intelligence

Static mapping of broadcast network names to streaming apps, seeded from code into the DB at every startup.

| Network | Streaming App | Requires Cable |
|---|---|---|
| ESPN, ESPN2, ABC, SEC Network, ACC Network | Disney+ | No |
| NBC, Peacock, Big Ten Network | Peacock | No |
| CBS, CBS Sports Network | Paramount+ | No |
| TNT, TBS, truTV | Max | No |
| Prime Video | Prime Video | No |
| Apple TV+, MLS Season Pass | Apple TV+ | No |
| NFL Sunday Ticket | YouTube TV | No |
| FOX, FS1 | — | Yes (cable/OTA) |
| NFL Network, MLB Network, NBA TV, NHL Network | — | Yes (cable) |

Broadcast data comes directly from ESPN's API per game. The mapping table translates network names to streaming options at query time.

---

## 6. User Stories

**Discovery**
- As a fan, I want to open Channel Stream and immediately see which of my teams are playing today.
- As a fan, I want to see the current score for a live game so I can decide whether it's worth tuning in.

**Broadcast Clarity**
- As a cord-cutter, I want to know which streaming app carries each game so I don't have to guess.
- As a cable subscriber, I want to see which channel the game is on, not just which app.
- As a user, I want to see all the broadcast options for a game (some games air on multiple networks).

**Schedule**
- As a fan, I want to see the full schedule for my followed teams this week so I can plan around games.
- As a fan, I want to filter my schedule by league so I can focus on football on Sunday and basketball on weeknights.

**Preferences**
- As a new user, I want to follow my teams during setup so my first feed is already personalized.
- As a user, I want to follow a new team and have it appear in my feed immediately.

---

## 7. Success Metrics

| Metric | Target |
|---|---|
| Live score freshness | ≤ 90 seconds behind ESPN |
| Sports Live API latency (cached) | < 100ms p95 |
| Sports Live API latency (cold) | < 500ms p95 |
| Broadcast coverage | ≥ 95% of ESPN-listed games have a resolved `watch_on` entry |
| Schedule horizon | 7 days of non-final games available |
| Supported sports | 8 (NFL, NBA, MLB, NHL, MLS, CFB, CBB, College Baseball) |

---

## 8. Data Flow

```
ESPN API (public, no key required)
    ↓  polled every 60s (live) / 10min (schedule)
Ingestion Worker (Go goroutine)
    ↓  upserts via INSERT … ON CONFLICT DO UPDATE
sports_events table (PostgreSQL)
    ↓  queried on every API request
Feed Handler (Go HTTP handler)
    ↓  enriched with broadcast_mappings lookup (in-memory cache)
Redis Cache (90s TTL for live, 5min for schedule)
    ↓
Client (Next.js / browser)
```

---

## 9. Milestones

### Phase 1 — Working Model (Current)

- ESPN ingestion worker running for all 8 sports
- `/v1/sports/live` and `/v1/sports/schedule` endpoints
- Broadcast intelligence: 35 network-to-app mappings
- Profile preferences: followed teams and leagues
- Redis caching with graceful degradation
- Seed data and local Supabase development environment

### Phase 2 — Frontend

- Next.js sports dashboard: today's games, live scores, broadcast chips
- Team/league following UI in profile settings
- Score auto-refresh every 90 seconds
- Broadcast chip design: streaming app logo + "requires cable" badge

### Phase 3 — Polish & Launch

- Score push via WebSocket or SSE (replace polling)
- Game alert notifications ("your team just went live")
- Multi-profile support
- Mobile-responsive layout
- Production deployment on AWS (ECS + RDS + ElastiCache)
