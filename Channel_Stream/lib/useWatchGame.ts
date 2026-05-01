"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAppStore } from "@/lib/store"
import { PROVIDERS } from "@/lib/providers"
import type { Provider } from "@/lib/providers"
import type { SportEvent } from "@/types/api"

export type WatchModal = {
  event: SportEvent
  app: string
  provider: Provider
}

// Build the deepest available link for a given provider + event.
// For Disney+/ESPN events we have a real per-game ESPN watch URL using the ESPN
// event ID embedded in game_id ("{league}_{espnId}").
export function buildWatchUrl(event: SportEvent, app: string): string {
  const espnId = event.game_id.includes("_") ? event.game_id.split("_").pop() : null

  switch (app) {
    case "disney_plus":
      return espnId
        ? `https://www.espn.com/watch/player/_/id/${espnId}`
        : "https://www.espn.com/watch"
    case "peacock":
      return "https://www.peacocktv.com/stream/sports/live"
    case "paramount_plus":
      return "https://www.paramountplus.com/live-tv/"
    case "max":
      return "https://play.max.com/channel/live"
    case "prime_video":
      return "https://www.amazon.com/gp/video/storefront"
    case "apple_tv_plus":
      return "https://tv.apple.com"
    case "youtube_tv":
      return "https://tv.youtube.com"
    case "hulu":
      return "https://www.hulu.com/live-tv"
    default:
      return "/providers"
  }
}

export function useWatchGame() {
  const { store, linkProvider } = useAppStore()
  const router                  = useRouter()
  const [modal, setModal]       = useState<WatchModal | null>(null)

  function watch(event: SportEvent) {
    // Already have a linked provider for this game — open deep link immediately
    const linked = event.watch_on.find(
      (opt) => !opt.requires_cable && opt.app && store.providerLinks[opt.app]?.linked,
    )
    if (linked?.app) {
      window.open(buildWatchUrl(event, linked.app), "_blank")
      return
    }

    // No linked provider — find first streamable option and prompt sign-in
    const streamable = event.watch_on.find((opt) => !opt.requires_cable && opt.app)
    if (streamable?.app) {
      const provider = PROVIDERS.find((p) => p.id === streamable.app)
      if (provider) {
        setModal({ event, app: streamable.app, provider })
        return
      }
    }

    // Cable-only game or no known provider
    router.push("/providers")
  }

  function authorize(email: string) {
    if (!modal) return
    linkProvider(modal.app, email)
    const url = buildWatchUrl(modal.event, modal.app)
    setModal(null)
    // Small delay so the modal closes before the tab opens (avoids popup blockers)
    setTimeout(() => window.open(url, "_blank"), 50)
  }

  function cancel() {
    setModal(null)
  }

  return { watch, modal, authorize, cancel }
}
