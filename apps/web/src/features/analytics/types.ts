export interface Overview {
  active_cameras: number;
  cameras_online: number;
  alerts_today: number;
  critical_alerts_today: number;
  current_occupancy: number;
  todays_footfall: number;
}

export interface MetricPoint {
  bucket: string;
  occupancy_avg: number;
  occupancy_peak: number;
  footfall: number;
  queue_avg: number;
  queue_peak: number;
}

export interface Timeseries {
  points: MetricPoint[];
}

export interface AlertBreakdown {
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
}

export interface CameraHealth {
  total: number;
  online: number;
  offline: number;
  uptime_pct: number;
}

export const TIME_RANGES = [
  { value: 'today', label: 'Today', bucket: 'hour' },
  { value: 'yesterday', label: 'Yesterday', bucket: 'hour' },
  { value: '7d', label: 'Last 7 days', bucket: 'day' },
  { value: '30d', label: 'Last 30 days', bucket: 'day' },
] as const;

export type TimeRange = (typeof TIME_RANGES)[number]['value'];
