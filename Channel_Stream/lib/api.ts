import type { FeedResponse, SportsResponse, ProvidersResponse } from "@/types/api"

// The base URL for your Go backend
// In development: Go server running locally
// In production: will be your deployed API URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"

// Seed data UUIDs: account = ...0001, profile = ...0002 
// A default profile and account ID for testing
const DEFAULT_PROFILE_ID = "00000000-0000-0000-0000-000000000002"
const DEFAULT_ACCOUNT_ID  = "00000000-0000-0000-0000-000000000001"

// Helper: make a GET request and parse JSON
// Generic function: <T> means "this function works with any type, and returns that type"
async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    next: { revalidate: 0 },
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
  return res.json() as Promise<T>
}

export async function getUpNextFeed(profileId = DEFAULT_PROFILE_ID): Promise<FeedResponse> {
  return get<FeedResponse>(`/v1/feed/up-next?profile_id=${profileId}`)
}

export async function getWatchNowFeed(
  profileId = DEFAULT_PROFILE_ID,
  accountId = DEFAULT_ACCOUNT_ID,
): Promise<FeedResponse> {
  return get<FeedResponse>(`/v1/feed/watch-now?profile_id=${profileId}&account_id=${accountId}`)
}

export async function getSportsLive(profileId = DEFAULT_PROFILE_ID): Promise<SportsResponse> {
  return get<SportsResponse>(`/v1/sports/live?profile_id=${profileId}`)
}

export async function getSportsSchedule(profileId = DEFAULT_PROFILE_ID): Promise<SportsResponse> {
  return get<SportsResponse>(`/v1/sports/schedule?profile_id=${profileId}`)
}

export async function getLinkedProviders(accountId = DEFAULT_ACCOUNT_ID): Promise<ProvidersResponse> {
  return get<ProvidersResponse>(`/v1/providers/linked?account_id=${accountId}`)
}

export async function getHealth(): Promise<{ status: string; version: string }> {
  return get("/v1/health")
}

// ── User preferences (requires Cognito access token) ─────────────────────────

export interface Preferences {
  teams: string[]
}

async function authedGet<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json() as Promise<T>
}

async function authedPut<T>(path: string, token: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method:  "PUT",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body:    JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json() as Promise<T>
}

export async function getPreferences(token: string): Promise<Preferences> {
  return authedGet<Preferences>("/v1/me/preferences", token)
}

export async function savePreferences(prefs: Preferences, token: string): Promise<Preferences> {
  return authedPut<Preferences>("/v1/me/preferences", token, prefs)
}
