import { apiRequest } from '@/lib/api-client';
import type { CreateStoreInput, Store, UpdateStoreInput } from './types';

const BASE = '/api/v1/stores';

export const storesApi = {
  list: () => apiRequest<Store[]>(BASE, { auth: true }),
  get: (id: string) => apiRequest<Store>(`${BASE}/${id}`, { auth: true }),
  create: (data: CreateStoreInput) =>
    apiRequest<Store>(BASE, { method: 'POST', body: data, auth: true }),
  update: (id: string, data: UpdateStoreInput) =>
    apiRequest<Store>(`${BASE}/${id}`, { method: 'PATCH', body: data, auth: true }),
  remove: (id: string) =>
    apiRequest<void>(`${BASE}/${id}`, { method: 'DELETE', auth: true }),
};
