import { apiRequest } from '@/lib/api-client';
import type { CreateZoneInput, Zone } from './types';

const BASE = '/api/v1/zones';

export const zonesApi = {
  listForCamera: (cameraId: string) =>
    apiRequest<Zone[]>(`${BASE}?camera_id=${cameraId}`, { auth: true }),
  create: (data: CreateZoneInput) =>
    apiRequest<Zone>(BASE, { method: 'POST', body: data, auth: true }),
  remove: (id: string) => apiRequest<void>(`${BASE}/${id}`, { method: 'DELETE', auth: true }),
};
