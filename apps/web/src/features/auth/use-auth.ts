'use client';

import { useAuthStore } from '@/stores/auth-store';

/** Convenience selector for auth state + logout. */
export function useAuth() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const user = useAuthStore((s) => s.user);
  const hydrated = useAuthStore((s) => s.hydrated);
  const clear = useAuthStore((s) => s.clear);

  return {
    isAuthenticated: Boolean(accessToken),
    accessToken,
    refreshToken,
    user,
    hydrated,
    clear,
  };
}
