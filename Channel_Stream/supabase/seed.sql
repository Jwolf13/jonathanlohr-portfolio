-- ─── 1. TEST ACCOUNT ────────────────────────────────────────
INSERT INTO accounts (id, email) VALUES
    ('00000000-0000-0000-0000-000000000001', 'jon@test.com');


-- ─── 2. TEST PROFILE ────────────────────────────────────────
-- followed_teams uses ESPN team abbreviations (LAL, LAD, LAR)
-- followed_leagues uses ESPN league slugs (nba, mlb, nfl)
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
-- The ingestion worker overwrites these rows on first run.
-- These seeds give the API real data to return before ESPN is polled.
INSERT INTO sports_events (
    id, sport, league,
    home_team_id, home_team_name, home_team_abbr,
    away_team_id, away_team_name, away_team_abbr,
    start_time, status,
    period_display, clock_display,
    score, broadcast, venue
) VALUES
    ('nba_seed_lal_bos', 'basketball', 'nba',
     '6', 'Los Angeles Lakers', 'LAL',
     '2', 'Boston Celtics',     'BOS',
     now() + interval '2 hours', 'scheduled',
     '', '',
     null, '["ESPN"]'::jsonb, 'Crypto.com Arena'),

    ('mlb_seed_lad_sfg', 'baseball', 'mlb',
     '19', 'Los Angeles Dodgers', 'LAD',
     '26', 'San Francisco Giants', 'SF',
     now() - interval '1 hour', 'live',
     'Bot 6th', '0:00',
     '{"home": "4", "away": "2"}'::jsonb, '["Apple TV+"]'::jsonb, 'Dodger Stadium'),

    ('nfl_seed_kc_buf', 'football', 'nfl',
     '12', 'Kansas City Chiefs', 'KC',
     '2', 'Buffalo Bills', 'BUF',
     now() + interval '3 days', 'scheduled',
     '', '',
     null, '["CBS", "Paramount+"]'::jsonb, 'Arrowhead Stadium');


-- ─── 8. INTERACTION EVENTS ──────────────────────────────────
INSERT INTO interactions (profile_id, content_id, action, context) VALUES
    ('00000000-0000-0000-0000-000000000002', 'cs_severance_s3e02', 'click',    '{"feed": "up_next",   "position": 1}'),
    ('00000000-0000-0000-0000-000000000002', 'cs_dune2',           'complete', '{"feed": "watch_now", "position": 3}'),
    ('00000000-0000-0000-0000-000000000002', 'cs_3body',           'dismiss',  '{"feed": "watch_now", "position": 5}'),
    ('00000000-0000-0000-0000-000000000002', 'cs_fallout',         'save',     '{"feed": "watch_now", "position": 7}');