'use client';

import { useMutation } from '@tanstack/react-query';
import { authApi } from './api';
import { useAuthStore } from '@/stores/auth-store';
import type { AuthResult, MeResponse } from './types';

/** Register a new account. */
export function useRegister() {
  return useMutation({ mutationFn: authApi.register });
}

/** Verify email and auto-login (persists the session). */
export function useVerifyEmail() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: authApi.verifyEmail,
    onSuccess: (result: AuthResult) => setSession(result),
  });
}

/** Log in with email + password. */
export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (result: AuthResult) => setSession(result),
  });
}

export function useResendVerification() {
  return useMutation({ mutationFn: authApi.resendVerification });
}

export function useForgotPassword() {
  return useMutation({ mutationFn: authApi.forgotPassword });
}

export function useResetPassword() {
  return useMutation({ mutationFn: authApi.resetPassword });
}

/** Create the user's company (onboarding step 1). Updates stored user context. */
export function useCreateOrganization() {
  const setUser = useAuthStore((s) => s.setUser);
  return useMutation({
    mutationFn: authApi.createOrganization,
    onSuccess: (me: MeResponse) => setUser(me),
  });
}
