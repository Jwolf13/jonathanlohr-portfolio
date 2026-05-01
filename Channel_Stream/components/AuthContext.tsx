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
  user:               User | null
  loading:            boolean
  selectedLeagues:    string[]
  setSelectedLeagues: (leagues: string[]) => void
  selectedTeams:      string[]
  setSelectedTeams:   (teams: string[]) => void
  signIn:             () => void
  signOut:            () => void
}

const AuthContext = createContext<AuthContextType>({
  user:               null,
  loading:            true,
  selectedLeagues:    [],
  setSelectedLeagues: () => {},
  selectedTeams:      [],
  setSelectedTeams:   () => {},
  signIn:             () => {},
  signOut:            () => {},
})

const SESSION_LEAGUES_KEY = "cs_selected_leagues"
const SESSION_TEAMS_KEY   = "cs_selected_teams"

function initUser(): User | null {
  if (typeof window === "undefined") return null
  const token = getStoredToken()
  if (!token) return null
  const p     = parseJwtPayload(token)
  const sub   = p.sub   as string | undefined
  const email = p.email as string | undefined
  return sub && email ? { sub, email, name: p.name as string | undefined } : null
}

function initFromSession(key: string): string[] {
  if (typeof window === "undefined") return []
  if (getStoredToken()) return [] // will be overwritten from server preferences
  try {
    const stored = sessionStorage.getItem(key)
    return stored ? (JSON.parse(stored) as string[]) : []
  } catch {
    return []
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]                    = useState<User | null>(initUser)
  const [selectedLeagues, setLeaguesState] = useState<string[]>(() => initFromSession(SESSION_LEAGUES_KEY))
  const [selectedTeams, setTeamsState]     = useState<string[]>(() => initFromSession(SESSION_TEAMS_KEY))
  const [loading, setLoading]              = useState<boolean>(() => {
    if (typeof window === "undefined") return false
    return getStoredToken() !== null
  })

  useEffect(() => {
    const token = getStoredToken()
    if (!token) return
    getPreferences(token)
      .then((prefs) => {
        if (prefs.leagues?.length > 0) setLeaguesState(prefs.leagues)
        if (prefs.teams?.length > 0) setTeamsState(prefs.teams)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const setSelectedLeagues = (leagues: string[]) => {
    setLeaguesState(leagues)
    sessionStorage.setItem(SESSION_LEAGUES_KEY, JSON.stringify(leagues))
    const token = getStoredToken()
    if (token && user) {
      // Use functional read to get current teams without stale closure
      setTeamsState((teams) => {
        savePreferences({ leagues, teams }, token).catch(() => {})
        return teams
      })
    }
  }

  const setSelectedTeams = (teams: string[]) => {
    setTeamsState(teams)
    sessionStorage.setItem(SESSION_TEAMS_KEY, JSON.stringify(teams))
    const token = getStoredToken()
    if (token && user) {
      setLeaguesState((leagues) => {
        savePreferences({ leagues, teams }, token).catch(() => {})
        return leagues
      })
    }
  }

  const signIn  = () => { startLogin() }
  const signOut = () => {
    clearTokens()
    sessionStorage.removeItem(SESSION_LEAGUES_KEY)
    sessionStorage.removeItem(SESSION_TEAMS_KEY)
    setUser(null)
    setLeaguesState([])
    setTeamsState([])
  }

  return (
    <AuthContext.Provider value={{
      user, loading,
      selectedLeagues, setSelectedLeagues,
      selectedTeams,   setSelectedTeams,
      signIn, signOut,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
