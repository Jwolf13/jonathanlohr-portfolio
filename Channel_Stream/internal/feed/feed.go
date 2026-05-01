package feed

import "time"

// FeedItem represents one piece of content in any feed.
// Think of this as the "shape" of data we return to clients.
//
// The `json:"..."` tags tell Go how to serialize this struct to JSON.
// Go field names are PascalCase (ContentID), JSON keys are snake_case (content_id).
type FeedItem struct {
	ContentID         string     `json:"content_id"`
	Title             string     `json:"title"`
	Type              string     `json:"type"`
	Provider          string     `json:"provider"`
	ProgressPct       int        `json:"progress_pct,omitempty"` // omitempty: skip if 0
	ResumePositionSec int        `json:"resume_position_sec,omitempty"`
	Rating            string     `json:"rating,omitempty"`
	Deeplink          string     `json:"deeplink,omitempty"`
	LastWatched       *time.Time `json:"last_watched,omitempty"` // pointer = nullable
	Score             float64    `json:"score,omitempty"`
	Reason            string     `json:"reason,omitempty"` // "continue_watching", "genre_match", etc.
}

// FeedResponse is the wrapper around a list of FeedItems.
// This is what the API actually returns.
type FeedResponse struct {
	Feed        string     `json:"feed"` // "watch_now", "up_next", "sports_live"
	GeneratedAt time.Time  `json:"generated_at"`
	Items       []FeedItem `json:"items"`
	Count       int        `json:"count"`
}

// SportEvent represents a live or scheduled game.
type SportEvent struct {
	GameID    string      `json:"game_id"`
	League    string      `json:"league"`
	Matchup   string      `json:"matchup"` // "lakers vs celtics"
	Status    string      `json:"status"`  // "live", "scheduled", "final"
	StartTime time.Time   `json:"start_time"`
	Score     any `json:"score,omitempty"`
	Broadcast any `json:"broadcast,omitempty"`
}

// ProviderLink represents a linked streaming service.
type ProviderLink struct {
	Provider     string     `json:"provider"`
	LinkedAt     time.Time  `json:"linked_at"`
	TokenExpires *time.Time `json:"token_expires,omitempty"`
	Status       string     `json:"status"` // "valid", "expired", "expiring_soon"
}

// ── Sports (enriched) ─────────────────────────────────────────────────────────

// WatchOption describes one way to watch a game (one streaming app or cable network).
type WatchOption struct {
	Network      string `json:"network"`
	App          string `json:"app,omitempty"`      // streaming app slug, empty = cable only
	AppDisplay   string `json:"app_display"`
	RequiresCable bool  `json:"requires_cable"`
}

// TeamInfo is the minimal team representation returned to clients.
type TeamInfo struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Abbr string `json:"abbr"`
}

// GameScore holds the current or final score for a game.
type GameScore struct {
	Home string `json:"home"`
	Away string `json:"away"`
}

// SportEventEnriched is the response shape for each game in the sports feed.
type SportEventEnriched struct {
	GameID       string        `json:"game_id"`
	Sport        string        `json:"sport"`
	League       string        `json:"league"`
	HomeTeam     TeamInfo      `json:"home_team"`
	AwayTeam     TeamInfo      `json:"away_team"`
	StartTime    time.Time     `json:"start_time"`
	Status       string        `json:"status"`
	StatusDetail string        `json:"status_detail,omitempty"` // "Q4 2:34", "Bot 6th", "Final"
	Score        *GameScore    `json:"score,omitempty"`
	Venue        string        `json:"venue,omitempty"`
	WatchOn      []WatchOption `json:"watch_on"`
}

// SportsResponse is the top-level response for all sports endpoints.
type SportsResponse struct {
	Feed        string               `json:"feed"`
	GeneratedAt time.Time            `json:"generated_at"`
	Events      []SportEventEnriched `json:"events"`
	Count       int                  `json:"count"`
}
