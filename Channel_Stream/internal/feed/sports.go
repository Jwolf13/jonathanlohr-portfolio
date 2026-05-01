package feed

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sort"
	"time"

	"github.com/jwolf13/channel-stream/internal/cache"
	"github.com/jwolf13/channel-stream/internal/db"
	"github.com/jwolf13/channel-stream/internal/ingestion"
)

// GetSportsLive handles GET /v1/sports/live
// Returns live games and today's upcoming games for the profile's followed teams.
func GetSportsLive(w http.ResponseWriter, r *http.Request) {
	profileID := r.URL.Query().Get("profile_id")
	if profileID == "" {
		profileID = "00000000-0000-0000-0000-000000000002"
	}

	// ── Cache check ───────────────────────────────────────────────────────────
	cacheKey := cache.SportsKey(profileID)
	if cached, found, _ := cache.Get(r.Context(), cacheKey); found {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-Cache", "HIT")
		fmt.Fprint(w, cached)
		return
	}

	followedTeams, followedLeagues := profilePreferences(r.Context(), profileID)

	events, err := querySportsEvents(r.Context(), followedTeams, followedLeagues, 0, 1)
	if err != nil {
		http.Error(w, "database error", http.StatusInternalServerError)
		return
	}

	response := SportsResponse{
		Feed:        "sports_live",
		GeneratedAt: time.Now().UTC(),
		Events:      events,
		Count:       len(events),
	}

	if b, err := json.Marshal(response); err == nil {
		cache.Set(r.Context(), cacheKey, string(b), cache.TTLSportsLive)
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache", "MISS")
	json.NewEncoder(w).Encode(response)
}

// GetSportsSchedule handles GET /v1/sports/schedule
// Returns all non-final games for the next 7 days for the profile's followed teams.
func GetSportsSchedule(w http.ResponseWriter, r *http.Request) {
	profileID := r.URL.Query().Get("profile_id")
	if profileID == "" {
		profileID = "00000000-0000-0000-0000-000000000002"
	}

	cacheKey := cache.FeedKey(profileID, "sports_schedule")
	if cached, found, _ := cache.Get(r.Context(), cacheKey); found {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-Cache", "HIT")
		fmt.Fprint(w, cached)
		return
	}

	followedTeams, followedLeagues := profilePreferences(r.Context(), profileID)

	events, err := querySportsEvents(r.Context(), followedTeams, followedLeagues, 0, 7)
	if err != nil {
		http.Error(w, "database error", http.StatusInternalServerError)
		return
	}

	response := SportsResponse{
		Feed:        "sports_schedule",
		GeneratedAt: time.Now().UTC(),
		Events:      events,
		Count:       len(events),
	}

	if b, err := json.Marshal(response); err == nil {
		// Schedule data is less time-sensitive than live scores
		cache.Set(r.Context(), cacheKey, string(b), cache.TTLUpNext)
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache", "MISS")
	json.NewEncoder(w).Encode(response)
}

// ── Shared query ──────────────────────────────────────────────────────────────

// querySportsEvents fetches events from the DB, enriches them with WatchOn,
// and returns them sorted: live first, then by start_time ascending.
// startDayOffset / endDayOffset are offsets from today (0 = today).
func querySportsEvents(
	ctx context.Context,
	followedTeams []string,
	followedLeagues []string,
	startDayOffset, endDayOffset int,
) ([]SportEventEnriched, error) {

	// Window: from a few hours ago (to catch games already in progress at page load)
	// through the end of the endDay window.
	windowStart := time.Now().AddDate(0, 0, startDayOffset).Truncate(24*time.Hour).Add(-3 * time.Hour)
	windowEnd   := time.Now().AddDate(0, 0, endDayOffset).Add(24 * time.Hour)

	rows, err := db.Pool.Query(ctx, `
		SELECT
			id, sport, league,
			home_team_id, COALESCE(home_team_name,''), COALESCE(home_team_abbr,''),
			away_team_id, COALESCE(away_team_name,''), COALESCE(away_team_abbr,''),
			start_time, status,
			COALESCE(period_display,''), COALESCE(clock_display,''),
			score, COALESCE(broadcast,'[]'::jsonb),
			COALESCE(venue,'')
		FROM sports_events
		WHERE start_time >= $1
		  AND start_time <= $2
		  AND status != 'final'
		  AND (
		      -- No preferences = show everything
		      ($3::text[] IS NULL OR cardinality($3::text[]) = 0 OR
		          home_team_abbr = ANY($3::text[]) OR away_team_abbr = ANY($3::text[]))
		      AND
		      ($4::text[] IS NULL OR cardinality($4::text[]) = 0 OR
		          league = ANY($4::text[]))
		  )
		ORDER BY
			CASE status WHEN 'live' THEN 0 WHEN 'scheduled' THEN 1 ELSE 2 END,
			start_time ASC
		LIMIT 100
	`, windowStart, windowEnd, followedTeams, followedLeagues)

	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var events []SportEventEnriched
	for rows.Next() {
		var (
			e            SportEventEnriched
			scoreJSON    []byte
			broadcastJSON []byte
		)
		err := rows.Scan(
			&e.GameID, &e.Sport, &e.League,
			&e.HomeTeam.ID, &e.HomeTeam.Name, &e.HomeTeam.Abbr,
			&e.AwayTeam.ID, &e.AwayTeam.Name, &e.AwayTeam.Abbr,
			&e.StartTime, &e.Status,
			&e.StatusDetail, // period_display serves as status_detail
			new(string),     // clock_display — absorbed into status_detail from ESPN
			&scoreJSON, &broadcastJSON,
			&e.Venue,
		)
		if err != nil {
			return nil, err
		}

		// Parse score
		if len(scoreJSON) > 0 && string(scoreJSON) != "null" {
			var gs GameScore
			if json.Unmarshal(scoreJSON, &gs) == nil {
				e.Score = &gs
			}
		}

		// Parse broadcast networks and enrich with WatchOn
		e.WatchOn = buildWatchOn(broadcastJSON)

		events = append(events, e)
	}

	if rows.Err() != nil {
		return nil, rows.Err()
	}

	return events, nil
}

// buildWatchOn converts a JSON array of network names (["ESPN","ABC"]) into
// a sorted list of WatchOption structs using the in-memory broadcast mapping cache.
func buildWatchOn(broadcastJSON []byte) []WatchOption {
	var networks []string
	if err := json.Unmarshal(broadcastJSON, &networks); err != nil {
		return nil
	}

	seen := map[string]bool{}
	var opts []WatchOption
	for _, network := range networks {
		m, ok := ingestion.LookupMapping(network)
		if !ok {
			// Unknown network — surface it anyway with no app
			opts = append(opts, WatchOption{
				Network:   network,
				AppDisplay: network,
			})
			continue
		}
		// Deduplicate by streaming app (ESPN and ESPN2 both map to Disney+)
		dedupeKey := m.AppDisplay
		if seen[dedupeKey] {
			continue
		}
		seen[dedupeKey] = true
		opts = append(opts, WatchOption{
			Network:      network,
			App:          m.StreamingApp,
			AppDisplay:   m.AppDisplay,
			RequiresCable: m.RequiresCable,
		})
	}

	// Streaming options first, then cable-only
	sort.Slice(opts, func(i, j int) bool {
		if opts[i].RequiresCable != opts[j].RequiresCable {
			return !opts[i].RequiresCable
		}
		mi, _ := ingestion.LookupMapping(opts[i].Network)
		mj, _ := ingestion.LookupMapping(opts[j].Network)
		return mi.SortOrder < mj.SortOrder
	})

	return opts
}

// profilePreferences reads the profile's followed_teams and followed_leagues
// from the preferences JSONB column. Returns empty slices if the profile
// has no preferences — the query then returns all games.
func profilePreferences(ctx context.Context, profileID string) (teams []string, leagues []string) {
	var prefJSON []byte
	err := db.Pool.QueryRow(ctx,
		`SELECT COALESCE(preferences, '{}') FROM profiles WHERE id = $1`,
		profileID,
	).Scan(&prefJSON)
	if err != nil {
		return nil, nil
	}

	var prefs struct {
		FollowedTeams   []string `json:"followed_teams"`
		FollowedLeagues []string `json:"followed_leagues"`
		// Legacy field name from initial seed data
		Teams []string `json:"teams"`
	}
	if err := json.Unmarshal(prefJSON, &prefs); err != nil {
		return nil, nil
	}

	// Support both "followed_teams" (new) and "teams" (legacy seed data)
	teams = prefs.FollowedTeams
	if len(teams) == 0 {
		teams = prefs.Teams
	}
	leagues = prefs.FollowedLeagues
	return teams, leagues
}
