"use client"

import { useState, useRef, useEffect } from "react"
import type { SportEvent } from "@/types/api"

export const ALL_LEAGUES = [
  { id: "nfl",                      label: "NFL",                sport: "Football",   icon: "🏈" },
  { id: "college-football",         label: "College Football",   sport: "Football",   icon: "🏈" },
  { id: "nba",                      label: "NBA",                sport: "Basketball", icon: "🏀" },
  { id: "mens-college-basketball",  label: "College Basketball", sport: "Basketball", icon: "🏀" },
  { id: "mlb",                      label: "MLB",                sport: "Baseball",   icon: "⚾" },
  { id: "college-baseball",         label: "College Baseball",   sport: "Baseball",   icon: "⚾" },
  { id: "nhl",                      label: "NHL",                sport: "Hockey",     icon: "🏒" },
  { id: "usa.1",                    label: "MLS",                sport: "Soccer",     icon: "⚽" },
] as const

interface Team { abbr: string; name: string; league: string }

function extractTeams(events: SportEvent[]): Team[] {
  const seen  = new Set<string>()
  const teams: Team[] = []
  for (const e of events) {
    for (const t of [e.home_team, e.away_team]) {
      if (!seen.has(t.abbr)) {
        seen.add(t.abbr)
        teams.push({ abbr: t.abbr, name: t.name, league: e.league })
      }
    }
  }
  return teams.sort((a, b) => a.name.localeCompare(b.name))
}

interface TeamPickerProps {
  events:          SportEvent[]
  selectedLeagues: string[]
  selectedTeams:   string[]
  onLeaguesChange: (l: string[]) => void
  onTeamsChange:   (t: string[]) => void
  mode:            "hero" | "compact"
}

export function TeamPicker({
  events, selectedLeagues, selectedTeams, onLeaguesChange, onTeamsChange, mode,
}: TeamPickerProps) {
  const [open, setOpen]     = useState(false)
  const [search, setSearch] = useState("")
  const ref                 = useRef<HTMLDivElement>(null)
  const inputRef            = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (mode !== "compact") return
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onClick)
    return () => document.removeEventListener("mousedown", onClick)
  }, [mode])

  useEffect(() => {
    if (open || mode === "hero") setTimeout(() => inputRef.current?.focus(), 50)
  }, [open, mode])

  const allTeams   = extractTeams(events)
  const filtered   = search.trim()
    ? allTeams.filter((t) =>
        t.name.toLowerCase().includes(search.toLowerCase()) ||
        t.abbr.toLowerCase().includes(search.toLowerCase()))
    : allTeams

  const totalSelected = selectedLeagues.length + selectedTeams.length

  const toggleLeague = (id: string) =>
    onLeaguesChange(
      selectedLeagues.includes(id)
        ? selectedLeagues.filter((l) => l !== id)
        : [...selectedLeagues, id],
    )

  const toggleTeam = (abbr: string) =>
    onTeamsChange(
      selectedTeams.includes(abbr)
        ? selectedTeams.filter((t) => t !== abbr)
        : [...selectedTeams, abbr],
    )

  const clearAll = () => { onLeaguesChange([]); onTeamsChange([]) }

  const body = (
    <div className={mode === "hero" ? "w-full max-w-2xl" : "w-80"}>
      {/* League quick-picks */}
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">By league</p>
      <div className={`grid gap-2 mb-5 ${mode === "hero" ? "grid-cols-4" : "grid-cols-2"}`}>
        {ALL_LEAGUES.map((l) => (
          <button
            key={l.id}
            onClick={() => toggleLeague(l.id)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left ${
              selectedLeagues.includes(l.id)
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            <span>{l.icon}</span>
            <span className="truncate">{l.label}</span>
          </button>
        ))}
      </div>

      {/* Individual team search */}
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Or find a team</p>
      <input
        ref={inputRef}
        type="text"
        placeholder="Search teams…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full bg-gray-800 text-sm text-white placeholder-gray-500 px-3 py-2 rounded-lg outline-none focus:ring-1 focus:ring-blue-500 mb-2"
      />
      <div className={`overflow-y-auto space-y-0.5 ${mode === "hero" ? "max-h-52" : "max-h-56"}`}>
        {allTeams.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-6">Loading teams…</p>
        ) : filtered.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-6">No teams match</p>
        ) : (
          filtered.map((team) => (
            <button
              key={team.abbr}
              onClick={() => toggleTeam(team.abbr)}
              className="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-gray-800 rounded-lg transition-colors text-left"
            >
              <span className={`w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center text-xs ${
                selectedTeams.includes(team.abbr)
                  ? "bg-blue-600 border-blue-600 text-white"
                  : "border-gray-600"
              }`}>
                {selectedTeams.includes(team.abbr) && "✓"}
              </span>
              <span className="font-mono text-xs text-gray-500 w-8 shrink-0">{team.abbr}</span>
              <span className={selectedTeams.includes(team.abbr) ? "text-blue-400" : "text-gray-300"}>
                {team.name}
              </span>
              <span className="ml-auto text-xs text-gray-600 uppercase">{team.league}</span>
            </button>
          ))
        )}
      </div>

      {totalSelected > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-800 flex justify-between items-center">
          <span className="text-sm text-gray-400">
            {totalSelected} selected
          </span>
          <button
            onClick={clearAll}
            className="text-xs text-gray-400 hover:text-white transition-colors"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  )

  if (mode === "hero") {
    return (
      <div className="flex flex-col items-center py-16 px-4">
        <p className="text-5xl mb-4">📺</p>
        <h2 className="text-2xl font-bold mb-2 text-center">What do you follow?</h2>
        <p className="text-gray-400 text-sm mb-10 text-center">
          Pick your leagues or teams — your games will appear here instantly.
        </p>
        {body}
      </div>
    )
  }

  // Compact dropdown
  const label = totalSelected === 0 ? "My Teams" : `${totalSelected} selected`
  return (
    <div ref={ref} className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          totalSelected > 0
            ? "bg-blue-600 text-white"
            : "bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white"
        }`}
      >
        <span>{label}</span>
        <span className="text-xs opacity-60">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-2 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 p-4">
          {body}
        </div>
      )}
    </div>
  )
}

/** Returns [] when nothing is selected — blank until user picks something. */
export function filterEvents<T extends {
  league: string
  home_team: { abbr: string }
  away_team: { abbr: string }
}>(events: T[], selectedLeagues: string[], selectedTeams: string[]): T[] {
  if (selectedLeagues.length === 0 && selectedTeams.length === 0) return []
  return events.filter(
    (e) =>
      selectedLeagues.includes(e.league) ||
      selectedTeams.includes(e.home_team.abbr) ||
      selectedTeams.includes(e.away_team.abbr),
  )
}
