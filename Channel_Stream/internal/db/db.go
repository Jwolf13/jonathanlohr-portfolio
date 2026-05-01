package db

import (
	"context" // for timeouts and cancellation
	"fmt"     // for formatting strings (like printf)
	"os"      // for reading environment variables

	"github.com/jackc/pgx/v5/pgxpool" // PostgreSQL connection pool
)

// Pool is the global database connection pool.
// It's exported (capital P) so other packages can use it.
// A connection pool maintains multiple open connections to the database,
// reusing them for each request instead of opening a new one each time.
var Pool *pgxpool.Pool

// Connect establishes a connection to PostgreSQL.
// Call this once at startup. If it fails, the program should stop.
func Connect() error {
	// Read the database URL from environment variables
	// This is safer than hardcoding: postgresql://postgres:postgres@localhost:54322/postgres
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		// Default to local Supabase if not set
		dbURL = "postgresql://postgres:postgres@localhost:54322/postgres"
	}

	// Create the connection pool
	// context.Background() means "no deadline" — wait as long as needed to connect
	pool, err := pgxpool.New(context.Background(), dbURL)
	if err != nil {
		return fmt.Errorf("cannot create connection pool: %w", err)
		// fmt.Errorf wraps the error with context ("cannot create..." tells us what we were doing)
	}

	// Test the connection by sending a "ping"
	if err := pool.Ping(context.Background()); err != nil {
		return fmt.Errorf("cannot ping database: %w", err)
	}

	Pool = pool // store globally so all handlers can use it
	fmt.Println("✓ Connected to PostgreSQL")
	return nil // nil means "no error"
}
