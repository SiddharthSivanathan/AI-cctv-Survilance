import { Badge } from '@visionops/ui';

const VARIANT: Record<string, 'success' | 'destructive' | 'secondary'> = {
  online: 'success',
  offline: 'destructive',
};

export function CameraStatusBadge({ status }: { status: string }) {
  const variant = VARIANT[status] ?? 'secondary';
  return <Badge variant={variant}>{status === 'unknown' ? 'Pending' : status}</Badge>;
}

const RESULT_LABEL: Record<string, string> = {
  connected: 'Connected',
  auth_failed: 'Authentication failed',
  unreachable: 'Camera unreachable',
  invalid_url: 'Invalid RTSP URL',
  timeout: 'Connection timed out',
  error: 'Connection error',
};

export function connectionLabel(status: string): string {
  return RESULT_LABEL[status] ?? status;
}
