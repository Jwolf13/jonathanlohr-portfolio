"use client"

import { useEffect, useState } from "react"
import { getUpNextFeed } from "@/lib/api"
import type { FeedResponse, FeedItem } from "@/types/api"

export default function UpNextPage() {
  const [feed, setFeed]       = useState<FeedResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getUpNextFeed()
      .then(setFeed)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Continue Watching</h1>
      <p className="text-gray-400 mb-8">Your in-progress shows and movies across all providers</p>

      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : feed && feed.items.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 max-w-3xl">
          {feed.items.map((item, index) => (
            <UpNextCard key={item.content_id} item={item} rank={index + 1} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="Nothing in progress"
          description="Start watching something on Netflix, Hulu, or Apple TV+ and it'll appear here."
        />
      )}
    </div>
  )
}

function UpNextCard({ item, rank }: { item: FeedItem; rank: number }) {
  const resumeTime = formatResumeTime(item.resume_position_sec)
  const providerLabel = item.provider?.replace(/_/g, " ")

  return (
    <div className="bg-gray-900 rounded-xl p-5 flex items-center gap-5">
      <span className="text-3xl font-bold text-gray-700 w-8 text-center">{rank}</span>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="bg-gray-800 text-gray-400 text-xs px-2 py-0.5 rounded capitalize">
            {item.type}
          </span>
          <span className="text-gray-500 text-xs capitalize">{providerLabel}</span>
        </div>
        <h3 className="font-semibold text-lg truncate">{item.title}</h3>
        <p className="text-gray-400 text-sm mt-0.5">Resume at {resumeTime}</p>

        <div className="mt-3 flex items-center gap-3">
          <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${item.progress_pct}%` }}
            />
          </div>
          <span className="text-gray-400 text-xs">{item.progress_pct}%</span>
        </div>
      </div>

      <a
        href={item.deeplink || "#"}
        target="_blank"
        rel="noopener noreferrer"
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex-shrink-0"
      >
        ▶ Resume
      </a>
    </div>
  )
}

function formatResumeTime(seconds?: number): string {
  if (!seconds) return "0:00"
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
  return `${m}:${s.toString().padStart(2, "0")}`
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="text-center py-16 text-gray-500">
      <p className="text-5xl mb-4">⏭</p>
      <h3 className="text-xl font-medium mb-2">{title}</h3>
      <p className="text-sm max-w-sm mx-auto">{description}</p>
    </div>
  )
}
