package feed

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/jwolf13/channel-stream/internal/cache"
	"github.com/jwolf13/channel-stream/internal/db"
)

// GetUpNext handles GET /v1/feed/up-next
// Returns all content the profile is currently watching, sorted by most recent.
func GetUpNext(w http.ResponseWriter, r *http.Request) {
	profileID := r.URL.Query().Get("profile_id")
	if profileID == "" {
		profileID = "00000000-0000-0000-0000-000000000002"
	}

	// ── Cache check ──────────────────────────────────────────────────────────
	// Pattern: check cache → return if found; otherwise query DB → store → return.
	cacheKey := cache.FeedKey(profileID, "up_next")
	if cached, found, _ := cache.Get(r.Context(), cacheKey); found {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-Cache", "HIT")
		fmt.Fprint(w, cached)
		return
	}
	// ─────────────────────────────────────────────────────────────────────────

	rows, err := db.Pool.Query(context.Background(), `
        SELECT
            c.id,
            c.title,
            c.type,
            ws.provider,
            ws.progress_pct,
            ws.position_sec,
            ws.last_watched,
            COALESCE(ca.deeplink_tpl, '') AS deeplink
        FROM watch_state ws
        JOIN content c ON c.id = ws.content_id
        LEFT JOIN content_availability ca
            ON ca.content_id = c.id
            AND ca.provider = ws.provider
        WHERE ws.profile_id = $1
          AND ws.status = 'in_progress'
        ORDER BY ws.last_watched DESC
        LIMIT 20
    `, profileID)

	if err != nil {
		http.Error(w, "database error", http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var items []FeedItem
	for rows.Next() {
		var item FeedItem
		var lastWatched time.Time

		err := rows.Scan(
			&item.ContentID,
			&item.Title,
			&item.Type,
			&item.Provider,
			&item.ProgressPct,
			&item.ResumePositionSec,
			&lastWatched,
			&item.Deeplink,
		)
		if err != nil {
			http.Error(w, "scan error", http.StatusInternalServerError)
			return
		}

		item.LastWatched = &lastWatched
		item.Reason = "continue_watching"
		items = append(items, item)
	}

	if rows.Err() != nil {
		http.Error(w, "row iteration error", http.StatusInternalServerError)
		return
	}

	response := FeedResponse{
		Feed:        "up_next",
		GeneratedAt: time.Now().UTC(),
		Items:       items,
		Count:       len(items),
	}

	// ── Store in cache ───────────────────────────────────────────────────────
	// Non-fatal: if marshalling or Set fails, we still return the response.
	if b, err := json.Marshal(response); err == nil {
		cache.Set(r.Context(), cacheKey, string(b), cache.TTLUpNext)
	}
	// ─────────────────────────────────────────────────────────────────────────

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache", "MISS")
	json.NewEncoder(w).Encode(response)
}
