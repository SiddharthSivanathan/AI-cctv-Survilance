'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from './api';
import { TIME_RANGES, type TimeRange } from './types';

const AUTO_REFRESH = 60_000;

export function useOverview() {
  return useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: analyticsApi.overview,
    refetchInterval: AUTO_REFRESH,
  });
}

export function useTimeseries(range: TimeRange) {
  const bucket = TIME_RANGES.find((r) => r.value === range)?.bucket ?? 'hour';
  return useQuery({
    queryKey: ['analytics', 'timeseries', range],
    queryFn: () => analyticsApi.timeseries(range, bucket),
    refetchInterval: AUTO_REFRESH,
  });
}

export function useAlertBreakdown(range: TimeRange) {
  return useQuery({
    queryKey: ['analytics', 'breakdown', range],
    queryFn: () => analyticsApi.alertBreakdown(range),
    refetchInterval: AUTO_REFRESH,
  });
}

export function useCameraHealth() {
  return useQuery({
    queryKey: ['analytics', 'camera-health'],
    queryFn: analyticsApi.cameraHealth,
    refetchInterval: AUTO_REFRESH,
  });
}
