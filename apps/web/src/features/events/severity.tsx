import { Badge } from '@visionops/ui';

const VARIANT: Record<string, 'destructive' | 'secondary' | 'success'> = {
  critical: 'destructive',
  high: 'destructive',
  medium: 'secondary',
  low: 'secondary',
};

export function SeverityBadge({ severity }: { severity: string }) {
  return <Badge variant={VARIANT[severity] ?? 'secondary'}>{severity}</Badge>;
}

const STATUS_VARIANT: Record<string, 'destructive' | 'secondary' | 'success'> = {
  open: 'destructive',
  acknowledged: 'secondary',
  resolved: 'success',
};

export function StatusBadge({ status }: { status: string }) {
  return <Badge variant={STATUS_VARIANT[status] ?? 'secondary'}>{status}</Badge>;
}
