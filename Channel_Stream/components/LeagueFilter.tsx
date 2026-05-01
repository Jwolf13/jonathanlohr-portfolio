"use client"

import { useState, useRef, useEffect } from "react"

// The id values match the ESPN league slugs stored in sports_events.league
export const ALL_LEAGUES = [
  { id: "nfl",                      label: "NFL",                 sport: "Football",   icon: "🏈" },
  { id: "college-football",         label: "College Football",    sport: "Football",   icon: "🏈" },
  { id: "nba",                      label: "NBA",                 sport: "Basketball", icon: "🏀" },
  { id: "mens-college-basketball",  label: "College Basketball",  sport: "Basketball", icon: "🏀" },
  { id: "mlb",                      label: "MLB",                 sport: "Baseball",   icon: "⚾" },
  { id: "college-baseball",         label: "College Baseball",    sport: "Baseball",   icon: "⚾" },
  { id: "nhl",                      label: "NHL",                 sport: "Hockey",     icon: "🏒" },
  { id: "usa.1",                    label: "MLS",                 sport: "Soccer",     icon: "⚽" },
] as const

export type LeagueId = (typeof ALL_LEAGUES)[number]["id"]

interface LeagueFilterProps {
  selectedLeagues: string[]
  onChange:        (leagues: string[]) => void
}

export function LeagueFilter({ selectedLeagues, onChange }: LeagueFilterProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [])

  const toggle = (id: string) => {
    onChange(
      selectedLeagues.includes(id)
        ? selectedLeagues.filter((l) => l !== id)
        : [...selectedLeagues, id],
    )
  }

  const label =
    selectedLeagues.length === 0 ? "All Sports" :
    selectedLeagues.length === 1
      ? (ALL_LEAGUES.find((l) => l.id === selectedLeagues[0])?.label ?? selectedLeagues[0])
      : `${selectedLeagues.length} sports selected`

  // Group leagues by sport for display
  const sports = Array.from(new Set(ALL_LEAGUES.map((l) => l.sport)))

  return (
    <div ref={ref} className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          selectedLeagues.length > 0
            ? "bg-blue-600 text-white"
            : "bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white"
        }`}
      >
        <span>{label}</span>
        <span className="text-xs opacity-60">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-64 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50">
          <div className="p-3 border-b border-gray-800">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Filter by sport</p>
          </div>

          <div className="py-2">
            {sports.map((sport) => {
              const leagues = ALL_LEAGUES.filter((l) => l.sport === sport)
              return (
                <div key={sport} className="mb-1">
                  <p className="px-4 py-1 text-xs text-gray-600 uppercase tracking-wider">{sport}</p>
                  {leagues.map((league) => (
                    <button
                      key={league.id}
                      onClick={() => toggle(league.id)}
                      className="w-full flex items-center gap-3 px-4 py-2 text-sm hover:bg-gray-800 transition-colors text-left"
                    >
                      <span
                        className={`w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center text-xs ${
                          selectedLeagues.includes(league.id)
                            ? "bg-blue-600 border-blue-600 text-white"
                            : "border-gray-600"
                        }`}
                      >
                        {selectedLeagues.includes(league.id) && "✓"}
                      </span>
                      <span className="text-base leading-none">{league.icon}</span>
                      <span className={selectedLeagues.includes(league.id) ? "text-blue-400" : "text-gray-300"}>
                        {league.label}
                      </span>
                    </button>
                  ))}
                </div>
              )
            })}
          </div>

          {selectedLeagues.length > 0 && (
            <div className="p-3 border-t border-gray-800">
              <button
                onClick={() => { onChange([]); setOpen(false) }}
                className="w-full text-sm text-gray-400 hover:text-white transition-colors py-1 text-center"
              >
                Show all sports
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/** Filter events by league. Empty selection = show everything. */
export function filterByLeagues<T extends { league: string }>(
  events: T[],
  selectedLeagues: string[],
): T[] {
  if (selectedLeagues.length === 0) return events
  return events.filter((e) => selectedLeagues.includes(e.league))
}
