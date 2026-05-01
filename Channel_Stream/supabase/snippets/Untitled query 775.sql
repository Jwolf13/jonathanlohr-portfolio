SELECT id, sport, league, home_team_abbr, away_team_abbr, status, broadcast
FROM sports_events
WHERE start_time >= now() - interval '3 hours'
  AND start_time <= now() + interval '24 hours'
  AND status != 'final'
ORDER BY start_time ASC
LIMIT 10;