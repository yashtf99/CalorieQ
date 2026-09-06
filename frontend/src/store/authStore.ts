import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  display_name: string | null
  created_at: string
  updated_at: string
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setTokens: (access: string, refresh: string, user?: User) => void
  setUser: (user: User) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setTokens: (access, refresh, user) =>
        set((s) => ({ accessToken: access, refreshToken: refresh, user: user ?? s.user })),
      setUser: (user) => set({ user }),
      clearAuth: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: 'calorieq-auth' },
  ),
)
