-- Sports pivot: add columns for ESPN ingestion data and broadcast mappings table.

-- ── 1. Extend sports_events ───────────────────────────────────────────────────
ALTER TABLE sports_events
    ADD COLUMN IF NOT EXISTS sport           TEXT,
    ADD COLUMN IF NOT EXISTS home_team_name  TEXT,
    ADD COLUMN IF NOT EXISTS home_team_abbr  TEXT,
    ADD COLUMN IF NOT EXISTS away_team_name  TEXT,
    ADD COLUMN IF NOT EXISTS away_team_abbr  TEXT,
    ADD COLUMN IF NOT EXISTS period_display  TEXT,
    ADD COLUMN IF NOT EXISTS clock_display   TEXT,
    ADD COLUMN IF NOT EXISTS venue           TEXT;

-- broadcast is now a JSON array of network name strings: ["ESPN","ABC"]
-- (was {"providers":[...],"channels":[...]} — new ingestion writes the new format)

-- ── 2. Broadcast mappings ─────────────────────────────────────────────────────
-- Static lookup: broadcast network name → streaming app.
-- Updated manually when rights deals change (once or twice a year).
CREATE TABLE IF NOT EXISTS broadcast_mappings (
    network         TEXT PRIMARY KEY,
    streaming_app   TEXT,           -- NULL = cable/satellite only, no streaming option
    app_display     TEXT NOT NULL,
    requires_cable  BOOLEAN NOT NULL DEFAULT false,
    sort_order      INT NOT NULL DEFAULT 99  -- lower = prefer showing first
);

-- Index for fast team-based filtering on the new columns
CREATE INDEX IF NOT EXISTS idx_sports_home_abbr ON sports_events(home_team_abbr);
CREATE INDEX IF NOT EXISTS idx_sports_away_abbr ON sports_events(away_team_abbr);
CREATE INDEX IF NOT EXISTS idx_sports_league    ON sports_events(league);
CREATE INDEX IF NOT EXISTS idx_sports_sport     ON sports_events(sport);
