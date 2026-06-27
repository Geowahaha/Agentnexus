import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api } from '../api/client'
import type { User } from '../types'

const TOKEN_KEY = 'agentnexus_token'

interface AuthContextValue {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithGoogle: (idToken: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password)
    localStorage.setItem(TOKEN_KEY, access_token)
    setToken(access_token)
    const me = await api.me(access_token)
    setUser(me)
  }, [])

  const loginWithGoogle = useCallback(async (idToken: string) => {
    const { access_token } = await api.loginWithGoogle(idToken)
    localStorage.setItem(TOKEN_KEY, access_token)
    setToken(access_token)
    const me = await api.me(access_token)
    setUser(me)
  }, [])

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    await api.register(email, password, fullName)
    await login(email, password)
  }, [login])

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    api
      .me(token)
      .then(setUser)
      .catch(() => logout())
      .finally(() => setLoading(false))
  }, [token, logout])

  const value = useMemo(
    () => ({ user, token, loading, login, loginWithGoogle, register, logout }),
    [user, token, loading, login, loginWithGoogle, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}