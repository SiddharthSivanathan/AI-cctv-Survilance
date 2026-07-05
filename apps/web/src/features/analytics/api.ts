import { apiRequest } from '@/lib/api-client';
import type { AlertBreakdown, CameraHealth, Overview, Timeseries } from './types';

const BASE = '/api/v1/analytics';

export const analyticsApi = {
  overview: () => apiRequest<Overview>(`${BASE}/overview`, { auth: true }),
  timeseries: (range: string, bucket: string) =>
    apiRequest<Timeseries>(`${BASE}/timeseries?range=${range}&bucket=${bucket}`, { auth: true }),
  alertBreakdown: (range: string) =>
    apiRequest<AlertBreakdown>(`${BASE}/alerts-breakdown?range=${range}`, { auth: true }),
  cameraHealth: () => apiRequest<CameraHealth>(`${BASE}/camera-health`, { auth: true }),
};
