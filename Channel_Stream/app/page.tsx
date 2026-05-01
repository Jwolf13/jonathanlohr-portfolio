"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { getSportsLive, getSportsSchedule, getHealth } from "@/lib/api"
import { useWatchGame } from "@/lib/useWatchGame"
import { useAuth } from "@/components/AuthContext"
import { TeamFilter, filterByTeams } from "@/components/TeamFilter"
import { OAuthModal } from "@/components/OAuthModal"
import type { SportsResponse, SportEvent } from "@/types/api"

export default function DashboardPage() {
  const [live, setLive]           = useState<SportsResponse | null>(null)
  const [schedule, setSchedule]   = useState<SportsResponse | null>(null)
  const [apiStatus, setApiStatus] = useState<"loading" | "ok" | "error">("loading")
  const { watch, modal, authorize, cancel } = useWatchGame()
  const { selectedTeams, setSelectedTeams, user } = useAuth()

  useEffect(() => {
    getHealth()
      .then(() => setApiStatus("ok"))
      .catch(() => setApiStatus("error"))

    Promise.all([getSportsLive(), getSportsSchedule()])
      .then(([liveData, scheduleData]) => {
        setLive(liveData)
        setSchedule(scheduleData)
      })
      .catch(() => setApiStatus("error"))
  }, [])

  // Merge all events for the team picker
  const allEvents     = [...(live?.events ?? []), ...(schedule?.events ?? [])]
  const liveEvents    = filterByTeams(live?.events.filter((e) => e.status === "live") ?? [], selectedTeams)
  const upcomingToday = filterByTeams(schedule?.events.filter((e) => e.status === "scheduled") ?? [], selectedTeams)

  const subtitle =
    selectedTeams.length === 0
      ? "Showing all teams and sports"
      : user
        ? `${selectedTeams.length} team${selectedTeams.length !== 1 ? "s" : ""} selected`
        : `${selectedTeams.length} team${selectedTeams.length !== 1 ? "s" : ""} selected — sign in to save`

  return (
    <div>
      <div className="flex items-center justify-between mb-8 gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-400 mt-1 text-sm">{subtitle}</p>
        </div>
        <div className="flex items-center gap-3">
          <TeamFilter events={allEvents} selectedTeams={selectedTeams} onChange={setSelectedTeams} />
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              apiStatus === "ok"    ? "bg-green-400" :
              apiStatus === "error" ? "bg-red-400"   :
                                      "bg-yellow-400 animate-pulse"
            }`} />
            <span className="text-sm text-gray-500">
              {apiStatus === "ok" ? "Live" : apiStatus === "error" ? "Offline" : "Connecting…"}
            </span>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Link href="/sports">
          <StatCard
            label="Live Now"
            value={live ? liveEvents.length : "—"}
            icon="🔴"
            color="red"
            note="games in progress"
          />
        </Link>
        <Link href="/schedule">
          <StatCard
            label="Upcoming"
            value={schedule ? upcomingToday.length : "—"}
            icon="📅"
            color="blue"
            note="games today"
          />
        </Link>
        <Link href="/providers">
          <StatCard label="Providers" value={4} icon="🔗" color="purple" note="accounts linked" />
        </Link>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-2 gap-8">

        {/* Live Games */}
        <section>
          <SectionHeader title="Live Now" href="/sports" />
          <div className="space-y-3">
            {live === null ? (
              <LoadingSkeleton count={2} />
            ) : liveEvents.length === 0 ? (
              <p className="text-gray-500 text-sm py-6 text-center">
                {selectedTeams.length > 0 ? "No live games for your teams." : "No games live right now."}
              </p>
            ) : (
              liveEvents.slice(0, 3).map((event) => (
                <LiveEventCard key={event.game_id} event={event} onWatch={() => watch(event)} />
              ))
            )}
          </div>
        </section>

        {/* Upcoming Games */}
        <section>
          <SectionHeader title="Upcoming Games" href="/schedule" />
          <div className="space-y-3">
            {schedule === null ? (
              <LoadingSkeleton count={3} />
            ) : upcomingToday.length === 0 ? (
              <p className="text-gray-500 text-sm py-6 text-center">
                {selectedTeams.length > 0 ? "No upcoming games for your teams." : "No upcoming games today."}
              </p>
            ) : (
              upcomingToday.slice(0, 4).map((event) => (
                <ScheduledEventCard key={event.game_id} event={event} onWatch={() => watch(event)} />
              ))
            )}
          </div>
        </section>

      </div>

      {modal && (
        <OAuthModal provider={modal.provider} onAuthorize={authorize} onCancel={cancel} />
      )}
    </div>
  )
}

function LiveEventCard({ event, onWatch }: { event: SportEvent; onWatch: () => void }) {
  const streamable = (event.watch_on ?? []).filter((o) => !o.requires_cable)
  const cableOnly  = (event.watch_on ?? []).filter((o) => o.requires_cable)

  return (
    <div
      onClick={onWatch}
      className="bg-gray-900 rounded-lg p-4 cursor-pointer hover:bg-gray-800 transition-colors group"
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="px-2 py-0.5 bg-red-600 text-white text-xs rounded-full font-bold animate-pulse">
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
      <div className="flex items-center justify-between mb-2">
        <div>
          <p className="font-semibold">{event.home_team.abbr} vs {event.away_team.abbr}</p>
          <p className="text-gray-600 text-xs">{event.home_team.name} vs {event.away_team.name}</p>
        </div>
        {event.score && (
          <p className="font-bold tabular-nums text-lg">{event.score.home} – {event.score.away}</p>
        )}
      </div>
      {(event.watch_on?.length ?? 0) > 0 && (
        <div className="flex gap-1.5 mt-1 flex-wrap">
          {streamable.map((opt) => (
            <span key={opt.network} className="text-xs font-medium px-2.5 py-1 rounded-lg bg-blue-900/70 text-blue-300 border border-blue-800">
              {opt.app_display}
            </span>
          ))}
          {cableOnly.map((opt) => (
            <span key={opt.network} className="text-xs px-2.5 py-1 rounded-lg bg-gray-800 text-gray-500 border border-gray-700">
              {opt.app_display} 📡
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function ScheduledEventCard({ event, onWatch }: { event: SportEvent; onWatch: () => void }) {
  const timeStr = new Date(event.start_time).toLocaleTimeString("en-US", {
    hour: "numeric", minute: "2-digit",
  })
  const streamable = (event.watch_on ?? []).filter((o) => !o.requires_cable)
  const cableOnly  = (event.watch_on ?? []).filter((o) => o.requires_cable)

  return (
    <div
      onClick={onWatch}
      className="bg-gray-900 rounded-lg p-4 cursor-pointer hover:bg-gray-800 transition-colors group"
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
          {event.league.toUpperCase()}
        </span>
        <span className="ml-auto text-xs text-gray-600 group-hover:text-blue-400 transition-colors">
          Watch →
        </span>
      </div>
      <div className="flex items-center justify-between mb-2">
        <div>
          <p className="font-medium">{event.home_team.abbr} vs {event.away_team.abbr}</p>
          <p className="text-gray-600 text-xs">{event.home_team.name} vs {event.away_team.name}</p>
        </div>
        <p className="text-sm font-medium text-gray-300 shrink-0">{timeStr}</p>
      </div>
      {(event.watch_on?.length ?? 0) > 0 && (
        <div className="flex gap-1.5 mt-1 flex-wrap">
          {streamable.map((opt) => (
            <span key={opt.network} className="text-xs font-medium px-2.5 py-1 rounded-lg bg-blue-900/70 text-blue-300 border border-blue-800">
              {opt.app_display}
            </span>
          ))}
          {cableOnly.slice(0, 1).map((opt) => (
            <span key={opt.network} className="text-xs px-2.5 py-1 rounded-lg bg-gray-800 text-gray-500 border border-gray-700">
              {opt.app_display} 📡
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({
  label, value, icon, color, note,
}: {
  label: string
  value: number | string
  icon: string
  color: "red" | "blue" | "purple"
  note: string
}) {
  const colorMap = { red: "text-red-400", blue: "text-blue-400", purple: "text-purple-400" }
  return (
    <div className="bg-gray-900 rounded-lg p-4 hover:bg-gray-800 transition-colors cursor-pointer">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm">{label}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <p className={`text-3xl font-bold ${colorMap[color]}`}>{value}</p>
      <p className="text-gray-600 text-xs mt-1">{note}</p>
    </div>
  )
}

function SectionHeader({ title, href }: { title: string; href: string }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      <Link href={href} className="text-blue-400 text-sm hover:text-blue-300">See all →</Link>
    </div>
  )
}

function LoadingSkeleton({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-gray-900 rounded-lg p-4 animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-3/4 mb-2" />
          <div className="h-3 bg-gray-800 rounded w-1/2" />
        </div>
      ))}
    </>
  )
}
