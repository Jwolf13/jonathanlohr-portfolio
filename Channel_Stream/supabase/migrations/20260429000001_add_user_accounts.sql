-- User accounts linked to Cognito identities.
-- cognito_sub is the unique identifier from Google/Cognito ("sub" JWT claim).
-- preferences stores selected teams as JSON: { "teams": ["LAL", "LAD"] }
CREATE TABLE IF NOT EXISTS user_accounts (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub TEXT        UNIQUE NOT NULL,
    email       TEXT,
    preferences JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_accounts_cognito_sub ON user_accounts(cognito_sub);
