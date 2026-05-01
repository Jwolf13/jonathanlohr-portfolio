"use client"

import { useEffect, useState } from "react"
import { getWatchNowFeed } from "@/lib/api"
import type { FeedResponse, FeedItem } from "@/types/api"

export default function WatchNowPage() {
  const [feed, setFeed]       = useState<FeedResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getWatchNowFeed().then(setFeed).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Watch Now</h1>
      <p className="text-gray-400 mb-8">
        Top picks from your linked providers — sorted by rating
      </p>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-gray-900 rounded-lg p-4 animate-pulse h-32" />
          ))}
        </div>
      ) : feed && feed.items.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {feed.items.map((item) => (
            <WatchNowCard key={item.content_id} item={item} />
          ))}
        </div>
      ) : (
        <EmptyState />
      )}
    </div>
  )
}

function WatchNowCard({ item }: { item: FeedItem }) {
  const providerLabel = item.provider?.replace(/_/g, " ")

  return (
    <div className="bg-gray-900 rounded-lg p-4 flex flex-col gap-3 hover:bg-gray-800 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold leading-tight">{item.title}</h3>
          <p className="text-gray-400 text-xs mt-1 capitalize">{providerLabel}</p>
        </div>
        {item.rating && (
          <span className="text-amber-400 text-sm font-semibold flex-shrink-0">★ {item.rating}</span>
        )}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="bg-gray-800 text-gray-400 text-xs px-2 py-0.5 rounded capitalize">
          {item.type}
        </span>
        {item.reason && (
          <span className="text-gray-500 text-xs">
            {item.reason.replace(/_/g, " ")}
          </span>
        )}
      </div>

      <a
        href={item.deeplink || "#"}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-auto w-full py-2 rounded-lg text-sm font-semibold text-white text-center bg-blue-600 hover:bg-blue-700 transition-colors"
      >
        Watch
      </a>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-16 text-gray-500">
      <p className="text-5xl mb-4">▶</p>
      <h3 className="text-xl font-medium mb-2">No content available</h3>
      <p className="text-sm max-w-sm mx-auto">
        Link a streaming service on the Providers page to see content here.
      </p>
    </div>
  )
}
