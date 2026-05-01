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

// GetWatchNow handles GET /v1/feed/watch-now
// Returns personalized content from the user's linked providers,
// excluding completed content, sorted by rating.
func GetWatchNow(w http.ResponseWriter, r *http.Request) {
	profileID := r.URL.Query().Get("profile_id")
	if profileID == "" {
		profileID = "00000000-0000-0000-0000-000000000002"
	}

	accountID := r.URL.Query().Get("account_id")
	if accountID == "" {
		accountID = "00000000-0000-0000-0000-000000000001"
	}

	// ── Cache check ──────────────────────────────────────────────────────────
	// Key includes both profile and account since results differ by provider links.
	cacheKey := cache.FeedKey(profileID, "watch_now")
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
            ca.provider,
            COALESCE(c.metadata->>'rating', '0') AS rating,
            COALESCE(ca.deeplink_tpl, '') AS deeplink
        FROM content c
        JOIN content_availability ca ON ca.content_id = c.id
        JOIN provider_links pl
            ON pl.provider = ca.provider
            AND pl.account_id = $2
        WHERE c.type IN ('series', 'movie')
          AND c.id NOT IN (
              SELECT content_id
              FROM watch_state
              WHERE profile_id = $1
                AND status = 'completed'
          )
        ORDER BY (c.metadata->>'rating')::FLOAT DESC NULLS LAST
        LIMIT 30
    `, profileID, accountID)

	if err != nil {
		http.Error(w, "database error", http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var items []FeedItem
	for rows.Next() {
		var item FeedItem
		err := rows.Scan(
			&item.ContentID,
			&item.Title,
			&item.Type,
			&item.Provider,
			&item.Rating,
			&item.Deeplink,
		)
		if err != nil {
			http.Error(w, "scan error", http.StatusInternalServerError)
			return
		}
		item.Score = 0.5
		item.Reason = "available_now"
		items = append(items, item)
	}

	if rows.Err() != nil {
		http.Error(w, "row iteration error", http.StatusInternalServerError)
		return
	}

	response := FeedResponse{
		Feed:        "watch_now",
		GeneratedAt: time.Now().UTC(),
		Items:       items,
		Count:       len(items),
	}

	// ── Store in cache ───────────────────────────────────────────────────────
	if b, err := json.Marshal(response); err == nil {
		cache.Set(r.Context(), cacheKey, string(b), cache.TTLWatchNow)
	}
	// ─────────────────────────────────────────────────────────────────────────

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache", "MISS")
	json.NewEncoder(w).Encode(response)
}
