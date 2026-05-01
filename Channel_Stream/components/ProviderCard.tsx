"use client"

import { ProviderLink } from "@/lib/store"
import { Provider } from "@/lib/providers"

type Props = {
  provider: Provider
  link: ProviderLink | undefined
  onLink: () => void
  onUnlink: () => void
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

function daysUntil(iso: string): number {
  return Math.max(
    0,
    Math.floor((new Date(iso).getTime() - Date.now()) / 86_400_000)
  )
}

function TokenExpiry({ iso }: { iso: string }) {
  const days = daysUntil(iso)
  const soon = days <= 7

  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-zinc-500">Token expires</span>
      <span className={soon ? "text-amber-400 font-medium" : "text-zinc-300"}>
        {days === 0 ? "Today" : days === 1 ? "Tomorrow" : `${days} days`}
      </span>
    </div>
  )
}

export function ProviderCard({ provider, link, onLink, onUnlink }: Props) {
  const isLinked = link?.linked === true

  return (
    <div
      data-testid={`provider-card-${provider.id}`}
      className={[
        "relative rounded-2xl border p-5 flex flex-col gap-4 transition-all duration-200",
        isLinked
          ? "border-zinc-700 bg-zinc-900/70"
          : "border-zinc-800 bg-zinc-900/30 hover:border-zinc-700",
      ].join(" ")}
    >
      {/* Status badge */}
      <div className="absolute top-4 right-4">
        {isLinked ? (
          <span
            data-testid={`status-linked-${provider.id}`}
            className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Linked
          </span>
        ) : (
          <span
            data-testid={`status-unlinked-${provider.id}`}
            className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-zinc-800 text-zinc-500 border border-zinc-700"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-zinc-600" />
            Not linked
          </span>
        )}
      </div>

      {/* Provider identity */}
      <div className="flex items-center gap-3 pr-24">
        <div
          className="w-11 h-11 rounded-xl flex items-center justify-center text-white font-bold text-base flex-shrink-0 select-none"
          style={{ backgroundColor: provider.color }}
          aria-hidden="true"
        >
          {provider.name.slice(0, 1)}
        </div>
        <div className="min-w-0">
          <h3 className="font-semibold text-zinc-100 text-base leading-tight">
            {provider.name}
          </h3>
          <p className="text-xs text-zinc-500 mt-0.5 leading-snug">
            {provider.description}
          </p>
        </div>
      </div>

      {/* Token / account details */}
      {isLinked && link ? (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-500">Account</span>
            <span className="text-zinc-300 truncate max-w-[180px] font-mono text-[11px]">
              {link.email}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-500">Linked</span>
            <span className="text-zinc-300">{formatDate(link.linkedAt)}</span>
          </div>
          <TokenExpiry iso={link.tokenExpiresAt} />
          {daysUntil(link.tokenExpiresAt) <= 7 && (
            <p className="text-xs text-amber-400/90 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2 mt-1 leading-snug">
              Token expiring soon — you may be prompted to re-authenticate.
            </p>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center">
          <p className="text-xs text-zinc-600 leading-relaxed">
            Link your {provider.name} account to see its content in your
            personalized feed.
          </p>
        </div>
      )}

      {/* Action */}
      {isLinked ? (
        <button
          data-testid={`unlink-${provider.id}`}
          onClick={onUnlink}
          className="w-full py-2 rounded-xl text-sm font-medium text-zinc-400 bg-zinc-800 hover:bg-zinc-700 hover:text-zinc-200 transition-colors border border-zinc-700"
        >
          Unlink Account
        </button>
      ) : (
        <button
          data-testid={`link-${provider.id}`}
          onClick={onLink}
          className="w-full py-2 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-[0.98]"
          style={{ backgroundColor: provider.color }}
        >
          Link Account
        </button>
      )}
    </div>
  )
}
