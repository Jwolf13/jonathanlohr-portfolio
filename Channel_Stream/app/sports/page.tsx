"use client"

import { useEffect, useState } from "react"
import { getSportsLive } from "@/lib/api"
import { useWatchGame } from "@/lib/useWatchGame"
import { useAuth } from "@/components/AuthContext"
import { TeamPicker, filterEvents } from "@/components/TeamPicker"
import { OAuthModal } from "@/components/OAuthModal"
import type { SportsResponse, SportEvent } from "@/types/api"

export default function SportsPage() {
  const [data, setData]       = useState<SportsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const { watch, modal, authorize, cancel } = useWatchGame()
  const { selectedLeagues, setSelectedLeagues, selectedTeams, setSelectedTeams } = useAuth()

  useEffect(() => {
    getSportsLive().then(setData).finally(() => setLoading(false))
  }, [])

  const allEvents      = data?.events ?? []
  const liveEvents     = allEvents.filter((e) => e.status === "live")
  const filtered       = filterEvents(liveEvents, selectedLeagues, selectedTeams)
  const nothingSelected = selectedLeagues.length === 0 && selectedTeams.length === 0

  return (
    <div>
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold">Sports Live</h1>
          <p className="text-gray-400 mt-1 text-sm">Games in progress — click any game to watch</p>
        </div>
        <TeamPicker
          mode="compact"
          events={allEvents}
          selectedLeagues={selectedLeagues}
          selectedTeams={selectedTeams}
          onLeaguesChange={setSelectedLeagues}
          onTeamsChange={setSelectedTeams}
        />
      </div>

      {loading ? (
        <div className="space-y-4 max-w-2xl">
          {[1, 2].map((i) => <div key={i} className="bg-gray-900 rounded-lg p-4 animate-pulse h-28" />)}
        </div>
      ) : liveEvents.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-5xl mb-4">🏟</p>
          <h3 className="text-xl font-medium mb-2">No games live right now</h3>
          <p className="text-sm">Check back during game time or browse the schedule.</p>
        </div>
      ) : nothingSelected ? (
        <p className="text-gray-500 text-sm py-8 text-center">
          Use the filter above to pick your leagues or teams.
        </p>
      ) : filtered.length === 0 ? (
        <p className="text-gray-500 text-sm py-8 text-center">
          No live games for your selected teams right now.
        </p>
      ) : (
        <div className="space-y-3 max-w-2xl">
          {filtered.map((e) => (
            <EventCard key={e.game_id} event={e} onWatch={() => watch(e)} />
          ))}
        </div>
      )}

      {modal && (
        <OAuthModal provider={modal.provider} onAuthorize={authorize} onCancel={cancel} />
      )}
    </div>
  )
}

function EventCard({ event, onWatch }: { event: SportEvent; onWatch: () => void }) {
  const streamable = (event.watch_on ?? []).filter((o) => !o.requires_cable)
  const cableOnly  = (event.watch_on ?? []).filter((o) => o.requires_cable)

  return (
    <div
      onClick={onWatch}
      className="bg-gray-900 rounded-lg p-4 cursor-pointer hover:bg-gray-800 transition-colors group"
    >
      {/* Header row */}
      <div className="flex items-center gap-2 mb-3">
        <span className="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full bg-red-600 text-white">
          <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
          LIVE
        </span>
        <span className="text-gray-400 text-xs uppercase">{event.league}</span>
        {event.status_detail && (
          <span className="text-gray-500 text-xs">{event.status_detail}</span>
        )}
        <span className="ml-auto text-xs text-gray-600 group-hover:text-blue-400 transition-colors">
          Watch →
        </span>
      </div>

      {/* Teams + score */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="font-semibold text-lg">
            {event.home_team.abbr} vs {event.away_team.abbr}
          </p>
          <p className="text-gray-500 text-xs mt-0.5">
            {event.home_team.name} vs {event.away_team.name}
          </p>
        </div>
        {event.score && (
          <div className="text-right">
            <p className="text-2xl font-bold tabular-nums">
              {event.score.home} – {event.score.away}
            </p>
            <p className="text-gray-500 text-xs mt-0.5">home – away</p>
          </div>
        )}
      </div>

      {/* Where to watch */}
      {(event.watch_on?.length ?? 0) > 0 && (
        <div className="mt-1">
          <p className="text-xs text-gray-600 mb-1.5 uppercase tracking-wider">Where to watch</p>
          <div className="flex gap-2 flex-wrap">
            {streamable.map((opt) => (
              <span
                key={opt.network}
                className="text-sm font-medium px-3 py-1.5 rounded-lg bg-blue-900/70 text-blue-300 border border-blue-800"
              >
                {opt.app_display}
              </span>
            ))}
            {cableOnly.map((opt) => (
              <span
                key={opt.network}
                className="text-sm px-3 py-1.5 rounded-lg bg-gray-800 text-gray-500 border border-gray-700"
              >
                {opt.app_display} 📡
              </span>
            ))}
          </div>
        </div>
      )}

      {event.venue && (
        <p className="text-gray-600 text-xs mt-2">{event.venue}</p>
      )}
    </div>
  )
}
