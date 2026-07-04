import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthResult, MeResponse, TokenResponse } from '@/features/auth/types';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: MeResponse | null;
  hydrated: boolean;
  setSession: (result: AuthResult) => void;
  setTokens: (tokens: TokenResponse) => void;
  setUser: (user: MeResponse) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      hydrated: false,
      setSession: (result) =>
        set({
          accessToken: result.tokens.access_token,
          refreshToken: result.tokens.refresh_token,
          user: result.user,
        }),
      setTokens: (tokens) =>
        set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }),
      setUser: (user) => set({ user }),
      clear: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: 'visionops-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) state.hydrated = true;
      },
    },
  ),
);
