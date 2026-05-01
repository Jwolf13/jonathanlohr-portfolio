"use client"

import { useAuth } from "@/components/AuthContext"

export function TopBar() {
  const { user, loading, signIn, signOut } = useAuth()

  return (
    <header className="h-14 border-b border-gray-800 bg-gray-950 flex items-center justify-end px-8 flex-shrink-0">
      {!loading && (
        user ? (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
                {user.email[0].toUpperCase()}
              </div>
              <span className="text-sm text-gray-300">{user.name ?? user.email}</span>
            </div>
            <button
              onClick={signOut}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              Sign out
            </button>
          </div>
        ) : (
          <button
            onClick={signIn}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors"
          >
            Sign up / Sign in
          </button>
        )
      )}
    </header>
  )
}
