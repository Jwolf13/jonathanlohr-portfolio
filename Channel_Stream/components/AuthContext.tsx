"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { getStoredToken, parseJwtPayload, clearTokens, startLogin } from "@/lib/auth"
import { getPreferences, savePreferences } from "@/lib/api"

export interface User {
  sub:   string
  email: string
  name?: string
}

interface AuthContextType {
  user:             User | null
  loading:          boolean
  selectedTeams:    string[]
  setSelectedTeams: (teams: string[]) => void
  signIn:           () => void
  signOut:          () => void
}

const AuthContext = createContext<AuthContextType>({
  user:             null,
  loading:          true,
  selectedTeams:    [],
  setSelectedTeams: () => {},
  signIn:           () => {},
  signOut:          () => {},
})

const SESSION_TEAMS_KEY = "cs_selected_teams"

function initUser(): User | null {
  if (typeof window === "undefined") return null
  const token = getStoredToken()
  if (!token) return null
  const p     = parseJwtPayload(token)
  const sub   = p.sub   as string | undefined
  const email = p.email as string | undefined
  return sub && email ? { sub, email, name: p.name as string | undefined } : null
}

function initTeams(): string[] {
  if (typeof window === "undefined") return []
  if (getStoredToken()) return [] // will be overwritten from server preferences
  try {
    const stored = sessionStorage.getItem(SESSION_TEAMS_KEY)
    return stored ? (JSON.parse(stored) as string[]) : []
  } catch {
    return []
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]                  = useState<User | null>(initUser)
  const [selectedTeams, setTeamsState]   = useState<string[]>(initTeams)
  const [loading, setLoading]            = useState<boolean>(() => {
    if (typeof window === "undefined") return false
    return getStoredToken() !== null
  })

  useEffect(() => {
    const token = getStoredToken()
    if (!token) return
    getPreferences(token)
      .then((prefs) => {
        if (prefs.teams?.length > 0) setTeamsState(prefs.teams)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const setSelectedTeams = (teams: string[]) => {
    setTeamsState(teams)
    sessionStorage.setItem(SESSION_TEAMS_KEY, JSON.stringify(teams))
    const token = getStoredToken()
    if (token && user) {
      savePreferences({ teams }, token).catch(() => {})
    }
  }

  const signIn  = () => { startLogin() }
  const signOut = () => {
    clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, selectedTeams, setSelectedTeams, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
