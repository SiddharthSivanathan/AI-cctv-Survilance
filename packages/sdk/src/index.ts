import type { ApiError } from '@visionops/types';

export interface ClientOptions {
  /** Base URL of the VisionOps API, e.g. http://localhost:8000 */
  baseUrl: string;
  /** Optional bearer token provider (async to support refresh flows). */
  getToken?: () => string | null | Promise<string | null>;
  /** Optional fetch implementation (defaults to global fetch). */
  fetch?: typeof fetch;
}

/** Thrown when the API returns a non-2xx response. */
export class VisionOpsApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiError | null,
  ) {
    super(body?.error?.message ?? `Request failed with status ${status}`);
    this.name = 'VisionOpsApiError';
  }
}

/**
 * Minimal typed HTTP client for the VisionOps API.
 * Feature-specific methods are added per phase as endpoints land.
 */
export class VisionOpsClient {
  private readonly baseUrl: string;
  private readonly getToken?: ClientOptions['getToken'];
  private readonly fetchImpl: typeof fetch;

  constructor(options: ClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.getToken = options.getToken;
    this.fetchImpl = options.fetch ?? globalThis.fetch;
  }

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const token = this.getToken ? await this.getToken() : null;
    const headers = new Headers(init.headers);
    headers.set('Content-Type', 'application/json');
    if (token) headers.set('Authorization', `Bearer ${token}`);

    const res = await this.fetchImpl(`${this.baseUrl}${path}`, { ...init, headers });
    if (!res.ok) {
      const body = (await res.json().catch(() => null)) as ApiError | null;
      throw new VisionOpsApiError(res.status, body);
    }
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  }

  /** Liveness/readiness probe against the API. */
  health(): Promise<{ status: string; service: string; version: string }> {
    return this.request('/health');
  }
}
