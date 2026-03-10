import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  userId: string | null
  fullName: string | null
  setTokens: (access: string, refresh: string) => void
  setUser: (id: string, name: string) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      userId: null,
      fullName: null,

      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),

      setUser: (id, name) =>
        set({ userId: id, fullName: name }),

      logout: () =>
        set({ accessToken: null, refreshToken: null, userId: null, fullName: null }),

      isAuthenticated: () => Boolean(get().accessToken),
    }),
    {
      name: 'studyos-auth',
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        userId: s.userId,
        fullName: s.fullName,
      }),
    },
  ),
)
