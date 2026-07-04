export interface Rule {
  id: string;
  camera_id: string;
  store_id: string;
  zone_id: string | null;
  name: string;
  rule_type: string;
  severity: string;
  cooldown_seconds: number;
  enabled: boolean;
  config: Record<string, unknown> | null;
}

export interface CreateRuleInput {
  camera_id: string;
  zone_id?: string | null;
  name: string;
  rule_type: string;
  severity?: string;
  cooldown_seconds?: number;
  enabled?: boolean;
  config?: Record<string, unknown>;
}

export const RULE_TYPES = [
  {
    value: 'queue_threshold',
    label: 'Queue too long',
    threshold_label: 'Max people in queue',
    threshold_key: 'threshold',
    needs_zone: true,
  },
  {
    value: 'occupancy_limit',
    label: 'Occupancy limit',
    threshold_label: 'Max people in area',
    threshold_key: 'threshold',
    needs_zone: true,
  },
  {
    value: 'loitering',
    label: 'Loitering',
    threshold_label: 'Seconds before alert',
    threshold_key: 'threshold_seconds',
    needs_zone: true,
  },
  {
    value: 'unattended_billing_counter',
    label: 'Unattended counter',
    threshold_label: 'Seconds unattended',
    threshold_key: 'threshold_seconds',
    needs_zone: true,
  },
] as const;

export const SEVERITIES = ['low', 'medium', 'high', 'critical'] as const;
