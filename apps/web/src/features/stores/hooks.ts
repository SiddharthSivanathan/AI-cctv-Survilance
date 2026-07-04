'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { storesApi } from './api';
import type { CreateStoreInput, UpdateStoreInput } from './types';

const KEY = ['stores'];

export function useStores() {
  return useQuery({ queryKey: KEY, queryFn: storesApi.list });
}

export function useStore(id: string) {
  return useQuery({ queryKey: ['stores', id], queryFn: () => storesApi.get(id), enabled: !!id });
}

export function useCreateStore() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateStoreInput) => storesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateStore(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateStoreInput) => storesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY });
      qc.invalidateQueries({ queryKey: ['stores', id] });
    },
  });
}

export function useDeleteStore() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => storesApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
