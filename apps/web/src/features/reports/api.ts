import { env } from '@/lib/env';
import { apiRequest } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import type { Report, ReportListItem } from './types';

const BASE = '/api/v1/reports';

export const reportsApi = {
  list: () => apiRequest<ReportListItem[]>(BASE, { auth: true }),
  get: (id: string) => apiRequest<Report>(`${BASE}/${id}`, { auth: true }),
  generate: (report_type: string) =>
    apiRequest<Report>(`${BASE}/generate`, { method: 'POST', body: { report_type }, auth: true }),

  /** Download a report export (pdf|csv) as a file. */
  download: async (id: string, format: 'pdf' | 'csv') => {
    const token = useAuthStore.getState().accessToken;
    const res = await fetch(`${env.apiUrl}${BASE}/${id}/${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!res.ok) throw new Error('Download failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${id}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  },
};
