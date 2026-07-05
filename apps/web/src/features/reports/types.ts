export interface TrendPoint {
  label: string;
  value: number;
}

export interface AlertRow {
  time: string;
  camera_name: string;
  event_type: string;
  severity: string;
  status: string;
}

export interface CameraActivityItem {
  camera_id: string;
  camera_name: string;
  total_footfall: number;
  total_events: number;
  avg_occupancy: number;
  peak_occupancy: number;
  uptime_pct: number;
  status: string;
}

export interface ReportData {
  company_name: string;
  logo_url: string | null;
  report_type: string;
  start_date: string;
  end_date: string;
  generated_at: string;
  executive_summary: string[];
  recommendations: string[];
  total_footfall: number;
  avg_occupancy: number;
  peak_occupancy: number;
  total_alerts: number;
  critical_alerts: number;
  overall_uptime_pct: number;
  total_cameras: number;
  cameras_online: number;
  queue_stats: { avg_queue_length: number; peak_queue_length: number; threshold_exceeded_count: number };
  alert_summary: { total_alerts: number; by_type: Record<string, number> };
  footfall_trend: TrendPoint[];
  occupancy_trend: TrendPoint[];
  queue_trend: TrendPoint[];
  alert_rows: AlertRow[];
  cameras: CameraActivityItem[];
}

export interface Report {
  id: string;
  report_type: string;
  period_start: string;
  period_end: string;
  status: string;
  generated_at: string;
  data: ReportData;
}

export interface ReportListItem {
  id: string;
  report_type: string;
  period_start: string;
  period_end: string;
  generated_at: string;
}

export const REPORT_TYPES = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
] as const;
