import { apiRequest } from '@/lib/api-client';
import type {
  Camera,
  ConnectionTestResult,
  CreateCameraInput,
  UpdateCameraInput,
} from './types';

const BASE = '/api/v1/cameras';

export const camerasApi = {
  list: (storeId?: string) =>
    apiRequest<Camera[]>(storeId ? `${BASE}?store_id=${storeId}` : BASE, { auth: true }),
  get: (id: string) => apiRequest<Camera>(`${BASE}/${id}`, { auth: true }),
  create: (data: CreateCameraInput) =>
    apiRequest<Camera>(BASE, { method: 'POST', body: data, auth: true }),
  update: (id: string, data: UpdateCameraInput) =>
    apiRequest<Camera>(`${BASE}/${id}`, { method: 'PATCH', body: data, auth: true }),
  remove: (id: string) =>
    apiRequest<void>(`${BASE}/${id}`, { method: 'DELETE', auth: true }),
  test: (id: string) =>
    apiRequest<Camera>(`${BASE}/${id}/test`, { method: 'POST', auth: true }),
  testConnection: (data: { rtsp_url: string; username?: string; password?: string }) =>
    apiRequest<ConnectionTestResult>(`${BASE}/test-connection`, {
      method: 'POST',
      body: data,
      auth: true,
    }),
};
