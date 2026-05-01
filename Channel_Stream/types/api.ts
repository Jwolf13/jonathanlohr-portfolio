export interface FeedItem {
  content_id: string
  title: string
  type: "movie" | "series" | "episode" | "sport_event"
  provider: string
  progress_pct?: number
  resume_position_sec?: number
  rating?: string
  deeplink?: string
  last_watched?: string
  score?: number
  reason?: string
}

export interface FeedResponse {
  feed: string
  generated_at: string
  items: FeedItem[]
  count: number
}

export interface WatchOption {
  network: string
  app?: string
  app_display: string
  requires_cable: boolean
}

export interface TeamInfo {
  id: string
  name: string
  abbr: string
}

export interface GameScore {
  home: string
  away: string
}

export interface SportEvent {
  game_id: string
  sport: string
  league: string
  home_team: TeamInfo
  away_team: TeamInfo
  start_time: string
  status: "live" | "scheduled" | "final"
  status_detail?: string
  score?: GameScore
  venue?: string
  watch_on: WatchOption[]
}

export interface SportsResponse {
  feed: string
  generated_at: string
  events: SportEvent[]
  count: number
}

export interface ProviderLink {
  provider: string
  linked_at: string
  token_expires?: string
  status: "valid" | "expired" | "expiring_soon" | "never_expires"
}

export interface ProvidersResponse {
  account_id: string
  providers: ProviderLink[]
  count: number
}
