"use client"

import { useState } from "react"
import { PROVIDERS } from "@/lib/providers"
import { useAppStore } from "@/lib/store"
import { ProviderCard } from "@/components/ProviderCard"
import { OAuthModal } from "@/components/OAuthModal"

export default function ProvidersPage() {
  const {
    store,
    hydrated,
    linkProvider,
    unlinkProvider,
  } = useAppStore()

  const [linkingId, setLinkingId]     = useState<string | null>(null)
  const [unlinkingId, setUnlinkingId] = useState<string | null>(null)

  const linkedCount = Object.values(store.providerLinks).filter((l) => l.linked).length
  const coveragePct = Math.round((linkedCount / PROVIDERS.length) * 100)

  const linkingProvider   = linkingId   ? PROVIDERS.find((p) => p.id === linkingId)   : null
  const unlinkingProvider = unlinkingId ? PROVIDERS.find((p) => p.id === unlinkingId) : null

  if (!hydrated) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-gray-600 border-t-gray-300 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-3xl font-bold">Streaming Accounts</h1>
      </div>

      <p className="text-gray-400 mt-1.5 text-sm mb-8">
        Link your streaming services so Channel Stream can surface personalized content.{" "}
        <span className="text-gray-300 font-medium">{linkedCount} of {PROVIDERS.length} linked</span>
      </p>

      <div className="max-w-5xl">
        {/* Coverage bar */}
        <div className="mb-8 p-4 bg-gray-900 rounded-lg">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-2.5">
            <span className="font-medium">Account coverage</span>
            <span className="font-semibold tabular-nums" data-testid="coverage-pct">
              {coveragePct}%
            </span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-700"
              style={{ width: `${coveragePct}%` }}
            />
          </div>
          <p className="text-xs text-gray-600 mt-2.5">
            {linkedCount === 0
              ? "Link your first service to get started"
              : linkedCount === PROVIDERS.length
              ? "All services linked — you're all set!"
              : `${PROVIDERS.length - linkedCount} service${PROVIDERS.length - linkedCount !== 1 ? "s" : ""} remaining`}
          </p>
        </div>

        {/* Provider grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {PROVIDERS.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              link={store.providerLinks[provider.id]}
              onLink={() => setLinkingId(provider.id)}
              onUnlink={() => setUnlinkingId(provider.id)}
            />
          ))}
        </div>
      </div>

      {/* OAuth Modal */}
      {linkingId && linkingProvider && (
        <OAuthModal
          provider={linkingProvider}
          onAuthorize={(email) => {
            linkProvider(linkingId, email)
            setLinkingId(null)
          }}
          onCancel={() => setLinkingId(null)}
        />
      )}

      {/* Unlink confirmation */}
      {unlinkingId && unlinkingProvider && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="unlink-title"
        >
          <div
            className="absolute inset-0 bg-black/75 backdrop-blur-sm"
            onClick={() => setUnlinkingId(null)}
            aria-hidden="true"
          />
          <div className="relative w-full max-w-sm bg-gray-900 border border-gray-700 rounded-lg p-6 shadow-2xl">
            <h2 id="unlink-title" className="text-lg font-semibold mb-2">
              Unlink {unlinkingProvider.name}?
            </h2>
            <p className="text-sm text-gray-400 mb-6 leading-relaxed">
              Content from{" "}
              <span className="font-semibold" style={{ color: unlinkingProvider.color }}>
                {unlinkingProvider.name}
              </span>{" "}
              will no longer appear in your feed. You can re-link at any time.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setUnlinkingId(null)}
                className="flex-1 py-2.5 rounded-lg text-sm font-medium text-gray-400 bg-gray-800 hover:bg-gray-700 transition-colors"
                data-testid="cancel-unlink"
              >
                Keep linked
              </button>
              <button
                onClick={() => {
                  unlinkProvider(unlinkingId)
                  setUnlinkingId(null)
                }}
                className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-white bg-red-600 hover:bg-red-500 transition-colors"
                data-testid="confirm-unlink"
              >
                Unlink
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
