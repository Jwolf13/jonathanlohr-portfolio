"use client"

import { useState, useEffect, useCallback } from "react"

const STORE_KEY = "channel_stream_v1"

const TOKEN_TTL_MS = 30 * 24 * 60 * 60 * 1000 // 30 days

const PROFILE_COLORS = [
  "#E50914",
  "#1CE783",
  "#0063E5",
  "#531FFF",
  "#F59E0B",
  "#EC4899",
]

export type ProviderLink = {
  providerId: string
  linked: boolean
  linkedAt: string
  tokenExpiresAt: string
  lastRefreshed: string
  email: string
}

export type Profile = {
  id: string
  name: string
  color: string
  isDefault: boolean
}

export type AppStore = {
  accountId: string
  profiles: Profile[]
  activeProfileId: string
  providerLinks: Record<string, ProviderLink>
}

function makeId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

function createDefaultStore(): AppStore {
  const profileId = makeId()
  return {
    accountId: makeId(),
    profiles: [
      {
        id: profileId,
        name: "Main Profile",
        color: PROFILE_COLORS[0],
        isDefault: true,
      },
    ],
    activeProfileId: profileId,
    providerLinks: {},
  }
}

function loadStore(): AppStore {
  if (typeof window === "undefined") return createDefaultStore()
  try {
    const raw = localStorage.getItem(STORE_KEY)
    if (!raw) return createDefaultStore()
    return JSON.parse(raw) as AppStore
  } catch {
    return createDefaultStore()
  }
}

function saveStore(store: AppStore): void {
  if (typeof window === "undefined") return
  localStorage.setItem(STORE_KEY, JSON.stringify(store))
}

export function useAppStore() {
  const [store, setStore] = useState<AppStore>(createDefaultStore)
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    setStore(loadStore())
    setHydrated(true)
  }, [])

  const update = useCallback((updater: (prev: AppStore) => AppStore) => {
    setStore((prev) => {
      const next = updater(prev)
      saveStore(next)
      return next
    })
  }, [])

  const linkProvider = useCallback(
    (providerId: string, email: string) => {
      const now = new Date()
      const expiresAt = new Date(now.getTime() + TOKEN_TTL_MS)
      update((prev) => ({
        ...prev,
        providerLinks: {
          ...prev.providerLinks,
          [providerId]: {
            providerId,
            linked: true,
            linkedAt: now.toISOString(),
            tokenExpiresAt: expiresAt.toISOString(),
            lastRefreshed: now.toISOString(),
            email,
          },
        },
      }))
    },
    [update]
  )

  const unlinkProvider = useCallback(
    (providerId: string) => {
      update((prev) => {
        const links = { ...prev.providerLinks }
        delete links[providerId]
        return { ...prev, providerLinks: links }
      })
    },
    [update]
  )

  const addProfile = useCallback(
    (name: string) => {
      update((prev) => {
        if (prev.profiles.length >= 6) return prev
        const colorIndex = prev.profiles.length % PROFILE_COLORS.length
        return {
          ...prev,
          profiles: [
            ...prev.profiles,
            {
              id: makeId(),
              name,
              color: PROFILE_COLORS[colorIndex],
              isDefault: false,
            },
          ],
        }
      })
    },
    [update]
  )

  const removeProfile = useCallback(
    (profileId: string) => {
      update((prev) => {
        if (prev.profiles.length <= 1) return prev
        const profiles = prev.profiles.filter((p) => p.id !== profileId)
        const activeProfileId =
          prev.activeProfileId === profileId
            ? profiles[0].id
            : prev.activeProfileId
        return { ...prev, profiles, activeProfileId }
      })
    },
    [update]
  )

  const switchProfile = useCallback(
    (profileId: string) => {
      update((prev) => ({ ...prev, activeProfileId: profileId }))
    },
    [update]
  )

  return {
    store,
    hydrated,
    linkProvider,
    unlinkProvider,
    addProfile,
    removeProfile,
    switchProfile,
  }
}
