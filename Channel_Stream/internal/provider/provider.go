package provider

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/jwolf13/channel-stream/internal/db"
	"github.com/jwolf13/channel-stream/internal/feed"
)

// GetLinkedProviders handles GET /v1/providers/linked
func GetLinkedProviders(w http.ResponseWriter, r *http.Request) {
	accountID := r.URL.Query().Get("account_id")
	if accountID == "" {
		accountID = "00000000-0000-0000-0000-000000000001"
	}

	rows, err := db.Pool.Query(context.Background(), `
        SELECT
            provider,
            linked_at,
            token_expires,
            CASE
                WHEN token_expires IS NULL THEN 'never_expires'
                WHEN token_expires < now() THEN 'expired'
                WHEN token_expires < now() + interval '7 days' THEN 'expiring_soon'
                ELSE 'valid'
            END AS status
        FROM provider_links
        WHERE account_id = $1
        ORDER BY provider
    `, accountID)

	if err != nil {
		http.Error(w, "database error", http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var links []feed.ProviderLink
	for rows.Next() {
		var link feed.ProviderLink
		var tokenExpires *time.Time // pointer = nullable

		err := rows.Scan(
			&link.Provider,
			&link.LinkedAt,
			&tokenExpires,
			&link.Status,
		)
		if err != nil {
			http.Error(w, "scan error", http.StatusInternalServerError)
			return
		}
		link.TokenExpires = tokenExpires
		links = append(links, link)
	}

	type ProvidersResponse struct {
		AccountID string              `json:"account_id"`
		Providers []feed.ProviderLink `json:"providers"`
		Count     int                 `json:"count"`
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(ProvidersResponse{
		AccountID: accountID,
		Providers: links,
		Count:     len(links),
	})
}
