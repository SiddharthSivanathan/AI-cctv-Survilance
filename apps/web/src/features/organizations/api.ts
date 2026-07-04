import { env } from '@/lib/env';
import { apiRequest } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import type { Organization, UpdateOrganizationInput } from './types';

const BASE = '/api/v1/organizations';

export const organizationsApi = {
  current: () => apiRequest<Organization>(`${BASE}/current`, { auth: true }),

  update: (data: UpdateOrganizationInput) =>
    apiRequest<Organization>(`${BASE}/current`, { method: 'PATCH', body: data, auth: true }),

  /** Logo upload is multipart, so it bypasses the JSON apiRequest helper. */
  uploadLogo: async (file: File): Promise<Organization> => {
    const form = new FormData();
    form.append('file', file);
    const token = useAuthStore.getState().accessToken;
    const res = await fetch(`${env.apiUrl}${BASE}/current/logo`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.error?.message ?? 'Logo upload failed');
    }
    return (await res.json()) as Organization;
  },
};
