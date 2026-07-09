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
    value: 'intrusion',
    label: 'Intrusion (zone entry)',
    threshold_label: '',
    threshold_key: '',
    needs_zone: true,
    no_threshold: true,
    needs_line: false,
  },
  {
    value: 'line_crossing',
    label: 'Line crossing (tripwire)',
    threshold_label: '',
    threshold_key: '',
    needs_zone: false,
    no_threshold: true,
    needs_line: true,
  },
  {
    value: 'queue_threshold',
    label: 'Queue too long',
    threshold_label: 'Max people in queue',
    threshold_key: 'threshold',
    needs_zone: true,
    no_threshold: false,
    needs_line: false,
  },
  {
    value: 'occupancy_limit',
    label: 'Occupancy limit',
    threshold_label: 'Max people in area',
    threshold_key: 'threshold',
    needs_zone: true,
    no_threshold: false,
    needs_line: false,
  },
  {
    value: 'loitering',
    label: 'Loitering',
    threshold_label: 'Seconds before alert',
    threshold_key: 'threshold_seconds',
    needs_zone: true,
    no_threshold: false,
    needs_line: false,
  },
  {
    value: 'unattended_billing_counter',
    label: 'Unattended counter',
    threshold_label: 'Seconds unattended',
    threshold_key: 'threshold_seconds',
    needs_zone: true,
    no_threshold: false,
    needs_line: false,
  },
] as const;

export const SEVERITIES = ['low', 'medium', 'high', 'critical'] as const;
