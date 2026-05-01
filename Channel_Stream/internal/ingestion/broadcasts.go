package ingestion

import (
	"context"
	"log"
	"sync"

	"github.com/jwolf13/channel-stream/internal/db"
)

// BroadcastMapping maps a broadcast network name to a streaming app.
type BroadcastMapping struct {
	StreamingApp  string // empty = cable/satellite only
	AppDisplay    string
	RequiresCable bool
	SortOrder     int
}

var (
	mappingMu    sync.RWMutex
	mappingCache = map[string]BroadcastMapping{}
)

// LookupMapping returns the streaming app for a broadcast network name.
// Returns zero value and false if the network is unknown.
func LookupMapping(network string) (BroadcastMapping, bool) {
	mappingMu.RLock()
	defer mappingMu.RUnlock()
	m, ok := mappingCache[network]
	return m, ok
}

// staticMappings is the source of truth. Update when rights deals change.
// sort_order: lower = show this option first in watch_on arrays.
var staticMappings = []struct {
	Network      string
	App          string
	Display      string
	Cable        bool
	Sort         int
}{
	// ── ESPN family → Disney+ ─────────────────────────────────────────────────
	{"ESPN", "disney_plus", "Disney+ (ESPN)", false, 1},
	{"ESPN2", "disney_plus", "Disney+ (ESPN2)", false, 2},
	{"ESPNU", "disney_plus", "Disney+ (ESPNU)", false, 3},
	{"ESPN+", "disney_plus", "Disney+ (ESPN+)", false, 4},
	{"SEC Network", "disney_plus", "Disney+ (SEC Network)", false, 5},
	{"ACC Network", "disney_plus", "Disney+ (ACC Network)", false, 6},
	{"ACC Network Extra", "disney_plus", "Disney+ (ACC Network)", false, 7},
	{"Big 12 Now", "disney_plus", "Disney+ (Big 12 Now)", false, 8},
	{"ESPNEWS", "disney_plus", "Disney+ (ESPNEWS)", false, 9},
	{"ESPN Deportes", "disney_plus", "Disney+ (ESPN Deportes)", false, 10},
	// ABC counts as Disney+ on streaming
	{"ABC", "disney_plus", "Disney+ (ABC)", false, 1},

	// ── NBC family → Peacock ──────────────────────────────────────────────────
	{"NBC", "peacock", "Peacock", false, 1},
	{"Peacock", "peacock", "Peacock", false, 1},
	{"Big Ten Network", "peacock", "Peacock (Big Ten Network)", false, 2},
	{"NBCSN", "peacock", "Peacock", false, 3}, // legacy, still appears in data

	// ── CBS family → Paramount+ ───────────────────────────────────────────────
	{"CBS", "paramount_plus", "Paramount+", false, 1},
	{"CBS Sports Network", "paramount_plus", "Paramount+", false, 2},
	{"Paramount+", "paramount_plus", "Paramount+", false, 1},

	// ── Turner / Warner → Max ─────────────────────────────────────────────────
	{"TNT", "max", "Max (TNT)", false, 1},
	{"TBS", "max", "Max (TBS)", false, 2},
	{"truTV", "max", "Max (truTV)", false, 3},

	// ── Amazon ────────────────────────────────────────────────────────────────
	{"Prime Video", "prime_video", "Prime Video", false, 1},
	{"Amazon", "prime_video", "Prime Video", false, 1},

	// ── Apple TV+ ─────────────────────────────────────────────────────────────
	{"Apple TV+", "apple_tv_plus", "Apple TV+", false, 1},
	// MLS Season Pass lives inside Apple TV+
	{"MLS Season Pass", "apple_tv_plus", "Apple TV+ (MLS Season Pass)", false, 1},

	// ── YouTube ───────────────────────────────────────────────────────────────
	{"NFL Sunday Ticket", "youtube_tv", "YouTube TV / Primetime Channels", false, 1},
	{"YouTube TV", "youtube_tv", "YouTube TV", false, 1},

	// ── Cable/satellite only (no direct streaming app) ────────────────────────
	{"FOX", "", "Fox (cable/satellite or local OTA)", true, 1},
	{"FS1", "", "FS1 (cable/satellite)", true, 2},
	{"FS2", "", "FS2 (cable/satellite)", true, 3},
	{"NFL Network", "", "NFL Network (cable/satellite)", true, 1},
	{"MLB Network", "", "MLB Network (cable/satellite)", true, 1},
	{"NBA TV", "", "NBA TV (cable/satellite)", true, 1},
	{"NHL Network", "", "NHL Network (cable/satellite)", true, 1},
	{"TUDN", "", "TUDN (cable/satellite)", true, 1},
	{"UniMás", "", "UniMás (cable/satellite)", true, 1},
	{"Univision", "", "Univision (cable/satellite)", true, 1},
	{"CW", "", "The CW (free OTA/app)", false, 3},
	{"Ion", "", "Ion (free OTA)", false, 5},
	{"USA Network", "peacock", "Peacock (USA Network)", false, 3},
}

// SeedBroadcastMappings writes staticMappings into the broadcast_mappings table.
// Uses INSERT … ON CONFLICT DO UPDATE so it's safe to call on every startup.
func SeedBroadcastMappings(ctx context.Context) error {
	for _, m := range staticMappings {
		app := &m.App
		if m.App == "" {
			app = nil
		}
		_, err := db.Pool.Exec(ctx, `
			INSERT INTO broadcast_mappings (network, streaming_app, app_display, requires_cable, sort_order)
			VALUES ($1, $2, $3, $4, $5)
			ON CONFLICT (network) DO UPDATE SET
				streaming_app  = EXCLUDED.streaming_app,
				app_display    = EXCLUDED.app_display,
				requires_cable = EXCLUDED.requires_cable,
				sort_order     = EXCLUDED.sort_order
		`, m.Network, app, m.Display, m.Cable, m.Sort)
		if err != nil {
			return err
		}
	}
	log.Printf("✓ Seeded %d broadcast mappings", len(staticMappings))
	return nil
}

// LoadMappings reads broadcast_mappings from the DB into the in-memory cache.
// Called once at startup after seeding. The handler uses the cache directly
// so it never hits the DB for every broadcast lookup.
func LoadMappings(ctx context.Context) error {
	rows, err := db.Pool.Query(ctx, `
		SELECT network, COALESCE(streaming_app,''), app_display, requires_cable, sort_order
		FROM broadcast_mappings
	`)
	if err != nil {
		return err
	}
	defer rows.Close()

	fresh := map[string]BroadcastMapping{}
	for rows.Next() {
		var network string
		var m BroadcastMapping
		if err := rows.Scan(&network, &m.StreamingApp, &m.AppDisplay, &m.RequiresCable, &m.SortOrder); err != nil {
			return err
		}
		fresh[network] = m
	}

	mappingMu.Lock()
	mappingCache = fresh
	mappingMu.Unlock()

	log.Printf("✓ Loaded %d broadcast mappings into cache", len(fresh))
	return nil
}
