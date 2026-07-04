'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { camerasApi } from './api';
import type { CreateCameraInput, UpdateCameraInput } from './types';

export function useCameras(storeId?: string) {
  return useQuery({
    queryKey: ['cameras', storeId ?? 'all'],
    queryFn: () => camerasApi.list(storeId),
  });
}

export function useCamera(id: string) {
  return useQuery({
    queryKey: ['camera', id],
    queryFn: () => camerasApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCamera() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateCameraInput) => camerasApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cameras'] }),
  });
}

export function useUpdateCamera(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateCameraInput) => camerasApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cameras'] });
      qc.invalidateQueries({ queryKey: ['camera', id] });
    },
  });
}

export function useDeleteCamera() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => camerasApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cameras'] }),
  });
}

export function useTestCamera(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => camerasApi.test(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cameras'] });
      qc.invalidateQueries({ queryKey: ['camera', id] });
    },
  });
}

export function useTestConnection() {
  return useMutation({ mutationFn: camerasApi.testConnection });
}
