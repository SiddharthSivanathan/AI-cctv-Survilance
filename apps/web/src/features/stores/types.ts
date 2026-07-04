export interface Store {
  id: string;
  organization_id: string;
  name: string;
  code: string | null;
  address: string | null;
  city: string | null;
  country: string | null;
  timezone: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CreateStoreInput {
  name: string;
  code?: string;
  address?: string;
  city?: string;
  country?: string;
  timezone?: string;
}

export type UpdateStoreInput = Partial<CreateStoreInput> & { status?: string };
