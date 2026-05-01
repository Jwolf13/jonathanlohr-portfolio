# Module 0 — How the Web Works
### The Mental Model You Need Before Writing Any Code

---

> **Who this is for**: Someone who has used websites and apps their whole life but has never thought about what's actually happening behind the scenes. By the end of this module, you will be able to *draw* how Channel Stream works on a whiteboard — and that drawing will be correct.

---

## 0.1 The Big Picture: What Is a "Full-Stack" App?

When you open Netflix and click a movie, dozens of things happen in under a second. Understanding *what* those things are — and in what order — is the entire foundation of full-stack development.

Think of a full-stack app like a restaurant:

| Restaurant Role | Software Equivalent | Channel Stream Example |
|---|---|---|
| **The Menu** (what you see) | **Frontend** — the UI you look at | The web dashboard showing today's games and live scores |
| **The Kitchen** (where food is made) | **Backend** — the server doing the logic | The Go API that builds your personalized sports feed |
| **The Pantry** (where ingredients are stored) | **Database** — permanent storage | PostgreSQL storing game data, broadcast networks, and profiles |
| **The Expediter** (who passes plates fast) | **Cache** — fast temporary memory | Redis holding your pre-built sports feed for 90 seconds |
| **The Supplier** (who delivers ingredients) | **External APIs** — third-party services | ESPN's public scoreboard API for live game and broadcast data |

**Full-stack** just means you understand and can build ALL of these layers — not just the menu (frontend) or just the kitchen (backend).

---

## 0.2 How a Request Travels (Step by Step)

Let's trace exactly what happens when you open Channel Stream and it shows you tonight's games.

### The Journey of One Request

```
YOUR BROWSER                    THE INTERNET                    OUR SERVERS
────────────                    ────────────                    ───────────

1. You open Channel Stream in a browser tab.

2. The Next.js app (client) asks:
   "I need the sports live feed for profile 00000000-...-000002"
   
3. It sends an HTTP request:
   GET http://localhost:8080/v1/sports/live?profile_id=00000000-0000-0000-0000-000000000002

   Think of HTTP like mailing a letter. It has:
   - An ADDRESS: localhost:8080
   - A VERB: GET (I want to receive something)
   - A PATH: /v1/sports/live (exactly what I want)
   - PARAMETERS: profile_id=... (who is asking)

4. The Go server receives the request.
   It asks: "Do I already have a pre-built feed for this profile in Redis?"

5a. CACHE HIT (the fast path, < 5ms):
    Redis says "yes, here it is!" → Go server returns it → Done.
    The cache TTL for the live feed is 90 seconds.

5b. CACHE MISS (first request or TTL expired, ~100ms):
    Redis says "no."
    Go server queries PostgreSQL:
    "Give me this profile's followed_teams and followed_leagues."
    Then: "Give me all live and scheduled games today for those teams."
    For each game, look up the broadcast networks in the in-memory
    broadcast mapping cache → translate "ESPN" to "Disney+ (ESPN)".
    Save result to Redis (TTL: 90 seconds).
    Return the feed.

6. The response comes back as JSON:
   {
     "feed": "sports_live",
     "events": [
       {
         "home_team": { "abbr": "LAL", "name": "Los Angeles Lakers" },
         "away_team": { "abbr": "BOS", "name": "Boston Celtics" },
         "status": "live",
         "status_detail": "Q3 4:12",
         "score": { "home": "87", "away": "91" },
         "watch_on": [
           { "app": "disney_plus", "app_display": "Disney+ (ESPN)", "requires_cable": false }
         ]
       }
     ]
   }

7. The browser reads the JSON and draws game cards.
   You see the Lakers game is live, Lakers trail by 4, on Disney+.
   You open the Disney+ app and watch.
```

That entire loop — steps 1 through 7 — happens in under 200 milliseconds on a cache hit.

---

## 0.3 The Four Verbs of the Web (HTTP Methods)

Every communication between a client (your app) and a server uses one of four verbs. Learn these — you will see them everywhere.

| Verb | What It Means | Channel Stream Example |
|---|---|---|
| **GET** | "Give me something" — read only, never changes data | `GET /v1/sports/live` → give me live games for my teams |
| **POST** | "Create something new" | `POST /v1/profiles` → create a new user profile |
| **PUT** | "Update something that already exists" | `PUT /v1/profiles/{id}/preferences` → update my followed teams |
| **DELETE** | "Remove something" | `DELETE /v1/profiles/{id}` → delete a profile |

These four verbs (GET, POST, PUT, DELETE) form the foundation of what's called a **REST API**. REST is just a set of conventions for how to structure web communication. Channel Stream uses a REST API.

---

## 0.4 What Is JSON? (The Language Computers Use to Talk)

JSON stands for **JavaScript Object Notation**. Ignore the "JavaScript" part — it's used everywhere.

It's just a way to structure data so any computer program can read it:

```json
{
  "game_id": "nba_401234567",
  "sport": "basketball",
  "league": "nba",
  "home_team": { "id": "6", "name": "Los Angeles Lakers", "abbr": "LAL" },
  "away_team": { "id": "2", "name": "Boston Celtics", "abbr": "BOS" },
  "status": "live",
  "status_detail": "Q3 4:12",
  "score": { "home": "87", "away": "91" },
  "watch_on": [
    { "network": "ESPN", "app": "disney_plus", "app_display": "Disney+ (ESPN)", "requires_cable": false }
  ]
}
```

Rules are simple:
- Data is in `"key": value` pairs
- Strings (text) go in `"quotes"`
- Numbers don't
- Lists go in `[square brackets]`
- Objects (groups of data) go in `{curly braces}`
- Objects and lists can nest inside each other

**Why does this matter?** Your Go backend produces JSON. Your Next.js frontend reads JSON. Your Roku app reads JSON. Redis stores JSON. Everything talks in JSON.

---

## 0.5 What Is a Database? (The Permanent Memory)

RAM (your computer's fast memory) forgets everything when you turn off the power. A database is permanent memory — it remembers everything even after a restart.

PostgreSQL (the database in Channel Stream) stores data in **tables**, like spreadsheets:

**The `sports_events` table** (stores every game):

| id | league | home_team_abbr | away_team_abbr | status | score |
|---|---|---|---|---|---|
| nba_401234567 | nba | LAL | BOS | live | {"home":"87","away":"91"} |
| nfl_401987654 | nfl | KC | BUF | scheduled | null |
| mlb_401876543 | mlb | LAD | SF | final | {"home":"5","away":"3"} |

**The `broadcast_mappings` table** (translates network names to streaming apps):

| network | streaming_app | app_display | requires_cable |
|---|---|---|---|
| ESPN | disney_plus | Disney+ (ESPN) | false |
| CBS | paramount_plus | Paramount+ | false |
| FOX | (null) | Fox (cable/satellite or local OTA) | true |

The database connects these tables using **foreign keys** and **joins**. A **SQL query** asks the database questions:
```sql
-- "Show me all live NBA games today for the Lakers"
SELECT id, home_team_name, away_team_name, status, score, broadcast
FROM sports_events
WHERE league = 'nba'
  AND status = 'live'
  AND (home_team_abbr = 'LAL' OR away_team_abbr = 'LAL')
  AND start_time >= now() - interval '6 hours';
```

---

## 0.6 What Is a Cache? (The Speed Cheat)

Databases are great but they're not instant. Querying today's games for a profile might involve:
- Reading the profile's followed teams and leagues
- Scanning hundreds of game rows and filtering by team abbreviation
- For each game, looking up broadcast networks and translating them to streaming apps
- Sorting live games to the top, then upcoming by start time

That takes 50–200ms per request. Fine for one user. But if 10,000 people refresh their sports feed at once during halftime, the database gets crushed.

**The solution**: When you build a feed, save the result in Redis (a super-fast in-memory store). Next time someone asks for that same profile's feed within 90 seconds, return the saved result — zero database queries.

```
Without cache:  Request → 2 DB queries (~100ms) → Response
With cache:     Request → Redis lookup (~2ms) → Response
```

The tradeoff: the cached live feed might be up to 90 seconds old. For Channel Stream, that's acceptable — scores don't need to be instant, just close to real-time.

---

## 0.7 The Channel Stream Tech Stack — One Sentence Each

You'll hear these terms constantly. Here's what each one actually does:

| Technology | What It Is | What It Does in Channel Stream |
|---|---|---|
| **Go** | A programming language | Runs the backend server — handles HTTP requests, polls ESPN, stores game data |
| **PostgreSQL** | A relational database | Permanently stores game events, broadcast mappings, and user profiles |
| **Supabase** | A tool that wraps PostgreSQL | Gives you a dashboard to view your database + easy local dev setup |
| **Redis** | An in-memory data store | Caches pre-built sports feeds for 90 seconds so we don't hit the database every time |
| **Next.js** | A React-based web framework | Builds the web dashboard (today's games, live scores, broadcast info) |
| **TypeScript** | JavaScript with type safety | The language Next.js is written in; catches bugs before they happen |
| **Docker** | A tool for running software in containers | Runs PostgreSQL and Redis locally without installing them on your machine |
| **Playwright** | A browser automation testing tool | Automatically opens a browser and checks that the UI works correctly |
| **AWS** | Amazon's cloud platform | Where the production servers run (ECS, RDS, ElastiCache) |
| **GitHub Actions** | Automated workflows on GitHub | Runs your tests and deploys your code every time you push a change |
| **ESPN unofficial API** | A free public sports data feed | Returns live scores, schedules, and broadcast networks for all 8 sports |

---

## 0.8 The Channel Stream Architecture — Draw This

This is the diagram you should be able to draw from memory:

```
┌─────────────────────────────────────────────────────┐
│                  CLIENTS (who talks to us)           │
│              Web Browser (Next.js, port 3001)        │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP requests
                        ▼
┌─────────────────────────────────────────────────────┐
│               GO BACKEND SERVER (port 8080)          │
│   /v1/sports/live       → Sports Feed handler       │
│   /v1/sports/schedule   → Sports Feed handler       │
│   /v1/feed/watch-now    → Watch Now handler         │
│   /v1/feed/up-next      → Up Next handler           │
│   /v1/health            → Health check              │
└──────────┬─────────────────────────────┬────────────┘
           │                             │
           ▼                             ▼
┌──────────────────┐           ┌─────────────────────┐
│   Redis Cache    │           │  PostgreSQL Database │
│   (optional)     │           │  (permanent storage) │
│                  │           │                     │
│  sports:{id}     │           │  Tables:            │
│    → [JSON] 90s  │           │  - profiles         │
│  feed:{id}:      │           │  - sports_events    │
│    schedule 5min │           │  - broadcast_       │
│                  │           │    mappings         │
└──────────────────┘           └─────────────────────┘
                                         ▲
                                         │ upserts every 60s
┌────────────────────────────────────────┴────────────┐
│     SPORTS INGESTION WORKER (background goroutine)   │
│                                                     │
│  Polls ESPN API → parses games → upserts to DB      │
│                                                     │
│  Live ticker (60s):  today's scores                 │
│  Schedule ticker (10min): tomorrow + day after      │
│                                                     │
│  ESPN URL: site.api.espn.com/apis/site/v2/sports/   │
│            {sport}/{league}/scoreboard?dates=YYYYMMDD│
└─────────────────────────────────────────────────────┘
```

---

## 0.9 Your Mental Model Checklist

Before moving to Module 1, you should be able to answer these from memory:

- [ ] What is the difference between a frontend and a backend?
- [ ] What does HTTP GET mean vs. POST vs. PUT vs. DELETE?
- [ ] What is JSON and why do we use it?
- [ ] What is a database and why can't we just use normal computer memory?
- [ ] What is a cache and what problem does it solve?
- [ ] What does Go do in Channel Stream?
- [ ] What does PostgreSQL do?
- [ ] What does Redis do?
- [ ] What does Next.js do?
- [ ] What does the ESPN API provide, and how does Channel Stream use it?
- [ ] What is a background goroutine and why do we need one for sports data?

If you can answer all of these, you're ready to write code.

---

**Next**: [Module 1 → Your Dev Environment & Tools](./MODULE_01_DEV_ENVIRONMENT.md)
