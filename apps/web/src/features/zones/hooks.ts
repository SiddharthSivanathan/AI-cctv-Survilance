'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { zonesApi } from './api';
import type { CreateZoneInput } from './types';

export function useZones(cameraId: string | undefined) {
  return useQuery({
    queryKey: ['zones', cameraId],
    queryFn: () => zonesApi.listForCamera(cameraId as string),
    enabled: !!cameraId,
  });
}

export function useCreateZone() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateZoneInput) => zonesApi.create(data),
    onSuccess: (zone) => qc.invalidateQueries({ queryKey: ['zones', zone.camera_id] }),
  });
}

export function useDeleteZone(cameraId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => zonesApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['zones', cameraId] }),
  });
}
