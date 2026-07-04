'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { eventsApi } from './api';

export function useEvents(params?: { status?: string; camera_id?: string }) {
  return useQuery({
    queryKey: ['events', params],
    queryFn: () => eventsApi.listEvents(params),
    refetchInterval: 5000,
  });
}

export function useAlerts(status?: string) {
  return useQuery({
    queryKey: ['alerts', status],
    queryFn: () => eventsApi.listAlerts(status),
    refetchInterval: 5000,
  });
}

export function useAcknowledgeAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => eventsApi.acknowledge(alertId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  });
}
