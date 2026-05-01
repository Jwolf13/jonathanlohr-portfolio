"use client"

import { useEffect, useState } from "react"
import { getSportsSchedule } from "@/lib/api"
import { useWatchGame } from "@/lib/useWatchGame"
import { useAuth } from "@/components/AuthContext"
import { TeamFilter, filterByTeams } from "@/components/TeamFilter"
import { OAuthModal } from "@/components/OAuthModal"
import type { SportsResponse, SportEvent } from "@/types/api"

export default function SchedulePage() {
  const [data, setData]       = useState<SportsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const { watch, modal, authorize, cancel } = useWatchGame()
  const { selectedTeams, setSelectedTeams } = useAuth()

  useEffect(() => {
    getSportsSchedule().then(setData).finally(() => setLoading(false))
  }, [])

  const scheduled = data?.events.filter((e) => e.status === "scheduled") ?? []
  const filtered  = filterByTeams(scheduled, selectedTeams)

  const grouped = groupByDay(filtered)
  const days    = Object.keys(grouped).sort()

  return (
    <div>
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold">Schedule</h1>
          <p className="text-gray-400 mt-1 text-sm">Upcoming games — click to watch</p>
        </div>
        <TeamFilter events={scheduled} selectedTeams={selectedTeams} onChange={setSelectedTeams} />
      </div>

      {loading ? (
        <div className="space-y-4 max-w-2xl">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-900 rounded-lg p-4 animate-pulse h-24" />
          ))}
        </div>
      ) : scheduled.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-5xl mb-4">📅</p>
          <h3 className="text-xl font-medium mb-2">Nothing scheduled</h3>
          <p className="text-sm">Games will appear here once they&apos;re on the schedule.</p>
        </div>
      ) : days.length === 0 ? (
        <p className="text-gray-500 text-sm py-8 text-center">
          No upcoming games for your selected teams.
        </p>
      ) : (
        <div className="space-y-8 max-w-2xl">
          {days.map((day) => (
            <section key={day}>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                {formatDay(day)}
              </h2>
              <div className="space-y-3">
                {grouped[day].map((event) => (
                  <ScheduleCard key={event.game_id} event={event} onWatch={() => watch(event)} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {modal && (
        <OAuthModal provider={modal.provider} onAuthorize={authorize} onCancel={cancel} />
      )}
    </div>
  )
}

function ScheduleCard({ event, onWatch }: { event: SportEvent; onWatch: () => void }) {
  const timeStr = new Date(event.start_time).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  })

  const streamable = event.watch_on.filter((o) => !o.requires_cable)
  const cableOnly  = event.watch_on.filter((o) => o.requires_cable)

  return (
    <div
      onClick={onWatch}
      className="bg-gray-900 rounded-lg p-4 cursor-pointer hover:bg-gray-800 transition-colors group"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-gray-500 bg-gray-800 px-2.5 py-1 rounded-full uppercase">
          {event.league}
        </span>
        {event.status_detail && (
          <span className="text-gray-500 text-xs">{event.status_detail}</span>
        )}
        <span className="ml-auto text-xs text-gray-600 group-hover:text-blue-400 transition-colors">
          Watch →
        </span>
      </div>

      {/* Teams + time */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="font-semibold text-lg">
            {event.home_team.abbr} vs {event.away_team.abbr}
          </p>
          <p className="text-gray-500 text-xs mt-0.5">
            {event.home_team.name} vs {event.away_team.name}
          </p>
        </div>
        <p className="text-sm font-medium text-gray-300 shrink-0">{timeStr}</p>
      </div>

      {/* Where to watch — prominent */}
      {event.watch_on.length > 0 && (
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

function groupByDay(events: SportEvent[]): Record<string, SportEvent[]> {
  const result: Record<string, SportEvent[]> = {}
  for (const event of events) {
    const day = event.start_time.slice(0, 10)
    if (!result[day]) result[day] = []
    result[day].push(event)
  }
  return result
}

function formatDay(isoDate: string): string {
  const date     = new Date(isoDate + "T12:00:00")
  const today    = new Date()
  today.setHours(12, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)

  if (date.toDateString() === today.toDateString())    return "Today"
  if (date.toDateString() === tomorrow.toDateString()) return "Tomorrow"
  return date.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })
}
