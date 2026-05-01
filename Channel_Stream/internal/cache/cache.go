package cache

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/redis/go-redis/v9"
)

// Client is the global Redis connection. Nil when Redis is unavailable.
var Client *redis.Client

// TTL constants — shorter = fresher data but more DB load; longer = faster but stale.
const (
	TTLWatchNow   = 10 * time.Minute  // stable recommendations
	TTLUpNext     = 5 * time.Minute   // watch state changes more often
	TTLSportsLive = 90 * time.Second  // live scores need freshness
	TTLProviders  = 15 * time.Minute  // provider links rarely change
)

// Connect establishes the Redis connection. Returns an error but does not
// fatally crash — the API degrades gracefully to direct DB queries when Redis
// is unavailable.
func Connect() error {
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "redis://localhost:6379"
	}

	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		return fmt.Errorf("invalid REDIS_URL: %w", err)
	}

	Client = redis.NewClient(opt)

	if err := Client.Ping(context.Background()).Err(); err != nil {
		Client = nil // leave nil so all callers treat Redis as unavailable
		return fmt.Errorf("cannot connect to Redis: %w", err)
	}

	fmt.Println("✓ Connected to Redis")
	return nil
}

// Get retrieves a cached value. Returns ("", false, nil) when the key is
// missing or when Redis is unavailable — callers always fall through to the DB.
func Get(ctx context.Context, key string) (string, bool, error) {
	if Client == nil {
		return "", false, nil
	}
	val, err := Client.Get(ctx, key).Result()
	if err == redis.Nil {
		return "", false, nil
	}
	if err != nil {
		return "", false, err
	}
	return val, true, nil
}

// Set stores a value with a TTL. No-ops when Redis is unavailable.
func Set(ctx context.Context, key string, value string, ttl time.Duration) error {
	if Client == nil {
		return nil
	}
	return Client.Set(ctx, key, value, ttl).Err()
}

// Delete removes a key from cache. No-ops when Redis is unavailable.
func Delete(ctx context.Context, key string) error {
	if Client == nil {
		return nil
	}
	return Client.Del(ctx, key).Err()
}

// DeletePattern removes all keys matching a glob pattern.
// Uses SCAN (not KEYS) so it never blocks the Redis server, even at scale.
func DeletePattern(ctx context.Context, pattern string) error {
	if Client == nil {
		return nil
	}
	var cursor uint64
	for {
		keys, next, err := Client.Scan(ctx, cursor, pattern, 100).Result()
		if err != nil {
			return err
		}
		if len(keys) > 0 {
			if err := Client.Del(ctx, keys...).Err(); err != nil {
				return err
			}
		}
		cursor = next
		if cursor == 0 {
			break
		}
	}
	return nil
}

// FeedKey returns the cache key for a personalized feed.
// Convention: "feed:{profile_id}:{feed_type}"
func FeedKey(profileID, feedType string) string {
	return fmt.Sprintf("feed:%s:%s", profileID, feedType)
}

// SportsKey returns the cache key for the sports live feed.
// Keyed by profile so per-profile team filtering can be added later.
func SportsKey(profileID string) string {
	return fmt.Sprintf("sports:live:%s", profileID)
}

// InvalidateProfileFeeds deletes all cached feeds for a profile.
// Call whenever the profile's watch state, provider links, or preferences change.
func InvalidateProfileFeeds(ctx context.Context, profileID string) error {
	if Client == nil {
		return nil
	}
	keys := []string{
		FeedKey(profileID, "watch_now"),
		FeedKey(profileID, "up_next"),
		SportsKey(profileID),
	}
	return Client.Del(ctx, keys...).Err()
}
