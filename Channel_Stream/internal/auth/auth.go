// Package auth validates Cognito access tokens by calling the Cognito
// userInfo endpoint. Tokens are cached for 5 minutes to avoid repeated calls.
package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

// UserInfo is the decoded identity from the Cognito userInfo endpoint.
type UserInfo struct {
	Sub   string `json:"sub"`
	Email string `json:"email"`
	Name  string `json:"name"`
}

type cacheEntry struct {
	info    UserInfo
	expires time.Time
}

var (
	mu         sync.Mutex
	tokenCache = map[string]cacheEntry{}
)

func cognitoDomain() string {
	if d := os.Getenv("COGNITO_DOMAIN"); d != "" {
		return d
	}
	return "https://channel-stream-jl.auth.us-east-1.amazoncognito.com"
}

// ValidateToken calls Cognito's /oauth2/userInfo endpoint.
// Valid tokens are cached for 5 minutes to avoid hammering Cognito.
func ValidateToken(ctx context.Context, token string) (UserInfo, error) {
	mu.Lock()
	if entry, ok := tokenCache[token]; ok && time.Now().Before(entry.expires) {
		mu.Unlock()
		return entry.info, nil
	}
	mu.Unlock()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet,
		cognitoDomain()+"/oauth2/userInfo", nil)
	if err != nil {
		return UserInfo{}, err
	}
	req.Header.Set("Authorization", "Bearer "+token)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return UserInfo{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return UserInfo{}, fmt.Errorf("invalid token: status %d", resp.StatusCode)
	}

	var info UserInfo
	if err := json.NewDecoder(resp.Body).Decode(&info); err != nil {
		return UserInfo{}, err
	}

	mu.Lock()
	tokenCache[token] = cacheEntry{info: info, expires: time.Now().Add(5 * time.Minute)}
	mu.Unlock()

	return info, nil
}

// BearerToken extracts the token from an "Authorization: Bearer <token>" header.
func BearerToken(r *http.Request) string {
	h := r.Header.Get("Authorization")
	if !strings.HasPrefix(h, "Bearer ") {
		return ""
	}
	return strings.TrimPrefix(h, "Bearer ")
}
