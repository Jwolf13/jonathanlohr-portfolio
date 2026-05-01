"use client"

import { useState, useRef, useEffect } from "react"
import type { SportEvent } from "@/types/api"

interface Team {
  abbr:   string
  name:   string
  league: string
}

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

interface TeamFilterProps {
  events:        SportEvent[]
  selectedTeams: string[]
  onChange:      (teams: string[]) => void
}

export function TeamFilter({ events, selectedTeams, onChange }: TeamFilterProps) {
  const [open, setOpen]     = useState(false)
  const [search, setSearch] = useState("")
  const ref                 = useRef<HTMLDivElement>(null)
  const inputRef            = useRef<HTMLInputElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [])

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50)
  }, [open])

  const allTeams = extractTeams(events)
  const filtered = search.trim()
    ? allTeams.filter(
        (t) =>
          t.name.toLowerCase().includes(search.toLowerCase()) ||
          t.abbr.toLowerCase().includes(search.toLowerCase()),
      )
    : allTeams

  const toggle = (abbr: string) => {
    onChange(
      selectedTeams.includes(abbr)
        ? selectedTeams.filter((t) => t !== abbr)
        : [...selectedTeams, abbr],
    )
  }

  const label =
    selectedTeams.length === 0 ? "My Teams" :
    selectedTeams.length === 1 ? selectedTeams[0] :
    `${selectedTeams.length} teams`

  const leagues = Array.from(new Set(filtered.map((t) => t.league))).sort()

  return (
    <div ref={ref} className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          selectedTeams.length > 0
            ? "bg-blue-600 text-white"
            : "bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white"
        }`}
      >
        <span>{label}</span>
        <span className="text-xs opacity-60">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-72 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50">
          <div className="p-3 border-b border-gray-800">
            <input
              ref={inputRef}
              type="text"
              placeholder="Search teams…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-gray-800 text-sm text-white placeholder-gray-500 px-3 py-2 rounded-lg outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="py-2 max-h-80 overflow-y-auto">
            {allTeams.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-6">Loading games…</p>
            ) : filtered.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-6">No teams match</p>
            ) : (
              leagues.map((league) => {
                const teamsInLeague = filtered.filter((t) => t.league === league)
                return (
                  <div key={league} className="mb-1">
                    <p className="px-4 py-1 text-xs text-gray-600 uppercase tracking-wider">{league}</p>
                    {teamsInLeague.map((team) => (
                      <button
                        key={team.abbr}
                        onClick={() => toggle(team.abbr)}
                        className="w-full flex items-center gap-3 px-4 py-2 text-sm hover:bg-gray-800 transition-colors text-left"
                      >
                        <span
                          className={`w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center text-xs ${
                            selectedTeams.includes(team.abbr)
                              ? "bg-blue-600 border-blue-600 text-white"
                              : "border-gray-600"
                          }`}
                        >
                          {selectedTeams.includes(team.abbr) && "✓"}
                        </span>
                        <span className="font-mono text-xs text-gray-500 w-8 shrink-0">{team.abbr}</span>
                        <span className={selectedTeams.includes(team.abbr) ? "text-blue-400" : "text-gray-300"}>
                          {team.name}
                        </span>
                      </button>
                    ))}
                  </div>
                )
              })
            )}
          </div>

          {selectedTeams.length > 0 && (
            <div className="p-3 border-t border-gray-800">
              <button
                onClick={() => { onChange([]); setOpen(false) }}
                className="w-full text-sm text-gray-400 hover:text-white transition-colors py-1 text-center"
              >
                Clear — show all teams
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/** Filter events by selected team abbreviations. Empty = show all. */
export function filterByTeams<T extends { home_team: { abbr: string }; away_team: { abbr: string } }>(
  events: T[],
  selectedTeams: string[],
): T[] {
  if (selectedTeams.length === 0) return events
  return events.filter(
    (e) => selectedTeams.includes(e.home_team.abbr) || selectedTeams.includes(e.away_team.abbr),
  )
}
