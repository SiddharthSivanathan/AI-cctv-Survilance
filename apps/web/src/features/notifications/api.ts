import { apiRequest } from '@/lib/api-client';
import type { NotificationList } from './types';

const BASE = '/api/v1/notifications';

export const notificationsApi = {
  list: () => apiRequest<NotificationList>(BASE, { auth: true }),
  unreadCount: () => apiRequest<{ unread: number }>(`${BASE}/unread-count`, { auth: true }),
  markRead: (id: string) =>
    apiRequest<unknown>(`${BASE}/${id}/read`, { method: 'POST', auth: true }),
  markAllRead: () =>
    apiRequest<{ updated: number }>(`${BASE}/read-all`, { method: 'POST', auth: true }),
};
