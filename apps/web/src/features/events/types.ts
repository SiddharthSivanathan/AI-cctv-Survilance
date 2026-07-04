export interface CameraEvent {
  id: string;
  camera_id: string;
  store_id: string | null;
  rule_id: string | null;
  event_type: string;
  severity: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  created_at: string;
}

export interface Alert {
  id: string;
  event_id: string;
  camera_id: string | null;
  event_type: string;
  severity: string;
  status: string;
  acknowledged: boolean;
  acknowledged_at: string | null;
  created_at: string;
}

export const EVENT_LABELS: Record<string, string> = {
  queue_threshold_exceeded: 'Queue too long',
  queue_resolved: 'Queue cleared',
  occupancy_limit_exceeded: 'Occupancy exceeded',
  occupancy_normalized: 'Occupancy normal',
  loitering_detected: 'Loitering detected',
  loitering_ended: 'Loitering ended',
  unattended_billing_counter: 'Counter unattended',
  billing_counter_staffed: 'Counter staffed',
  camera_offline: 'Camera offline',
};

export function eventLabel(type: string): string {
  return EVENT_LABELS[type] ?? type;
}
