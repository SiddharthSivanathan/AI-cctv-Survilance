'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores/auth-store';

/**
 * Tracks whether the persisted auth store has finished rehydrating from
 * localStorage. Starts `false` (matching server render), then flips to `true`
 * via a real React state update once hydration completes — so guarded routes
 * re-render instead of getting stuck on a loading state.
 */
function useAuthHydrated(): boolean {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => setHydrated(true));
    // May already be hydrated by the time this effect runs.
    if (useAuthStore.persist.hasHydrated()) setHydrated(true);
    return unsub;
  }, []);
  return hydrated;
}

/** Convenience selector for auth state + logout. */
export function useAuth() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);
  const hydrated = useAuthHydrated();

  return {
    isAuthenticated: Boolean(accessToken),
    accessToken,
    refreshToken,
    user,
    hydrated,
    clear,
  };
}
