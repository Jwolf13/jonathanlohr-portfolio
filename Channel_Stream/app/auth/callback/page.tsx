"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { exchangeCode, storeTokens } from "@/lib/auth"

export default function AuthCallbackPage() {
  const router = useRouter()
  const [error, setError] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code   = params.get("code")
    const state  = params.get("state")

    if (!code || !state || params.get("error")) {
      setError(true)
      return
    }

    exchangeCode(code, state)
      .then((tokens) => {
        if (!tokens) { setError(true); return }
        storeTokens(tokens)
        router.replace("/")
      })
      .catch(() => setError(true))
  }, [router])

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <p className="text-2xl font-semibold mb-2">Sign-in failed</p>
        <p className="text-gray-400 mb-6 text-sm">Something went wrong during authentication.</p>
        <a href="/" className="text-blue-400 hover:text-blue-300 text-sm transition-colors">
          ← Back to home
        </a>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center py-32">
      <div className="flex items-center gap-3 text-gray-400">
        <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <span>Signing you in…</span>
      </div>
    </div>
  )
}
