'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuth } from '@/features/auth/use-auth';

/**
 * Client-side route guard. Waits for the persisted auth store to hydrate,
 * then redirects unauthenticated users to /login and users who still need
 * onboarding to /onboarding.
 */
export function AuthGuard({
  children,
  requireOnboarded = true,
}: {
  children: React.ReactNode;
  requireOnboarded?: boolean;
}) {
  const router = useRouter();
  const { hydrated, isAuthenticated, user } = useAuth();

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (requireOnboarded && user?.needs_onboarding) {
      router.replace('/onboarding');
    }
  }, [hydrated, isAuthenticated, user, requireOnboarded, router]);

  if (!hydrated || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }
  return <>{children}</>;
}
