import { apiRequest } from '@/lib/api-client';
import type {
  AuthResult,
  MeResponse,
  MessageResponse,
  OrganizationResponse,
} from './types';

const BASE = '/api/v1/auth';
const ORG = '/api/v1/organizations';

export const authApi = {
  register: (data: { full_name: string; email: string; password: string }) =>
    apiRequest<MessageResponse>(`${BASE}/register`, { method: 'POST', body: data }),

  verifyEmail: (token: string) =>
    apiRequest<AuthResult>(`${BASE}/verify-email`, { method: 'POST', body: { token } }),

  resendVerification: (email: string) =>
    apiRequest<MessageResponse>(`${BASE}/resend-verification`, {
      method: 'POST',
      body: { email },
    }),

  login: (data: { email: string; password: string }) =>
    apiRequest<AuthResult>(`${BASE}/login`, { method: 'POST', body: data }),

  logout: (refresh_token: string) =>
    apiRequest<MessageResponse>(`${BASE}/logout`, { method: 'POST', body: { refresh_token } }),

  forgotPassword: (email: string) =>
    apiRequest<MessageResponse>(`${BASE}/forgot-password`, { method: 'POST', body: { email } }),

  resetPassword: (data: { token: string; password: string }) =>
    apiRequest<MessageResponse>(`${BASE}/reset-password`, { method: 'POST', body: data }),

  me: () => apiRequest<MeResponse>(`${BASE}/me`, { auth: true }),

  createOrganization: (data: { name: string; industry?: string }) =>
    apiRequest<MeResponse>(ORG, { method: 'POST', body: data, auth: true }),

  currentOrganization: () =>
    apiRequest<OrganizationResponse>(`${ORG}/current`, { auth: true }),
};
