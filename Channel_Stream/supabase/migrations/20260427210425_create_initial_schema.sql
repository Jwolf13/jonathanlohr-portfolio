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
