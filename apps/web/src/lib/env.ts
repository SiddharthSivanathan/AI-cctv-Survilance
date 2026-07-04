/**
 * Public runtime configuration for the web app.
 * Only NEXT_PUBLIC_* vars are available in the browser.
 */
export const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? 'VisionOps AI',
} as const;
