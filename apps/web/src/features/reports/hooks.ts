'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { reportsApi } from './api';

export function useReports() {
  return useQuery({ queryKey: ['reports'], queryFn: reportsApi.list });
}

export function useReport(id: string) {
  return useQuery({ queryKey: ['report', id], queryFn: () => reportsApi.get(id), enabled: !!id });
}

export function useGenerateReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reportType: string) => reportsApi.generate(reportType),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports'] }),
  });
}
