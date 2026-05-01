// Package user handles user preference endpoints.
// GET  /v1/me/preferences — returns saved teams for the authenticated user
// PUT  /v1/me/preferences — saves teams for the authenticated user
package user

import (
	"encoding/json"
	"net/http"

	"github.com/jwolf13/channel-stream/internal/auth"
	"github.com/jwolf13/channel-stream/internal/db"
)

type Preferences struct {
	Teams []string `json:"teams"`
}

func GetPreferences(w http.ResponseWriter, r *http.Request) {
	token := auth.BearerToken(r)
	if token == "" {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	userInfo, err := auth.ValidateToken(r.Context(), token)
	if err != nil {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}

	var prefJSON []byte
	err = db.Pool.QueryRow(r.Context(),
		`SELECT COALESCE(preferences, '{}') FROM user_accounts WHERE cognito_sub = $1`,
		userInfo.Sub,
	).Scan(&prefJSON)

	w.Header().Set("Content-Type", "application/json")

	if err != nil {
		// No account yet — return empty preferences without erroring
		json.NewEncoder(w).Encode(Preferences{Teams: []string{}})
		return
	}

	// Return the raw JSONB — it's already {"teams":[...]}
	w.Write(prefJSON)
}

func PutPreferences(w http.ResponseWriter, r *http.Request) {
	token := auth.BearerToken(r)
	if token == "" {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	userInfo, err := auth.ValidateToken(r.Context(), token)
	if err != nil {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}

	var prefs Preferences
	if err := json.NewDecoder(r.Body).Decode(&prefs); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	if prefs.Teams == nil {
		prefs.Teams = []string{}
	}

	prefJSON, _ := json.Marshal(prefs)

	_, err = db.Pool.Exec(r.Context(), `
		INSERT INTO user_accounts (cognito_sub, email, preferences)
		VALUES ($1, $2, $3)
		ON CONFLICT (cognito_sub) DO UPDATE SET
			email       = EXCLUDED.email,
			preferences = EXCLUDED.preferences,
			updated_at  = now()
	`, userInfo.Sub, userInfo.Email, prefJSON)
	if err != nil {
		http.Error(w, "database error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(prefs)
}
