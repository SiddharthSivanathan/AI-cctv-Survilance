import { apiRequest } from '@/lib/api-client';
import type { LiveStreamResponse } from './types';

export const streamsApi = {
  startLive: (cameraId: string) =>
    apiRequest<LiveStreamResponse>(`/api/v1/cameras/${cameraId}/live`, {
      method: 'POST',
      auth: true,
    }),
};
