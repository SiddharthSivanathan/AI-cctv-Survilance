'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { rulesApi } from './api';
import type { CreateRuleInput } from './types';

export function useRules() {
  return useQuery({ queryKey: ['rules'], queryFn: rulesApi.list });
}

export function useCreateRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateRuleInput) => rulesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  });
}

export function useUpdateRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateRuleInput> }) =>
      rulesApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  });
}

export function useDeleteRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => rulesApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  });
}
