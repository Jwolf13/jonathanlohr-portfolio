package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/joho/godotenv"

	"github.com/jwolf13/channel-stream/internal/cache"
	"github.com/jwolf13/channel-stream/internal/db"
	"github.com/jwolf13/channel-stream/internal/feed"
	"github.com/jwolf13/channel-stream/internal/ingestion"
	"github.com/jwolf13/channel-stream/internal/provider"
	"github.com/jwolf13/channel-stream/internal/user"
)

func main() {
	// ─── 1. Load environment variables from .env file ─────────────────────
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found — using system environment variables")
	}

	// ─── 2. Cancellable context for graceful shutdown ─────────────────────
	// signal.NotifyContext cancels ctx when SIGINT (Ctrl-C) or SIGTERM arrives.
	// Background goroutines watch ctx.Done() and stop cleanly.
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	// ─── 3. Connect to the database ───────────────────────────────────────
	if err := db.Connect(); err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Pool.Close()

	// ─── 3b. Run migrations ───────────────────────────────────────────────
	if err := runMigrations(ctx); err != nil {
		log.Fatal("Migration failed:", err)
	}

	// ─── 4. Connect to Redis (optional — degrades gracefully without it) ──
	if err := cache.Connect(); err != nil {
		log.Println("Warning: Redis unavailable, caching disabled:", err)
	}

	// ─── 5. Start the sports ingestion worker ─────────────────────────────
	// Runs in the background: seeds broadcast mappings, then polls ESPN every
	// 60 s for live scores and every 10 min for the 3-day schedule.
	go ingestion.StartSportsWorker(ctx)

	// ─── 6. Set up the HTTP router ────────────────────────────────────────
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.RealIP)
	r.Use(corsMiddleware)

	// ─── 7. Define routes ─────────────────────────────────────────────────
	r.Get("/v1/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintln(w, `{"status":"ok","version":"1.0.0"}`)
	})

	r.Get("/v1/feed/up-next", feed.GetUpNext)
	r.Get("/v1/feed/watch-now", feed.GetWatchNow)
	r.Get("/v1/sports/live", feed.GetSportsLive)
	r.Get("/v1/sports/schedule", feed.GetSportsSchedule)

	r.Get("/v1/providers/linked", provider.GetLinkedProviders)

	r.Get("/v1/me/preferences", user.GetPreferences)
	r.Put("/v1/me/preferences", user.PutPreferences)

	// ─── 8. Start the server ──────────────────────────────────────────────
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	fmt.Printf("Channel Stream API running at http://localhost:%s\n", port)
	fmt.Println("Endpoints:")
	fmt.Println("  GET /v1/health")
	fmt.Println("  GET /v1/feed/up-next")
	fmt.Println("  GET /v1/feed/watch-now")
	fmt.Println("  GET /v1/sports/live")
	fmt.Println("  GET /v1/sports/schedule")
	fmt.Println("  GET /v1/providers/linked")
	fmt.Println("  GET /v1/me/preferences")
	fmt.Println("  PUT /v1/me/preferences")
	fmt.Println()

	log.Fatal(http.ListenAndServe(":"+port, r))
}

func runMigrations(ctx context.Context) error {
	_, err := db.Pool.Exec(ctx, `
		CREATE TABLE IF NOT EXISTS user_accounts (
			id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
			cognito_sub TEXT        UNIQUE NOT NULL,
			email       TEXT,
			preferences JSONB       NOT NULL DEFAULT '{}',
			created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
			updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
		);
		CREATE INDEX IF NOT EXISTS idx_user_accounts_cognito_sub ON user_accounts(cognito_sub);
	`)
	if err != nil {
		return err
	}
	log.Println("Migrations OK")
	return nil
}

// corsMiddleware allows requests from our Next.js frontend
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*") // In production: specific domains only
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		// Handle preflight requests (browsers send OPTIONS before actual requests)
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}
