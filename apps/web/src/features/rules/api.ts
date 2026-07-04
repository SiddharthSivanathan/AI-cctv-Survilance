import { apiRequest } from '@/lib/api-client';
import type { CreateRuleInput, Rule } from './types';

const BASE = '/api/v1/rules';

export const rulesApi = {
  list: () => apiRequest<Rule[]>(BASE, { auth: true }),
  create: (data: CreateRuleInput) =>
    apiRequest<Rule>(BASE, { method: 'POST', body: data, auth: true }),
  update: (id: string, data: Partial<CreateRuleInput>) =>
    apiRequest<Rule>(`${BASE}/${id}`, { method: 'PATCH', body: data, auth: true }),
  remove: (id: string) => apiRequest<void>(`${BASE}/${id}`, { method: 'DELETE', auth: true }),
};
