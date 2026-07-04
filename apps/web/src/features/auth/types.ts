/** Auth DTOs mirroring the backend OpenAPI schema (generated in a later phase). */

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_email_verified: boolean;
}

export interface OrganizationResponse {
  id: string;
  name: string;
  slug: string;
  industry: string | null;
  status: string;
  logo_url?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  address?: string | null;
  timezone?: string;
  currency?: string;
  alert_email_enabled?: boolean;
  created_at?: string;
}

export interface MeResponse {
  user: UserResponse;
  organization: OrganizationResponse | null;
  role: string | null;
  needs_onboarding: boolean;
}

export interface AuthResult {
  tokens: TokenResponse;
  user: MeResponse;
}

export interface MessageResponse {
  message: string;
}

export interface ApiErrorBody {
  error: { code: string; message: string; details?: Record<string, unknown> };
}
