"use client"

import { useState } from "react"
import { Provider } from "@/lib/providers"

type Props = {
  provider: Provider
  onAuthorize: (email: string) => void
  onCancel: () => void
}

type Step = "login" | "authorize"

export function OAuthModal({ provider, onAuthorize, onCancel }: Props) {
  const [step, setStep] = useState<Step>("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) {
      setError("Email is required")
      return
    }
    if (!password) {
      setError("Password is required")
      return
    }
    setError("")
    setStep("authorize")
  }

  async function handleAuthorize() {
    setLoading(true)
    await new Promise((r) => setTimeout(r, 1200))
    setLoading(false)
    onAuthorize(email.trim())
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="oauth-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/75 backdrop-blur-sm"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative w-full max-w-md rounded-2xl overflow-hidden shadow-2xl ring-1 ring-zinc-700">
        {/* Provider header */}
        <div
          className="px-6 py-5 text-center"
          style={{ backgroundColor: provider.color }}
        >
          <p id="oauth-title" className="text-xl font-bold text-white tracking-tight">
            {provider.name}
          </p>
          <p className="text-sm text-white/75 mt-1">
            {step === "login"
              ? "Sign in to link your account"
              : "Authorize Channel Stream"}
          </p>
        </div>

        {/* Body */}
        <div className="bg-zinc-900 px-6 py-6">
          {step === "login" ? (
            <form onSubmit={handleLogin} className="space-y-4" noValidate>
              <div>
                <label
                  className="block text-sm font-medium text-zinc-300 mb-1.5"
                  htmlFor="oauth-email"
                >
                  Email
                </label>
                <input
                  id="oauth-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  autoFocus
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3.5 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-offset-0 transition-shadow"
                  style={
                    {
                      "--tw-ring-color": provider.color,
                    } as React.CSSProperties
                  }
                />
              </div>
              <div>
                <label
                  className="block text-sm font-medium text-zinc-300 mb-1.5"
                  htmlFor="oauth-password"
                >
                  Password
                </label>
                <input
                  id="oauth-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3.5 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-offset-0 transition-shadow"
                />
              </div>
              {error && (
                <p className="text-sm text-red-400" role="alert">
                  {error}
                </p>
              )}
              <div className="flex flex-col gap-2 pt-1">
                <button
                  type="submit"
                  className="w-full py-2.5 rounded-xl font-semibold text-white transition-opacity hover:opacity-90 active:opacity-80"
                  style={{ backgroundColor: provider.color }}
                >
                  Continue
                </button>
                <button
                  type="button"
                  onClick={onCancel}
                  className="w-full py-2.5 rounded-xl font-medium text-zinc-400 hover:text-zinc-200 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-5">
              <div>
                <p className="text-sm text-zinc-300 leading-relaxed mb-4">
                  <span className="font-semibold text-zinc-100">
                    Channel Stream
                  </span>{" "}
                  is requesting access to your{" "}
                  <span
                    className="font-semibold"
                    style={{ color: provider.color }}
                  >
                    {provider.name}
                  </span>{" "}
                  account.
                </p>

                <div className="bg-zinc-800/60 rounded-2xl p-4">
                  <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
                    Permissions requested
                  </p>
                  <ul className="space-y-2">
                    {provider.permissions.map((perm) => (
                      <li
                        key={perm}
                        className="flex items-center gap-2.5 text-sm text-zinc-300"
                      >
                        <svg
                          className="w-4 h-4 flex-shrink-0 text-emerald-400"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          aria-hidden="true"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        {perm}
                      </li>
                    ))}
                  </ul>
                </div>

                <p className="text-xs text-zinc-500 mt-3">
                  Signing in as{" "}
                  <span className="text-zinc-300 font-medium">{email}</span>
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={onCancel}
                  className="flex-1 py-2.5 rounded-xl font-medium text-zinc-400 bg-zinc-800 hover:bg-zinc-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAuthorize}
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-xl font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-70 flex items-center justify-center gap-2"
                  style={{ backgroundColor: provider.color }}
                >
                  {loading ? (
                    <>
                      <svg
                        className="w-4 h-4 animate-spin"
                        viewBox="0 0 24 24"
                        fill="none"
                        aria-hidden="true"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                      <span>Linking...</span>
                    </>
                  ) : (
                    "Authorize"
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
