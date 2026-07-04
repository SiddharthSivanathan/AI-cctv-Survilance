import { VisionOpsClient } from '@visionops/sdk';
import { env } from './env';

/**
 * Shared API client instance for the web app.
 * Auth token wiring is added in Phase 3 (auth) via `getToken`.
 */
export const apiClient = new VisionOpsClient({
  baseUrl: env.apiUrl,
});
