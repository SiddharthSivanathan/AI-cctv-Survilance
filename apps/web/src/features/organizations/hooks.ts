'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { organizationsApi } from './api';
import type { UpdateOrganizationInput } from './types';

const KEY = ['organization'];

export function useOrganization() {
  return useQuery({ queryKey: KEY, queryFn: organizationsApi.current });
}

export function useUpdateOrganization() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateOrganizationInput) => organizationsApi.update(data),
    onSuccess: (org) => qc.setQueryData(KEY, org),
  });
}

export function useUploadLogo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => organizationsApi.uploadLogo(file),
    onSuccess: (org) => qc.setQueryData(KEY, org),
  });
}
