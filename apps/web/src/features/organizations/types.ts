export interface Organization {
  id: string;
  name: string;
  slug: string;
  industry: string | null;
  status: string;
  logo_url: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  address: string | null;
  timezone: string;
  currency: string;
  alert_email_enabled: boolean;
  created_at: string;
}

export interface UpdateOrganizationInput {
  name?: string;
  industry?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  address?: string | null;
  timezone?: string;
  currency?: string;
  alert_email_enabled?: boolean;
}
