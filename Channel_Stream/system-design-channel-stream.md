# Channel Stream — System Design Document

**Multi-Platform Entertainment Orchestration Engine**
*Design Review Draft · April 2026*

---

## 1. Problem Statement and System Scope

The average US household subscribes to 4.7 streaming services and at least one live sports package. Every evening, users face the same question: "What should I watch?" They bounce between apps, lose track of where they left off, miss live games they care about, and never discover content buried in catalogs they're already paying for.

**Channel Stream** eliminates this decision fatigue by acting as a unified orchestration layer across streaming providers and live sports. It aggregates provider catalogs, sports schedules, user watch history, and stated preferences into four core experiences:

- **Watch Now** — personalized, immediately-available content across all subscribed services
- **Up Next** — resume points, next episodes, and queued content across providers
- **Sports Live Now** — real-time schedule of games the user cares about, with direct deep-links
- **Curated Channels** — lean-back, channel-like feeds organized by mood, genre, or context (e.g., "Sunday Night Sports," "Wind Down," "Family Movie Night")

The system targets connected TV platforms first (Roku, Fire TV, Samsung Tizen) with a companion mobile app for profile management and remote queuing.

**Scope**: Content discovery, aggregation, and deep-linking. We do **not** host, transcode, or serve video. We are a navigation and recommendation layer.

---

## 2. Explicit Assumptions and Out-of-Scope Items

### Assumptions

- We negotiate API or data-feed access with major streaming providers (Netflix, Hulu, Disney+, Max, Prime Video, Peacock, Paramount+, Apple TV+). Some will be official APIs, others will require partnership agreements or licensed data feeds from providers like Gracenote or JustWatch.
- Sports data comes from licensed feeds (ESPN API, Sportradar, or equivalent).
- Users authenticate with each streaming provider via OAuth 2.0 or provider-specific linking flows. We store tokens; we do not store credentials.
- Content playback is handled by deep-linking into provider apps on the device. We never play video ourselves.
- Initial target: US market, English language. Internationalization is Phase 2+.
- MAU target at launch: 50K–200K. Scale planning horizon: 5M MAU within 18 months.

### Out of Scope

- Video hosting, transcoding, or DRM
- Social features (watch parties, shared profiles across households)
- Ad serving or ad-supported tier management
- Provider billing or subscription management
- Content moderation (we aggregate metadata, not user-generated content)
- Voice assistant integration (deferred to Phase 2)

---

## 3. Functional Requirements

**FR-1 Provider Linking**: Users can link/unlink streaming accounts. The system tracks which providers a user has access to.

**FR-2 Catalog Aggregation**: Ingest and normalize content metadata (titles, genres, ratings, artwork, availability windows) from all supported providers into a unified catalog.


**FR-3 Watch State Sync**: Pull "continue watching" and "watchlist" data from each provider. Present a unified Up Next queue.

**FR-4 Sports Schedule Ingestion**: Ingest live sports schedules, scores, and broadcast/streaming availability. Users can follow teams, leagues, and athletes.

**FR-5 Personalized Recommendations**: Generate Watch Now and Curated Channel feeds using collaborative filtering, content-based signals, and explicit preferences (genre, mood, time-of-day).

**FR-6 Sports Live Now**: Surface in-progress and upcoming games the user cares about, ranked by affinity and game state (close game > blowout).

**FR-7 Deep Linking**: Every content card resolves to a deep-link that launches the correct provider app on the user's device and starts playback.

**FR-8 Multi-Profile Support**: A household account supports up to 6 profiles, each with independent preferences and watch state.

**FR-9 Cross-Device Continuity**: Actions on the companion mobile app (add to queue, update preferences) reflect on TV within seconds.

**FR-10 Curated Channels**: System-generated or editorially-curated lean-back feeds that auto-play sequential content, simulating a "channel" experience.

---

## 4. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Feed generation latency (p95) | < 300ms for cached, < 1.5s for cold |
| Deep-link resolution (p95) | < 200ms |
| Sports schedule freshness | ≤ 60s for live scores, ≤ 5min for schedule changes |
| Catalog freshness | ≤ 6 hours |
| Watch state sync | ≤ 5 minutes (provider-dependent) |
| Availability | 99.9% (≈ 8.7h downtime/year) |
| Cross-device sync latency | < 3s for user-initiated actions |
| Cold start (new user, first feed) | < 4s including onboarding preferences |
| Client app start-to-content | < 2s on Roku Express (low-end target device) |

---

## 5. Traffic, Scale, and Storage Estimates

### At 200K MAU (Launch)

| Metric | Estimate |
|---|---|
| DAU | ~60K (30% DAU/MAU for utility app) |
| Peak concurrent users | ~15K (evening prime-time) |
| Feed requests/day | ~300K (avg 5 sessions/day/user) |
| Peak feed requests/sec | ~50 |
| Deep-link resolutions/day | ~150K |
| Sports schedule polls/day | ~20K |

### At 5M MAU (18-month horizon)

| Metric | Estimate |
|---|---|
| DAU | ~1.5M |
| Peak concurrent | ~375K |
| Peak feed requests/sec | ~1,250 |

### Storage

| Data | Size Estimate |
|---|---|
| Unified catalog (all providers) | ~2M titles × 5KB avg = ~10GB |
| User profiles + preferences | 200K users × 6 profiles × 2KB = ~2.4GB |
| Watch state records | 1.2M profiles × 50 records avg × 200B = ~12GB |
| Sports schedules (rolling 30 days) | ~50K events × 3KB = ~150MB |
| Interaction events (90-day window) | ~500M events × 200B = ~100GB |
| Recommendation model artifacts | ~2GB |

**Total active storage**: ~130GB at launch. Well within a single Postgres instance. Event data moves to columnar storage (ClickHouse or Parquet on S3) for analytics.

---

## 6. API Contracts

### Core REST API (JSON over HTTPS)

```
# Feed endpoints
GET  /v1/feed/watch-now?profile_id={id}&limit=30&cursor={token}
GET  /v1/feed/up-next?profile_id={id}&limit=20
GET  /v1/feed/sports-live?profile_id={id}
GET  /v1/feed/channel/{channel_id}?profile_id={id}&limit=50

# Content
GET  /v1/content/{content_id}
GET  /v1/content/{content_id}/availability?region=US
GET  /v1/content/{content_id}/deeplink?profile_id={id}&device_type=roku

# Provider management
POST /v1/providers/link     { provider: "netflix", auth_code: "..." }
DELETE /v1/providers/{provider_id}/unlink
GET  /v1/providers/linked?account_id={id}

# Sports
GET  /v1/sports/live?profile_id={id}
GET  /v1/sports/schedule?teams={ids}&date_range=today
POST /v1/sports/follow     { profile_id, entity_type: "team", entity_id: "..." }

# Profile & preferences
GET    /v1/profiles?account_id={id}
PUT    /v1/profiles/{id}/preferences  { genres: [...], moods: [...] }
POST   /v1/profiles/{id}/interactions { content_id, action: "dismiss|save|watched" }

# System
GET  /v1/health
GET  /v1/config/client?platform=roku&app_version=1.2.0
```

### Response Shape (Watch Now Feed)

```json
{
  "feed": "watch_now",
  "generated_at": "2026-04-27T20:15:00Z",
  "items": [
    {
      "content_id": "cs_tt1234567",
      "title": "Severance",
      "type": "series",
      "season": 3, "episode": 2,
      "provider": "apple_tv_plus",
      "artwork": { "poster": "https://cdn.channelstream.app/..." },
      "deeplink": "https://tv.apple.com/show/severance/...",
      "score": 0.94,
      "reason": "continue_watching",
      "resume_position_sec": 1847
    }
  ],
  "cursor": "eyJwYWdlIjoy..."
}
```

### WebSocket (Sports Live Updates)

```
WS /v1/sports/live/stream?profile_id={id}

Server → Client:
{
  "type": "score_update",
  "game_id": "nba_20260427_lal_bos",
  "home_score": 98, "away_score": 95,
  "period": "4Q", "clock": "2:34",
  "status": "live"
}
```

---

## 7. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT TIER                               │
│   Roku App  ·  Fire TV App  ·  Tizen App  ·  Mobile Companion   │
└──────────────────┬───────────────────────────────────────────────┘
                   │ HTTPS / WSS
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                      EDGE / GATEWAY                              │
│   CloudFront CDN (artwork, config)  ·  API Gateway (rate limit,  │
│   auth, routing)  ·  WebSocket Gateway (sports push)             │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                   APPLICATION TIER                                │
│              Modular Monolith (Go or Rust)                        │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐             │
│  │ Feed Service│  │ Provider    │  │ Sports       │             │
│  │ Module      │  │ Link Module │  │ Module       │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘             │
│         │                │                │                      │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴───────┐             │
│  │ Reco Engine │  │ Content     │  │ Deep Link    │             │
│  │ Module      │  │ Catalog Mod │  │ Resolver     │             │
│  └─────────────┘  └─────────────┘  └──────────────┘             │
└──────────────────┬───────────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────────┐
        ▼          ▼          ▼              ▼
┌────────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│ PostgreSQL │ │ Redis  │ │ S3 / CDN │ │ Message  │
│ (primary)  │ │ Cluster│ │ (assets) │ │ Queue    │
│            │ │        │ │          │ │ (SQS)    │
└────────────┘ └────────┘ └──────────┘ └──────────┘
                                            │
                              ┌──────────────┤
                              ▼              ▼
                       ┌────────────┐ ┌────────────┐
                       │ Catalog    │ │ Watch State│
                       │ Ingestion  │ │ Sync       │
                       │ Workers    │ │ Workers    │
                       └────────────┘ └────────────┘
```

**Why a modular monolith**: At 50 req/s, microservices add operational overhead (service mesh, distributed tracing complexity, deployment orchestration) without meaningful benefit. A single deployable binary with well-defined module boundaries (enforced via Go packages or Rust crates) gives us monolith simplicity with clean extraction seams for later.

---

## 8. Data Model and Database Choices

### Primary Store: PostgreSQL 16

Relational integrity for accounts, profiles, provider links, and watch state. These are transactional, user-facing, and consistency-critical.

```sql
-- Accounts and profiles
CREATE TABLE accounts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  UUID REFERENCES accounts(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    avatar_url  TEXT,
    preferences JSONB DEFAULT '{}',  -- { genres: [], moods: [], sports_teams: [] }
    created_at  TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT max_profiles CHECK (/* enforced at app layer */)
);

-- Provider linking
CREATE TABLE provider_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID REFERENCES accounts(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL,  -- 'netflix', 'hulu', etc.
    access_token    TEXT NOT NULL,  -- encrypted at rest
    refresh_token   TEXT,
    token_expires   TIMESTAMPTZ,
    linked_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(account_id, provider)
);

-- Unified content catalog
CREATE TABLE content (
    id              TEXT PRIMARY KEY,  -- 'cs_tt1234567' (our ID)
    title           TEXT NOT NULL,
    type            TEXT NOT NULL,  -- 'movie', 'series', 'episode', 'sport_event'
    parent_id       TEXT REFERENCES content(id),  -- episode → series
    metadata        JSONB NOT NULL,  -- year, genres, cast, ratings, runtime
    artwork         JSONB,
    updated_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_content_type ON content(type);
CREATE INDEX idx_content_metadata ON content USING GIN(metadata);

-- Provider availability (which content is on which service)
CREATE TABLE content_availability (
    content_id      TEXT REFERENCES content(id),
    provider        TEXT NOT NULL,
    region          TEXT DEFAULT 'US',
    deeplink_tpl    TEXT NOT NULL,  -- template with {profile} placeholders
    available_from  TIMESTAMPTZ,
    available_until TIMESTAMPTZ,
    PRIMARY KEY (content_id, provider, region)
);

-- Watch state (unified across providers)
CREATE TABLE watch_state (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID REFERENCES profiles(id) ON DELETE CASCADE,
    content_id      TEXT REFERENCES content(id),
    provider        TEXT NOT NULL,
    progress_pct    SMALLINT DEFAULT 0,  -- 0-100
    position_sec    INT DEFAULT 0,
    status          TEXT DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'abandoned'
    last_watched    TIMESTAMPTZ DEFAULT now(),
    synced_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(profile_id, content_id)
);
CREATE INDEX idx_watch_state_profile ON watch_state(profile_id, last_watched DESC);

-- Sports
CREATE TABLE sports_events (
    id              TEXT PRIMARY KEY,
    league          TEXT NOT NULL,
    home_team_id    TEXT NOT NULL,
    away_team_id    TEXT NOT NULL,
    start_time      TIMESTAMPTZ NOT NULL,
    status          TEXT DEFAULT 'scheduled',  -- 'scheduled','live','final'
    score           JSONB,
    broadcast       JSONB,  -- { providers: ["espn_plus", "peacock"], channels: ["ESPN"] }
    updated_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_sports_events_time ON sports_events(start_time) WHERE status != 'final';

-- Interaction events (for recommendation training)
CREATE TABLE interactions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY,
    profile_id      UUID NOT NULL,
    content_id      TEXT NOT NULL,
    action          TEXT NOT NULL,  -- 'view', 'click', 'dismiss', 'save', 'complete'
    context         JSONB,  -- { feed: 'watch_now', position: 3 }
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_interactions_profile ON interactions(profile_id, created_at DESC);
```

### Redis 7 (Cluster Mode)

- **Feed cache**: Pre-computed feed JSON per profile, TTL 5–15 min
- **Sports live state**: Current scores and game clocks, TTL 90s
- **Session/rate-limit counters**: Sliding window counters
- **Provider token cache**: Short-lived decrypted tokens to avoid constant KMS calls

### S3

- Artwork assets (poster images, logos), served via CloudFront
- Interaction event archives (Parquet format for analytics)
- Recommendation model snapshots

### ClickHouse (Phase 2)

Columnar analytics store for interaction events once volume exceeds what Postgres handles comfortably for analytical queries (~100M+ rows).

---

## 9. Caching Strategy

```
Request flow for GET /v1/feed/watch-now:

  Client ──▶ CDN (miss for personalized) ──▶ API Gateway
                                                │
                                                ▼
                                           Redis lookup
                                        feed:{profile_id}:watch_now
                                                │
                                     ┌──── HIT ─┤── MISS ────┐
                                     │                         │
                                     ▼                         ▼
                               Return cached            Feed Generator
                               (< 5ms)                  (query Postgres,
                                                        run ranking,
                                                        write to Redis,
                                                        TTL 10min)
                                                        (200-800ms)
```

### Cache Layers

**L1 — Client-side**: TV apps cache the last-rendered feed locally (SQLite or flat JSON). On app launch, show stale-while-revalidate: render cached feed instantly, fetch fresh feed in background, animate diff. This is critical for the 2-second start-to-content target on low-powered Roku hardware.

**L2 — CDN**: Static assets only (artwork, app config, provider logos). Personalized feeds are never CDN-cached.

**L3 — Redis**: Per-profile feed cache. Keyed as `feed:{profile_id}:{feed_type}`. TTL varies by feed type: Watch Now (10 min), Up Next (5 min, invalidated on watch-state sync), Sports Live (no cache — real-time), Curated Channels (30 min).

**Invalidation Strategy**: Event-driven. When a watch-state sync completes, publish a `watch_state.updated` event. The feed module subscribes, deletes the affected profile's `up_next` and `watch_now` cache keys. Next request triggers a fresh generation. This is eventual consistency — a user might see a stale "continue watching" entry for up to 5 minutes. Acceptable for this product.

---

## 10. Queue and Async Processing Design

### Message Broker: Amazon SQS (with SNS fan-out where needed)

SQS is chosen over Kafka at this scale for operational simplicity. Migration to Kafka is warranted when event throughput exceeds ~10K/sec sustained.

### Queue Topology

```
┌─────────────────────────────────────────────────────────┐
│                    PRODUCER EVENTS                       │
│  catalog.updated · watch_state.synced · sports.updated  │
│  user.preference_changed · provider.linked              │
└──────────────────────┬──────────────────────────────────┘
                       │
                  SNS Topic
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Feed     │ │ Reco     │ │ Analytics│
    │ Invalidation│ │ Retraining│ │ Pipeline │
    │ Queue    │ │ Queue    │ │ Queue    │
    └──────────┘ └──────────┘ └──────────┘
```

### Worker Types

**Catalog Ingestion Workers** (scheduled, every 4–6 hours per provider): Pull catalog deltas from provider APIs or data feeds. Normalize into the unified `content` schema. Upsert `content_availability`. Publish `catalog.updated` events.

**Watch State Sync Workers** (scheduled, every 5 minutes per active user): Poll provider APIs for watch progress. Reconcile with our `watch_state` table (provider wins on conflicts — they have ground truth). Publish `watch_state.synced`.

**Sports Schedule Workers** (scheduled, every 60 seconds during live windows): Poll sports data feeds. Update `sports_events` table. Push score updates to WebSocket gateway via Redis Pub/Sub.

**Feed Invalidation Workers**: Subscribe to state-change events. Delete relevant Redis cache keys. Optionally pre-warm feeds for recently-active profiles.

**Recommendation Batch Workers** (scheduled, nightly): Train/retrain lightweight recommendation models on interaction data. Publish updated model artifacts to S3. Application instances hot-reload models.

### Dead Letter Queue

All queues have a DLQ with a max receive count of 3. DLQ messages trigger a CloudWatch alarm. Manual inspection + replay via a simple admin CLI tool.

---

## 11. Recommendation and Ranking Flow

### Philosophy

Start simple. A sophisticated model on bad data loses to a simple model on good data. Phase 1 uses a scoring heuristic. Phase 2 introduces learned embeddings.

### Phase 1: Weighted Score Heuristic

```
score(content, profile) =
    w1 * genre_match(content.genres, profile.preferred_genres)
  + w2 * recency_boost(content.release_date)
  + w3 * popularity_signal(content.global_watch_count)
  + w4 * provider_affinity(content.provider, profile.usage_by_provider)
  + w5 * time_of_day_fit(content.metadata, current_time)
  + w6 * completion_signal(profile.watch_state, content)
  + w7 * editorial_boost(content.curated_score)
```

Weights are tunable per-feed type. Watch Now favors provider affinity and recency. Curated Channels favor genre coherence and time-of-day fit. Up Next is deterministic (sorted by `last_watched DESC`, filtered to `status = 'in_progress'`).

### Sports Ranking

```
sports_score(event, profile) =
    team_affinity(event.teams, profile.followed_teams) * 10
  + league_affinity(event.league, profile.followed_leagues) * 5
  + game_closeness(event.score_differential) * 3  -- live games only
  + rivalry_boost(event) * 2
  + time_proximity(event.start_time) * 1
```

### Phase 2: Embedding-Based Collaborative Filtering

Train content and user embeddings (dimension ~64) using implicit feedback (views, completions, dismissals). Serve via approximate nearest neighbor (ANN) lookup using a library like Hnswlib embedded in the application process. No separate ML serving infrastructure needed at this scale.

### Feed Assembly Pipeline

```
Profile request arrives
        │
        ▼
  ┌─────────────┐
  │ Candidate    │  Pull ~500 candidates from catalog
  │ Generation   │  (filter by: user's linked providers,
  │              │   region, content type for this feed)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Scoring      │  Apply scoring function to all candidates
  │              │  (heuristic in Phase 1, ANN in Phase 2)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Filtering    │  Remove: already completed, dismissed,
  │ & Dedup      │  duplicate across providers (keep cheapest/preferred)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Ranking &    │  Final sort. Apply diversity rules
  │ Diversity    │  (no 3+ items from same provider in a row,
  │              │   mix content types, inject sports if live)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Serialize    │  Resolve deep-links, attach artwork URLs,
  │ & Cache      │  write to Redis, return response
  └─────────────┘
```

---

## 12. Multi-Platform Client Strategy

### Platform Constraints

| | Roku | Fire TV / Android TV | Samsung Tizen |
|---|---|---|---|
| Language | BrightScript + SceneGraph | Kotlin + Leanback | Tizen Web (HTML/CSS/JS) |
| RAM | 512MB–1GB | 1–2GB | 1–1.5GB |
| CPU | ARM, single-core-like perf | Quad-core ARM | Quad-core ARM |
| Deep linking | `roUrlTransfer` + channel launch | Android Intents | `tizen.application.launchAppControl` |
| Input | IR remote (D-pad) | IR remote / BT remote | IR remote |

### Architecture: Shared Logic, Native Shells

```
┌──────────────────────────────────────────────┐
│              Shared (TypeScript)              │
│  API client · Feed state machine · Cache     │
│  manager · Deep-link resolver · Analytics    │
│  event emitter · Preference sync             │
└──────────────────────┬───────────────────────┘
                       │ compiled/bundled per platform
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  ┌──────────┐  ┌────────────┐  ┌──────────┐
  │ Roku     │  │ Android TV │  │ Tizen    │
  │ Shell    │  │ Shell      │  │ Shell    │
  │ (BSG +   │  │ (Kotlin +  │  │ (HTML +  │
  │  thin JS │  │  Leanback) │  │  Canvas) │
  │  bridge) │  │            │  │          │
  └──────────┘  └────────────┘  └──────────┘
```

**Roku**: The most constrained platform. The SceneGraph XML UI is native; the shared TypeScript logic compiles to a JS bundle executed in Roku's limited JavaScript environment (or called via a thin BrightScript bridge). Feed data is fetched once and cached in `roSGNode` fields. Image loading is lazy with aggressive LRU eviction (Roku's texture memory is ~30MB). Target: 10 visible cards, 30 pre-fetched.

**Fire TV / Android TV**: Kotlin app using the Leanback library for the 10-foot UI. Shared logic runs as a Kotlin Multiplatform or embedded JS engine module. Deep linking uses standard Android `Intent` URIs. Most forgiving platform for memory and compute.

**Samsung Tizen**: Web app (HTML5 + Canvas for smooth scrolling). Shared TypeScript runs natively. Use `requestAnimationFrame` for 60fps card scrolling. Tizen's `AVPlay` API is not needed (we deep-link, not play), but `tizen.application.launchAppControl` is the deep-link mechanism.

### Key Client Behaviors

**Stale-while-revalidate**: On every app launch, render the locally-cached feed within 500ms. Fetch fresh data in background. Animate updates (fade in new items, slide out removed ones). Users see content immediately; freshness arrives silently.

**Prefetch**: When the user scrolls to the edge of a feed, prefetch the next page. Also prefetch the deep-link resolution for the currently-focused card so launch is instant on "OK" press.

**Graceful degradation**: If the API is unreachable, show cached content with a subtle "offline" indicator. Sports Live falls back to "check back soon." No error screens; always show something watchable.

---

## 13. Security, Privacy, and Observability

### Security

**Authentication**: Account creation via email + password (bcrypt, cost factor 12) or OAuth (Sign in with Apple, Google). Sessions use short-lived JWTs (15-min access token, 7-day refresh token). TV devices use a device code flow (display a code, user confirms on mobile/web).

**Provider Tokens**: OAuth tokens from streaming providers are encrypted at rest using AWS KMS (AES-256-GCM) with per-account data keys. Tokens are decrypted only in memory, only in the provider sync module. Never logged, never cached unencrypted.

**API Security**: All traffic over TLS 1.3. Rate limiting at the gateway (100 req/min per user, 1000 req/min per account). Input validation via schema enforcement (no SQL injection surface — we use parameterized queries exclusively). CORS restricted to our domains.

**Device Security**: TV apps pin TLS certificates. App bundles are signed. No sensitive data stored on-device beyond the session refresh token (encrypted in platform keystore where available).

### Privacy

- We collect: watch history (from providers), interaction events (clicks, dismissals), stated preferences, device type
- We do not collect: actual video viewing telemetry, precise location, contacts, microphone/camera data
- Users can export or delete all data (CCPA/GDPR compliance). Deletion cascades through all tables and purges Redis cache.
- Provider tokens are revocable by the user at any time. Revocation is immediate and synchronous.

### Observability

**Metrics** (Prometheus + Grafana):
- Feed latency histograms (p50, p95, p99) by feed type
- Cache hit ratio by feed type
- Provider API latency and error rates (per provider)
- Sports WebSocket connection count and message throughput
- Queue depth and consumer lag per queue

**Logging** (structured JSON → CloudWatch / Loki):
- Request-level logs with trace ID, profile ID, feed type, latency, cache hit/miss
- Provider sync logs with token refresh events (no token values)
- Error logs with stack traces and request context

**Tracing** (OpenTelemetry → Jaeger/Tempo):
- End-to-end request traces through feed generation pipeline
- Provider API call spans (to diagnose slow provider responses)

**Alerting**:
- Feed p95 > 2s for 5 minutes → page
- Provider sync failure rate > 20% for 10 minutes → page
- Sports WebSocket disconnection spike → page
- Queue DLQ depth > 0 → warn (Slack notification)

---

## 14. Failure Modes, Resiliency, and Scaling Strategy

### Failure Modes and Mitigations

**Provider API outage**: Circuit breaker per provider (open after 5 consecutive failures, half-open after 60s). Serve stale catalog data. Show "last updated X ago" on affected provider's content. Watch state freezes at last known good state. User can still browse and deep-link — they just won't see fresh "continue watching" data for that provider.

**Database failover**: Postgres with a synchronous standby (RDS Multi-AZ). Automatic failover in ~60s. During failover, feeds are served from Redis cache. Write operations (preference updates, interactions) are queued in-memory (bounded buffer, 1000 events) and replayed after recovery. If the buffer fills, writes are dropped (interactions are best-effort; preference updates return 503).

**Redis failure**: Redis Cluster with 3 masters + 3 replicas. Loss of one shard degrades performance (cache misses for ~1/3 of profiles) but doesn't cause outage. Full Redis loss: all requests hit Postgres. At launch scale (50 req/s), Postgres handles this fine. At 5M MAU scale, this would require activating a read replica pool.

**Sports data feed outage**: Cache the last known schedule and scores. Show "scores may be delayed" banner. Fall back to displaying schedule without live scores.

**Recommendation model corruption**: Models are versioned in S3. Application loads the latest valid model on startup. If the latest model fails a health check (e.g., returns empty results for a test profile), roll back to the previous version automatically.

### Scaling Strategy

**Phase 1 (Launch → 500K MAU)**: Single modular monolith instance behind an ALB, auto-scaled 2–6 instances based on CPU. Single Postgres (db.r6g.xlarge), single Redis cluster (cache.r6g.large). This handles ~200 req/s comfortably.

**Phase 2 (500K → 2M MAU)**: Add Postgres read replicas for feed generation queries (read-heavy workload). Move interaction events to ClickHouse. Increase Redis cluster to 6 shards. Consider extracting the sports module as an independent service (different scaling profile — bursty during game times).

**Phase 3 (2M → 5M+ MAU)**: Extract feed generation into a dedicated service (the hottest path). Deploy recommendation serving as a sidecar or embedded library (not a network hop). Add a second region for latency and redundancy. Kafka replaces SQS for event streaming.

---

## 15. Key Trade-offs

### Consistency vs. Availability

**Decision: Favor availability with eventual consistency for most data.**

Watch state and catalog data are eventually consistent by nature — we're syncing from external providers on a polling cadence. Users tolerate a few minutes of staleness in their "continue watching" data. Provider links and account data are strongly consistent (Postgres transactions). Feed ranking is inherently approximate — a slightly stale feed is better than a loading spinner.

**Exception**: Provider link/unlink operations are synchronous and strongly consistent. Showing content from an unlinked provider is a bad UX. These operations invalidate all caches for the account immediately.

### Latency vs. Durability

**Decision: Interaction events are fire-and-forget (low durability, low latency). Account mutations are durable-first.**

When a user clicks a content card, we emit an interaction event asynchronously. If it's lost, the recommendation model is trivially less informed — acceptable. When a user updates preferences or links a provider, we write to Postgres synchronously and confirm to the client only after commit.

### Monolith vs. Microservices

**Decision: Modular monolith for Phase 1, with explicit extraction seams.**

At launch scale, a microservices architecture would mean: 6+ deployable services, a service mesh, distributed tracing as a requirement rather than a nice-to-have, and network latency between every module. The feed generation path would cross 3–4 network boundaries. For a startup team of 3–8 engineers, this is unnecessary complexity.

The modular monolith gives us: single deployment, in-process function calls (microsecond latency between modules), shared database connection pool, and simple local development. Module boundaries are enforced by Go package visibility or Rust crate boundaries. When a module needs independent scaling (sports is the likely first candidate), we extract it — the interface is already defined.

### Read vs. Write Optimization

**Decision: Heavily read-optimized.**

The read-to-write ratio is approximately 50:1. Feed reads dominate. We optimize with: pre-computed feed caching (Redis), denormalized content records (JSONB metadata avoids JOINs), read replicas for feed queries. Writes (interaction events, watch state syncs) are batched and async where possible. The only latency-sensitive writes are provider link/unlink and preference updates — these are infrequent and straightforward.

---

## 16. Phase 1 MVP Architecture and Phase 2 Evolution

### Phase 1 MVP (Months 1–4)

**Goal**: Ship a functional product on one platform (Roku) with 3–5 streaming providers and basic sports.

**What ships**:
- Account creation, profile management (1 profile per account in MVP)
- Provider linking for Netflix, Hulu, Disney+, Prime Video, Apple TV+
- Watch Now feed (weighted scoring heuristic)
- Up Next feed (resume watching, merged across providers)
- Sports Live Now (NFL, NBA, MLB schedules + live scores)
- Deep-linking to provider apps on Roku
- Basic preference onboarding (pick 5 genres, follow 3 teams)

**What doesn't ship**:
- Curated Channels (needs more catalog data and editorial investment)
- Multi-profile support
- Fire TV and Tizen apps
- Companion mobile app
- Advanced recommendation model

**Tech Stack**:
- Single Go binary, deployed on ECS Fargate (2 instances)
- PostgreSQL on RDS (db.r6g.large)
- Redis on ElastiCache (cache.r6g.large, single shard)
- SQS for async work, S3 for assets
- CloudFront for artwork CDN
- Terraform for infrastructure, GitHub Actions for CI/CD
- Prometheus + Grafana on Grafana Cloud (no self-hosting infra)

**Team**: 2 backend engineers, 1 Roku/TV engineer, 1 product/design. One of the backend engineers owns infra.

### Phase 2 Evolution (Months 5–12)

**Goal**: Multi-platform launch, deeper personalization, lean-back experience.

| Capability | Details |
|---|---|
| Multi-platform | Fire TV + Tizen apps using shared TypeScript core |
| Multi-profile | Up to 6 profiles per account, profile switching on TV |
| Curated Channels | System-generated channels based on mood/time, editorial curation tools |
| Mobile companion | React Native app for preference management, remote queue |
| Embedding-based reco | Train content + user embeddings, ANN serving |
| ClickHouse | Migrate interaction analytics off Postgres |
| Sports depth | Add college sports, soccer leagues, combat sports |
| Service extraction | Sports module becomes independent service (bursty scaling) |
| Voice (stretch) | Alexa/Google Assistant integration for Fire TV |

### Migration Path (Monolith → Services)

The modular monolith enforces boundaries that make extraction straightforward:

1. **Sports Module** (first extraction candidate): Already has a distinct data model, distinct ingestion pipeline, and a bursty traffic profile (game days). Extract to a separate service with its own Redis instance and WebSocket gateway.

2. **Recommendation Engine** (second candidate): If model training or serving latency becomes a bottleneck, extract the scoring/ranking logic into a sidecar or lightweight service. The feed module calls it via gRPC (in-process in monolith, network call after extraction — same interface).

3. **Feed Generation** remains in the monolith longest — it's the orchestrator that ties everything together. It only extracts if request volume demands independent scaling of the feed-serving path.

---

## Architect's Recommendation

**Ship the monolith. Instrument everything. Extract when the data tells you to.**

This system is fundamentally a read-heavy aggregation layer. The hard engineering problems are not distributed systems problems — they're integration problems (provider API quirks, deep-link format fragmentation, watch-state reconciliation across providers with different data models). A modular monolith lets a small team iterate fast on these integration challenges without paying a microservices tax.

**Three things to get right from day one:**

1. **Deep-link reliability.** If users press "OK" and the wrong app opens or playback doesn't start, trust is destroyed. Invest in a deep-link testing harness across all devices. Maintain a provider-specific deep-link template registry and test it on every catalog update.

2. **Feed latency on Roku.** The Roku Express has the processing power of a 2012 smartphone. The API response must be compact (no unnecessary fields), artwork URLs must resolve to pre-sized images (no client-side resizing), and the client must render from cache first, always.

3. **Provider token management.** This is the most security-sensitive and operationally fragile part of the system. Tokens expire, providers revoke them, rate limits vary. Build robust refresh logic, per-provider circuit breakers, and clear user-facing messaging when a provider link needs re-authentication.

**What I would not invest in early:** ML-heavy recommendation (the heuristic will outperform any model trained on sparse early data), a custom design system for TV (use platform conventions — Roku users expect Roku-like UI), or multi-region deployment (US-only at launch, single region is fine).

**The 18-month litmus test:** If Channel Stream reaches 2M MAU, the first service extraction will be sports (bursty, independent data model). The second will be recommendation serving (compute-intensive, benefits from GPU sidecar). The feed orchestrator and provider integration layer should stay monolithic until at least 5M MAU. If you're extracting services before 500K MAU, you're optimizing prematurely.

---

*This document should be treated as a living artifact. Review quarterly against actual traffic patterns and operational pain points. The best architecture is the one that ships and survives contact with real users.*
