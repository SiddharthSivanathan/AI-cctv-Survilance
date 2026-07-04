import { apiRequest } from '@/lib/api-client';
import type { Alert, CameraEvent } from './types';

export const eventsApi = {
  listEvents: (params?: { status?: string; camera_id?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return apiRequest<CameraEvent[]>(`/api/v1/events${q ? `?${q}` : ''}`, { auth: true });
  },
  listAlerts: (status?: string) =>
    apiRequest<Alert[]>(`/api/v1/alerts${status ? `?status=${status}` : ''}`, { auth: true }),
  acknowledge: (alertId: string) =>
    apiRequest<Alert>(`/api/v1/alerts/${alertId}/acknowledge`, { method: 'POST', auth: true }),
};
