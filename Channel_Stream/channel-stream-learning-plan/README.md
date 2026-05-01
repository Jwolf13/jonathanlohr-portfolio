# Channel Stream — Full-Stack Learning Plan

**The complete guide to building, maintaining, and presenting Channel Stream as a real engineering product.**

This curriculum takes you from zero coding knowledge of full-stack development to a production-deployable, presentation-ready system. Every module assumes you are reading it for the first time — nothing is skipped, nothing is assumed.

---

## What You Will Build

Channel Stream tells sports fans where and how to watch the games they follow — live scores, broadcast network, and the exact streaming app to open. You are building:

| Layer | Technology | What It Does |
|---|---|---|
| Database | PostgreSQL + Supabase | Stores game events, broadcast mappings, and user profiles |
| Backend API | Go | Ingests ESPN data and serves sports feeds over HTTP |
| Cache | Redis | Makes sports feeds near-instant on repeat requests (90s TTL) |
| Frontend | Next.js + TypeScript | Web dashboard showing today's games, scores, and broadcast info |
| Testing | Go testing + Playwright | Automatically verifies everything works |
| Infrastructure | AWS ECS + Terraform | Deploys to the real internet |
| CI/CD | GitHub Actions | Tests and deploys on every code push |

---

## Modules (Read in Order)

| # | Module | What You'll Be Able to Do |
|---|---|---|
| [0](./MODULE_00_HOW_THE_WEB_WORKS.md) | **How the Web Works** | Draw the architecture from memory; explain HTTP, JSON, databases, and caches |
| [1](./MODULE_01_DEV_ENVIRONMENT.md) | **Dev Environment & Tools** | Have every tool installed and verified; create the project structure |
| [2](./MODULE_02_DATABASE.md) | **Database: PostgreSQL & Supabase** | Create the schema, seed test data, and run the SQL queries that power each feed |
| [3](./MODULE_03_BACKEND_GO.md) | **Backend: Go API Server** | Build a running API with all 5 endpoints returning correct data |
| [4](./MODULE_04_FRONTEND_NEXTJS.md) | **Frontend: Next.js Dashboard** | Build the web companion app that displays all feeds from your API |
| [5](./MODULE_05_REDIS_CACHING.md) | **Caching with Redis** | Reduce repeat request latency from 247ms to 8ms with cache |
| [6](./MODULE_06_TESTING_PLAYWRIGHT.md) | **Testing with Playwright** | Write tests that verify the app works end-to-end, every time |
| [7](./MODULE_07_DEPLOYMENT_DEVOPS.md) | **Deployment & DevOps** | Deploy to AWS with zero-downtime CI/CD via GitHub Actions |
| [8](./MODULE_08_PRESENTATION.md) | **Presenting Like a Real Business** | Deliver the 10-minute demo; answer hard architecture questions |

---

## Quick Start (Shortest Path to Running Code)

If you just want to see it working before reading any modules:

```bash
# Prerequisites: Docker Desktop, Go 1.22+, Node.js 20+

# 1. Get the code
git clone https://github.com/jwolf13/channel-stream
cd channel-stream

# 2. Start the database
brew install supabase/tap/supabase
supabase start
supabase db reset

# 3. Start the backend (also starts ESPN ingestion worker)
go run ./cmd/server
# → http://localhost:8080

# 4. Test the sports feed
curl "http://localhost:8080/v1/sports/live?profile_id=00000000-0000-0000-0000-000000000002" | python3 -m json.tool

# 5. Start the frontend
npm install && npm run dev
# → http://localhost:3001
```

---

## How Long This Takes

| If you study... | Time to complete |
|---|---|
| 2 hours/day | ~5–6 weeks |
| 4 hours/day | ~2–3 weeks |
| Full-time (8+ hours) | ~1–2 weeks |

The learning is not linear — database and backend concepts compound. Module 0 and 2 take the longest. Modules after that go faster because concepts build on each other.

---

## Key Files in This Project

| File | Purpose |
|---|---|
| `PRD.md` | Product Requirements Document — what we're building and why |
| `system-design-channel-stream.md` | System design — how it's architected and key tradeoffs |
| `supabase/migrations/` | SQL that creates the database tables |
| `supabase/seed.sql` | Fake data for local development |
| `cmd/server/main.go` | Entry point — wires DB, Redis, ingestion worker, HTTP router |
| `internal/feed/` | Feed handlers (Watch Now, Up Next, Sports Live, Sports Schedule) |
| `internal/ingestion/` | ESPN ingestion worker + broadcast mapping cache |
| `internal/provider/` | Provider linking endpoint |
| `internal/cache/` | Redis caching utilities |
| `src/app/` | Next.js pages (one folder = one page) |
| `src/lib/api.ts` | All API calls from the frontend |
| `src/types/api.ts` | TypeScript types matching Go structs |
| `tests/` | Playwright E2E tests |
| `infrastructure/main.tf` | Terraform AWS infrastructure |
| `.github/workflows/deploy.yml` | GitHub Actions CI/CD pipeline |

---

## The Core Endpoints (What You're Building)

```
GET /v1/sports/live       → Live and today's games for followed teams (90s TTL cache)
GET /v1/sports/schedule   → 7-day schedule for followed teams (5min TTL cache)
GET /v1/feed/watch-now    → Content available now across all linked providers
GET /v1/feed/up-next      → Continue watching — all in-progress shows merged
GET /v1/providers/linked  → Connected streaming services and token status
```

Each sports endpoint is:
1. A background ESPN poll (every 60s live, every 10min schedule) → PostgreSQL
2. A SQL query with team/league filtering at request time
3. Broadcast network → streaming app translation (in-memory, zero DB calls)
4. Cached in Redis for 90 seconds (live) or 5 minutes (schedule)
5. Served as JSON to the Next.js dashboard

---

## Concepts You Will Master

After completing this curriculum, you will understand and be able to explain:

**Backend:**
- REST API design and HTTP methods (GET, POST, PUT, DELETE)
- Go project structure, error handling, and type system
- PostgreSQL schema design, indexes, and JOIN queries
- Parameterized queries and SQL injection prevention
- Connection pooling and why it matters at scale

**Caching:**
- Cache hit vs. miss and how to measure cache effectiveness
- TTL (Time To Live) and when to set short vs. long expiration
- Cache invalidation events and eventual consistency tradeoffs

**Frontend:**
- React component model and state management
- TypeScript interfaces and why types matter
- Next.js routing, server vs. client components
- API client design and error handling in the browser

**Infrastructure:**
- Docker containers and multi-stage builds
- AWS ECS Fargate (serverless containers)
- Infrastructure as Code with Terraform
- CI/CD pipelines and zero-downtime deployments

**Testing:**
- Unit tests for pure functions
- Integration tests against a real database
- End-to-end tests with Playwright (browser automation)
- Test IDs for stable UI element selection

**Soft skills:**
- The 90-second technical pitch
- Live demo script and preparation
- Answering architecture questions under pressure
- Writing technical documentation that non-technical people can read

---

## Using Claude Code Throughout This Curriculum

Claude Code (which you're already using) can help at every stage:

| Stage | What to ask Claude Code |
|---|---|
| Module 2 | "Write a SQL query that gives me all content matching genres in a user's preferences JSON" |
| Module 3 | "Add proper error logging to all my Go handlers using the standard log package" |
| Module 4 | "Create a Sports Live page using the same card component pattern as Up Next" |
| Module 5 | "Help me debug why the X-Cache header is showing MISS on every request" |
| Module 6 | "Write Playwright tests for the Watch Now page that verify content count and deeplinks" |
| Module 7 | "Review my Dockerfile for security issues and optimization opportunities" |
| Module 8 | "Open a browser to http://localhost:3001 and tell me if the sports dashboard loads correctly" |

The Playwright MCP gives Claude Code the ability to actually open a browser, navigate your app, and tell you what it sees — use this heavily in Modules 6 and 8.

---

*Built for real. Deployable to production. Ready to present.*
