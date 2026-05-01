// Package ingestion polls the ESPN unofficial API and writes game data into
// sports_events. It runs as a background goroutine inside the main server.
package ingestion

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/jwolf13/channel-stream/internal/db"
)

// ── ESPN API response types ───────────────────────────────────────────────────
// These mirror the JSON shape returned by ESPN's scoreboard endpoints.
// Unexported because callers only interact with the DB, not these raw structs.

type espnResponse struct {
	Events []espnEvent `json:"events"`
}

type espnEvent struct {
	ID           string           `json:"id"`
	Date         string           `json:"date"`
	Name         string           `json:"name"`
	ShortName    string           `json:"shortName"`
	Competitions []espnCompetition `json:"competitions"`
}

type espnCompetition struct {
	ID          string           `json:"id"`
	Status      espnStatus       `json:"status"`
	Competitors []espnCompetitor `json:"competitors"`
	Broadcasts  []espnBroadcast  `json:"broadcasts"`
	Venue       struct {
		FullName string `json:"fullName"`
	} `json:"venue"`
}

type espnStatus struct {
	DisplayClock string        `json:"displayClock"`
	Period       int           `json:"period"`
	Type         espnStatusType `json:"type"`
}

type espnStatusType struct {
	Name      string `json:"name"`  // STATUS_IN_PROGRESS, STATUS_FINAL, STATUS_SCHEDULED
	Detail    string `json:"detail"` // "Q4 2:34", "Bot 6th", "Final"
	State     string `json:"state"`  // "pre", "in", "post"
	Completed bool   `json:"completed"`
}

type espnCompetitor struct {
	HomeAway    string   `json:"homeAway"` // "home" or "away"
	Score       string   `json:"score"`
	Team        espnTeam `json:"team"`
	CuratedRank struct {
		Current int `json:"current"` // AP ranking; 99 = unranked
	} `json:"curatedRank"`
}

type espnTeam struct {
	ID               string `json:"id"`
	Abbreviation     string `json:"abbreviation"`
	DisplayName      string `json:"displayName"`
	ShortDisplayName string `json:"shortDisplayName"`
}

type espnBroadcast struct {
	Market string   `json:"market"`
	Names  []string `json:"names"`
}

// ── Sport config ──────────────────────────────────────────────────────────────

type sportConfig struct {
	Sport  string // "football", "basketball", etc.
	League string // ESPN league slug: "nfl", "college-football", etc.
	Label  string // human-readable for log messages
}

// allSports is the full list of sports Channel Stream ingests.
var allSports = []sportConfig{
	{"football", "nfl", "NFL"},
	{"football", "college-football", "College Football"},
	{"basketball", "nba", "NBA"},
	{"basketball", "mens-college-basketball", "College Basketball"},
	{"baseball", "mlb", "MLB"},
	{"baseball", "college-baseball", "College Baseball"},
	{"hockey", "nhl", "NHL"},
	{"soccer", "usa.1", "MLS"},
}

// ── Worker entrypoint ─────────────────────────────────────────────────────────

// StartSportsWorker seeds broadcast mappings, then polls ESPN every 60 seconds
// for live/today games and every 10 minutes for the upcoming 3-day schedule.
// Call this in a goroutine: go ingestion.StartSportsWorker(ctx)
func StartSportsWorker(ctx context.Context) {
	log.Println("Sports ingestion worker starting…")

	// Remove placeholder seed rows — real ESPN data replaces them.
	if _, err := db.Pool.Exec(ctx, `DELETE FROM sports_events WHERE id LIKE '%_seed_%'`); err != nil {
		log.Printf("Warning: seed cleanup failed: %v", err)
	} else {
		log.Println("Cleared seed placeholder rows")
	}

	if err := SeedBroadcastMappings(ctx); err != nil {
		log.Printf("Warning: broadcast seed failed: %v", err)
	}
	if err := LoadMappings(ctx); err != nil {
		log.Printf("Warning: broadcast cache load failed: %v", err)
	}

	// Fetch immediately so the API serves real data from the first request.
	fetchAll(ctx, 0)
	fetchAll(ctx, 1)
	fetchAll(ctx, 2)

	liveTicker     := time.NewTicker(60 * time.Second)
	scheduleTicker := time.NewTicker(10 * time.Minute)
	defer liveTicker.Stop()
	defer scheduleTicker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("Sports ingestion worker stopped")
			return
		case <-liveTicker.C:
			fetchAll(ctx, 0) // today — keep live scores fresh
		case <-scheduleTicker.C:
			fetchAll(ctx, 1) // tomorrow
			fetchAll(ctx, 2) // day after
		}
	}
}

// fetchAll fetches all sports for a given day offset (0=today, 1=tomorrow…).
func fetchAll(ctx context.Context, dayOffset int) {
	date := time.Now().AddDate(0, 0, dayOffset).Format("20060102")
	for _, sport := range allSports {
		if err := fetchAndUpsert(ctx, sport, date); err != nil {
			log.Printf("ingestion %s (%s): %v", sport.Label, date, err)
		}
	}
}

// ── Fetch and upsert ──────────────────────────────────────────────────────────

func fetchAndUpsert(ctx context.Context, sport sportConfig, date string) error {
	url := fmt.Sprintf(
		"https://site.api.espn.com/apis/site/v2/sports/%s/%s/scoreboard?dates=%s&limit=100",
		sport.Sport, sport.League, date,
	)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", "ChannelStream/1.0")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("ESPN returned %d for %s", resp.StatusCode, sport.Label)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}

	var result espnResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return fmt.Errorf("parse: %w", err)
	}

	for _, event := range result.Events {
		if err := upsertEvent(ctx, sport, event); err != nil {
			log.Printf("  upsert %s %s: %v", sport.Label, event.ID, err)
		}
	}
	return nil
}

func upsertEvent(ctx context.Context, sport sportConfig, event espnEvent) error {
	if len(event.Competitions) == 0 {
		return nil
	}
	comp := event.Competitions[0]

	// ── Teams ─────────────────────────────────────────────────────────────────
	var home, away espnCompetitor
	for _, c := range comp.Competitors {
		if c.HomeAway == "home" {
			home = c
		} else {
			away = c
		}
	}

	// ── Status ────────────────────────────────────────────────────────────────
	status := mapStatus(comp.Status.Type.State, comp.Status.Type.Completed)

	// ── Broadcast networks ────────────────────────────────────────────────────
	// Collect unique national broadcast names; skip local/regional markets.
	seen := map[string]bool{}
	var networks []string
	for _, b := range comp.Broadcasts {
		if strings.ToLower(b.Market) == "local" {
			continue
		}
		for _, name := range b.Names {
			if !seen[name] {
				seen[name] = true
				networks = append(networks, name)
			}
		}
	}
	broadcastJSON, _ := json.Marshal(networks)

	// ── Score (only meaningful once a game starts) ────────────────────────────
	var scoreJSON []byte
	if status == "live" || status == "final" {
		score := map[string]string{"home": home.Score, "away": away.Score}
		scoreJSON, _ = json.Marshal(score)
	}

	// ── Start time ────────────────────────────────────────────────────────────
	// ESPN omits seconds in their date strings ("2026-05-01T01:30Z"), which
	// fails Go's strict RFC3339 parser. Try progressively looser formats.
	startTime, err := time.Parse(time.RFC3339, event.Date)
	if err != nil {
		startTime, err = time.Parse("2006-01-02T15:04Z", event.Date)
	}
	if err != nil {
		startTime, err = time.Parse("2006-01-02T15:04:05Z", event.Date)
	}
	if err != nil {
		startTime = time.Now()
		log.Printf("  warn: could not parse date %q for event %s", event.Date, event.ID)
	}

	// ESPN IDs are scoped per league. Prefix to guarantee global uniqueness.
	gameID := sport.League + "_" + event.ID

	_, err = db.Pool.Exec(ctx, `
		INSERT INTO sports_events (
			id, sport, league,
			home_team_id, home_team_name, home_team_abbr,
			away_team_id, away_team_name, away_team_abbr,
			start_time, status,
			period_display, clock_display,
			score, broadcast, venue,
			updated_at
		) VALUES (
			$1, $2, $3,
			$4, $5, $6,
			$7, $8, $9,
			$10, $11,
			$12, $13,
			$14, $15, $16,
			now()
		)
		ON CONFLICT (id) DO UPDATE SET
			start_time     = EXCLUDED.start_time,
			status         = EXCLUDED.status,
			period_display = EXCLUDED.period_display,
			clock_display  = EXCLUDED.clock_display,
			score          = EXCLUDED.score,
			broadcast      = EXCLUDED.broadcast,
			updated_at     = now()
	`,
		gameID, sport.Sport, sport.League,
		home.Team.ID, home.Team.DisplayName, home.Team.Abbreviation,
		away.Team.ID, away.Team.DisplayName, away.Team.Abbreviation,
		startTime, status,
		comp.Status.Type.Detail, comp.Status.DisplayClock,
		scoreJSON, broadcastJSON, comp.Venue.FullName,
	)
	return err
}

// mapStatus converts ESPN's state/completed fields into our three-value status.
func mapStatus(state string, completed bool) string {
	if completed || state == "post" {
		return "final"
	}
	if state == "in" {
		return "live"
	}
	return "scheduled"
}
