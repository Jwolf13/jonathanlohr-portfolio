"use client"

import { useState, useRef, useEffect } from "react"
import type { SportEvent } from "@/types/api"

interface TeamsFilterProps {
  events:        SportEvent[]
  selectedTeams: string[]
  onChange:      (teams: string[]) => void
}

interface Team {
  abbr:   string
  name:   string
  league: string
}

export function TeamsFilter({ events, selectedTeams, onChange }: TeamsFilterProps) {
  const [open, setOpen]     = useState(false)
  const [search, setSearch] = useState("")
  const ref = useRef<HTMLDivElement>(null)

  // Extract unique teams from all fetched events
  const allTeams: Team[] = []
  const seen = new Set<string>()
  for (const e of events) {
    if (!seen.has(e.home_team.abbr)) {
      seen.add(e.home_team.abbr)
      allTeams.push({ abbr: e.home_team.abbr, name: e.home_team.name, league: e.league })
    }
    if (!seen.has(e.away_team.abbr)) {
      seen.add(e.away_team.abbr)
      allTeams.push({ abbr: e.away_team.abbr, name: e.away_team.name, league: e.league })
    }
  }
  allTeams.sort((a, b) => a.abbr.localeCompare(b.abbr))

  const filtered = search
    ? allTeams.filter(
        (t) =>
          t.abbr.toLowerCase().includes(search.toLowerCase()) ||
          t.name.toLowerCase().includes(search.toLowerCase()),
      )
    : allTeams

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [])

  const toggle = (abbr: string) => {
    onChange(
      selectedTeams.includes(abbr)
        ? selectedTeams.filter((t) => t !== abbr)
        : [...selectedTeams, abbr],
    )
  }

  const label =
    selectedTeams.length === 0 ? "All Teams" :
    selectedTeams.length === 1 ? selectedTeams[0] :
    `${selectedTeams.length} teams`

  if (allTeams.length === 0) return null

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
        <div className="absolute left-0 top-full mt-2 w-72 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50">
          {/* Search */}
          <div className="p-3 border-b border-gray-800">
            <input
              autoFocus
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search teams…"
              className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded-lg outline-none placeholder-gray-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Team list */}
          <div className="max-h-64 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-4">No teams found</p>
            ) : (
              filtered.map((team) => (
                <button
                  key={team.abbr}
                  onClick={() => toggle(team.abbr)}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm hover:bg-gray-800 transition-colors text-left"
                >
                  {/* Checkbox */}
                  <span
                    className={`w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center text-xs ${
                      selectedTeams.includes(team.abbr)
                        ? "bg-blue-600 border-blue-600 text-white"
                        : "border-gray-600"
                    }`}
                  >
                    {selectedTeams.includes(team.abbr) && "✓"}
                  </span>
                  <span className={`font-mono font-bold w-9 text-left flex-shrink-0 ${selectedTeams.includes(team.abbr) ? "text-blue-400" : "text-white"}`}>
                    {team.abbr}
                  </span>
                  <span className="text-gray-400 truncate flex-1">{team.name}</span>
                  <span className="text-gray-600 text-xs uppercase flex-shrink-0">{team.league}</span>
                </button>
              ))
            )}
          </div>

          {/* Clear footer */}
          {selectedTeams.length > 0 && (
            <div className="p-3 border-t border-gray-800">
              <button
                onClick={() => { onChange([]); setOpen(false) }}
                className="w-full text-sm text-gray-400 hover:text-white transition-colors py-1 text-center"
              >
                Clear all ({selectedTeams.length} selected)
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/** Filter a list of events to only those matching the selected team abbreviations.
 *  If selectedTeams is empty, returns all events unchanged. */
export function filterByTeams(events: SportEvent[], selectedTeams: string[]): SportEvent[] {
  if (selectedTeams.length === 0) return events
  return events.filter(
    (e) => selectedTeams.includes(e.home_team.abbr) || selectedTeams.includes(e.away_team.abbr),
  )
}
