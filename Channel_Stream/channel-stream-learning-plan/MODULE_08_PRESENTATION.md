# Module 8 — Presenting Like a Real Business
### Turning a Technical Project Into a Compelling Story

---

> **Goal**: Build a presentation package that makes Channel Stream look like a real company — not a school project. Learn how to tell the story to technical audiences (engineers), business audiences (investors, hiring managers), and mixed audiences. Create the artifacts that real engineering teams produce.

> **Time**: ~4–6 hours

---

## 8.1 Know Your Audience Before You Present

The biggest mistake in technical presentations: showing the same slides to everyone.

| Audience | What They Care About | What to Show |
|---|---|---|
| **Hiring manager / Recruiter** | Can you build real things? Do you think like an engineer? | Live demo, GitHub repo, your learning journey |
| **Technical interviewer / CTO** | Do you understand the tradeoffs? Can you defend decisions? | Architecture diagram, why Go, why Redis, failure modes |
| **Product/business stakeholder** | Does this solve a real problem? Can it scale? Will it make money? | Problem statement, demo, metrics, roadmap |
| **Investor** | What's the market? What's the moat? How do you win? | TAM, competitive landscape, technical differentiation |

This module covers all four — you'll build materials for each.

---

## 8.2 The 90-Second Pitch (For Any Audience)

Memorize this. Practice it until it flows naturally:

> "Sports fans in the US pay for Peacock, Disney+, Paramount+, Max, Prime Video, and Apple TV+ — and they still miss games because they don't know which app carries what. The rights landscape changes every season and it's genuinely confusing.
>
> Channel Stream is the answer to 'where can I watch this game?' You follow your teams — Lakers, Chiefs, Dodgers — and you get one feed: which games are happening right now, the current score, and exactly which streaming app to open. One tap and you're watching.
>
> Under the hood: a Go backend that polls ESPN's live data every 60 seconds for 8 sports, maps broadcast networks to streaming apps via a curated database, and serves everything through Redis-cached API endpoints. The whole thing runs on data that's free, publicly available, and updates in near-real-time.
>
> No content licensing. No provider API keys. No watch history that users have to trust us with. Just the question every sports fan has every game day: what's on and where do I watch it?"

Practice until you can say this in 90 seconds without notes.

---

## 8.3 The Technical Demo Script

A live demo is worth ten slides. Here's the exact script for a technical demo:

### Setup (Before the Demo)
```bash
# Make sure everything is running
supabase start
go run ./cmd/server &
npm run dev &

# Verify
curl http://localhost:8080/v1/health
# Open http://localhost:3001 in browser (package.json runs Next.js on 3001)
```

### Demo Flow (8 minutes)

**Minute 1-2: The Problem**
- Open 5 browser tabs: ESPN, Peacock, Disney+, Paramount+, Max
- Say: "NFL Sunday. Chiefs are playing. Which app? CBS? NFL Network? Peacock? Prime Video? This happens every single week."
- Close all tabs. Open http://localhost:3001

**Minute 2-3: The Sports Dashboard**
- Show the dashboard: "One screen. Your teams. Live scores. Which app to open."
- Point to the live game card: "Dodgers game, live right now, bottom of the 6th, 4-2. Apple TV+ carries it. One tap."
- "The whole thing loaded in under 100 milliseconds. Let me show you why."

**Minute 3-4: The API (For Technical Audiences)**
- Open Thunder Client in VS Code
- Make a live request: `GET http://localhost:8080/v1/sports/live?profile_id=00000000-0000-0000-0000-000000000002`
- "First request: hits the database. See the X-Cache: MISS header. Two queries."
- Make the same request again: "Second request: served from Redis. X-Cache: HIT. Zero database queries."
- "The sports live feed caches at 90-second TTL — scores are near-real-time, and we don't hit the database on every user."

**Minute 4-5: The Ingestion Worker**
- Open the server terminal: show the ESPN poll logs appearing every 60 seconds
- Open Supabase Studio: http://localhost:54323
- Show the `sports_events` table: "These rows were just written by a background goroutine. Each one was an ESPN API call, parsed, and upserted. No manual data entry."
- Show `broadcast_mappings`: "35 rows. ESPN maps to Disney+. TNT maps to Max. FOX requires cable. This is the intelligence that makes the product work."

**Minute 5-6: Broadcast Intelligence**
- Pull up the API response JSON in Thunder Client
- Expand a `watch_on` array: "The user asked 'where can I watch this game?' We answered: Disney+ (ESPN), streaming, no cable required."
- "That logic is 40 lines of Go in `buildWatchOn()`. It reads an in-memory broadcast cache and returns sorted streaming options. Zero additional DB calls."

**Minute 6-7: The Schedule**
- `GET http://localhost:8080/v1/sports/schedule` — show the 7-day view
- "Week of games. Filtered to your teams. Same broadcast intelligence, same streaming guidance."
- "Plan your week without opening five apps."

**Minute 7-8: Architecture & Scale**
- Show `system-design-channel-stream.md` diagram
- "Go monolith. ESPN as the data source — free, public, no API key. PostgreSQL for persistence. Redis for caching. The ingestion worker and HTTP server are goroutines in the same process — simple, until scale demands otherwise."
- "On game day for a popular team, the sports feed cache absorbs thousands of requests per minute. The ESPN API is only polled 8 times per minute regardless of user load."

---

## 8.4 The Architecture One-Pager

This is the single page you hand someone technical when they ask "how does it work?"

Create `docs/ARCHITECTURE_ONE_PAGER.md`:

```markdown
# Channel Stream — Architecture One-Pager

## What It Is
A unified streaming navigation and recommendation layer. We aggregate content 
catalogs, watch history, and sports schedules from all major providers into 
four personalized feeds: Watch Now, Up Next, Sports Live Now, and Curated Channels.
We deep-link into provider apps — zero content licensing costs.

## Stack

| Layer         | Technology                        | Rationale                                      |
|---------------|-----------------------------------|------------------------------------------------|
| Backend       | Go (modular monolith)             | Single binary, in-process modules, fast startup |
| Database      | PostgreSQL 16 (RDS Multi-AZ)      | ACID transactions, JSONB for catalog metadata  |
| Cache         | Redis 7 (ElastiCache)             | Per-profile feed cache, 10-min TTL             |
| Frontend      | Next.js + TypeScript (Vercel)     | SSR, fast initial load, TypeScript safety       |
| Infra         | AWS ECS Fargate + Terraform       | Serverless containers, IaC, reproducible        |
| CI/CD         | GitHub Actions                    | Test-on-push, auto-deploy-on-merge-to-main      |

## Request Flow (Watch Now Feed)

```
Client → API Gateway → Go Backend
            ↓
        Redis lookup (feed:{profile_id}:watch_now)
            ↓ miss
        PostgreSQL query (JOIN content × content_availability × provider_links)
            ↓
        Score & rank 500 candidates (genre, recency, provider affinity)
            ↓
        Write to Redis (TTL 10min) → Return response
```

- Cache HIT: < 10ms
- Cache MISS: 200–500ms (p95 < 1.5s)
- Cache hit ratio at launch: ~85% (estimated)

## Scale Profile

| MAU      | Instances | Database       | Redis        | Cost/mo |
|----------|-----------|----------------|--------------|---------|
| 200K     | 2×Fargate | db.r6g.large   | 1 shard      | ~$177   |
| 2M       | 4×Fargate | + read replica | 3 shards     | ~$450   |
| 5M       | 8×Fargate | Multi-primary  | 6 shards     | ~$1,200 |

## Failure Modes (Top 3)

1. **Provider API down**: Circuit breaker per provider. Serve stale catalog. 
   Watch state freezes at last known good.
   
2. **Redis failure**: Falls through to PostgreSQL. At 50 req/s (launch scale), 
   Postgres handles this without degradation.
   
3. **Database failover**: Multi-AZ standby promotes in ~60s. Feeds served 
   from Redis cache during window. Writes queue in memory (1,000 event buffer).

## Trade-offs Made

- **Monolith over microservices**: At 50 req/s, network hops between services 
  add latency without benefit. Extract when data says to (Sports first at 500K MAU).
  
- **Eventual consistency for feeds**: Watch state freshness: 5 minutes. 
  Catalog freshness: 6 hours. Acceptable — provider data is inherently async.
  
- **Heuristic ranking over ML**: Phase 1 scoring function beats any ML model 
  trained on sparse early-user data. Phase 2 switches to embedding-based CF.
```

---

## 8.5 The GitHub README (Your Public Technical Profile)

The README is the first thing any technical person sees. Make it count.

Create `README.md` in your project root:

```markdown
# Channel Stream

**Multi-platform streaming orchestration engine.** Eliminates decision fatigue 
across streaming services and live sports by aggregating content catalogs, watch 
history, and sports schedules into personalized feeds — Watch Now, Up Next, 
Sports Live Now, and Curated Channels.

→ Deep-links into provider apps. Zero content licensing costs.

## Demo

![Dashboard Screenshot](docs/screenshots/dashboard.png)

**Live feeds (no login required):**
- `GET /v1/feed/watch-now` — personalized content across linked providers
- `GET /v1/feed/up-next` — unified continue-watching across providers
- `GET /v1/sports/live` — live and upcoming games for followed teams

## Stack

- **Backend**: Go 1.26 — modular monolith, chi router, pgx PostgreSQL driver
- **Database**: PostgreSQL 16 — normalized catalog, JSONB metadata, partial indexes
- **Cache**: Redis 7 — per-profile feed cache, 10-min TTL, pub/sub for sports
- **Frontend**: Next.js 16 + TypeScript + Tailwind CSS — companion web dashboard
- **Infrastructure**: AWS ECS Fargate + RDS + ElastiCache, Terraform
- **CI/CD**: GitHub Actions — test on push, deploy on merge to main
- **Testing**: Go `testing` + Playwright for E2E

## Getting Started (Local Development)

Prerequisites: Docker Desktop, Go 1.22+, Node.js 20+, Supabase CLI

```bash
# Clone
git clone https://github.com/jwolf13/channel-stream
cd channel-stream

# Start local database (PostgreSQL via Supabase)
supabase start
supabase db reset  # applies migrations + seed data

# Start Go backend
go run ./cmd/server
# → Running at http://localhost:8080

# Start web dashboard (new terminal)
# Note: Next.js is at the project root, not in a web/ subdir
npm install && npm run dev
# → Running at http://localhost:3001

# Test all endpoints
curl http://localhost:8080/v1/feed/up-next | python3 -m json.tool
```

Full local dev guide: [LOCAL_DEV_GUIDE.md](./LOCAL_DEV_GUIDE.md)

## Architecture

[System Design Document](./system-design-channel-stream.md) — Full system design 
including data model, caching strategy, scaling plan, and failure modes.

```
Client (Roku/Web) → API Gateway → Go Backend → Redis → PostgreSQL
                                              ↑
                                  SQS Workers (catalog sync, sports ingestion)
```

## Running Tests

```bash
# Go unit + integration tests
go test ./... -v -cover

# Playwright E2E tests (runs all specs in tests/)
npm test

# API tests only (Go backend must be running separately)
npx playwright test tests/api.spec.ts
```

## Project Status

- [x] Phase 1 MVP — Core API (Watch Now, Up Next, Sports Live, Provider Linking)
- [x] Redis caching with TTL and cache invalidation
- [x] Next.js web dashboard
- [x] Go + Playwright test suite
- [x] Docker + GitHub Actions CI/CD pipeline
- [ ] Phase 2 — Roku app, multi-profile, curated channels
- [ ] Phase 2 — Embedding-based recommendations
- [ ] Phase 3 — Sports WebSocket, ClickHouse analytics
```

---

## 8.6 The "Why I Built This" Story (For Interviews)

When a hiring manager asks "Tell me about a project you're proud of," use this structure:

**Situation** (30 seconds):
"I built Channel Stream — a full-stack content aggregation and recommendation API. It's the backend for a streaming guide that would sit across Netflix, Hulu, Disney+, and sports providers and eliminate the decision fatigue of 'what should I watch.'"

**What I Built** (60 seconds):
"I built a Go REST API server with four feed endpoints — Watch Now, Up Next, Sports Live, and provider linking. The data layer is PostgreSQL with seven normalized tables, custom SQL queries using JOINs and window functions. I added Redis caching — which got the repeat request latency from 247ms to 8ms. The frontend is Next.js with TypeScript, calling my own API."

**Technical Decisions** (60 seconds):
"I made a deliberate choice to use a modular monolith rather than microservices. At the scale of the MVP — 50 requests per second — microservices would have added network latency between every module call without any benefit. The module boundaries are defined in Go packages, so when we need to extract services later — sports would go first because it has independent scaling needs — the interface contract is already there."

**What I Learned** (30 seconds):
"The hardest part was cache invalidation. I had to think carefully about which events should invalidate which cache keys and when it's acceptable to serve slightly stale data. For watch state, 5 minutes of staleness is fine. For provider link/unlink, it needs to be immediate — showing content from a service you just cancelled is a bad experience."

**Current State / Where It's Going** (15 seconds):
"The API is running, tests pass in CI, and I've deployed it to ECS. Next step is the Roku BrightScript client."

---

## 8.7 Metrics and Numbers That Impress

Learn to talk about your project in concrete numbers. Vague is weak; specific is strong.

| Metric | Weak Version | Strong Version |
|---|---|---|
| Caching | "Redis makes it faster" | "Redis cache reduces p95 latency from 247ms to 8ms — 31x improvement" |
| Database | "It uses PostgreSQL" | "PostgreSQL with 7 tables, composite primary keys on content_availability, partial index on sports_events filtering non-final games" |
| Scale | "It can handle lots of users" | "Single ECS instance handles 200 req/s. Current design targets 200K MAU at $177/month" |
| Testing | "I wrote some tests" | "85% Go test coverage, 12 Playwright E2E tests covering all 4 core feeds and 3 edge cases" |
| CI/CD | "It deploys automatically" | "GitHub Actions pipeline: Go tests → Playwright E2E → Docker build → ECS deploy. Under 4 minutes end-to-end" |

---

## 8.8 Questions You'll Get (And How to Answer)

### "Why Go instead of Python or Node?"

"Go compiles to a single statically-linked binary with no runtime dependencies. Cold start on ECS is under 200ms. The type system catches whole categories of bugs at compile time. And Go's goroutines make handling concurrent requests natural without the complexity of async/await or threading. For a read-heavy API server, it was the right tool."

### "How does your recommendation system work?"

"Phase 1 is a weighted scoring heuristic — I score each candidate content item against the user's genre preferences, viewing history, provider affinity, and time-of-day context. The weights are tunable per feed type. Phase 2 will use embedding-based collaborative filtering — train user and content vectors using implicit feedback, then serve via approximate nearest-neighbor lookup embedded in-process. No separate ML serving infrastructure at that scale."

### "What would you do differently if starting over?"

"I'd add OpenTelemetry tracing from day one. Distributed tracing shows you exactly where latency comes from in the feed generation pipeline — was it the database query, the scoring logic, or the Redis write? Without it, you're guessing when something is slow."

### "How do you handle when a streaming provider API goes down?"

"Circuit breaker per provider. After 5 consecutive failures, the circuit opens and we stop calling that provider for 60 seconds. We serve stale catalog data from PostgreSQL — the data doesn't disappear, it just might be up to 6 hours old. The user-facing experience degrades gracefully: the feed still loads, affected content might have a 'last updated 6 hours ago' indicator. Watch state for that provider freezes at the last known state — which is actually the provider's ground truth anyway."

---

## 8.9 Your Professional Development Artifacts

Create these files in your repo under `docs/`:

### Learning Log (`docs/LEARNING_LOG.md`)

```markdown
# Channel Stream — Learning Log

## Week 1
- Set up Go project structure, understood module system
- Wrote first PostgreSQL query with pgx driver
- Learned the difference between pointer receivers and value receivers in Go

## Week 2
- Built all four API handlers
- Debugged JSONB scanning issue (needed []byte, not string)
- Understood why parameterized queries prevent SQL injection

## Week 3
- Added Redis caching — saw 31x latency improvement in local testing
- Learned cache invalidation tradeoffs (TTL vs event-driven)
- Built Next.js frontend, first time using TypeScript interfaces for API types

## Key Concepts Mastered
- [ ] HTTP methods and REST API design
- [ ] Database normalization (1NF through 3NF)
- [ ] Connection pooling and why it matters
- [ ] Cache TTL vs event-driven invalidation
- [ ] Docker multi-stage builds
- [ ] CI/CD pipeline architecture
- [ ] Zero-downtime deployment with ECS rolling updates
```

### Decision Log (`docs/DECISIONS.md`)

```markdown
# Architecture Decisions

## ADR-001: Go for the Backend

**Date**: April 2026
**Status**: Accepted

**Context**: Needed to choose a backend language.

**Decision**: Go

**Reasons**:
- Single binary deployment — no runtime dependencies
- Native concurrency model suited for read-heavy API server
- Strong typing catches errors at compile time
- HTTP and JSON support is excellent in the standard library

**Alternatives considered**:
- Python (FastAPI): Slower, async model is more complex
- Node.js: Similar performance, but JS type system is weaker without TypeScript overhead
- Rust: Too complex for a first production service

---

## ADR-002: Modular Monolith over Microservices

**Date**: April 2026
**Status**: Accepted

**Context**: Need to serve 200K MAU at launch.

**Decision**: Single deployable Go binary with package-level module boundaries.

**Reasons**:
- At 50 req/s, network hops between services add latency without benefit
- Single deployment unit simplifies operations for a small team
- Package boundaries enforce the same separation as service boundaries
- Extraction path is clear: Sports first at 500K MAU

**Risks**:
- Harder to scale individual modules independently
- Database schema is shared (mitigated by module ownership of specific tables)
```

---

## 8.10 Your Presentation Order of Operations

When presenting to someone for the first time, do it in this order:

1. **Problem** (30 seconds): The 20-minute browsing problem. Use a story, not statistics.

2. **Solution + Demo** (3-5 minutes): Show it working. Live beats slides every time.

3. **Architecture** (2-3 minutes): The one-pager diagram. "Here's how it actually works."

4. **Key technical decisions** (1-2 minutes): Monolith, Go, Redis. Explain the WHY.

5. **What you learned** (1 minute): This is about you as a developer, not just the code.

6. **What's next** (30 seconds): Roku client, multi-profile, Curated Channels.

7. **Questions**: Invite them. Have answers ready for the 8 questions above.

Total: ~10 minutes. Short enough to hold attention, long enough to be credible.

---

## 8.11 Final Checklist — "Ready to Present" Criteria

Before you call this project presentation-ready:

**The code works:**
- [ ] All 5 API endpoints return correct responses
- [ ] Redis caching is working (X-Cache headers)
- [ ] Next.js dashboard loads in under 2 seconds
- [ ] `go test ./...` passes
- [ ] `npm test` passes

**The repo looks professional:**
- [ ] README has demo instructions, stack table, and architecture overview
- [ ] Code is organized in `cmd/`, `internal/` structure
- [ ] No hardcoded passwords, secrets, or test credentials in code
- [ ] `.gitignore` covers `.env`, `node_modules`, compiled binaries
- [ ] Meaningful commit messages (not "stuff" or "fix")

**You can explain it:**
- [ ] 90-second pitch memorized
- [ ] You can explain each architectural decision with a reason
- [ ] You can describe the caching strategy and TTL values
- [ ] You can explain what happens when the database goes down
- [ ] You know the approximate costs to run in production

**The story is clear:**
- [ ] Learning Log shows growth over time
- [ ] Decision Log documents WHY choices were made
- [ ] Architecture one-pager exists and is accurate

---

Congratulations. You now have a full-stack portfolio project that demonstrates:
- Backend API design in Go
- Database design and SQL
- Caching and performance engineering
- Frontend development with Next.js/TypeScript
- Automated testing (unit, integration, E2E)
- Infrastructure as code and deployment
- Technical communication and documentation

That's the full stack — from the database to the screen to the presentation room.

---

**Back to start**: [Module 0 → How the Web Works](./MODULE_00_HOW_THE_WEB_WORKS.md)
