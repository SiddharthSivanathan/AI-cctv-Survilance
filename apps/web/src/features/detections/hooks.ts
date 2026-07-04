'use client';

import { useQuery } from '@tanstack/react-query';
import { detectionsApi } from './api';

/** Polls the latest detection overlay for a camera while enabled. */
export function useLatestDetections(cameraId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['detections', cameraId],
    queryFn: () => detectionsApi.latest(cameraId),
    enabled,
    refetchInterval: 1000,
    staleTime: 0,
  });
}
