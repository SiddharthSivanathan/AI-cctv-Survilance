import { apiRequest } from '@/lib/api-client';
import type { LatestDetections } from './types';

export const detectionsApi = {
  latest: (cameraId: string) =>
    apiRequest<LatestDetections>(`/api/v1/cameras/${cameraId}/detections/latest`, { auth: true }),
};
